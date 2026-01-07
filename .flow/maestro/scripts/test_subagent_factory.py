#!/usr/bin/env python3
"""
Unit Tests for Subagent Factory

Tests task-to-subagent mapping, category detection, fallback handling,
and agent configuration generation.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from subagent_factory import (
    SubagentFactory,
    TaskCategoryParser,
    SubagentSelector,
    FallbackAgentHandler,
    SubagentConfig,
    SkillMapping,
    DetectionResult,
    AgentConfig
)


class TestTaskCategoryParser(unittest.TestCase):
    """Test task category parsing and keyword extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "detection_config": {
                "confidence_threshold": 0.6,
                "priority_order": ["security", "testing", "frontend", "backend"]
            }
        }
        self.parser = TaskCategoryParser(self.config)

    def test_extract_keywords_frontend(self):
        """Test keyword extraction for frontend tasks."""
        description = "Create React component for user profile with TypeScript"
        keywords = self.parser.extract_keywords(description)

        self.assertIn("react", keywords)
        self.assertIn("typescript", [k.lower() for k in keywords])
        self.assertIn("component", keywords)

    def test_extract_keywords_backend(self):
        """Test keyword extraction for backend tasks."""
        description = "Implement REST API endpoint for user authentication"
        keywords = self.parser.extract_keywords(description)

        self.assertIn("api", keywords)
        self.assertIn("endpoint", keywords)
        self.assertIn("authentication", [k.lower() for k in keywords])

    def test_extract_keywords_with_file_extensions(self):
        """Test keyword extraction with file extensions."""
        description = "Fix bug in user_service.py and add tests to test_auth.py"
        keywords = self.parser.extract_keywords(description)

        self.assertIn(".py", keywords)

    def test_categorize_task_with_ui(self):
        """Test task categorization for UI tasks."""
        description = "Build responsive UI component"
        metadata = {"files": []}
        result = self.parser.categorize_task(description, metadata)

        self.assertTrue(result["has_ui"])
        self.assertIn("ui", result["keywords"])

    def test_categorize_task_with_backend(self):
        """Test task categorization for backend tasks."""
        description = "Create API controller for user management"
        metadata = {"files": []}
        result = self.parser.categorize_task(description, metadata)

        self.assertTrue(result["has_backend"])
        self.assertIn("api", result["keywords"])

    def test_categorize_task_with_tests(self):
        """Test task categorization for testing tasks."""
        description = "Write unit tests for authentication module"
        metadata = {"files": []}
        result = self.parser.categorize_task(description, metadata)

        self.assertTrue(result["has_tests"])

    def test_categorize_task_with_file_extensions(self):
        """Test categorization extracts file extensions."""
        description = "Update authentication logic"
        metadata = {"files": ["user_service.py", "auth_controller.py"]}
        result = self.parser.categorize_task(description, metadata)

        self.assertIn(".py", result["extensions"])


class TestSubagentSelector(unittest.TestCase):
    """Test subagent selection logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.categories = {
            "frontend": {
                "subagent": "frontend-developer",
                "skill": "frontend-design",
                "patterns": ["component", "ui|interface", "react|vue|angular"],
                "fallback_agents": ["react-pro", "javascript-pro"]
            },
            "backend": {
                "subagent": "backend-architect",
                "patterns": ["api|endpoint", "service|controller", "database|schema"],
                "fallback_agents": ["api-documenter", "database-admin"]
            },
            "security": {
                "subagent": "security-auditor",
                "patterns": ["auth|authentication", "security|vulnerability", "jwt|oauth"],
                "fallback_agents": []
            },
            "default": {
                "subagent": "general-purpose",
                "fallback_agents": []
            }
        }

        self.config = {
            "detection_config": {
                "confidence_threshold": 0.6,
                "priority_order": ["security", "frontend", "backend", "default"]
            }
        }

        self.selector = SubagentSelector(self.categories, self.config)

    def test_match_patterns_high_confidence(self):
        """Test pattern matching with high confidence."""
        description = "Create React component for user interface"
        analysis = {
            "keywords": ["react", "component", "interface"],
            "extensions": []
        }
        patterns = ["component", "react", "ui|interface"]

        confidence, matches = self.selector.match_patterns(
            description,
            analysis,
            patterns
        )

        self.assertGreater(confidence, 0.5)
        self.assertGreater(len(matches), 0)

    def test_match_patterns_low_confidence(self):
        """Test pattern matching with low confidence."""
        description = "Write documentation for project"
        analysis = {
            "keywords": ["documentation", "project"],
            "extensions": []
        }
        patterns = ["component", "react", "api|endpoint"]

        confidence, matches = self.selector.match_patterns(
            description,
            analysis,
            patterns
        )

        self.assertLess(confidence, 0.5)

    def test_select_category_frontend(self):
        """Test category selection for frontend tasks."""
        description = "Create React component for user authentication UI"
        analysis = {
            "keywords": ["react", "component", "authentication", "ui"],
            "extensions": []
        }

        category, confidence, matches = self.selector.select_category(
            description,
            analysis
        )

        self.assertEqual(category, "frontend")
        self.assertGreater(confidence, 0.0)

    def test_select_category_backend(self):
        """Test category selection for backend tasks."""
        description = "Implement REST API endpoint for user management"
        analysis = {
            "keywords": ["api", "endpoint", "user", "management"],
            "extensions": []
        }

        category, confidence, matches = self.selector.select_category(
            description,
            analysis
        )

        self.assertEqual(category, "backend")

    def test_select_category_security_priority(self):
        """Test that security category takes priority."""
        description = "Implement secure authentication with JWT tokens for React app"
        analysis = {
            "keywords": ["authentication", "jwt", "security", "react", "app"],
            "extensions": []
        }

        category, confidence, matches = self.selector.select_category(
            description,
            analysis
        )

        # Security should be selected due to priority order
        self.assertEqual(category, "security")

    def test_select_subagent_frontend(self):
        """Test subagent selection for frontend tasks."""
        description = "Create Vue component for dashboard"
        metadata = {"files": ["DashboardComponent.vue"]}

        result = self.selector.select_subagent(description, metadata)

        self.assertEqual(result.subagent_type, "frontend-developer")
        self.assertEqual(result.category, "frontend")
        self.assertGreater(result.confidence, 0.0)

    def test_select_subagent_backend(self):
        """Test subagent selection for backend tasks."""
        description = "Create database schema for user management"
        metadata = {"files": ["user_service.py"]}

        result = self.selector.select_subagent(description, metadata)

        self.assertEqual(result.subagent_type, "backend-architect")
        self.assertEqual(result.category, "backend")

    def test_select_subagent_default(self):
        """Test subagent selection falls back to default."""
        description = "Write some documentation"
        metadata = {"files": []}

        result = self.selector.select_subagent(description, metadata)

        self.assertEqual(result.subagent_type, "general-purpose")
        self.assertEqual(result.category, "default")

    def test_fallback_agents_included(self):
        """Test that fallback agents are included in result."""
        description = "Create React component"
        metadata = {"files": []}

        result = self.selector.select_subagent(description, metadata)

        self.assertEqual(result.fallback_agents, ["react-pro", "javascript-pro"])


class TestFallbackAgentHandler(unittest.TestCase):
    """Test fallback agent handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.categories = {
            "frontend": {
                "subagent": "frontend-developer",
                "fallback_agents": ["react-pro", "javascript-pro", "typescript-pro"]
            },
            "backend": {
                "subagent": "backend-architect",
                "fallback_agents": ["api-documenter", "database-admin"]
            }
        }

        self.config = {
            "detection_config": {
                "max_fallback_attempts": 3
            }
        }

        self.handler = FallbackAgentHandler(self.categories, self.config)

    def test_get_fallback_agents_frontend(self):
        """Test getting fallback agents for frontend."""
        fallback_agents = self.handler.get_fallback_agents(
            "frontend-developer",
            "frontend"
        )

        self.assertEqual(
            fallback_agents,
            ["react-pro", "javascript-pro", "typescript-pro"]
        )

    def test_get_fallback_agents_backend(self):
        """Test getting fallback agents for backend."""
        fallback_agents = self.handler.get_fallback_agents(
            "backend-architect",
            "backend"
        )

        self.assertEqual(fallback_agents, ["api-documenter", "database-admin"])

    def test_get_fallback_agents_unknown_subagent(self):
        """Test getting fallback agents for unknown subagent."""
        fallback_agents = self.handler.get_fallback_agents(
            "unknown-agent",
            "unknown"
        )

        self.assertEqual(fallback_agents, [])

    def test_select_fallback_first_available(self):
        """Test selecting first available fallback agent."""
        available_agents = ["react-pro", "javascript-pro", "typescript-pro"]
        attempted_agents = []

        fallback = self.handler.select_fallback(
            "frontend-developer",
            "frontend",
            attempted_agents,
            available_agents
        )

        self.assertEqual(fallback, "react-pro")

    def test_select_fallback_skip_attempted(self):
        """Test selecting fallback skips already attempted agents."""
        available_agents = ["react-pro", "javascript-pro", "typescript-pro"]
        attempted_agents = ["react-pro"]

        fallback = self.handler.select_fallback(
            "frontend-developer",
            "frontend",
            attempted_agents,
            available_agents
        )

        self.assertEqual(fallback, "javascript-pro")

    def test_select_fallback_exhausted(self):
        """Test selecting fallback when all are exhausted."""
        available_agents = ["react-pro"]
        attempted_agents = ["react-pro"]

        fallback = self.handler.select_fallback(
            "frontend-developer",
            "frontend",
            attempted_agents,
            available_agents
        )

        self.assertIsNone(fallback)


class TestSubagentFactory(unittest.TestCase):
    """Test the main SubagentFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a mock config for testing
        self.mock_config = {
            "task_categories": {
                "frontend": {
                    "subagent": "frontend-developer",
                    "skill": "frontend-design",
                    "patterns": ["component", "ui|interface", "react|vue|angular"],
                    "fallback_agents": ["react-pro", "javascript-pro"]
                },
                "backend": {
                    "subagent": "backend-architect",
                    "patterns": ["api|endpoint", "service|controller"],
                    "fallback_agents": ["api-documenter"]
                },
                "default": {
                    "subagent": "general-purpose",
                    "fallback_agents": []
                }
            },
            "skill_mappings": {
                "frontend-design": {
                    "triggers": ["create.*ui", "build.*interface"],
                    "prompt_template": "Create UI for: {task_description}"
                }
            },
            "detection_config": {
                "confidence_threshold": 0.6,
                "priority_order": ["frontend", "backend", "default"],
                "max_fallback_attempts": 3
            }
        }

        # Create a temporary config file for testing
        import tempfile
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False
        )
        import yaml
        yaml.dump(self.mock_config, self.temp_file)
        self.temp_file.close()

        # Set environment variable to use temp config
        import os
        os.environ["SUBAGENT_TYPES_PATH"] = self.temp_file.name

        self.factory = SubagentFactory()

    def tearDown(self):
        """Clean up temporary files."""
        import os
        if "SUBAGENT_TYPES_PATH" in os.environ:
            del os.environ["SUBAGENT_TYPES_PATH"]

        import pathlib
        pathlib.Path(self.temp_file.name).unlink(missing_ok=True)

    def test_detect_subagent_type_frontend(self):
        """Test detecting subagent type for frontend task."""
        subagent_type = self.factory.detect_subagent_type(
            "Create React component for user interface"
        )

        self.assertEqual(subagent_type, "frontend-developer")

    def test_detect_subagent_type_backend(self):
        """Test detecting subagent type for backend task."""
        subagent_type = self.factory.detect_subagent_type(
            "Implement REST API endpoint"
        )

        self.assertEqual(subagent_type, "backend-architect")

    def test_detect_subagent_type_default(self):
        """Test detecting subagent type falls back to default."""
        subagent_type = self.factory.detect_subagent_type(
            "Write some documentation"
        )

        self.assertEqual(subagent_type, "general-purpose")

    def test_detect_skill_frontend_design(self):
        """Test skill detection for frontend design."""
        skill = self.factory.detect_skill("Create responsive UI component")

        self.assertEqual(skill, "frontend-design")

    def test_detect_skill_no_match(self):
        """Test skill detection returns None when no match."""
        skill = self.factory.detect_skill("Write some documentation")

        self.assertIsNone(skill)

    def test_select_subagent_from_metadata(self):
        """Test selecting subagent from task metadata."""
        metadata = {
            "description": "Create Vue component",
            "files": ["UserProfile.vue"],
            "dependencies": ["vue"]
        }

        subagent = self.factory.select_subagent(metadata)

        self.assertEqual(subagent, "frontend-developer")

    def test_detect_subagent_detailed(self):
        """Test detailed subagent detection."""
        result = self.factory.detect_subagent_detailed(
            "Create React component with TypeScript",
            {"files": ["Component.tsx"]}
        )

        self.assertEqual(result.subagent_type, "frontend-developer")
        self.assertEqual(result.category, "frontend")
        self.assertGreater(result.confidence, 0.0)
        self.assertEqual(result.skill, "frontend-design")

    def test_get_fallback_agents(self):
        """Test getting fallback agents."""
        fallback_agents = self.factory.get_fallback_agents("frontend-developer")

        self.assertEqual(fallback_agents, ["react-pro", "javascript-pro"])

    def test_create_agent_config_frontend(self):
        """Test creating agent config for frontend task."""
        task_context = {
            "description": "Create UI component",
            "prd": "Build user management system",
            "code_patterns": "Component-based architecture",
            "confidence": 0.8,
            "matched_patterns": ["component"]
        }

        config = self.factory.create_agent_config(
            "frontend-developer",
            task_context
        )

        self.assertEqual(config.subagent_type, "frontend-developer")
        self.assertIn("frontend-developer", config.system_prompt)
        self.assertIsNotNone(config.skill_config)
        self.assertEqual(config.skill_config["name"], "frontend-design")
        self.assertEqual(config.fallback_chain, ["react-pro", "javascript-pro"])

    def test_create_agent_config_backend(self):
        """Test creating agent config for backend task."""
        task_context = {
            "description": "Implement API endpoint",
            "prd": "Build REST API"
        }

        config = self.factory.create_agent_config(
            "backend-architect",
            task_context
        )

        self.assertEqual(config.subagent_type, "backend-architect")
        self.assertIn("backend-architect", config.system_prompt)
        self.assertIsNone(config.skill_config)
        self.assertEqual(config.fallback_chain, ["api-documenter"])

    def test_system_prompt_includes_prd(self):
        """Test system prompt includes PRD context."""
        task_context = {
            "description": "Create component",
            "prd": "This is the PRD content for the project"
        }

        config = self.factory.create_agent_config(
            "frontend-developer",
            task_context
        )

        self.assertIn("PRD Context:", config.system_prompt)
        self.assertIn("This is the PRD content", config.system_prompt)

    def test_skill_prompt_formatting(self):
        """Test skill prompt is formatted correctly."""
        task_context = {
            "description": "Create user interface",
            "prd": "Build UI system",
            "existing_patterns": "Atomic design"
        }

        config = self.factory.create_agent_config(
            "frontend-developer",
            task_context
        )

        self.assertIsNotNone(config.skill_config)
        self.assertIn("Create UI for: Create user interface", config.skill_config["prompt"])


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = {
            "task_categories": {
                "frontend": {
                    "subagent": "frontend-developer",
                    "skill": "frontend-design",
                    "patterns": ["component", "ui|interface", "react|vue|angular"],
                    "fallback_agents": ["react-pro"]
                },
                "backend": {
                    "subagent": "backend-architect",
                    "patterns": ["api|endpoint", "service|controller"],
                    "fallback_agents": ["api-documenter"]
                },
                "default": {
                    "subagent": "general-purpose",
                    "fallback_agents": []
                }
            },
            "skill_mappings": {
                "frontend-design": {
                    "triggers": ["create.*ui", "build.*interface"],
                    "prompt_template": "Create UI for: {task_description}"
                }
            },
            "detection_config": {
                "confidence_threshold": 0.6,
                "priority_order": ["frontend", "backend", "default"],
                "max_fallback_attempts": 3
            }
        }

        # Create a temporary config file for testing
        import tempfile
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False
        )
        import yaml
        yaml.dump(self.mock_config, self.temp_file)
        self.temp_file.close()

        # Set environment variable to use temp config
        import os
        os.environ["SUBAGENT_TYPES_PATH"] = self.temp_file.name

        self.factory = SubagentFactory()

    def tearDown(self):
        """Clean up temporary files."""
        import os
        if "SUBAGENT_TYPES_PATH" in os.environ:
            del os.environ["SUBAGENT_TYPES_PATH"]

        import pathlib
        pathlib.Path(self.temp_file.name).unlink(missing_ok=True)

    def test_complete_workflow_frontend(self):
        """Test complete workflow for frontend task."""
        task_description = "Create React component for user profile interface"
        task_metadata = {
            "description": task_description,
            "files": ["UserProfile.tsx"],
            "dependencies": ["react", "typescript"]
        }

        # Detect subagent
        subagent = self.factory.detect_subagent_type(task_description)
        self.assertEqual(subagent, "frontend-developer")

        # Detailed detection
        result = self.factory.detect_subagent_detailed(task_description, task_metadata)
        self.assertEqual(result.subagent_type, "frontend-developer")
        self.assertEqual(result.skill, "frontend-design")

        # Create agent config
        config = self.factory.create_agent_config(subagent, {
            "description": task_description,
            "confidence": result.confidence,
            "matched_patterns": result.matched_patterns
        })

        self.assertEqual(config.subagent_type, "frontend-developer")
        self.assertIsNotNone(config.skill_config)

    def test_complete_workflow_backend(self):
        """Test complete workflow for backend task."""
        task_description = "Implement REST API service for user authentication"
        task_metadata = {
            "description": task_description,
            "files": ["auth_service.py"],
            "dependencies": ["fastapi", "sqlalchemy"]
        }

        # Detect subagent
        subagent = self.factory.detect_subagent_type(task_description)
        self.assertEqual(subagent, "backend-architect")

        # Detailed detection
        result = self.factory.detect_subagent_detailed(task_description, task_metadata)
        self.assertEqual(result.subagent_type, "backend-architect")

        # Create agent config
        config = self.factory.create_agent_config(subagent, {
            "description": task_description,
            "confidence": result.confidence
        })

        self.assertEqual(config.subagent_type, "backend-architect")

    def test_fallback_workflow(self):
        """Test fallback agent workflow."""
        task_description = "Create React component"

        # Get fallback agents
        fallback_agents = self.factory.get_fallback_agents("frontend-developer")
        self.assertEqual(fallback_agents, ["react-pro"])

        # Simulate primary agent failure and select fallback
        result = self.factory.detect_subagent_detailed(task_description)

        # Fallback handler would use these
        self.assertEqual(result.fallback_agents, ["react-pro"])


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
