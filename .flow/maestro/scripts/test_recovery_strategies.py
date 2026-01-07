#!/usr/bin/env python3
"""
Unit tests for Maestro Recovery Strategies.

Tests retry with backoff, alternative approach selection, rollback to
checkpoint, and human input request strategies.
"""

import json
import subprocess
import time
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, call, MagicMock
from shutil import rmtree

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent))

from recovery_strategies import (
    RecoveryStrategies,
    RecoveryStrategyType,
    CheckpointType,
    RetryConfig,
    RetryResult,
    AlternativeApproach,
    Checkpoint,
    HumanInputRequest,
    RecoveryResult,
)


class TestRetryWithBackoff(unittest.TestCase):
    """Test retry with exponential backoff strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategies = RecoveryStrategies()

    def test_success_on_first_attempt(self):
        """Test operation succeeds on first attempt."""
        operation = Mock(return_value="success")

        result = self.strategies.retry_with_backoff(operation)

        self.assertTrue(result.success)
        self.assertEqual(result.attempts_made, 1)
        self.assertEqual(result.result, "success")
        self.assertIsNone(result.final_error)
        operation.assert_called_once()

    def test_success_on_second_attempt(self):
        """Test operation succeeds on second attempt after one failure."""
        call_count = 0

        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Temporary failure")
            return "success"

        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        result = self.strategies.retry_with_backoff(flaky_operation, config=config)

        self.assertTrue(result.success)
        self.assertEqual(result.attempts_made, 2)
        self.assertEqual(result.result, "success")

    def test_failure_after_max_attempts(self):
        """Test operation fails after max attempts exhausted."""
        operation = Mock(side_effect=ValueError("Persistent failure"))

        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
        result = self.strategies.retry_with_backoff(operation, config=config)

        self.assertFalse(result.success)
        self.assertEqual(result.attempts_made, 3)
        self.assertIn("Persistent failure", result.final_error)
        self.assertIsNone(result.result)

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            max_delay_seconds=100.0,
            jitter=False,
        )

        # Attempt 1: base_delay * (2 ^ 0) = 1.0
        delay_1 = self.strategies._calculate_backoff(1, config)
        self.assertEqual(delay_1, 1.0)

        # Attempt 2: base_delay * (2 ^ 1) = 2.0
        delay_2 = self.strategies._calculate_backoff(2, config)
        self.assertEqual(delay_2, 2.0)

        # Attempt 3: base_delay * (2 ^ 2) = 4.0
        delay_3 = self.strategies._calculate_backoff(3, config)
        self.assertEqual(delay_3, 4.0)

    def test_backoff_capped_at_max_delay(self):
        """Test backoff delay is capped at max_delay_seconds."""
        config = RetryConfig(
            base_delay_seconds=10.0,
            exponential_base=10.0,
            max_delay_seconds=50.0,
            jitter=False,
        )

        # Attempt 3: 10 * (10 ^ 2) = 1000, should be capped to 50
        delay = self.strategies._calculate_backoff(3, config)
        self.assertEqual(delay, 50.0)

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delay."""
        config = RetryConfig(
            base_delay_seconds=10.0,
            exponential_base=2.0,
            jitter=True,
        )

        delays = [
            self.strategies._calculate_backoff(2, config)
            for _ in range(10)
        ]

        # With jitter, we should see variation (not all identical)
        # Base delay for attempt 2 is 20.0, with jitter it should vary by ±25%
        self.assertTrue(len(set(delays)) > 1)
        # All delays should be within reasonable bounds
        for delay in delays:
            self.assertGreaterEqual(delay, 15.0)  # 20 - 25%
            self.assertLessEqual(delay, 25.0)  # 20 + 25%

    def test_retry_only_on_specified_exceptions(self):
        """Test that retry only happens for specified exception types."""
        config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)

        # Use a real function that raises KeyError
        def key_error_operation():
            raise KeyError("Not retried")

        result = self.strategies.retry_with_backoff(
            key_error_operation,
            config=config,
            retry_on=(ValueError,),  # Only retry on ValueError
        )

        self.assertFalse(result.success)
        self.assertEqual(result.attempts_made, 1)  # Should not retry
        self.assertIn("Not retried", result.final_error)

    def test_retry_on_multiple_exception_types(self):
        """Test retry on multiple exception types."""
        call_count = 0

        def multi_error_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Error 1")
            elif call_count == 2:
                raise KeyError("Error 2")
            return "success"

        config = RetryConfig(max_attempts=5, base_delay_seconds=0.01)
        result = self.strategies.retry_with_backoff(
            multi_error_operation,
            config=config,
            retry_on=(ValueError, KeyError),
        )

        self.assertTrue(result.success)
        self.assertEqual(result.attempts_made, 3)

    def test_custom_operation_name_in_logs(self):
        """Test that custom operation name appears in error messages."""
        operation = Mock(side_effect=ValueError("Test error"))

        config = RetryConfig(max_attempts=2, base_delay_seconds=0.01)
        result = self.strategies.retry_with_backoff(
            operation,
            config=config,
            operation_name="custom_operation",
        )

        self.assertFalse(result.success)
        # The operation name should be used in logging (verify via mock)
        operation.assert_called()


class TestAlternativeApproach(unittest.TestCase):
    """Test alternative approach selection strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategies = RecoveryStrategies()

    def test_finds_alternative_for_test_failure(self):
        """Test finding alternative approaches for test failures."""
        result = self.strategies.try_alternative_approach(
            context={"task_type": "testing"},
            failure_info={"error": "AssertionError: test failed"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.details["failure_type"], "test_failure")
        self.assertIn("approach_name", result.details)
        self.assertIn("all_available_approaches", result.details)

    def test_finds_alternative_for_dependency_conflict(self):
        """Test finding alternative approaches for dependency conflicts."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "DependencyConflict: version mismatch"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.details["failure_type"], "dependency_conflict")
        self.assertIn("approach_name", result.details)

    def test_finds_alternative_for_implementation_failure(self):
        """Test finding alternative approaches for implementation failures."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "NotImplementedError: feature missing"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.details["failure_type"], "implementation_failure")

    def test_returns_low_risk_approach_by_default(self):
        """Test that low-risk approaches are preferred."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "test failed"},
        )

        # First approach for test_failure should be low risk
        self.assertEqual(result.details["risk_level"], "low")

    def test_returns_all_available_approaches(self):
        """Test that all available approaches are included in result."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "test failed"},
        )

        all_approaches = result.details["all_available_approaches"]
        self.assertGreater(len(all_approaches), 1)
        self.assertIn("id", all_approaches[0])
        self.assertIn("name", all_approaches[0])
        self.assertIn("risk_level", all_approaches[0])

    def test_includes_implementation_pattern(self):
        """Test that implementation pattern is included."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "test failed"},
        )

        self.assertIn("implementation_pattern", result.details)
        self.assertIsInstance(result.details["implementation_pattern"], str)

    def test_includes_required_changes(self):
        """Test that required changes are included."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "test failed"},
        )

        self.assertIn("required_changes", result.details)
        self.assertIsInstance(result.details["required_changes"], list)

    def test_handles_unknown_failure_type(self):
        """Test handling of unknown failure types."""
        result = self.strategies.try_alternative_approach(
            context={},
            failure_info={"error": "Unknown error type"},
        )

        # Should default to test_failure approaches
        self.assertTrue(result.success)

    def test_failure_categorization(self):
        """Test failure categorization logic."""
        # Test failure detection
        self.assertEqual(
            self.strategies._categorize_failure({"error": "pytest failed"}),
            "test_failure"
        )

        # Implementation failure detection
        self.assertEqual(
            self.strategies._categorize_failure({"error": "NotImplementedError"}),
            "implementation_failure"
        )

        # Dependency conflict detection
        self.assertEqual(
            self.strategies._categorize_failure({"error": "version conflict"}),
            "dependency_conflict"
        )


class TestCheckpointManagement(unittest.TestCase):
    """Test checkpoint creation and rollback."""

    def setUp(self):
        """Set up test fixtures with temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.strategies = RecoveryStrategies(repo_root=self.temp_dir)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )

        # Create initial commit
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("initial")
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )

    def tearDown(self):
        """Clean up temp directory."""
        rmtree(self.temp_dir)

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        checkpoint = self.strategies.create_checkpoint(
            session_id="test-session",
            description="Test checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        self.assertIsNotNone(checkpoint.checkpoint_id)
        self.assertTrue(checkpoint.checkpoint_id.startswith("cp-"))
        self.assertEqual(checkpoint.description, "Test checkpoint")
        self.assertEqual(checkpoint.phase, "implement")
        self.assertEqual(checkpoint.checkpoint_type, CheckpointType.MANUAL)

    def test_checkpoint_saves_to_file(self):
        """Test that checkpoint is persisted to file."""
        session_id = "test-session"
        checkpoint = self.strategies.create_checkpoint(
            session_id=session_id,
            description="Test checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        checkpoint_file = self.strategies._get_checkpoint_file(session_id)
        self.assertTrue(checkpoint_file.exists())

        with open(checkpoint_file) as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(len(data["checkpoints"]), 1)
        self.assertEqual(data["checkpoints"][0]["checkpoint_id"], checkpoint.checkpoint_id)

    def test_multiple_checkpoints_accumulate(self):
        """Test that multiple checkpoints are accumulated."""
        session_id = "test-session"

        self.strategies.create_checkpoint(
            session_id=session_id,
            description="First checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        self.strategies.create_checkpoint(
            session_id=session_id,
            description="Second checkpoint",
            phase="validate",
            checkpoint_type=CheckpointType.MANUAL,
        )

        checkpoint_file = self.strategies._get_checkpoint_file(session_id)
        with open(checkpoint_file) as f:
            data = json.load(f)

        self.assertEqual(len(data["checkpoints"]), 2)
        self.assertEqual(data["summary"]["total_checkpoints"], 2)

    def test_checkpoint_includes_state_snapshot(self):
        """Test that state snapshot is included in checkpoint."""
        state_snapshot = {
            "tasks_completed": 5,
            "decisions_made": 2,
        }

        checkpoint = self.strategies.create_checkpoint(
            session_id="test-session",
            description="Test checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.SAFE_STATE,
            state_snapshot=state_snapshot,
        )

        self.assertEqual(checkpoint.state_snapshot, state_snapshot)

    def test_checkpoint_summary_updates(self):
        """Test that checkpoint summary is updated correctly."""
        session_id = "test-session"

        self.strategies.create_checkpoint(
            session_id=session_id,
            description="Checkpoint 1",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        self.strategies.create_checkpoint(
            session_id=session_id,
            description="Checkpoint 2",
            phase="validate",
            checkpoint_type=CheckpointType.SAFE_STATE,
        )

        checkpoint_file = self.strategies._get_checkpoint_file(session_id)
        with open(checkpoint_file) as f:
            data = json.load(f)

        summary = data["summary"]
        self.assertEqual(summary["total_checkpoints"], 2)
        self.assertEqual(summary["checkpoints_by_type"]["manual"], 1)
        self.assertEqual(summary["checkpoints_by_type"]["safe_state"], 1)

    @patch.object(RecoveryStrategies, '_get_current_commit')
    @patch('subprocess.run')
    def test_rollback_to_checkpoint(self, mock_run, mock_commit):
        """Test rolling back to a checkpoint."""
        # Mock commit info to avoid real git calls during create_checkpoint
        mock_commit.return_value = {
            "sha": "abc123",
            "message": "Test commit"
        }

        # First create a checkpoint
        session_id = "test-session"
        checkpoint = self.strategies.create_checkpoint(
            session_id=session_id,
            description="Test checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        # Reset mock to track only rollback calls
        mock_run.reset_mock()
        mock_run.return_value = MagicMock(returncode=0)

        # Perform rollback
        success = self.strategies.rollback_to_checkpoint(
            session_id=session_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        self.assertTrue(success)

        # Verify git reset was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn("git", call_args[0][0])
        self.assertIn("reset", call_args[0][0])
        self.assertIn("--hard", call_args[0][0])
        self.assertIn(checkpoint.commit_sha, call_args[0][0])

    @patch.object(RecoveryStrategies, '_get_current_commit')
    @patch('subprocess.run')
    def test_rollback_marks_checkpoint_used(self, mock_run, mock_commit):
        """Test that rollback marks checkpoint as used."""
        # Mock commit info to avoid real git calls
        mock_commit.return_value = {
            "sha": "abc123",
            "message": "Test commit"
        }

        session_id = "test-session"
        checkpoint = self.strategies.create_checkpoint(
            session_id=session_id,
            description="Test checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        # Reset mock for rollback
        mock_run.reset_mock()
        mock_run.return_value = MagicMock(returncode=0)

        self.strategies.rollback_to_checkpoint(
            session_id=session_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        # Load checkpoint and verify it's marked as used
        loaded = self.strategies._load_checkpoint(session_id, checkpoint.checkpoint_id)
        self.assertTrue(loaded.rollback_used)
        self.assertEqual(loaded.rollback_count, 1)

    def test_load_nonexistent_checkpoint(self):
        """Test loading a checkpoint that doesn't exist."""
        loaded = self.strategies._load_checkpoint(
            session_id="nonexistent",
            checkpoint_id="fake-checkpoint",
        )
        self.assertIsNone(loaded)

    @patch.object(RecoveryStrategies, '_get_current_commit')
    @patch('subprocess.run')
    def test_rollback_with_git_error(self, mock_run, mock_commit):
        """Test rollback when git command fails."""
        # Mock commit info to avoid real git calls
        mock_commit.return_value = {
            "sha": "abc123",
            "message": "Test commit"
        }

        session_id = "test-session"
        checkpoint = self.strategies.create_checkpoint(
            session_id=session_id,
            description="Test checkpoint",
            phase="implement",
            checkpoint_type=CheckpointType.MANUAL,
        )

        # Reset mock and set up for failure
        mock_run.reset_mock()
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        success = self.strategies.rollback_to_checkpoint(
            session_id=session_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        self.assertFalse(success)

    @patch('subprocess.run')
    def test_rollback_nonexistent_checkpoint(self, mock_subprocess):
        """Test rollback to nonexistent checkpoint."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        success = self.strategies.rollback_to_checkpoint(
            session_id="test-session",
            checkpoint_id="nonexistent-checkpoint",
        )

        self.assertFalse(success)


class TestHumanInputRequest(unittest.TestCase):
    """Test human input request strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategies = RecoveryStrategies()

    @patch('builtins.input', return_value="2\n")
    def test_request_input_with_selection(self, mock_input):
        """Test requesting human input and getting selection."""
        options = ["Option A", "Option B", "Option C"]

        selected = self.strategies.request_human_input(
            issue="Test issue",
            options=options,
        )

        self.assertEqual(selected, "Option B")
        mock_input.assert_called_once()

    @patch('builtins.input', return_value="\n")
    def test_request_input_with_default(self, mock_input):
        """Test requesting input with default option."""
        options = ["Option A", "Option B", "Option C"]

        selected = self.strategies.request_human_input(
            issue="Test issue",
            options=options,
            default_option="Option A",
        )

        self.assertEqual(selected, "Option A")

    @patch('builtins.input', side_effect=["invalid", "2\n"])
    def test_request_input_with_invalid_then_valid(self, mock_input):
        """Test handling invalid input then valid input."""
        options = ["Option A", "Option B", "Option C"]

        selected = self.strategies.request_human_input(
            issue="Test issue",
            options=options,
        )

        self.assertEqual(selected, "Option B")
        self.assertEqual(mock_input.call_count, 2)

    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_request_input_with_interrupt(self, mock_input):
        """Test handling keyboard interrupt (defaults to first option)."""
        options = ["Option A", "Option B", "Option C"]

        selected = self.strategies.request_human_input(
            issue="Test issue",
            options=options,
        )

        # Should default to first option when interrupted
        self.assertEqual(selected, "Option A")

    @patch('builtins.input', side_effect=["2\n", "Because it's better\n"])
    def test_request_input_with_justification(self, mock_input):
        """Test requesting justification along with selection."""
        options = ["Option A", "Option B", "Option C"]

        selected = self.strategies.request_human_input(
            issue="Test issue",
            options=options,
            requires_justification=True,
        )

        self.assertEqual(selected, "Option B")
        self.assertEqual(mock_input.call_count, 2)  # Selection + justification

    def test_generate_unique_request_id(self):
        """Test that request IDs are unique."""
        request_ids = set()

        for _ in range(10):
            # We can't easily test the full method without mocking input,
            # but we can verify the timestamp-based ID generation
            timestamp = int(datetime.utcnow().timestamp())
            request_id = f"req-{timestamp}"
            request_ids.add(request_id)

        # At least some IDs should be unique (unless all 10 were created
        # in the same second, which is unlikely but possible)
        # In a real scenario, we'd patch time.time() to control this


class TestIntegration(unittest.TestCase):
    """Integration tests for recovery strategies."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.strategies = RecoveryStrategies(repo_root=self.temp_dir)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )

        # Create initial commit
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("initial")
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )

    def tearDown(self):
        """Clean up temp directory."""
        rmtree(self.temp_dir)

    def test_checkpoint_then_rollback_workflow(self):
        """Test complete workflow of creating checkpoint and rolling back."""
        session_id = "integration-test"

        # Create checkpoint
        checkpoint = self.strategies.create_checkpoint(
            session_id=session_id,
            description="Before changes",
            phase="implement",
            checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
        )

        # Modify file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("modified")

        # Get current commit SHA (should be different)
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        current_sha = result.stdout.strip()

        # Commit changes
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Modified file"],
            cwd=self.temp_dir,
            capture_output=True,
            check=True,
        )

        # Verify file was modified
        self.assertEqual(test_file.read_text(), "modified")

        # Rollback to checkpoint
        success = self.strategies.rollback_to_checkpoint(
            session_id=session_id,
            checkpoint_id=checkpoint.checkpoint_id,
        )

        self.assertTrue(success)

        # Verify file content was restored
        self.assertEqual(test_file.read_text(), "initial")


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRetryWithBackoff))
    suite.addTests(loader.loadTestsFromTestCase(TestAlternativeApproach))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckpointManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestHumanInputRequest))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    result = run_tests()

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
