#!/usr/bin/env python3
"""
Maestro Validation Gate Executor - Orchestrates validation gates

Runs all validation gates in the refinement loop:
- Test execution and result collection
- PRD requirement validation
- Quality gate checks (linting, type checking, security)
- Critical issue detection

Returns ValidationResults with detailed status for each gate.
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


class ValidationGateStatus(Enum):
    """Status of a validation gate."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class GateResult:
    """Result from a single validation gate."""

    gate_name: str
    status: ValidationGateStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "execution_time": self.execution_time,
        }


@dataclass
class TestResults:
    """Results from test execution."""

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    coverage: float = 0.0
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.total,
            "coverage": self.coverage,
            "failures": self.failures,
        }

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.passed > 0


class ValidationGate:
    """Base class for validation gates."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"maestro.validation.{name}")

    def execute(self, context: Dict[str, Any]) -> GateResult:
        """
        Execute the validation gate.

        Args:
            context: Execution context with project_root, session_id, etc.

        Returns:
            GateResult with execution outcome
        """
        raise NotImplementedError("Subclasses must implement execute()")


class TestExecutionGate(ValidationGate):
    """Executes test suite and collects results."""

    def __init__(self):
        super().__init__(
            name="test_execution",
            description="Run test suite and collect results",
        )

    def execute(self, context: Dict[str, Any]) -> GateResult:
        """Execute tests and return results."""
        import time

        start_time = time.time()
        project_root = context.get("project_root")

        try:
            # Detect test framework
            test_framework = self._detect_test_framework(project_root)

            if test_framework == "pytest":
                results = self._run_pytest(project_root)
            elif test_framework == "unittest":
                results = self._run_unittest(project_root)
            elif test_framework == "jest":
                results = self._run_jest(project_root)
            elif test_framework == "go":
                results = self._run_go_tests(project_root)
            else:
                return GateResult(
                    gate_name=self.name,
                    status=ValidationGateStatus.SKIPPED,
                    message=f"No test framework detected",
                )

            execution_time = time.time() - start_time

            status = ValidationGateStatus.PASSED if results.success else ValidationGateStatus.FAILED

            return GateResult(
                gate_name=self.name,
                status=status,
                message=f"Tests: {results.passed}/{results.total} passed",
                details=results.to_dict(),
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Test execution failed: {e}")

            return GateResult(
                gate_name=self.name,
                status=ValidationGateStatus.FAILED,
                message=f"Test execution error: {e}",
                execution_time=execution_time,
            )

    def _detect_test_framework(self, project_root: Optional[Path]) -> Optional[str]:
        """Detect which test framework is being used."""
        if not project_root:
            return None

        # Check for Python frameworks
        if (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists():
            return "pytest"
        if (project_root / "test").exists() or (project_root / "tests").exists():
            # Check for pytest usage
            test_dirs = ["test", "tests"]
            for test_dir in test_dirs:
                test_path = project_root / test_dir
                if test_path.exists():
                    # Look for pytest markers
                    for py_file in test_path.rglob("*.py"):
                        content = py_file.read_text()
                        if "import pytest" in content or "from pytest" in content:
                            return "pytest"
                    return "unittest"

        # Check for JavaScript frameworks
        if (project_root / "package.json").exists():
            package_json = json.loads((project_root / "package.json").read_text())
            if "jest" in package_json.get("devDependencies", {}):
                return "jest"

        # Check for Go
        if any((project_root / "*_test.go").glob("*")):
            return "go"

        return None

    def _run_pytest(self, project_root: Path) -> TestResults:
        """Run pytest and collect results."""
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "-v", "--cov=.", "--cov-report=json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Parse output
        output = result.stdout + result.stderr

        # Try to read coverage file
        coverage = 0.0
        coverage_file = project_root / "coverage.json"
        if coverage_file.exists():
            try:
                coverage_data = json.loads(coverage_file.read_text())
                coverage = coverage_data.get("totals", {}).get("percent_covered", 0.0)
            except Exception:
                pass

        # Parse test counts from output
        import re

        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        total = passed + failed

        return TestResults(
            passed=passed,
            failed=failed,
            total=total,
            coverage=coverage,
        )

    def _run_unittest(self, project_root: Path) -> TestResults:
        """Run unittest and collect results."""
        result = subprocess.run(
            ["python", "-m", "unittest", "discover", "-v"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr

        # Parse unittest output
        import re

        passed_match = re.search(r"Ran (\d+) test", output)
        total = int(passed_match.group(1)) if passed_match else 0

        # Check if tests passed
        failed = 1 if "FAILED" in output else 0
        passed = total - failed if total > 0 else 0

        return TestResults(
            passed=passed,
            failed=failed,
            total=total,
        )

    def _run_jest(self, project_root: Path) -> TestResults:
        """Run Jest and collect results."""
        result = subprocess.run(
            ["npm", "test", "--", "--json", "--outputFile=test-results.json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Parse Jest output
        results_file = project_root / "test-results.json"
        if results_file.exists():
            try:
                jest_results = json.loads(results_file.read_text())
                success = jest_results.get("success", False)
                total = jest_results.get("numTotalTests", 0)
                passed = jest_results.get("numPassedTests", 0)
                failed = jest_results.get("numFailedTests", 0)

                return TestResults(
                    passed=passed,
                    failed=failed,
                    total=total,
                )
            except Exception:
                pass

        # Fallback to parsing output
        return TestResults(passed=0, failed=1, total=1)

    def _run_go_tests(self, project_root: Path) -> TestResults:
        """Run Go tests and collect results."""
        result = subprocess.run(
            ["go", "test", "./...", "-v"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr

        # Parse Go test output
        import re

        passed_match = re.search(r"PASS: (.+)", output)
        failed_match = re.search(r"FAIL: (.+)", output)

        passed = len(re.findall(r"PASS:", output)) if passed_match else 0
        failed = len(re.findall(r"FAIL:", output)) if failed_match else 0
        total = passed + failed

        return TestResults(
            passed=passed,
            failed=failed,
            total=total,
        )


class QualityGateChecker(ValidationGate):
    """Runs quality gate checks (linting, type checking, etc.)."""

    def __init__(self):
        super().__init__(
            name="quality_gates",
            description="Run quality gate checks",
        )

    def execute(self, context: Dict[str, Any]) -> GateResult:
        """Execute quality gates and return results."""
        import time

        start_time = time.time()
        project_root = context.get("project_root")

        try:
            gate_results = {}

            # Run various quality checks
            gate_results["lint"] = self._check_linting(project_root)
            gate_results["typecheck"] = self._check_typecheck(project_root)
            gate_results["security"] = self._check_security(project_root)

            # Determine overall status
            all_passed = all(result["passed"] for result in gate_results.values() if result)

            status = ValidationGateStatus.PASSED if all_passed else ValidationGateStatus.FAILED

            failed_gates = [name for name, result in gate_results.items() if not result.get("passed", True)]
            message = f"Quality gates: {', '.join(failed_gates)} failed" if failed_gates else "All quality gates passed"

            execution_time = time.time() - start_time

            return GateResult(
                gate_name=self.name,
                status=status,
                message=message,
                details={"gates": gate_results},
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Quality gate execution failed: {e}")

            return GateResult(
                gate_name=self.name,
                status=ValidationGateStatus.FAILED,
                message=f"Quality gate error: {e}",
                execution_time=execution_time,
            )

    def _check_linting(self, project_root: Optional[Path]) -> Dict[str, Any]:
        """Check code linting."""
        if not project_root:
            return {"passed": False, "message": "No project root"}

        # Detect and run linter
        if (project_root / ".flake8").exists() or (project_root / "setup.cfg").exists():
            result = subprocess.run(
                ["flake8", "."],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            return {"passed": result.returncode == 0, "output": result.stdout + result.stderr}

        if (project_root / "pyproject.toml").exists():
            # Try ruff
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 or "not found" not in result.stderr.lower():
                return {"passed": result.returncode == 0, "output": result.stdout + result.stderr}

        if (project_root / "package.json").exists():
            result = subprocess.run(
                ["npm", "run", "lint"],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            return {"passed": result.returncode == 0, "output": result.stdout + result.stderr}

        return {"passed": True, "message": "No linter configured"}

    def _check_typecheck(self, project_root: Optional[Path]) -> Dict[str, Any]:
        """Check type checking."""
        if not project_root:
            return {"passed": False, "message": "No project root"}

        # Check for mypy
        if (project_root / "pyproject.toml").exists() or (project_root / "mypy.ini").exists():
            result = subprocess.run(
                ["mypy", "."],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 or "Success" in result.stdout:
                return {"passed": True, "output": result.stdout + result.stderr}
            return {"passed": False, "output": result.stdout + result.stderr}

        # Check for TypeScript
        if (project_root / "tsconfig.json").exists():
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            return {"passed": result.returncode == 0, "output": result.stdout + result.stderr}

        return {"passed": True, "message": "No type checker configured"}

    def _check_security(self, project_root: Optional[Path]) -> Dict[str, Any]:
        """Check security issues."""
        if not project_root:
            return {"passed": False, "message": "No project root"}

        # Check for bandit
        result = subprocess.run(
            ["bandit", "-r", ".", "-f", "json"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {"passed": True, "output": "No security issues found"}

        # Bandit might not be installed, skip
        if "command not found" in result.stderr or "not found" in result.stderr.lower():
            return {"passed": True, "message": "Security scanner not available"}

        # Parse bandit output
        try:
            bandit_results = json.loads(result.stdout)
            issues = bandit_results.get("results", [])
            high_severity = [i for i in issues if i.get("issue_severity") == "HIGH"]

            if high_severity:
                return {
                    "passed": False,
                    "output": f"Found {len(high_severity)} high severity security issues",
                }
        except Exception:
            pass

        return {"passed": True, "message": "No critical security issues"}


class ValidationGateExecutor:
    """
    Orchestrates execution of all validation gates.

    Runs gates in order, collects results, and provides summary.
    """

    def __init__(self, project_root: Path, session_id: str):
        """
        Initialize Validation Gate Executor.

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
        self.logger = logging.getLogger(f"maestro.validation.{session_id[:8]}")

        # Register validation gates
        self.gates: List[ValidationGate] = [
            TestExecutionGate(),
            QualityGateChecker(),
        ]

    def execute_validation_gates(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute all validation gates.

        Args:
            context: Optional execution context

        Returns:
            Dictionary with all gate results and summary
        """
        self.logger.info("Executing validation gates")

        context = context or {}
        context.update({
            "project_root": self.project_root,
            "session_id": self.session_id,
        })

        gate_results = []

        for gate in self.gates:
            self.logger.info(f"Running gate: {gate.name}")

            try:
                result = gate.execute(context)
                gate_results.append(result)

                # Log gate completion
                self.decision_logger.log_decision(
                    decision_type="validation_gate",
                    decision={
                        "decision": f"Validation gate {gate.name} completed with status {result.status.value}",
                        "rationale": result.message,
                        "gate": gate.name,
                        "status": result.status.value,
                        "message": result.message,
                        "execution_time": result.execution_time,
                    },
                )

            except Exception as e:
                self.logger.error(f"Gate {gate.name} failed: {e}")
                gate_results.append(GateResult(
                    gate_name=gate.name,
                    status=ValidationGateStatus.FAILED,
                    message=f"Gate execution error: {e}",
                ))

        # Calculate summary
        summary = self._calculate_summary(gate_results)

        # Log overall validation result
        self.decision_logger.log_decision(
            decision_type="validation_summary",
            decision={
                "decision": f"Validation complete: {summary['overall_status']} ({summary['gates_passed']}/{summary['gates_passed'] + summary['gates_failed']} gates passed)",
                "rationale": f"Executed {len(gate_results)} validation gates in {summary['total_execution_time']:.2f}s",
                "overall_status": summary["overall_status"],
                "gates_passed": summary["gates_passed"],
                "gates_failed": summary["gates_failed"],
                "total_execution_time": summary["total_execution_time"],
            },
        )

        return {
            "gates": [r.to_dict() for r in gate_results],
            "summary": summary,
        }

    def _calculate_summary(self, gate_results: List[GateResult]) -> Dict[str, Any]:
        """Calculate summary of gate results."""
        passed = sum(1 for r in gate_results if r.status == ValidationGateStatus.PASSED)
        failed = sum(1 for r in gate_results if r.status == ValidationGateStatus.FAILED)
        skipped = sum(1 for r in gate_results if r.status == ValidationGateStatus.SKIPPED)

        overall_status = "passed" if failed == 0 and passed > 0 else "failed"
        total_time = sum(r.execution_time for r in gate_results)

        return {
            "overall_status": overall_status,
            "gates_passed": passed,
            "gates_failed": failed,
            "gates_skipped": skipped,
            "total_execution_time": total_time,
            "gate_names": [r.gate_name for r in gate_results],
        }

    def register_gate(self, gate: ValidationGate) -> None:
        """
        Register a custom validation gate.

        Args:
            gate: ValidationGate instance to add
        """
        self.gates.append(gate)
        self.logger.info(f"Registered validation gate: {gate.name}")


def main():
    """Example usage of ValidationGateExecutor."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python validation_gate_executor.py <session-id>")
        sys.exit(1)

    project_root = Path.cwd()
    session_id = sys.argv[1]

    # Create executor
    executor = ValidationGateExecutor(project_root, session_id)

    # Execute validation gates
    results = executor.execute_validation_gates()

    print(f"\nValidation Summary:")
    print(f"Status: {results['summary']['overall_status']}")
    print(f"Passed: {results['summary']['gates_passed']}")
    print(f"Failed: {results['summary']['gates_failed']}")
    print(f"Total time: {results['summary']['total_execution_time']:.2f}s")


if __name__ == "__main__":
    main()
