#!/usr/bin/env python3
"""
Simple test runner for ErrorHandler (no pytest dependency)
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from error_handler import (
    Error,
    ErrorCategory,
    ErrorHandler,
    ErrorType,
    RecoveryResult,
    RecoveryStrategy,
)


class TestRunner:
    """Simple test runner."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def run_test(self, test_func):
        """Run a test function."""
        test_name = test_func.__name__
        try:
            test_func()
            self.passed += 1
            self.tests.append((test_name, "PASSED"))
            print(f"✓ {test_name}")
        except AssertionError as e:
            self.failed += 1
            self.tests.append((test_name, "FAILED", str(e)))
            print(f"✗ {test_name}: {e}")
        except Exception as e:
            self.failed += 1
            self.tests.append((test_name, "ERROR", str(e)))
            print(f"✗ {test_name}: ERROR - {e}")

    def summary(self):
        """Print test summary."""
        print(f"\n{'='*60}")
        print(f"Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"{'='*60}")

        if self.failed > 0:
            print("\nFailed tests:")
            for test in self.tests:
                if len(test) > 1 and test[1] != "PASSED":
                    print(f"  - {test[0]}: {test[1]}")
            return False
        return True


def test_detect_no_error():
    """Test that normal output doesn't trigger error detection."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation completed successfully")
    assert error is None, "Should not detect error in normal output"


def test_detect_timeout_error():
    """Test detection of timeout errors."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation timed out after 30 seconds")
    assert error is not None, "Should detect timeout error"
    assert error.category == ErrorCategory.TRANSIENT, "Timeout should be transient"
    assert error.error_type == ErrorType.TIMEOUT, "Should be TIMEOUT type"


def test_detect_network_error():
    """Test detection of network errors."""
    handler = ErrorHandler()
    error = handler.detect_error("Connection refused by remote host")
    assert error is not None, "Should detect network error"
    assert error.category == ErrorCategory.TRANSIENT, "Network error should be transient"
    assert error.error_type == ErrorType.NETWORK, "Should be NETWORK type"


def test_detect_rate_limit_error():
    """Test detection of rate limit errors."""
    handler = ErrorHandler()
    error = handler.detect_error("API rate limit exceeded, please retry later")
    assert error is not None, "Should detect rate limit error"
    assert error.error_type == ErrorType.RATE_LIMITED, "Should be RATE_LIMITED type"


def test_detect_syntax_error():
    """Test detection of syntax errors."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax at line 42")
    assert error is not None, "Should detect syntax error"
    assert error.category == ErrorCategory.PERMANENT, "Syntax error should be permanent"
    assert error.error_type == ErrorType.SYNTAX_ERROR, "Should be SYNTAX_ERROR type"


def test_detect_import_error():
    """Test detection of import errors."""
    handler = ErrorHandler()
    error = handler.detect_error("ImportError: No module named 'requests'")
    assert error is not None, "Should detect import error"
    assert error.category == ErrorCategory.PERMANENT, "Import error should be permanent"
    assert error.error_type == ErrorType.IMPORT_ERROR, "Should be IMPORT_ERROR type"


def test_detect_file_not_found_error():
    """Test detection of file not found errors."""
    handler = ErrorHandler()
    error = handler.detect_error("FileNotFoundError: No such file or directory: '/path'")
    assert error is not None, "Should detect file not found error"
    assert error.error_type == ErrorType.FILE_NOT_FOUND, "Should be FILE_NOT_FOUND type"


def test_detect_permission_denied_error():
    """Test detection of permission errors."""
    handler = ErrorHandler()
    error = handler.detect_error("Permission denied: cannot access file")
    assert error is not None, "Should detect permission error"
    assert error.error_type == ErrorType.PERMISSION_DENIED, "Should be PERMISSION_DENIED type"


def test_detect_dependency_missing_error():
    """Test detection of missing dependency errors."""
    handler = ErrorHandler()
    error = handler.detect_error("dependency 'numpy' not found")
    assert error is not None, "Should detect dependency missing error"
    assert error.error_type == ErrorType.DEPENDENCY_MISSING, "Should be DEPENDENCY_MISSING type"


def test_detect_ambiguous_error():
    """Test detection of ambiguous errors."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred during processing")
    assert error is not None, "Should detect ambiguous error"
    assert error.category == ErrorCategory.AMBIGUOUS, "Should be AMBIGUOUS category"


def test_detect_error_with_exit_code():
    """Test error detection with exit code."""
    handler = ErrorHandler()
    error = handler.detect_error("", source="test", exit_code=1)
    assert error is not None, "Should detect error from exit code"
    assert error.exit_code == 1, "Exit code should be 1"


def test_detect_error_with_context():
    """Test error detection with additional context."""
    handler = ErrorHandler()
    context = {"task_id": "task-123", "attempt": 2}
    error = handler.detect_error("timeout", context=context)
    assert error is not None, "Should detect error"
    assert error.context == context, "Context should be preserved"


def test_classify_transient_error():
    """Test classification of transient errors."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation timed out")
    category = handler.classify_error(error)
    assert category == ErrorCategory.TRANSIENT, "Should be TRANSIENT category"


def test_classify_permanent_error():
    """Test classification of permanent errors."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    category = handler.classify_error(error)
    assert category == ErrorCategory.PERMANENT, "Should be PERMANENT category"


def test_classify_ambiguous_error():
    """Test classification of ambiguous errors."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred")
    category = handler.classify_error(error)
    assert category == ErrorCategory.AMBIGUOUS, "Should be AMBIGUOUS category"


def test_strategy_for_transient_error():
    """Test strategy selection for transient errors."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation timed out")
    strategy = handler.select_recovery_strategy(error)
    assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF, "Should use RETRY_WITH_BACKOFF"


def test_strategy_for_permanent_error_with_checkpoint():
    """Test strategy selection for permanent errors with checkpoint."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    strategy = handler.select_recovery_strategy(error, context={"has_checkpoint": True})
    assert strategy == RecoveryStrategy.ROLLBACK_TO_CHECKPOINT, "Should use ROLLBACK_TO_CHECKPOINT"


def test_strategy_for_permanent_error_without_checkpoint():
    """Test strategy selection for permanent errors without checkpoint."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    strategy = handler.select_recovery_strategy(error, context={"has_checkpoint": False})
    assert strategy == RecoveryStrategy.ALTERNATIVE_APPROACH, "Should use ALTERNATIVE_APPROACH"


def test_strategy_for_ambiguous_error():
    """Test strategy selection for ambiguous errors."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred")
    strategy = handler.select_recovery_strategy(error)
    assert strategy == RecoveryStrategy.REQUEST_HUMAN_INPUT, "Should use REQUEST_HUMAN_INPUT"


def test_strategy_for_ambiguous_error_with_skip():
    """Test strategy selection for ambiguous errors when skip is allowed."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred")
    strategy = handler.select_recovery_strategy(error, context={"can_skip": True})
    assert strategy == RecoveryStrategy.SKIP_AND_CONTINUE, "Should use SKIP_AND_CONTINUE"


def test_strategy_for_transient_error_exhausted_retries():
    """Test strategy selection when retries are exhausted."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation timed out")
    strategy = handler.select_recovery_strategy(error, context={"retry_count": 10})
    assert strategy == RecoveryStrategy.ESCALATE, "Should use ESCALATE when retries exhausted"


def test_execute_retry_with_backoff():
    """Test execution of retry with backoff strategy."""
    handler = ErrorHandler()
    context = {"command": "pytest tests/", "retry_count": 0}
    result = handler.execute_recovery(RecoveryStrategy.RETRY_WITH_BACKOFF, context)

    assert isinstance(result, RecoveryResult), "Should return RecoveryResult"
    assert result.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF, "Strategy should match"
    assert result.success is True, "Should be successful"
    assert result.retry_count == 1, "Retry count should increment"
    assert "retry" in result.next_action, "Next action should be retry"


def test_execute_retry_exponential_backoff():
    """Test exponential backoff delay calculation."""
    handler = ErrorHandler()
    command = "pytest tests/"

    for i in range(5):
        context = {"command": command, "retry_count": i}
        result = handler.execute_recovery(RecoveryStrategy.RETRY_WITH_BACKOFF, context)
        assert result.retry_count == i + 1, f"Retry count should be {i + 1}"


def test_execute_alternative_approach():
    """Test execution of alternative approach strategy."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    result = handler.execute_recovery(
        RecoveryStrategy.ALTERNATIVE_APPROACH,
        {"error": error}
    )

    assert result.strategy == RecoveryStrategy.ALTERNATIVE_APPROACH, "Strategy should match"
    assert result.success is True, "Should be successful"
    assert result.next_action == "try_alternative", "Next action should be try_alternative"


def test_execute_rollback_to_checkpoint():
    """Test execution of rollback to checkpoint strategy."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    result = handler.execute_recovery(
        RecoveryStrategy.ROLLBACK_TO_CHECKPOINT,
        {"error": error, "checkpoint_id": "checkpoint-abc123"}
    )

    assert result.strategy == RecoveryStrategy.ROLLBACK_TO_CHECKPOINT, "Strategy should match"
    assert result.success is True, "Should be successful"
    assert "checkpoint-abc123" in result.next_action, "Next action should include checkpoint ID"


def test_execute_request_human_input():
    """Test execution of request human input strategy."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred")
    result = handler.execute_recovery(
        RecoveryStrategy.REQUEST_HUMAN_INPUT,
        {"error": error}
    )

    assert result.strategy == RecoveryStrategy.REQUEST_HUMAN_INPUT, "Strategy should match"
    assert result.success is False, "Should not be successful"
    assert result.next_action == "wait_for_human_input", "Next action should wait for human"
    assert "Human input required" in result.message, "Message should indicate human input needed"


def test_execute_skip_and_continue():
    """Test execution of skip and continue strategy."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred")
    result = handler.execute_recovery(
        RecoveryStrategy.SKIP_AND_CONTINUE,
        {"error": error}
    )

    assert result.strategy == RecoveryStrategy.SKIP_AND_CONTINUE, "Strategy should match"
    assert result.success is True, "Should be successful"
    assert result.next_action == "continue_to_next_task", "Next action should continue"


def test_execute_escalate():
    """Test execution of escalate strategy."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation timed out")
    result = handler.execute_recovery(
        RecoveryStrategy.ESCALATE,
        {"error": error, "retry_count": 5}
    )

    assert result.strategy == RecoveryStrategy.ESCALATE, "Strategy should match"
    assert result.success is False, "Should not be successful"
    assert result.next_action == "escalate_to_human", "Next action should escalate"


def test_successful_subprocess():
    """Test handling of successful subprocess execution."""
    handler = ErrorHandler()
    result = subprocess.CompletedProcess(
        args=["echo", "hello"],
        returncode=0,
        stdout=b"hello\n",
        stderr=b"",
    )

    error, recovery = handler.handle_subprocess_result(result, "echo hello")

    assert error is None, "Should not detect error"
    assert recovery is None, "Should not suggest recovery"


def test_failed_subprocess_with_error():
    """Test handling of failed subprocess execution."""
    handler = ErrorHandler()
    result = subprocess.CompletedProcess(
        args=["ls", "/nonexistent"],
        returncode=2,
        stdout=b"",
        stderr=b"ls: cannot access '/nonexistent': No such file or directory",
    )

    error, recovery = handler.handle_subprocess_result(result, "ls /nonexistent")

    assert error is not None, "Should detect error"
    assert error.exit_code == 2, "Exit code should be 2"
    assert error.category == ErrorCategory.PERMANENT, "Should be PERMANENT error"
    assert recovery is not None, "Should suggest recovery strategy"


def test_subprocess_with_timeout():
    """Test handling of subprocess timeout."""
    handler = ErrorHandler()
    result = subprocess.CompletedProcess(
        args=["sleep", "30"],
        returncode=124,
        stdout=b"",
        stderr=b"Operation timed out",
    )

    error, recovery = handler.handle_subprocess_result(result, "sleep 30")

    assert error is not None, "Should detect error"
    assert error.category == ErrorCategory.TRANSIENT, "Should be TRANSIENT error"
    assert recovery is not None, "Should suggest recovery strategy"
    assert recovery.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF, "Should use RETRY_WITH_BACKOFF"


def test_subprocess_increments_retry_count():
    """Test that subprocess handling increments retry count."""
    handler = ErrorHandler()
    result = subprocess.CompletedProcess(
        args=["pytest"],
        returncode=1,
        stdout=b"",
        stderr=b"Operation timed out",
    )

    _, recovery1 = handler.handle_subprocess_result(result, "pytest", context={"retry_count": 0})
    assert recovery1.retry_count == 1, "First retry should have count 1"

    _, recovery2 = handler.handle_subprocess_result(result, "pytest", context={"retry_count": 1})
    assert recovery2.retry_count == 2, "Second retry should have count 2"


def test_error_logging():
    """Test that errors are logged."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    handler.error_log.append(error)

    assert len(handler.error_log) == 1, "Should have one error logged"
    assert handler.error_log[0].error_type == ErrorType.SYNTAX_ERROR, "Should log SYNTAX_ERROR"


def test_error_summary_empty():
    """Test error summary with no errors."""
    handler = ErrorHandler()
    summary = handler.get_error_summary()

    assert summary["total_errors"] == 0, "Should have zero errors"
    assert summary["by_category"] == {}, "Should have no categories"
    assert summary["by_type"] == {}, "Should have no types"


def test_error_summary_with_errors():
    """Test error summary with multiple errors."""
    handler = ErrorHandler()
    # Manually add errors to the log (detect_error doesn't auto-add)
    error1 = handler.detect_error("Operation timed out")
    error2 = handler.detect_error("SyntaxError: invalid syntax")
    error3 = handler.detect_error("Operation timed out")
    handler.error_log.extend([error1, error2, error3])

    summary = handler.get_error_summary()

    assert summary["total_errors"] == 3, "Should have three errors"
    assert summary["by_category"]["transient"] == 2, "Should have two transient errors"
    assert summary["by_category"]["permanent"] == 1, "Should have one permanent error"


def test_save_error_log():
    """Test saving error log to file."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    handler.error_log.append(error)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        filepath = Path(f.name)

    try:
        saved_path = handler.save_error_log(filepath)
        assert saved_path == filepath, "Should save to specified path"

        with open(saved_path) as f:
            data = json.load(f)

        assert "errors" in data, "Should have errors key"
        assert len(data["errors"]) == 1, "Should have one error"
        assert data["errors"][0]["error_type"] == "syntax_error", "Should be syntax_error"
    finally:
        filepath.unlink(missing_ok=True)


def test_error_to_dict():
    """Test error serialization to dictionary."""
    error = Error(
        error_id="abc123",
        timestamp="2024-01-01T00:00:00Z",
        error_type=ErrorType.SYNTAX_ERROR,
        category=ErrorCategory.PERMANENT,
        message="Invalid syntax",
        source="test",
        context={"test": "value"},
    )

    data = error.to_dict()

    assert data["error_id"] == "abc123", "Error ID should match"
    assert data["error_type"] == "syntax_error", "Error type should be serialized"
    assert data["category"] == "permanent", "Category should be serialized"


def test_recovery_result_to_dict():
    """Test recovery result serialization to dictionary."""
    result = RecoveryResult(
        strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
        success=True,
        message="Retrying...",
        retry_count=2,
        next_action="retry",
    )

    data = result.to_dict()

    assert data["strategy"] == "retry_with_backoff", "Strategy should be serialized"
    assert data["success"] is True, "Success should be True"
    assert data["retry_count"] == 2, "Retry count should be 2"


def test_suggestion_for_timeout():
    """Test suggestion for timeout errors."""
    handler = ErrorHandler()
    error = handler.detect_error("Operation timed out")
    assert "timeout" in error.suggestion.lower(), "Suggestion should mention timeout"


def test_suggestion_for_syntax_error():
    """Test suggestion for syntax errors."""
    handler = ErrorHandler()
    error = handler.detect_error("SyntaxError: invalid syntax")
    assert "syntax" in error.suggestion.lower(), "Suggestion should mention syntax"


def test_suggestion_for_import_error():
    """Test suggestion for import errors."""
    handler = ErrorHandler()
    error = handler.detect_error("ImportError: No module named")
    assert ("dependency" in error.suggestion.lower() or "install" in error.suggestion.lower()), \
        "Suggestion should mention dependency or install"


def test_suggestion_for_ambiguous_error():
    """Test suggestion for ambiguous errors."""
    handler = ErrorHandler()
    error = handler.detect_error("An error occurred")
    assert "investigation" in error.suggestion.lower(), "Suggestion should mention investigation"


def main():
    """Run all tests."""
    print("Running ErrorHandler tests...\n")

    runner = TestRunner()

    # Test error detection
    print("Error Detection Tests:")
    runner.run_test(test_detect_no_error)
    runner.run_test(test_detect_timeout_error)
    runner.run_test(test_detect_network_error)
    runner.run_test(test_detect_rate_limit_error)
    runner.run_test(test_detect_syntax_error)
    runner.run_test(test_detect_import_error)
    runner.run_test(test_detect_file_not_found_error)
    runner.run_test(test_detect_permission_denied_error)
    runner.run_test(test_detect_dependency_missing_error)
    runner.run_test(test_detect_ambiguous_error)
    runner.run_test(test_detect_error_with_exit_code)
    runner.run_test(test_detect_error_with_context)

    # Test error classification
    print("\nError Classification Tests:")
    runner.run_test(test_classify_transient_error)
    runner.run_test(test_classify_permanent_error)
    runner.run_test(test_classify_ambiguous_error)

    # Test recovery strategy selection
    print("\nRecovery Strategy Selection Tests:")
    runner.run_test(test_strategy_for_transient_error)
    runner.run_test(test_strategy_for_permanent_error_with_checkpoint)
    runner.run_test(test_strategy_for_permanent_error_without_checkpoint)
    runner.run_test(test_strategy_for_ambiguous_error)
    runner.run_test(test_strategy_for_ambiguous_error_with_skip)
    runner.run_test(test_strategy_for_transient_error_exhausted_retries)

    # Test recovery execution
    print("\nRecovery Execution Tests:")
    runner.run_test(test_execute_retry_with_backoff)
    runner.run_test(test_execute_retry_exponential_backoff)
    runner.run_test(test_execute_alternative_approach)
    runner.run_test(test_execute_rollback_to_checkpoint)
    runner.run_test(test_execute_request_human_input)
    runner.run_test(test_execute_skip_and_continue)
    runner.run_test(test_execute_escalate)

    # Test subprocess handling
    print("\nSubprocess Handling Tests:")
    runner.run_test(test_successful_subprocess)
    runner.run_test(test_failed_subprocess_with_error)
    runner.run_test(test_subprocess_with_timeout)
    runner.run_test(test_subprocess_increments_retry_count)

    # Test error logging
    print("\nError Logging Tests:")
    runner.run_test(test_error_logging)
    runner.run_test(test_error_summary_empty)
    runner.run_test(test_error_summary_with_errors)
    runner.run_test(test_save_error_log)

    # Test serialization
    print("\nSerialization Tests:")
    runner.run_test(test_error_to_dict)
    runner.run_test(test_recovery_result_to_dict)

    # Test suggestions
    print("\nSuggestion Tests:")
    runner.run_test(test_suggestion_for_timeout)
    runner.run_test(test_suggestion_for_syntax_error)
    runner.run_test(test_suggestion_for_import_error)
    runner.run_test(test_suggestion_for_ambiguous_error)

    # Print summary
    success = runner.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
