#!/usr/bin/env python3
"""
Example usage of Maestro Checkpoint Manager

Demonstrates checkpoint creation, tracking, and rollback workflows
for safe development operations.
"""

import tempfile
from pathlib import Path
from uuid import uuid4

from checkpoint_manager import (
    CheckpointManager,
    CheckpointPhase,
    CheckpointType,
    StateSnapshot,
)


def example_basic_checkpoint_workflow():
    """
    Example 1: Basic checkpoint workflow

    Create checkpoints during development phases and list them.
    """
    print("=" * 60)
    print("Example 1: Basic Checkpoint Workflow")
    print("=" * 60)

    # Initialize checkpoint manager
    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Create checkpoints at different phases
    phases = [
        (CheckpointPhase.PLAN, "Planning phase completed", CheckpointType.PHASE_COMPLETE),
        (CheckpointPhase.IMPLEMENT, "Core implementation done", CheckpointType.PHASE_COMPLETE),
        (CheckpointPhase.VALIDATE, "Validation tests passing", CheckpointType.SAFE_STATE),
    ]

    checkpoint_ids = []
    for phase, description, cp_type in phases:
        print(f"\nCreating checkpoint: {description}")
        print(f"  Phase: {phase.value}")
        print(f"  Type: {cp_type.value}")

        try:
            checkpoint = manager.create_checkpoint(
                session_id=session_id,
                description=description,
                phase=phase,
                checkpoint_type=cp_type,
                commit_first=False,
            )
            checkpoint_ids.append(checkpoint.checkpoint_id)
            print(f"  ✓ Created: {checkpoint.checkpoint_id}")
            print(f"  Commit: {checkpoint.commit_sha}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

    # List all checkpoints
    print(f"\n{'='*60}")
    print("All Checkpoints:")
    print(f"{'='*60}")

    try:
        checkpoints = manager.list_checkpoints(session_id)
        for i, cp in enumerate(checkpoints, 1):
            print(f"\n{i}. {cp.description}")
            print(f"   Phase: {cp.phase.value}")
            print(f"   Type: {cp.checkpoint_type.value}")
            print(f"   Commit: {cp.commit_sha}")
            print(f"   Time: {cp.timestamp}")

        # Get summary
        summary = manager.get_checkpoint_summary(session_id)
        print(f"\n{'='*60}")
        print("Summary:")
        print(f"{'='*60}")
        print(f"Total checkpoints: {summary.total_checkpoints}")
        print(f"By type: {summary.checkpoints_by_type}")
        print(f"Latest: {summary.latest_checkpoint}")

    except Exception as e:
        print(f"Error listing checkpoints: {e}")


def example_checkpoint_with_state_snapshot():
    """
    Example 2: Checkpoint with state snapshot

    Create checkpoint with detailed session state information.
    """
    print("\n" + "=" * 60)
    print("Example 2: Checkpoint with State Snapshot")
    print("=" * 60)

    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Create state snapshot
    state_snapshot = StateSnapshot(
        tasks_completed=15,
        decisions_made=8,
        files_modified=23,
        files_created=12,
        tests_passing=42,
        tests_failing=1,
    )

    print("\nState Snapshot:")
    print(f"  Tasks completed: {state_snapshot.tasks_completed}")
    print(f"  Decisions made: {state_snapshot.decisions_made}")
    print(f"  Files modified: {state_snapshot.files_modified}")
    print(f"  Files created: {state_snapshot.files_created}")
    print(f"  Tests passing: {state_snapshot.tests_passing}")
    print(f"  Tests failing: {state_snapshot.tests_failing}")

    # Create checkpoint with state snapshot
    try:
        checkpoint = manager.create_checkpoint(
            session_id=session_id,
            description="Implementation milestone reached",
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.TASK_GROUP_COMPLETE,
            state_snapshot=state_snapshot,
            commit_first=False,
        )

        print(f"\n✓ Checkpoint created: {checkpoint.checkpoint_id}")

        # Retrieve and display state
        retrieved = manager.get_checkpoint(session_id, checkpoint.checkpoint_id)
        if retrieved.state_snapshot:
            print("\nRetrieved State Snapshot:")
            print(f"  Tasks completed: {retrieved.state_snapshot.tasks_completed}")
            print(f"  Decisions made: {retrieved.state_snapshot.decisions_made}")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_pre_operation_checkpoint():
    """
    Example 3: Checkpoint before risky operation

    Create safety checkpoint before performing risky changes.
    """
    print("\n" + "=" * 60)
    print("Example 3: Pre-Operation Safety Checkpoint")
    print("=" * 60)

    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Validate current state
    print("\nValidating repository state...")
    validation = manager.validate_checkpoint_state()

    print(f"  Valid: {validation.is_valid}")
    print(f"  Uncommitted changes: {validation.has_uncommitted_changes}")
    print(f"  Tests passing: {validation.tests_passing}")

    if validation.warnings:
        print("\n  Warnings:")
        for warning in validation.warnings:
            print(f"    - {warning}")

    if validation.errors:
        print("\n  Errors:")
        for error in validation.errors:
            print(f"    - {error}")

    # Create safety checkpoint before risky operation
    if validation.is_valid:
        print("\nCreating safety checkpoint before risky operation...")
        try:
            checkpoint = manager.create_checkpoint(
                session_id=session_id,
                description="Before database migration",
                phase=CheckpointPhase.IMPLEMENT,
                checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
                commit_first=False,
            )

            print(f"✓ Safety checkpoint created: {checkpoint.checkpoint_id}")
            print(f"  Can rollback to: {checkpoint.commit_sha}")

            # Simulate risky operation failing
            print("\n  Performing risky operation...")
            print("  ✗ Operation failed!")

            # Rollback
            print("\nRolling back to safety checkpoint...")
            # Note: Actual rollback would require git repository
            print(f"  Would rollback to: {checkpoint.checkpoint_id}")

        except Exception as e:
            print(f"✗ Error: {e}")


def example_rollback_workflow():
    """
    Example 4: Rollback workflow

    Demonstrate checkpoint creation and rollback capability.
    """
    print("\n" + "=" * 60)
    print("Example 4: Rollback Workflow")
    print("=" * 60)

    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Create initial checkpoint
    print("\n1. Creating initial stable checkpoint...")
    try:
        stable_checkpoint = manager.create_checkpoint(
            session_id=session_id,
            description="Stable state before changes",
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.SAFE_STATE,
            commit_first=False,
        )
        print(f"   ✓ Checkpoint: {stable_checkpoint.checkpoint_id}")
        print(f"   Commit: {stable_checkpoint.commit_sha}")

        # Make changes (simulated)
        print("\n2. Making changes...")
        print("   - Modified 5 files")
        print("   - Added new feature")

        # Create checkpoint after changes
        print("\n3. Creating checkpoint after changes...")
        new_checkpoint = manager.create_checkpoint(
            session_id=session_id,
            description="After implementing new feature",
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.TASK_GROUP_COMPLETE,
            commit_first=False,
        )
        print(f"   ✓ Checkpoint: {new_checkpoint.checkpoint_id}")

        # List checkpoints before rollback
        print("\n4. Current checkpoints:")
        checkpoints = manager.list_checkpoints(session_id)
        for i, cp in enumerate(checkpoints, 1):
            print(f"   {i}. {cp.description}")
            print(f"      Rollback count: {cp.rollback_count}")

        # Perform rollback (simulated)
        print("\n5. Rolling back to stable state...")
        print(f"   Rolling back to: {stable_checkpoint.checkpoint_id}")
        print(f"   Note: Actual rollback requires git repository")

        # Show what rollback would do
        print("\n6. Rollback would:")
        print(f"   - Reset git to {stable_checkpoint.commit_sha}")
        print(f"   - Update rollback metadata")
        print(f"   - Preserve checkpoint history")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_error_recovery_checkpoint():
    """
    Example 5: Error recovery checkpoint

    Create checkpoint when recovering from errors.
    """
    print("\n" + "=" * 60)
    print("Example 5: Error Recovery Checkpoint")
    print("=" * 60)

    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Simulate error scenario
    print("\nScenario: Implementation error detected")
    print("  - Validation failed")
    print("  - Tests are failing")

    # Create error recovery checkpoint
    try:
        print("\nCreating error recovery checkpoint...")
        checkpoint = manager.create_checkpoint(
            session_id=session_id,
            description="Recovery point after validation error",
            phase=CheckpointPhase.VALIDATE,
            checkpoint_type=CheckpointType.ERROR_RECOVERY,
            commit_first=False,
        )

        print(f"✓ Checkpoint created: {checkpoint.checkpoint_id}")
        print(f"  Type: {checkpoint.checkpoint_type.value}")
        print(f"  Can rollback to this point if fixes fail")

        # List all checkpoints
        print("\nAll checkpoints in session:")
        checkpoints = manager.list_checkpoints(session_id)
        for cp in checkpoints:
            print(f"  - {cp.description} ({cp.checkpoint_type.value})")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_checkpoint_querying():
    """
    Example 6: Querying and filtering checkpoints

    Demonstrate various ways to query checkpoint information.
    """
    print("\n" + "=" * 60)
    print("Example 6: Checkpoint Querying")
    print("=" * 60)

    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Create multiple checkpoints of different types
    checkpoint_configs = [
        ("Plan complete", CheckpointPhase.PLAN, CheckpointType.PHASE_COMPLETE),
        ("Tasks generated", CheckpointPhase.GENERATE_TASKS, CheckpointType.PHASE_COMPLETE),
        ("Safe state 1", CheckpointPhase.IMPLEMENT, CheckpointType.SAFE_STATE),
        ("Feature done", CheckpointPhase.IMPLEMENT, CheckpointType.TASK_GROUP_COMPLETE),
        ("Safe state 2", CheckpointPhase.IMPLEMENT, CheckpointType.SAFE_STATE),
    ]

    print("\nCreating checkpoints...")
    for description, phase, cp_type in checkpoint_configs:
        try:
            cp = manager.create_checkpoint(
                session_id=session_id,
                description=description,
                phase=phase,
                checkpoint_type=cp_type,
                commit_first=False,
            )
            print(f"  ✓ {description} ({cp_type.value})")
        except Exception as e:
            print(f"  ✗ {description}: {e}")

    # Query checkpoints
    print("\nQuerying checkpoints...")

    try:
        # Get all checkpoints
        all_checkpoints = manager.list_checkpoints(session_id)
        print(f"\nTotal checkpoints: {len(all_checkpoints)}")

        # Get summary
        summary = manager.get_checkpoint_summary(session_id)
        print(f"\nCheckpoint Summary:")
        print(f"  Total: {summary.total_checkpoints}")
        print(f"  By type:")
        for cp_type, count in summary.checkpoints_by_type.items():
            print(f"    {cp_type}: {count}")
        print(f"  Used for rollback: {summary.checkpoints_used_for_rollback}")
        print(f"  Latest checkpoint: {summary.latest_checkpoint}")

        # Filter by type
        print("\nSafe State Checkpoints:")
        for cp in all_checkpoints:
            if cp.checkpoint_type == CheckpointType.SAFE_STATE:
                print(f"  - {cp.description}")
                print(f"    Created: {cp.timestamp}")

    except Exception as e:
        print(f"Error querying checkpoints: {e}")


def example_checkpoint_metadata():
    """
    Example 7: Checkpoint metadata and tracking

    Display detailed checkpoint information.
    """
    print("\n" + "=" * 60)
    print("Example 7: Checkpoint Metadata")
    print("=" * 60)

    manager = CheckpointManager()
    session_id = str(uuid4())

    print(f"\nSession ID: {session_id}")

    # Create checkpoint with full metadata
    try:
        state_snapshot = StateSnapshot(
            tasks_completed=25,
            decisions_made=12,
            files_modified=45,
            files_created=28,
            tests_passing=87,
            tests_failing=0,
        )

        checkpoint = manager.create_checkpoint(
            session_id=session_id,
            description="Feature implementation complete",
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            state_snapshot=state_snapshot,
            commit_first=False,
        )

        print("\nCheckpoint Metadata:")
        print(f"  ID: {checkpoint.checkpoint_id}")
        print(f"  Description: {checkpoint.description}")
        print(f"  Phase: {checkpoint.phase.value}")
        print(f"  Type: {checkpoint.checkpoint_type.value}")
        print(f"  Commit SHA: {checkpoint.commit_sha}")
        print(f"  Timestamp: {checkpoint.timestamp}")
        print(f"  Tags: {', '.join(checkpoint.tags) if checkpoint.tags else 'None'}")
        print(f"  Rollback used: {checkpoint.rollback_used}")
        print(f"  Rollback count: {checkpoint.rollback_count}")

        if checkpoint.state_snapshot:
            print("\n  State Snapshot:")
            print(f"    Tasks completed: {checkpoint.state_snapshot.tasks_completed}")
            print(f"    Decisions made: {checkpoint.state_snapshot.decisions_made}")
            print(f"    Files modified: {checkpoint.state_snapshot.files_modified}")
            print(f"    Files created: {checkpoint.state_snapshot.files_created}")
            print(f"    Tests passing: {checkpoint.state_snapshot.tests_passing}")
            print(f"    Tests failing: {checkpoint.state_snapshot.tests_failing}")

    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Maestro Checkpoint Manager - Usage Examples")
    print("=" * 60)

    examples = [
        example_basic_checkpoint_workflow,
        example_checkpoint_with_state_snapshot,
        example_pre_operation_checkpoint,
        example_rollback_workflow,
        example_error_recovery_checkpoint,
        example_checkpoint_querying,
        example_checkpoint_metadata,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples Complete")
    print("=" * 60)
    print("\nNote: These examples demonstrate the API. Actual git operations")
    print("require a valid git repository. Set commit_first=False to skip")
    print("commit creation for testing purposes.")
    print()


if __name__ == "__main__":
    main()
