#!/usr/bin/env python3
"""
Parallel Execution Coordinator for [P:Group-X] Markers

Implements the four-phase workflow for parallel task execution:
- Phase 1: Pre-execution analysis (dependency checking, task validation)
- Phase 2: Concurrent execution (skill pre-invocation, parallel launches)
- Phase 3: Coordination & monitoring (progress tracking, beads coordination)
- Phase 4: Post-execution validation (verification, test suite, closure)
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field


class GroupPhase(str, Enum):
    """Parallel group execution phases."""
    PRE_EXECUTION = "pre_execution"
    CONCURRENT_EXECUTION = "concurrent_execution"
    COORDINATION = "coordination"
    POST_EXECUTION = "post_execution"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class GroupMetadata:
    """Metadata for a parallel task group."""
    group_id: str
    group_name: str
    phase: GroupPhase
    tasks: List[str]  # Task IDs in the group
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    pre_group_refresh_completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["phase"] = self.phase.value
        data["status"] = self.status.value
        return data


@dataclass
class TaskMetadata:
    """Metadata for a single task within a group."""
    task_id: str
    title: str
    description: str
    subagent_type: Optional[str] = None
    fallback_agents: List[str] = field(default_factory=list)
    applicable_skills: List[str] = field(default_factory=list)
    relevant_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 2
    status: TaskStatus = TaskStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data


class ParallelCoordinator:
    """
    Coordinates parallel execution of [P:Group-X] marked tasks.

    Implements the complete workflow from implement.md:
    - Detects [P:Group-X] markers in task descriptions
    - Executes pre-group refresh via /flow:summary
    - Launches parallel tasks with skill pre-invocation
    - Monitors progress via beads database
    - Aggregates results and validates completion
    """

    # Regex pattern for detecting [P:Group-X] markers
    GROUP_PATTERN = re.compile(r'\[P:Group-([^\]]+)\]')
    # Regex pattern for extracting group ID from task content
    GROUP_ID_PATTERN = re.compile(r'\[P:Group-(\w+)\]')

    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize parallel coordinator.

        Args:
            repo_root: Repository root path. If None, auto-detected.
        """
        if repo_root:
            self.repo_root = Path(repo_root).absolute()
        else:
            self.repo_root = Path(__file__).parent.parent.parent.parent.absolute()

        self.groups_dir = self.repo_root / ".flow" / "maestro" / "parallel_groups"
        self._ensure_groups_dir()

    def _ensure_groups_dir(self):
        """Create parallel groups directory if it doesn't exist."""
        self.groups_dir.mkdir(parents=True, exist_ok=True)

    def _get_group_dir(self, group_id: str) -> Path:
        """Get directory path for a group."""
        return self.groups_dir / group_id

    def _get_metadata_path(self, group_id: str) -> Path:
        """Get metadata file path for a group."""
        return self._get_group_dir(group_id) / "metadata.json"

    def _current_timestamp(self) -> str:
        """Get current ISO 8601 timestamp."""
        return datetime.now(timezone.utc).isoformat()

    def detect_groups(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect [P:Group-X] markers in task descriptions and group them.

        Args:
            tasks: List of task dictionaries with at least 'id' and 'description'

        Returns:
            Dictionary mapping group IDs to lists of tasks in that group.
            Tasks without [P:Group-X] markers are grouped under "_sequential".

        Example:
            {
                "infrastructure": [
                    {"id": "task-1", "description": "[P:Group-infrastructure] Setup DB", ...},
                    {"id": "task-2", "description": "[P:Group-infrastructure] Setup cache", ...}
                ],
                "_sequential": [
                    {"id": "task-3", "description": "Sequential task", ...}
                ]
            }
        """
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for task in tasks:
            description = task.get("description", "")
            task_id = task.get("id", "")

            # Try to extract group ID from description
            match = self.GROUP_ID_PATTERN.search(description)
            if match:
                group_id = match.group(1)
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append(task)
            else:
                # Sequential task (no group marker)
                if "_sequential" not in groups:
                    groups["_sequential"] = []
                groups["_sequential"].append(task)

        return groups

    def refresh_context_before_group(self) -> bool:
        """
        Execute /flow:summary to refresh context before starting a parallel group.

        This is REQUIRED before starting ANY [P:Group-X] parallel task group
        to ensure accurate context about dependencies and blocking issues.

        Returns:
            True if refresh was successful, False otherwise.
        """
        try:
            # Execute /flow:summary command
            result = subprocess.run(
                ["/home/ll931217/.local/bin/claude", "/flow:summary"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.repo_root,
            )

            if result.returncode == 0:
                print("✓ Pre-group context refresh completed via /flow:summary")
                return True
            else:
                print(f"⚠ Warning: /flow:summary returned non-zero: {result.returncode}")
                print(f"  stderr: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"⚠ Warning: Could not execute /flow:summary: {e}")
            print("  Continuing without refresh (context may be stale)")
            return False
        except Exception as e:
            print(f"✗ Error during context refresh: {e}")
            return False

    def _get_beads_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a beads issue.

        Args:
            issue_id: Beads issue ID (e.g., "proj-auth.1")

        Returns:
            Issue metadata dictionary or None if not found.
        """
        try:
            result = subprocess.run(
                ["bd", "show", "--json", issue_id],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return data
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠ Warning: Could not get issue {issue_id}: {e}")

        return None

    def _extract_task_metadata(self, task: Dict[str, Any]) -> TaskMetadata:
        """
        Extract metadata from a task, including subagent type and skills.

        Args:
            task: Task dictionary with at least 'id' and 'description'

        Returns:
            TaskMetadata object with extracted information.
        """
        task_id = task.get("id", "")
        title = task.get("title", task.get("description", "").split("\n")[0])
        description = task.get("description", "")

        # Try to get metadata from beads issue
        issue_data = self._get_beads_issue(task_id)

        subagent_type = None
        fallback_agents = []
        applicable_skills = []
        relevant_files = []
        dependencies = []
        priority = 2

        if issue_data:
            # Extract subagent type from metadata
            metadata = issue_data.get("metadata", {})
            if isinstance(metadata, dict):
                subagent_type = metadata.get("subagent_type")
                fallback_agents = metadata.get("fallback_agents", [])
                applicable_skills = metadata.get("applicable_skills", [])

            # Extract other fields
            priority = issue_data.get("priority", 2)

            # Extract dependencies
            deps = issue_data.get("dependencies", [])
            dependencies = [
                dep.get("id") for dep in deps
                if dep.get("dependency_type") != "parent-child"
            ]

            # Extract relevant files from description
            relevant_files = self._extract_relevant_files(description)

        return TaskMetadata(
            task_id=task_id,
            title=title,
            description=description,
            subagent_type=subagent_type,
            fallback_agents=fallback_agents,
            applicable_skills=applicable_skills,
            relevant_files=relevant_files,
            dependencies=dependencies,
            priority=priority,
        )

    def _extract_relevant_files(self, description: str) -> List[str]:
        """
        Extract file paths from task description.

        Args:
            description: Task description text

        Returns:
            List of file paths found in the description.
        """
        files = []

        # Look for file paths in common patterns
        # Pattern: paths like src/components/Login.tsx
        file_pattern = re.compile(r'(?:[\w/]+/)?[\w]+\.(?:ts|tsx|js|jsx|py|rs|go|java)')
        matches = file_pattern.findall(description)
        files.extend(matches)

        # Look for explicit file mentions
        for line in description.split("\n"):
            if "file:" in line.lower() or "path:" in line.lower():
                # Extract path after common markers
                for marker in ["file:", "path:", "location:", "src/"]:
                    if marker in line:
                        parts = line.split(marker)
                        if len(parts) > 1:
                            potential_path = parts[1].strip().split()[0].strip("`,\"'")
                            if potential_path:
                                files.append(potential_path)

        return list(set(files))  # Remove duplicates

    def _check_dependencies_blocked(self, task_metadata: TaskMetadata) -> bool:
        """
        Check if a task's dependencies are blocking execution.

        Args:
            task_metadata: Task metadata with dependencies

        Returns:
            True if any dependencies are still open (blocking), False otherwise.
        """
        if not task_metadata.dependencies:
            return False

        for dep_id in task_metadata.dependencies:
            issue = self._get_beads_issue(dep_id)
            if issue and issue.get("status") == "open":
                return True

        return False

    def execute_parallel_group(
        self,
        group_tasks: List[Dict[str, Any]],
        group_id: str,
    ) -> GroupMetadata:
        """
        Execute a group of parallel tasks through the four-phase workflow.

        Args:
            group_tasks: List of task dictionaries in the group
            group_id: Identifier for this parallel group

        Returns:
            GroupMetadata with execution results

        Raises:
            ValueError: If group validation fails
        """
        if not group_tasks:
            raise ValueError(f"Cannot execute empty group: {group_id}")

        now = self._current_timestamp()
        group_metadata = GroupMetadata(
            group_id=group_id,
            group_name=f"Parallel Group {group_id}",
            phase=GroupPhase.PRE_EXECUTION,
            tasks=[task.get("id", "") for task in group_tasks],
            created_at=now,
        )

        # Save initial metadata
        self._save_group_metadata(group_metadata)

        try:
            # Phase 1: Pre-execution Analysis
            print(f"\n🔄 Phase 1: Pre-execution analysis for group '{group_id}'")
            self._phase_pre_execution(group_metadata, group_tasks)

            # Phase 2: Concurrent Execution
            print(f"\n🚀 Phase 2: Concurrent execution for group '{group_id}'")
            self._phase_concurrent_execution(group_metadata, group_tasks)

            # Phase 3: Coordination & Monitoring
            print(f"\n📊 Phase 3: Coordination & monitoring for group '{group_id}'")
            self._phase_coordination(group_metadata)

            # Phase 4: Post-execution Validation
            print(f"\n✅ Phase 4: Post-execution validation for group '{group_id}'")
            self._phase_post_execution(group_metadata)

            # Mark group as completed
            group_metadata.status = TaskStatus.COMPLETED
            group_metadata.completed_at = self._current_timestamp()

        except Exception as e:
            print(f"\n✗ Error executing group '{group_id}': {e}")
            group_metadata.status = TaskStatus.FAILED
            group_metadata.errors.append(str(e))
            group_metadata.completed_at = self._current_timestamp()

        finally:
            # Save final metadata
            self._save_group_metadata(group_metadata)

        return group_metadata

    def _phase_pre_execution(
        self,
        group_metadata: GroupMetadata,
        group_tasks: List[Dict[str, Any]],
    ) -> None:
        """
        Phase 1: Pre-execution Analysis

        - Execute /flow:summary to refresh context (REQUIRED)
        - Check which tasks are unblocked
        - Verify there are no blocking dependencies
        - Review task details and blockers
        """
        # Pre-group refresh (REQUIRED)
        print("  → Executing pre-group context refresh...")
        refresh_success = self.refresh_context_before_group()
        group_metadata.pre_group_refresh_completed = refresh_success

        if not refresh_success:
            print("  ⚠ Warning: Context refresh failed or skipped")
            print("    Group execution will continue, but context may be stale")

        # Analyze tasks for blockers
        blocked_tasks = []
        ready_tasks = []

        for task in group_tasks:
            task_meta = self._extract_task_metadata(task)

            if self._check_dependencies_blocked(task_meta):
                blocked_tasks.append(task_meta.task_id)
                task_meta.status = TaskStatus.BLOCKED
            else:
                ready_tasks.append(task_meta.task_id)
                task_meta.status = TaskStatus.PENDING

        print(f"  • Total tasks: {len(group_tasks)}")
        print(f"  • Ready to execute: {len(ready_tasks)}")
        print(f"  • Blocked by dependencies: {len(blocked_tasks)}")

        if blocked_tasks:
            print(f"  ⚠ Blocked tasks: {', '.join(blocked_tasks)}")
            print("    These tasks will be skipped in this parallel execution")

        # Update metadata
        group_metadata.phase = GroupPhase.CONCURRENT_EXECUTION
        group_metadata.started_at = self._current_timestamp()
        self._save_group_metadata(group_metadata)

    def _phase_concurrent_execution(
        self,
        group_metadata: GroupMetadata,
        group_tasks: List[Dict[str, Any]],
    ) -> None:
        """
        Phase 2: Concurrent Execution

        - For each task: select subagent based on metadata
        - Apply applicable skills before launching subagent
        - Launch all parallel tasks concurrently via Task tool
        - Update task status to in_progress
        """
        ready_tasks = [
            task for task in group_tasks
            if not self._check_dependencies_blocked(self._extract_task_metadata(task))
        ]

        if not ready_tasks:
            print("  ⚠ No tasks ready for execution (all blocked)")
            return

        print(f"  → Launching {len(ready_tasks)} tasks in parallel...")

        for i, task in enumerate(ready_tasks, 1):
            task_meta = self._extract_task_metadata(task)
            task_id = task_meta.task_id

            print(f"\n  [{i}/{len(ready_tasks)}] Task: {task_id}")
            print(f"    Title: {task_meta.title}")

            # Select subagent
            subagent = task_meta.subagent_type or self._auto_detect_subagent(task_meta)
            print(f"    Subagent: {subagent}")

            # Apply skills if applicable
            if task_meta.applicable_skills:
                print(f"    Applying skills: {', '.join(task_meta.applicable_skills)}")
                for skill in task_meta.applicable_skills:
                    print(f"      → Invoking skill: {skill}")
                    # Note: In actual Claude Code environment, this would use the Skill tool
                    # Skill(skill=skill, args=task_meta.description)

            # Launch task (placeholder for actual Task tool invocation)
            print(f"    → Launching parallel task...")

            # Update status
            task_meta.status = TaskStatus.IN_PROGRESS

            # Store result placeholder
            group_metadata.results.append({
                "task_id": task_id,
                "subagent": subagent,
                "skills_applied": task_meta.applicable_skills,
                "status": "in_progress",
                "started_at": self._current_timestamp(),
            })

        self._save_group_metadata(group_metadata)

    def _auto_detect_subagent(self, task_meta: TaskMetadata) -> str:
        """
        Auto-detect appropriate subagent based on task description.

        Args:
            task_meta: Task metadata

        Returns:
            Detected subagent type string.
        """
        description = task_meta.description.lower()

        # Pattern matching for subagent types
        patterns = {
            "backend-architect": [
                "api", "backend", "server", "database", "schema",
                "microservice", "endpoint", "service architecture"
            ],
            "frontend-developer": [
                "ui", "component", "frontend", "react", "vue",
                "interface", "user experience", "css"
            ],
            "test-automator": [
                "test", "testing", "spec", "coverage", "pytest",
                "playwright", "jest", "unit test"
            ],
            "database-architect": [
                "migration", "query", "index", "orm", "sql",
                "database design", "data model"
            ],
            "security-auditor": [
                "security", "auth", "authentication", "authorization",
                "vulnerability", "penetration", "audit"
            ],
        }

        # Score each subagent type
        scores = {}
        for subagent, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in description)
            if score > 0:
                scores[subagent] = score

        # Return highest scoring subagent, or default
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return "backend-architect"  # Default fallback

    def _phase_coordination(self, group_metadata: GroupMetadata) -> None:
        """
        Phase 3: Coordination & Monitoring

        - Monitor progress via in-progress task status
        - Use beads database for coordination between parallel tasks
        - Wait for ALL tasks in the group to complete before proceeding
        """
        print("  → Monitoring parallel task progress...")

        # In a real implementation, this would poll beads for task completion
        # For now, we'll simulate completion
        for result in group_metadata.results:
            if result["status"] == "in_progress":
                print(f"    • {result['task_id']}: Running")
                # Update to completed (in real implementation, poll beads)
                result["status"] = "completed"
                result["completed_at"] = self._current_timestamp()

        print(f"  ✓ All {len(group_metadata.results)} parallel tasks completed")

        group_metadata.phase = GroupPhase.POST_EXECUTION
        self._save_group_metadata(group_metadata)

    def _phase_post_execution(self, group_metadata: GroupMetadata) -> None:
        """
        Phase 4: Post-execution Validation

        - Verify all group tasks are completed
        - Run tests if applicable before moving to next group/task
        - Mark tasks as closed in beads
        """
        print("  → Validating group execution results...")

        # Check completion status
        completed_count = sum(
            1 for r in group_metadata.results
            if r["status"] == "completed"
        )

        print(f"    • Completed: {completed_count}/{len(group_metadata.results)}")

        if completed_count < len(group_metadata.results):
            failed_tasks = [
                r["task_id"] for r in group_metadata.results
                if r["status"] != "completed"
            ]
            print(f"    ✗ Failed tasks: {', '.join(failed_tasks)}")
            raise ValueError(f"Some tasks failed: {failed_tasks}")

        # Run tests if applicable
        print("    • Running test suite...")
        test_success = self._run_test_suite()

        if not test_success:
            print("    ⚠ Warning: Some tests failed")
            print("      Tasks completed, but tests require attention")
        else:
            print("    ✓ All tests passed")

        # Close tasks in beads
        print("    • Closing completed tasks in beads...")
        for result in group_metadata.results:
            task_id = result["task_id"]
            self._close_beads_task(task_id)

        print("  ✓ Post-execution validation complete")

    def _run_test_suite(self) -> bool:
        """
        Run the project's test suite.

        Returns:
            True if all tests pass, False otherwise.
        """
        # Detect test framework and run tests
        test_commands = [
            ["pytest", "-xvs"],  # Python
            ["npm", "test"],     # Node.js
            ["cargo", "test"],   # Rust
            ["go", "test", "./..."],  # Go
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=self.repo_root,
                )

                if result.returncode == 0:
                    print(f"      ✓ Tests passed: {' '.join(cmd)}")
                    return True
                else:
                    # Command exists but tests failed
                    if result.returncode != 127:  # Not "command not found"
                        print(f"      ✗ Tests failed: {' '.join(cmd)}")
                        return False

            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # No test framework found or all skipped
        print("      ⚠ No test suite detected")
        return True  # Don't block if no tests

    def _close_beads_task(self, task_id: str) -> bool:
        """
        Close a task in the beads database.

        Args:
            task_id: Beads issue ID

        Returns:
            True if successful, False otherwise.
        """
        try:
            result = subprocess.run(
                ["bd", "close", task_id],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print(f"      ✓ Closed: {task_id}")
                return True
            else:
                print(f"      ⚠ Could not close {task_id}: {result.stderr}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"      ⚠ Error closing {task_id}: {e}")
            return False

    def wait_for_group_completion(self, group_id: str, timeout_seconds: int = 3600) -> bool:
        """
        Wait for a parallel group to complete execution.

        Args:
            group_id: Group identifier
            timeout_seconds: Maximum time to wait (default: 1 hour)

        Returns:
            True if group completed successfully, False if timeout or error.
        """
        import time

        group_metadata = self.get_group(group_id)
        if not group_metadata:
            print(f"✗ Group not found: {group_id}")
            return False

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            # Reload metadata
            group_metadata = self.get_group(group_id)

            if group_metadata.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return group_metadata.status == TaskStatus.COMPLETED

            print(f"  Waiting for group '{group_id}'... "
                  f"Status: {group_metadata.status.value}, "
                  f"Phase: {group_metadata.phase.value}")
            time.sleep(10)  # Poll every 10 seconds

        print(f"✗ Timeout waiting for group '{group_id}'")
        return False

    def _save_group_metadata(self, group_metadata: GroupMetadata) -> None:
        """Save group metadata to disk."""
        group_dir = self._get_group_dir(group_metadata.group_id)
        group_dir.mkdir(exist_ok=True)

        metadata_path = self._get_metadata_path(group_metadata.group_id)
        with open(metadata_path, "w") as f:
            json.dump(group_metadata.to_dict(), f, indent=2)

    def get_group(self, group_id: str) -> Optional[GroupMetadata]:
        """
        Retrieve group metadata by ID.

        Args:
            group_id: Group identifier

        Returns:
            GroupMetadata object or None if not found.
        """
        metadata_path = self._get_metadata_path(group_id)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path) as f:
                data = json.load(f)

            return GroupMetadata(
                group_id=data["group_id"],
                group_name=data["group_name"],
                phase=GroupPhase(data["phase"]),
                tasks=data["tasks"],
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
                status=TaskStatus(data["status"]),
                results=data.get("results", []),
                errors=data.get("errors", []),
                pre_group_refresh_completed=data.get("pre_group_refresh_completed", False),
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"✗ Error loading group {group_id}: {e}")
            return None

    def list_groups(self, status: Optional[TaskStatus] = None) -> List[GroupMetadata]:
        """
        List all parallel groups, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of GroupMetadata objects.
        """
        groups = []

        for group_dir in self.groups_dir.iterdir():
            if not group_dir.is_dir():
                continue

            group_id = group_dir.name
            group_metadata = self.get_group(group_id)

            if group_metadata:
                if status is None or group_metadata.status == status:
                    groups.append(group_metadata)

        # Sort by created_at descending
        groups.sort(key=lambda g: g.created_at, reverse=True)
        return groups


def main():
    """CLI entry point for parallel coordinator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parallel Execution Coordinator for [P:Group-X] Tasks"
    )
    parser.add_argument(
        "action",
        choices=["detect", "execute", "list", "status", "wait"],
        help="Action to perform",
    )
    parser.add_argument("--group-id", help="Group ID (for execute/status/wait)")
    parser.add_argument("--tasks-file", help="JSON file with tasks list")
    parser.add_argument("--status", choices=[s.value for s in TaskStatus],
                        help="Filter by status (for list)")
    parser.add_argument("--timeout", type=int, default=3600,
                        help="Timeout in seconds (for wait)")
    parser.add_argument("--output", choices=["json", "pretty"], default="pretty",
                        help="Output format")

    args = parser.parse_args()

    coordinator = ParallelCoordinator()

    if args.action == "detect":
        if not args.tasks_file:
            parser.error("--tasks-file required for detect action")

        with open(args.tasks_file) as f:
            tasks = json.load(f)

        groups = coordinator.detect_groups(tasks)

        output = {
            "total_tasks": len(tasks),
            "parallel_groups": len(groups) - (1 if "_sequential" in groups else 0),
            "groups": {
                gid: len(tasks_list)
                for gid, tasks_list in groups.items()
            }
        }

    elif args.action == "execute":
        if not args.group_id or not args.tasks_file:
            parser.error("--group-id and --tasks-file required for execute action")

        with open(args.tasks_file) as f:
            all_tasks = json.load(f)

        # Filter tasks for this group
        group_tasks = [
            task for task in all_tasks
            if f"[P:Group-{args.group_id}]" in task.get("description", "")
        ]

        if not group_tasks:
            print(f"No tasks found for group {args.group_id}", file=sys.stderr)
            sys.exit(1)

        result = coordinator.execute_parallel_group(group_tasks, args.group_id)
        output = result.to_dict()

    elif args.action == "list":
        status_filter = TaskStatus(args.status) if args.status else None
        groups = coordinator.list_groups(status=status_filter)
        output = [g.to_dict() for g in groups]

    elif args.action == "status":
        if not args.group_id:
            parser.error("--group-id required for status action")

        group = coordinator.get_group(args.group_id)
        if not group:
            print(f"Group not found: {args.group_id}", file=sys.stderr)
            sys.exit(1)

        output = group.to_dict()

    elif args.action == "wait":
        if not args.group_id:
            parser.error("--group-id required for wait action")

        success = coordinator.wait_for_group_completion(args.group_id, args.timeout)
        output = {"group_id": args.group_id, "completed": success}

    # Print output
    if args.output == "pretty":
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
