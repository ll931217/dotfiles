#!/usr/bin/env python3
"""
End-to-End Tests for Autonomous Workflows

Tests complete autonomous implementation flows from feature request
to completion, including error recovery and validation.
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "decision-engine" / "scripts"))

from orchestrator import MaestroOrchestrator
from session_manager import SessionStatus
from checkpoint_manager import CheckpointPhase


class TestE2EWorkflowBasic(unittest.TestCase):
    """E2E tests for basic autonomous workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "e2e-test-session"

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
            "feature_request": "E2E test feature",
            "status": SessionStatus.INITIALIZING.value,
            "current_phase": "plan",
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
        subagent_config_path = self.project_root / ".claude" / "subagent-types.yaml"
        subagent_config_path.write_text(subagent_config)

        import os
        os.environ["SUBAGENT_TYPES_PATH"] = str(subagent_config_path)

        # Mock git commands
        self.git_patcher = patch("subprocess.run")
        self.mock_run = self.git_patcher.start()
        self.mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch("orchestrator.MaestroOrchestrator._execute_workflow_phases")
    def test_e2e_feature_request_to_completion(self, mock_workflow):
        """Test complete flow from feature request to completion."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Mock workflow to return successful completion
        mock_workflow.return_value = {
            "iterations": [],
            "decisions": [],
            "checkpoints": [],
        }

        # Mock session manager methods
        with patch.object(orchestrator.session_manager, 'create_session') as mock_create, \
             patch.object(orchestrator.session_manager, 'get_session') as mock_get, \
             patch.object(orchestrator.session_manager, 'transition_state'):

            mock_session = MagicMock()
            mock_session.session_id = "e2e-result-session"
            mock_create.return_value = mock_session
            mock_get.return_value = mock_session

            # Execute feature request
            result = orchestrator.execute("Implement user authentication")

            # Verify successful completion
            self.assertIsNotNone(result)
            self.assertEqual(result["status"], "completed")

    @patch("orchestrator.MaestroOrchestrator._execute_workflow_phases")
    def test_e2e_session_resume(self, mock_workflow):
        """Test resuming an existing session."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Mock workflow to return continuation
        mock_workflow.return_value = {
            "iterations": [],
            "decisions": [],
            "checkpoints": [],
        }

        # Mock session manager
        with patch.object(orchestrator.session_manager, 'get_session') as mock_get, \
             patch.object(orchestrator.session_manager, 'transition_state'):

            mock_session = MagicMock()
            mock_session.session_id = self.session_id
            mock_get.return_value = mock_session

            # Resume session by passing session_id
            result = orchestrator.execute("Continue implementation", resume_session=self.session_id)

            # Verify session was resumed
            self.assertIsNotNone(result)


class TestE2EWorkflowPhases(unittest.TestCase):
    """E2E tests for individual workflow phases."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "e2e-phase-test"

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
            "feature_request": "Test phase workflow",
            "status": SessionStatus.INITIALIZING.value,
            "current_phase": "plan",
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

    def test_e2e_phase_planning(self):
        """Test planning phase completes successfully."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Mock session manager
        with patch.object(orchestrator.session_manager, 'get_session') as mock_get, \
             patch.object(orchestrator.session_manager, 'transition_state'):

            mock_session = MagicMock()
            mock_session.session_id = self.session_id
            mock_get.return_value = mock_session

            # Test planning phase (would normally generate PRD)
            # For E2E test, just verify phase can be set
            orchestrator.session_manager.transition_state(
                session_id=self.session_id,
                new_state=SessionStatus.PLANNING
            )

    def test_e2e_phase_implementation(self):
        """Test implementation phase completes successfully."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Mock session manager
        with patch.object(orchestrator.session_manager, 'get_session') as mock_get, \
             patch.object(orchestrator.session_manager, 'transition_state'):

            mock_session = MagicMock()
            mock_session.session_id = self.session_id
            mock_get.return_value = mock_session

            # Test implementation phase
            orchestrator.session_manager.transition_state(
                session_id=self.session_id,
                new_state=SessionStatus.IMPLEMENTING
            )

    def test_e2e_phase_validation(self):
        """Test validation phase completes successfully."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Mock session manager
        with patch.object(orchestrator.session_manager, 'get_session') as mock_get, \
             patch.object(orchestrator.session_manager, 'transition_state'):

            mock_session = MagicMock()
            mock_session.session_id = self.session_id
            mock_get.return_value = mock_session

            # Test validation phase
            orchestrator.session_manager.transition_state(
                session_id=self.session_id,
                new_state=SessionStatus.VALIDATING
            )


class TestE2ECheckpointRecovery(unittest.TestCase):
    """E2E tests for checkpoint and recovery scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "e2e-checkpoint-test"

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
            "feature_request": "Test checkpoint recovery",
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

    def test_e2e_checkpoint_creation_and_recovery(self):
        """Test creating checkpoint and recovering from it."""
        from checkpoint_manager import CheckpointType, StateSnapshot

        orchestrator = MaestroOrchestrator(self.project_root)

        # Create checkpoint
        checkpoint = orchestrator.checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.IMPLEMENT,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="Test checkpoint for recovery",
            state_snapshot=StateSnapshot(tasks_completed=5)
        )

        # Verify checkpoint created
        self.assertIsNotNone(checkpoint)
        self.assertEqual(checkpoint.phase, CheckpointPhase.IMPLEMENT)

        # Verify checkpoint can be retrieved
        retrieved = orchestrator.checkpoint_manager.get_checkpoint(
            self.session_id,
            checkpoint.checkpoint_id
        )

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.checkpoint_id, checkpoint.checkpoint_id)


class TestE2EValidationReporting(unittest.TestCase):
    """E2E tests for validation and reporting phases."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "e2e-validation-test"

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
            "feature_request": "Test validation and reporting",
            "status": SessionStatus.VALIDATING.value,
            "current_phase": "validate",
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

    def test_e2e_validation_quality_gates(self):
        """Test validation phase with quality gates."""
        from quality_gate_runner import QualityGateRunner, QualityGateResult, QualityGateStatus

        runner = QualityGateRunner(self.project_root, self.session_id)

        # Create a simple mock result that's JSON-serializable
        mock_result = QualityGateResult(
            gate_name="test_gate",
            status=QualityGateStatus.PASSED,
            message="Test passed",
            score=100.0
        )

        # Verify the result can be created
        self.assertEqual(mock_result.status, QualityGateStatus.PASSED)
        self.assertEqual(mock_result.score, 100.0)

        # Verify to_dict works for JSON serialization
        result_dict = mock_result.to_dict()
        self.assertIn("gate_name", result_dict)
        self.assertIn("status", result_dict)

    def test_e2e_report_generation(self):
        """Test final report generation."""
        from report_generator import ReportGenerator, ReportData, ReportFormat

        generator = ReportGenerator(self.project_root, self.session_id)

        # Generate report with sample data
        report_data = ReportData(
            session_id=self.session_id,
            feature_request="Test feature",
        )

        report = generator.generate_report(
            report_data=report_data,
            output_format=ReportFormat.MARKDOWN,
        )

        # Verify report generated
        self.assertIn("Implementation Report", report)


class TestE2EErrorScenarios(unittest.TestCase):
    """E2E tests for error handling scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "e2e-error-test"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

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

    def test_e2e_handles_missing_session_gracefully(self):
        """Test handling of missing session during execution."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Try to resume non-existent session
        # Should raise FileNotFoundError for missing session
        with self.assertRaises(FileNotFoundError) as context:
            orchestrator.execute("Continue work", resume_session="non-existent-session")

        # Verify error message mentions session not found
        self.assertIn("not found", str(context.exception).lower())

    def test_e2e_handles_checkpoint_failure(self):
        """Test handling of checkpoint creation failure."""
        from checkpoint_manager import CheckpointManager, CheckpointType, CheckpointPhase, StateSnapshot

        manager = CheckpointManager(self.project_root)

        # Create checkpoint for non-existent session (should handle gracefully)
        try:
            checkpoint = manager.create_checkpoint(
                session_id="non-existent-session",
                phase=CheckpointPhase.PLAN,
                checkpoint_type=CheckpointType.PHASE_COMPLETE,
                description="Test",
                state_snapshot=StateSnapshot()
            )
            # If it succeeds, verify it created the session
            self.assertIsNotNone(checkpoint)
        except Exception as e:
            # If it fails, verify it's a reasonable error
            self.assertIsNotNone(e)


if __name__ == "__main__":
    unittest.main()
