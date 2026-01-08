#!/usr/bin/env python3
"""
Unit tests for Maestro Orchestrator Validation Phase

Tests the autonomous validation functionality including:
- Test framework detection and execution
- PRD requirement validation
- Quality gate execution (linting, typecheck, security)
- Validation report generation
- Autonomous recovery from validation failures
- Session state transitions
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch, call
from typing import Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from orchestrator import MaestroOrchestrator
from session_manager import SessionManager, SessionStatus
from checkpoint_manager import CheckpointManager, CheckpointPhase, CheckpointType
from decision_logger import DecisionLogger


class TestValidationPhase(unittest.TestCase):
    """Test cases for the validation phase implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "test-validation-session-123"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        import json
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature for validation",
            "status": SessionStatus.IMPLEMENTING.value,
            "current_phase": "validate",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "test-branch",
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
        self.mock_run.return_value = MagicMock(stdout="test-branch\n", returncode=0)

        # Create orchestrator
        self.orchestrator = MaestroOrchestrator(self.project_root)
        self.orchestrator.session_id = self.session_id

        # Create a test PRD file
        self.prd_path = self.project_root / "test-prd.md"
        self.prd_path.write_text("""---
title: Test PRD
status: approved
requirements:
  - id: REQ-1
    title: First requirement
    description: Implement first feature
    category: core
    priority: P0
    validation_criteria:
      - Unit tests pass
      - Integration tests pass
  - id: REQ-2
    title: Second requirement
    description: Implement second feature
    category: ui
    priority: P1
---

# Test PRD

This is a test PRD for validation.
""")

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_detect_test_framework_pytest(self):
        """Test detection of pytest framework."""
        # Create pytest.ini
        (self.project_root / "pytest.ini").write_text("[pytest]\n")

        framework = self.orchestrator._detect_test_framework()

        self.assertEqual(framework, "pytest")

    def test_detect_test_framework_unittest(self):
        """Test detection of unittest framework."""
        # Create tests directory without pytest markers
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("""
import unittest

class TestExample(unittest.TestCase):
    def test_example(self):
        self.assertTrue(True)
""")

        framework = self.orchestrator._detect_test_framework()

        self.assertEqual(framework, "unittest")

    def test_detect_test_framework_none(self):
        """Test detection when no framework is present."""
        framework = self.orchestrator._detect_test_framework()

        self.assertIsNone(framework)

    def test_execute_pytest_success(self):
        """Test successful pytest execution."""
        # Mock pytest output
        self.mock_run.return_value = MagicMock(
            returncode=0,
            stdout="130 passed in 5.2s\n",
            stderr="",
        )

        result = self.orchestrator._run_pytest()

        self.assertTrue(result["success"])
        self.assertEqual(result["passed"], 130)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["total"], 130)

    def test_execute_pytest_with_failures(self):
        """Test pytest execution with failures."""
        # Mock pytest output with failures
        self.mock_run.return_value = MagicMock(
            returncode=1,
            stdout="127 passed, 3 failed\nFAILED test_module.py::test_function\n",
            stderr="",
        )

        result = self.orchestrator._run_pytest()

        self.assertFalse(result["success"])
        self.assertEqual(result["passed"], 127)
        self.assertEqual(result["failed"], 3)
        self.assertEqual(result["total"], 130)
        self.assertTrue(len(result["failures"]) > 0)

    def test_execute_unittest_success(self):
        """Test successful unittest execution."""
        # Mock unittest output
        self.mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Ran 50 tests in 2.1s\nOK\n",
            stderr="",
        )

        result = self.orchestrator._run_unittest()

        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 50)
        self.assertEqual(result["passed"], 50)
        self.assertEqual(result["failed"], 0)

    def test_execute_unittest_with_failures(self):
        """Test unittest execution with failures."""
        # Mock unittest output with failures
        self.mock_run.return_value = MagicMock(
            returncode=1,
            stdout="Ran 50 tests in 2.1s\nFAILED (failures=2)\n",
            stderr="",
        )

        result = self.orchestrator._run_unittest()

        self.assertFalse(result["success"])
        self.assertEqual(result["total"], 50)
        self.assertEqual(result["failed"], 1)

    @patch("subprocess.run")
    def test_check_linting_passed(self, mock_subprocess):
        """Test linting check when passed."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = self.orchestrator._check_linting()

        self.assertEqual(result["status"], "passed")
        self.assertIn("No linting issues", result["message"])

    @patch("subprocess.run")
    def test_check_linting_failed(self, mock_subprocess):
        """Test linting check when failed."""
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout="file.py:1:1: E401 multiple imports on one line\n",
            stderr="",
        )

        result = self.orchestrator._check_linting()

        self.assertEqual(result["status"], "failed")
        self.assertIn("linting issues", result["message"])

    @patch("subprocess.run")
    def test_check_typecheck_passed(self, mock_subprocess):
        """Test type checking when passed."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="Success: no issues found\n",
            stderr="",
        )

        result = self.orchestrator._check_typecheck()

        self.assertEqual(result["status"], "passed")
        self.assertIn("No type errors", result["message"])

    @patch("subprocess.run")
    def test_check_typecheck_failed(self, mock_subprocess):
        """Test type checking when failed."""
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout="file.py:5: error: incompatible return value type\n",
            stderr="",
        )

        result = self.orchestrator._check_typecheck()

        self.assertEqual(result["status"], "failed")
        self.assertIn("type errors", result["message"])

    @patch("subprocess.run")
    def test_check_security_passed(self, mock_subprocess):
        """Test security check when passed."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout='{"results": []}\n',
            stderr="",
        )

        result = self.orchestrator._check_security()

        self.assertEqual(result["status"], "passed")
        self.assertIn("No security issues", result["message"])

    @patch("subprocess.run")
    def test_execute_quality_gates(self, mock_subprocess):
        """Test execution of multiple quality gates."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        gate_names = ["lint", "typecheck", "security"]
        results = self.orchestrator._execute_quality_gates(gate_names)

        self.assertEqual(len(results), 3)
        self.assertIn("lint", results)
        self.assertIn("typecheck", results)
        self.assertIn("security", results)
        self.assertEqual(results["lint"]["status"], "passed")
        self.assertEqual(results["typecheck"]["status"], "passed")
        self.assertEqual(results["security"]["status"], "passed")

    @patch("subprocess.run")
    def test_validate_prd_requirements(self, mock_subprocess):
        """Test PRD requirement validation."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        result = self.orchestrator._validate_prd_requirements(self.prd_path)

        self.assertEqual(result["total_requirements"], 2)
        self.assertGreaterEqual(result["coverage_percentage"], 0.0)
        self.assertIsInstance(result["critical_gaps"], list)

    def test_generate_validation_report(self):
        """Test validation report generation."""
        validation_results = {
            "autonomous_mode": True,
            "tests": {
                "framework": "pytest",
                "status": "passed",
                "passed": 127,
                "failed": 0,
                "total": 127,
                "coverage": 85.5,
                "failures": [],
            },
            "prd": {
                "status": "passed",
                "total_requirements": 2,
                "validated_requirements": 2,
                "coverage_percentage": 100.0,
                "critical_gaps": [],
            },
            "quality_gates": {
                "lint": {"status": "passed", "message": "No linting issues"},
                "typecheck": {"status": "passed", "message": "No type errors"},
                "security": {"status": "passed", "message": "No security issues"},
            },
        }

        report = self.orchestrator._generate_validation_report(validation_results)

        self.assertIn("Validation Report", report)
        self.assertIn("pytest", report)
        self.assertIn("127/127", report)
        self.assertIn("85.5%", report)
        self.assertIn("2/2", report)
        self.assertIn("100.0%", report)

    def test_is_validation_successful_all_passed(self):
        """Test validation success check when all passed."""
        validation_results = {
            "tests": {"status": "passed"},
            "prd": {"status": "passed", "critical_gaps": []},
            "quality_gates": {
                "lint": {"status": "passed"},
                "typecheck": {"status": "passed"},
            },
        }

        self.assertTrue(self.orchestrator._is_validation_successful(validation_results))

    def test_is_validation_successful_test_failed(self):
        """Test validation success check when tests failed."""
        validation_results = {
            "tests": {"status": "failed"},
            "prd": {"status": "passed", "critical_gaps": []},
            "quality_gates": {},
        }

        self.assertFalse(self.orchestrator._is_validation_successful(validation_results))

    def test_is_validation_successful_prd_failed(self):
        """Test validation success check when PRD validation failed."""
        validation_results = {
            "tests": {"status": "passed"},
            "prd": {
                "status": "failed",
                "critical_gaps": ["REQ-1", "REQ-2"]
            },
            "quality_gates": {},
        }

        self.assertFalse(self.orchestrator._is_validation_successful(validation_results))

    def test_is_validation_successful_quality_gate_failed(self):
        """Test validation success check when quality gate failed."""
        validation_results = {
            "tests": {"status": "passed"},
            "prd": {"status": "passed", "critical_gaps": []},
            "quality_gates": {
                "lint": {"status": "failed"},
            },
        }

        self.assertFalse(self.orchestrator._is_validation_successful(validation_results))

    @patch("subprocess.run")
    @patch.object(MaestroOrchestrator, '_detect_test_framework')
    @patch.object(MaestroOrchestrator, '_execute_tests')
    @patch.object(MaestroOrchestrator, '_validate_prd_requirements')
    @patch.object(MaestroOrchestrator, '_execute_quality_gates')
    @patch.object(CheckpointManager, 'create_checkpoint')
    def test_phase_validation_full_execution(
        self,
        mock_create_checkpoint,
        mock_execute_gates,
        mock_validate_prd,
        mock_execute_tests,
        mock_detect_framework,
        mock_subprocess,
    ):
        """Test complete validation phase execution."""
        # Setup mocks
        mock_detect_framework.return_value = "pytest"
        mock_execute_tests.return_value = {
            "success": True,
            "passed": 127,
            "failed": 0,
            "total": 127,
            "coverage": 85.5,
            "failures": [],
        }
        mock_validate_prd.return_value = {
            "total_requirements": 2,
            "validated_requirements": 2,
            "coverage_percentage": 100.0,
            "critical_gaps": [],
            "all_requirements_met": True,
        }
        mock_execute_gates.return_value = {
            "lint": {"status": "passed", "message": "No linting issues"},
            "typecheck": {"status": "passed", "message": "No type errors"},
            "security": {"status": "passed", "message": "No security issues"},
        }
        mock_create_checkpoint.return_value = MagicMock(commit_sha="abc123", checkpoint_id="chk-123")

        # Execute validation phase
        result = self.orchestrator._phase_validation(self.prd_path)

        # Verify results
        self.assertTrue(result.get("autonomous_mode"))
        self.assertFalse(result.get("human_interaction"))
        self.assertEqual(result["tests"]["framework"], "pytest")
        self.assertEqual(result["tests"]["status"], "passed")
        self.assertEqual(result["prd"]["status"], "passed")
        self.assertEqual(result["prd"]["coverage_percentage"], 100.0)
        self.assertIn("quality_gates", result)

        # Verify state transition was called
        session = self.orchestrator.session_manager.get_session(self.session_id)
        self.assertEqual(session["status"], SessionStatus.VALIDATING.value)

        # Verify checkpoint was created
        mock_create_checkpoint.assert_called_once()

    @patch("subprocess.run")
    @patch.object(MaestroOrchestrator, '_detect_test_framework')
    @patch.object(MaestroOrchestrator, '_execute_tests')
    @patch.object(MaestroOrchestrator, '_validate_prd_requirements')
    @patch.object(MaestroOrchestrator, '_execute_quality_gates')
    @patch.object(CheckpointManager, 'create_checkpoint')
    def test_phase_validation_with_failures(
        self,
        mock_create_checkpoint,
        mock_execute_gates,
        mock_validate_prd,
        mock_execute_tests,
        mock_detect_framework,
        mock_subprocess,
    ):
        """Test validation phase with failures and recovery."""
        # Setup mocks with failures
        mock_detect_framework.return_value = "pytest"
        mock_execute_tests.return_value = {
            "success": False,
            "passed": 120,
            "failed": 7,
            "total": 127,
            "coverage": 80.0,
            "failures": ["test_module.py::test_function"],
        }
        mock_validate_prd.return_value = {
            "total_requirements": 2,
            "validated_requirements": 1,
            "coverage_percentage": 50.0,
            "critical_gaps": ["REQ-1"],
            "all_requirements_met": False,
        }
        mock_execute_gates.return_value = {
            "lint": {"status": "failed", "message": "Found 5 linting issues"},
            "typecheck": {"status": "passed", "message": "No type errors"},
        }
        mock_create_checkpoint.return_value = MagicMock(commit_sha="abc123", checkpoint_id="chk-123")

        # Execute validation phase
        result = self.orchestrator._phase_validation(self.prd_path)

        # Verify failure is detected
        self.assertEqual(result["tests"]["status"], "failed")
        self.assertEqual(result["prd"]["status"], "failed")
        self.assertIn("recovery", result)

        # Verify recovery was attempted
        recovery = result["recovery"]
        self.assertIn("actions_taken", recovery)
        self.assertIn("strategy", recovery)

    def test_attempt_validation_recovery_no_failures(self):
        """Test validation recovery when there are no failures."""
        validation_results = {
            "tests": {"status": "passed"},
            "prd": {"status": "passed", "critical_gaps": []},
            "quality_gates": {
                "lint": {"status": "passed"},
            },
        }

        recovery = self.orchestrator._attempt_validation_recovery(validation_results)

        self.assertFalse(recovery.get("success"))
        self.assertIn("not attempted", recovery.get("message", ""))

    def test_attempt_validation_recovery_with_failures(self):
        """Test validation recovery with failures."""
        validation_results = {
            "tests": {"status": "failed", "failed": 5},
            "prd": {"status": "failed", "critical_gaps": ["REQ-1"]},
            "quality_gates": {
                "lint": {"status": "failed"},
            },
        }

        recovery = self.orchestrator._attempt_validation_recovery(validation_results)

        self.assertIn("actions_taken", recovery)
        self.assertIn("strategy", recovery)
        self.assertIn("logged_issues_for_refinement", recovery.get("actions_taken", []))


class TestValidationPhaseIntegration(unittest.TestCase):
    """Integration tests for validation phase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "test-validation-integration-456"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        import json
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Integration test feature",
            "status": SessionStatus.IMPLEMENTING.value,
            "current_phase": "validate",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "integration-test",
                "commit": "def456",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

        # Mock git commands
        self.git_patcher = patch("subprocess.run")
        self.mock_run = self.git_patcher.start()
        self.mock_run.return_value = MagicMock(stdout="integration-test\n", returncode=0)

        # Create orchestrator
        self.orchestrator = MaestroOrchestrator(self.project_root)
        self.orchestrator.session_id = self.session_id

        # Create test PRD
        self.prd_path = self.project_root / "integration-test-prd.md"
        self.prd_path.write_text("""---
title: Integration Test PRD
status: approved
requirements:
  - id: INT-1
    title: Integration requirement
    description: Test integration
    category: testing
    priority: P0
---

# Integration Test PRD
""")

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    @patch.object(MaestroOrchestrator, '_detect_test_framework')
    @patch.object(MaestroOrchestrator, '_execute_tests')
    @patch.object(MaestroOrchestrator, '_validate_prd_requirements')
    @patch.object(MaestroOrchestrator, '_execute_quality_gates')
    @patch.object(CheckpointManager, 'create_checkpoint')
    def test_validation_phase_decision_logging(
        self,
        mock_create_checkpoint,
        mock_execute_gates,
        mock_validate_prd,
        mock_execute_tests,
        mock_detect_framework,
        mock_subprocess,
    ):
        """Test that validation phase logs decisions properly."""
        # Setup mocks
        mock_detect_framework.return_value = "pytest"
        mock_execute_tests.return_value = {
            "success": True,
            "passed": 50,
            "failed": 0,
            "total": 50,
            "coverage": 75.0,
            "failures": [],
        }
        mock_validate_prd.return_value = {
            "total_requirements": 1,
            "validated_requirements": 1,
            "coverage_percentage": 100.0,
            "critical_gaps": [],
            "all_requirements_met": True,
        }
        mock_execute_gates.return_value = {
            "lint": {"status": "passed", "message": "Clean"},
        }
        mock_create_checkpoint.return_value = MagicMock(commit_sha="xyz789", checkpoint_id="chk-xyz")

        # Execute validation phase
        self.orchestrator._phase_validation(self.prd_path)

        # Verify decisions were logged
        decisions = self.orchestrator.decision_logger.get_decisions()
        decision_types = [d.decision_type for d in decisions]

        self.assertIn("test_execution", decision_types)
        self.assertIn("prd_validation", decision_types)
        self.assertIn("quality_gates", decision_types)

    @patch("subprocess.run")
    @patch.object(MaestroOrchestrator, '_detect_test_framework')
    @patch.object(MaestroOrchestrator, '_execute_tests')
    @patch.object(MaestroOrchestrator, '_validate_prd_requirements')
    @patch.object(MaestroOrchestrator, '_execute_quality_gates')
    @patch.object(CheckpointManager, 'create_checkpoint')
    def test_validation_phase_checkpoint_creation(
        self,
        mock_create_checkpoint,
        mock_execute_gates,
        mock_validate_prd,
        mock_execute_tests,
        mock_detect_framework,
        mock_subprocess,
    ):
        """Test that validation phase creates proper checkpoints."""
        # Setup mocks
        mock_detect_framework.return_value = "pytest"
        mock_execute_tests.return_value = {
            "success": True,
            "passed": 30,
            "failed": 0,
            "total": 30,
            "coverage": 90.0,
            "failures": [],
        }
        mock_validate_prd.return_value = {
            "total_requirements": 1,
            "validated_requirements": 1,
            "coverage_percentage": 100.0,
            "critical_gaps": [],
            "all_requirements_met": True,
        }
        mock_execute_gates.return_value = {}
        mock_create_checkpoint.return_value = MagicMock(commit_sha="chk123", checkpoint_id="cp-123")

        # Execute validation phase
        result = self.orchestrator._phase_validation(self.prd_path)

        # Verify checkpoint was created
        mock_create_checkpoint.assert_called_once()
        call_args = mock_create_checkpoint.call_args

        self.assertEqual(call_args[1]["session_id"], self.session_id)
        self.assertEqual(call_args[1]["phase"], CheckpointPhase.VALIDATE)
        self.assertEqual(call_args[1]["checkpoint_type"], CheckpointType.PHASE_COMPLETE)
        self.assertIn("Validation phase complete", call_args[1]["description"])

        # Verify checkpoint ID is in results
        self.assertEqual(result["checkpoint"], "cp-123")


if __name__ == "__main__":
    unittest.main()
