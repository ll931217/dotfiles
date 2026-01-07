#!/usr/bin/env python3
"""
Integration Tests for Subagent Coordination

Tests how SubagentFactory, SkillOrchestrator, and ParallelCoordinator
work together to coordinate autonomous implementation.
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from subagent_factory import SubagentFactory
from skill_orchestrator import SkillOrchestrator
from parallel_coordinator import ParallelCoordinator


class TestSubagentFactoryIntegration(unittest.TestCase):
    """Integration tests for SubagentFactory with real config files."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create subagent config
        subagent_config = """subagent_types:
  general-purpose:
    model: sonnet
    description: General purpose agent
    capabilities:
      - code_writing
      - debugging
      - analysis
  frontend:
    model: sonnet
    description: Frontend specialist
    capabilities:
      - react
      - typescript
      - css
"""
        config_path = self.project_root / ".claude" / "subagent-types.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(subagent_config)

        # Set environment variable for config path
        import os
        os.environ["SUBAGENT_TYPES_PATH"] = str(config_path)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_factory_detects_subagent_type(self):
        """Test that factory detects subagent type from description."""
        factory = SubagentFactory()

        # Detect subagent type for frontend task
        subagent_type = factory.detect_subagent_type(
            "Create React component for user profile with TypeScript"
        )

        # Should detect frontend specialist
        self.assertIsNotNone(subagent_type)

    def test_factory_detects_skill(self):
        """Test skill detection from task description."""
        factory = SubagentFactory()

        skill = factory.detect_skill(
            "Create responsive navigation bar with CSS Grid"
        )

        # May return None if no skill mapping exists, but should not crash
        # The type is Optional[str], so both None and str are valid
        self.assertTrue(skill is None or isinstance(skill, str))

    def test_factory_selects_subagent_from_metadata(self):
        """Test selecting subagent from task metadata."""
        factory = SubagentFactory()

        task_metadata = {
            "description": "Implement REST API endpoint for user authentication",
            "category": "backend",
            "priority": "high",
        }

        subagent_type = factory.select_subagent(task_metadata)

        # Should select appropriate subagent
        self.assertIsNotNone(subagent_type)

    def test_factory_gets_fallback_agents(self):
        """Test getting fallback agents for a subagent type."""
        factory = SubagentFactory()

        fallbacks = factory.get_fallback_agents("frontend")

        # Should return list of fallback agents
        self.assertIsInstance(fallbacks, list)

    def test_factory_creates_agent_config(self):
        """Test creating agent config for subagent."""
        factory = SubagentFactory()

        config = factory.create_agent_config(
            subagent_type="frontend",
            task_context={
                "description": "Create login form component",
                "category": "frontend",
            }
        )

        # Should return AgentConfig object
        self.assertIsNotNone(config)
        self.assertEqual(config.subagent_type, "frontend")


class TestSkillOrchestratorIntegration(unittest.TestCase):
    """Integration tests for SkillOrchestrator with project context."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create project structure
        (self.project_root / "src").mkdir(parents=True, exist_ok=True)
        (self.project_root / "src" / "auth.ts").write_text("export const login = () => {}")
        (self.project_root / "package.json").write_text('{"name": "test-project"}')

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_orchestrator_detects_applicable_skills(self):
        """Test detecting applicable skills from task metadata."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        task_description = "Create React login component with email validation"

        skills = orchestrator.detect_applicable_skills(
            task_description=task_description,
            task_category="frontend"
        )

        self.assertIsInstance(skills, list)
        # Should detect frontend-related skills

    def test_orchestrator_gets_available_skills(self):
        """Test getting list of available skills."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        skills = orchestrator.get_available_skills()

        self.assertIsInstance(skills, list)

    def test_orchestrator_gets_skill_info(self):
        """Test getting info for a specific skill."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        # Get skill info (skill may or may not exist)
        info = orchestrator.get_skill_info("frontend-design")

        # Should return None if skill doesn't exist, or dict if it does
        self.assertTrue(info is None or isinstance(info, dict))

    def test_orchestrator_manages_invocation_history(self):
        """Test invocation history tracking."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        # Initially empty
        history = orchestrator.get_invocation_history()
        self.assertIsInstance(history, list)

        # Clear history
        orchestrator.clear_invocation_history()
        history = orchestrator.get_invocation_history()
        self.assertEqual(len(history), 0)


class TestParallelCoordinatorIntegration(unittest.TestCase):
    """Integration tests for ParallelCoordinator with task execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.coordinator = ParallelCoordinator(repo_root=str(self.project_root))

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_coordinator_detects_parallel_groups(self):
        """Test detecting parallel groups from task markers."""
        tasks = [
            {"id": "1", "description": "[P:Group-infra] Setup database"},
            {"id": "2", "description": "[P:Group-infra] Setup cache"},
            {"id": "3", "description": "[P:Group-auth] Implement login"},
            {"id": "4", "description": "[P:Group-auth] Implement logout"},
            {"id": "5", "description": "Regular sequential task"},
        ]

        groups = self.coordinator.detect_groups(tasks)

        # Should detect 2 parallel groups
        self.assertIn("infra", groups)
        self.assertIn("auth", groups)
        self.assertEqual(len(groups["infra"]), 2)
        self.assertEqual(len(groups["auth"]), 2)

    def test_coordinator_lists_groups(self):
        """Test listing groups."""
        groups = self.coordinator.list_groups()

        self.assertIsInstance(groups, list)

    def test_coordinator_gets_group_by_id(self):
        """Test getting group metadata by ID."""
        # Non-existent group should return None
        group = self.coordinator.get_group("non-existent")

        self.assertIsNone(group)


class TestSubagentCoordinationWorkflow(unittest.TestCase):
    """Integration tests for complete subagent coordination workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create project structure
        (self.project_root / "src").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude").mkdir(parents=True, exist_ok=True)

        # Create subagent config
        subagent_config = """subagent_types:
  general-purpose:
    model: sonnet
    description: General purpose agent
  frontend:
    model: sonnet
    description: Frontend specialist
"""
        (self.project_root / ".claude" / "subagent-types.yaml").write_text(subagent_config)

        import os
        os.environ["SUBAGENT_TYPES_PATH"] = str(
            self.project_root / ".claude" / "subagent-types.yaml"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_workflow_factory_to_orchestrator(self):
        """Test workflow from factory to orchestrator."""
        factory = SubagentFactory()
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        # Detect subagent type for frontend task
        task_metadata = {
            "description": "Create React login component",
            "category": "frontend",
        }

        subagent_type = factory.select_subagent(task_metadata)
        self.assertIsNotNone(subagent_type)

        # Detect applicable skills
        skills = orchestrator.detect_applicable_skills(
            task_description=task_metadata["description"],
            task_category=task_metadata["category"]
        )
        self.assertIsInstance(skills, list)

    def test_workflow_parallel_task_delegation(self):
        """Test delegating parallel tasks to subagents."""
        coordinator = ParallelCoordinator(repo_root=str(self.project_root))
        factory = SubagentFactory()

        tasks = [
            {"id": "1", "description": "[P:Group-ui] Create button component"},
            {"id": "2", "description": "[P:Group-ui] Create input component"},
        ]

        # Detect parallel groups
        groups = coordinator.detect_groups(tasks)
        self.assertIn("ui", groups)

        # Select subagent for each task
        for task in groups["ui"]:
            subagent_type = factory.select_subagent(task)
            self.assertIsNotNone(subagent_type)

    def test_workflow_skill_detection_with_subagent(self):
        """Test detecting skills and selecting appropriate subagent."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))
        factory = SubagentFactory()

        task_metadata = {
            "description": "Create responsive navigation bar",
            "category": "frontend",
        }

        # Detect applicable skills
        skills = orchestrator.detect_applicable_skills(
            task_description=task_metadata["description"],
            task_category=task_metadata["category"]
        )
        self.assertIsInstance(skills, list)

        # Select appropriate subagent
        subagent_type = factory.select_subagent(task_metadata)
        self.assertIsNotNone(subagent_type)

    def test_workflow_factory_creates_configs_for_multiple_tasks(self):
        """Test creating agent configs for multiple different tasks."""
        factory = SubagentFactory()

        tasks = [
            {
                "id": "1",
                "description": "Create React component",
                "category": "frontend",
            },
            {
                "id": "2",
                "description": "Implement API endpoint",
                "category": "backend",
            },
        ]

        for task in tasks:
            subagent_type = factory.select_subagent(task)
            config = factory.create_agent_config(
                subagent_type=subagent_type,
                task_context=task,
            )

            self.assertIsNotNone(config)
            self.assertEqual(config.subagent_type, subagent_type)


class TestSubagentFactoryErrorHandling(unittest.TestCase):
    """Integration tests for error handling in subagent coordination."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_factory_handles_missing_config(self):
        """Test factory handles missing config file gracefully."""
        # Remove SUBAGENT_TYPES_PATH if set
        import os
        if "SUBAGENT_TYPES_PATH" in os.environ:
            del os.environ["SUBAGENT_TYPES_PATH"]

        factory = SubagentFactory()

        # Should use default config or handle gracefully
        subagent_type = factory.detect_subagent_type("Some task")
        self.assertIsNotNone(subagent_type)

    def test_orchestrator_handles_empty_task_metadata(self):
        """Test orchestrator handles empty task metadata gracefully."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        # Provide empty description
        skills = orchestrator.detect_applicable_skills("")

        # Should handle gracefully and return empty list
        self.assertIsInstance(skills, list)

    def test_coordinator_handles_mixed_task_descriptions(self):
        """Test coordinator handles mixed task descriptions."""
        coordinator = ParallelCoordinator(repo_root=str(self.project_root))

        tasks = [
            {"id": "1", "description": "[P:Group-test] Valid parallel task"},
            {"id": "2", "description": "Sequential task without marker"},
            {"id": "3", "description": "[P:Group-invalid"},  # Invalid marker
            {"id": "4", "description": "[P:Group-test] Another parallel task"},
        ]

        groups = coordinator.detect_groups(tasks)

        # Should still detect valid groups
        self.assertIn("test", groups)
        self.assertEqual(len(groups["test"]), 2)


class TestSkillOrchestratorIntegration(unittest.TestCase):
    """Additional integration tests for SkillOrchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_invocation_history_tracking(self):
        """Test that invocation history is tracked."""
        orchestrator = SkillOrchestrator(repo_root=str(self.project_root))

        # Initially empty
        history = orchestrator.get_invocation_history()
        initial_count = len(history)

        # Clear should work
        orchestrator.clear_invocation_history()
        history = orchestrator.get_invocation_history()
        self.assertEqual(len(history), 0)


if __name__ == "__main__":
    unittest.main()
