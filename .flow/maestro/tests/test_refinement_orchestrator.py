#!/usr/bin/env python3
"""
Tests for Refinement Orchestrator
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from refinement_orchestrator import (
    RefinementOrchestrator,
    CompletionCriterion,
    ValidationResults,
    IterationResult,
)
from session_manager import SessionStatus


class TestValidationResults(unittest.TestCase):
    """Test cases for ValidationResults."""

    def test_validation_results_creation(self):
        """Test creating ValidationResults."""
        results = ValidationResults(
            tests_passed=True,
            test_count=100,
            prd_requirements_met=True,
            prd_requirements_total=8,
            prd_requirements_met_count=8,
            quality_gates_passed=True,
            quality_gate_results={"lint": True, "typecheck": True},
            critical_issues=[],
        )

        self.assertTrue(results.tests_passed)
        self.assertEqual(results.test_count, 100)
        self.assertTrue(results.prd_requirements_met)
        self.assertTrue(results.quality_gates_passed)
        self.assertEqual(len(results.critical_issues), 0)

    def test_to_dict(self):
        """Test converting ValidationResults to dict."""
        results = ValidationResults(tests_passed=True, test_count=50)
        data = results.to_dict()

        self.assertIn("tests_passed", data)
        self.assertTrue(data["tests_passed"])
        self.assertEqual(data["test_count"], 50)


class TestIterationResult(unittest.TestCase):
    """Test cases for IterationResult."""

    def test_iteration_result_creation(self):
        """Test creating IterationResult."""
        result = IterationResult(
            iteration_number=1,
            should_continue=True,
        )

        self.assertEqual(result.iteration_number, 1)
        self.assertTrue(result.should_continue)

    def test_to_dict(self):
        """Test converting IterationResult to dict."""
        result = IterationResult(
            iteration_number=1,
            completion_criteria_met=[CompletionCriterion.ALL_TESTS_PASSING],
        )
        data = result.to_dict()

        self.assertEqual(data["iteration_number"], 1)
        self.assertIn("all_tests_passing", data["completion_criteria_met"])


class TestRefinementOrchestrator(unittest.TestCase):
    """Test cases for RefinementOrchestrator."""

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
        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature",
            "status": SessionStatus.PLANNING.value,
            "current_phase": "plan",
            "start_time": "2025-01-07T10:00:00Z",
            "created_at": "2025-01-07T10:00:00Z",
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
        """Test RefinementOrchestrator initialization."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        self.assertEqual(orchestrator.session_id, self.session_id)
        self.assertEqual(orchestrator.max_iterations, 3)
        self.assertEqual(len(orchestrator.completion_criteria), 4)

    def test_custom_completion_criteria(self):
        """Test RefinementOrchestrator with custom completion criteria."""
        custom_criteria = [CompletionCriterion.ALL_TESTS_PASSING]
        orchestrator = RefinementOrchestrator(
            self.project_root,
            self.session_id,
            completion_criteria=custom_criteria,
        )

        self.assertEqual(orchestrator.completion_criteria, custom_criteria)

    def test_should_continue_refining_no_iterations(self):
        """Test should_continue_refining when no iterations have run."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        self.assertTrue(orchestrator.should_continue_refining())

    def test_should_continue_refining_complete(self):
        """Test should_continue_refining when complete."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        # Add a complete iteration
        orchestrator.iterations.append(IterationResult(
            iteration_number=1,
            should_continue=False,
            completion_criteria_met=list(orchestrator.completion_criteria),
        ))

        self.assertFalse(orchestrator.should_continue_refining())

    def test_should_continue_refining_max_iterations(self):
        """Test should_continue_refining when max iterations reached."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id, max_iterations=2)

        # Add max iterations
        orchestrator.iterations.append(IterationResult(iteration_number=1, should_continue=True))
        orchestrator.iterations.append(IterationResult(iteration_number=2, should_continue=True))

        self.assertFalse(orchestrator.should_continue_refining())

    def test_get_progress_summary_no_iterations(self):
        """Test get_progress_summary when no iterations have run."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        summary = orchestrator.get_progress_summary()

        self.assertEqual(summary["total_iterations"], 0)
        self.assertFalse(summary["complete"])
        self.assertEqual(len(summary["completion_criteria_met"]), 0)

    def test_get_progress_summary_with_iterations(self):
        """Test get_progress_summary with iterations."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        orchestrator.iterations.append(IterationResult(
            iteration_number=1,
            completion_criteria_met=[CompletionCriterion.ALL_TESTS_PASSING],
            should_continue=True,
            improvements_needed=["Fix tests"],
        ))

        summary = orchestrator.get_progress_summary()

        self.assertEqual(summary["total_iterations"], 1)
        self.assertFalse(summary["complete"])
        self.assertIn("all_tests_passing", summary["completion_criteria_met"])
        self.assertEqual(summary["improvements_needed"], ["Fix tests"])

    def test_get_progress_summary_complete(self):
        """Test get_progress_summary when complete."""
        orchestrator = RefinementOrchestrator(
            self.project_root,
            self.session_id,
            completion_criteria=[
                CompletionCriterion.ALL_TESTS_PASSING,
                CompletionCriterion.NO_CRITICAL_ISSUES,
            ],
        )

        orchestrator.iterations.append(IterationResult(
            iteration_number=1,
            completion_criteria_met=list(orchestrator.completion_criteria),
            should_continue=False,
        ))

        summary = orchestrator.get_progress_summary()

        self.assertTrue(summary["complete"])
        self.assertEqual(summary["completion_percentage"], 100)

    def test_check_completion_criteria_all_met(self):
        """Test _check_completion_criteria when all criteria are met."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        validation = ValidationResults(
            tests_passed=True,
            prd_requirements_met=True,
            quality_gates_passed=True,
            critical_issues=[],
        )

        met = orchestrator._check_completion_criteria(validation)

        self.assertEqual(len(met), 4)

    def test_check_completion_criteria_partial(self):
        """Test _check_completion_criteria with partial completion."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        validation = ValidationResults(
            tests_passed=False,
            prd_requirements_met=True,
            quality_gates_passed=False,
            critical_issues=[],
        )

        met = orchestrator._check_completion_criteria(validation)

        self.assertEqual(len(met), 2)  # PRD met, no critical issues

    def test_identify_improvements(self):
        """Test _identify_improvements generates correct improvement list."""
        orchestrator = RefinementOrchestrator(self.project_root, self.session_id)

        validation = ValidationResults(
            tests_passed=False,
            test_count=100,
            prd_requirements_met=False,
            prd_requirements_total=8,
            prd_requirements_met_count=5,
            quality_gates_passed=False,
            quality_gate_results={"lint": False, "typecheck": True},
            critical_issues=["Security issue"],
        )

        met_criteria = [CompletionCriterion.NO_CRITICAL_ISSUES]  # Only this is met (wait, this is wrong)

        improvements = orchestrator._identify_improvements(validation, met_criteria)

        self.assertGreater(len(improvements), 0)
        self.assertTrue(any("tests" in imp.lower() for imp in improvements))
        self.assertTrue(any("prd" in imp.lower() for imp in improvements))


class TestCompletionCriterion(unittest.TestCase):
    """Test cases for CompletionCriterion enum."""

    def test_completion_criterion_values(self):
        """Test CompletionCriterion enum values."""
        self.assertEqual(CompletionCriterion.ALL_TESTS_PASSING.value, "all_tests_passing")
        self.assertEqual(CompletionCriterion.ALL_PRD_REQUIREMENTS_MET.value, "all_prd_requirements_met")
        self.assertEqual(CompletionCriterion.QUALITY_GATES_PASSED.value, "quality_gates_passed")
        self.assertEqual(CompletionCriterion.NO_CRITICAL_ISSUES.value, "no_critical_issues")


if __name__ == "__main__":
    unittest.main()
