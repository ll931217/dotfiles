#!/usr/bin/env python3
"""
Example demonstration of RetryManager functionality.

Shows how to use RetryManager for handling transient failures with exponential backoff.
"""

import json
import time
from retry_manager import RetryManager


def example_successful_operation():
    """Example: Operation succeeds on first attempt."""
    print("\n" + "=" * 60)
    print("Example 1: Successful Operation")
    print("=" * 60)

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    def fetch_data():
        return "Data fetched successfully"

    result = manager.execute_with_retry(
        fetch_data,
        {"operation_name": "fetch_data"}
    )

    print(f"Result: {result}")

    history = manager.get_retry_history("fetch_data")
    print(f"Retry History: {json.dumps(history, indent=2)}")


def example_transient_error_recovery():
    """Example: Operation fails then recovers."""
    print("\n" + "=" * 60)
    print("Example 2: Transient Error Recovery")
    print("=" * 60)

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    attempt_count = {"count": 0}

    def fetch_with_transient_error():
        attempt_count["count"] += 1
        if attempt_count["count"] < 2:
            raise ConnectionError("Network timeout - retrying")
        return "Data recovered after retry"

    result = manager.execute_with_retry(
        fetch_with_transient_error,
        {"operation_name": "fetch_with_retry"}
    )

    print(f"Result: {result}")

    stats = manager.get_retry_statistics("fetch_with_retry")
    print(f"Statistics: {json.dumps(stats, indent=2)}")


def example_max_retries_exceeded():
    """Example: Operation fails after max retries."""
    print("\n" + "=" * 60)
    print("Example 3: Max Retries Exceeded")
    print("=" * 60)

    manager = RetryManager(max_retries=2, initial_delay=0.1)

    def always_failing_operation():
        raise TimeoutError("Service unavailable")

    try:
        manager.execute_with_retry(
            always_failing_operation,
            {"operation_name": "failing_operation"}
        )
    except TimeoutError as e:
        print(f"Operation failed after all retries: {e}")

    history = manager.get_retry_history("failing_operation")
    print(f"Total attempts: {len(history['failing_operation'])}")


def example_permanent_error():
    """Example: Permanent error does not trigger retries."""
    print("\n" + "=" * 60)
    print("Example 4: Permanent Error (No Retries)")
    print("=" * 60)

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    attempt_count = {"count": 0}

    def operation_with_permanent_error():
        attempt_count["count"] += 1
        raise ValueError("Invalid configuration")

    try:
        manager.execute_with_retry(
            operation_with_permanent_error,
            {"operation_name": "permanent_error_operation"}
        )
    except ValueError as e:
        print(f"Permanent error detected: {e}")
        print(f"Attempted {attempt_count['count']} time(s) - no retries for permanent errors")


def example_exponential_backoff_delays():
    """Example: Demonstrate exponential backoff timing."""
    print("\n" + "=" * 60)
    print("Example 5: Exponential Backoff Timing")
    print("=" * 60)

    manager = RetryManager(
        max_retries=3,
        initial_delay=0.1,
        backoff_base=2.0
    )

    print("\nRetry delay schedule:")
    for i in range(5):
        delay = manager.calculate_delay(i)
        print(f"  Attempt {i}: {delay:.2f}s delay")

    print("\nSimulating retries with actual delays...")
    attempt_times = []

    def slow_operation():
        attempt_times.append(time.time())
        count = len(attempt_times)
        if count < 4:
            raise ConnectionError(f"Attempt {count} failed")
        return "Success after retries"

    start_time = time.time()
    result = manager.execute_with_retry(
        slow_operation,
        {"operation_name": "slow_operation"}
    )
    elapsed = time.time() - start_time

    print(f"Result: {result}")
    print(f"Total elapsed time: {elapsed:.2f}s")
    print(f"Number of attempts: {len(attempt_times)}")


def example_custom_retry_exceptions():
    """Example: Retry on custom exception types."""
    print("\n" + "=" * 60)
    print("Example 6: Custom Retry Exceptions")
    print("=" * 60)

    class DatabaseConnectionError(Exception):
        pass

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    attempt_count = {"count": 0}

    def database_operation():
        attempt_count["count"] += 1
        if attempt_count["count"] < 3:
            raise DatabaseConnectionError("Database connection lost")
        return "Query executed successfully"

    result = manager.execute_with_retry(
        database_operation,
        {
            "operation_name": "database_query",
            "retry_on": (DatabaseConnectionError,),
        }
    )

    print(f"Result: {result}")
    print(f"Attempts: {attempt_count['count']}")


def example_retry_statistics():
    """Example: Collect and display retry statistics."""
    print("\n" + "=" * 60)
    print("Example 7: Retry Statistics")
    print("=" * 60)

    manager = RetryManager(max_retries=3, initial_delay=0.05)

    # Run multiple operations
    operations = [
        ("op1", lambda: "success1"),
        ("op2", lambda: (_ for _ in ()).throw(ConnectionError("fail"))),
        ("op3", lambda: "success3"),
    ]

    for op_name, func in operations:
        try:
            manager.execute_with_retry(func, {"operation_name": op_name})
        except ConnectionError:
            pass

    # Get all statistics
    all_stats = manager.get_retry_statistics()
    print("\nAll operation statistics:")
    print(json.dumps(all_stats, indent=2))


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("RetryManager Examples")
    print("=" * 60)

    example_successful_operation()
    example_transient_error_recovery()
    example_max_retries_exceeded()
    example_permanent_error()
    example_exponential_backoff_delays()
    example_custom_retry_exceptions()
    example_retry_statistics()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
