#!/usr/bin/env python3
"""
Maestro Quality Gate Runner - Executes and manages quality gates

Focused module for running quality gate checks:
- Code linting
- Type checking
- Security scanning
- Code coverage validation
- Custom quality gate plugins

Provides standalone execution or integration with ValidationGateExecutor.
"""

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
sys.path.insert(0, str(maestro_root / "scripts"))
sys.path.insert(0, str(maestro_root / "decision-engine" / "scripts"))

from session_manager import SessionManager
from decision_logger import DecisionLogger


class QualityGateStatus(Enum):
    """Status of a quality gate."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class QualityGateResult:
    """Result from a quality gate check."""

    gate_name: str
    status: QualityGateStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    score: float = 100.0  # Quality score (0-100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "execution_time": self.execution_time,
            "score": self.score,
        }


@dataclass
class QualityGateConfig:
    """Configuration for a quality gate."""

    name: str
    enabled: bool = True
    required: bool = True  # If True, failure blocks deployment
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    threshold: float = 0.0  # Minimum score threshold
    custom_checker: Optional[Callable[[], QualityGateResult]] = None


class QualityGate:
    """Base class for quality gates."""

    def __init__(self, name: str, config: Optional[QualityGateConfig] = None):
        self.name = name
        self.config = config or QualityGateConfig(name=name)
        self.logger = logging.getLogger(f"maestro.quality.{name}")

    def execute(self, project_root: Path) -> QualityGateResult:
        """
        Execute the quality gate check.

        Args:
            project_root: Root directory of the project

        Returns:
            QualityGateResult with execution outcome
        """
        if not self.config.enabled:
            return QualityGateResult(
                gate_name=self.name,
                status=QualityGateStatus.SKIPPED,
                message="Quality gate disabled",
            )

        if self.config.custom_checker:
            return self.config.custom_checker()

        return self._execute_default(project_root)

    def _execute_default(self, project_root: Path) -> QualityGateResult:
        """Execute default check logic."""
        raise NotImplementedError("Subclasses must implement _execute_default")


class LintingGate(QualityGate):
    """Code linting quality gate."""

    def __init__(self, config: Optional[QualityGateConfig] = None):
        super().__init__("linting", config)

    def _execute_default(self, project_root: Path) -> QualityGateResult:
        """Execute linting checks."""
        import time

        start_time = time.time()

        # Detect and run appropriate linter
        linter_result = self._run_linter(project_root)

        execution_time = time.time() - start_time

        status = QualityGateStatus.PASSED if linter_result["passed"] else QualityGateStatus.FAILED

        return QualityGateResult(
            gate_name=self.name,
            status=status,
            message=linter_result["message"],
            details=linter_result,
            execution_time=execution_time,
            score=linter_result.get("score", 100.0 if linter_result["passed"] else 0.0),
        )

    def _run_linter(self, project_root: Path) -> Dict[str, Any]:
        """Run appropriate linter for the project."""
        # Try different linters
        linters = [
            self._try_ruff,
            self._try_flake8,
            self._try_eslint,
            self._try_golint,
        ]

        for linter_func in linters:
            result = linter_func(project_root)
            if result is not None:
                return result

        return {
            "passed": True,
            "message": "No linter configured",
            "score": 100.0,
        }

    def _try_ruff(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running ruff."""
        result = subprocess.run(
            ["ruff", "check", ".", "--output-format=json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if "not found" in result.stderr.lower():
            return None

        try:
            issues = json.loads(result.stdout)
            error_count = len(issues)

            return {
                "passed": error_count == 0,
                "message": f"Found {error_count} linting issues",
                "issues": issues,
                "score": max(0, 100 - error_count * 2),
            }
        except Exception:
            return {
                "passed": result.returncode == 0,
                "message": "Ruff linting check",
                "score": 100.0 if result.returncode == 0 else 0.0,
            }

    def _try_flake8(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running flake8."""
        if not (project_root / ".flake8").exists() and not (project_root / "setup.cfg").exists():
            return None

        result = subprocess.run(
            ["flake8", ".", "--format=json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {
                "passed": True,
                "message": "No flake8 issues",
                "score": 100.0,
            }

        return {
            "passed": False,
            "message": "Flake8 found issues",
            "output": result.stdout + result.stderr,
            "score": 0.0,
        }

    def _try_eslint(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running ESLint."""
        if not (project_root / "package.json").exists():
            return None

        result = subprocess.run(
            ["npm", "run", "lint", "--", "--format=json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        try:
            issues = json.loads(result.stdout)
            error_count = len(issues)

            return {
                "passed": error_count == 0,
                "message": f"ESLint: {error_count} issues",
                "score": max(0, 100 - error_count * 5),
            }
        except Exception:
            return {
                "passed": result.returncode == 0,
                "message": "ESLint check",
                "score": 100.0 if result.returncode == 0 else 0.0,
            }

    def _try_golint(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running go lint."""
        go_files = list(project_root.rglob("*.go"))
        if not go_files:
            return None

        result = subprocess.run(
            ["golangci-lint", "run"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if "command not found" in result.stderr.lower():
            return None

        return {
            "passed": result.returncode == 0,
            "message": "Go lint check",
            "score": 100.0 if result.returncode == 0 else 0.0,
        }


class TypeCheckingGate(QualityGate):
    """Type checking quality gate."""

    def __init__(self, config: Optional[QualityGateConfig] = None):
        super().__init__("typecheck", config)

    def _execute_default(self, project_root: Path) -> QualityGateResult:
        """Execute type checking."""
        import time

        start_time = time.time()

        checker_result = self._run_type_checker(project_root)

        execution_time = time.time() - start_time

        status = QualityGateStatus.PASSED if checker_result["passed"] else QualityGateStatus.FAILED

        return QualityGateResult(
            gate_name=self.name,
            status=status,
            message=checker_result["message"],
            details=checker_result,
            execution_time=execution_time,
            score=checker_result.get("score", 100.0 if checker_result["passed"] else 0.0),
        )

    def _run_type_checker(self, project_root: Path) -> Dict[str, Any]:
        """Run appropriate type checker."""
        checkers = [
            self._try_mypy,
            self._try_tsc,
            self._try_pyright,
        ]

        for checker_func in checkers:
            result = checker_func(project_root)
            if result is not None:
                return result

        return {
            "passed": True,
            "message": "No type checker configured",
            "score": 100.0,
        }

    def _try_mypy(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running mypy."""
        if not ((project_root / "mypy.ini").exists() or (project_root / "pyproject.toml").exists()):
            return None

        result = subprocess.run(
            ["mypy", ".", "--json-report", "/tmp/mypy-report"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if "command not found" in result.stderr.lower():
            return None

        # Try to parse JSON report
        try:
            report_file = Path("/tmp/mypy-report.json")
            if report_file.exists():
                report = json.loads(report_file.read_text())
                error_count = len(report.get("files", []))

                return {
                    "passed": result.returncode == 0,
                    "message": f"mypy: {error_count} type errors",
                    "score": max(0, 100 - error_count * 10),
                }
        except Exception:
            pass

        return {
            "passed": result.returncode == 0,
            "message": "mypy type check",
            "score": 100.0 if result.returncode == 0 else 0.0,
        }

    def _try_tsc(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running TypeScript compiler."""
        if not (project_root / "tsconfig.json").exists():
            return None

        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        return {
            "passed": result.returncode == 0,
            "message": "TypeScript type check",
            "score": 100.0 if result.returncode == 0 else 0.0,
        }

    def _try_pyright(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running pyright."""
        result = subprocess.run(
            ["pyright", ".", "--outputjson"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if "command not found" in result.stderr.lower():
            return None

        try:
            output = json.loads(result.stdout)
            error_count = output.get("generalDiagnostics", [])

            return {
                "passed": error_count == 0,
                "message": f"pyright: {len(error_count)} type errors",
                "score": max(0, 100 - len(error_count) * 10),
            }
        except Exception:
            return {
                "passed": result.returncode == 0,
                "message": "pyright type check",
                "score": 100.0 if result.returncode == 0 else 0.0,
            }


class SecurityGate(QualityGate):
    """Security scanning quality gate."""

    def __init__(self, config: Optional[QualityGateConfig] = None):
        super().__init__("security", config)

    def _execute_default(self, project_root: Path) -> QualityGateResult:
        """Execute security scanning."""
        import time

        start_time = time.time()

        security_result = self._run_security_scan(project_root)

        execution_time = time.time() - start_time

        status = QualityGateStatus.PASSED if security_result["passed"] else QualityGateStatus.FAILED

        # Security issues are critical
        if not security_result["passed"] and self.config.required:
            status = QualityGateStatus.FAILED

        return QualityGateResult(
            gate_name=self.name,
            status=status,
            message=security_result["message"],
            details=security_result,
            execution_time=execution_time,
            score=security_result.get("score", 100.0 if security_result["passed"] else 0.0),
        )

    def _run_security_scan(self, project_root: Path) -> Dict[str, Any]:
        """Run security scan."""
        scanners = [
            self._try_bandit,
            self._try_safety,
            self._try_npm_audit,
        ]

        results = []
        for scanner_func in scanners:
            result = scanner_func(project_root)
            if result is not None:
                results.append(result)

        if not results:
            return {
                "passed": True,
                "message": "No security scanner configured",
                "score": 100.0,
            }

        # Aggregate results
        all_passed = all(r["passed"] for r in results)
        total_score = sum(r.get("score", 0) for r in results) / len(results)

        return {
            "passed": all_passed,
            "message": f"Security scan: {len([r for r in results if not r['passed']])} scanners found issues",
            "scanners": results,
            "score": total_score,
        }

    def _try_bandit(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running bandit."""
        result = subprocess.run(
            ["bandit", "-r", ".", "-f", "json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if "command not found" in result.stderr.lower():
            return None

        try:
            bandit_results = json.loads(result.stdout)
            high_severity = [i for i in bandit_results.get("results", []) if i.get("issue_severity") == "HIGH"]

            return {
                "passed": len(high_severity) == 0,
                "message": f"Bandit: {len(high_severity)} high severity issues",
                "score": max(0, 100 - len(high_severity) * 20),
            }
        except Exception:
            return {
                "passed": result.returncode == 0,
                "message": "Bandit security scan",
                "score": 100.0 if result.returncode == 0 else 0.0,
            }

    def _try_safety(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running safety."""
        result = subprocess.run(
            ["safety", "check", "--json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if "command not found" in result.stderr.lower():
            return None

        try:
            issues = json.loads(result.stdout)
            vuln_count = len(issues)

            return {
                "passed": vuln_count == 0,
                "message": f"Safety: {vuln_count} vulnerabilities",
                "score": max(0, 100 - vuln_count * 30),
            }
        except Exception:
            return {
                "passed": result.returncode == 0,
                "message": "Safety dependency check",
                "score": 100.0 if result.returncode == 0 else 0.0,
            }

    def _try_npm_audit(self, project_root: Path) -> Optional[Dict[str, Any]]:
        """Try running npm audit."""
        if not (project_root / "package.json").exists():
            return None

        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        try:
            audit = json.loads(result.stdout)
            vulns = audit.get("vulnerabilities", {})
            high_vulns = [v for v in vulns.values() if v.get("severity") == "high"]

            return {
                "passed": len(high_vulns) == 0,
                "message": f"npm audit: {len(high_vulns)} high severity vulnerabilities",
                "score": max(0, 100 - len(high_vulns) * 25),
            }
        except Exception:
            return {
                "passed": result.returncode == 0,
                "message": "npm audit check",
                "score": 100.0 if result.returncode == 0 else 0.0,
            }


class QualityGateRunner:
    """
    Orchestrates execution of quality gates.

    Runs configured quality gates and provides aggregated results.
    """

    def __init__(self, project_root: Path, session_id: str):
        """
        Initialize Quality Gate Runner.

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
        self.logger = logging.getLogger(f"maestro.quality.{session_id[:8]}")

        # Register default quality gates
        self.gates: List[QualityGate] = [
            LintingGate(),
            TypeCheckingGate(),
            SecurityGate(),
        ]

    def execute_quality_gates(
        self,
        custom_gates: Optional[List[QualityGate]] = None,
    ) -> Dict[str, Any]:
        """
        Execute all quality gates.

        Args:
            custom_gates: Optional list of custom gates to run instead of defaults

        Returns:
            Dictionary with all gate results and summary
        """
        self.logger.info("Executing quality gates")

        gates_to_run = custom_gates or self.gates
        gate_results = []

        for gate in gates_to_run:
            self.logger.info(f"Running quality gate: {gate.name}")

            try:
                result = gate.execute(self.project_root)
                gate_results.append(result)

                # Log gate completion
                self.decision_logger.log_decision(
                    decision_type="quality_gate",
                    decision={
                        "decision": f"Quality gate {gate.name} completed with status {result.status.value}",
                        "rationale": result.message,
                        "gate": gate.name,
                        "status": result.status.value,
                        "score": result.score,
                    },
                )

            except Exception as e:
                self.logger.error(f"Quality gate {gate.name} failed: {e}")
                gate_results.append(QualityGateResult(
                    gate_name=gate.name,
                    status=QualityGateStatus.FAILED,
                    message=f"Quality gate error: {e}",
                    score=0.0,
                ))

        # Calculate summary
        summary = self._calculate_summary(gate_results)

        # Log overall result
        self.decision_logger.log_decision(
            decision_type="quality_gate_summary",
            decision={
                "decision": f"Quality gate check: {summary['overall_status']} (average score: {summary['average_score']:.1f})",
                "rationale": f"Ran {len(gate_results)} quality gates, {summary['passed']} passed",
                "overall_status": summary["overall_status"],
                "average_score": summary["average_score"],
                "passed": summary["passed"],
                "failed": summary["failed"],
            },
        )

        return {
            "gates": [r.to_dict() for r in gate_results],
            "summary": summary,
        }

    def _calculate_summary(self, gate_results: List[QualityGateResult]) -> Dict[str, Any]:
        """Calculate summary of gate results."""
        passed = sum(1 for r in gate_results if r.status == QualityGateStatus.PASSED)
        failed = sum(1 for r in gate_results if r.status == QualityGateStatus.FAILED)
        skipped = sum(1 for r in gate_results if r.status == QualityGateStatus.SKIPPED)
        warnings = sum(1 for r in gate_results if r.status == QualityGateStatus.WARNING)

        total_score = sum(r.score for r in gate_results)
        average_score = total_score / len(gate_results) if gate_results else 0.0

        overall_status = "passed" if failed == 0 and average_score >= 50 else "failed"

        return {
            "overall_status": overall_status,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "warnings": warnings,
            "average_score": average_score,
            "total_score": total_score,
            "gate_names": [r.gate_name for r in gate_results],
        }

    def register_gate(self, gate: QualityGate) -> None:
        """
        Register a custom quality gate.

        Args:
            gate: QualityGate instance to add
        """
        self.gates.append(gate)
        self.logger.info(f"Registered quality gate: {gate.name}")


def main():
    """Example usage of QualityGateRunner."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python quality_gate_runner.py <session-id>")
        sys.exit(1)

    project_root = Path.cwd()
    session_id = sys.argv[1]

    # Create runner
    runner = QualityGateRunner(project_root, session_id)

    # Execute quality gates
    results = runner.execute_quality_gates()

    print(f"\nQuality Gate Summary:")
    print(f"Status: {results['summary']['overall_status']}")
    print(f"Average Score: {results['summary']['average_score']:.1f}/100")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")


if __name__ == "__main__":
    main()
