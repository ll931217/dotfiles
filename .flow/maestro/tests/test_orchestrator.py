#!/usr/bin/env python3
"""
Tests for Maestro Orchestrator

Comprehensive unit tests for the main orchestrator.py module.
"""

import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "decision-engine" / "scripts"))

from orchestrator import MaestroOrchestrator
from session_manager import SessionStatus


class TestMaestroOrchestratorInitialization(unittest.TestCase):
    """Test MaestroOrchestrator initialization and basic setup."""

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
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        from session_manager import SessionStatus

        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature: user authentication",
            "status": SessionStatus.INITIALIZING.value,
            "current_phase": "plan",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "feature/test-auth",
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
    capabilities:
      - code_writing
      - debugging
      - analysis
"""
        subagent_config_path = self.project_root / ".claude" / "subagent-types.yaml"
        subagent_config_path.write_text(subagent_config)

        # Set environment variable for subagent config path
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

    def test_initialization(self):
        """Test MaestroOrchestrator initialization."""
        orchestrator = MaestroOrchestrator(self.project_root)

        self.assertEqual(orchestrator.project_root, self.project_root)
        self.assertIsNotNone(orchestrator.session_manager)
        self.assertIsNotNone(orchestrator.decision_logger)
        self.assertIsNotNone(orchestrator.error_handler)
        self.assertIsNotNone(orchestrator.checkpoint_manager)
        self.assertIsNotNone(orchestrator.subagent_factory)
        self.assertIsNotNone(orchestrator.skill_orchestrator)
        self.assertIsNotNone(orchestrator.parallel_coordinator)

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config_path = self.project_root / "custom_config.json"
        custom_config = {
            "max_iterations": 5,
            "enable_checkpoints": True,
        }
        config_path.write_text(json.dumps(custom_config))

        orchestrator = MaestroOrchestrator(self.project_root, config_path)

        self.assertEqual(orchestrator.project_root, self.project_root)

    def test_checkpoint_manager_initialization(self):
        """Test checkpoint manager is initialized."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Verify checkpoint manager was initialized
        self.assertIsNotNone(orchestrator.checkpoint_manager)


class TestMaestroOrchestratorBasicWorkflow(unittest.TestCase):
    """Test basic workflow operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "test-session-123"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        from session_manager import SessionStatus

        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature: user authentication",
            "status": SessionStatus.INITIALIZING.value,
            "current_phase": "plan",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "feature/test-auth",
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

    def test_orchestrator_components_setup(self):
        """Test that orchestrator sets up all components correctly."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Verify all core components are initialized
        self.assertIsNotNone(orchestrator.session_manager)
        self.assertIsNotNone(orchestrator.decision_logger)
        self.assertIsNotNone(orchestrator.error_handler)
        self.assertIsNotNone(orchestrator.checkpoint_manager)
        self.assertIsNotNone(orchestrator.subagent_factory)
        self.assertIsNotNone(orchestrator.skill_orchestrator)
        self.assertIsNotNone(orchestrator.parallel_coordinator)

    @patch("orchestrator.MaestroOrchestrator._execute_workflow_phases")
    def test_create_new_session_mocked(self, mock_workflow):
        """Test creating a new session with mocked workflow."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Mock session manager methods
        with patch.object(orchestrator.session_manager, 'create_session') as mock_create, \
             patch.object(orchestrator.session_manager, 'get_session') as mock_get, \
             patch.object(orchestrator.session_manager, 'transition_state'):
            mock_session = MagicMock()
            mock_session.session_id = "new-session-456"
            mock_create.return_value = mock_session
            mock_get.return_value = mock_session

            # Mock workflow to return success
            mock_workflow.return_value = {
                "session_id": "new-session-456",
                "status": "completed",
                "iterations": [],
                "decisions": [],
                "checkpoints": [],
            }

            # Create a new session (don't resume)
            result = orchestrator.execute("Test feature request")

            # Verify session was created and workflow executed
            self.assertIsNotNone(result)
            mock_create.assert_called_once()
            mock_workflow.assert_called_once()


class TestMaestroOrchestratorIntegration(unittest.TestCase):
    """Integration tests for MaestroOrchestrator with real components."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "integration-test-123"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        from session_manager import SessionStatus

        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Integration test feature",
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

    def test_session_lifecycle(self):
        """Test complete session lifecycle."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Initial status
        session = orchestrator.session_manager.get_session(self.session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, self.session_id)

    def test_component_integration(self):
        """Test integration of all Maestro components."""
        orchestrator = MaestroOrchestrator(self.project_root)

        # Verify all components are initialized and working together
        self.assertIsNotNone(orchestrator.session_manager)
        self.assertIsNotNone(orchestrator.decision_logger)
        self.assertIsNotNone(orchestrator.error_handler)
        self.assertIsNotNone(orchestrator.checkpoint_manager)
        self.assertIsNotNone(orchestrator.subagent_factory)
        self.assertIsNotNone(orchestrator.skill_orchestrator)
        self.assertIsNotNone(orchestrator.parallel_coordinator)


if __name__ == "__main__":
    unittest.main()
