#!/usr/bin/env python3
"""
Unit tests for RetryManager

Tests retry logic, exponential backoff, and error handling.
"""

import time
from unittest.mock import patch

import pytest

from retry_manager import RetryManager, RetryAttempt


class TestRetryManager:
    """Test retry manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = RetryManager(
            max_retries=3,
            backoff_base=2.0,
            initial_delay=0.1,  # Use small delay for tests
            max_delay=10.0,
        )

    def test_calculate_delay_first_attempt(self):
        """Test that first attempt has zero delay."""
        delay = self.manager.calculate_delay(0)
        assert delay == 0.0

    def test_calculate_delay_exponential_backoff(self):
        """Test exponential backoff calculation."""
        # Attempt 0: 0s
        assert self.manager.calculate_delay(0) == 0.0
        # Attempt 1: 0.1s (initial_delay)
        assert self.manager.calculate_delay(1) == 0.1
        # Attempt 2: 0.2s (initial_delay * 2^1)
        assert self.manager.calculate_delay(2) == 0.2
        # Attempt 3: 0.4s (initial_delay * 2^2)
        assert self.manager.calculate_delay(3) == 0.4
        # Attempt 4: 0.8s (initial_delay * 2^3)
        assert self.manager.calculate_delay(4) == 0.8

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        # Create manager with small max_delay
        manager = RetryManager(
            max_retries=10,
            backoff_base=2.0,
            initial_delay=1.0,
            max_delay=5.0,
        )

        # With large attempt number, delay should be capped
        delay = manager.calculate_delay(20)
        assert delay == 5.0

    def test_is_transient_error_connection_error(self):
        """Test that ConnectionError is recognized as transient."""
        error = ConnectionError("Connection refused")
        assert self.manager.is_transient_error(error) is True

    def test_is_transient_error_timeout_error(self):
        """Test that TimeoutError is recognized as transient."""
        error = TimeoutError("Operation timed out")
        assert self.manager.is_transient_error(error) is True

    def test_is_transient_error_os_error_network(self):
        """Test that network OSError is recognized as transient."""
        error = OSError("Network unreachable")
        assert self.manager.is_transient_error(error) is True

    def test_is_transient_error_message_based(self):
        """Test transient error detection based on error message."""
        # Test various transient error messages
        test_cases = [
            "timeout occurred",
            "connection was reset",
            "temporary failure, try again",
            "rate limit exceeded",
            "deadline exceeded",
        ]

        for message in test_cases:
            error = Exception(message)
            assert self.manager.is_transient_error(error) is True, f"Failed for: {message}"

    def test_is_transient_error_permanent(self):
        """Test that permanent errors are not recognized as transient."""
        error = ValueError("Invalid input")
        assert self.manager.is_transient_error(error) is False

    def test_execute_with_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        def successful_func():
            return "success"

        result = self.manager.execute_with_retry(
            successful_func,
            {"operation_name": "test_success"}
        )

        assert result == "success"

        # Check history
        history = self.manager.get_retry_history("test_success")
        assert len(history) == 1
        assert history[0]["success"] is True
        assert history[0]["attempt_number"] == 1

    def test_execute_with_retry_transient_error_recovery(self):
        """Test recovery from transient error."""
        call_count = {"count": 0}

        def flaky_func():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise ConnectionError("Simulated transient error")
            return "recovered"

        result = self.manager.execute_with_retry(
            flaky_func,
            {"operation_name": "test_flaky"}
        )

        assert result == "recovered"
        assert call_count["count"] == 2

        # Check history
        history = self.manager.get_retry_history("test_flaky")
        assert len(history) == 2
        assert history[0]["success"] is False
        assert history[1]["success"] is True

    def test_execute_with_retry_multiple_retries(self):
        """Test multiple retry attempts."""
        call_count = {"count": 0}

        def very_flaky_func():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise TimeoutError("Simulated timeout")
            return "finally succeeded"

        result = self.manager.execute_with_retry(
            very_flaky_func,
            {"operation_name": "test_very_flaky"}
        )

        assert result == "finally succeeded"
        assert call_count["count"] == 3

        # Check history
        history = self.manager.get_retry_history("test_very_flaky")
        assert len(history) == 3
        assert history[0]["success"] is False
        assert history[1]["success"] is False
        assert history[2]["success"] is True

    def test_execute_with_retry_max_retries_exceeded(self):
        """Test that max retries limit is enforced."""
        def always_failing_func():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            self.manager.execute_with_retry(
                always_failing_func,
                {"operation_name": "test_always_fails"}
            )

        # Should have attempted max_retries + 1 times (initial + retries)
        history = self.manager.get_retry_history("test_always_fails")
        assert len(history) == 4  # 1 initial + 3 retries
        assert all(not attempt["success"] for attempt in history)

    def test_execute_with_retry_permanent_error_no_retry(self):
        """Test that permanent errors don't trigger retries."""
        call_count = {"count": 0}

        def permanent_error_func():
            call_count["count"] += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError, match="Invalid input"):
            self.manager.execute_with_retry(
                permanent_error_func,
                {"operation_name": "test_permanent_error"}
            )

        # Should only attempt once (no retries for permanent errors)
        assert call_count["count"] == 1
        history = self.manager.get_retry_history("test_permanent_error")
        assert len(history) == 1

    def test_execute_with_retry_custom_retry_on(self):
        """Test custom retry_on exception types."""
        class CustomError(Exception):
            pass

        call_count = {"count": 0}

        def custom_error_func():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise CustomError("Custom transient error")
            return "recovered"

        result = self.manager.execute_with_retry(
            custom_error_func,
            {
                "operation_name": "test_custom_error",
                "retry_on": (CustomError,),
            }
        )

        assert result == "recovered"
        assert call_count["count"] == 2

    def test_execute_with_retry_missing_operation_name(self):
        """Test that operation_name is required in context."""
        def dummy_func():
            return "result"

        with pytest.raises(ValueError, match="operation_name must be provided"):
            self.manager.execute_with_retry(
                dummy_func,
                {}  # Missing operation_name
            )

    def test_execute_with_retry_with_function_args(self):
        """Test that function arguments are passed correctly."""
        def func_with_args(a, b, c=None):
            return a + b + (c or 0)

        result = self.manager.execute_with_retry(
            func_with_args,
            {"operation_name": "test_args"},
            1,
            2,
            c=3,
        )

        assert result == 6

    def test_get_retry_history_single_operation(self):
        """Test getting retry history for a single operation."""
        def flaky_func():
            raise ConnectionError("Fail")

        try:
            self.manager.execute_with_retry(
                flaky_func,
                {"operation_name": "test_history"}
            )
        except ConnectionError:
            pass

        history = self.manager.get_retry_history("test_history")
        assert isinstance(history, dict)
        assert "test_history" in history
        assert len(history["test_history"]) == 4  # max_retries + 1

    def test_get_retry_history_all_operations(self):
        """Test getting retry history for all operations."""
        def func1():
            return "success1"

        def func2():
            return "success2"

        self.manager.execute_with_retry(
            func1,
            {"operation_name": "op1"}
        )
        self.manager.execute_with_retry(
            func2,
            {"operation_name": "op2"}
        )

        history = self.manager.get_retry_history()
        assert "op1" in history
        assert "op2" in history
        assert len(history["op1"]) == 1
        assert len(history["op2"]) == 1

    def test_get_retry_statistics_single_operation(self):
        """Test getting retry statistics for a single operation."""
        def flaky_func():
            call_count = getattr(flaky_func, "count", 0) + 1
            flaky_func.count = call_count
            if call_count < 2:
                raise ConnectionError("Fail")
            return "success"

        try:
            self.manager.execute_with_retry(
                flaky_func,
                {"operation_name": "test_stats"}
            )
        except ConnectionError:
            pass

        stats = self.manager.get_retry_statistics("test_stats")
        assert stats["operation_name"] == "test_stats"
        assert stats["total_attempts"] >= 1
        assert "total_delay_seconds" in stats
        assert "success_rate" in stats

    def test_get_retry_statistics_all_operations(self):
        """Test getting retry statistics for all operations."""
        def func1():
            return "success1"

        def func2():
            return "success2"

        self.manager.execute_with_retry(
            func1,
            {"operation_name": "op1"}
        )
        self.manager.execute_with_retry(
            func2,
            {"operation_name": "op2"}
        )

        stats = self.manager.get_retry_statistics()
        assert isinstance(stats, dict)
        assert "op1" in stats
        assert "op2" in stats

    def test_clear_history_single_operation(self):
        """Test clearing history for a single operation."""
        def dummy_func():
            return "success"

        self.manager.execute_with_retry(
            dummy_func,
            {"operation_name": "test_clear"}
        )

        # Verify history exists
        assert "test_clear" in self.manager.retry_history

        # Clear history
        self.manager.clear_history("test_clear")

        # Verify history is cleared
        assert "test_clear" not in self.manager.retry_history

    def test_clear_history_all_operations(self):
        """Test clearing all retry history."""
        def dummy_func():
            return "success"

        self.manager.execute_with_retry(
            dummy_func,
            {"operation_name": "test_clear_all"}
        )

        # Verify history exists
        assert len(self.manager.retry_history) > 0

        # Clear all history
        self.manager.clear_history()

        # Verify all history is cleared
        assert len(self.manager.retry_history) == 0

    def test_retry_attempt_to_dict(self):
        """Test RetryAttempt serialization."""
        error = ConnectionError("Test error")
        attempt = RetryAttempt(
            attempt_number=2,
            delay_seconds=1.5,
            error_before=error,
            success=True,
        )

        result = attempt.to_dict()
        assert result["attempt_number"] == 2
        assert result["delay_seconds"] == 1.5
        assert result["error_before"] == "Test error"
        assert result["error_type"] == "ConnectionError"
        assert result["success"] is True
        assert "timestamp" in result

    def test_retry_attempt_with_no_error(self):
        """Test RetryAttempt with no error."""
        attempt = RetryAttempt(
            attempt_number=1,
            delay_seconds=0.0,
            success=True,
        )

        result = attempt.to_dict()
        assert result["error_before"] is None
        assert result["error_type"] is None


class TestRetryManagerIntegration:
    """Integration tests for retry manager."""

    def test_retry_with_delays(self):
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
        # First call: immediate
        # Second call: after ~0.05s
        # Third call: after ~0.10s
        # Total elapsed should be at least 0.15s
        assert elapsed >= 0.14, f"Expected at least 0.14s, got {elapsed:.2f}s"

    def test_different_operations_separate_history(self):
        """Test that different operations maintain separate retry histories."""
        manager = RetryManager(max_retries=2)

        def func_a():
            raise ConnectionError("A fails")

        def func_b():
            return "B succeeds"

        try:
            manager.execute_with_retry(
                func_a,
                {"operation_name": "operation_a"}
            )
        except ConnectionError:
            pass

        manager.execute_with_retry(
            func_b,
            {"operation_name": "operation_b"}
        )

        history_a = manager.get_retry_history("operation_a")
        history_b = manager.get_retry_history("operation_b")

        # Operation A should have multiple attempts (failed all)
        assert len(history_a["operation_a"]) == 3  # 1 initial + 2 retries

        # Operation B should have one attempt (succeeded)
        assert len(history_b["operation_b"]) == 1
        assert history_b["operation_b"][0]["success"] is True
