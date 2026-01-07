#!/usr/bin/env python3
"""
Example usage of Maestro Recovery Strategies.

This script demonstrates how to use the four recovery strategies:
1. Retry with exponential backoff
2. Alternative approach selection
3. Rollback to checkpoint
4. Human input request
"""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from recovery_strategies import (
    RecoveryStrategies,
    RetryConfig,
    CheckpointType,
)


def example_retry_with_backoff():
    """Example: Retry with exponential backoff."""
    print("\n" + "="*70)
    print("Example 1: Retry with Exponential Backoff")
    print("="*70)

    strategies = RecoveryStrategies()

    # Simulate a flaky operation that fails twice then succeeds
    attempt_count = 0

    def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RuntimeError(f"Temporary failure (attempt {attempt_count})")
        return "Success!"

    # Retry with custom configuration
    config = RetryConfig(
        max_attempts=5,
        base_delay_seconds=0.5,
        jitter=False,  # Disable jitter for predictable demo
    )

    result = strategies.retry_with_backoff(
        flaky_operation,
        config=config,
        operation_name="flaky operation",
    )

    print(f"\nResult: {result.success}")
    print(f"Attempts made: {result.attempts_made}")
    print(f"Total time: {result.total_time_seconds:.2f}s")
    if result.success:
        print(f"Final result: {result.result}")


def example_alternative_approach():
    """Example: Alternative approach selection."""
    print("\n" + "="*70)
    print("Example 2: Alternative Approach Selection")
    print("="*70)

    strategies = RecoveryStrategies()

    # Get alternative approaches for test failure
    result = strategies.try_alternative_approach(
        context={"task_type": "testing", "test_framework": "pytest"},
        failure_info={
            "error": "AssertionError: test_user_authentication fails intermittently",
            "error_type": "AssertionError",
        },
    )

    print(f"\nRecovery strategy: {result.strategy_used}")
    print(f"Message: {result.message}")
    print(f"\nRecommended approach:")
    print(f"  Name: {result.details['approach_name']}")
    print(f"  Pattern: {result.details['implementation_pattern']}")
    print(f"  Risk level: {result.details['risk_level']}")
    print(f"  Required changes:")
    for change in result.details['required_changes']:
        print(f"    - {change}")

    print(f"\nAll available approaches:")
    for approach in result.details['all_available_approaches']:
        print(f"  - {approach['name']} ({approach['risk_level']} risk)")


def example_checkpoint_and_rollback():
    """Example: Checkpoint creation and rollback."""
    print("\n" + "="*70)
    print("Example 3: Checkpoint Creation and Rollback")
    print("="*70)

    strategies = RecoveryStrategies()
    session_id = "example-session"

    # Create a checkpoint
    print("\nCreating checkpoint...")
    checkpoint = strategies.create_checkpoint(
        session_id=session_id,
        description="Before making changes",
        phase="implement",
        checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
        state_snapshot={
            "tasks_completed": 3,
            "files_modified": 5,
        },
    )

    print(f"Checkpoint created:")
    print(f"  ID: {checkpoint.checkpoint_id}")
    print(f"  Commit: {checkpoint.commit_sha}")
    print(f"  Description: {checkpoint.description}")
    print(f"  Type: {checkpoint.checkpoint_type.value}")

    # Show checkpoint info
    print(f"\nCheckpoint file created at: {strategies._get_checkpoint_file(session_id)}")

    # In a real scenario, you would make changes here
    # For this demo, we'll just show how to rollback
    print(f"\nTo rollback to this checkpoint, use:")
    print(f"  strategies.rollback_to_checkpoint(")
    print(f"      session_id='{session_id}',")
    print(f"      checkpoint_id='{checkpoint.checkpoint_id}',")
    print(f"  )")


def example_retry_strategies():
    """Example: Different retry strategies for different scenarios."""
    print("\n" + "="*70)
    print("Example 4: Retry Strategies for Different Scenarios")
    print("="*70)

    strategies = RecoveryStrategies()

    # Scenario 1: Network operation (aggressive retry)
    print("\nScenario 1: Network operation")
    print("  Strategy: Many retries with short delays")

    config_network = RetryConfig(
        max_attempts=10,
        base_delay_seconds=0.5,
        max_delay_seconds=5.0,
        exponential_base=1.5,
        jitter=True,
    )
    print(f"  Config: max_attempts={config_network.max_attempts}, "
          f"base_delay={config_network.base_delay_seconds}s")

    # Scenario 2: Database operation (moderate retry)
    print("\nScenario 2: Database operation")
    print("  Strategy: Moderate retries with exponential backoff")

    config_db = RetryConfig(
        max_attempts=5,
        base_delay_seconds=1.0,
        max_delay_seconds=30.0,
        exponential_base=2.0,
        jitter=True,
    )
    print(f"  Config: max_attempts={config_db.max_attempts}, "
          f"base_delay={config_db.base_delay_seconds}s")

    # Scenario 3: External API (conservative retry)
    print("\nScenario 3: External API call")
    print("  Strategy: Few retries with long delays")

    config_api = RetryConfig(
        max_attempts=3,
        base_delay_seconds=2.0,
        max_delay_seconds=60.0,
        exponential_base=2.0,
        jitter=True,
    )
    print(f"  Config: max_attempts={config_api.max_attempts}, "
          f"base_delay={config_api.base_delay_seconds}s")


def example_recovery_workflow():
    """Example: Complete recovery workflow combining strategies."""
    print("\n" + "="*70)
    print("Example 5: Complete Recovery Workflow")
    print("="*70)

    strategies = RecoveryStrategies()
    session_id = "workflow-example"

    print("\nWorkflow: Implement feature with recovery strategies")
    print("-" * 70)

    # Step 1: Create checkpoint
    print("\n[1] Creating checkpoint before implementation...")
    checkpoint = strategies.create_checkpoint(
        session_id=session_id,
        description="Before implementing user authentication",
        phase="implement",
        checkpoint_type=CheckpointType.SAFE_STATE,
    )
    print(f"    Checkpoint {checkpoint.checkpoint_id} created")

    # Step 2: Attempt implementation with retry
    print("\n[2] Attempting implementation with retry...")

    def implement_auth():
        # Simulate implementation that might fail
        raise NotImplementedError("OAuth provider not configured")

    result = strategies.retry_with_backoff(
        implement_auth,
        config=RetryConfig(max_attempts=2),
        operation_name="implement authentication",
    )

    if not result.success:
        print(f"    Failed after {result.attempts_made} attempts")
        print(f"    Error: {result.final_error}")

        # Step 3: Get alternative approaches
        print("\n[3] Getting alternative approaches...")
        recovery = strategies.try_alternative_approach(
            context={"task": "authentication"},
            failure_info={"error": str(result.final_error)},
        )

        print(f"    Recommendation: {recovery.details['approach_name']}")
        print(f"    Implementation pattern: {recovery.details['implementation_pattern']}")

        # Step 4: Request human input if needed
        print("\n[4] In production, you could:")
        print(f"    a) Try the recommended alternative approach")
        print(f"    b) Rollback to checkpoint: {checkpoint.checkpoint_id}")
        print(f"    c) Request human input for decision")

    print("\n    Workflow complete!")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Maestro Recovery Strategies - Usage Examples")
    print("="*70)

    try:
        example_retry_with_backoff()
        example_alternative_approach()
        example_checkpoint_and_rollback()
        example_retry_strategies()
        example_recovery_workflow()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
