#!/usr/bin/env python3
"""
Unit tests for Checkpoint Manager

Tests checkpoint creation, validation, rollback, and tracking.
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock

from checkpoint_manager import (
    Checkpoint,
    CheckpointManager,
    CheckpointType,
    CheckpointPhase,
    StateSnapshot,
    CheckpointSummary,
    ValidationResult,
)


class TestCheckpointType(unittest.TestCase):
    """Test CheckpointType enum."""

    def test_checkpoint_type_values(self):
        """Test all checkpoint type values are defined."""
        expected_types = [
            "phase_complete",
            "task_group_complete",
            "safe_state",
            "pre_risky_operation",
            "error_recovery",
            "manual",
        ]

        for cp_type in expected_types:
            self.assertTrue(hasattr(CheckpointType, cp_type.upper()))


class TestCheckpointPhase(unittest.TestCase):
    """Test CheckpointPhase enum."""

    def test_phase_values(self):
        """Test all phase values are defined."""
        expected_phases = [
            "plan",
            "generate_tasks",
            "implement",
            "validate",
            "cleanup",
        ]

        for phase in expected_phases:
            self.assertTrue(hasattr(CheckpointPhase, phase.upper()))


class TestStateSnapshot(unittest.TestCase):
    """Test StateSnapshot dataclass."""

    def test_default_values(self):
        """Test StateSnapshot defaults to zero values."""
        snapshot = StateSnapshot()

        self.assertEqual(snapshot.tasks_completed, 0)
        self.assertEqual(snapshot.decisions_made, 0)
        self.assertEqual(snapshot.files_modified, 0)
        self.assertEqual(snapshot.files_created, 0)
        self.assertEqual(snapshot.tests_passing, 0)
        self.assertEqual(snapshot.tests_failing, 0)

    def test_to_dict(self):
        """Test StateSnapshot serialization."""
        snapshot = StateSnapshot(
            tasks_completed=5,
            decisions_made=3,
            files_modified=10,
            files_created=7,
            tests_passing=15,
            tests_failing=2,
        )

        data = snapshot.to_dict()

        self.assertEqual(data["tasks_completed"], 5)
        self.assertEqual(data["decisions_made"], 3)
        self.assertEqual(data["files_modified"], 10)
        self.assertEqual(data["files_created"], 7)
        self.assertEqual(data["tests_passing"], 15)
        self.assertEqual(data["tests_failing"], 2)


class TestCheckpoint(unittest.TestCase):
    """Test Checkpoint dataclass."""

    def test_checkpoint_creation(self):
        """Test basic checkpoint creation."""
        checkpoint_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            commit_sha="abc123",
            timestamp=timestamp,
            description="Test checkpoint",
            phase=CheckpointPhase.IMPLEMENT,
        )

        self.assertEqual(checkpoint.checkpoint_id, checkpoint_id)
        self.assertEqual(checkpoint.commit_sha, "abc123")
        self.assertEqual(checkpoint.description, "Test checkpoint")
        self.assertEqual(checkpoint.phase, CheckpointPhase.IMPLEMENT)

    def test_to_dict(self):
        """Test checkpoint serialization."""
        checkpoint_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        snapshot = StateSnapshot(
            tasks_completed=5,
            files_created=3,
        )

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            commit_sha="abc123",
            timestamp=timestamp,
            description="Test checkpoint",
            phase=CheckpointPhase.PLAN,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            state_snapshot=snapshot,
            tags=["tag1", "tag2"],
        )

        data = checkpoint.to_dict()

        self.assertEqual(data["checkpoint_id"], checkpoint_id)
        self.assertEqual(data["commit_sha"], "abc123")
        self.assertEqual(data["phase"], "plan")
        self.assertEqual(data["checkpoint_type"], "phase_complete")
        self.assertIn("state_snapshot", data)
        self.assertEqual(len(data["tags"]), 2)

    def test_string_enum_conversion(self):
        """Test conversion of string enums to enum types."""
        checkpoint = Checkpoint(
            checkpoint_id=str(uuid4()),
            commit_sha="abc123",
            timestamp=datetime.utcnow().isoformat() + "Z",
            description="Test",
            phase="implement",  # String instead of enum
            checkpoint_type="manual",  # String instead of enum
        )

        self.assertIsInstance(checkpoint.phase, CheckpointPhase)
        self.assertIsInstance(checkpoint.checkpoint_type, CheckpointType)
        self.assertEqual(checkpoint.phase, CheckpointPhase.IMPLEMENT)
        self.assertEqual(checkpoint.checkpoint_type, CheckpointType.MANUAL)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(is_valid=True)

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)

    def test_invalid_result(self):
        """Test invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Not in git repo"],
            warnings=["Uncommitted changes"],
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.warnings), 1)


class TestCheckpointManager(unittest.TestCase):
    """Test CheckpointManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.session_id = str(uuid4())
        self.manager = CheckpointManager(repo_root=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _init_git_repo(self):
        """Initialize a git repository in temp directory."""
        subprocess = __import__("subprocess")
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir,
            capture_output=True,
        )

        # Create initial commit
        test_file = self.temp_path / "test.txt"
        test_file.write_text("initial content")
        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=self.temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            capture_output=True,
        )

    def test_checkpoint_manager_initialization(self):
        """Test CheckpointManager initialization."""
        manager = CheckpointManager(repo_root=self.temp_dir)

        self.assertEqual(manager.repo_root, self.temp_path)
        self.assertTrue(manager.checkpoints_dir.exists())

    def test_validate_checkpoint_state_no_git(self):
        """Test validation fails without git repository."""
        result = self.manager.validate_checkpoint_state()

        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)

    def test_validate_checkpoint_state_with_git(self):
        """Test validation with git repository."""
        self._init_git_repo()

        result = self.manager.validate_checkpoint_state()

        self.assertTrue(result.is_valid)
        self.assertFalse(result.has_uncommitted_changes)

    def test_validate_checkpoint_state_with_uncommitted_changes(self):
        """Test validation detects uncommitted changes."""
        self._init_git_repo()

        # Create uncommitted change
        test_file = self.temp_path / "test.txt"
        test_file.write_text("modified content")

        result = self.manager.validate_checkpoint_state()

        self.assertTrue(result.is_valid)
        self.assertTrue(result.has_uncommitted_changes)
        self.assertGreater(len(result.warnings), 0)

    @patch("checkpoint_manager.subprocess.run")
    def test_create_checkpoint_without_commit(self, mock_run):
        """Test creating checkpoint without committing first."""
        self._init_git_repo()

        # Mock git commands
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def\n",
            stderr="",
        )

        checkpoint = self.manager.create_checkpoint(
            self.session_id,
            "Test checkpoint",
            CheckpointPhase.IMPLEMENT,
            CheckpointType.SAFE_STATE,
            commit_first=False,
        )

        self.assertIsNotNone(checkpoint.checkpoint_id)
        self.assertEqual(checkpoint.description, "Test checkpoint")
        self.assertEqual(checkpoint.phase, CheckpointPhase.IMPLEMENT)
        self.assertEqual(checkpoint.checkpoint_type, CheckpointType.SAFE_STATE)

    @patch("checkpoint_manager.subprocess.run")
    def test_create_checkpoint_with_state_snapshot(self, mock_run):
        """Test creating checkpoint with state snapshot."""
        self._init_git_repo()

        # Mock git commands
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def\n",
            stderr="",
        )

        snapshot = StateSnapshot(
            tasks_completed=10,
            files_created=5,
            tests_passing=20,
        )

        checkpoint = self.manager.create_checkpoint(
            self.session_id,
            "Test checkpoint",
            CheckpointPhase.PLAN,
            CheckpointType.PHASE_COMPLETE,
            state_snapshot=snapshot,
            commit_first=False,
        )

        self.assertIsNotNone(checkpoint.state_snapshot)
        self.assertEqual(checkpoint.state_snapshot.tasks_completed, 10)
        self.assertEqual(checkpoint.state_snapshot.files_created, 5)

    def test_create_checkpoint_saves_to_log(self):
        """Test checkpoint is saved to log file."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123def\n",
                stderr="",
            )

            checkpoint = self.manager.create_checkpoint(
                self.session_id,
                "Test checkpoint",
                CheckpointPhase.IMPLEMENT,
                commit_first=False,
            )

            # Check log file exists
            log_path = self.manager._get_checkpoint_log_path(self.session_id)
            self.assertTrue(log_path.exists())

            # Load and verify log content
            with open(log_path) as f:
                log_data = json.load(f)

            self.assertEqual(log_data["session_id"], self.session_id)
            self.assertEqual(len(log_data["checkpoints"]), 1)
            self.assertEqual(
                log_data["checkpoints"][0]["checkpoint_id"],
                checkpoint.checkpoint_id,
            )

    def test_list_checkpoints(self):
        """Test listing checkpoints for a session."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

            # Create multiple checkpoints
            cp1 = self.manager.create_checkpoint(
                self.session_id,
                "First checkpoint",
                CheckpointPhase.PLAN,
                commit_first=False,
            )
            cp2 = self.manager.create_checkpoint(
                self.session_id,
                "Second checkpoint",
                CheckpointPhase.IMPLEMENT,
                commit_first=False,
            )

            checkpoints = self.manager.list_checkpoints(self.session_id)

            self.assertEqual(len(checkpoints), 2)
            # Should be sorted newest first
            self.assertEqual(checkpoints[0].checkpoint_id, cp2.checkpoint_id)
            self.assertEqual(checkpoints[1].checkpoint_id, cp1.checkpoint_id)

    def test_get_checkpoint(self):
        """Test getting specific checkpoint."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

            created = self.manager.create_checkpoint(
                self.session_id,
                "Test checkpoint",
                CheckpointPhase.PLAN,
                commit_first=False,
            )

            retrieved = self.manager.get_checkpoint(
                self.session_id,
                created.checkpoint_id,
            )

            self.assertEqual(
                created.checkpoint_id,
                retrieved.checkpoint_id,
            )
            self.assertEqual(created.description, retrieved.description)

    def test_get_nonexistent_checkpoint(self):
        """Test getting non-existent checkpoint raises error."""
        with self.assertRaises(FileNotFoundError):
            self.manager.get_checkpoint(
                self.session_id,
                "nonexistent-id",
            )

    def test_get_checkpoint_summary(self):
        """Test getting checkpoint summary."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

            # Create checkpoints of different types
            self.manager.create_checkpoint(
                self.session_id,
                "Phase complete",
                CheckpointPhase.PLAN,
                CheckpointType.PHASE_COMPLETE,
                commit_first=False,
            )
            self.manager.create_checkpoint(
                self.session_id,
                "Safe state",
                CheckpointPhase.IMPLEMENT,
                CheckpointType.SAFE_STATE,
                commit_first=False,
            )

            summary = self.manager.get_checkpoint_summary(self.session_id)

            self.assertEqual(summary.total_checkpoints, 2)
            self.assertEqual(summary.checkpoints_by_type["phase_complete"], 1)
            self.assertEqual(summary.checkpoints_by_type["safe_state"], 1)

    def test_rollback_to_checkpoint(self):
        """Test rolling back to a checkpoint."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )

            checkpoint = self.manager.create_checkpoint(
                self.session_id,
                "Test checkpoint",
                CheckpointPhase.IMPLEMENT,
                commit_first=False,
            )

            # Perform rollback
            success = self.manager.rollback_to_checkpoint(
                self.session_id,
                checkpoint.checkpoint_id,
                hard_reset=False,
            )

            self.assertTrue(success)

            # Verify checkpoint metadata updated
            updated = self.manager.get_checkpoint(
                self.session_id,
                checkpoint.checkpoint_id,
            )
            self.assertTrue(updated.rollback_used)
            self.assertEqual(updated.rollback_count, 1)

    def test_rollback_with_uncommitted_changes_fails(self):
        """Test rollback fails with uncommitted changes."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            # Mock validation to return uncommitted changes
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=" M test.txt\n",
                stderr="",
            )

            checkpoint = self.manager.create_checkpoint(
                self.session_id,
                "Test checkpoint",
                CheckpointPhase.IMPLEMENT,
                commit_first=False,
            )

            # Try to rollback with uncommitted changes
            with self.assertRaises(ValueError) as context:
                self.manager.rollback_to_checkpoint(
                    self.session_id,
                    checkpoint.checkpoint_id,
                )

            self.assertIn("uncommitted changes", str(context.exception))

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )

            checkpoint = self.manager.create_checkpoint(
                self.session_id,
                "Test checkpoint",
                CheckpointPhase.PLAN,
                commit_first=False,
            )

            # Delete checkpoint
            success = self.manager.delete_checkpoint(
                self.session_id,
                checkpoint.checkpoint_id,
                delete_tag=False,
            )

            self.assertTrue(success)

            # Verify checkpoint is deleted
            with self.assertRaises(FileNotFoundError):
                self.manager.get_checkpoint(
                    self.session_id,
                    checkpoint.checkpoint_id,
                )

    def test_checkpoint_log_persistence(self):
        """Test checkpoint log persists across manager instances."""
        self._init_git_repo()

        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

            # Create checkpoint with first manager
            manager1 = CheckpointManager(repo_root=self.temp_dir)
            cp1 = manager1.create_checkpoint(
                self.session_id,
                "Test checkpoint",
                CheckpointPhase.PLAN,
                commit_first=False,
            )

            # Retrieve with new manager instance
            manager2 = CheckpointManager(repo_root=self.temp_dir)
            cp2 = manager2.get_checkpoint(
                self.session_id,
                cp1.checkpoint_id,
            )

            self.assertEqual(cp1.checkpoint_id, cp2.checkpoint_id)
            self.assertEqual(cp1.description, cp2.description)

    def test_checkpoint_without_session_id(self):
        """Test CheckpointManager can be initialized without session_id."""
        manager = CheckpointManager(repo_root=self.temp_dir)

        self.assertIsNone(manager.session_id)

        # Session ID provided when creating checkpoint
        with patch("checkpoint_manager.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="abc123\n",
                stderr="",
            )

            checkpoint = manager.create_checkpoint(
                self.session_id,
                "Test",
                CheckpointPhase.PLAN,
                commit_first=False,
            )

            self.assertIsNotNone(checkpoint.checkpoint_id)


class TestCheckpointIntegration(unittest.TestCase):
    """Integration tests for checkpoint workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.session_id = str(uuid4())

        # Initialize git repo
        subprocess = __import__("subprocess")
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir,
            capture_output=True,
        )

        # Initial commit
        test_file = self.temp_path / "test.txt"
        test_file.write_text("initial")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=self.temp_dir,
            capture_output=True,
        )

        self.manager = CheckpointManager(repo_root=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_checkpoint_workflow(self):
        """Test complete checkpoint creation and query workflow."""
        # Create multiple checkpoints
        phases = [
            CheckpointPhase.PLAN,
            CheckpointPhase.IMPLEMENT,
            CheckpointPhase.VALIDATE,
        ]

        checkpoint_ids = []
        for phase in phases:
            subprocess = __import__("subprocess")
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
            )
            commit_sha = result.stdout.strip()

            checkpoint = Checkpoint(
                checkpoint_id=str(uuid4()),
                commit_sha=commit_sha,
                timestamp=datetime.utcnow().isoformat() + "Z",
                description=f"Checkpoint at {phase.value}",
                phase=phase,
                checkpoint_type=CheckpointType.PHASE_COMPLETE,
            )

            # Manually save checkpoint
            self.manager._save_checkpoint(self.session_id, checkpoint)
            checkpoint_ids.append(checkpoint.checkpoint_id)

        # List checkpoints
        checkpoints = self.manager.list_checkpoints(self.session_id)
        self.assertEqual(len(checkpoints), 3)

        # Get summary
        summary = self.manager.get_checkpoint_summary(self.session_id)
        self.assertEqual(summary.total_checkpoints, 3)
        self.assertEqual(summary.checkpoints_by_type["phase_complete"], 3)


if __name__ == "__main__":
    unittest.main()
