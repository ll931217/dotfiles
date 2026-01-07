#!/usr/bin/env python3
"""
Example: Integrating task ordering into Maestro autonomous orchestrator.

This example shows how to use the task ordering system within the
/flow:autonomous command to execute tasks with optimal sequencing.
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

# Add decision engine scripts to path
sys.path.insert(0, "/home/ll931217/GitHub/dotfiles.feat-orchestrate-flow/.flow/maestro/decision-engine/scripts")

from task_ordering import TaskOrderingEngine


def execute_task(task_id: str, task_details: Dict) -> bool:
    """
    Execute a single task.

    In a real implementation, this would:
    1. Call the appropriate subagent
    2. Monitor execution
    3. Handle errors
    4. Return success/failure

    Args:
        task_id: Task identifier
        task_details: Task metadata

    Returns:
        True if successful, False otherwise
    """
    print(f"  → Executing: [{task_id}] {task_details['title']}")

    # TODO: Implement actual task execution
    # - Determine subagent from task labels or type
    # - Invoke subagent with task context
    # - Monitor and handle errors
    # - Return success/failure

    return True


def execute_parallel_group(tasks: Dict[str, Dict], group_id: int) -> Dict[str, bool]:
    """
    Execute a group of tasks in parallel.

    Args:
        tasks: Dictionary of task_id -> task_details
        group_id: Group identifier for logging

    Returns:
        Dictionary of task_id -> success
    """
    print(f"\n[P:Group-{group_id}] Executing {len(tasks)} tasks in parallel:")

    results = {}

    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        # Submit all tasks
        futures = {
            executor.submit(execute_task, task_id, details): task_id
            for task_id, details in tasks.items()
        }

        # Collect results as they complete
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                success = future.result()
                results[task_id] = success
                status = "✓" if success else "✗"
                print(f"  {status} [{task_id}] completed")
            except Exception as e:
                results[task_id] = False
                print(f"  ✗ [{task_id}] failed: {e}")

    return results


def execute_sequential_group(tasks: Dict[str, Dict], group_id: int) -> Dict[str, bool]:
    """
    Execute a single task (sequential group).

    Args:
        tasks: Dictionary with single task_id -> task_details
        group_id: Group identifier for logging

    Returns:
        Dictionary of task_id -> success
    """
    task_id, details = list(tasks.items())[0]

    print(f"\n[Group-{group_id}] Executing sequential task:")
    success = execute_task(task_id, details)

    return {task_id: success}


def execute_autonomous_workflow(strategy: str = "topological") -> bool:
    """
    Execute autonomous workflow with optimized task ordering.

    Args:
        strategy: Task ordering strategy to use

    Returns:
        True if all tasks succeeded, False otherwise
    """
    print("=" * 70)
    print("MAESTRO AUTONOMOUS WORKFLOW")
    print("=" * 70)

    # Step 1: Get ordered tasks from beads
    print("\n[1/4] Loading tasks from beads...")
    engine = TaskOrderingEngine(strategy=strategy)
    engine.load_from_beads()

    if not engine.graph["nodes"]:
        print("No tasks found in beads.")
        return True

    print(f"Loaded {len(engine.graph['nodes'])} tasks")

    # Step 2: Compute optimal ordering
    print("\n[2/4] Computing optimal task order...")
    result = engine.compute_ordering(detect_conflicts=True)

    print(f"Strategy: {result['strategy']}")
    print(f"Total groups: {result['total_groups']}")
    print(f"Parallelizable groups: {result['parallelizable_groups']}")
    print(f"Critical path length: {result['critical_path_length']}")

    # Step 3: Execute groups
    print("\n[3/4] Executing tasks...")

    all_success = True
    completed_tasks = set()

    for i, group_task_ids in enumerate(result["sequence"], 1):
        # Get task details for this group
        group_tasks = {
            task_id: result["tasks"][task_id]
            for task_id in group_task_ids
        }

        # Execute group (parallel or sequential)
        if len(group_tasks) == 1:
            results = execute_sequential_group(group_tasks, i)
        else:
            results = execute_parallel_group(group_tasks, i)

        # Check results
        group_success = all(results.values())
        all_success = all_success and group_success

        # Track completed tasks
        completed_tasks.update(results.keys())

        # Handle failure
        if not group_success:
            failed_tasks = [tid for tid, success in results.items() if not success]
            print(f"\n⚠ Group {i} failed: {failed_tasks}")

            # TODO: Implement recovery strategies
            # - Retry failed tasks
            # - Try alternative approaches
            # - Rollback to checkpoint
            # - Request human input

            # For now, stop on failure
            print("Stopping execution due to failures.")
            break

    # Step 4: Report results
    print("\n[4/4] Execution complete")
    print("=" * 70)
    print(f"Tasks completed: {len(completed_tasks)}/{result['total_tasks']}")
    print(f"Status: {'✓ SUCCESS' if all_success else '✗ FAILED'}")
    print("=" * 70)

    return all_success


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Execute autonomous workflow with task ordering"
    )
    parser.add_argument(
        "--strategy",
        choices=["topological", "risk_first", "foundational_first", "parallel_maximizing"],
        default="topological",
        help="Task ordering strategy"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show execution plan without running"
    )

    args = parser.parse_args()

    if args.dry_run:
        # Show execution plan only
        print("\n[DRY RUN] Execution plan:")
        engine = TaskOrderingEngine(strategy=args.strategy)
        engine.load_from_beads()
        result = engine.compute_ordering()

        for i, group in enumerate(result["sequence"], 1):
            if len(group) == 1:
                task_id = group[0]
                task = result["tasks"][task_id]
                print(f"Group {i}: {task['title']}")
            else:
                print(f"Group {i}: [P:Group-{i}] {len(group)} parallel tasks")
                for task_id in group:
                    task = result["tasks"][task_id]
                    print(f"  - {task['title']}")
    else:
        # Execute workflow
        success = execute_autonomous_workflow(strategy=args.strategy)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
