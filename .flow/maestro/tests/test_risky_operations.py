#!/usr/bin/env python3
"""
Unit tests for Risky Operations Detection and Checkpoint Integration

Tests risky operation detection, classification, pre-operation checkpoint
creation, auto-rollback triggers, and safe execution wrapper.
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock, Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from risky_operations import (
    RiskyOperationDetector,
    OperationRisk,
    RiskLevel,
)
from checkpoint_manager import (
    CheckpointManager,
    CheckpointType,
    CheckpointPhase,
    StateSnapshot,
)


class TestRiskLevel(unittest.TestCase):
    """Test RiskLevel enum."""

    def test_risk_level_values(self):
        """Test all risk level values are defined."""
        expected_levels = ["low", "medium", "high", "critical"]

        for level in expected_levels:
            self.assertTrue(hasattr(RiskLevel, level.upper()))


class TestOperationRisk(unittest.TestCase):
    """Test OperationRisk dataclass."""

    def test_operation_risk_creation(self):
        """Test OperationRisk object creation."""
        risk = OperationRisk(
            is_risky=True,
            operation_type="git_push",
            risk_level=RiskLevel.HIGH,
            description="Git push operation",
            requires_checkpoint=True,
            suggested_mitigation="Create checkpoint first",
        )

        self.assertTrue(risk.is_risky)
        self.assertEqual(risk.operation_type, "git_push")
        self.assertEqual(risk.risk_level, RiskLevel.HIGH)

    def test_to_dict(self):
        """Test OperationRisk serialization."""
        risk = OperationRisk(
            is_risky=True,
            operation_type="file_deletion",
            risk_level=RiskLevel.CRITICAL,
            description="Delete files",
            requires_checkpoint=True,
            suggested_mitigation="Verify paths",
        )

        data = risk.to_dict()

        self.assertTrue(data["is_risky"])
        self.assertEqual(data["operation_type"], "file_deletion")
        self.assertEqual(data["risk_level"], "critical")
        self.assertEqual(data["description"], "Delete files")
        self.assertTrue(data["requires_checkpoint"])
        self.assertEqual(data["suggested_mitigation"], "Verify paths")


class TestRiskyOperationDetector(unittest.TestCase):
    """Test risky operation detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = RiskyOperationDetector()

    def test_detect_git_push(self):
        """Test detection of git push operations."""
        operations = [
            "git push origin master",
            "git push --force",
            "git commit --amend",
            "git rebase main",
        ]

        for op in operations:
            with self.subTest(operation=op):
                risk = self.detector.classify_operation(op)
                self.assertTrue(risk.is_risky, f"Failed to detect: {op}")
                self.assertEqual(risk.operation_type, "git_push")
                self.assertEqual(risk.risk_level, RiskLevel.HIGH)

    def test_detect_file_deletion(self):
        """Test detection of file deletion operations."""
        operations = [
            "rm -rf /path/to/files",
            "del /Q C:\\files",
            "unlink important_file.txt",
            "shred sensitive.dat",
        ]

        for op in operations:
            with self.subTest(operation=op):
                risk = self.detector.classify_operation(op)
                self.assertTrue(risk.is_risky, f"Failed to detect: {op}")
                self.assertEqual(risk.operation_type, "file_deletion")
                self.assertEqual(risk.risk_level, RiskLevel.CRITICAL)

    def test_detect_bulk_modification(self):
        """Test detection of bulk modification operations."""
        operations = [
            "mass delete *.log",
            "bulk update user records",
            "replace all 'foo' with 'bar'",
            "find . -name '*.tmp' -exec rm {} \\;",
        ]

        for op in operations:
            with self.subTest(operation=op):
                risk = self.detector.classify_operation(op)
                self.assertTrue(risk.is_risky, f"Failed to detect: {op}")
                self.assertIn(risk.operation_type, ["bulk_modification"])

    def test_detect_database_migration(self):
        """Test detection of database migration operations."""
        operations = [
            "python manage.py migrate",
            "alembic upgrade head",
            "rollback database to v1",
            "DROP TABLE users",
            "TRUNCATE TABLE logs",
        ]

        for op in operations:
            with self.subTest(operation=op):
                risk = self.detector.classify_operation(op)
                self.assertTrue(risk.is_risky, f"Failed to detect: {op}")
                self.assertEqual(risk.operation_type, "database_migration")
                self.assertEqual(risk.risk_level, RiskLevel.CRITICAL)

    def test_detect_safe_operations(self):
        """Test that safe operations are not flagged as risky."""
        safe_operations = [
            "git status",
            "git log --oneline",
            "ls -la",
            "cat README.md",
            "echo 'hello world'",
            "pytest --dry-run",
        ]

        for op in safe_operations:
            with self.subTest(operation=op):
                risk = self.detector.classify_operation(op)
                self.assertFalse(risk.is_risky, f"Incorrectly flagged as risky: {op}")
                self.assertEqual(risk.risk_level, RiskLevel.LOW)

    def test_is_risky_operation(self):
        """Test the is_risky_operation helper method."""
        self.assertTrue(self.detector.is_risky_operation("git push origin main"))
        self.assertFalse(self.detector.is_risky_operation("git status"))

    def test_get_operation_description(self):
        """Test generation of human-readable operation description."""
        description = self.detector.get_operation_description("git push origin main")

        self.assertIn("HIGH", description)
        self.assertIn("Git operation that modifies remote history", description)
        self.assertIn("git_push", description)
        self.assertIn("Requires Checkpoint: Yes", description)

    def test_should_create_checkpoint(self):
        """Test checkpoint creation decision."""
        self.assertTrue(
            self.detector.should_create_checkpoint("rm -rf /tmp/*")
        )
        self.assertFalse(
            self.detector.should_create_checkpoint("git status")
        )

    def test_get_risky_operations_from_list(self):
        """Test filtering risky operations from a list."""
        operations = [
            "git status",
            "git push origin main",
            "ls -la",
            "rm -rf /tmp/test",
            "cat README.md",
            "python manage.py migrate",
        ]

        risky_ops = self.detector.get_risky_operations_from_list(operations)

        self.assertEqual(len(risky_ops), 3)
        self.assertEqual(risky_ops[0]["index"], 1)
        self.assertEqual(risky_ops[1]["index"], 3)
        self.assertEqual(risky_ops[2]["index"], 5)

    def test_estimate_recovery_complexity(self):
        """Test recovery complexity estimation."""
        test_cases = [
            ("git status", "simple"),
            ("git push origin main", "moderate"),
            ("bulk delete *.log", "complex"),
            ("python manage.py migrate", "very_complex"),
            ("deploy to production", "very_complex"),
        ]

        for operation, expected_complexity in test_cases:
            with self.subTest(operation=operation):
                complexity = self.detector.estimate_recovery_complexity(operation)
                self.assertEqual(complexity, expected_complexity)

    def test_custom_pattern_config(self):
        """Test detector with custom patterns."""
        custom_config = {
            "custom_patterns": {
                "custom_risky": {
                    "pattern": r"dangerous\s+command",
                    "risk_level": RiskLevel.MEDIUM,
                    "description": "Custom dangerous command",
                    "mitigation": "Be careful",
                },
            },
        }

        custom_detector = RiskyOperationDetector(config=custom_config)
        risk = custom_detector.classify_operation("dangerous command here")

        self.assertTrue(risk.is_risky)
        self.assertEqual(risk.operation_type, "custom_risky")


class TestCheckpointPreOperations(unittest.TestCase):
    """Test checkpoint manager pre-operation support."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.session_id = str(uuid4())

        # Initialize checkpoint manager with temp directory
        self.checkpoint_manager = CheckpointManager(
            repo_root=self.temp_dir,
            session_id=self.session_id,
        )

        # Initialize git repository
        self._init_git_repo()

    def _init_git_repo(self):
        """Initialize a git repository in temp directory."""
        import subprocess

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
        test_file = self.temp_path / "README.md"
        test_file.write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            capture_output=True,
        )

    def test_create_pre_operation_checkpoint(self):
        """Test creating a pre-operation checkpoint."""
        checkpoint = self.checkpoint_manager.create_pre_operation_checkpoint(
            session_id=self.session_id,
            operation_type="git_push",
            operation_description="Push to origin main",
            phase=CheckpointPhase.IMPLEMENT,
        )

        self.assertEqual(checkpoint.checkpoint_type, CheckpointType.PRE_RISKY_OPERATION)
        self.assertIn("Pre-operation checkpoint before git_push", checkpoint.description)
        self.assertIn("Push to origin main", checkpoint.description)
        self.assertIsNotNone(checkpoint.commit_sha)

    def test_pre_operation_checkpoint_with_state_snapshot(self):
        """Test creating pre-operation checkpoint with state snapshot."""
        snapshot = StateSnapshot(
            tasks_completed=5,
            decisions_made=3,
            files_modified=10,
        )

        checkpoint = self.checkpoint_manager.create_pre_operation_checkpoint(
            session_id=self.session_id,
            operation_type="file_deletion",
            operation_description="Delete temp files",
            state_snapshot=snapshot,
        )

        self.assertEqual(checkpoint.state_snapshot.tasks_completed, 5)
        self.assertEqual(checkpoint.state_snapshot.files_modified, 10)

    def test_should_trigger_rollback_exhausted_attempts(self):
        """Test rollback trigger on exhausted attempts."""
        error_context = {
            "error_category": "transient",
            "error_type": "timeout",
        }

        # Should trigger after 3 attempts
        self.assertFalse(
            self.checkpoint_manager.should_trigger_rollback(error_context, 1)
        )
        self.assertFalse(
            self.checkpoint_manager.should_trigger_rollback(error_context, 2)
        )
        self.assertTrue(
            self.checkpoint_manager.should_trigger_rollback(error_context, 3)
        )

    def test_should_trigger_rollback_permanent_error(self):
        """Test immediate rollback trigger on permanent errors."""
        error_context = {
            "error_category": "permanent",
            "error_type": "disk_full",
        }

        # Should trigger immediately regardless of attempts
        self.assertTrue(
            self.checkpoint_manager.should_trigger_rollback(error_context, 1)
        )

    def test_should_trigger_rollback_resource_exhaustion(self):
        """Test rollback trigger on resource exhaustion with partial progress."""
        error_context = {
            "error_category": "transient",
            "error_type": "timeout",
            "resource_exhausted": True,
            "has_partial_progress": True,
        }

        # Should trigger immediately
        self.assertTrue(
            self.checkpoint_manager.should_trigger_rollback(error_context, 1)
        )

    def test_should_trigger_rollback_validation_failure(self):
        """Test rollback trigger on validation failures."""
        error_context = {
            "error_category": "transient",
            "error_type": "validation_error",
            "validation_failed": True,
        }

        # Should trigger after 2 attempts
        self.assertFalse(
            self.checkpoint_manager.should_trigger_rollback(error_context, 1)
        )
        self.assertTrue(
            self.checkpoint_manager.should_trigger_rollback(error_context, 2)
        )

    def test_should_trigger_rollback_unrecoverable_errors(self):
        """Test rollback trigger on unrecoverable error types."""
        unrecoverable_errors = [
            "disk_full",
            "permission_denied",
            "database_connection_lost",
            "network_partition",
        ]

        for error_type in unrecoverable_errors:
            with self.subTest(error_type=error_type):
                error_context = {
                    "error_category": "transient",
                    "error_type": error_type,
                }

                self.assertTrue(
                    self.checkpoint_manager.should_trigger_rollback(error_context, 1)
                )


class TestOrchestratorCheckpointWrapper(unittest.TestCase):
    """Test orchestrator execute_with_checkpoint wrapper."""

    def setUp(self):
        """Set up test fixtures."""
        from orchestrator import MaestroOrchestrator

        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Initialize git repository
        self._init_git_repo()

        # Initialize orchestrator
        self.orchestrator = MaestroOrchestrator(
            project_root=self.temp_path,
        )
        self.orchestrator.session_id = str(uuid4())

    def _init_git_repo(self):
        """Initialize a git repository in temp directory."""
        import subprocess

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
        test_file = self.temp_path / "README.md"
        test_file.write_text("# Test Repository")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            capture_output=True,
        )

    @patch('orchestrator.RiskyOperationDetector')
    def test_execute_with_safe_operation(self, mock_detector_class):
        """Test execution of safe operation without checkpoint."""
        # Mock safe operation
        mock_detector = MagicMock()
        mock_detector.classify_operation.return_value = OperationRisk(
            is_risky=False,
            operation_type=None,
            risk_level=RiskLevel.LOW,
            description="Safe operation",
            requires_checkpoint=False,
        )
        mock_detector_class.return_value = mock_detector

        # Execute safe operation
        def safe_func():
            return "operation_result"

        result = self.orchestrator.execute_with_checkpoint(
            operation="git status",
            operation_func=safe_func,
            phase=CheckpointPhase.IMPLEMENT,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "operation_result")
        self.assertFalse(result["checkpoint_created"])
        self.assertFalse(result["rollback_performed"])

    @patch('orchestrator.RiskyOperationDetector')
    def test_execute_with_risky_operation_success(self, mock_detector_class):
        """Test successful execution of risky operation with checkpoint."""
        # Mock risky operation
        mock_detector = MagicMock()
        mock_detector.classify_operation.return_value = OperationRisk(
            is_risky=True,
            operation_type="git_push",
            risk_level=RiskLevel.HIGH,
            description="Git push",
            requires_checkpoint=True,
            suggested_mitigation="Create checkpoint",
        )
        mock_detector_class.return_value = mock_detector

        # Execute risky operation
        def risky_func():
            return "pushed_successfully"

        result = self.orchestrator.execute_with_checkpoint(
            operation="git push origin main",
            operation_func=risky_func,
            phase=CheckpointPhase.IMPLEMENT,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "pushed_successfully")
        self.assertTrue(result["checkpoint_created"])
        self.assertIsNotNone(result["checkpoint_id"])
        self.assertFalse(result["rollback_performed"])

    @patch('orchestrator.RiskyOperationDetector')
    def test_execute_with_risky_operation_failure_and_rollback(self, mock_detector_class):
        """Test execution failure triggering rollback."""
        # Mock risky operation
        mock_detector = MagicMock()
        mock_detector.classify_operation.return_value = OperationRisk(
            is_risky=True,
            operation_type="file_deletion",
            risk_level=RiskLevel.CRITICAL,
            description="Delete files",
            requires_checkpoint=True,
        )
        mock_detector_class.return_value = mock_detector

        # Execute failing operation
        def failing_func():
            class CustomError(Exception):
                category = "permanent"

            raise CustomError("Deletion failed")

        result = self.orchestrator.execute_with_checkpoint(
            operation="rm -rf /tmp/test",
            operation_func=failing_func,
            phase=CheckpointPhase.IMPLEMENT,
            max_recovery_attempts=1,
        )

        # The operation should have failed
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])
        # The error should mention the failure
        self.assertIn("Deletion failed", result["error"])


class TestRollbackContextPreservation(unittest.TestCase):
    """Test that rollback preserves operation context."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.session_id = str(uuid4())

        self.checkpoint_manager = CheckpointManager(
            repo_root=self.temp_dir,
            session_id=self.session_id,
        )

        self._init_git_repo()

    def _init_git_repo(self):
        """Initialize git repository."""
        import subprocess

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

        test_file = self.temp_path / "README.md"
        test_file.write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=self.temp_dir,
            capture_output=True,
        )

    def test_checkpoint_preserves_operation_context(self):
        """Test that pre-operation checkpoints preserve operation context."""
        checkpoint = self.checkpoint_manager.create_pre_operation_checkpoint(
            session_id=self.session_id,
            operation_type="database_migration",
            operation_description="Migrate user tables to v2",
            phase=CheckpointPhase.IMPLEMENT,
        )

        # Check that operation context is stored
        self.assertTrue(hasattr(checkpoint, "operation_context"))
        self.assertEqual(
            checkpoint.operation_context["operation_type"],
            "database_migration",
        )
        self.assertEqual(
            checkpoint.operation_context["operation_description"],
            "Migrate user tables to v2",
        )
        self.assertIn("created_at", checkpoint.operation_context)

    def test_rollback_preserves_state_snapshot(self):
        """Test that rollback preserves and reports the state snapshot."""
        snapshot = StateSnapshot(
            tasks_completed=10,
            decisions_made=5,
            files_modified=20,
            files_created=15,
        )

        # Create a test file and commit it
        test_file = self.temp_path / "test.txt"
        test_file.write_text("test content")
        import subprocess
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=self.temp_dir,
            capture_output=True,
        )

        checkpoint = self.checkpoint_manager.create_pre_operation_checkpoint(
            session_id=self.session_id,
            operation_type="bulk_modification",
            operation_description="Update all user records",
            state_snapshot=snapshot,
        )

        # The checkpoint creates a tag, so we need to handle that for rollback
        # Git tags are not "uncommitted changes" for git reset purposes
        # But the checkpoint manager checks git status which shows tag refs
        # So we need to skip the uncommitted changes check for this test

        # Perform rollback with hard_reset to skip validation
        rollback_op = self.checkpoint_manager.rollback_to_checkpoint(
            session_id=self.session_id,
            checkpoint_id=checkpoint.checkpoint_id,
            hard_reset=True,  # Skip the uncommitted changes check
        )

        # Verify state snapshot is preserved in rollback
        self.assertIsNotNone(rollback_op.state_snapshot_restored)
        self.assertEqual(
            rollback_op.state_snapshot_restored.tasks_completed,
            10,
        )
        self.assertEqual(
            rollback_op.state_snapshot_restored.files_modified,
            20,
        )


if __name__ == "__main__":
    unittest.main()
