#!/usr/bin/env python3
"""
Simple test runner for RetryManager to verify basic functionality.
"""

import time
from retry_manager import RetryManager, RetryAttempt


def test_calculate_delay():
    """Test exponential backoff calculation."""
    manager = RetryManager(backoff_base=2.0, initial_delay=1.0)

    assert manager.calculate_delay(0) == 0.0, "First attempt should have 0 delay"
    assert manager.calculate_delay(1) == 1.0, "Second attempt should have 1s delay"
    assert manager.calculate_delay(2) == 2.0, "Third attempt should have 2s delay"
    assert manager.calculate_delay(3) == 4.0, "Fourth attempt should have 4s delay"

    print("✓ test_calculate_delay passed")


def test_is_transient_error():
    """Test transient error detection."""
    manager = RetryManager()

    # Test connection errors
    assert manager.is_transient_error(ConnectionError("Connection refused")) is True
    assert manager.is_transient_error(TimeoutError("Timed out")) is True

    # Test message-based detection
    assert manager.is_transient_error(Exception("timeout occurred")) is True
    assert manager.is_transient_error(Exception("temporary failure")) is True

    # Test permanent errors
    assert manager.is_transient_error(ValueError("Invalid input")) is False

    print("✓ test_is_transient_error passed")


def test_execute_success_on_first_attempt():
    """Test successful execution on first attempt."""
    manager = RetryManager()

    def successful_func():
        return "success"

    result = manager.execute_with_retry(
        successful_func,
        {"operation_name": "test_success"}
    )

    assert result == "success"
    history = manager.get_retry_history("test_success")
    assert len(history["test_success"]) == 1
    assert history["test_success"][0]["success"] is True

    print("✓ test_execute_success_on_first_attempt passed")


def test_execute_with_transient_error_recovery():
    """Test recovery from transient error."""
    manager = RetryManager()

    call_count = {"count": 0}

    def flaky_func():
        call_count["count"] += 1
        if call_count["count"] < 2:
            raise ConnectionError("Simulated transient error")
        return "recovered"

    result = manager.execute_with_retry(
        flaky_func,
        {"operation_name": "test_flaky"}
    )

    assert result == "recovered"
    assert call_count["count"] == 2

    history = manager.get_retry_history("test_flaky")
    assert len(history["test_flaky"]) == 2
    assert history["test_flaky"][0]["success"] is False
    assert history["test_flaky"][1]["success"] is True

    print("✓ test_execute_with_transient_error_recovery passed")


def test_execute_with_max_retries_exceeded():
    """Test that max retries limit is enforced."""
    manager = RetryManager(max_retries=2)

    def always_failing_func():
        raise ConnectionError("Always fails")

    try:
        manager.execute_with_retry(
            always_failing_func,
            {"operation_name": "test_always_fails"}
        )
        assert False, "Should have raised ConnectionError"
    except ConnectionError:
        pass

    history = manager.get_retry_history("test_always_fails")
    assert len(history["test_always_fails"]) == 3  # 1 initial + 2 retries

    print("✓ test_execute_with_max_retries_exceeded passed")


def test_execute_with_permanent_error_no_retry():
    """Test that permanent errors don't trigger retries."""
    manager = RetryManager()

    call_count = {"count": 0}

    def permanent_error_func():
        call_count["count"] += 1
        raise ValueError("Invalid input")

    try:
        manager.execute_with_retry(
            permanent_error_func,
            {"operation_name": "test_permanent_error"}
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    assert call_count["count"] == 1, "Should only attempt once"

    print("✓ test_execute_with_permanent_error_no_retry passed")


def test_get_retry_statistics():
    """Test getting retry statistics."""
    manager = RetryManager()

    def flaky_func():
        call_count = getattr(flaky_func, "count", 0) + 1
        flaky_func.count = call_count
        if call_count < 2:
            raise ConnectionError("Fail")
        return "success"

    try:
        manager.execute_with_retry(
            flaky_func,
            {"operation_name": "test_stats"}
        )
    except ConnectionError:
        pass

    stats = manager.get_retry_statistics("test_stats")
    assert stats["operation_name"] == "test_stats"
    assert stats["total_attempts"] >= 1
    assert "total_delay_seconds" in stats

    print("✓ test_get_retry_statistics passed")


def test_clear_history():
    """Test clearing retry history."""
    manager = RetryManager()

    def dummy_func():
        return "success"

    manager.execute_with_retry(
        dummy_func,
        {"operation_name": "test_clear"}
    )

    assert "test_clear" in manager.retry_history

    manager.clear_history("test_clear")

    assert "test_clear" not in manager.retry_history

    print("✓ test_clear_history passed")


def test_retry_with_delays():
    """Test that retries actually wait with appropriate delays."""
    manager = RetryManager(
        max_retries=2,
        initial_delay=0.05,
        backoff_base=2.0,
    )

    call_times = []

    def timed_func():
        call_times.append(time.time())
        count = len(call_times)
        if count < 3:
            raise ConnectionError(f"Attempt {count}")
        return "success"

    start_time = time.time()
    result = manager.execute_with_retry(
        timed_func,
        {"operation_name": "test_delays"}
    )
    elapsed = time.time() - start_time

    assert result == "success"
    assert len(call_times) == 3

    # Check that delays were applied
    assert elapsed >= 0.14, f"Expected at least 0.14s, got {elapsed:.2f}s"

    print("✓ test_retry_with_delays passed")


def main():
    """Run all tests."""
    print("Running RetryManager tests...\n")

    test_calculate_delay()
    test_is_transient_error()
    test_execute_success_on_first_attempt()
    test_execute_with_transient_error_recovery()
    test_execute_with_max_retries_exceeded()
    test_execute_with_permanent_error_no_retry()
    test_get_retry_statistics()
    test_clear_history()
    test_retry_with_delays()

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    main()
