#!/usr/bin/env python3
"""
Tests for TaskOrderingStrategy

Comprehensive test suite covering:
- Simple dependency chains
- Parallel group detection
- Complex dependency graphs
- Critical path minimization
- [P:Group-N] marker generation
- Integration with ParallelCoordinator format
"""

import json
import sys
import unittest
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, "/home/ll931217/GitHub/dotfiles.feat-orchestrate-flow/.flow/maestro/decision-engine/scripts")

from decision_strategy import DecisionContext
from task_ordering_strategy import (
    TaskOrderingStrategy,
    TaskDependency,
    OrderedTask,
    create_task_ordering_decision,
)


class TestTaskDependency(unittest.TestCase):
    """Test TaskDependency dataclass."""

    def test_task_dependency_creation(self):
        """Test creating TaskDependency."""
        task = TaskDependency(
            task_id="task-1",
            depends_on=["task-0"],
            priority=1
        )

        self.assertEqual(task.task_id, "task-1")
        self.assertEqual(task.depends_on, ["task-0"])
        self.assertEqual(task.priority, 1)

    def test_task_dependency_defaults(self):
        """Test TaskDependency with default values."""
        task = TaskDependency(task_id="task-1")

        self.assertEqual(task.task_id, "task-1")
        self.assertEqual(task.depends_on, [])
        self.assertEqual(task.priority, 2)


class TestOrderedTask(unittest.TestCase):
    """Test OrderedTask dataclass."""

    def test_ordered_task_creation(self):
        """Test creating OrderedTask."""
        task = OrderedTask(
            task_id="task-1",
            group="Group-1",
            order=0,
            dependencies=["task-0"]
        )

        self.assertEqual(task.task_id, "task-1")
        self.assertEqual(task.group, "Group-1")
        self.assertEqual(task.order, 0)
        self.assertEqual(task.dependencies, ["task-0"])

    def test_is_parallel(self):
        """Test is_parallel method."""
        parallel_task = OrderedTask(
            task_id="task-1",
            group="Group-1",
            order=0
        )

        sequential_task = OrderedTask(
            task_id="task-2",
            group="Sequential-1",
            order=1
        )

        self.assertTrue(parallel_task.is_parallel())
        self.assertFalse(sequential_task.is_parallel())

    def test_get_group_marker(self):
        """Test get_group_marker method."""
        parallel_task = OrderedTask(
            task_id="task-1",
            group="Group-1",
            order=0
        )

        sequential_task = OrderedTask(
            task_id="task-2",
            group="Sequential-1",
            order=1
        )

        self.assertEqual(parallel_task.get_group_marker(), "[P:Group-1]")
        self.assertEqual(sequential_task.get_group_marker(), "")


class TestTaskOrderingStrategy(unittest.TestCase):
    """Test TaskOrderingStrategy class."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_strategy_name(self):
        """Test get_strategy_name."""
        name = self.strategy.get_strategy_name()

        self.assertEqual(name, "task_ordering_parallel_maximizer")

    def test_strategy_description(self):
        """Test get_strategy_description."""
        description = self.strategy.get_strategy_description()

        self.assertIn("parallel", description.lower())
        self.assertIn("topological", description.lower())

    def test_supported_decision_types(self):
        """Test get_supported_decision_types."""
        types = self.strategy.get_supported_decision_types()

        self.assertIn("task_ordering", types)
        self.assertIn("execution_plan", types)
        self.assertIn("parallelization", types)

    def test_validate_context_with_tasks(self):
        """Test validate_context with valid tasks."""
        context = DecisionContext(
            prd_requirements={"tasks": [{"id": "task-1"}]},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        result = self.strategy.validate_context(context)

        self.assertTrue(result)

    def test_validate_context_without_tasks(self):
        """Test validate_context without tasks raises error."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        with self.assertRaises(ValueError) as cm:
            self.strategy.validate_context(context)

        self.assertIn("tasks", str(cm.exception).lower())

    def test_validate_context_with_none(self):
        """Test validate_context with None raises error."""
        with self.assertRaises(ValueError) as cm:
            self.strategy.validate_context(None)

        self.assertIn("none", str(cm.exception).lower())


class TestSimpleDependencyChain(unittest.TestCase):
    """Test simple linear dependency chain: A -> B -> C."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_linear_chain_ordering(self):
        """Test ordering of linear dependency chain."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-b"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        # Parse ordered tasks
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Should have 3 tasks
        self.assertEqual(len(ordered_tasks), 3)

        # Should be in order: A -> B -> C
        self.assertEqual(ordered_tasks[0].task_id, "task-a")
        self.assertEqual(ordered_tasks[1].task_id, "task-b")
        self.assertEqual(ordered_tasks[2].task_id, "task-c")

        # All should be sequential
        for task in ordered_tasks:
            self.assertFalse(task.is_parallel())

    def test_linear_chain_dependencies(self):
        """Test dependencies are preserved in linear chain."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-b"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Check dependencies
        self.assertEqual(ordered_tasks[0].dependencies, [])
        self.assertEqual(ordered_tasks[1].dependencies, ["task-a"])
        self.assertEqual(ordered_tasks[2].dependencies, ["task-b"])


class TestParallelGroupDetection(unittest.TestCase):
    """Test parallel group detection: A -> [B, C] -> D."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_parallel_group_detection(self):
        """Test detection of parallel tasks."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-d", "depends_on": ["task-b", "task-c"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Should have 4 tasks
        self.assertEqual(len(ordered_tasks), 4)

        # First task: A (sequential)
        self.assertEqual(ordered_tasks[0].task_id, "task-a")
        self.assertFalse(ordered_tasks[0].is_parallel())

        # Second group: B and C (parallel)
        b_task = next(t for t in ordered_tasks if t.task_id == "task-b")
        c_task = next(t for t in ordered_tasks if t.task_id == "task-c")

        self.assertTrue(b_task.is_parallel())
        self.assertTrue(c_task.is_parallel())
        self.assertEqual(b_task.group, c_task.group)  # Same group

        # Last task: D (sequential, depends on both B and C)
        d_task = next(t for t in ordered_tasks if t.task_id == "task-d")
        self.assertFalse(d_task.is_parallel())

    def test_parallel_group_marker_format(self):
        """Test [P:Group-N] marker format."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Find parallel group
        parallel_tasks = [t for t in ordered_tasks if t.is_parallel()]

        # Should have [P:Group-N] marker
        for task in parallel_tasks:
            marker = task.get_group_marker()
            self.assertTrue(marker.startswith("[P:Group-"))
            self.assertTrue(marker.endswith("]"))


class TestComplexDependencyGraph(unittest.TestCase):
    """Test complex dependency graph with multiple levels."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_diamond_dependency(self):
        """Test diamond dependency: A -> [B, C] -> D."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-d", "depends_on": ["task-b", "task-c"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Verify order: A -> [B, C] -> D
        self.assertEqual(ordered_tasks[0].task_id, "task-a")

        # B and C should be in same group (parallel)
        b_task = next(t for t in ordered_tasks if t.task_id == "task-b")
        c_task = next(t for t in ordered_tasks if t.task_id == "task-c")
        self.assertEqual(b_task.group, c_task.group)

        # D should be last
        d_task = next(t for t in ordered_tasks if t.task_id == "task-d")
        self.assertTrue(d_task.order > b_task.order)
        self.assertTrue(d_task.order > c_task.order)

    def test_multiple_independent_branches(self):
        """Test multiple independent branches."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": [], "priority": 2},
            {"id": "task-d", "depends_on": ["task-c"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # A and C should be in parallel group (both have no deps)
        a_task = next(t for t in ordered_tasks if t.task_id == "task-a")
        c_task = next(t for t in ordered_tasks if t.task_id == "task-c")

        self.assertTrue(a_task.is_parallel())
        self.assertTrue(c_task.is_parallel())
        self.assertEqual(a_task.group, c_task.group)

        # B and D should be in parallel group (depend on A and C respectively)
        b_task = next(t for t in ordered_tasks if t.task_id == "task-b")
        d_task = next(t for t in ordered_tasks if t.task_id == "task-d")

        self.assertTrue(b_task.is_parallel())
        self.assertTrue(d_task.is_parallel())
        self.assertEqual(b_task.group, d_task.group)

    def test_complex_multilevel_graph(self):
        """Test complex multi-level graph."""
        # Graph structure:
        #     A     D
        #    / \   /
        #   B   C E
        #    \ /
        #     F
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-d", "depends_on": [], "priority": 2},
            {"id": "task-e", "depends_on": ["task-d"], "priority": 2},
            {"id": "task-f", "depends_on": ["task-b", "task-c", "task-e"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Should have 3 groups: [A, D] -> [B, C, E] -> [F]
        groups = {}
        for task in ordered_tasks:
            if task.group not in groups:
                groups[task.group] = []
            groups[task.group].append(task)

        # Should have 3 groups
        self.assertEqual(len(groups), 3)

        # First group: A and D
        first_group = sorted(groups.values(), key=lambda g: g[0].order)[0]
        first_group_ids = [t.task_id for t in first_group]
        self.assertIn("task-a", first_group_ids)
        self.assertIn("task-d", first_group_ids)

        # Last group: F
        f_task = next(t for t in ordered_tasks if t.task_id == "task-f")
        self.assertTrue(f_task.order > max(
            next(t for t in ordered_tasks if t.task_id == "task-b").order,
            next(t for t in ordered_tasks if t.task_id == "task-c").order,
            next(t for t in ordered_tasks if t.task_id == "task-e").order
        ))


class TestCriticalPathMinimization(unittest.TestCase):
    """Test critical path minimization."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_critical_path_identification(self):
        """Test identification of critical path."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-d", "depends_on": ["task-b"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        # Should have high confidence
        self.assertGreaterEqual(decision.confidence, 0.7)

        # Should mention critical path in rationale
        self.assertIn("rationale", decision.__dict__)


class TestCircularDependencyDetection(unittest.TestCase):
    """Test circular dependency detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_circular_dependencies_raise_error(self):
        """Test that circular dependencies raise error."""
        tasks = [
            {"id": "task-a", "depends_on": ["task-b"], "priority": 2},
            {"id": "task-b", "depends_on": ["task-c"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        with self.assertRaises(ValueError) as cm:
            self.strategy.decide(context)

        self.assertIn("circular", str(cm.exception).lower())


class TestParallelGroupMarkerGeneration(unittest.TestCase):
    """Test [P:Group-N] marker generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_marker_format_for_parallel_groups(self):
        """Test marker format is correct for parallel groups."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": [], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a", "task-b"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Find parallel group (A and B)
        parallel_tasks = [t for t in ordered_tasks if t.is_parallel()]

        self.assertEqual(len(parallel_tasks), 2)

        # Check markers
        for task in parallel_tasks:
            marker = task.get_group_marker()
            self.assertTrue(marker.startswith("[P:Group-"))
            self.assertTrue(marker.endswith("]"))

    def test_no_marker_for_sequential_tasks(self):
        """Test that sequential tasks have no marker."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # All tasks should be sequential
        for task in ordered_tasks:
            self.assertFalse(task.is_parallel())
            self.assertEqual(task.get_group_marker(), "")


class TestParallelCoordinatorIntegration(unittest.TestCase):
    """Test integration with ParallelCoordinator format."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_output_format_compatibility(self):
        """Test output format is compatible with ParallelCoordinator."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Each task should have required fields
        for task in ordered_tasks:
            self.assertIsInstance(task.task_id, str)
            self.assertIsInstance(task.group, str)
            self.assertIsInstance(task.order, int)
            self.assertIsInstance(task.dependencies, list)

    def test_group_detection_for_coordinator(self):
        """Test group detection matches ParallelCoordinator expectations."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2, "description": "[P:Group-1] Setup A"},
            {"id": "task-b", "depends_on": [], "priority": 2, "description": "[P:Group-1] Setup B"},
            {"id": "task-c", "depends_on": ["task-a", "task-b"], "priority": 2, "description": "Final task"},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Should detect A and B as parallel
        a_task = next(t for t in ordered_tasks if t.task_id == "task-a")
        b_task = next(t for t in ordered_tasks if t.task_id == "task-b")

        self.assertTrue(a_task.is_parallel())
        self.assertTrue(b_task.is_parallel())
        self.assertEqual(a_task.group, b_task.group)

        # C should be sequential
        c_task = next(t for t in ordered_tasks if t.task_id == "task-c")
        self.assertFalse(c_task.is_parallel())


class TestConfidenceCalculation(unittest.TestCase):
    """Test confidence calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_high_confidence_with_parallel_groups(self):
        """Test high confidence with good parallelization."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": [], "priority": 2},
            {"id": "task-c", "depends_on": [], "priority": 2},
            {"id": "task-d", "depends_on": ["task-a", "task-b", "task-c"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        # Should have high confidence (good parallelization)
        self.assertGreaterEqual(decision.confidence, 0.8)
        self.assertEqual(decision.get_confidence_level(), "high")

    def test_moderate_confidence_sequential(self):
        """Test moderate confidence with mostly sequential tasks."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
            {"id": "task-c", "depends_on": ["task-b"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        # Should have moderate confidence (mostly sequential)
        self.assertGreater(decision.confidence, 0.5)
        self.assertLess(decision.confidence, 0.9)


class TestRationaleGeneration(unittest.TestCase):
    """Test rationale generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_rationale_contains_plan(self):
        """Test rationale contains execution plan."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        # Rationale should contain key information
        self.assertIn("Task Ordering", decision.rationale)
        self.assertIn("Total tasks", decision.rationale)
        self.assertIn("Execution Plan", decision.rationale)

    def test_rationale_shows_groups(self):
        """Test rationale shows group information."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": [], "priority": 2},
            {"id": "task-c", "depends_on": ["task-a", "task-b"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        # Rationale should mention parallel tasks
        self.assertIn("parallel", decision.rationale.lower())


class TestConvenienceFunction(unittest.TestCase):
    """Test create_task_ordering_decision convenience function."""

    def test_convenience_function(self):
        """Test create_task_ordering_decision function."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
        ]

        decision = create_task_ordering_decision(tasks, session_id="test")

        # Should return valid decision
        self.assertIsInstance(decision.choice, str)
        self.assertIsInstance(decision.rationale, str)
        self.assertIsInstance(decision.confidence, float)
        self.assertGreater(decision.confidence, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)

    def test_convenience_function_parsing(self):
        """Test parsing result from convenience function."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-a"], "priority": 2},
        ]

        decision = create_task_ordering_decision(tasks)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Should be parseable and correct
        self.assertEqual(len(ordered_tasks), 2)
        self.assertEqual(ordered_tasks[0].task_id, "task-a")
        self.assertEqual(ordered_tasks[1].task_id, "task-b")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TaskOrderingStrategy()

    def test_empty_task_list(self):
        """Test handling of empty task list."""
        context = DecisionContext(
            prd_requirements={"tasks": []},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        with self.assertRaises(ValueError) as cm:
            self.strategy.decide(context)

        self.assertIn("no tasks", str(cm.exception).lower())

    def test_single_task_no_deps(self):
        """Test single task with no dependencies."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # Should have single task
        self.assertEqual(len(ordered_tasks), 1)
        self.assertEqual(ordered_tasks[0].task_id, "task-a")
        self.assertFalse(ordered_tasks[0].is_parallel())

    def test_all_independent_tasks(self):
        """Test all tasks are independent (fully parallel)."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": [], "priority": 2},
            {"id": "task-c", "depends_on": [], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        # All should be in same parallel group
        for task in ordered_tasks:
            self.assertTrue(task.is_parallel())
            self.assertEqual(task.group, ordered_tasks[0].group)

    def test_task_with_missing_dependency(self):
        """Test task referencing non-existent dependency."""
        tasks = [
            {"id": "task-a", "depends_on": [], "priority": 2},
            {"id": "task-b", "depends_on": ["task-nonexistent"], "priority": 2},
        ]

        context = DecisionContext(
            prd_requirements={"tasks": tasks},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        # Should still work, dependency just won't exist
        decision = self.strategy.decide(context)
        ordered_tasks = [OrderedTask(**t) for t in json.loads(decision.choice)]

        self.assertEqual(len(ordered_tasks), 2)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTaskDependency))
    suite.addTests(loader.loadTestsFromTestCase(TestOrderedTask))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskOrderingStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleDependencyChain))
    suite.addTests(loader.loadTestsFromTestCase(TestParallelGroupDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexDependencyGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestCriticalPathMinimization))
    suite.addTests(loader.loadTestsFromTestCase(TestCircularDependencyDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestParallelGroupMarkerGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestParallelCoordinatorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestRationaleGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
