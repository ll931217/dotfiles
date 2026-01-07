#!/usr/bin/env python3
"""
Tests for Quality Gate Runner
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from quality_gate_runner import (
    QualityGateRunner,
    QualityGate,
    QualityGateStatus,
    QualityGateResult,
    QualityGateConfig,
    LintingGate,
    TypeCheckingGate,
    SecurityGate,
)


class MockQualityGate(QualityGate):
    """Mock quality gate for testing."""

    def __init__(self, name: str, status: QualityGateStatus, score: float = 100.0):
        super().__init__(name)
        self.mock_status = status
        self.mock_score = score

    def _execute_default(self, project_root: Path) -> QualityGateResult:
        return QualityGateResult(
            gate_name=self.name,
            status=self.mock_status,
            message="Mock result",
            score=self.mock_score,
        )


class TestQualityGateResult(unittest.TestCase):
    """Test cases for QualityGateResult."""

    def test_quality_gate_result_creation(self):
        """Test creating QualityGateResult."""
        result = QualityGateResult(
            gate_name="test_gate",
            status=QualityGateStatus.PASSED,
            message="Test passed",
            score=95.0,
        )

        self.assertEqual(result.gate_name, "test_gate")
        self.assertEqual(result.status, QualityGateStatus.PASSED)
        self.assertEqual(result.score, 95.0)

    def test_to_dict(self):
        """Test converting QualityGateResult to dict."""
        result = QualityGateResult(
            gate_name="test_gate",
            status=QualityGateStatus.PASSED,
            message="Test passed",
            execution_time=1.5,
            score=95.0,
        )

        data = result.to_dict()

        self.assertEqual(data["gate_name"], "test_gate")
        self.assertEqual(data["status"], "passed")
        self.assertEqual(data["score"], 95.0)


class TestQualityGateConfig(unittest.TestCase):
    """Test cases for QualityGateConfig."""

    def test_config_creation(self):
        """Test creating QualityGateConfig."""
        config = QualityGateConfig(
            name="test_config",
            enabled=True,
            required=True,
            threshold=80.0,
        )

        self.assertEqual(config.name, "test_config")
        self.assertTrue(config.enabled)
        self.assertTrue(config.required)
        self.assertEqual(config.threshold, 80.0)


class TestLintingGate(unittest.TestCase):
    """Test cases for LintingGate."""

    def setUp(self):
        """Set up test fixtures."""
        self.gate = LintingGate()

    def test_gate_initialization(self):
        """Test LintingGate initialization."""
        self.assertEqual(self.gate.name, "linting")

    def test_execute_disabled(self):
        """Test executing disabled gate."""
        config = QualityGateConfig(name="linting", enabled=False)
        gate = LintingGate(config)

        result = gate.execute(Path.cwd())

        self.assertEqual(result.status, QualityGateStatus.SKIPPED)
        self.assertIn("disabled", result.message.lower())

    @patch("subprocess.run")
    def test_try_ruff_success(self, mock_run):
        """Test ruff with no issues."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[]",
            stderr="",
        )

        result = self.gate._try_ruff(Path.cwd())

        self.assertIsNotNone(result)
        self.assertTrue(result["passed"])

    @patch("subprocess.run")
    def test_try_ruff_with_issues(self, mock_run):
        """Test ruff with linting issues."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='[{"location": "test.py:1", "message": "Unused import"}]',
            stderr="",
        )

        result = self.gate._try_ruff(Path.cwd())

        self.assertIsNotNone(result)
        self.assertFalse(result["passed"])


class TestTypeCheckingGate(unittest.TestCase):
    """Test cases for TypeCheckingGate."""

    def setUp(self):
        """Set up test fixtures."""
        self.gate = TypeCheckingGate()

    def test_gate_initialization(self):
        """Test TypeCheckingGate initialization."""
        self.assertEqual(self.gate.name, "typecheck")

    @patch("subprocess.run")
    def test_try_mypy_success(self, mock_run):
        """Test mypy with no type errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "mypy.ini").write_text("[mypy]\n")

            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Success: no issues found",
                stderr="",
            )

            result = self.gate._try_mypy(temp_path)

            self.assertIsNotNone(result)
            self.assertTrue(result["passed"])

    @patch("subprocess.run")
    def test_try_tsc_success(self, mock_run):
        """Test TypeScript compiler with no errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "tsconfig.json").write_text("{}")

            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            )

            result = self.gate._try_tsc(temp_path)

            self.assertIsNotNone(result)
            self.assertTrue(result["passed"])


class TestSecurityGate(unittest.TestCase):
    """Test cases for SecurityGate."""

    def setUp(self):
        """Set up test fixtures."""
        self.gate = SecurityGate()

    def test_gate_initialization(self):
        """Test SecurityGate initialization."""
        self.assertEqual(self.gate.name, "security")

    @patch("subprocess.run")
    def test_try_bandit_no_issues(self, mock_run):
        """Test bandit with no security issues."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"results": []}',
            stderr="",
        )

        result = self.gate._try_bandit(Path.cwd())

        self.assertIsNotNone(result)
        self.assertTrue(result["passed"])

    @patch("subprocess.run")
    def test_try_bandit_with_issues(self, mock_run):
        """Test bandit with security issues."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='{"results": [{"issue_severity": "HIGH", "issue_text": "Test issue"}]}',
            stderr="",
        )

        result = self.gate._try_bandit(Path.cwd())

        self.assertIsNotNone(result)
        self.assertFalse(result["passed"])
        self.assertIn("high severity", result["message"].lower())


class TestQualityGateRunner(unittest.TestCase):
    """Test cases for QualityGateRunner."""

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
        import json

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
        """Test QualityGateRunner initialization."""
        runner = QualityGateRunner(self.project_root, self.session_id)

        self.assertEqual(runner.session_id, self.session_id)
        self.assertEqual(len(runner.gates), 3)  # Default gates

    def test_register_custom_gate(self):
        """Test registering a custom quality gate."""
        runner = QualityGateRunner(self.project_root, self.session_id)

        initial_count = len(runner.gates)

        custom_gate = MockQualityGate("custom", QualityGateStatus.PASSED, 95.0)
        runner.register_gate(custom_gate)

        self.assertEqual(len(runner.gates), initial_count + 1)
        self.assertIn(custom_gate, runner.gates)

    def test_execute_quality_gates_all_passed(self):
        """Test executing quality gates when all pass."""
        # Create mock gates
        mock_gates = [
            MockQualityGate("gate1", QualityGateStatus.PASSED, 100.0),
            MockQualityGate("gate2", QualityGateStatus.PASSED, 90.0),
            MockQualityGate("gate3", QualityGateStatus.PASSED, 95.0),
        ]

        runner = QualityGateRunner(self.project_root, self.session_id)
        results = runner.execute_quality_gates(custom_gates=mock_gates)

        self.assertEqual(len(results["gates"]), 3)
        self.assertEqual(results["summary"]["overall_status"], "passed")
        self.assertEqual(results["summary"]["passed"], 3)
        self.assertEqual(results["summary"]["failed"], 0)
        self.assertAlmostEqual(results["summary"]["average_score"], 95.0, places=1)

    def test_execute_quality_gates_with_failure(self):
        """Test executing quality gates when one fails."""
        mock_gates = [
            MockQualityGate("gate1", QualityGateStatus.PASSED, 100.0),
            MockQualityGate("gate2", QualityGateStatus.FAILED, 0.0),
            MockQualityGate("gate3", QualityGateStatus.PASSED, 90.0),
        ]

        runner = QualityGateRunner(self.project_root, self.session_id)
        results = runner.execute_quality_gates(custom_gates=mock_gates)

        self.assertEqual(results["summary"]["overall_status"], "failed")
        self.assertEqual(results["summary"]["passed"], 2)
        self.assertEqual(results["summary"]["failed"], 1)
        self.assertAlmostEqual(results["summary"]["average_score"], 190.0 / 3, places=1)

    def test_calculate_summary(self):
        """Test summary calculation."""
        runner = QualityGateRunner(self.project_root, self.session_id)

        gate_results = [
            QualityGateResult(
                gate_name="gate1",
                status=QualityGateStatus.PASSED,
                message="Passed",
                score=100.0,
            ),
            QualityGateResult(
                gate_name="gate2",
                status=QualityGateStatus.FAILED,
                message="Failed",
                score=0.0,
            ),
            QualityGateResult(
                gate_name="gate3",
                status=QualityGateStatus.WARNING,
                message="Warning",
                score=70.0,
            ),
        ]

        summary = runner._calculate_summary(gate_results)

        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["warnings"], 1)
        self.assertAlmostEqual(summary["average_score"], 170.0 / 3, places=1)


class TestQualityGateStatus(unittest.TestCase):
    """Test cases for QualityGateStatus enum."""

    def test_status_values(self):
        """Test QualityGateStatus enum values."""
        self.assertEqual(QualityGateStatus.PASSED.value, "passed")
        self.assertEqual(QualityGateStatus.FAILED.value, "failed")
        self.assertEqual(QualityGateStatus.SKIPPED.value, "skipped")
        self.assertEqual(QualityGateStatus.WARNING.value, "warning")


if __name__ == "__main__":
    unittest.main()
