#!/usr/bin/env python3
"""
Simple wrapper for task ordering with easy Maestro integration.

This script provides a simplified interface for the task ordering system,
optimized for integration with the Maestro orchestrator.
"""

import json
import sys
from typing import Dict, List, Any

# Import the engine
sys.path.insert(0, "/home/ll931217/GitHub/dotfiles.feat-orchestrate-flow/.flow/maestro/decision-engine/scripts")
from task_ordering import TaskOrderingEngine


def order_tasks(
    strategy: str = "topological",
    detect_conflicts: bool = True,
    format: str = "simple"
) -> Dict[str, Any]:
    """
    Order tasks based on dependencies and strategy.

    Args:
        strategy: Ordering strategy (topological, risk_first, foundational_first, parallel_maximizing)
        detect_conflicts: Whether to detect and resolve file conflicts
        format: Output format (simple, detailed, json)

    Returns:
        Dictionary with ordered tasks and metadata
    """
    engine = TaskOrderingEngine(strategy=strategy)
    engine.load_from_beads()

    if not engine.graph["nodes"]:
        return {
            "error": "No tasks found in beads",
            "tasks": [],
            "groups": []
        }

    result = engine.compute_ordering(detect_conflicts=detect_conflicts)

    if format == "simple":
        return simplify_output(result)
    elif format == "detailed":
        return result
    else:
        return result


def simplify_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Simplify output for easy consumption."""
    simplified = {
        "strategy": result["strategy"],
        "total_tasks": result["total_tasks"],
        "total_groups": result["total_groups"],
        "parallelizable_groups": result["parallelizable_groups"],
        "critical_path_length": result["critical_path_length"],
        "groups": []
    }

    for i, group in enumerate(result["sequence"], 1):
        group_info = {
            "group_id": i,
            "type": "parallel" if len(group) > 1 else "sequential",
            "task_count": len(group),
            "tasks": []
        }

        for task_id in group:
            task = result["tasks"][task_id]
            group_info["tasks"].append({
                "id": task_id,
                "title": task["title"],
                "priority": task["priority"],
                "type": task["type"]
            })

        simplified["groups"].append(group_info)

    return simplified


def print_execution_plan(result: Dict[str, Any]) -> None:
    """Print human-readable execution plan."""
    print(f"\n{'='*60}")
    print(f"Execution Plan: {result['strategy'].upper()} Strategy")
    print(f"{'='*60}")
    print(f"Total tasks: {result['total_tasks']}")
    print(f"Total groups: {result['total_groups']}")
    print(f"Parallelizable groups: {result['parallelizable_groups']}")
    print(f"Critical path length: {result['critical_path_length']}")
    print(f"{'='*60}\n")

    for group in result["groups"]:
        group_id = group["group_id"]
        group_type = group["type"]

        if group_type == "parallel":
            print(f"[P:Group-{group_id}] {group['task_count']} parallel tasks:")
        else:
            print(f"[Group-{group_id}] Sequential task:")

        for task in group["tasks"]:
            priority_label = f"P{task['priority']}"
            print(f"  - [{task['id']}] {task['title']} ({priority_label})")

        print()


def get_next_group(result: Dict[str, Any], completed: List[str]) -> List[str]:
    """
    Get the next group of tasks that can be executed.

    Args:
        result: Ordering result
        completed: List of completed task IDs

    Returns:
        List of task IDs ready for execution
    """
    for group in result["groups"]:
        task_ids = [t["id"] for t in group["tasks"]]

        # Check if all tasks in group are incomplete
        if any(task_id not in completed for task_id in task_ids):
            # Check if dependencies are satisfied
            all_deps_satisfied = True
            for task in group["tasks"]:
                task_id = task["id"]
                # Get dependencies from full result
                if "tasks" in result:
                    continue  # Simplified result doesn't have deps

            return task_ids

    return []


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Order tasks for autonomous execution"
    )
    parser.add_argument(
        "--strategy",
        choices=["topological", "risk_first", "foundational_first", "parallel_maximizing"],
        default="topological",
        help="Ordering strategy"
    )
    parser.add_argument(
        "--no-conflicts",
        action="store_true",
        help="Skip conflict detection"
    )
    parser.add_argument(
        "--format",
        choices=["simple", "detailed", "json"],
        default="simple",
        help="Output format"
    )
    parser.add_argument(
        "--print-plan",
        action="store_true",
        help="Print human-readable execution plan"
    )

    args = parser.parse_args()

    result = order_tasks(
        strategy=args.strategy,
        detect_conflicts=not args.no_conflicts,
        format=args.format
    )

    if args.print_plan and "error" not in result:
        print_execution_plan(result)
    elif args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
