#!/usr/bin/env python3
"""
Maestro Report Generator - Generates comprehensive implementation reports

Consolidates all validation results into comprehensive reports:
- Test execution results
- PRD requirement coverage
- Quality gate results
- Iteration progress
- Decision logs
- Changelog and recommendations

Generates markdown reports for human review and machine-readable JSON.
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
sys.path.insert(0, str(maestro_root / "scripts"))
sys.path.insert(0, str(maestro_root / "decision-engine" / "scripts"))

from session_manager import SessionManager
from decision_logger import DecisionLogger


class ReportFormat(Enum):
    """Output format for reports."""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


@dataclass
class TestExecutionSummary:
    """Summary of test execution results."""

    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    coverage_percentage: float = 0.0
    failures: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0.0


@dataclass
class RequirementCoverageSummary:
    """Summary of PRD requirement coverage."""

    total_requirements: int = 0
    implemented_requirements: int = 0
    validated_requirements: int = 0
    coverage_percentage: float = 0.0
    missing_requirements: List[str] = field(default_factory=list)
    critical_gaps: List[str] = field(default_factory=list)


@dataclass
class QualityGateSummary:
    """Summary of quality gate results."""

    total_gates: int = 0
    passed_gates: int = 0
    failed_gates: int = 0
    skipped_gates: int = 0
    average_score: float = 0.0
    gate_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IterationSummary:
    """Summary of refinement iterations."""

    total_iterations: int = 0
    completed_iterations: int = 0
    completion_criteria_met: List[str] = field(default_factory=list)
    improvements_made: List[str] = field(default_factory=list)


@dataclass
class ReportData:
    """Consolidated data for report generation."""

    session_id: str
    feature_request: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    test_summary: Optional[TestExecutionSummary] = None
    requirement_summary: Optional[RequirementCoverageSummary] = None
    quality_gate_summary: Optional[QualityGateSummary] = None
    iteration_summary: Optional[IterationSummary] = None
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        """Determine overall implementation status."""
        checks = []

        if self.test_summary:
            checks.append(self.test_summary.success_rate >= 80)

        if self.requirement_summary:
            checks.append(self.requirement_summary.coverage_percentage >= 90)

        if self.quality_gate_summary:
            checks.append(self.quality_gate_summary.average_score >= 70)

        if not checks:
            return "unknown"

        return "success" if all(checks) else "partial"


class ReportGenerator:
    """
    Generates comprehensive implementation reports.

    Consolidates test results, requirement coverage, quality gates,
    and iteration data into human-readable and machine-readable reports.
    """

    def __init__(self, project_root: Path, session_id: str):
        """
        Initialize Report Generator.

        Args:
            project_root: Root directory of the project
            session_id: Current session ID
        """
        self.project_root = Path(project_root).resolve()
        self.session_id = session_id

        # Initialize components
        self.session_manager = SessionManager(self.project_root)
        self.decision_logger = DecisionLogger(session_id, self.project_root)

        # Setup logging
        self.logger = logging.getLogger(f"maestro.report.{session_id[:8]}")

    def generate_report(
        self,
        report_data: ReportData,
        output_format: ReportFormat = ReportFormat.MARKDOWN,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate comprehensive implementation report.

        Args:
            report_data: Consolidated report data
            output_format: Desired output format
            output_path: Optional path to write report

        Returns:
            Generated report as string
        """
        self.logger.info(f"Generating {output_format.value} report")

        if output_format == ReportFormat.MARKDOWN:
            report = self._generate_markdown_report(report_data)
        elif output_format == ReportFormat.JSON:
            report = self._generate_json_report(report_data)
        elif output_format == ReportFormat.HTML:
            report = self._generate_html_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            self.logger.info(f"Report written to {output_path}")

        return report

    def _generate_markdown_report(self, data: ReportData) -> str:
        """Generate markdown report."""
        lines = [
            "# Implementation Report",
            "",
            f"**Session**: {data.session_id}",
            f"**Feature**: {data.feature_request}",
            f"**Generated**: {data.timestamp}",
            f"**Status**: {self._get_status_emoji(data.overall_status)} {data.overall_status.upper()}",
            "",
            "---",
            "",
        ]

        # Executive Summary
        lines.extend([
            "## Executive Summary",
            "",
            self._generate_executive_summary(data),
            "",
        ])

        # Test Results
        if data.test_summary:
            lines.extend([
                "## Test Results",
                "",
                self._generate_test_summary(data.test_summary),
                "",
            ])

        # Requirement Coverage
        if data.requirement_summary:
            lines.extend([
                "## PRD Requirement Coverage",
                "",
                self._generate_requirement_summary(data.requirement_summary),
                "",
            ])

        # Quality Gates
        if data.quality_gate_summary:
            lines.extend([
                "## Quality Gates",
                "",
                self._generate_quality_gate_summary(data.quality_gate_summary),
                "",
            ])

        # Iteration Summary
        if data.iteration_summary:
            lines.extend([
                "## Iteration Progress",
                "",
                self._generate_iteration_summary(data.iteration_summary),
                "",
            ])

        # Recommendations
        if data.recommendations:
            lines.extend([
                "## Recommendations",
                "",
            ])
            for i, rec in enumerate(data.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Decision Log
        if data.decisions:
            lines.extend([
                "## Key Decisions",
                "",
            ])
            for decision in data.decisions[:10]:  # Show last 10 decisions
                lines.extend([
                    f"### {decision.get('decision_type', 'Unknown')}",
                    "",
                    f"**Decision**: {decision.get('decision', 'N/A')}",
                    f"**Rationale**: {decision.get('rationale', 'N/A')}",
                    "",
                ])

        return "\n".join(lines)

    def _generate_json_report(self, data: ReportData) -> str:
        """Generate JSON report."""
        report_dict = {
            "session_id": data.session_id,
            "feature_request": data.feature_request,
            "timestamp": data.timestamp,
            "overall_status": data.overall_status,
            "test_summary": data.test_summary.__dict__ if data.test_summary else None,
            "requirement_summary": data.requirement_summary.__dict__ if data.requirement_summary else None,
            "quality_gate_summary": data.quality_gate_summary.__dict__ if data.quality_gate_summary else None,
            "iteration_summary": data.iteration_summary.__dict__ if data.iteration_summary else None,
            "decisions": data.decisions,
            "recommendations": data.recommendations,
        }

        return json.dumps(report_dict, indent=2, default=str)

    def _generate_html_report(self, data: ReportData) -> str:
        """Generate HTML report."""
        # Convert markdown to HTML
        markdown_report = self._generate_markdown_report(data)

        # Simple markdown to HTML conversion
        html = markdown_report
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n")
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n")
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n")
        html = html.replace("**", "<strong>").replace("**", "</strong>")
        html = html.replace("- ", "<li>")
        html = html.replace("\n\n", "</p>\n<p>")

        # Wrap in HTML structure
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Implementation Report - {data.session_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 30px; }}
        .status-success {{ color: green; }}
        .status-partial {{ color: orange; }}
        .status-failed {{ color: red; }}
        ul {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <p>{html}</p>
</body>
</html>
"""

        return full_html

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        return {
            "success": "✅",
            "partial": "🟡",
            "failed": "❌",
            "unknown": "❓",
        }.get(status, "❓")

    def _generate_executive_summary(self, data: ReportData) -> str:
        """Generate executive summary."""
        summary_parts = []

        # Overall assessment
        if data.overall_status == "success":
            summary_parts.append("The implementation has been successfully completed with all quality gates passing.")
        elif data.overall_status == "partial":
            summary_parts.append("The implementation is partially complete with some areas requiring attention.")
        else:
            summary_parts.append("The implementation has significant issues that need to be addressed.")

        # Test coverage
        if data.test_summary:
            summary_parts.append(
                f"Test suite shows {data.test_summary.success_rate:.1f}% success rate "
                f"with {data.test_summary.coverage_percentage:.1f}% code coverage."
            )

        # Requirement coverage
        if data.requirement_summary:
            summary_parts.append(
                f"PRD requirement coverage is {data.requirement_summary.coverage_percentage:.1f}% "
                f"({data.requirement_summary.validated_requirements}/{data.requirement_summary.total_requirements} validated)."
            )

        # Quality gates
        if data.quality_gate_summary:
            summary_parts.append(
                f"Quality gates achieved an average score of {data.quality_gate_summary.average_score:.1f}/100 "
                f"({data.quality_gate_summary.passed_gates}/{data.quality_gate_summary.total_gates} passed)."
            )

        return " ".join(summary_parts)

    def _generate_test_summary(self, summary: TestExecutionSummary) -> str:
        """Generate test summary section."""
        lines = [
            f"**Total Tests**: {summary.total_tests}",
            f"**Passed**: {summary.passed_tests} ({summary.success_rate:.1f}%)",
            f"**Failed**: {summary.failed_tests}",
            f"**Coverage**: {summary.coverage_percentage:.1f}%",
            "",
        ]

        if summary.failures:
            lines.extend([
                "**Failed Tests**:",
                "",
            ])
            for failure in summary.failures[:5]:  # Show first 5 failures
                lines.append(f"- {failure}")

            if len(summary.failures) > 5:
                lines.append(f"- ... and {len(summary.failures) - 5} more")

            lines.append("")

        return "\n".join(lines)

    def _generate_requirement_summary(self, summary: RequirementCoverageSummary) -> str:
        """Generate requirement coverage section."""
        lines = [
            f"**Total Requirements**: {summary.total_requirements}",
            f"**Implemented**: {summary.implemented_requirements}",
            f"**Validated**: {summary.validated_requirements}",
            f"**Coverage**: {summary.coverage_percentage:.1f}%",
            "",
        ]

        if summary.critical_gaps:
            lines.extend([
                "**🚨 Critical Gaps**:",
                "",
            ])
            for gap in summary.critical_gaps:
                lines.append(f"- {gap}")
            lines.append("")

        if summary.missing_requirements:
            lines.extend([
                "**Missing Requirements**:",
                "",
            ])
            for req in summary.missing_requirements[:5]:  # Show first 5
                lines.append(f"- {req}")

            if len(summary.missing_requirements) > 5:
                lines.append(f"- ... and {len(summary.missing_requirements) - 5} more")

            lines.append("")

        return "\n".join(lines)

    def _generate_quality_gate_summary(self, summary: QualityGateSummary) -> str:
        """Generate quality gate section."""
        lines = [
            f"**Total Gates**: {summary.total_gates}",
            f"**Passed**: {summary.passed_gates}",
            f"**Failed**: {summary.failed_gates}",
            f"**Average Score**: {summary.average_score:.1f}/100",
            "",
        ]

        if summary.gate_results:
            lines.extend([
                "**Gate Details**:",
                "",
            ])
            for gate_result in summary.gate_results:
                status_emoji = "✅" if gate_result.get("status") == "passed" else "❌"
                lines.append(
                    f"- {status_emoji} **{gate_result.get('gate_name', 'Unknown')}**: "
                    f"{gate_result.get('score', 0):.1f}/100 - {gate_result.get('message', 'No message')}"
                )

            lines.append("")

        return "\n".join(lines)

    def _generate_iteration_summary(self, summary: IterationSummary) -> str:
        """Generate iteration summary section."""
        lines = [
            f"**Total Iterations**: {summary.total_iterations}",
            f"**Completed**: {summary.completed_iterations}",
            "",
        ]

        if summary.completion_criteria_met:
            lines.extend([
                "**Completion Criteria Met**:",
                "",
            ])
            for criterion in summary.completion_criteria_met:
                lines.append(f"- ✅ {criterion}")
            lines.append("")

        if summary.improvements_made:
            lines.extend([
                "**Improvements Made**:",
                "",
            ])
            for improvement in summary.improvements_made[:5]:  # Show first 5
                lines.append(f"- {improvement}")

            if len(summary.improvements_made) > 5:
                lines.append(f"- ... and {len(summary.improvements_made) - 5} more")

            lines.append("")

        return "\n".join(lines)

    def collect_report_data(
        self,
        validation_results: Optional[Dict[str, Any]] = None,
        requirement_results: Optional[Dict[str, Any]] = None,
        quality_gate_results: Optional[Dict[str, Any]] = None,
        iteration_results: Optional[Dict[str, Any]] = None,
    ) -> ReportData:
        """
        Collect and consolidate data for report generation.

        Args:
            validation_results: Results from validation gate executor
            requirement_results: Results from PRD requirement validator
            quality_gate_results: Results from quality gate runner
            iteration_results: Results from refinement orchestrator

        Returns:
            ReportData with all consolidated information
        """
        self.logger.info("Collecting report data")

        # Get session info
        session = self.session_manager.get_session(self.session_id)
        if not session:
            raise ValueError(f"Session {self.session_id} not found")

        feature_request = session.feature_request

        # Collect test results
        test_summary = None
        if validation_results:
            test_data = validation_results.get("gates", [{}])[0]  # First gate is usually tests
            if test_data and "test" in test_data.get("gate_name", "").lower():
                test_summary = self._parse_test_results(test_data)

        # Collect requirement coverage
        requirement_summary = None
        if requirement_results:
            requirement_summary = self._parse_requirement_results(requirement_results)

        # Collect quality gate results
        quality_gate_summary = None
        if quality_gate_results:
            quality_gate_summary = self._parse_quality_gate_results(quality_gate_results)

        # Collect iteration data
        iteration_summary = None
        if iteration_results:
            iteration_summary = self._parse_iteration_results(iteration_results)

        # Collect recent decisions
        all_decisions = self.decision_logger.get_session_decisions(self.session_id)
        decisions = [
            {
                "decision_type": d.decision_type,
                "decision": d.decision,
                "rationale": d.rationale,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in all_decisions[-20:]  # Last 20 decisions
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            test_summary, requirement_summary, quality_gate_summary
        )

        return ReportData(
            session_id=self.session_id,
            feature_request=feature_request,
            test_summary=test_summary,
            requirement_summary=requirement_summary,
            quality_gate_summary=quality_gate_summary,
            iteration_summary=iteration_summary,
            decisions=decisions,
            recommendations=recommendations,
        )

    def _parse_test_results(self, test_data: Dict[str, Any]) -> TestExecutionSummary:
        """Parse test results from validation data."""
        details = test_data.get("details", {})
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        return TestExecutionSummary(
            total_tests=details.get("total", details.get("test_count", 0)),
            passed_tests=details.get("passed", 0),
            failed_tests=details.get("failed", 0),
            skipped_tests=details.get("skipped", 0),
            coverage_percentage=details.get("coverage", 0.0),
            failures=details.get("failures", []),
        )

    def _parse_requirement_results(self, req_data: Dict[str, Any]) -> RequirementCoverageSummary:
        """Parse requirement results."""
        return RequirementCoverageSummary(
            total_requirements=req_data.get("total_requirements", 0),
            implemented_requirements=req_data.get("implemented_requirements", 0),
            validated_requirements=req_data.get("validated_requirements", 0),
            coverage_percentage=req_data.get("coverage_percentage", 0.0),
            missing_requirements=req_data.get("missing_requirements", []),
            critical_gaps=req_data.get("critical_gaps", []),
        )

    def _parse_quality_gate_results(self, gate_data: Dict[str, Any]) -> QualityGateSummary:
        """Parse quality gate results."""
        summary = gate_data.get("summary", {})

        return QualityGateSummary(
            total_gates=len(gate_data.get("gates", [])),
            passed_gates=summary.get("gates_passed", 0),
            failed_gates=summary.get("gates_failed", 0),
            skipped_gates=summary.get("gates_skipped", 0),
            average_score=summary.get("average_score", 0.0),
            gate_results=gate_data.get("gates", []),
        )

    def _parse_iteration_results(self, iter_data: Dict[str, Any]) -> IterationSummary:
        """Parse iteration results."""
        return IterationSummary(
            total_iterations=iter_data.get("total_iterations", 0),
            completed_iterations=iter_data.get("completed_iterations", 0),
            completion_criteria_met=iter_data.get("completion_criteria_met", []),
            improvements_made=iter_data.get("improvements_made", []),
        )

    def _generate_recommendations(
        self,
        test_summary: Optional[TestExecutionSummary],
        requirement_summary: Optional[RequirementCoverageSummary],
        quality_gate_summary: Optional[QualityGateSummary],
    ) -> List[str]:
        """Generate recommendations based on results."""
        recommendations = []

        # Test recommendations
        if test_summary:
            if test_summary.success_rate < 80:
                recommendations.append(
                    f"Improve test success rate from {test_summary.success_rate:.1f}% to at least 80%"
                )

            if test_summary.coverage_percentage < 70:
                recommendations.append(
                    f"Increase code coverage from {test_summary.coverage_percentage:.1f}% to at least 70%"
                )

        # Requirement recommendations
        if requirement_summary:
            if requirement_summary.coverage_percentage < 90:
                missing = len(requirement_summary.missing_requirements)
                recommendations.append(
                    f"Complete {missing} missing PRD requirements to achieve 90% coverage"
                )

            if requirement_summary.critical_gaps:
                recommendations.append(
                    f"Address {len(requirement_summary.critical_gaps)} critical priority gaps"
                )

        # Quality gate recommendations
        if quality_gate_summary:
            if quality_gate_summary.average_score < 70:
                recommendations.append(
                    f"Improve quality gate scores from {quality_gate_summary.average_score:.1f} to at least 70"
                )

            failed_gates = quality_gate_summary.failed_gates
            if failed_gates > 0:
                recommendations.append(f"Fix {failed_gates} failing quality gates")

        return recommendations


def main():
    """Example usage of ReportGenerator."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python report_generator.py <session-id>")
        sys.exit(1)

    project_root = Path.cwd()
    session_id = sys.argv[1]

    # Create report generator
    generator = ReportGenerator(project_root, session_id)

    # Collect report data
    report_data = generator.collect_report_data()

    # Generate report
    report = generator.generate_report(
        report_data=report_data,
        output_format=ReportFormat.MARKDOWN,
    )

    print(report)


if __name__ == "__main__":
    main()
