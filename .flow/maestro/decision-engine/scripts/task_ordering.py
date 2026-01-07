#!/usr/bin/env python3
"""
Task ordering with dependency resolution for autonomous execution.

Implements intelligent task sequencing based on dependency graph analysis,
parallel execution detection, and priority-based ordering strategies.
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any, Optional


# Priority mapping (lower number = higher priority)
PRIORITY_MAP = {
    0: "P0",  # Critical
    1: "P1",  # High
    2: "P2",  # Normal
    3: "P3",  # Low
    4: "P4",  # Lowest
}


def get_beads_issues() -> List[Dict]:
    """Get all open issues from beads database."""
    try:
        result = subprocess.run(
            ["bd", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            issues = json.loads(result.stdout)
            # Filter only open issues
            return [issue for issue in issues if issue.get("status") == "open"]
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error getting beads issues: {e}", file=sys.stderr)
    return []


def get_issue_details(issue_id: str) -> Dict:
    """Get detailed information for a specific issue."""
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
                data = data[0]
            return {
                "id": data.get("id"),
                "title": data.get("title"),
                "description": data.get("description", ""),
                "status": data.get("status"),
                "type": data.get("issue_type"),
                "priority": data.get("priority", 2),
                "labels": data.get("labels", []),
                "parent": data.get("parent"),
                # Extract dependencies
                "depends_on": _extract_dependencies(data),
                "blocks": data.get("blocks", []),
                "children": data.get("children", []),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error getting issue details for {issue_id}: {e}", file=sys.stderr)
    return {}


def _extract_dependencies(issue_data: Dict) -> List[str]:
    """Extract dependency IDs from issue data."""
    deps = []
    dependencies = issue_data.get("dependencies", [])
    for dep in dependencies:
        if isinstance(dep, dict):
            dep_id = dep.get("id")
            if dep_id and dep.get("dependency_type") != "parent-child":
                deps.append(dep_id)
    return deps


class TaskOrderingEngine:
    """Engine for ordering tasks based on dependencies and priorities."""

    def __init__(self, strategy: str = "topological"):
        self.strategy = strategy
        self.graph = {
            "nodes": [],  # All task IDs
            "edges": [],  # (dep_id, task_id) tuples
            "adj": defaultdict(list),  # adjacency list
            "reverse_adj": defaultdict(list),  # reverse adjacency
            "tasks": {},  # task_id -> task details
        }
        self.priority_groups = defaultdict(set)  # priority -> task_ids

    def load_from_beads(self, issues: Optional[List[Dict]] = None) -> None:
        """Load tasks from beads issues."""
        if issues is None:
            issues = get_beads_issues()

        for issue in issues:
            issue_id = issue.get("id")
            if not issue_id:
                continue

            self.graph["tasks"][issue_id] = {
                "id": issue_id,
                "title": issue.get("title", ""),
                "type": issue.get("issue_type", "task"),
                "priority": issue.get("priority", 2),
                "labels": issue.get("labels", []),
                "parent": issue.get("parent"),
            }

            self.graph["nodes"].append(issue_id)
            self.priority_groups[issue.get("priority", 2)].add(issue_id)

            # Get dependencies
            details = get_issue_details(issue_id)
            if details:
                depends_on = details.get("depends_on", [])
                self.graph["tasks"][issue_id]["depends_on"] = depends_on

                for dep_id in depends_on:
                    self.graph["edges"].append((dep_id, issue_id))
                    self.graph["adj"][dep_id].append(issue_id)
                    self.graph["reverse_adj"][issue_id].append(dep_id)

    def detect_conflicts(self) -> Set[Tuple[str, str]]:
        """
        Detect tasks that conflict (should not run in parallel).

        Tasks conflict if they modify the same resources.
        This is a simplified version - real implementation would parse file paths.
        """
        conflicts = set()

        # Simple heuristic: tasks with similar titles in same epic might conflict
        for i, task1 in enumerate(self.graph["nodes"]):
            for task2 in self.graph["nodes"][i+1:]:
                t1 = self.graph["tasks"][task1]
                t2 = self.graph["tasks"][task2]

                # Check if same parent (epic)
                if t1.get("parent") and t1["parent"] == t2.get("parent"):
                    # Check for similar keywords suggesting same resource
                    keywords = ["schema", "api", "ui", "service", "model"]
                    t1_words = set(t1["title"].lower().split())
                    t2_words = set(t2["title"].lower().split())

                    common = t1_words & t2_words & set(keywords)
                    if common:
                        conflicts.add((task1, task2))

        return conflicts

    def topological_sort(self) -> List[List[str]]:
        """
        Perform topological sort with parallel group detection.

        Returns:
            List of groups, where each group is a list of tasks that can run in parallel.
        """
        in_degree = {node: 0 for node in self.graph["nodes"]}

        # Calculate in-degrees
        for src, dst in self.graph["edges"]:
            in_degree[dst] += 1

        # Initialize queue with nodes having no dependencies
        queue = deque([node for node in self.graph["nodes"] if in_degree[node] == 0])
        groups = []
        seen = set()

        while queue:
            # All tasks in current queue can run in parallel
            current_group = list(queue)
            groups.append(current_group)
            seen.update(current_group)
            queue.clear()

            # Update in-degrees for dependent tasks
            for task in current_group:
                for neighbor in self.graph["adj"].get(task, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0 and neighbor not in seen:
                        queue.append(neighbor)

        return groups

    def risk_first_ordering(self) -> List[List[str]]:
        """
        Order tasks by priority first, then topological sort within each priority.

        Returns:
            List of groups, where each group is a list of tasks that can run in parallel.
        """
        # Get tasks sorted by priority (0 = highest priority)
        prioritized_tasks = []
        for priority in sorted(PRIORITY_MAP.keys()):
            tasks = list(self.priority_groups.get(priority, set()))
            prioritized_tasks.extend([(priority, task) for task in tasks])

        groups = []
        processed = set()

        # Process each priority level
        for priority, task in prioritized_tasks:
            if task in processed:
                continue

            # Build subgraph of unprocessed tasks at this or higher priority
            unprocessed_at_level = [
                t for p, t in prioritized_tasks
                if t not in processed and p <= priority
            ]

            # Find tasks that can run now (dependencies satisfied)
            ready_tasks = []
            for t in unprocessed_at_level:
                deps = self.graph["tasks"][t].get("depends_on", [])
                if all(dep in processed for dep in deps):
                    ready_tasks.append(t)

            if ready_tasks:
                groups.append(ready_tasks)
                processed.update(ready_tasks)

        return groups

    def foundational_first_ordering(self) -> List[List[str]]:
        """
        Order tasks with foundational elements first.

        Foundational tasks are identified by keywords: schema, core, base, init.

        Returns:
            List of groups, where each group is a list of tasks that can run in parallel.
        """
        foundation_keywords = ["schema", "core", "base", "init", "setup", "config"]

        # Categorize tasks
        foundational = []
        non_foundational = []

        for task_id in self.graph["nodes"]:
            task = self.graph["tasks"][task_id]
            title_lower = task["title"].lower()

            if any(kw in title_lower for kw in foundation_keywords):
                foundational.append(task_id)
            else:
                non_foundational.append(task_id)

        # Get topological order
        topo_groups = self.topological_sort()

        # Reorder to prioritize foundational tasks
        reordered = []
        seen = set()

        # First pass: foundational tasks in topological order
        for group in topo_groups:
            foundational_in_group = [t for t in group if t in foundational and t not in seen]
            if foundational_in_group:
                reordered.append(foundational_in_group)
                seen.update(foundational_in_group)

        # Second pass: remaining tasks
        for group in topo_groups:
            remaining = [t for t in group if t not in seen]
            if remaining:
                reordered.append(remaining)
                seen.update(remaining)

        return reordered

    def parallel_maximizing_ordering(self) -> List[List[str]]:
        """
        Maximize parallel execution by finding largest independent sets.

        Returns:
            List of groups, where each group is a list of tasks that can run in parallel.
        """
        # This is essentially the topological sort approach
        # which already maximizes parallelism at each level
        return self.topological_sort()

    def detect_file_conflicts(self, task1: str, task2: str) -> bool:
        """
        Detect if two tasks modify the same files.

        This parses task descriptions to extract file paths.
        Returns True if conflicts detected.
        """
        t1 = self.graph["tasks"][task1]
        t2 = self.graph["tasks"][task2]

        # Extract file paths from description
        import re

        def extract_files(description: str) -> Set[str]:
            # Match markdown code blocks with file paths
            pattern = r'`([^`]+\.(?:ts|js|py|go|rs|java|md))`'
            return set(re.findall(pattern, description))

        files1 = extract_files(t1.get("title", "") + " " + t1.get("description", ""))
        files2 = extract_files(t2.get("title", "") + " " + t2.get("description", ""))

        # Check for overlap
        return bool(files1 & files2)

    def apply_conflict_resolution(self, groups: List[List[str]]) -> List[List[str]]:
        """
        Split parallel groups that have conflicting tasks.

        Returns:
            List of groups with conflicts resolved.
        """
        resolved = []

        for group in groups:
            # Build conflict graph within group
            conflict_graph = {task: set() for task in group}

            for i, t1 in enumerate(group):
                for t2 in group[i+1:]:
                    if self.detect_file_conflicts(t1, t2):
                        conflict_graph[t1].add(t2)
                        conflict_graph[t2].add(t1)

            # Greedy coloring to separate conflicting tasks
            colors = {}  # task -> color (group index)
            color_groups = defaultdict(list)

            for task in group:
                used_colors = {colors[conflict] for conflict in conflict_graph[task] if conflict in colors}

                # Find first available color
                color = 0
                while color in used_colors:
                    color += 1

                colors[task] = color
                color_groups[color].append(task)

            # Add colored groups (now conflict-free)
            for color in sorted(color_groups.keys()):
                if color_groups[color]:
                    resolved.append(color_groups[color])

        return resolved

    def compute_ordering(self, detect_conflicts: bool = True) -> Dict[str, Any]:
        """
        Compute task ordering based on selected strategy.

        Args:
            detect_conflicts: Whether to detect and resolve file conflicts

        Returns:
            Dictionary with ordering results and metadata.
        """
        # Apply strategy
        if self.strategy == "topological":
            groups = self.topological_sort()
        elif self.strategy == "risk_first":
            groups = self.risk_first_ordering()
        elif self.strategy == "foundational_first":
            groups = self.foundational_first_ordering()
        elif self.strategy == "parallel_maximizing":
            groups = self.parallel_maximizing_ordering()
        else:
            groups = self.topological_sort()

        # Resolve conflicts if requested
        if detect_conflicts:
            groups = self.apply_conflict_resolution(groups)

        # Build rationale
        rationale = self._build_rationale(groups)

        # Format output
        return {
            "strategy": self.strategy,
            "sequence": groups,
            "rationale": rationale,
            "total_tasks": len(self.graph["nodes"]),
            "total_groups": len(groups),
            "parallelizable_groups": sum(1 for g in groups if len(g) > 1),
            "critical_path_length": len(groups),
            "tasks": self.graph["tasks"],
        }

    def _build_rationale(self, groups: List[List[str]]) -> str:
        """Build human-readable rationale for the ordering."""
        lines = [f"Strategy: {self.strategy}", ""]

        for i, group in enumerate(groups, 1):
            if len(group) == 1:
                task_id = group[0]
                task = self.graph["tasks"][task_id]
                priority = PRIORITY_MAP.get(task.get("priority", 2), "P2")
                lines.append(f"Group {i}: [{task_id}] {task['title']} ({priority}) - sequential")
            else:
                lines.append(f"Group {i}: [P:Group-{i}] {len(group)} parallel tasks")
                for task_id in group:
                    task = self.graph["tasks"][task_id]
                    priority = PRIORITY_MAP.get(task.get("priority", 2), "P2")
                    lines.append(f"  - {task_id}: {task['title']} ({priority})")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Order tasks based on dependency analysis"
    )
    parser.add_argument(
        "--strategy",
        choices=["topological", "risk_first", "foundational_first", "parallel_maximizing"],
        default="topological",
        help="Ordering strategy to use",
    )
    parser.add_argument(
        "--no-conflicts",
        action="store_true",
        help="Skip conflict detection",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    args = parser.parse_args()

    # Load and order tasks
    engine = TaskOrderingEngine(strategy=args.strategy)
    engine.load_from_beads()

    if not engine.graph["nodes"]:
        print("No tasks found.", file=sys.stderr)
        sys.exit(1)

    result = engine.compute_ordering(detect_conflicts=not args.no_conflicts)

    if args.output_format == "json":
        # Add task details to output
        result["tasks"] = engine.graph["tasks"]
        print(json.dumps(result, indent=2))
    else:
        print(result["rationale"])
        print(f"\nTotal tasks: {result['total_tasks']}")
        print(f"Total groups: {result['total_groups']}")
        print(f"Parallelizable groups: {result['parallelizable_groups']}")


if __name__ == "__main__":
    main()
