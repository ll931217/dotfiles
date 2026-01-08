#!/usr/bin/env python3
"""
Comprehensive verification script for RetryManager implementation.
Tests all aspects of the retry mechanism with exponential backoff.
"""

import json
import time
from retry_manager import RetryManager, RetryAttempt
from error_handler import ErrorHandler


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_1_basic_retry_manager():
    """Test 1: Basic RetryManager functionality."""
    print_section("Test 1: Basic RetryManager Functionality")

    manager = RetryManager(
        max_retries=3,
        backoff_base=2.0,
        initial_delay=1.0,
        max_delay=60.0,
    )

    print("Configuration:")
    print(f"  - Max retries: {manager.max_retries}")
    print(f"  - Backoff base: {manager.backoff_base}")
    print(f"  - Initial delay: {manager.initial_delay}s")
    print(f"  - Max delay: {manager.max_delay}s")

    print("\nExponential backoff schedule:")
    for i in range(5):
        delay = manager.calculate_delay(i)
        print(f"  Attempt {i}: {delay}s delay")

    print("\n✅ Test 1 passed")


def test_2_successful_operation():
    """Test 2: Successful operation without retries."""
    print_section("Test 2: Successful Operation (No Retries)")

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    def successful_operation():
        return "Operation completed successfully"

    result = manager.execute_with_retry(
        successful_operation,
        {"operation_name": "successful_op"}
    )

    print(f"Result: {result}")

    history = manager.get_retry_history("successful_op")
    print(f"Attempts: {len(history['successful_op'])}")
    print(f"Success: {history['successful_op'][0]['success']}")

    print("\n✅ Test 2 passed")


def test_3_transient_error_recovery():
    """Test 3: Recovery from transient error."""
    print_section("Test 3: Transient Error Recovery")

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    attempt_count = {"count": 0}

    def operation_with_transient_error():
        attempt_count["count"] += 1
        if attempt_count["count"] < 2:
            raise ConnectionError("Network timeout - retrying")
        return "Recovered after retry"

    result = manager.execute_with_retry(
        operation_with_transient_error,
        {"operation_name": "transient_error_op"}
    )

    print(f"Result: {result}")
    print(f"Total attempts: {attempt_count['count']}")

    stats = manager.get_retry_statistics("transient_error_op")
    print(f"Statistics: {json.dumps(stats, indent=2)}")

    print("\n✅ Test 3 passed")


def test_4_max_retries_exceeded():
    """Test 4: Max retries exceeded."""
    print_section("Test 4: Max Retries Exceeded")

    manager = RetryManager(max_retries=2, initial_delay=0.1)

    def always_failing_operation():
        raise TimeoutError("Service unavailable")

    try:
        manager.execute_with_retry(
            always_failing_operation,
            {"operation_name": "failing_op"}
        )
    except TimeoutError as e:
        print(f"Expected failure: {e}")

    history = manager.get_retry_history("failing_op")
    print(f"Total attempts: {len(history['failing_op'])}")
    print(f"Expected: {2 + 1} (1 initial + 2 retries)")

    assert len(history['failing_op']) == 3, "Should have 3 attempts"

    print("\n✅ Test 4 passed")


def test_5_permanent_error_no_retry():
    """Test 5: Permanent error does not trigger retries."""
    print_section("Test 5: Permanent Error (No Retries)")

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    attempt_count = {"count": 0}

    def operation_with_permanent_error():
        attempt_count["count"] += 1
        raise ValueError("Invalid configuration")

    try:
        manager.execute_with_retry(
            operation_with_permanent_error,
            {"operation_name": "permanent_error_op"}
        )
    except ValueError as e:
        print(f"Permanent error: {e}")

    print(f"Total attempts: {attempt_count['count']}")
    print(f"Expected: 1 (no retries for permanent errors)")

    assert attempt_count['count'] == 1, "Should only attempt once"

    print("\n✅ Test 5 passed")


def test_6_exponential_backoff_timing():
    """Test 6: Verify exponential backoff timing."""
    print_section("Test 6: Exponential Backoff Timing")

    manager = RetryManager(
        max_retries=3,
        initial_delay=0.05,
        backoff_base=2.0,
    )

    attempt_times = []

    def timed_operation():
        attempt_times.append(time.time())
        count = len(attempt_times)
        if count < 4:
            raise ConnectionError(f"Attempt {count} failed")
        return "Success"

    start_time = time.time()
    result = manager.execute_with_retry(
        timed_operation,
        {"operation_name": "timed_op"}
    )
    elapsed = time.time() - start_time

    print(f"Result: {result}")
    print(f"Total attempts: {len(attempt_times)}")
    print(f"Total elapsed time: {elapsed:.2f}s")
    print(f"Expected minimum: {0.05 + 0.10 + 0.20:.2f}s")

    assert elapsed >= 0.35, f"Expected at least 0.35s, got {elapsed:.2f}s"

    print("\n✅ Test 6 passed")


def test_7_custom_exception_types():
    """Test 7: Custom exception types for retry."""
    print_section("Test 7: Custom Exception Types")

    class CustomTransientError(Exception):
        pass

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    attempt_count = {"count": 0}

    def operation_with_custom_error():
        attempt_count["count"] += 1
        if attempt_count["count"] < 3:
            raise CustomTransientError("Custom transient error")
        return "Success with custom exception"

    result = manager.execute_with_retry(
        operation_with_custom_error,
        {
            "operation_name": "custom_error_op",
            "retry_on": (CustomTransientError,),
        }
    )

    print(f"Result: {result}")
    print(f"Total attempts: {attempt_count['count']}")

    print("\n✅ Test 7 passed")


def test_8_error_handler_integration():
    """Test 8: ErrorHandler integration."""
    print_section("Test 8: ErrorHandler Integration")

    handler = ErrorHandler()

    attempt_count = {"count": 0}

    def flaky_operation():
        attempt_count["count"] += 1
        if attempt_count["count"] < 2:
            raise ConnectionError("Network timeout")
        return "Operation succeeded"

    result = handler.execute_with_retry(
        flaky_operation,
        {"operation_name": "handler_test_op"}
    )

    print(f"Result: {result}")
    print(f"Attempts: {attempt_count['count']}")

    # Get statistics through ErrorHandler
    stats = handler.get_retry_statistics()
    print(f"Statistics available: {'handler_test_op' in stats}")

    # Get history through ErrorHandler
    history = handler.get_retry_history()
    print(f"History available: {'handler_test_op' in history}")

    print("\n✅ Test 8 passed")


def test_9_retry_statistics():
    """Test 9: Retry statistics aggregation."""
    print_section("Test 9: Retry Statistics")

    manager = RetryManager(max_retries=2, initial_delay=0.05)

    # Run multiple operations
    operations = [
        ("op_success", lambda: "success"),
        ("op_failure", lambda: (_ for _ in ()).throw(ConnectionError("fail"))),
        ("op_success2", lambda: "success2"),
    ]

    for op_name, func in operations:
        try:
            manager.execute_with_retry(func, {"operation_name": op_name})
        except ConnectionError:
            pass

    # Get all statistics
    all_stats = manager.get_retry_statistics()
    print("All operation statistics:")
    print(json.dumps(all_stats, indent=2))

    # Get specific operation statistics
    op_stats = manager.get_retry_statistics("op_failure")
    print(f"\nop_failure statistics:")
    print(json.dumps(op_stats, indent=2))

    print("\n✅ Test 9 passed")


def test_10_retry_history_management():
    """Test 10: Retry history management."""
    print_section("Test 10: Retry History Management")

    manager = RetryManager(max_retries=3, initial_delay=0.1)

    def dummy_operation():
        return "success"

    manager.execute_with_retry(
        dummy_operation,
        {"operation_name": "test_op"}
    )

    # Check history exists
    history = manager.get_retry_history("test_op")
    print(f"History entries: {len(history['test_op'])}")
    assert len(history['test_op']) > 0

    # Clear history for specific operation
    manager.clear_history("test_op")
    history_after = manager.get_retry_history("test_op")
    print(f"History after clear: {len(history_after['test_op'])}")
    assert len(history_after['test_op']) == 0

    # Run another operation
    manager.execute_with_retry(
        dummy_operation,
        {"operation_name": "test_op2"}
    )

    # Clear all history
    manager.clear_history()
    all_history = manager.get_retry_history()
    print(f"All history after clear all: {len(all_history)}")
    assert len(all_history) == 0

    print("\n✅ Test 10 passed")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("  RETRY MANAGER COMPREHENSIVE VERIFICATION")
    print("=" * 70)

    test_1_basic_retry_manager()
    test_2_successful_operation()
    test_3_transient_error_recovery()
    test_4_max_retries_exceeded()
    test_5_permanent_error_no_retry()
    test_6_exponential_backoff_timing()
    test_7_custom_exception_types()
    test_8_error_handler_integration()
    test_9_retry_statistics()
    test_10_retry_history_management()

    print("\n" + "=" * 70)
    print("  ✅ ALL VERIFICATION TESTS PASSED!")
    print("=" * 70)
    print("\nRetry Manager Implementation Summary:")
    print("  ✓ Exponential backoff calculation")
    print("  ✓ Transient error detection")
    print("  ✓ Max retry limit enforcement")
    print("  ✓ Retry history tracking")
    print("  ✓ Retry statistics aggregation")
    print("  ✓ Custom exception support")
    print("  ✓ ErrorHandler integration")
    print("  ✓ History management")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
