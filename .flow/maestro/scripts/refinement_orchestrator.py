#!/usr/bin/env python3
"""
Maestro Refinement Orchestrator - Implements the iterative refinement loop

Manages the plan-implement-validate-review cycle:
1. Plan - Generate/update PRD
2. Implement - Execute tasks
3. Validate - Run tests and quality gates
4. Review - Check completion criteria and decide whether to continue

Continues until all completion criteria are met or max iterations reached.
"""

import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
sys.path.insert(0, str(maestro_root / "scripts"))
sys.path.insert(0, str(maestro_root / "decision-engine" / "scripts"))

from session_manager import SessionManager, SessionStatus
from decision_logger import DecisionLogger
from error_handler import ErrorHandler
from checkpoint_manager import CheckpointManager, CheckpointType
from phase_manager import PhaseManager, Phase, PhaseResult


class CompletionCriterion(Enum):
    """Completion criteria for the refinement loop."""

    ALL_TESTS_PASSING = "all_tests_passing"
    ALL_PRD_REQUIREMENTS_MET = "all_prd_requirements_met"
    QUALITY_GATES_PASSED = "quality_gates_passed"
    NO_CRITICAL_ISSUES = "no_critical_issues"


@dataclass
class ValidationResults:
    """Results from the validation phase."""

    tests_passed: bool = False
    test_count: int = 0
    prd_requirements_met: bool = False
    prd_requirements_total: int = 0
    prd_requirements_met_count: int = 0
    quality_gates_passed: bool = False
    quality_gate_results: Dict[str, bool] = field(default_factory=dict)
    critical_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tests_passed": self.tests_passed,
            "test_count": self.test_count,
            "prd_requirements_met": self.prd_requirements_met,
            "prd_requirements_total": self.prd_requirements_total,
            "prd_requirements_met_count": self.prd_requirements_met_count,
            "quality_gates_passed": self.quality_gates_passed,
            "quality_gate_results": self.quality_gate_results,
            "critical_issues": self.critical_issues,
        }


@dataclass
class IterationResult:
    """Results from a single refinement iteration."""

    iteration_number: int
    phase_results: Dict[str, Any] = field(default_factory=dict)
    validation_results: Optional[ValidationResults] = None
    completion_criteria_met: List[CompletionCriterion] = field(default_factory=list)
    should_continue: bool = False
    improvements_needed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "iteration_number": self.iteration_number,
            "phase_results": self.phase_results,
            "validation_results": self.validation_results.to_dict() if self.validation_results else None,
            "completion_criteria_met": [c.value for c in self.completion_criteria_met],
            "should_continue": self.should_continue,
            "improvements_needed": self.improvements_needed,
        }


class RefinementOrchestrator:
    """
    Orchestrates the iterative refinement loop.

    Implements plan-implement-validate-review cycle with configurable
    completion criteria and maximum iterations.
    """

    def __init__(
        self,
        project_root: Path,
        session_id: str,
        max_iterations: int = 3,
        completion_criteria: Optional[List[CompletionCriterion]] = None,
    ):
        """
        Initialize Refinement Orchestrator.

        Args:
            project_root: Root directory of the project
            session_id: Current session ID
            max_iterations: Maximum number of refinement iterations
            completion_criteria: List of criteria that must be met
        """
        self.project_root = Path(project_root).resolve()
        self.session_id = session_id
        self.max_iterations = max_iterations

        # Default completion criteria
        self.completion_criteria = completion_criteria or [
            CompletionCriterion.ALL_TESTS_PASSING,
            CompletionCriterion.ALL_PRD_REQUIREMENTS_MET,
            CompletionCriterion.QUALITY_GATES_PASSED,
            CompletionCriterion.NO_CRITICAL_ISSUES,
        ]

        # Initialize components
        self.session_manager = SessionManager(self.project_root)
        self.decision_logger = DecisionLogger(session_id, self.project_root)
        self.phase_manager = PhaseManager(self.project_root, session_id)
        self.error_handler = ErrorHandler(self.project_root)
        self.checkpoint_manager = CheckpointManager(self.project_root)

        # Setup logging
        self.logger = logging.getLogger(f"maestro.refinement.{session_id[:8]}")

        # Track iterations
        self.iterations: List[IterationResult] = []

    def execute_refinement_loop(
        self,
        planning_func: Callable[[], Dict[str, Any]],
        implementation_func: Callable[[], Dict[str, Any]],
        validation_func: Callable[[], ValidationResults],
    ) -> List[IterationResult]:
        """
        Execute the iterative refinement loop.

        Args:
            planning_func: Function to execute planning phase
            implementation_func: Function to execute implementation phase
            validation_func: Function to validate results

        Returns:
            List of iteration results
        """
        self.logger.info(f"Starting refinement loop (max {self.max_iterations} iterations)")

        for iteration in range(1, self.max_iterations + 1):
            self.logger.info(f"=== Iteration {iteration}/{self.max_iterations} ===")

            result = self._execute_iteration(
                iteration_number=iteration,
                planning_func=planning_func,
                implementation_func=implementation_func,
                validation_func=validation_func,
            )

            self.iterations.append(result)

            # Log iteration completion
            self.decision_logger.log_decision(
                decision_type="iteration",
                decision={
                    "decision": f"Iteration {iteration} completed",
                    "rationale": f"Criteria met: {', '.join([c.value for c in result.completion_criteria_met])}",
                    "should_continue": result.should_continue,
                    "iteration": iteration,
                },
            )

            if not result.should_continue:
                self.logger.info("All completion criteria met - refinement complete")
                break
            else:
                self.logger.info(f"Improvements needed: {result.improvements_needed}")
                self.logger.info(f"Starting iteration {iteration + 1}")

        return self.iterations

    def _execute_iteration(
        self,
        iteration_number: int,
        planning_func: Callable[[], Dict[str, Any]],
        implementation_func: Callable[[], Dict[str, Any]],
        validation_func: Callable[[], ValidationResults],
    ) -> IterationResult:
        """Execute a single refinement iteration."""
        phase_results = {}
        improvements_needed = []

        # Phase 1: Plan
        self.logger.info("Phase 1: Planning")
        try:
            plan_result = self.phase_manager.execute_phase(
                phase=Phase.PLANNING,
                execute_func=planning_func,
            )
            phase_results["planning"] = {
                "success": plan_result.success,
                "data": plan_result.data,
            }
        except Exception as e:
            self.logger.error(f"Planning phase failed: {e}")
            improvements_needed.append(f"Planning error: {e}")

        # Phase 2: Implement (skip if planning failed)
        if not improvements_needed or phase_results.get("planning", {}).get("success"):
            self.logger.info("Phase 2: Implementation")
            try:
                impl_result = self.phase_manager.execute_phase(
                    phase=Phase.IMPLEMENTATION,
                    execute_func=implementation_func,
                )
                phase_results["implementation"] = {
                    "success": impl_result.success,
                    "data": impl_result.data,
                }
            except Exception as e:
                self.logger.error(f"Implementation phase failed: {e}")
                improvements_needed.append(f"Implementation error: {e}")

        # Phase 3: Validate (skip if implementation failed)
        if not improvements_needed or phase_results.get("implementation", {}).get("success"):
            self.logger.info("Phase 3: Validation")
            try:
                validation_result = validation_func()
                phase_results["validation"] = validation_result.to_dict()
            except Exception as e:
                self.logger.error(f"Validation phase failed: {e}")
                validation_result = ValidationResults()
                improvements_needed.append(f"Validation error: {e}")
        else:
            validation_result = ValidationResults()

        # Phase 4: Review
        self.logger.info("Phase 4: Review")
        completion_criteria_met = self._check_completion_criteria(validation_result)
        should_continue = len(completion_criteria_met) < len(self.completion_criteria)

        # Identify improvements needed
        if should_continue:
            improvements_needed.extend(self._identify_improvements(
                validation_result, completion_criteria_met
            ))

        return IterationResult(
            iteration_number=iteration_number,
            phase_results=phase_results,
            validation_results=validation_result,
            completion_criteria_met=completion_criteria_met,
            should_continue=should_continue,
            improvements_needed=improvements_needed,
        )

    def _check_completion_criteria(self, validation: ValidationResults) -> List[CompletionCriterion]:
        """Check which completion criteria are met."""
        met = []

        for criterion in self.completion_criteria:
            if criterion == CompletionCriterion.ALL_TESTS_PASSING:
                if validation.tests_passed:
                    met.append(criterion)
            elif criterion == CompletionCriterion.ALL_PRD_REQUIREMENTS_MET:
                if validation.prd_requirements_met:
                    met.append(criterion)
            elif criterion == CompletionCriterion.QUALITY_GATES_PASSED:
                if validation.quality_gates_passed:
                    met.append(criterion)
            elif criterion == CompletionCriterion.NO_CRITICAL_ISSUES:
                if not validation.critical_issues:
                    met.append(criterion)

        return met

    def _identify_improvements(
        self,
        validation: ValidationResults,
        met_criteria: List[CompletionCriterion],
    ) -> List[str]:
        """Identify what improvements are needed based on validation results."""
        improvements = []

        # Check which criteria are not met
        unmet = set(self.completion_criteria) - set(met_criteria)

        for criterion in unmet:
            if criterion == CompletionCriterion.ALL_TESTS_PASSING:
                improvements.append("Fix failing tests")
            elif criterion == CompletionCriterion.ALL_PRD_REQUIREMENTS_MET:
                improvements.append(
                    f"Implement missing PRD requirements "
                    f"({validation.prd_requirements_met_count}/{validation.prd_requirements_total} met)"
                )
            elif criterion == CompletionCriterion.QUALITY_GATES_PASSED:
                failed_gates = [
                    gate for gate, passed in validation.quality_gate_results.items() if not passed
                ]
                improvements.append(f"Fix quality gates: {', '.join(failed_gates)}")
            elif criterion == CompletionCriterion.NO_CRITICAL_ISSUES:
                improvements.append(f"Resolve critical issues: {', '.join(validation.critical_issues[:3])}")

        return improvements

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get summary of refinement progress."""
        if not self.iterations:
            return {
                "total_iterations": 0,
                "complete": False,
                "completion_criteria_met": [],
            }

        latest = self.iterations[-1]

        return {
            "total_iterations": len(self.iterations),
            "max_iterations": self.max_iterations,
            "complete": not latest.should_continue,
            "completion_criteria_met": [c.value for c in latest.completion_criteria_met],
            "completion_percentage": int(
                len(latest.completion_criteria_met) / len(self.completion_criteria) * 100
            ),
            "improvements_needed": latest.improvements_needed if latest.should_continue else [],
        }

    def should_continue_refining(self) -> bool:
        """Check if refinement should continue."""
        if not self.iterations:
            return True

        latest = self.iterations[-1]
        return latest.should_continue and len(self.iterations) < self.max_iterations


def main():
    """Example usage of RefinementOrchestrator."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python refinement_orchestrator.py <session-id>")
        sys.exit(1)

    project_root = Path.cwd()
    session_id = sys.argv[1]

    # Create refinement orchestrator
    orchestrator = RefinementOrchestrator(project_root, session_id)

    # Define iteration functions
    def planning():
        return {"prd_generated": True}

    def implementation():
        return {"tasks_completed": 5}

    def validation():
        return ValidationResults(
            tests_passed=True,
            test_count=100,
            prd_requirements_met=True,
            prd_requirements_total=8,
            prd_requirements_met_count=8,
            quality_gates_passed=True,
            quality_gate_results={"lint": True, "typecheck": True},
            critical_issues=[],
        )

    # Execute refinement loop
    results = orchestrator.execute_refinement_loop(
        planning_func=planning,
        implementation_func=implementation,
        validation_func=validation,
    )

    print(f"\nRefinement complete after {len(results)} iterations")
    summary = orchestrator.get_progress_summary()
    print(f"Complete: {summary['complete']}")
    print(f"Completion: {summary['completion_percentage']}%")


if __name__ == "__main__":
    main()
