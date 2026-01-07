#!/usr/bin/env python3
"""
Tests for Phase Manager
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from phase_manager import (
    Phase,
    PhaseManager,
    PhaseResult,
    PhaseTransitionError,
)
from session_manager import SessionStatus


class TestPhaseManager(unittest.TestCase):
    """Test cases for PhaseManager."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "test-session-123"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature",
            "status": SessionStatus.PLANNING.value,  # Use planning to allow initialization transition
            "current_phase": "plan",  # SessionPhase enum value
            "start_time": "2025-01-07T10:00:00Z",
            "created_at": "2025-01-07T10:00:00Z",
            "git_context": {
                "branch": "main",
                "commit": "abc123",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

        # Mock git commands
        self.git_patcher = patch("subprocess.run")
        self.mock_run = self.git_patcher.start()
        self.mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test PhaseManager initialization."""
        manager = PhaseManager(self.project_root, self.session_id)

        self.assertEqual(manager.session_id, self.session_id)
        self.assertEqual(manager.project_root, self.project_root)
        self.assertIsNone(manager.current_phase)

    def test_can_transition_to_initialization(self):
        """Test transition to initialization phase from start."""
        manager = PhaseManager(self.project_root, self.session_id)

        # From PLANNING session status, can transition to PLANNING phase (matching)
        self.assertTrue(manager.can_transition_to(Phase.PLANNING))

    def test_cannot_transition_invalid_path(self):
        """Test that invalid transitions are rejected."""
        manager = PhaseManager(self.project_root, self.session_id)
        manager.current_phase = Phase.PLANNING

        # Cannot skip from planning directly to completed
        self.assertFalse(manager.can_transition_to(Phase.COMPLETED))

    def test_valid_transition_path(self):
        """Test valid transition path through phases."""
        manager = PhaseManager(self.project_root, self.session_id)

        # Valid path: INITIALIZATION -> PLANNING -> TASK_GENERATION
        manager.current_phase = Phase.INITIALIZATION
        self.assertTrue(manager.can_transition_to(Phase.PLANNING))

        manager.current_phase = Phase.PLANNING
        self.assertTrue(manager.can_transition_to(Phase.TASK_GENERATION))

    def test_validate_preconditions_success(self):
        """Test precondition validation when valid."""
        manager = PhaseManager(self.project_root, self.session_id)

        # PLANNING phase should be valid when session status is PLANNING
        is_valid, errors = manager.validate_preconditions(Phase.PLANNING)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_preconditions_invalid_state(self):
        """Test precondition validation with wrong session state."""
        manager = PhaseManager(self.project_root, self.session_id)

        # Update session to wrong state
        session_path = (
            self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json"
        )
        metadata = json.loads(session_path.read_text())
        metadata["status"] = SessionStatus.COMPLETED.value
        session_path.write_text(json.dumps(metadata))

        is_valid, errors = manager.validate_preconditions(Phase.INITIALIZATION)

        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_execute_phase_success(self):
        """Test successful phase execution."""
        manager = PhaseManager(self.project_root, self.session_id)

        def mock_execute():
            return {"test_data": "success"}

        # Use PLANNING phase which matches PLANNING status
        result = manager.execute_phase(
            phase=Phase.PLANNING,
            execute_func=mock_execute,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.phase, Phase.PLANNING)
        self.assertEqual(result.data["test_data"], "success")
        self.assertIsNone(result.checkpoint)  # PLANNING phase doesn't create checkpoint
        self.assertEqual(manager.current_phase, Phase.PLANNING)

    def test_execute_phase_failure(self):
        """Test phase execution with error."""
        manager = PhaseManager(self.project_root, self.session_id)

        def failing_execute():
            raise ValueError("Test error")

        # Use PLANNING phase which matches PLANNING status
        result = manager.execute_phase(
            phase=Phase.PLANNING,
            execute_func=failing_execute,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.phase, Phase.PLANNING)
        self.assertGreater(len(result.errors), 0)

    def test_transition_to_success(self):
        """Test successful phase transition."""
        manager = PhaseManager(self.project_root, self.session_id)

        # First set current phase to PLANNING
        manager.current_phase = Phase.PLANNING

        # Then can transition to TASK_GENERATION
        success = manager.transition_to(Phase.TASK_GENERATION)

        self.assertTrue(success)
        self.assertEqual(manager.current_phase, Phase.TASK_GENERATION)

    def test_transition_to_invalid(self):
        """Test invalid phase transition."""
        manager = PhaseManager(self.project_root, self.session_id)

        # Try to skip to implementation without going through init
        success = manager.transition_to(Phase.IMPLEMENTATION)

        self.assertFalse(success)

    def test_get_phase_progress(self):
        """Test getting phase progress."""
        manager = PhaseManager(self.project_root, self.session_id)
        manager.current_phase = Phase.IMPLEMENTATION

        progress = manager.get_phase_progress()

        self.assertEqual(progress["current_phase"], "implementation")
        self.assertGreater(progress["progress_percent"], 0)
        self.assertIn("implementation", progress["completed_phases"])
        self.assertIn("validation", progress["remaining_phases"])

    def test_get_next_phase(self):
        """Test getting next phase in workflow."""
        manager = PhaseManager(self.project_root, self.session_id)
        manager.current_phase = Phase.PLANNING

        next_phase = manager.get_next_phase()

        self.assertEqual(next_phase, Phase.TASK_GENERATION)

    def test_get_next_phase_at_terminal(self):
        """Test that terminal phase has no next phase."""
        manager = PhaseManager(self.project_root, self.session_id)
        manager.current_phase = Phase.COMPLETED

        next_phase = manager.get_next_phase()

        self.assertIsNone(next_phase)

    def test_can_retry_phase(self):
        """Test checking if phase can be retried."""
        manager = PhaseManager(self.project_root, self.session_id)

        # Most phases allow retry
        self.assertTrue(manager.can_retry_phase(Phase.PLANNING))
        self.assertTrue(manager.can_retry_phase(Phase.IMPLEMENTATION))

    def test_cannot_retry_failed_phase(self):
        """Test that failed phase cannot be retried."""
        manager = PhaseManager(self.project_root, self.session_id)

        # Failed phase doesn't allow retry
        self.assertFalse(manager.can_retry_phase(Phase.FAILED))


class TestPhase(unittest.TestCase):
    """Test cases for Phase enum."""

    def test_phase_values(self):
        """Test Phase enum values."""
        self.assertEqual(Phase.INITIALIZATION.value, "initialization")
        self.assertEqual(Phase.PLANNING.value, "planning")
        self.assertEqual(Phase.TASK_GENERATION.value, "task_generation")
        self.assertEqual(Phase.IMPLEMENTATION.value, "implementation")
        self.assertEqual(Phase.VALIDATION.value, "validation")
        self.assertEqual(Phase.REPORT_GENERATION.value, "report_generation")
        self.assertEqual(Phase.COMPLETED.value, "completed")
        self.assertEqual(Phase.FAILED.value, "failed")


class TestPhaseResult(unittest.TestCase):
    """Test cases for PhaseResult dataclass."""

    def test_phase_result_creation(self):
        """Test creating PhaseResult."""
        result = PhaseResult(
            phase=Phase.PLANNING,
            success=True,
            data={"prd_generated": True},
            checkpoint="abc123",
        )

        self.assertEqual(result.phase, Phase.PLANNING)
        self.assertTrue(result.success)
        self.assertEqual(result.data["prd_generated"], True)
        self.assertEqual(result.checkpoint, "abc123")
        self.assertEqual(len(result.errors), 0)

    def test_phase_result_with_errors(self):
        """Test PhaseResult with errors."""
        result = PhaseResult(
            phase=Phase.IMPLEMENTATION,
            success=False,
            errors=["Test failure"],
        )

        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 1)
        self.assertIsNone(result.checkpoint)


if __name__ == "__main__":
    unittest.main()
