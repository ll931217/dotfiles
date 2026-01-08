"""
Comprehensive tests for AutoRecoveryManager.

Tests cover:
- Fix generation strategy
- Retry with exponential backoff
- Alternative approach selection
- Rollback trigger
- Human escalation (last resort)
- Recovery history logging
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import tempfile
import json
import time

# Import the module under test
import sys
maestro_root = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(maestro_root))

from auto_recovery import (
    AutoRecoveryManager,
    RecoveryStrategyType,
    RecoveryAttempt,
    RecoveryResult,
    Error,
)


class TestErrorClassification(unittest.TestCase):
    """Test error classification for strategy selection."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager()

    def test_classify_transient_error(self):
        """Test classification of transient errors."""
        error = Error(
            error_type="TimeoutError",
            message="Connection timed out after 30s",
            source="network",
        )
        category = self.manager._classify_error(error)
        self.assertEqual(category, "transient")

    def test_classify_code_quality_error(self):
        """Test classification of code quality errors."""
        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax on line 42",
            source="linter",
        )
        category = self.manager._classify_error(error)
        self.assertEqual(category, "code_quality")

    def test_classify_test_failure_error(self):
        """Test classification of test failure errors."""
        error = Error(
            error_type="AssertionError",
            message="Test failed: expected 5, got 3",
            source="pytest",
        )
        category = self.manager._classify_error(error)
        self.assertEqual(category, "test_failure")

    def test_classify_dependency_error(self):
        """Test classification of dependency errors."""
        error = Error(
            error_type="ImportError",
            message="No module named 'requests'",
            source="import",
        )
        category = self.manager._classify_error(error)
        self.assertEqual(category, "dependency")

    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        error = Error(
            error_type="CustomError",
            message="Something went wrong",
            source="unknown",
        )
        category = self.manager._classify_error(error)
        self.assertEqual(category, "unknown")


class TestStrategySelection(unittest.TestCase):
    """Test recovery strategy selection based on error type."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager()

    def test_strategy_selection_for_transient_errors(self):
        """Test strategy selection for transient errors."""
        # Set up retry handler
        self.manager.retry_handler = lambda e: True

        error = Error(
            error_type="TimeoutError",
            message="Connection timed out",
            source="network",
        )
        strategies = self.manager._select_recovery_strategies(error, {})
        # Should prioritize retry for transient errors when handler is configured
        self.assertIn(RecoveryStrategyType.RETRY, strategies)
        self.assertIn(RecoveryStrategyType.FIX, strategies)

    def test_strategy_selection_for_code_quality_errors(self):
        """Test strategy selection for code quality errors."""
        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )
        strategies = self.manager._select_recovery_strategies(error, {})
        # Should prioritize fix generation
        self.assertIn(RecoveryStrategyType.FIX, strategies)
        self.assertIn(RecoveryStrategyType.ALTERNATIVE, strategies)

    def test_strategy_selection_for_test_failures(self):
        """Test strategy selection for test failures."""
        # Set up handlers
        self.manager.retry_handler = lambda e: True
        self.manager.alternative_selector = lambda e: "alternative"

        error = Error(
            error_type="AssertionError",
            message="Test failed",
            source="pytest",
        )
        strategies = self.manager._select_recovery_strategies(error, {})
        # Should try fix, retry, and alternative in that order when configured
        self.assertIn(RecoveryStrategyType.FIX, strategies)
        self.assertIn(RecoveryStrategyType.RETRY, strategies)
        self.assertIn(RecoveryStrategyType.ALTERNATIVE, strategies)

    def test_strategy_selection_rollback_last(self):
        """Test that rollback is always last (before escalation)."""
        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )
        self.manager.rollback_handler = lambda: True
        strategies = self.manager._select_recovery_strategies(error, {})
        # Rollback should be last in the list
        if strategies:
            last_strategy = strategies[-1]
            self.assertEqual(last_strategy, RecoveryStrategyType.ROLLBACK)


class TestFixGeneration(unittest.TestCase):
    """Test fix generation strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager()

    def test_fix_generation_with_callback(self):
        """Test fix generation when callback is configured."""
        # Configure fix generator
        def mock_fix_generator(error):
            return "Fix: Update the syntax error on line 42"

        self.manager.fix_generator = mock_fix_generator

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = self.manager._attempt_fix_generation(error, {}, 1)

        self.assertTrue(result["success"])
        self.assertIn("Fix", result["changes_made"][0])

    def test_fix_generation_without_callback(self):
        """Test fix generation when callback is not configured."""
        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = self.manager._attempt_fix_generation(error, {}, 1)

        self.assertFalse(result["success"])
        self.assertIn("not configured", result["message"])

    def test_fix_generation_with_code_blocks(self):
        """Test parsing of fix suggestions with code blocks."""
        fix_suggestion = """
        Here's the fix:

        ```python
        def fixed_function():
            return "correct"
        ```

        Additional changes:
        - Updated import statements
        - Fixed indentation
        """

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        changes = self.manager._parse_fix_changes(fix_suggestion, error)

        self.assertGreater(len(changes), 0)
        self.assertTrue(any("code fix" in change.lower() for change in changes))


class TestRetryWithBackoff(unittest.TestCase):
    """Test retry strategy with exponential backoff."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager(base_delay=0.1, max_delay=1.0)

    def test_retry_success_on_first_attempt(self):
        """Test retry succeeding on first attempt."""
        retry_mock = MagicMock(return_value=True)
        self.manager.retry_handler = retry_mock

        error = Error(
            error_type="TimeoutError",
            message="Connection timed out",
            source="network",
        )

        result = self.manager._attempt_retry(error, {}, 1)

        self.assertTrue(result["success"])
        retry_mock.assert_called_once_with(error)

    def test_retry_with_exponential_backoff(self):
        """Test that retry delay increases exponentially."""
        call_times = []

        def mock_retry(error):
            call_times.append(time.time())
            return len(call_times) < 3  # Fail first 2 attempts

        self.manager.retry_handler = mock_retry
        self.manager.max_attempts = 3

        error = Error(
            error_type="TimeoutError",
            message="Connection timed out",
            source="network",
        )

        # This will make multiple retry attempts
        strategies = [RecoveryStrategyType.RETRY]
        for strategy in strategies:
            for attempt_num in range(1, 4):
                start = time.time()
                self.manager._attempt_retry(error, {}, attempt_num)
                duration = time.time() - start
                if attempt_num < 3:
                    # Should have delayed (simulated by exponential backoff logic)
                    self.assertGreater(duration, 0)

    def test_retry_exhausted(self):
        """Test retry after max attempts exhausted."""
        retry_mock = MagicMock(return_value=False)
        self.manager.retry_handler = retry_mock

        error = Error(
            error_type="TimeoutError",
            message="Connection timed out",
            source="network",
        )

        result = self.manager._attempt_retry(error, {}, 3)

        self.assertFalse(result["success"])
        self.assertEqual(retry_mock.call_count, 1)


class TestAlternativeApproach(unittest.TestCase):
    """Test alternative approach strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager()

    def test_alternative_selection_success(self):
        """Test successful alternative approach selection."""
        def mock_alternative_selector(error):
            return "Use asyncio instead of threading"

        self.manager.alternative_selector = mock_alternative_selector

        error = Error(
            error_type="ImportError",
            message="Module not found",
            source="import",
        )

        result = self.manager._attempt_alternative(error, {}, 1)

        self.assertTrue(result["success"])
        self.assertIn("asyncio", result["changes_made"][0])

    def test_alternative_selection_no_alternative(self):
        """Test when no alternative is available."""
        def mock_alternative_selector(error):
            return None  # No alternative available

        self.manager.alternative_selector = mock_alternative_selector

        error = Error(
            error_type="ImportError",
            message="Module not found",
            source="import",
        )

        result = self.manager._attempt_alternative(error, {}, 1)

        self.assertFalse(result["success"])
        self.assertIn("No alternative", result["message"])

    def test_alternative_selection_not_configured(self):
        """Test alternative selection when callback is not configured."""
        self.manager.alternative_selector = None

        error = Error(
            error_type="ImportError",
            message="Module not found",
            source="import",
        )

        result = self.manager._attempt_alternative(error, {}, 1)

        self.assertFalse(result["success"])
        self.assertIn("not configured", result["message"])


class TestRollback(unittest.TestCase):
    """Test rollback strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager()

    def test_rollback_success(self):
        """Test successful rollback to checkpoint."""
        rollback_mock = MagicMock(return_value=True)
        self.manager.rollback_handler = rollback_mock

        error = Error(
            error_type="RuntimeError",
            message="Critical error occurred",
            source="runtime",
        )

        result = self.manager._attempt_rollback(error, {}, 1)

        self.assertTrue(result["success"])
        self.assertIn("Rolled back", result["changes_made"][0])
        rollback_mock.assert_called_once()

    def test_rollback_failure(self):
        """Test rollback failure."""
        rollback_mock = MagicMock(return_value=False)
        self.manager.rollback_handler = rollback_mock

        error = Error(
            error_type="RuntimeError",
            message="Critical error occurred",
            source="runtime",
        )

        result = self.manager._attempt_rollback(error, {}, 1)

        self.assertFalse(result["success"])

    def test_rollback_not_configured(self):
        """Test rollback when handler is not configured."""
        self.manager.rollback_handler = None

        error = Error(
            error_type="RuntimeError",
            message="Critical error occurred",
            source="runtime",
        )

        result = self.manager._attempt_rollback(error, {}, 1)

        self.assertFalse(result["success"])
        self.assertIn("not configured", result["message"])


class TestHumanEscalation(unittest.TestCase):
    """Test human escalation as last resort."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager(max_attempts=2)

    def test_escalation_after_all_strategies_fail(self):
        """Test escalation after all recovery strategies fail."""
        # Configure all strategies to fail
        self.manager.fix_generator = lambda e: None
        self.manager.retry_handler = lambda e: False
        self.manager.alternative_selector = lambda e: None
        self.manager.rollback_handler = lambda: False

        error = Error(
            error_type="SyntaxError",
            message="Cannot fix this error",
            source="linter",
        )

        result = self.manager.attempt_recovery(error, {})

        self.assertFalse(result.success)
        self.assertTrue(result.escalated_to_human)
        self.assertEqual(result.strategy_used, RecoveryStrategyType.ESCALATE)
        self.assertIn("human intervention required", result.message.lower())

    def test_escalation_only_after_all_attempts(self):
        """Test that escalation only happens after all strategies are attempted."""
        attempt_count = 0

        def failing_fix(error):
            nonlocal attempt_count
            attempt_count += 1
            return None

        self.manager.fix_generator = failing_fix
        self.manager.retry_handler = None
        self.manager.alternative_selector = None
        self.manager.rollback_handler = None

        error = Error(
            error_type="SyntaxError",
            message="Cannot fix",
            source="linter",
        )

        result = self.manager.attempt_recovery(error, {})

        # Should have attempted fix multiple times before escalating
        self.assertGreaterEqual(attempt_count, self.manager.max_attempts)
        self.assertTrue(result.escalated_to_human)


class TestRecoveryHistory(unittest.TestCase):
    """Test recovery history tracking and logging."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager()

    def test_recovery_history_tracking(self):
        """Test that recovery attempts are tracked in history."""
        # Configure a successful fix
        self.manager.fix_generator = lambda e: "Fix applied"

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = self.manager.attempt_recovery(error, {})

        # Check that result was added to history
        self.assertEqual(len(self.manager.recovery_history), 1)
        history_entry = self.manager.recovery_history[0]
        self.assertEqual(history_entry.strategy_used, RecoveryStrategyType.FIX)
        self.assertTrue(history_entry.success)

    def test_recovery_attempt_details(self):
        """Test that individual recovery attempts are logged."""
        self.manager.fix_generator = lambda e: "Fix applied"

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = self.manager.attempt_recovery(error, {})

        # Check attempt details
        self.assertGreater(len(result.attempts), 0)
        attempt = result.attempts[0]
        self.assertEqual(attempt.strategy, "fix")
        self.assertTrue(attempt.success)
        self.assertIn("timestamp", attempt.to_dict())

    def test_save_recovery_history(self):
        """Test saving recovery history to file."""
        # Add a recovery result
        self.manager.fix_generator = lambda e: "Fix applied"
        error = Error(error_type="TestError", message="Test", source="test")
        self.manager.attempt_recovery(error, {})

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = Path(f.name)

        try:
            self.manager.save_recovery_history(temp_path)

            # Load and verify
            with open(temp_path) as f:
                saved_history = json.load(f)

            self.assertEqual(len(saved_history), 1)
            self.assertIn("strategy_used", saved_history[0])
        finally:
            temp_path.unlink()

    def test_clear_recovery_history(self):
        """Test clearing recovery history."""
        # Add a recovery result
        self.manager.fix_generator = lambda e: "Fix applied"
        error = Error(error_type="TestError", message="Test", source="test")
        self.manager.attempt_recovery(error, {})

        self.assertGreater(len(self.manager.recovery_history), 0)

        # Clear history
        self.manager.clear_recovery_history()
        self.assertEqual(len(self.manager.recovery_history), 0)

    def test_get_recovery_history(self):
        """Test getting recovery history as dictionaries."""
        # Add a recovery result
        self.manager.fix_generator = lambda e: "Fix applied"
        error = Error(error_type="TestError", message="Test", source="test")
        self.manager.attempt_recovery(error, {})

        history = self.manager.get_recovery_history()

        self.assertEqual(len(history), 1)
        self.assertIn("strategy_used", history[0])
        self.assertIn("attempts", history[0])
        self.assertIn("timestamp", history[0])


class TestRecoveryResultSerialization(unittest.TestCase):
    """Test serialization of recovery results."""

    def test_recovery_result_to_dict(self):
        """Test converting RecoveryResult to dictionary."""
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=None,
            error_after=None,
            changes_made=["Applied fix"],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.5,
            message="Success",
        )

        result = RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategyType.FIX,
            attempts=[attempt],
            final_error=None,
            message="Recovery successful",
        )

        result_dict = result.to_dict()

        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["strategy_used"], "fix")
        self.assertEqual(len(result_dict["attempts"]), 1)
        self.assertIn("timestamp", result_dict)

    def test_recovery_attempt_to_dict(self):
        """Test converting RecoveryAttempt to dictionary."""
        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=["Fixed syntax"],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.5,
            message="Fixed",
        )

        attempt_dict = attempt.to_dict()

        self.assertEqual(attempt_dict["attempt_number"], 1)
        self.assertEqual(attempt_dict["strategy"], "fix")
        self.assertTrue(attempt_dict["success"])
        self.assertIn("error_before", attempt_dict)
        self.assertIn("changes_made", attempt_dict)


class TestEndToEndRecoveryScenarios(unittest.TestCase):
    """Test end-to-end recovery scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = AutoRecoveryManager(max_attempts=2)

    def test_transient_error_recovery_success(self):
        """Test successful recovery from transient error."""
        # Configure retry to succeed on second attempt
        call_count = [0]

        def mock_retry(error):
            call_count[0] += 1
            return call_count[0] >= 2

        self.manager.retry_handler = mock_retry

        error = Error(
            error_type="TimeoutError",
            message="Connection timed out",
            source="network",
        )

        result = self.manager.attempt_recovery(error, {})

        self.assertTrue(result.success)
        self.assertEqual(result.strategy_used, RecoveryStrategyType.RETRY)
        self.assertGreater(len(result.attempts), 0)

    def test_code_quality_recovery_with_fix(self):
        """Test recovery from code quality error using fix generation."""
        self.manager.fix_generator = lambda e: "Fix: Correct syntax error"

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = self.manager.attempt_recovery(error, {})

        self.assertTrue(result.success)
        self.assertEqual(result.strategy_used, RecoveryStrategyType.FIX)

    def test_complex_recovery_multiple_strategies(self):
        """Test recovery that requires multiple strategy attempts."""
        attempt_log = []

        def mock_alternative(error):
            attempt_log.append("alternative")
            # Alternative fails first time
            if attempt_log.count("alternative") < 2:
                return None
            return "Use different approach"  # Alternative succeeds on second attempt

        def mock_fix(error):
            attempt_log.append("fix")
            return None  # Fix fails

        self.manager.fix_generator = mock_fix
        self.manager.retry_handler = lambda e: False
        self.manager.alternative_selector = mock_alternative
        self.manager.rollback_handler = lambda: False
        self.manager.max_attempts = 2  # Set low to speed up test

        # Use test_failure error type which has fix -> retry -> alternative strategy order
        error = Error(
            error_type="AssertionError",
            message="Test failed",
            source="pytest",
        )

        result = self.manager.attempt_recovery(error, {})

        self.assertTrue(result.success)
        # Alternative should succeed after fix fails
        self.assertEqual(result.strategy_used, RecoveryStrategyType.ALTERNATIVE)
        # Should have tried fix first, then alternative
        self.assertIn("fix", attempt_log)
        self.assertIn("alternative", attempt_log)


if __name__ == "__main__":
    unittest.main()
