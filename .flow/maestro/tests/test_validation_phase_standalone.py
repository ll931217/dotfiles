#!/usr/bin/env python3
"""
Standalone unit tests for Validation Phase Implementation

Tests the validation functionality without requiring full orchestrator initialization.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import logging
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from orchestrator_validation_implementation import ValidationPhaseImplementation


class TestValidationPhaseImplementation(unittest.TestCase):
    """Test cases for ValidationPhaseImplementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create logger
        self.logger = logging.getLogger("test_validation")
        self.logger.setLevel(logging.INFO)

        # Create session ID
        self.session_id = "test-session-123"

        # Create implementation instance
        self.impl = ValidationPhaseImplementation(
            logger=self.logger,
            project_root=self.project_root,
            session_id=self.session_id,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_detect_test_framework_pytest(self):
        """Test detection of pytest framework."""
        # Create pytest.ini
        (self.project_root / "pytest.ini").write_text("[pytest]\n")

        framework = self.impl.detect_test_framework()

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

        framework = self.impl.detect_test_framework()

        self.assertEqual(framework, "unittest")

    def test_detect_test_framework_none(self):
        """Test detection when no framework is present."""
        framework = self.impl.detect_test_framework()

        self.assertIsNone(framework)

    @patch("subprocess.run")
    def test_run_pytest_success(self, mock_run):
        """Test successful pytest execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="130 passed in 5.2s\n",
            stderr="",
        )

        result = self.impl._run_pytest()

        self.assertTrue(result["success"])
        self.assertEqual(result["passed"], 130)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["total"], 130)

    @patch("subprocess.run")
    def test_run_pytest_with_failures(self, mock_run):
        """Test pytest execution with failures."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="127 passed, 3 failed\nFAILED test_module.py::test_function\n",
            stderr="",
        )

        result = self.impl._run_pytest()

        self.assertFalse(result["success"])
        self.assertEqual(result["passed"], 127)
        self.assertEqual(result["failed"], 3)
        self.assertEqual(result["total"], 130)
        self.assertTrue(len(result["failures"]) > 0)

    @patch("subprocess.run")
    def test_run_unittest_success(self, mock_run):
        """Test successful unittest execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Ran 50 tests in 2.1s\nOK\n",
            stderr="",
        )

        result = self.impl._run_unittest()

        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 50)
        self.assertEqual(result["passed"], 50)
        self.assertEqual(result["failed"], 0)

    @patch("subprocess.run")
    def test_check_linting_passed(self, mock_run):
        """Test linting check when passed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        result = self.impl._check_linting()

        self.assertEqual(result["status"], "passed")
        self.assertIn("No linting issues", result["message"])

    @patch("subprocess.run")
    def test_check_linting_failed(self, mock_run):
        """Test linting check when failed."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="file.py:1:1: E401 multiple imports on one line\n",
            stderr="",
        )

        result = self.impl._check_linting()

        self.assertEqual(result["status"], "failed")
        self.assertIn("linting issues", result["message"])

    @patch("subprocess.run")
    def test_check_typecheck_passed(self, mock_run):
        """Test type checking when passed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success: no issues found\n",
            stderr="",
        )

        result = self.impl._check_typecheck()

        self.assertEqual(result["status"], "passed")
        self.assertIn("No type errors", result["message"])

    @patch("subprocess.run")
    def test_check_typecheck_failed(self, mock_run):
        """Test type checking when failed."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="file.py:5: error: incompatible return value type\n",
            stderr="",
        )

        result = self.impl._check_typecheck()

        self.assertEqual(result["status"], "failed")
        self.assertIn("type errors", result["message"])

    @patch("subprocess.run")
    def test_check_security_passed(self, mock_run):
        """Test security check when passed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"results": []}\n',
            stderr="",
        )

        result = self.impl._check_security()

        self.assertEqual(result["status"], "passed")
        self.assertIn("No security issues", result["message"])

    @patch("subprocess.run")
    def test_execute_quality_gates(self, mock_run):
        """Test execution of multiple quality gates."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        gate_names = ["lint", "typecheck", "security"]
        results = self.impl.execute_quality_gates(gate_names)

        self.assertEqual(len(results), 3)
        self.assertIn("lint", results)
        self.assertIn("typecheck", results)
        self.assertIn("security", results)
        self.assertEqual(results["lint"]["status"], "passed")
        self.assertEqual(results["typecheck"]["status"], "passed")
        self.assertEqual(results["security"]["status"], "passed")

    @patch("subprocess.run")
    def test_validate_prd_requirements(self, mock_run):
        """Test PRD requirement validation."""
        mock_run.return_value = MagicMock(returncode=0)

        # Create a test PRD
        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text("""---
title: Test PRD
requirements:
  - id: REQ-1
    title: First requirement
    description: Test
    category: core
    priority: P0
---
# Test PRD
""")

        result = self.impl.validate_prd_requirements(prd_path)

        self.assertEqual(result["total_requirements"], 1)
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

        report = self.impl.generate_validation_report(validation_results)

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

        self.assertTrue(self.impl.is_validation_successful(validation_results))

    def test_is_validation_successful_test_failed(self):
        """Test validation success check when tests failed."""
        validation_results = {
            "tests": {"status": "failed"},
            "prd": {"status": "passed", "critical_gaps": []},
            "quality_gates": {},
        }

        self.assertFalse(self.impl.is_validation_successful(validation_results))

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

        self.assertFalse(self.impl.is_validation_successful(validation_results))

    def test_is_validation_successful_quality_gate_failed(self):
        """Test validation success check when quality gate failed."""
        validation_results = {
            "tests": {"status": "passed"},
            "prd": {"status": "passed", "critical_gaps": []},
            "quality_gates": {
                "lint": {"status": "failed"},
            },
        }

        self.assertFalse(self.impl.is_validation_successful(validation_results))


class TestValidationPhaseIntegration(unittest.TestCase):
    """Integration tests for validation phase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create logger
        self.logger = logging.getLogger("test_integration")
        self.logger.setLevel(logging.INFO)

        # Create session ID
        self.session_id = "test-integration-456"

        # Create implementation instance
        self.impl = ValidationPhaseImplementation(
            logger=self.logger,
            project_root=self.project_root,
            session_id=self.session_id,
        )

        # Create test PRD
        self.prd_path = self.project_root / "integration-test-prd.md"
        self.prd_path.write_text("""---
title: Integration Test PRD
requirements:
  - id: INT-1
    title: Integration requirement
    description: Test
    category: testing
    priority: P0
---
# Integration Test PRD
""")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_full_validation_workflow(self, mock_run):
        """Test complete validation workflow."""
        # Mock all subprocess calls
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        # Step 1: Detect framework
        (self.project_root / "pytest.ini").write_text("[pytest]\n")
        framework = self.impl.detect_test_framework()
        self.assertEqual(framework, "pytest")

        # Step 2: Execute tests
        test_result = self.impl.execute_tests(framework)
        self.assertTrue(test_result["success"])

        # Step 3: Validate PRD
        prd_result = self.impl.validate_prd_requirements(self.prd_path)
        self.assertEqual(prd_result["total_requirements"], 1)

        # Step 4: Execute quality gates
        gate_results = self.impl.execute_quality_gates(["lint", "typecheck"])
        self.assertEqual(gate_results["lint"]["status"], "passed")
        self.assertEqual(gate_results["typecheck"]["status"], "passed")

        # Step 5: Check overall success
        validation_results = {
            "tests": test_result,
            "prd": prd_result,
            "quality_gates": gate_results,
        }
        is_successful = self.impl.is_validation_successful(validation_results)
        self.assertTrue(is_successful)

        # Step 6: Generate report
        report = self.impl.generate_validation_report(validation_results)
        self.assertIn("Validation Report", report)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
