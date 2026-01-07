#!/usr/bin/env python3
"""
Unit tests for ErrorHandler

Tests error detection, classification, and recovery strategy selection.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from error_handler import (
    Error,
    ErrorCategory,
    ErrorHandler,
    ErrorType,
    RecoveryResult,
    RecoveryStrategy,
)


class TestErrorDetection:
    """Test error detection from various sources."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_detect_no_error(self):
        """Test that normal output doesn't trigger error detection."""
        output = "Operation completed successfully"
        error = self.handler.detect_error(output)

        assert error is None

    def test_detect_timeout_error(self):
        """Test detection of timeout errors."""
        output = "Operation timed out after 30 seconds"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.TRANSIENT
        assert error.error_type == ErrorType.TIMEOUT

    def test_detect_network_error(self):
        """Test detection of network errors."""
        output = "Connection refused by remote host"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.TRANSIENT
        assert error.error_type == ErrorType.NETWORK

    def test_detect_rate_limit_error(self):
        """Test detection of rate limit errors."""
        output = "API rate limit exceeded, please retry later"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.TRANSIENT
        assert error.error_type == ErrorType.RATE_LIMITED

    def test_detect_syntax_error(self):
        """Test detection of syntax errors."""
        output = "SyntaxError: invalid syntax at line 42"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.PERMANENT
        assert error.error_type == ErrorType.SYNTAX_ERROR

    def test_detect_import_error(self):
        """Test detection of import errors."""
        output = "ImportError: No module named 'requests'"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.PERMANENT
        assert error.error_type == ErrorType.IMPORT_ERROR

    def test_detect_file_not_found_error(self):
        """Test detection of file not found errors."""
        output = "FileNotFoundError: No such file or directory: '/path/to/file'"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.PERMANENT
        assert error.error_type == ErrorType.FILE_NOT_FOUND

    def test_detect_permission_denied_error(self):
        """Test detection of permission errors."""
        output = "Permission denied: cannot access file"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.PERMANENT
        assert error.error_type == ErrorType.PERMISSION_DENIED

    def test_detect_dependency_missing_error(self):
        """Test detection of missing dependency errors."""
        output = "dependency 'numpy' not found"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.PERMANENT
        assert error.error_type == ErrorType.DEPENDENCY_MISSING

    def test_detect_ambiguous_error(self):
        """Test detection of ambiguous errors."""
        output = "An error occurred during processing"
        error = self.handler.detect_error(output)

        assert error is not None
        assert error.category == ErrorCategory.AMBIGUOUS

    def test_detect_error_with_exit_code(self):
        """Test error detection with exit code."""
        error = self.handler.detect_error(
            output="",
            source="test",
            exit_code=1,
        )

        assert error is not None
        assert error.exit_code == 1

    def test_detect_error_with_context(self):
        """Test error detection with additional context."""
        context = {"task_id": "task-123", "attempt": 2}
        error = self.handler.detect_error(
            output="timeout",
            context=context,
        )

        assert error is not None
        assert error.context == context


class TestErrorClassification:
    """Test error classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_classify_transient_error(self):
        """Test classification of transient errors."""
        error = self.handler.detect_error("Operation timed out")
        category = self.handler.classify_error(error)

        assert category == ErrorCategory.TRANSIENT

    def test_classify_permanent_error(self):
        """Test classification of permanent errors."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        category = self.handler.classify_error(error)

        assert category == ErrorCategory.PERMANENT

    def test_classify_ambiguous_error(self):
        """Test classification of ambiguous errors."""
        error = self.handler.detect_error("An error occurred")
        category = self.handler.classify_error(error)

        assert category == ErrorCategory.AMBIGUOUS


class TestRecoveryStrategySelection:
    """Test recovery strategy selection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_strategy_for_transient_error(self):
        """Test strategy selection for transient errors."""
        error = self.handler.detect_error("Operation timed out")
        strategy = self.handler.select_recovery_strategy(error)

        assert strategy == RecoveryStrategy.RETRY_WITH_BACKOFF

    def test_strategy_for_permanent_error_with_checkpoint(self):
        """Test strategy selection for permanent errors with checkpoint."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        strategy = self.handler.select_recovery_strategy(
            error,
            context={"has_checkpoint": True},
        )

        assert strategy == RecoveryStrategy.ROLLBACK_TO_CHECKPOINT

    def test_strategy_for_permanent_error_without_checkpoint(self):
        """Test strategy selection for permanent errors without checkpoint."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        strategy = self.handler.select_recovery_strategy(
            error,
            context={"has_checkpoint": False},
        )

        assert strategy == RecoveryStrategy.ALTERNATIVE_APPROACH

    def test_strategy_for_ambiguous_error(self):
        """Test strategy selection for ambiguous errors."""
        error = self.handler.detect_error("An error occurred")
        strategy = self.handler.select_recovery_strategy(error)

        assert strategy == RecoveryStrategy.REQUEST_HUMAN_INPUT

    def test_strategy_for_ambiguous_error_with_skip(self):
        """Test strategy selection for ambiguous errors when skip is allowed."""
        error = self.handler.detect_error("An error occurred")
        strategy = self.handler.select_recovery_strategy(
            error,
            context={"can_skip": True},
        )

        assert strategy == RecoveryStrategy.SKIP_AND_CONTINUE

    def test_strategy_for_transient_error_exhausted_retries(self):
        """Test strategy selection when retries are exhausted."""
        error = self.handler.detect_error("Operation timed out")
        strategy = self.handler.select_recovery_strategy(
            error,
            context={"retry_count": 10},  # Exceeds max_retries
        )

        assert strategy == RecoveryStrategy.ESCALATE


class TestRecoveryExecution:
    """Test recovery strategy execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_execute_retry_with_backoff(self):
        """Test execution of retry with backoff strategy."""
        context = {
            "command": "pytest tests/",
            "retry_count": 0,
        }

        result = self.handler.execute_recovery(
            RecoveryStrategy.RETRY_WITH_BACKOFF,
            context,
        )

        assert isinstance(result, RecoveryResult)
        assert result.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
        assert result.success is True
        assert result.retry_count == 1
        assert "retry" in result.next_action

    def test_execute_retry_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        command = "pytest tests/"

        for i in range(5):
            context = {
                "command": command,
                "retry_count": i,
            }
            result = self.handler.execute_recovery(
                RecoveryStrategy.RETRY_WITH_BACKOFF,
                context,
            )

            # Verify retry count increments
            assert result.retry_count == i + 1

    def test_execute_alternative_approach(self):
        """Test execution of alternative approach strategy."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        context = {"error": error}

        result = self.handler.execute_recovery(
            RecoveryStrategy.ALTERNATIVE_APPROACH,
            context,
        )

        assert result.strategy == RecoveryStrategy.ALTERNATIVE_APPROACH
        assert result.success is True
        assert result.next_action == "try_alternative"

    def test_execute_rollback_to_checkpoint(self):
        """Test execution of rollback to checkpoint strategy."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        context = {
            "error": error,
            "checkpoint_id": "checkpoint-abc123",
        }

        result = self.handler.execute_recovery(
            RecoveryStrategy.ROLLBACK_TO_CHECKPOINT,
            context,
        )

        assert result.strategy == RecoveryStrategy.ROLLBACK_TO_CHECKPOINT
        assert result.success is True
        assert "checkpoint-abc123" in result.next_action

    def test_execute_request_human_input(self):
        """Test execution of request human input strategy."""
        error = self.handler.detect_error("An error occurred")
        context = {"error": error}

        result = self.handler.execute_recovery(
            RecoveryStrategy.REQUEST_HUMAN_INPUT,
            context,
        )

        assert result.strategy == RecoveryStrategy.REQUEST_HUMAN_INPUT
        assert result.success is False
        assert result.next_action == "wait_for_human_input"
        assert "Human input required" in result.message

    def test_execute_skip_and_continue(self):
        """Test execution of skip and continue strategy."""
        error = self.handler.detect_error("An error occurred")
        context = {"error": error}

        result = self.handler.execute_recovery(
            RecoveryStrategy.SKIP_AND_CONTINUE,
            context,
        )

        assert result.strategy == RecoveryStrategy.SKIP_AND_CONTINUE
        assert result.success is True
        assert result.next_action == "continue_to_next_task"

    def test_execute_escalate(self):
        """Test execution of escalate strategy."""
        error = self.handler.detect_error("Operation timed out")
        context = {
            "error": error,
            "retry_count": 5,
        }

        result = self.handler.execute_recovery(
            RecoveryStrategy.ESCALATE,
            context,
        )

        assert result.strategy == RecoveryStrategy.ESCALATE
        assert result.success is False
        assert result.next_action == "escalate_to_human"


class TestSubprocessHandling:
    """Test subprocess result handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_successful_subprocess(self):
        """Test handling of successful subprocess execution."""
        result = subprocess.CompletedProcess(
            args=["echo", "hello"],
            returncode=0,
            stdout=b"hello\n",
            stderr=b"",
        )

        error, recovery = self.handler.handle_subprocess_result(
            result,
            "echo hello",
        )

        assert error is None
        assert recovery is None

    def test_failed_subprocess_with_error(self):
        """Test handling of failed subprocess execution."""
        result = subprocess.CompletedProcess(
            args=["ls", "/nonexistent"],
            returncode=2,
            stdout=b"",
            stderr=b"ls: cannot access '/nonexistent': No such file or directory",
        )

        error, recovery = self.handler.handle_subprocess_result(
            result,
            "ls /nonexistent",
        )

        assert error is not None
        assert error.exit_code == 2
        assert error.category == ErrorCategory.PERMANENT
        assert recovery is not None

    def test_subprocess_with_timeout(self):
        """Test handling of subprocess timeout."""
        result = subprocess.CompletedProcess(
            args=["sleep", "30"],
            returncode=124,  # timeout exit code
            stdout=b"",
            stderr=b"Operation timed out",
        )

        error, recovery = self.handler.handle_subprocess_result(
            result,
            "sleep 30",
        )

        assert error is not None
        assert error.category == ErrorCategory.TRANSIENT
        assert recovery is not None
        assert recovery.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF

    def test_subprocess_increments_retry_count(self):
        """Test that subprocess handling increments retry count."""
        result = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=1,
            stdout=b"",
            stderr=b"Operation timed out",
        )

        # First retry
        _, recovery1 = self.handler.handle_subprocess_result(
            result,
            "pytest",
            context={"retry_count": 0},
        )
        assert recovery1.retry_count == 1

        # Second retry
        _, recovery2 = self.handler.handle_subprocess_result(
            result,
            "pytest",
            context={"retry_count": 1},
        )
        assert recovery2.retry_count == 2


class TestErrorLogging:
    """Test error logging and summary."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_error_logging(self):
        """Test that errors are logged."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        self.handler.error_log.append(error)

        assert len(self.handler.error_log) == 1
        assert self.handler.error_log[0].error_type == ErrorType.SYNTAX_ERROR

    def test_error_summary_empty(self):
        """Test error summary with no errors."""
        summary = self.handler.get_error_summary()

        assert summary["total_errors"] == 0
        assert summary["by_category"] == {}
        assert summary["by_type"] == {}

    def test_error_summary_with_errors(self):
        """Test error summary with multiple errors."""
        self.handler.detect_error("Operation timed out")
        self.handler.detect_error("SyntaxError: invalid syntax")
        self.handler.detect_error("Operation timed out")

        summary = self.handler.get_error_summary()

        assert summary["total_errors"] == 3
        assert summary["by_category"]["transient"] == 2
        assert summary["by_category"]["permanent"] == 1

    def test_save_error_log(self):
        """Test saving error log to file."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        self.handler.error_log.append(error)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            filepath = Path(f.name)

        try:
            saved_path = self.handler.save_error_log(filepath)

            assert saved_path == filepath

            with open(saved_path) as f:
                data = json.load(f)

            assert "errors" in data
            assert len(data["errors"]) == 1
            assert data["errors"][0]["error_type"] == "syntax_error"
        finally:
            filepath.unlink(missing_ok=True)

    def test_save_error_log_auto_path(self):
        """Test saving error log with auto-generated path."""
        handler = ErrorHandler(session_id="test-session")

        with tempfile.TemporaryDirectory() as tmpdir:
            handler.base_path = Path(tmpdir)
            handler.session_dir = handler.base_path / "sessions" / "test-session"
            handler.session_dir.mkdir(parents=True, exist_ok=True)

            error = handler.detect_error("SyntaxError: invalid syntax")
            handler.error_log.append(error)

            saved_path = handler.save_error_log()

            assert saved_path.exists()
            assert saved_path.name == "error_log.json"


class TestErrorSerialization:
    """Test error serialization to dictionary."""

    def test_error_to_dict(self):
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

        assert data["error_id"] == "abc123"
        assert data["error_type"] == "syntax_error"
        assert data["category"] == "permanent"

    def test_recovery_result_to_dict(self):
        """Test recovery result serialization to dictionary."""
        result = RecoveryResult(
            strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            success=True,
            message="Retrying...",
            retry_count=2,
            next_action="retry",
        )

        data = result.to_dict()

        assert data["strategy"] == "retry_with_backoff"
        assert data["success"] is True
        assert data["retry_count"] == 2


class TestErrorSuggestions:
    """Test error suggestion generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ErrorHandler()

    def test_suggestion_for_timeout(self):
        """Test suggestion for timeout errors."""
        error = self.handler.detect_error("Operation timed out")
        assert "timeout" in error.suggestion.lower()

    def test_suggestion_for_syntax_error(self):
        """Test suggestion for syntax errors."""
        error = self.handler.detect_error("SyntaxError: invalid syntax")
        assert "syntax" in error.suggestion.lower()

    def test_suggestion_for_import_error(self):
        """Test suggestion for import errors."""
        error = self.handler.detect_error("ImportError: No module named")
        assert "dependency" in error.suggestion.lower() or "install" in error.suggestion.lower()

    def test_suggestion_for_ambiguous_error(self):
        """Test suggestion for ambiguous errors."""
        error = self.handler.detect_error("An error occurred")
        assert "investigation" in error.suggestion.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
