#!/usr/bin/env python3
"""
Tests for Report Generator
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from report_generator import (
    ReportGenerator,
    ReportFormat,
    ReportData,
    TestExecutionSummary,
    RequirementCoverageSummary,
    QualityGateSummary,
    IterationSummary,
)


class TestTestExecutionSummary(unittest.TestCase):
    """Test cases for TestExecutionSummary."""

    def test_summary_creation(self):
        """Test creating TestExecutionSummary."""
        summary = TestExecutionSummary(
            total_tests=100,
            passed_tests=95,
            failed_tests=5,
            coverage_percentage=85.0,
        )

        self.assertEqual(summary.total_tests, 100)
        self.assertEqual(summary.passed_tests, 95)

    def test_success_rate(self):
        """Test success_rate calculation."""
        summary = TestExecutionSummary(
            total_tests=100,
            passed_tests=95,
            failed_tests=5,
        )

        self.assertEqual(summary.success_rate, 95.0)

    def test_success_rate_no_tests(self):
        """Test success_rate with no tests."""
        summary = TestExecutionSummary()

        self.assertEqual(summary.success_rate, 0.0)


class TestRequirementCoverageSummary(unittest.TestCase):
    """Test cases for RequirementCoverageSummary."""

    def test_summary_creation(self):
        """Test creating RequirementCoverageSummary."""
        summary = RequirementCoverageSummary(
            total_requirements=10,
            implemented_requirements=8,
            validated_requirements=6,
            coverage_percentage=60.0,
        )

        self.assertEqual(summary.total_requirements, 10)
        self.assertEqual(summary.validated_requirements, 6)


class TestQualityGateSummary(unittest.TestCase):
    """Test cases for QualityGateSummary."""

    def test_summary_creation(self):
        """Test creating QualityGateSummary."""
        summary = QualityGateSummary(
            total_gates=3,
            passed_gates=2,
            failed_gates=1,
            average_score=75.0,
        )

        self.assertEqual(summary.total_gates, 3)
        self.assertEqual(summary.passed_gates, 2)


class TestIterationSummary(unittest.TestCase):
    """Test cases for IterationSummary."""

    def test_summary_creation(self):
        """Test creating IterationSummary."""
        summary = IterationSummary(
            total_iterations=3,
            completed_iterations=3,
            completion_criteria_met=["all_tests_passing"],
        )

        self.assertEqual(summary.total_iterations, 3)
        self.assertEqual(summary.completed_iterations, 3)


class TestReportData(unittest.TestCase):
    """Test cases for ReportData."""

    def test_overall_status_success(self):
        """Test overall_status with all passing."""
        data = ReportData(
            session_id="test-session",
            feature_request="Test feature",
            test_summary=TestExecutionSummary(
                total_tests=100,
                passed_tests=95,
                coverage_percentage=85.0,
            ),
            requirement_summary=RequirementCoverageSummary(
                total_requirements=10,
                validated_requirements=9,
                coverage_percentage=90.0,
            ),
            quality_gate_summary=QualityGateSummary(
                total_gates=3,
                passed_gates=3,
                average_score=80.0,
            ),
        )

        self.assertEqual(data.overall_status, "success")

    def test_overall_status_partial(self):
        """Test overall_status with mixed results."""
        data = ReportData(
            session_id="test-session",
            feature_request="Test feature",
            test_summary=TestExecutionSummary(
                total_tests=100,
                passed_tests=70,  # Below 80%
                coverage_percentage=60.0,
            ),
            requirement_summary=RequirementCoverageSummary(
                total_requirements=10,
                validated_requirements=9,
                coverage_percentage=90.0,
            ),
        )

        self.assertEqual(data.overall_status, "partial")

    def test_overall_status_unknown(self):
        """Test overall_status with no data."""
        data = ReportData(
            session_id="test-session",
            feature_request="Test feature",
        )

        self.assertEqual(data.overall_status, "unknown")


class TestReportGenerator(unittest.TestCase):
    """Test cases for ReportGenerator."""

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
            "status": SessionStatus.COMPLETED.value,
            "current_phase": "cleanup",
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
        from unittest.mock import patch
        self.git_patcher = patch("subprocess.run")
        self.mock_run = self.git_patcher.start()
        self.mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

        # Create generator
        self.generator = ReportGenerator(self.project_root, self.session_id)

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test ReportGenerator initialization."""
        self.assertEqual(self.generator.session_id, self.session_id)
        self.assertEqual(self.generator.project_root, self.project_root)

    def test_generate_markdown_report(self):
        """Test generating markdown report."""
        report_data = ReportData(
            session_id=self.session_id,
            feature_request="Test feature",
            test_summary=TestExecutionSummary(
                total_tests=100,
                passed_tests=95,
                failed_tests=5,
                coverage_percentage=85.0,
            ),
            requirement_summary=RequirementCoverageSummary(
                total_requirements=10,
                validated_requirements=9,
                coverage_percentage=90.0,
            ),
        )

        report = self.generator.generate_report(
            report_data=report_data,
            output_format=ReportFormat.MARKDOWN,
        )

        self.assertIn("Implementation Report", report)
        self.assertIn("Test Results", report)
        self.assertIn("95", report)  # passed tests
        self.assertIn("85.0%", report)  # coverage

    def test_generate_json_report(self):
        """Test generating JSON report."""
        report_data = ReportData(
            session_id=self.session_id,
            feature_request="Test feature",
            test_summary=TestExecutionSummary(
                total_tests=100,
                passed_tests=95,
            ),
        )

        report = self.generator.generate_report(
            report_data=report_data,
            output_format=ReportFormat.JSON,
        )

        import json
        parsed = json.loads(report)

        self.assertEqual(parsed["session_id"], self.session_id)
        self.assertEqual(parsed["feature_request"], "Test feature")
        self.assertIn("test_summary", parsed)

    def test_generate_html_report(self):
        """Test generating HTML report."""
        report_data = ReportData(
            session_id=self.session_id,
            feature_request="Test feature",
        )

        report = self.generator.generate_report(
            report_data=report_data,
            output_format=ReportFormat.HTML,
        )

        self.assertIn("<!DOCTYPE html>", report)
        self.assertIn("<title>", report)
        self.assertIn("</html>", report)

    def test_generate_report_to_file(self):
        """Test generating report to file."""
        report_data = ReportData(
            session_id=self.session_id,
            feature_request="Test feature",
        )

        output_path = self.project_root / "reports" / "test-report.md"

        report = self.generator.generate_report(
            report_data=report_data,
            output_format=ReportFormat.MARKDOWN,
            output_path=output_path,
        )

        self.assertTrue(output_path.exists())
        self.assertIn("Implementation Report", report)

    def test_collect_report_data(self):
        """Test collecting report data."""
        # Create some validation results
        validation_results = {
            "gates": [
                {
                    "gate_name": "test_execution",
                    "details": {
                        "total": 100,
                        "passed": 95,
                        "failed": 5,
                        "coverage": 85.0,
                    },
                }
            ]
        }

        report_data = self.generator.collect_report_data(
            validation_results=validation_results,
        )

        self.assertEqual(report_data.session_id, self.session_id)
        self.assertEqual(report_data.feature_request, "Test feature")
        self.assertIsNotNone(report_data.test_summary)
        self.assertEqual(report_data.test_summary.total_tests, 100)

    def test_get_status_emoji(self):
        """Test status emoji generation."""
        self.assertEqual(self.generator._get_status_emoji("success"), "✅")
        self.assertEqual(self.generator._get_status_emoji("partial"), "🟡")
        self.assertEqual(self.generator._get_status_emoji("failed"), "❌")
        self.assertEqual(self.generator._get_status_emoji("unknown"), "❓")

    def test_generate_executive_summary(self):
        """Test executive summary generation."""
        report_data = ReportData(
            session_id=self.session_id,
            feature_request="Test feature",
            test_summary=TestExecutionSummary(
                total_tests=100,
                passed_tests=95,
                coverage_percentage=85.0,
            ),
            requirement_summary=RequirementCoverageSummary(
                total_requirements=10,
                validated_requirements=9,
                coverage_percentage=90.0,
            ),
            quality_gate_summary=QualityGateSummary(
                total_gates=3,
                passed_gates=3,
                average_score=85.0,
            ),
        )

        summary = self.generator._generate_executive_summary(report_data)

        self.assertIn("95.0%", summary)  # test success rate
        self.assertIn("90.0%", summary)  # requirement coverage
        self.assertIn("85.0", summary)  # quality gate score

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        test_summary = TestExecutionSummary(
            total_tests=100,
            passed_tests=70,  # Below 80%
            coverage_percentage=50.0,  # Below 70%
        )

        requirement_summary = RequirementCoverageSummary(
            total_requirements=10,
            validated_requirements=7,
            coverage_percentage=70.0,  # Below 90%
            critical_gaps=["REQ-1", "REQ-2"],
        )

        quality_gate_summary = QualityGateSummary(
            total_gates=3,
            passed_gates=2,
            failed_gates=1,
            average_score=60.0,  # Below 70
        )

        recommendations = self.generator._generate_recommendations(
            test_summary, requirement_summary, quality_gate_summary
        )

        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any("80%" in r for r in recommendations))
        self.assertTrue(any("70%" in r for r in recommendations))

    def test_parse_test_results(self):
        """Test parsing test results."""
        test_data = {
            "gate_name": "test_execution",
            "details": {
                "total": 100,
                "passed": 95,
                "failed": 5,
                "coverage": 85.0,
            },
        }

        summary = self.generator._parse_test_results(test_data)

        self.assertEqual(summary.total_tests, 100)
        self.assertEqual(summary.passed_tests, 95)
        self.assertEqual(summary.coverage_percentage, 85.0)

    def test_parse_requirement_results(self):
        """Test parsing requirement results."""
        req_data = {
            "total_requirements": 10,
            "implemented_requirements": 9,
            "validated_requirements": 8,
            "coverage_percentage": 80.0,
            "missing_requirements": ["REQ-9", "REQ-10"],
        }

        summary = self.generator._parse_requirement_results(req_data)

        self.assertEqual(summary.total_requirements, 10)
        self.assertEqual(summary.validated_requirements, 8)
        self.assertEqual(len(summary.missing_requirements), 2)


class TestReportFormat(unittest.TestCase):
    """Test cases for ReportFormat enum."""

    def test_format_values(self):
        """Test ReportFormat enum values."""
        self.assertEqual(ReportFormat.MARKDOWN.value, "markdown")
        self.assertEqual(ReportFormat.JSON.value, "json")
        self.assertEqual(ReportFormat.HTML.value, "html")


if __name__ == "__main__":
    unittest.main()
