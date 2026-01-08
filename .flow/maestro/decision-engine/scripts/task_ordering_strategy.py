#!/usr/bin/env python3
"""
Task Ordering Strategy for Parallel Execution

Implements intelligent task sequencing to maximize parallel execution
while respecting dependencies. Uses topological sort with parallel group
detection and critical path optimization.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Set, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, "/home/ll931217/GitHub/dotfiles.feat-orchestrate-flow/.flow/maestro/decision-engine/scripts")

from decision_strategy import DecisionStrategy, DecisionContext, Decision


@dataclass
class TaskDependency:
    """
    Represents a task with its dependencies.

    Attributes:
        task_id: Unique identifier for the task
        depends_on: List of task IDs this task depends on
        priority: Task priority (0=highest, 4=lowest)
    """
    task_id: str
    depends_on: List[str] = field(default_factory=list)
    priority: int = 2


@dataclass
class OrderedTask:
    """
    Represents a task in the execution order.

    Attributes:
        task_id: Unique identifier for the task
        group: Parallel group identifier (e.g., "Group-1", "Group-2")
        order: Execution order (lower numbers execute first)
        dependencies: List of task IDs this task depends on
    """
    task_id: str
    group: str
    order: int
    dependencies: List[str] = field(default_factory=list)

    def is_parallel(self) -> bool:
        """Check if this task is part of a parallel group."""
        return self.group.startswith("Group-")

    def get_group_marker(self) -> str:
        """Get the [P:Group-N] marker for this task."""
        return f"[P:{self.group}]" if self.is_parallel() else ""


class TaskOrderingStrategy(DecisionStrategy):
    """
    Strategy for ordering tasks to maximize parallel execution.

    This strategy analyzes task dependencies and creates an optimal execution
    plan that:
    - Groups independent tasks for parallel execution
    - Orders dependent tasks sequentially
    - Minimizes critical path length
    - Uses [P:Group-N] markers for parallel groups

    Example:
        Input tasks: [A, B(depends_on=A), C, D(depends_on=B,C)]

        Output:
        - Group-1: [A, C] (parallel, no dependencies)
        - Group-2: [B] (sequential, depends on A)
        - Group-3: [D] (sequential, depends on B and C)
    """

    def decide(self, context: DecisionContext) -> Decision:
        """
        Order tasks for optimal parallel execution.

        Args:
            context: Decision context containing:
                - prd_requirements: Task list and dependencies
                - current_state: Current execution state
                - available_options: Optional task data
                - constraints: Execution constraints

        Returns:
            Decision with ordered task list and group assignments

        Raises:
            ValueError: If context is invalid or tasks have circular dependencies
            RuntimeError: If ordering cannot be computed
        """
        # Validate context
        self.validate_context(context)

        # Extract tasks from context
        tasks = self._extract_tasks(context)

        if not tasks:
            raise ValueError("No tasks found in context")

        # Build dependency graph
        graph = self._build_dependency_graph(tasks)

        # Check for circular dependencies
        if self._has_circular_dependencies(graph):
            raise ValueError("Tasks have circular dependencies, cannot order")

        # Perform topological sort with parallel group detection
        ordered_tasks = self._topological_sort_with_groups(graph, tasks)

        # Minimize critical path
        ordered_tasks = self._minimize_critical_path(ordered_tasks, graph)

        # Calculate confidence
        confidence = self._calculate_confidence(graph, ordered_tasks)

        # Build rationale
        rationale = self._build_rationale(ordered_tasks, graph)

        # Format choice as JSON string of ordered tasks
        import json
        choice = json.dumps([t.__dict__ for t in ordered_tasks])

        # Extract alternatives (task IDs that could be reordered)
        alternatives = self._get_alternatives(tasks)

        return Decision(
            choice=choice,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
            context_snapshot=context.to_dict(),
            decision_type="task_ordering",
            metadata={
                "total_tasks": len(tasks),
                "total_groups": len(set(t.group for t in ordered_tasks)),
                "parallel_groups": len(set(t.group for t in ordered_tasks if t.is_parallel())),
                "critical_path_length": max(t.order for t in ordered_tasks) + 1,
            }
        )

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "task_ordering_parallel_maximizer"

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return "Orders tasks to maximize parallel execution using topological sort and dependency analysis"

    def get_supported_decision_types(self) -> List[str]:
        """Return supported decision types."""
        return ["task_ordering", "execution_plan", "parallelization"]

    def validate_context(self, context: DecisionContext) -> bool:
        """
        Validate context has required data.

        Args:
            context: Context to validate

        Returns:
            True if valid

        Raises:
            ValueError: If context is invalid
        """
        if not context:
            raise ValueError("Context cannot be None")

        # Check for task data in prd_requirements
        if "tasks" not in context.prd_requirements and "task_list" not in context.prd_requirements:
            # Try to get tasks from metadata
            if not context.metadata.get("tasks"):
                raise ValueError("Context must contain 'tasks' in prd_requirements or metadata")

        return True

    def _extract_tasks(self, context: DecisionContext) -> List[TaskDependency]:
        """
        Extract task list from context.

        Args:
            context: Decision context

        Returns:
            List of TaskDependency objects
        """
        # Try multiple sources for task data
        tasks_data = (
            context.prd_requirements.get("tasks") or
            context.prd_requirements.get("task_list") or
            context.metadata.get("tasks") or
            []
        )

        if not tasks_data:
            # Try available_options
            for option in context.available_options:
                if "tasks" in option:
                    tasks_data = option["tasks"]
                    break

        if not tasks_data:
            return []

        # Convert to TaskDependency objects
        tasks = []
        for task_data in tasks_data:
            if isinstance(task_data, dict):
                task = TaskDependency(
                    task_id=task_data.get("id") or task_data.get("task_id", ""),
                    depends_on=task_data.get("depends_on", task_data.get("dependencies", [])),
                    priority=task_data.get("priority", 2)
                )
            elif isinstance(task_data, str):
                # Simple task ID string
                task = TaskDependency(task_id=task_data)
            else:
                continue

            if task.task_id:
                tasks.append(task)

        return tasks

    def _build_dependency_graph(
        self,
        tasks: List[TaskDependency]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build dependency graph from task list.

        Args:
            tasks: List of tasks with dependencies

        Returns:
            Dictionary with graph structure:
            {
                "nodes": List[str],  # All task IDs
                "edges": List[Tuple[str, str]],  # (dep_id, task_id)
                "adj": Dict[str, List[str]],  # adjacency list
                "tasks": Dict[str, TaskDependency],  # task_id -> task
            }
        """
        graph = {
            "nodes": [],
            "edges": [],
            "adj": defaultdict(list),
            "tasks": {},
        }

        for task in tasks:
            graph["nodes"].append(task.task_id)
            graph["tasks"][task.task_id] = task

            for dep_id in task.depends_on:
                graph["edges"].append((dep_id, task.task_id))
                graph["adj"][dep_id].append(task.task_id)

        return graph

    def _has_circular_dependencies(self, graph: Dict[str, Dict[str, Any]]) -> bool:
        """
        Detect circular dependencies using DFS.

        Args:
            graph: Dependency graph

        Returns:
            True if circular dependencies exist
        """
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph["adj"].get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph["nodes"]:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def _topological_sort_with_groups(
        self,
        graph: Dict[str, Dict[str, Any]],
        tasks: List[TaskDependency]
    ) -> List[OrderedTask]:
        """
        Perform topological sort with parallel group detection.

        Groups tasks at each level of the dependency graph. Tasks with
        all dependencies satisfied can run in parallel.

        Args:
            graph: Dependency graph
            tasks: Original task list

        Returns:
            List of OrderedTask objects with group assignments
        """
        # Calculate in-degrees (only count dependencies that exist in graph)
        in_degree = {node: 0 for node in graph["nodes"]}
        for src, dst in graph["edges"]:
            # Only count edge if source exists in graph
            if src in graph["nodes"]:
                in_degree[dst] += 1

        # Initialize queue with nodes having no (or only missing) dependencies
        queue = deque([node for node in graph["nodes"] if in_degree[node] == 0])

        ordered_tasks = []
        group_number = 1
        seen = set()

        while queue:
            # All tasks in current queue can run in parallel
            current_group = list(queue)

            # Create ordered tasks for this group
            for task_id in current_group:
                task = graph["tasks"][task_id]
                ordered_task = OrderedTask(
                    task_id=task_id,
                    group=f"Group-{group_number}" if len(current_group) > 1 else f"Sequential-{group_number}",
                    order=len(ordered_tasks),
                    dependencies=task.depends_on.copy()
                )
                ordered_tasks.append(ordered_task)
                seen.add(task_id)

            # Clear queue and update in-degrees
            queue.clear()

            # Update in-degrees for dependent tasks
            for task_id in current_group:
                for neighbor in graph["adj"].get(task_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0 and neighbor not in seen:
                        queue.append(neighbor)

            group_number += 1

        return ordered_tasks

    def _minimize_critical_path(
        self,
        ordered_tasks: List[OrderedTask],
        graph: Dict[str, Dict[str, Any]]
    ) -> List[OrderedTask]:
        """
        Minimize critical path by reordering parallel groups.

        Tasks on the critical path (longest dependency chain) should be
        prioritized within parallel groups.

        Args:
            ordered_tasks: Current ordered tasks
            graph: Dependency graph

        Returns:
            Optimized list of ordered tasks
        """
        # Calculate task depths (distance from start)
        depths = self._calculate_task_depths(graph)

        # Sort within each group by depth (deeper tasks first)
        group_tasks = defaultdict(list)
        for task in ordered_tasks:
            group_tasks[task.group].append(task)

        optimized = []
        current_order = 0

        # Process groups in order
        for group in sorted(group_tasks.keys(), key=lambda g: ordered_tasks[next(
            i for i, t in enumerate(ordered_tasks) if t.group == g
        )].order):
            tasks = group_tasks[group]

            if len(tasks) == 1:
                # Sequential task
                tasks[0].order = current_order
                optimized.append(tasks[0])
            else:
                # Parallel group - sort by depth
                tasks.sort(key=lambda t: depths.get(t.task_id, 0), reverse=True)
                for i, task in enumerate(tasks):
                    task.order = current_order + i
                    optimized.append(task)

            current_order += len(tasks)

        return optimized

    def _calculate_task_depths(
        self,
        graph: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Calculate the depth of each task in the dependency graph.

        Depth is the length of the longest path from any root to this task.

        Args:
            graph: Dependency graph

        Returns:
            Dictionary mapping task_id -> depth
        """
        # Build reverse adjacency
        reverse_adj = defaultdict(list)
        for src, dst in graph["edges"]:
            reverse_adj[dst].append(src)

        # Calculate depths using topological order
        in_degree = {node: 0 for node in graph["nodes"]}
        for src, dst in graph["edges"]:
            in_degree[dst] += 1

        queue = deque([node for node in graph["nodes"] if in_degree[node] == 0])
        depths = {node: 0 for node in graph["nodes"]}

        while queue:
            node = queue.popleft()

            for neighbor in graph["adj"].get(node, []):
                # Update depth
                depths[neighbor] = max(depths[neighbor], depths[node] + 1)

                # Update in-degree
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return depths

    def _calculate_confidence(
        self,
        graph: Dict[str, Dict[str, Any]],
        ordered_tasks: List[OrderedTask]
    ) -> float:
        """
        Calculate confidence in the ordering.

        Higher confidence when:
        - Many parallel groups found (good parallelization)
        - Few sequential tasks (efficient execution)
        - No circular dependencies (valid ordering)

        Args:
            graph: Dependency graph
            ordered_tasks: Ordered task list

        Returns:
            Confidence score from 0.0 to 1.0
        """
        # Base confidence
        confidence = 0.8

        # Boost for parallel groups
        parallel_groups = len(set(t.group for t in ordered_tasks if t.is_parallel()))
        if parallel_groups > 0:
            confidence += min(0.1 * parallel_groups, 0.2)

        # Penalty for mostly sequential execution
        sequential_ratio = len([t for t in ordered_tasks if not t.is_parallel()]) / len(ordered_tasks)
        if sequential_ratio > 0.7:
            confidence -= 0.1

        # Ensure within bounds
        return max(0.0, min(1.0, confidence))

    def _build_rationale(
        self,
        ordered_tasks: List[OrderedTask],
        graph: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Build human-readable rationale for the ordering.

        Args:
            ordered_tasks: Ordered task list
            graph: Dependency graph

        Returns:
            Rationale string
        """
        lines = [
            "Task Ordering Strategy: Parallel Maximization",
            "",
            "Groups tasks by dependency level to maximize parallel execution.",
            ""

        ]

        # Group by execution order
        groups = defaultdict(list)
        for task in ordered_tasks:
            groups[task.order].append(task)

        # Count statistics
        total_tasks = len(ordered_tasks)
        parallel_tasks = len([t for t in ordered_tasks if t.is_parallel()])
        sequential_tasks = total_tasks - parallel_tasks

        lines.append(f"Total tasks: {total_tasks}")
        lines.append(f"Parallel tasks: {parallel_tasks}")
        lines.append(f"Sequential tasks: {sequential_tasks}")
        lines.append(f"Execution stages: {len(groups)}")
        lines.append("")

        # Show execution plan
        lines.append("Execution Plan:")
        lines.append("")

        current_group = None
        group_tasks = []

        for task in ordered_tasks:
            if task.group != current_group:
                if group_tasks:
                    # Show previous group
                    if len(group_tasks) == 1:
                        lines.append(f"  Stage {group_tasks[0].order}: {group_tasks[0].task_id} (sequential)")
                    else:
                        group_id = group_tasks[0].group.replace("Group-", "")
                        lines.append(f"  Stage {group_tasks[0].order}: [P:Group-{group_id}] {len(group_tasks)} parallel tasks")
                        for t in group_tasks:
                            lines.append(f"    - {t.task_id}")

                current_group = task.group
                group_tasks = [task]
            else:
                group_tasks.append(task)

        # Show last group
        if group_tasks:
            if len(group_tasks) == 1:
                lines.append(f"  Stage {group_tasks[0].order}: {group_tasks[0].task_id} (sequential)")
            else:
                group_id = group_tasks[0].group.replace("Group-", "")
                lines.append(f"  Stage {group_tasks[0].order}: [P:Group-{group_id}] {len(group_tasks)} parallel tasks")
                for t in group_tasks:
                    lines.append(f"    - {t.task_id}")

        return "\n".join(lines)

    def _get_alternatives(self, tasks: List[TaskDependency]) -> List[str]:
        """
        Get list of alternative task IDs that could be reordered.

        Args:
            tasks: Original task list

        Returns:
            List of task IDs
        """
        return [task.task_id for task in tasks]


def create_task_ordering_decision(
    tasks: List[Dict[str, Any]],
    session_id: str = "default"
) -> Decision:
    """
    Convenience function to create a task ordering decision.

    Args:
        tasks: List of task dictionaries with 'id', 'depends_on', 'priority'
        session_id: Session identifier

    Returns:
        Decision with ordered tasks

    Example:
        >>> tasks = [
        ...     {"id": "task-a", "depends_on": [], "priority": 2},
        ...     {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
        ...     {"id": "task-c", "depends_on": [], "priority": 2},
        ... ]
        >>> decision = create_task_ordering_decision(tasks)
        >>> ordered = json.loads(decision.choice)
        >>> print([t['task_id'] for t in ordered])
    """
    from datetime import datetime, timezone

    context = DecisionContext(
        prd_requirements={"tasks": tasks},
        current_state={},
        available_options=[],
        constraints={},
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    strategy = TaskOrderingStrategy()
    return strategy.decide(context)


if __name__ == "__main__":
    # Example usage
    example_tasks = [
        {"id": "setup-database", "depends_on": [], "priority": 0},
        {"id": "create-schema", "depends_on": ["setup-database"], "priority": 1},
        {"id": "build-api", "depends_on": ["create-schema"], "priority": 2},
        {"id": "build-ui", "depends_on": [], "priority": 2},
        {"id": "integration-test", "depends_on": ["build-api", "build-ui"], "priority": 3},
    ]

    decision = create_task_ordering_decision(example_tasks)

    print("=" * 60)
    print("Task Ordering Decision")
    print("=" * 60)
    print(f"\nConfidence: {decision.get_confidence_level()} ({decision.confidence:.2f})")
    print(f"\nRationale:\n{decision.rationale}")
    print(f"\nMetadata:")
    for key, value in decision.metadata.items():
        print(f"  {key}: {value}")
