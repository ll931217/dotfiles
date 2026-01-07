#!/usr/bin/env python3
"""
Error Recovery Scenario Tests

Tests for error detection, recovery strategies, rollback, and
human input request handling.
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "decision-engine" / "scripts"))

from error_handler import ErrorHandler, ErrorCategory, RecoveryStrategy
from session_manager import SessionStatus
from checkpoint_manager import CheckpointManager, CheckpointType, CheckpointPhase, StateSnapshot


class TestErrorHandlerIntegration(unittest.TestCase):
    """Integration tests for ErrorHandler with recovery strategies."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "error-test-session"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        import json
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test error recovery",
            "status": SessionStatus.IMPLEMENTING.value,
            "current_phase": "implement",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "main",
                "commit": "abc123",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_error_classification(self):
        """Test error classification into categories."""
        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        # Create Error objects for classification using ErrorType enum
        from error_handler import Error, ErrorType

        errors = [
            (ErrorType.TIMEOUT, ErrorCategory.TRANSIENT),
            (ErrorType.SYNTAX_ERROR, ErrorCategory.PERMANENT),
        ]

        for error_type, expected_category in errors:
            error_obj = Error(
                error_id="test-001",
                timestamp=datetime.now().isoformat(),
                error_type=error_type,
                category=expected_category,
                message="Test error message",
                source="test"
            )
            classified = handler.classify_error(error_obj)
            self.assertEqual(classified, expected_category)

    def test_error_recovery_strategy_selection(self):
        """Test error recovery strategy classification."""
        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        # Test different error types get different strategies
        from error_handler import Error, ErrorType

        network_error = Error(
            error_id="test-002",
            timestamp=datetime.now().isoformat(),
            error_type=ErrorType.NETWORK,
            category=ErrorCategory.TRANSIENT,
            message="Network timeout",
            source="test"
        )

        # Get recovery strategy
        strategy = handler.select_recovery_strategy(network_error)

        self.assertIsNotNone(strategy)
        # For transient errors, should get retry strategy
        self.assertEqual(strategy, RecoveryStrategy.RETRY_WITH_BACKOFF)

    def test_error_logging(self):
        """Test error detection and logging."""
        from error_handler import ErrorType

        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        # Detect error from output
        error = handler.detect_error(
            output="Connection timeout error",
            source="test",
            exit_code=1
        )

        # Verify error was detected
        self.assertIsNotNone(error)
        self.assertEqual(error.category, ErrorCategory.TRANSIENT)
        self.assertEqual(error.error_type, ErrorType.TIMEOUT)


class TestRetryStrategy(unittest.TestCase):
    """Tests for retry strategies."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_retry_with_exponential_backoff(self):
        """Test retry with exponential backoff strategy."""
        attempts = [0]
        max_attempts = 3

        def flaky_function():
            attempts[0] += 1
            if attempts[0] < max_attempts:
                raise ConnectionError("Temporary failure")
            return "success"

        # Implement retry logic with exponential backoff
        for retry in range(max_attempts):
            try:
                result = flaky_function()
                self.assertEqual(result, "success")
                self.assertEqual(attempts[0], max_attempts)
                break
            except ConnectionError:
                if retry == max_attempts - 1:
                    self.fail("Max retries exceeded")
                # Exponential backoff
                time.sleep(0.1 * (2 ** retry))

    def test_retry_max_attempts_exceeded(self):
        """Test that max attempts is respected."""
        attempts = [0]
        max_attempts = 3

        def failing_function():
            attempts[0] += 1
            raise ValueError("Persistent failure")

        # Test that max attempts is enforced
        for retry in range(max_attempts):
            try:
                failing_function()
            except ValueError:
                if retry == max_attempts - 1:
                    # Should have attempted max_attempts times
                    self.assertEqual(attempts[0], max_attempts)
                else:
                    continue
                break

    def test_retry_on_specific_exceptions(self):
        """Test retry only on specific exception types."""
        retryable_exceptions = (ConnectionError, TimeoutError)
        non_retryable_exception = ValueError("Non-retryable error")

        def function_with_non_retryable_error():
            raise non_retryable_exception

        # Should not retry on non-retryable exception
        with self.assertRaises(ValueError):
            function_with_non_retryable_error()


class TestRollbackScenarios(unittest.TestCase):
    """Tests for rollback scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "rollback-test-session"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        import json
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test rollback",
            "status": SessionStatus.IMPLEMENTING.value,
            "current_phase": "implement",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "main",
                "commit": "abc123",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

        # Create subagent config
        subagent_config = """subagent_types:
  general-purpose:
    model: sonnet
    description: General purpose agent
"""
        (self.project_root / ".claude" / "subagent-types.yaml").write_text(subagent_config)

        import os
        os.environ["SUBAGENT_TYPES_PATH"] = str(
            self.project_root / ".claude" / "subagent-types.yaml"
        )

        # Mock git
        self.git_patcher = patch("subprocess.run")
        self.mock_run = self.git_patcher.start()
        self.mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_checkpoint_rollback(self):
        """Test rolling back to a previous checkpoint."""
        checkpoint_manager = CheckpointManager(self.project_root)

        # Create initial checkpoint
        initial_checkpoint = checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.PLAN,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="Initial checkpoint before risky operation",
            state_snapshot=StateSnapshot(tasks_completed=1)
        )

        # Simulate some changes (create another checkpoint)
        subsequent_checkpoint = checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="After some changes",
            state_snapshot=StateSnapshot(tasks_completed=2)
        )

        # Rollback to initial checkpoint
        # In real scenario, would revert git commit and restore state
        retrieved = checkpoint_manager.get_checkpoint(
            self.session_id,
            initial_checkpoint.checkpoint_id
        )

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.checkpoint_id, initial_checkpoint.checkpoint_id)

    def test_rollback_after_error(self):
        """Test rollback after encountering an error."""
        checkpoint_manager = CheckpointManager(self.project_root)

        # Create checkpoint before risky operation
        pre_error_checkpoint = checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
            description="Before risky operation",
            state_snapshot=StateSnapshot(tasks_completed=1)
        )

        # Verify checkpoint exists for potential rollback
        retrieved = checkpoint_manager.get_checkpoint(
            self.session_id,
            pre_error_checkpoint.checkpoint_id
        )

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.checkpoint_id, pre_error_checkpoint.checkpoint_id)

    def test_multiple_checkpoint_selection(self):
        """Test selecting the right checkpoint for rollback."""
        checkpoint_manager = CheckpointManager(self.project_root)

        # Create multiple checkpoints
        checkpoint1 = checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.PLAN,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="Checkpoint 1",
            state_snapshot=StateSnapshot(tasks_completed=1)
        )

        checkpoint2 = checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="Checkpoint 2",
            state_snapshot=StateSnapshot(tasks_completed=2)
        )

        # List checkpoints and verify order
        checkpoints = checkpoint_manager.list_checkpoints(self.session_id)
        self.assertGreater(len(checkpoints), 0)


class TestHumanInputRequest(unittest.TestCase):
    """Tests for human input request scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "human-input-test"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)

        # Create session metadata (start with IMPLEMENTING, not PAUSED)
        import json
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test human input",
            "status": SessionStatus.IMPLEMENTING.value,
            "current_phase": "implement",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "main",
                "commit": "abc123",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_request_human_input_for_ambiguous_decision(self):
        """Test requesting human input for ambiguous decision."""
        # Simulate ambiguous situation requiring human input
        ambiguous_context = {
            "situation": "Multiple valid approaches found",
            "options": [
                "Use React with TypeScript",
                "Use Vue with TypeScript",
                "Use Svelte with TypeScript",
            ],
            "reasoning": "All options are valid, need human preference"
        }

        # In real scenario, would pause workflow and request input
        # For test, verify context is properly structured
        self.assertIn("situation", ambiguous_context)
        self.assertIn("options", ambiguous_context)
        self.assertEqual(len(ambiguous_context["options"]), 3)

    def test_continue_after_human_input(self):
        """Test continuing workflow after receiving human input."""
        from session_manager import SessionManager

        session_manager = SessionManager(self.project_root)

        # Start from IMPLEMENTING, then transition to PAUSED
        session_manager.transition_state(
            session_id=self.session_id,
            new_state=SessionStatus.PAUSED
        )

        # Verify state transition - Session is a dataclass
        session = session_manager.get_session(self.session_id)
        self.assertEqual(session.status, SessionStatus.PAUSED)

        # Simulate receiving input and continuing
        session_manager.transition_state(
            session_id=self.session_id,
            new_state=SessionStatus.IMPLEMENTING
        )

        session = session_manager.get_session(self.session_id)
        self.assertEqual(session.status, SessionStatus.IMPLEMENTING)

    def test_timeout_waiting_for_human_input(self):
        """Test handling timeout when waiting for human input."""
        from session_manager import SessionManager

        session_manager = SessionManager(self.project_root)

        # Set session to PAUSED state (waiting for human input)
        session_manager.transition_state(
            session_id=self.session_id,
            new_state=SessionStatus.PAUSED
        )

        # Simulate timeout by checking timestamp - Session is a dataclass
        session = session_manager.get_session(self.session_id)
        created_time = datetime.fromisoformat(session.created_at)

        # In real scenario, would check if timeout exceeded
        # For test, verify we can access the timestamp
        self.assertIsNotNone(created_time)


class TestRecoveryStrategySelection(unittest.TestCase):
    """Tests for automatic recovery strategy selection."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "recovery-strategy-test"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        import json
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test recovery strategies",
            "status": SessionStatus.IMPLEMENTING.value,
            "current_phase": "implement",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "main",
                "commit": "abc123",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_select_retry_for_transient_errors(self):
        """Test selecting retry strategy for transient errors."""
        from error_handler import ErrorHandler, Error, ErrorType

        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        # Transient error (network timeout)
        transient_error = Error(
            error_id="test-003",
            timestamp=datetime.now().isoformat(),
            error_type=ErrorType.TIMEOUT,
            category=ErrorCategory.TRANSIENT,
            message="Connection timed out",
            source="test"
        )

        # Get recovery strategy
        strategy = handler.select_recovery_strategy(transient_error)

        # Should select retry strategy for transient errors
        self.assertEqual(strategy, RecoveryStrategy.RETRY_WITH_BACKOFF)

    def test_select_rollback_for_critical_errors(self):
        """Test selecting rollback for critical errors."""
        from error_handler import ErrorHandler, Error, ErrorType

        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        # Permanent error with checkpoint available
        critical_error = Error(
            error_id="test-004",
            timestamp=datetime.now().isoformat(),
            error_type=ErrorType.LOGIC_ERROR,
            category=ErrorCategory.PERMANENT,
            message="Database integrity check failed",
            source="test"
        )

        # Get recovery strategy with checkpoint context
        strategy = handler.select_recovery_strategy(
            critical_error,
            context={"has_checkpoint": True}
        )

        # Should select rollback when checkpoint is available
        self.assertEqual(strategy, RecoveryStrategy.ROLLBACK_TO_CHECKPOINT)

    def test_select_alternative_for_permanent_errors(self):
        """Test selecting alternative approach for permanent errors."""
        from error_handler import ErrorHandler, Error, ErrorType

        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        # Permanent error that requires alternative approach (no checkpoint)
        permanent_error = Error(
            error_id="test-005",
            timestamp=datetime.now().isoformat(),
            error_type=ErrorType.DEPENDENCY_MISSING,
            category=ErrorCategory.PERMANENT,
            message="Incompatible version detected",
            source="test"
        )

        # Get recovery strategy without checkpoint
        strategy = handler.select_recovery_strategy(
            permanent_error,
            context={"has_checkpoint": False}
        )

        # Should select alternative approach when no checkpoint available
        self.assertEqual(strategy, RecoveryStrategy.ALTERNATIVE_APPROACH)


if __name__ == "__main__":
    unittest.main()
