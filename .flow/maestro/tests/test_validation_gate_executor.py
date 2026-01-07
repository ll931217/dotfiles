#!/usr/bin/env python3
"""
Tests for Validation Gate Executor
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validation_gate_executor import (
    ValidationGateExecutor,
    ValidationGate,
    ValidationGateStatus,
    GateResult,
    TestResults,
    TestExecutionGate,
    QualityGateChecker,
)


class MockValidationGate(ValidationGate):
    """Mock validation gate for testing."""

    def __init__(self, name: str, status: ValidationGateStatus, message: str = ""):
        super().__init__(name, "Mock gate")
        self.mock_status = status
        self.mock_message = message

    def execute(self, context):
        return GateResult(
            gate_name=self.name,
            status=self.mock_status,
            message=self.mock_message,
        )


class TestGateResult(unittest.TestCase):
    """Test cases for GateResult."""

    def test_gate_result_creation(self):
        """Test creating GateResult."""
        result = GateResult(
            gate_name="test_gate",
            status=ValidationGateStatus.PASSED,
            message="Test passed",
        )

        self.assertEqual(result.gate_name, "test_gate")
        self.assertEqual(result.status, ValidationGateStatus.PASSED)
        self.assertEqual(result.message, "Test passed")

    def test_to_dict(self):
        """Test converting GateResult to dict."""
        result = GateResult(
            gate_name="test_gate",
            status=ValidationGateStatus.PASSED,
            message="Test passed",
            details={"key": "value"},
            execution_time=1.5,
        )

        data = result.to_dict()

        self.assertEqual(data["gate_name"], "test_gate")
        self.assertEqual(data["status"], "passed")
        self.assertEqual(data["message"], "Test passed")
        self.assertEqual(data["details"]["key"], "value")
        self.assertEqual(data["execution_time"], 1.5)


class TestTestResults(unittest.TestCase):
    """Test cases for TestResults."""

    def test_test_results_creation(self):
        """Test creating TestResults."""
        results = TestResults(
            passed=10,
            failed=2,
            skipped=1,
            total=13,
            coverage=85.5,
        )

        self.assertEqual(results.passed, 10)
        self.assertEqual(results.failed, 2)
        self.assertEqual(results.total, 13)
        self.assertEqual(results.coverage, 85.5)

    def test_success_property(self):
        """Test TestResults success property."""
        # All tests pass
        results = TestResults(passed=10, failed=0, total=10)
        self.assertTrue(results.success)

        # Some tests fail
        results = TestResults(passed=8, failed=2, total=10)
        self.assertFalse(results.success)

        # No tests run
        results = TestResults(passed=0, failed=0, total=0)
        self.assertFalse(results.success)

    def test_to_dict(self):
        """Test converting TestResults to dict."""
        results = TestResults(
            passed=10,
            failed=2,
            skipped=1,
            total=13,
            coverage=85.5,
            failures=["test_foo", "test_bar"],
        )

        data = results.to_dict()

        self.assertEqual(data["passed"], 10)
        self.assertEqual(data["failed"], 2)
        self.assertEqual(data["coverage"], 85.5)
        self.assertEqual(len(data["failures"]), 2)


class TestTestExecutionGate(unittest.TestCase):
    """Test cases for TestExecutionGate."""

    def setUp(self):
        """Set up test fixtures."""
        self.gate = TestExecutionGate()

    def test_gate_initialization(self):
        """Test TestExecutionGate initialization."""
        self.assertEqual(self.gate.name, "test_execution")
        self.assertIn("test", self.gate.description.lower())

    @patch("subprocess.run")
    def test_detect_pytest_framework(self, mock_run):
        """Test detecting pytest framework."""
        # Create temp directory with pytest.ini
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "pytest.ini").write_text("[pytest]\n")

            framework = self.gate._detect_test_framework(temp_path)

            self.assertEqual(framework, "pytest")

    @patch("subprocess.run")
    def test_detect_unittest_framework(self, mock_run):
        """Test detecting unittest framework."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tests_dir = temp_path / "tests"
            tests_dir.mkdir()

            # Create a simple unittest file
            (tests_dir / "test_example.py").write_text("""
import unittest

class TestExample(unittest.TestCase):
    def test_example(self):
        self.assertTrue(True)
""")

            framework = self.gate._detect_test_framework(temp_path)

            self.assertEqual(framework, "unittest")

    @patch("subprocess.run")
    def test_detect_jest_framework(self, mock_run):
        """Test detecting Jest framework."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create package.json with jest
            package_json = {
                "devDependencies": {
                    "jest": "^29.0.0",
                },
            }
            (temp_path / "package.json").write_text(json.dumps(package_json))

            framework = self.gate._detect_test_framework(temp_path)

            self.assertEqual(framework, "jest")

    def test_detect_no_framework(self):
        """Test detecting no framework."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Empty directory

            framework = self.gate._detect_test_framework(temp_path)

            self.assertIsNone(framework)


class TestQualityGateChecker(unittest.TestCase):
    """Test cases for QualityGateChecker."""

    def setUp(self):
        """Set up test fixtures."""
        self.gate = QualityGateChecker()

    def test_gate_initialization(self):
        """Test QualityGateChecker initialization."""
        self.assertEqual(self.gate.name, "quality_gates")
        self.assertIn("quality", self.gate.description.lower())

    @patch("subprocess.run")
    def test_check_linting_flake8(self, mock_run):
        """Test linting check with flake8."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".flake8").write_text("[flake8]\n")

            result = self.gate._check_linting(temp_path)

            self.assertTrue(result["passed"])

    @patch("subprocess.run")
    def test_check_linting_failure(self, mock_run):
        """Test linting check failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="E501 line too long",
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "setup.cfg").write_text("[flake8]\n")

            result = self.gate._check_linting(temp_path)

            self.assertFalse(result["passed"])

    @patch("subprocess.run")
    def test_check_linting_not_configured(self, mock_run):
        """Test linting check when not configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # No linter configuration

            result = self.gate._check_linting(temp_path)

            self.assertTrue(result["passed"])
            self.assertIn("No linter configured", result["message"])

    @patch("subprocess.run")
    def test_check_typecheck_mypy(self, mock_run):
        """Test type checking with mypy."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success: no issues found",
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "mypy.ini").write_text("[mypy]\n")

            result = self.gate._check_typecheck(temp_path)

            self.assertTrue(result["passed"])

    @patch("subprocess.run")
    def test_check_typecheck_typescript(self, mock_run):
        """Test type checking with TypeScript."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "tsconfig.json").write_text("{}")

            result = self.gate._check_typecheck(temp_path)

            self.assertTrue(result["passed"])

    @patch("subprocess.run")
    def test_check_security_bandit(self, mock_run):
        """Test security check with bandit."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            result = self.gate._check_security(temp_path)

            self.assertTrue(result["passed"])


class TestValidationGateExecutor(unittest.TestCase):
    """Test cases for ValidationGateExecutor."""

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
        from session_manager import SessionStatus

        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature",
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
        """Test ValidationGateExecutor initialization."""
        executor = ValidationGateExecutor(self.project_root, self.session_id)

        self.assertEqual(executor.session_id, self.session_id)
        self.assertEqual(len(executor.gates), 2)  # Default gates

    def test_register_custom_gate(self):
        """Test registering a custom validation gate."""
        executor = ValidationGateExecutor(self.project_root, self.session_id)

        initial_count = len(executor.gates)

        custom_gate = MockValidationGate("custom", ValidationGateStatus.PASSED, "Custom test")
        executor.register_gate(custom_gate)

        self.assertEqual(len(executor.gates), initial_count + 1)
        self.assertIn(custom_gate, executor.gates)

    @patch.object(TestExecutionGate, "execute")
    @patch.object(QualityGateChecker, "execute")
    def test_execute_validation_gates_all_passed(self, mock_quality, mock_test):
        """Test executing validation gates when all pass."""
        # Setup mocks
        mock_test.return_value = GateResult(
            gate_name="test_execution",
            status=ValidationGateStatus.PASSED,
            message="Tests passed",
        )
        mock_quality.return_value = GateResult(
            gate_name="quality_gates",
            status=ValidationGateStatus.PASSED,
            message="Quality gates passed",
        )

        executor = ValidationGateExecutor(self.project_root, self.session_id)
        results = executor.execute_validation_gates()

        self.assertEqual(len(results["gates"]), 2)
        self.assertEqual(results["summary"]["overall_status"], "passed")
        self.assertEqual(results["summary"]["gates_passed"], 2)
        self.assertEqual(results["summary"]["gates_failed"], 0)

    @patch.object(TestExecutionGate, "execute")
    @patch.object(QualityGateChecker, "execute")
    def test_execute_validation_gates_with_failure(self, mock_quality, mock_test):
        """Test executing validation gates when one fails."""
        # Setup mocks
        mock_test.return_value = GateResult(
            gate_name="test_execution",
            status=ValidationGateStatus.FAILED,
            message="Tests failed",
        )
        mock_quality.return_value = GateResult(
            gate_name="quality_gates",
            status=ValidationGateStatus.PASSED,
            message="Quality gates passed",
        )

        executor = ValidationGateExecutor(self.project_root, self.session_id)
        results = executor.execute_validation_gates()

        self.assertEqual(results["summary"]["overall_status"], "failed")
        self.assertEqual(results["summary"]["gates_passed"], 1)
        self.assertEqual(results["summary"]["gates_failed"], 1)

    def test_calculate_summary(self):
        """Test summary calculation."""
        executor = ValidationGateExecutor(self.project_root, self.session_id)

        gate_results = [
            GateResult(
                gate_name="gate1",
                status=ValidationGateStatus.PASSED,
                message="Passed",
                execution_time=1.0,
            ),
            GateResult(
                gate_name="gate2",
                status=ValidationGateStatus.FAILED,
                message="Failed",
                execution_time=2.0,
            ),
            GateResult(
                gate_name="gate3",
                status=ValidationGateStatus.SKIPPED,
                message="Skipped",
                execution_time=0.0,
            ),
        ]

        summary = executor._calculate_summary(gate_results)

        self.assertEqual(summary["overall_status"], "failed")
        self.assertEqual(summary["gates_passed"], 1)
        self.assertEqual(summary["gates_failed"], 1)
        self.assertEqual(summary["gates_skipped"], 1)
        self.assertEqual(summary["total_execution_time"], 3.0)


class TestValidationGateStatus(unittest.TestCase):
    """Test cases for ValidationGateStatus enum."""

    def test_status_values(self):
        """Test ValidationGateStatus enum values."""
        self.assertEqual(ValidationGateStatus.PENDING.value, "pending")
        self.assertEqual(ValidationGateStatus.RUNNING.value, "running")
        self.assertEqual(ValidationGateStatus.PASSED.value, "passed")
        self.assertEqual(ValidationGateStatus.FAILED.value, "failed")
        self.assertEqual(ValidationGateStatus.SKIPPED.value, "skipped")


if __name__ == "__main__":
    unittest.main()
