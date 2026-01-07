#!/usr/bin/env python3
"""
Tests for task ordering with dependency resolution.
"""

import json
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, "/home/ll931217/GitHub/dotfiles.feat-orchestrate-flow/.flow/maestro/decision-engine/scripts")

from task_ordering import (
    TaskOrderingEngine,
    PRIORITY_MAP,
    get_beads_issues,
    get_issue_details,
    _extract_dependencies,
)


class TestTaskOrderingEngine(unittest.TestCase):
    """Test cases for TaskOrderingEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = TaskOrderingEngine(strategy="topological")

    def test_empty_graph(self):
        """Test ordering with empty graph."""
        result = self.engine.compute_ordering()
        self.assertEqual(result["total_tasks"], 0)
        self.assertEqual(result["total_groups"], 0)

    def test_simple_linear_chain(self):
        """Test simple linear dependency chain: A -> B -> C."""
        # Mock tasks
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Task A", "priority": 2, "depends_on": []},
            "task-b": {"id": "task-b", "title": "Task B", "priority": 2, "depends_on": ["task-a"]},
            "task-c": {"id": "task-c", "title": "Task C", "priority": 2, "depends_on": ["task-b"]},
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c"]
        self.engine.graph["edges"] = [("task-a", "task-b"), ("task-b", "task-c")]
        self.engine.graph["adj"] = {
            "task-a": ["task-b"],
            "task-b": ["task-c"],
            "task-c": [],
        }

        result = self.engine.compute_ordering()

        self.assertEqual(result["total_tasks"], 3)
        self.assertEqual(len(result["sequence"]), 3)

        # Verify order
        self.assertEqual(result["sequence"][0], ["task-a"])
        self.assertEqual(result["sequence"][1], ["task-b"])
        self.assertEqual(result["sequence"][2], ["task-c"])

    def test_parallel_execution(self):
        """Test parallel execution detection: A -> [B, C] -> D."""
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Task A", "priority": 2, "depends_on": []},
            "task-b": {"id": "task-b", "title": "Task B", "priority": 2, "depends_on": ["task-a"]},
            "task-c": {"id": "task-c", "title": "Task C", "priority": 2, "depends_on": ["task-a"]},
            "task-d": {"id": "task-d", "title": "Task D", "priority": 2, "depends_on": ["task-b", "task-c"]},
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c", "task-d"]
        self.engine.graph["edges"] = [
            ("task-a", "task-b"),
            ("task-a", "task-c"),
            ("task-b", "task-d"),
            ("task-c", "task-d"),
        ]
        self.engine.graph["adj"] = {
            "task-a": ["task-b", "task-c"],
            "task-b": ["task-d"],
            "task-c": ["task-d"],
            "task-d": [],
        }

        result = self.engine.compute_ordering()

        self.assertEqual(result["total_tasks"], 4)
        self.assertEqual(len(result["sequence"]), 3)

        # Verify parallel group
        self.assertEqual(result["sequence"][0], ["task-a"])
        self.assertIn("task-b", result["sequence"][1])
        self.assertIn("task-c", result["sequence"][1])
        self.assertEqual(len(result["sequence"][1]), 2)  # B and C in parallel
        self.assertEqual(result["sequence"][2], ["task-d"])

    def test_risk_first_ordering(self):
        """Test priority-based ordering."""
        self.engine.strategy = "risk_first"
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Task A", "priority": 0, "depends_on": []},  # P0
            "task-b": {"id": "task-b", "title": "Task B", "priority": 2, "depends_on": []},  # P2
            "task-c": {"id": "task-c", "title": "Task C", "priority": 1, "depends_on": []},  # P1
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c"]
        self.engine.graph["edges"] = []
        self.engine.graph["adj"] = {}
        self.engine.priority_groups = {
            0: {"task-a"},
            1: {"task-c"},
            2: {"task-b"},
        }

        result = self.engine.compute_ordering()

        # P0 should be first
        self.assertIn("task-a", result["sequence"][0])
        # P1 before P2
        c_group = next(g for g in result["sequence"] if "task-c" in g)
        b_group = next(g for g in result["sequence"] if "task-b" in g)
        c_index = result["sequence"].index(c_group)
        b_index = result["sequence"].index(b_group)
        self.assertLess(c_index, b_index)

    def test_foundational_first_ordering(self):
        """Test foundational task detection."""
        self.engine.strategy = "foundational_first"
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Create database schema", "priority": 2, "depends_on": []},
            "task-b": {"id": "task-b", "title": "Build UI", "priority": 2, "depends_on": []},
            "task-c": {"id": "task-c", "title": "Implement API", "priority": 2, "depends_on": ["task-a"]},
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c"]
        self.engine.graph["edges"] = [("task-a", "task-c")]
        self.engine.graph["adj"] = {
            "task-a": ["task-c"],
            "task-b": [],
            "task-c": [],
        }

        result = self.engine.compute_ordering()

        # Foundational task (schema) should be first
        self.assertEqual(result["sequence"][0], ["task-a"])

    def test_file_conflict_detection(self):
        """Test file conflict detection between tasks."""
        self.engine.graph["tasks"] = {
            "task-a": {
                "id": "task-a",
                "title": "Modify auth service",
                "description": "Update `src/auth.ts` and `src/auth.test.ts`",
                "priority": 2,
                "depends_on": [],
            },
            "task-b": {
                "id": "task-b",
                "title": "Add auth feature",
                "description": "Add methods to `src/auth.ts`",
                "priority": 2,
                "depends_on": [],
            },
            "task-c": {
                "id": "task-c",
                "title": "Update user service",
                "description": "Modify `src/user.ts`",
                "priority": 2,
                "depends_on": [],
            },
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c"]
        self.engine.graph["edges"] = []
        self.engine.graph["adj"] = {}

        result = self.engine.compute_ordering(detect_conflicts=True)

        # task-a and task-b should be separated due to conflict
        # They should not be in the same group
        for group in result["sequence"]:
            if len(group) > 1:
                # If parallel group exists, task-c can be with either a or b
                # but a and b should not be together
                if "task-a" in group and "task-b" in group:
                    self.fail("Conflicting tasks task-a and task-b are in the same parallel group")

    def test_complex_dependency_graph(self):
        """Test complex dependency graph with multiple levels."""
        # Graph structure:
        #     A     D
        #    / \   /
        #   B   C E
        #    \ /
        #     F
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Task A", "priority": 2, "depends_on": []},
            "task-b": {"id": "task-b", "title": "Task B", "priority": 2, "depends_on": ["task-a"]},
            "task-c": {"id": "task-c", "title": "Task C", "priority": 2, "depends_on": ["task-a"]},
            "task-d": {"id": "task-d", "title": "Task D", "priority": 2, "depends_on": []},
            "task-e": {"id": "task-e", "title": "Task E", "priority": 2, "depends_on": ["task-d"]},
            "task-f": {"id": "task-f", "title": "Task F", "priority": 2, "depends_on": ["task-b", "task-c", "task-e"]},
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c", "task-d", "task-e", "task-f"]
        self.engine.graph["edges"] = [
            ("task-a", "task-b"),
            ("task-a", "task-c"),
            ("task-d", "task-e"),
            ("task-b", "task-f"),
            ("task-c", "task-f"),
            ("task-e", "task-f"),
        ]
        self.engine.graph["adj"] = {
            "task-a": ["task-b", "task-c"],
            "task-b": ["task-f"],
            "task-c": ["task-f"],
            "task-d": ["task-e"],
            "task-e": ["task-f"],
            "task-f": [],
        }

        result = self.engine.compute_ordering()

        # Should have 3 groups: [A, D] -> [B, C, E] -> [F]
        self.assertEqual(len(result["sequence"]), 3)

        # Group 1: A and D (parallel, no dependencies)
        self.assertIn("task-a", result["sequence"][0])
        self.assertIn("task-d", result["sequence"][0])

        # Group 2: B, C, and E (parallel, depend on A or D)
        self.assertIn("task-b", result["sequence"][1])
        self.assertIn("task-c", result["sequence"][1])
        self.assertIn("task-e", result["sequence"][1])

        # Group 3: F (depends on B, C, E)
        self.assertEqual(result["sequence"][2], ["task-f"])

    def test_parallel_maximizing_strategy(self):
        """Test parallel maximizing strategy."""
        self.engine.strategy = "parallel_maximizing"
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Task A", "priority": 2, "depends_on": []},
            "task-b": {"id": "task-b", "title": "Task B", "priority": 2, "depends_on": ["task-a"]},
            "task-c": {"id": "task-c", "title": "Task C", "priority": 2, "depends_on": ["task-a"]},
            "task-d": {"id": "task-d", "title": "Task D", "priority": 2, "depends_on": []},
        }
        self.engine.graph["nodes"] = ["task-a", "task-b", "task-c", "task-d"]
        self.engine.graph["edges"] = [
            ("task-a", "task-b"),
            ("task-a", "task-c"),
        ]
        self.engine.graph["adj"] = {
            "task-a": ["task-b", "task-c"],
            "task-b": [],
            "task-c": [],
            "task-d": [],
        }

        result = self.engine.compute_ordering()

        # Group 1: A and D (parallel, no dependencies)
        self.assertIn("task-a", result["sequence"][0])
        self.assertIn("task-d", result["sequence"][0])
        self.assertEqual(len(result["sequence"][0]), 2)

    def test_rationale_generation(self):
        """Test rationale generation."""
        self.engine.graph["tasks"] = {
            "task-a": {"id": "task-a", "title": "Task A", "priority": 0, "depends_on": []},
            "task-b": {"id": "task-b", "title": "Task B", "priority": 2, "depends_on": []},
        }
        self.engine.graph["nodes"] = ["task-a", "task-b"]
        self.engine.graph["edges"] = []
        self.engine.graph["adj"] = {}

        result = self.engine.compute_ordering()

        self.assertIn("rationale", result)
        self.assertIn("Strategy", result["rationale"])
        self.assertIn("Group", result["rationale"])


class TestBeadsIntegration(unittest.TestCase):
    """Test cases for beads integration."""

    @patch("task_ordering.subprocess.run")
    def test_get_beads_issues(self, mock_run):
        """Test getting issues from beads."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {"id": "test-1", "title": "Test 1", "status": "open"},
                {"id": "test-2", "title": "Test 2", "status": "closed"},
            ])
        )

        issues = get_beads_issues()

        self.assertEqual(len(issues), 1)  # Only open issues
        self.assertEqual(issues[0]["id"], "test-1")

    @patch("task_ordering.subprocess.run")
    def test_get_issue_details(self, mock_run):
        """Test getting issue details."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([{
                "id": "test-1",
                "title": "Test 1",
                "status": "open",
                "priority": 1,
                "dependencies": [
                    {"id": "dep-1", "dependency_type": "blocks"},
                    {"id": "parent-1", "dependency_type": "parent-child"},
                ],
            }])
        )

        details = get_issue_details("test-1")

        self.assertEqual(details["id"], "test-1")
        self.assertEqual(details["priority"], 1)
        self.assertEqual(len(details["depends_on"]), 1)  # Only non-parent-child deps
        self.assertIn("dep-1", details["depends_on"])

    def test_extract_dependencies(self):
        """Test dependency extraction."""
        issue_data = {
            "dependencies": [
                {"id": "dep-1", "dependency_type": "blocks"},
                {"id": "parent-1", "dependency_type": "parent-child"},
                {"id": "dep-2", "dependency_type": "depends_on"},
            ]
        }

        deps = _extract_dependencies(issue_data)

        self.assertEqual(len(deps), 2)
        self.assertIn("dep-1", deps)
        self.assertIn("dep-2", deps)
        self.assertNotIn("parent-1", deps)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTaskOrderingEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestBeadsIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
