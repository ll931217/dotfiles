#!/usr/bin/env python3
"""
Unit tests for Parallel Execution Coordinator

Tests the four-phase workflow for [P:Group-X] parallel task execution.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from parallel_coordinator import (
    ParallelCoordinator,
    GroupMetadata,
    TaskMetadata,
    GroupPhase,
    TaskStatus,
)


class TestParallelGroupDetection(unittest.TestCase):
    """Test group detection from [P:Group-X] markers."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_detect_single_group(self):
        """Test detecting a single parallel group."""
        tasks = [
            {"id": "task-1", "description": "[P:Group-infra] Setup database"},
            {"id": "task-2", "description": "[P:Group-infra] Setup cache"},
        ]

        groups = self.coordinator.detect_groups(tasks)

        self.assertIn("infra", groups)
        self.assertEqual(len(groups["infra"]), 2)
        self.assertNotIn("_sequential", groups)

    def test_detect_multiple_groups(self):
        """Test detecting multiple parallel groups."""
        tasks = [
            {"id": "task-1", "description": "[P:Group-infra] Setup database"},
            {"id": "task-2", "description": "[P:Group-infra] Setup cache"},
            {"id": "task-3", "description": "[P:Group-auth] Implement login"},
            {"id": "task-4", "description": "[P:Group-auth] Implement logout"},
        ]

        groups = self.coordinator.detect_groups(tasks)

        self.assertEqual(len(groups), 2)
        self.assertIn("infra", groups)
        self.assertIn("auth", groups)
        self.assertEqual(len(groups["infra"]), 2)
        self.assertEqual(len(groups["auth"]), 2)

    def test_detect_mixed_sequential_and_parallel(self):
        """Test detecting mixed sequential and parallel tasks."""
        tasks = [
            {"id": "task-1", "description": "[P:Group-infra] Setup database"},
            {"id": "task-2", "description": "[P:Group-infra] Setup cache"},
            {"id": "task-3", "description": "Sequential task without group"},
            {"id": "task-4", "description": "Another sequential task"},
        ]

        groups = self.coordinator.detect_groups(tasks)

        self.assertIn("infra", groups)
        self.assertIn("_sequential", groups)
        self.assertEqual(len(groups["infra"]), 2)
        self.assertEqual(len(groups["_sequential"]), 2)

    def test_detect_all_sequential(self):
        """Test detecting all sequential tasks (no groups)."""
        tasks = [
            {"id": "task-1", "description": "First sequential task"},
            {"id": "task-2", "description": "Second sequential task"},
        ]

        groups = self.coordinator.detect_groups(tasks)

        self.assertIn("_sequential", groups)
        self.assertEqual(len(groups["_sequential"]), 2)
        self.assertEqual(len(groups), 1)  # Only _sequential

    def test_group_pattern_variations(self):
        """Test various [P:Group-X] marker formats."""
        tasks = [
            {"id": "task-1", "description": "[P:Group-testcase1] Task 1"},
            {"id": "task-2", "description": "[P:Group-TEST_CASE_2] Task 2"},
            {"id": "task-3", "description": "[P:Group-test_case_3] Task 3"},
        ]

        groups = self.coordinator.detect_groups(tasks)

        # Note: The regex captures word characters only, so hyphens don't match
        self.assertIn("testcase1", groups)
        self.assertIn("TEST_CASE_2", groups)
        self.assertIn("test_case_3", groups)


class TestTaskMetadataExtraction(unittest.TestCase):
    """Test task metadata extraction from beads issues."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_extract_basic_metadata(self):
        """Test extracting basic task metadata."""
        task = {
            "id": "proj-auth.1",
            "title": "Implement login endpoint",
            "description": "Create login POST endpoint with JWT authentication",
        }

        metadata = self.coordinator._extract_task_metadata(task)

        self.assertEqual(metadata.task_id, "proj-auth.1")
        self.assertEqual(metadata.title, "Implement login endpoint")
        self.assertIn("login POST endpoint", metadata.description)

    def test_extract_relevant_files(self):
        """Test extracting file paths from descriptions."""
        descriptions = [
            "Implement src/components/Login.tsx with TypeScript",
            "Create tests for src/services/AuthService.ts",
            "Update package.json and tsconfig.json",
        ]

        for desc in descriptions:
            files = self.coordinator._extract_relevant_files(desc)
            self.assertGreater(len(files), 0, f"No files found in: {desc}")

    def test_extract_files_with_markers(self):
        """Test extracting files with explicit markers."""
        description = """
        Implement authentication flow:
        - file: src/api/routes.ts
        - path: src/services/AuthService.ts
        - location: src/types/auth.ts
        """

        files = self.coordinator._extract_relevant_files(description)

        self.assertIn("src/api/routes.ts", files)
        self.assertIn("src/services/AuthService.ts", files)
        self.assertIn("src/types/auth.ts", files)


class TestSubagentDetection(unittest.TestCase):
    """Test automatic subagent detection based on task descriptions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_detect_backend_architect(self):
        """Test detecting backend-architect subagent."""
        task_meta = TaskMetadata(
            task_id="task-1",
            title="API Design",
            description="Design RESTful API endpoints for user management",
        )

        subagent = self.coordinator._auto_detect_subagent(task_meta)

        self.assertEqual(subagent, "backend-architect")

    def test_detect_frontend_developer(self):
        """Test detecting frontend-developer subagent."""
        task_meta = TaskMetadata(
            task_id="task-2",
            title="UI Component",
            description="Create React components for user interface with CSS",
        )

        subagent = self.coordinator._auto_detect_subagent(task_meta)

        self.assertEqual(subagent, "frontend-developer")

    def test_detect_test_automator(self):
        """Test detecting test-automator subagent."""
        task_meta = TaskMetadata(
            task_id="task-3",
            title="Test Suite",
            description="Write comprehensive pytest tests with coverage",
        )

        subagent = self.coordinator._auto_detect_subagent(task_meta)

        self.assertEqual(subagent, "test-automator")

    def test_detect_security_auditor(self):
        """Test detecting security-auditor subagent."""
        task_meta = TaskMetadata(
            task_id="task-4",
            title="Security Review",
            description="Audit authentication system for vulnerabilities",
        )

        subagent = self.coordinator._auto_detect_subagent(task_meta)

        self.assertEqual(subagent, "security-auditor")

    def test_default_subagent(self):
        """Test default subagent for unclear descriptions."""
        task_meta = TaskMetadata(
            task_id="task-5",
            title="Generic Task",
            description="Do something generic",
        )

        subagent = self.coordinator._auto_detect_subagent(task_meta)

        self.assertEqual(subagent, "backend-architect")  # Default


class TestDependencyChecking(unittest.TestCase):
    """Test dependency blocking detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_no_dependencies(self):
        """Test task with no dependencies."""
        task_meta = TaskMetadata(
            task_id="task-1",
            title="Independent Task",
            description="Task with no dependencies",
            dependencies=[],
        )

        is_blocked = self.coordinator._check_dependencies_blocked(task_meta)

        self.assertFalse(is_blocked)

    @patch.object(ParallelCoordinator, '_get_beads_issue')
    def test_blocking_dependency_open(self, mock_get_issue):
        """Test task with blocking open dependency."""
        mock_get_issue.return_value = {"status": "open"}

        task_meta = TaskMetadata(
            task_id="task-2",
            title="Dependent Task",
            description="Task with open dependency",
            dependencies=["dep-1"],
        )

        is_blocked = self.coordinator._check_dependencies_blocked(task_meta)

        self.assertTrue(is_blocked)

    @patch.object(ParallelCoordinator, '_get_beads_issue')
    def test_non_blocking_dependency_closed(self, mock_get_issue):
        """Test task with closed (non-blocking) dependency."""
        mock_get_issue.return_value = {"status": "closed"}

        task_meta = TaskMetadata(
            task_id="task-3",
            title="Dependent Task",
            description="Task with closed dependency",
            dependencies=["dep-1"],
        )

        is_blocked = self.coordinator._check_dependencies_blocked(task_meta)

        self.assertFalse(is_blocked)


class TestGroupExecutionPhases(unittest.TestCase):
    """Test the four-phase group execution workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_phase_pre_execution(self):
        """Test Phase 1: Pre-execution analysis."""
        group_tasks = [
            {"id": "task-1", "description": "[P:Group-test] Task 1"},
            {"id": "task-2", "description": "[P:Group-test] Task 2"},
        ]

        group_metadata = GroupMetadata(
            group_id="test",
            group_name="Test Group",
            phase=GroupPhase.PRE_EXECUTION,
            tasks=["task-1", "task-2"],
            created_at=self.coordinator._current_timestamp(),
        )

        # Mock context refresh
        with patch.object(self.coordinator, 'refresh_context_before_group') as mock_refresh:
            mock_refresh.return_value = True

            self.coordinator._phase_pre_execution(group_metadata, group_tasks)

            # Verify pre-group refresh was called
            mock_refresh.assert_called_once()

            # Verify phase transition
            self.assertEqual(group_metadata.phase, GroupPhase.CONCURRENT_EXECUTION)
            self.assertIsNotNone(group_metadata.started_at)

    def test_phase_concurrent_execution(self):
        """Test Phase 2: Concurrent execution."""
        group_tasks = [
            {"id": "task-1", "description": "[P:Group-test] Implement API endpoint"},
        ]

        group_metadata = GroupMetadata(
            group_id="test",
            group_name="Test Group",
            phase=GroupPhase.CONCURRENT_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            started_at=self.coordinator._current_timestamp(),
        )

        self.coordinator._phase_concurrent_execution(group_metadata, group_tasks)

        # Verify results were added
        self.assertEqual(len(group_metadata.results), 1)
        self.assertEqual(group_metadata.results[0]["task_id"], "task-1")
        self.assertIn("subagent", group_metadata.results[0])

    def test_phase_coordination(self):
        """Test Phase 3: Coordination & monitoring."""
        group_metadata = GroupMetadata(
            group_id="test",
            group_name="Test Group",
            phase=GroupPhase.CONCURRENT_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            started_at=self.coordinator._current_timestamp(),
            results=[
                {
                    "task_id": "task-1",
                    "status": "in_progress",
                    "started_at": self.coordinator._current_timestamp(),
                }
            ],
        )

        self.coordinator._phase_coordination(group_metadata)

        # Verify all tasks marked as completed
        self.assertEqual(group_metadata.results[0]["status"], "completed")
        self.assertIsNotNone(group_metadata.results[0].get("completed_at"))
        self.assertEqual(group_metadata.phase, GroupPhase.POST_EXECUTION)

    @patch.object(ParallelCoordinator, '_run_test_suite')
    @patch.object(ParallelCoordinator, '_close_beads_task')
    def test_phase_post_execution(self, mock_close, mock_tests):
        """Test Phase 4: Post-execution validation."""
        mock_tests.return_value = True
        mock_close.return_value = True

        group_metadata = GroupMetadata(
            group_id="test",
            group_name="Test Group",
            phase=GroupPhase.POST_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            started_at=self.coordinator._current_timestamp(),
            results=[
                {
                    "task_id": "task-1",
                    "status": "completed",
                    "started_at": self.coordinator._current_timestamp(),
                    "completed_at": self.coordinator._current_timestamp(),
                }
            ],
        )

        # Should not raise exception
        self.coordinator._phase_post_execution(group_metadata)

        # Verify tests were run
        mock_tests.assert_called_once()

        # Verify tasks were closed
        mock_close.assert_called_once_with("task-1")

    @patch.object(ParallelCoordinator, '_run_test_suite')
    @patch.object(ParallelCoordinator, '_close_beads_task')
    def test_phase_post_execution_with_failures(self, mock_close, mock_tests):
        """Test Phase 4 with failed tasks."""
        mock_tests.return_value = True

        group_metadata = GroupMetadata(
            group_id="test",
            group_name="Test Group",
            phase=GroupPhase.POST_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            started_at=self.coordinator._current_timestamp(),
            results=[
                {
                    "task_id": "task-1",
                    "status": "failed",
                    "started_at": self.coordinator._current_timestamp(),
                }
            ],
        )

        # Should raise exception for failed tasks
        with self.assertRaises(ValueError):
            self.coordinator._phase_post_execution(group_metadata)


class TestGroupPersistence(unittest.TestCase):
    """Test group metadata persistence and retrieval."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_save_and_load_group_metadata(self):
        """Test saving and loading group metadata."""
        original_metadata = GroupMetadata(
            group_id="test-group",
            group_name="Test Group",
            phase=GroupPhase.PRE_EXECUTION,
            tasks=["task-1", "task-2"],
            created_at="2024-01-01T00:00:00Z",
            started_at="2024-01-01T00:01:00Z",
            completed_at="2024-01-01T00:05:00Z",
            status=TaskStatus.COMPLETED,
            results=[{"task_id": "task-1", "status": "completed"}],
            errors=["error-1"],
            pre_group_refresh_completed=True,
        )

        # Save metadata
        self.coordinator._save_group_metadata(original_metadata)

        # Load metadata
        loaded_metadata = self.coordinator.get_group("test-group")

        self.assertIsNotNone(loaded_metadata)
        self.assertEqual(loaded_metadata.group_id, "test-group")
        self.assertEqual(loaded_metadata.group_name, "Test Group")
        self.assertEqual(loaded_metadata.phase, GroupPhase.PRE_EXECUTION)
        self.assertEqual(loaded_metadata.status, TaskStatus.COMPLETED)
        self.assertEqual(len(loaded_metadata.tasks), 2)
        self.assertEqual(len(loaded_metadata.results), 1)
        self.assertEqual(len(loaded_metadata.errors), 1)
        self.assertTrue(loaded_metadata.pre_group_refresh_completed)

    def test_list_groups(self):
        """Test listing all groups."""
        # Create multiple groups
        for i in range(3):
            metadata = GroupMetadata(
                group_id=f"group-{i}",
                group_name=f"Group {i}",
                phase=GroupPhase.PRE_EXECUTION,
                tasks=[f"task-{i}"],
                created_at=self.coordinator._current_timestamp(),
                status=TaskStatus.PENDING,
            )
            self.coordinator._save_group_metadata(metadata)

        # List all groups
        all_groups = self.coordinator.list_groups()

        self.assertEqual(len(all_groups), 3)

        # List by status
        pending_groups = self.coordinator.list_groups(status=TaskStatus.PENDING)
        self.assertEqual(len(pending_groups), 3)

        completed_groups = self.coordinator.list_groups(status=TaskStatus.COMPLETED)
        self.assertEqual(len(completed_groups), 0)

    def test_get_nonexistent_group(self):
        """Test retrieving a non-existent group."""
        group = self.coordinator.get_group("nonexistent")
        self.assertIsNone(group)


class TestContextRefresh(unittest.TestCase):
    """Test pre-group context refresh via /flow:summary."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    @patch('subprocess.run')
    def test_successful_context_refresh(self, mock_run):
        """Test successful context refresh."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Summary output...",
            stderr="",
        )

        success = self.coordinator.refresh_context_before_group()

        self.assertTrue(success)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_failed_context_refresh(self, mock_run):
        """Test failed context refresh."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error message",
        )

        success = self.coordinator.refresh_context_before_group()

        self.assertFalse(success)

    @patch('subprocess.run')
    def test_timeout_context_refresh(self, mock_run):
        """Test context refresh with timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("claude", 120)

        success = self.coordinator.refresh_context_before_group()

        self.assertFalse(success)


class TestWaitForCompletion(unittest.TestCase):
    """Test waiting for group completion."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    def test_wait_for_completed_group(self):
        """Test waiting for already completed group."""
        metadata = GroupMetadata(
            group_id="test-group",
            group_name="Test",
            phase=GroupPhase.POST_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            status=TaskStatus.COMPLETED,
            completed_at=self.coordinator._current_timestamp(),
        )
        self.coordinator._save_group_metadata(metadata)

        success = self.coordinator.wait_for_group_completion("test-group", timeout_seconds=1)

        self.assertTrue(success)

    def test_wait_for_failed_group(self):
        """Test waiting for failed group."""
        metadata = GroupMetadata(
            group_id="test-group",
            group_name="Test",
            phase=GroupPhase.POST_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            status=TaskStatus.FAILED,
            completed_at=self.coordinator._current_timestamp(),
        )
        self.coordinator._save_group_metadata(metadata)

        success = self.coordinator.wait_for_group_completion("test-group", timeout_seconds=1)

        self.assertFalse(success)

    def test_wait_timeout(self):
        """Test timeout when waiting for group."""
        metadata = GroupMetadata(
            group_id="test-group",
            group_name="Test",
            phase=GroupPhase.CONCURRENT_EXECUTION,
            tasks=["task-1"],
            created_at=self.coordinator._current_timestamp(),
            status=TaskStatus.IN_PROGRESS,
        )
        self.coordinator._save_group_metadata(metadata)

        success = self.coordinator.wait_for_group_completion(
            "test-group",
            timeout_seconds=2  # Short timeout
        )

        self.assertFalse(success)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.coordinator = ParallelCoordinator(repo_root=self.temp_dir)

    @patch.object(ParallelCoordinator, 'refresh_context_before_group')
    @patch.object(ParallelCoordinator, '_run_test_suite')
    @patch.object(ParallelCoordinator, '_close_beads_task')
    def test_execute_simple_group(self, mock_close, mock_tests, mock_refresh):
        """Test executing a simple parallel group."""
        mock_refresh.return_value = True
        mock_tests.return_value = True
        mock_close.return_value = True

        group_tasks = [
            {"id": "task-1", "description": "[P:Group-test] Task 1"},
            {"id": "task-2", "description": "[P:Group-test] Task 2"},
        ]

        result = self.coordinator.execute_parallel_group(group_tasks, "test")

        self.assertEqual(result.group_id, "test")
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.completed_at)
        self.assertEqual(len(result.results), 2)

    def test_detect_and_execute_workflow(self):
        """Test complete detect-then-execute workflow."""
        tasks = [
            {"id": "task-1", "description": "[P:Group-infra] Setup database"},
            {"id": "task-2", "description": "[P:Group-infra] Setup cache"},
            {"id": "task-3", "description": "Sequential task"},
        ]

        # Detect groups
        groups = self.coordinator.detect_groups(tasks)

        self.assertIn("infra", groups)
        self.assertIn("_sequential", groups)

        # Verify parallel group detected correctly
        self.assertEqual(len(groups["infra"]), 2)
        self.assertEqual(len(groups["_sequential"]), 1)


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParallelGroupDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskMetadataExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestSubagentDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestDependencyChecking))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupExecutionPhases))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupPersistence))
    suite.addTests(loader.loadTestsFromTestCase(TestContextRefresh))
    suite.addTests(loader.loadTestsFromTestCase(TestWaitForCompletion))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    import sys
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
