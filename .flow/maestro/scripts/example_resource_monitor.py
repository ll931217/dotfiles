#!/usr/bin/env python3
"""
Example demonstrating ResourceMonitor usage.

This script shows how the ResourceMonitor tracks resource usage
and enforces limits during workflow execution.
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from resource_monitor import (
    ResourceMonitor,
    ResourceLimits,
    LimitStatus,
)


def demonstrate_basic_usage():
    """Demonstrate basic resource monitoring."""
    print("=" * 60)
    print("Resource Monitor Demo: Basic Usage")
    print("=" * 60)
    print()

    # Configure limits
    limits = ResourceLimits(
        max_duration_seconds=600,  # 10 minutes
        max_tokens=10000,
        max_api_calls=100,
        checkpoint_interval=60,  # 1 minute
    )

    # Initialize monitor
    monitor = ResourceMonitor(limits, session_id="demo-session-1")
    print(f"✓ Resource monitor initialized")
    print(f"  - Max duration: {limits.max_duration_seconds}s")
    print(f"  - Max tokens: {limits.max_tokens}")
    print(f"  - Max API calls: {limits.max_api_calls}")
    print()

    # Simulate some operations
    print("Simulating operations...")
    for i in range(5):
        tokens = 1000
        monitor.record_operation(tokens=tokens, api_call=True)
        print(f"  Operation {i+1}: Used {tokens} tokens, 1 API call")

    print()

    # Get usage report
    summary = monitor.get_usage_summary()
    print("Current usage:")
    print(f"  Tokens: {summary['tokens']['used']}/{summary['tokens']['limit']} "
          f"({summary['tokens']['percentage']:.1f}%)")
    print(f"  API calls: {summary['api_calls']['used']}/{summary['api_calls']['limit']} "
          f"({summary['api_calls']['percentage']:.1f}%)")
    print(f"  Time: {summary['duration']['used']:.1f}s/{summary['duration']['limit']}s "
          f"({summary['duration']['percentage']:.1f}%)")
    print()

    # Check limits
    result = monitor.check_limits()
    print(f"Limit check status: {result.status.value}")
    print(f"Can continue: {result.can_continue}")
    print()


def demonstrate_approaching_limits():
    """Demonstrate behavior when approaching limits."""
    print("=" * 60)
    print("Resource Monitor Demo: Approaching Limits")
    print("=" * 60)
    print()

    # Configure limits
    limits = ResourceLimits(
        max_duration_seconds=600,
        max_tokens=10000,
        max_api_calls=100,
        checkpoint_interval=60,
    )

    # Initialize monitor
    monitor = ResourceMonitor(limits, session_id="demo-session-2")
    print(f"✓ Resource monitor initialized")
    print()

    # Use 85% of token limit (approaching threshold)
    print("Using 85% of token limit...")
    for i in range(85):
        monitor.record_operation(tokens=100, api_call=True)

    # Check status
    result = monitor.check_limits()
    print(f"Status: {result.status.value}")
    print(f"Reason: {result.reason}")
    print()

    # Test should_continue with different progress levels
    print("Testing should_continue with different progress levels:")

    # Low progress - should stop
    progress = 0.5
    can_continue = monitor.should_continue(progress)
    print(f"  Progress: {progress*100:.0f}% → Can continue: {can_continue}")
    if not can_continue:
        print(f"    → Stopping gracefully to save partial results")

    print()

    # High progress - should continue
    progress = 0.9
    can_continue = monitor.should_continue(progress)
    print(f"  Progress: {progress*100:.0f}% → Can continue: {can_continue}")
    if can_continue:
        print(f"    → Continuing to completion")

    print()


def demonstrate_exceeded_limits():
    """Demonstrate behavior when limits are exceeded."""
    print("=" * 60)
    print("Resource Monitor Demo: Exceeded Limits")
    print("=" * 60)
    print()

    # Configure limits
    limits = ResourceLimits(
        max_duration_seconds=600,
        max_tokens=10000,
        max_api_calls=100,
        checkpoint_interval=60,
    )

    # Initialize monitor
    monitor = ResourceMonitor(limits, session_id="demo-session-3")
    print(f"✓ Resource monitor initialized")
    print()

    # Exceed token limit
    print("Exceeding token limit...")
    for i in range(101):
        monitor.record_operation(tokens=100, api_call=True)

    # Check status
    result = monitor.check_limits()
    print(f"Status: {result.status.value}")
    print(f"Reason: {result.reason}")
    print(f"Exceeded limits: {result.exceeded_limits}")
    print()

    # Test should_continue - should always return False
    progress = 0.95
    can_continue = monitor.should_continue(progress)
    print(f"Even with {progress*100:.0f}% progress: Can continue: {can_continue}")
    print()


def demonstrate_checkpointing():
    """Demonstrate checkpoint creation."""
    print("=" * 60)
    print("Resource Monitor Demo: Checkpointing")
    print("=" * 60)
    print()

    # Configure limits with short checkpoint interval
    limits = ResourceLimits(
        max_duration_seconds=600,
        max_tokens=10000,
        max_api_calls=100,
        checkpoint_interval=2,  # 2 seconds for demo
    )

    # Initialize monitor
    monitor = ResourceMonitor(limits, session_id="demo-session-4")
    print(f"✓ Resource monitor initialized")
    print(f"✓ Checkpoint interval: {limits.checkpoint_interval}s")
    print()

    # First operation creates checkpoint
    print("First operation...")
    monitor.record_operation(tokens=1000, api_call=True)
    print(f"Checkpoints created: {monitor.usage.checkpoints_created}")
    print()

    # Wait for interval to pass
    print("Waiting for checkpoint interval to pass...")
    time.sleep(2.1)

    # Next operation creates another checkpoint
    print("Second operation (after interval)...")
    monitor.record_operation(tokens=1000, api_call=True)
    print(f"Checkpoints created: {monitor.usage.checkpoints_created}")
    print()


def demonstrate_remaining_resources():
    """Demonstrate remaining resource calculations."""
    print("=" * 60)
    print("Resource Monitor Demo: Remaining Resources")
    print("=" * 60)
    print()

    # Configure limits
    limits = ResourceLimits(
        max_duration_seconds=600,
        max_tokens=10000,
        max_api_calls=100,
        checkpoint_interval=60,
    )

    # Initialize monitor
    monitor = ResourceMonitor(limits, session_id="demo-session-5")
    print(f"✓ Resource monitor initialized")
    print()

    # Use some resources
    print("Using resources...")
    for i in range(30):
        monitor.record_operation(tokens=200, api_call=True)

    # Simulate some time elapsed
    monitor.usage.start_time = datetime.now() - timedelta(seconds=100)

    print()

    # Get remaining resources
    time_remaining = monitor.get_time_remaining()
    tokens_remaining = monitor.get_tokens_remaining()
    api_calls_remaining = monitor.get_api_calls_remaining()

    print("Remaining resources:")
    print(f"  Time: {time_remaining:.0f}s")
    print(f"  Tokens: {tokens_remaining}")
    print(f"  API calls: {api_calls_remaining}")
    print()

    # Estimate completion possibility
    print("Estimating completion possibility:")
    possible = monitor.get_estimated_completion_possible(
        estimated_tokens_remaining=5000,
        estimated_time_remaining=300,
    )
    print(f"  Need 5000 tokens and 300s: Possible = {possible}")
    print()


def main():
    """Run all demonstrations."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Resource Monitor Demonstration" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    demonstrate_basic_usage()
    demonstrate_approaching_limits()
    demonstrate_exceeded_limits()
    demonstrate_checkpointing()
    demonstrate_remaining_resources()

    print("=" * 60)
    print("All demonstrations completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
