#!/usr/bin/env python3
"""
Example usage of Parallel Execution Coordinator

Demonstrates how to use the ParallelCoordinator to execute [P:Group-X] marked tasks
through the four-phase workflow: Pre-execution, Concurrent Execution, Coordination,
and Post-execution.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parallel_coordinator import ParallelCoordinator, TaskStatus


def example_detect_groups():
    """Example 1: Detect parallel groups from task descriptions."""
    print("=" * 60)
    print("Example 1: Detecting [P:Group-X] markers")
    print("=" * 60)

    coordinator = ParallelCoordinator()

    # Sample tasks with [P:Group-X] markers
    tasks = [
        {
            "id": "proj-auth.1",
            "title": "Setup Database",
            "description": "[P:Group-infrastructure] Configure PostgreSQL database",
        },
        {
            "id": "proj-auth.2",
            "title": "Setup Redis",
            "description": "[P:Group-infrastructure] Configure Redis caching",
        },
        {
            "id": "proj-auth.3",
            "title": "Implement Login",
            "description": "[P:Group-auth] Create login endpoint",
        },
        {
            "id": "proj-auth.4",
            "title": "Implement Logout",
            "description": "[P:Group-auth] Create logout endpoint",
        },
        {
            "id": "proj-auth.5",
            "title": "Write Documentation",
            "description": "Document authentication flow (sequential)",
        },
    ]

    # Detect groups
    groups = coordinator.detect_groups(tasks)

    print("\nDetected Groups:")
    for group_id, group_tasks in groups.items():
        if group_id == "_sequential":
            print(f"\n📋 Sequential Tasks ({len(group_tasks)}):")
        else:
            print(f"\n🔄 Parallel Group '{group_id}' ({len(group_tasks)} tasks):")

        for task in group_tasks:
            print(f"  • {task['id']}: {task.get('title', 'No title')}")

    print(f"\n📊 Summary:")
    print(f"  • Total tasks: {len(tasks)}")
    print(f"  • Parallel groups: {len(groups) - (1 if '_sequential' in groups else 0)}")
    print(f"  • Sequential tasks: {len(groups.get('_sequential', []))}")


def example_execute_parallel_group():
    """Example 2: Execute a parallel group."""
    print("\n" + "=" * 60)
    print("Example 2: Executing a Parallel Group")
    print("=" * 60)

    coordinator = ParallelCoordinator()

    # Sample tasks for a parallel group
    group_tasks = [
        {
            "id": "proj-auth.3",
            "title": "Implement Login",
            "description": "[P:Group-auth] Create POST /api/auth/login endpoint with JWT",
        },
        {
            "id": "proj-auth.4",
            "title": "Implement Logout",
            "description": "[P:Group-auth] Create POST /api/auth/logout endpoint",
        },
        {
            "id": "proj-auth.5",
            "title": "Implement Refresh",
            "description": "[P:Group-auth] Create POST /api/auth/refresh endpoint",
        },
    ]

    print(f"\n🚀 Executing parallel group 'auth' with {len(group_tasks)} tasks...")

    # Note: In actual usage, this would:
    # - Execute /flow:summary for context refresh
    # - Launch tasks via Task tool with parallel invocations
    # - Monitor progress via beads database
    # - Run tests and close tasks

    # For demonstration, we'll show the metadata structure
    print("\n📋 Execution Plan:")
    for task in group_tasks:
        print(f"\n  Task: {task['id']}")
        print(f"  Title: {task['title']}")

        # Auto-detect subagent
        from parallel_coordinator import TaskMetadata
        task_meta = coordinator._extract_task_metadata(task)
        subagent = coordinator._auto_detect_subagent(task_meta)
        print(f"  Subagent: {subagent}")

        # Extract relevant files
        files = coordinator._extract_relevant_files(task['description'])
        if files:
            print(f"  Files: {', '.join(files)}")


def example_task_metadata_extraction():
    """Example 3: Extract task metadata."""
    print("\n" + "=" * 60)
    print("Example 3: Task Metadata Extraction")
    print("=" * 60)

    coordinator = ParallelCoordinator()

    tasks = [
        {
            "id": "proj-ui.1",
            "title": "Create Login Component",
            "description": """
            Implement React login component with TypeScript.

            Files to modify:
            - src/components/Login.tsx
            - src/types/auth.ts
            - src/services/AuthService.ts

            Requirements:
            - Email/password inputs
            - Form validation
            - Error handling
            - Loading states
            """,
        },
        {
            "id": "proj-ui.2",
            "title": "Create Dashboard Component",
            "description": """
            Create dashboard layout component with navigation.

            Relevant files:
            - src/components/Dashboard.tsx
            - src/components/Navigation.tsx
            """,
        },
    ]

    for task in tasks:
        print(f"\n📝 Task: {task['id']}")
        print(f"  Title: {task['title']}")

        task_meta = coordinator._extract_task_metadata(task)

        print(f"  Description: {task_meta.description[:100]}...")

        if task_meta.relevant_files:
            print(f"  Relevant Files:")
            for file in task_meta.relevant_files:
                print(f"    • {file}")


def example_subagent_detection():
    """Example 4: Automatic subagent detection."""
    print("\n" + "=" * 60)
    print("Example 4: Automatic Subagent Detection")
    print("=" * 60)

    coordinator = ParallelCoordinator()

    test_cases = [
        ("Backend API Task", "Design RESTful API endpoints for user management"),
        ("Frontend UI Task", "Create React components for user interface with CSS"),
        ("Testing Task", "Write comprehensive pytest tests with coverage"),
        ("Security Task", "Audit authentication system for vulnerabilities"),
        ("Database Task", "Design database schema with proper indexes"),
        ("Generic Task", "Implement feature X"),
    ]

    print("\n🤖 Subagent Detection Results:")
    for name, description in test_cases:
        from parallel_coordinator import TaskMetadata
        task_meta = TaskMetadata(
            task_id="test",
            title=name,
            description=description,
        )
        subagent = coordinator._auto_detect_subagent(task_meta)
        print(f"\n  {name}:")
        print(f"    Description: {description[:60]}...")
        print(f"    Detected: {subagent}")


def example_group_workflow():
    """Example 5: Complete workflow with state tracking."""
    print("\n" + "=" * 60)
    print("Example 5: Complete Group Execution Workflow")
    print("=" * 60)

    coordinator = ParallelCoordinator()

    print("\n📊 Four-Phase Workflow:")
    print("\n  Phase 1: Pre-execution Analysis")
    print("    • Execute /flow:summary to refresh context (REQUIRED)")
    print("    • Check which tasks are unblocked")
    print("    • Verify there are no blocking dependencies")
    print("    • Review task details and blockers")

    print("\n  Phase 2: Concurrent Execution")
    print("    • Select subagent for each task")
    print("    • Apply applicable skills before launching")
    print("    • Launch all parallel tasks concurrently")
    print("    • Update task status to in_progress")

    print("\n  Phase 3: Coordination & Monitoring")
    print("    • Monitor progress via in-progress task status")
    print("    • Use beads database for coordination")
    print("    • Wait for ALL tasks in the group to complete")

    print("\n  Phase 4: Post-execution Validation")
    print("    • Verify all group tasks are completed")
    print("    • Run tests if applicable")
    print("    • Mark tasks as closed in beads")

    print("\n📁 Group Metadata Persistence:")
    print("  • Stored in: .flow/maestro/parallel_groups/<group-id>/metadata.json")
    print("  • Tracks: phase, status, tasks, results, errors")
    print("  • Enables: recovery, monitoring, debugging")


def example_cli_usage():
    """Example 6: Command-line interface usage."""
    print("\n" + "=" * 60)
    print("Example 6: CLI Usage")
    print("=" * 60)

    print("\n🖥️  Available Commands:")
    print("\n  1. Detect groups from tasks file:")
    print("     $ python parallel_coordinator.py detect --tasks-file tasks.json")

    print("\n  2. Execute a parallel group:")
    print("     $ python parallel_coordinator.py execute \\")
    print("         --group-id infrastructure \\")
    print("         --tasks-file tasks.json")

    print("\n  3. List all parallel groups:")
    print("     $ python parallel_coordinator.py list --status pending")

    print("\n  4. Get group status:")
    print("     $ python parallel_coordinator.py status --group-id infrastructure")

    print("\n  5. Wait for group completion:")
    print("     $ python parallel_coordinator.py wait \\")
    print("         --group-id infrastructure \\")
    print("         --timeout 3600")

    print("\n📝 Tasks file format (tasks.json):")
    print(json.dumps(
        [
            {
                "id": "proj-auth.1",
                "title": "Setup Database",
                "description": "[P:Group-infra] Configure PostgreSQL",
            },
            {
                "id": "proj-auth.2",
                "title": "Setup Redis",
                "description": "[P:Group-infra] Configure Redis",
            },
        ],
        indent=2
    ))


def example_integration_with_beads():
    """Example 7: Integration with beads task tracking."""
    print("\n" + "=" * 60)
    print("Example 7: Integration with Beads")
    print("=" * 60)

    print("\n🔗 Beads Integration Points:")
    print("\n  1. Task Metadata:")
    print("     • subagent_type: Primary subagent for task")
    print("     • fallback_agents: Alternative subagents")
    print("     • applicable_skills: Skills to apply before execution")

    print("\n  2. Dependency Tracking:")
    print("     • Checks dependency status before execution")
    print("     • Blocks execution if dependencies are open")
    print("     • Updates beads after task completion")

    print("\n  3. Status Coordination:")
    print("     • Monitors task status via beads database")
    print("     • Coordinates parallel tasks via shared state")
    print("     • Closes tasks via 'bd close <task-id>'")

    print("\n📋 Example beads metadata:")
    print(json.dumps(
        {
            "id": "proj-auth.1",
            "metadata": {
                "subagent_type": "backend-architect",
                "fallback_agents": ["database-architect"],
                "applicable_skills": ["mcp-builder"],
            },
            "dependencies": [
                {"id": "proj-auth.0", "dependency_type": "blocks"}
            ],
            "status": "open",
        },
        indent=2
    ))


def main():
    """Run all examples."""
    examples = [
        example_detect_groups,
        example_execute_parallel_group,
        example_task_metadata_extraction,
        example_subagent_detection,
        example_group_workflow,
        example_cli_usage,
        example_integration_with_beads,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples Complete")
    print("=" * 60)
    print("\n💡 For more information, see:")
    print("  • .claude/commands/flow/implement.md (Parallel execution workflow)")
    print("  • .flow/maestro/scripts/parallel_coordinator.py (Implementation)")
    print("  • .flow/maestro/scripts/test_parallel_coordinator.py (Tests)")


if __name__ == "__main__":
    main()
