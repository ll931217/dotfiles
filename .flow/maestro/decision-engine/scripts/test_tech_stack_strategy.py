#!/usr/bin/env python3
"""
Comprehensive tests for TechStackStrategy.

Tests autonomous technology stack selection across domains,
categories, and decision hierarchy application.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from decision_strategy import DecisionContext, Decision
from tech_stack_strategy import TechStackStrategy, DOMAIN_BEST_PRACTICES


class TestTechStackStrategyInit(unittest.TestCase):
    """Test TechStackStrategy initialization."""

    def test_init_without_project_root(self):
        """Test initialization without project root."""
        strategy = TechStackStrategy()
        self.assertIsNotNone(strategy)
        self.assertIsNone(strategy.project_root)
        self.assertIsNone(strategy._dependencies)
        self.assertIsNone(strategy._patterns)

    def test_init_with_project_root(self):
        """Test initialization with project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy = TechStackStrategy(tmpdir)
            self.assertIsNotNone(strategy)
            self.assertEqual(strategy.project_root, Path(tmpdir))


class TestStrategyMetadata(unittest.TestCase):
    """Test strategy metadata methods."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_strategy_name(self):
        """Test getting strategy name."""
        self.assertEqual(self.strategy.get_strategy_name(), "tech_stack_autonomous")

    def test_strategy_description(self):
        """Test getting strategy description."""
        desc = self.strategy.get_strategy_description()
        self.assertIn("autonomous", desc.lower())
        self.assertIn("best practices", desc.lower())
        self.assertIn("existing patterns", desc.lower())

    def test_supported_decision_types(self):
        """Test getting supported decision types."""
        types = self.strategy.get_supported_decision_types()
        self.assertIn("tech_stack", types)
        self.assertIn("language", types)
        self.assertIn("framework", types)
        self.assertIn("database", types)
        self.assertIn("frontend", types)
        self.assertIn("backend", types)


class TestDomainDetection(unittest.TestCase):
    """Test problem domain detection from PRD requirements."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_detect_web_api_domain(self):
        """Test detecting web API domain."""
        prd_reqs = {
            "feature": "REST API",
            "requirements": ["Build RESTful endpoints", "JSON responses"]
        }
        domain = self.strategy._detect_domain(prd_reqs)
        self.assertEqual(domain, "web_api")

    def test_detect_web_ui_domain(self):
        """Test detecting web UI domain."""
        prd_reqs = {
            "feature": "User interface",
            "requirements": ["Build responsive UI", "Dashboard components"]
        }
        domain = self.strategy._detect_domain(prd_reqs)
        self.assertEqual(domain, "web_ui")

    def test_detect_cli_tool_domain(self):
        """Test detecting CLI tool domain."""
        prd_reqs = {
            "feature": "Command line tool",
            "requirements": ["Terminal interface", "Command processing"]
        }
        domain = self.strategy._detect_domain(prd_reqs)
        self.assertEqual(domain, "cli_tool")

    def test_detect_full_stack_domain(self):
        """Test detecting full-stack domain."""
        prd_reqs = {
            "feature": "Complete application",
            "requirements": ["Full stack development", "End-to-end features"]
        }
        domain = self.strategy._detect_domain(prd_reqs)
        self.assertEqual(domain, "full_stack")

    def test_default_domain(self):
        """Test default domain when no keywords match."""
        prd_reqs = {"feature": "Generic feature"}
        domain = self.strategy._detect_domain(prd_reqs)
        self.assertEqual(domain, "web_api")


class TestCategoryDetection(unittest.TestCase):
    """Test technology category detection."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_detect_language_category(self):
        """Test detecting language category."""
        prd_reqs = {"feature": "Choose programming language"}
        category = self.strategy._detect_category(prd_reqs, "web_api")
        self.assertEqual(category, "language")

    def test_detect_frontend_category(self):
        """Test detecting frontend category."""
        prd_reqs = {"feature": "Build UI components"}
        category = self.strategy._detect_category(prd_reqs, "web_ui")
        self.assertEqual(category, "frontend_framework")

    def test_detect_backend_category(self):
        """Test detecting backend category."""
        prd_reqs = {"feature": "API server"}
        category = self.strategy._detect_category(prd_reqs, "web_api")
        self.assertEqual(category, "backend_framework")

    def test_explicit_category(self):
        """Test explicit category specification."""
        prd_reqs = {"category": "database"}
        category = self.strategy._detect_category(prd_reqs, "web_api")
        self.assertEqual(category, "database")

    def test_domain_based_default(self):
        """Test domain-based default category."""
        prd_reqs = {"feature": "API"}
        category = self.strategy._detect_category(prd_reqs, "web_api")
        self.assertEqual(category, "backend_framework")


class TestScoringCriteria(unittest.TestCase):
    """Test scoring criteria application."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_score_best_practices_web_api(self):
        """Test best practices scoring for web API."""
        option = {"name": "FastAPI"}
        tech_data = {
            "category": "backend_framework",
            "ecosystem": "python",
            "best_practice_rank": 2,
        }
        score = self.strategy._score_best_practices(option, tech_data, "web_api")

        # FastAPI is a best practice for web_api (rank 2)
        self.assertGreater(score, 0.7)
        self.assertLessEqual(score, 1.0)

    def test_score_best_practices_web_ui(self):
        """Test best practices scoring for web UI."""
        option = {"name": "React"}
        tech_data = {
            "category": "frontend_framework",
            "ecosystem": "nodejs",
            "best_practice_rank": 1,
        }
        score = self.strategy._score_best_practices(option, tech_data, "web_ui")

        # React is a top best practice for web_ui
        self.assertEqual(score, 1.0)

    def test_score_existing_patterns_with_match(self):
        """Test existing patterns scoring with match."""
        strategy = TechStackStrategy()
        strategy._dependencies = {"express": "^4.18.0"}

        option = {"name": "Express"}
        tech_data = {
            "category": "backend_framework",
            "ecosystem": "nodejs",
            "detect_patterns": ["express", "express()"],
        }
        score = strategy._score_existing_patterns(option, tech_data)
        self.assertEqual(score, 1.0)  # Perfect match

    def test_score_existing_patterns_without_match(self):
        """Test existing patterns scoring without match."""
        strategy = TechStackStrategy()
        strategy._dependencies = {}

        option = {"name": "Express"}
        tech_data = {
            "category": "backend_framework",
            "ecosystem": "nodejs",
            "detect_patterns": ["express", "express()"],
        }
        score = self.strategy._score_existing_patterns(option, tech_data)
        self.assertEqual(score, 0.5)  # Neutral

    def test_score_simplicity_simple_tech(self):
        """Test simplicity scoring for simple technology."""
        option = {"name": "Flask"}
        tech_data = {"category": "backend_framework"}
        score = self.strategy._score_simplicity(option, tech_data)
        self.assertEqual(score, 1.0)  # Flask is simple

    def test_score_simplicity_complex_tech(self):
        """Test simplicity scoring for complex technology."""
        option = {"name": "Django"}
        tech_data = {"category": "backend_framework"}
        score = self.strategy._score_simplicity(option, tech_data)
        self.assertLess(score, 1.0)  # Django is more complex

    def test_score_consistency_with_match(self):
        """Test consistency scoring with match."""
        option = {"name": "FastAPI"}
        tech_data = {"category": "backend_framework", "ecosystem": "python"}

        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={"language": "python"},
            available_options=[],
            constraints={},
            session_id="test",
        )

        score = self.strategy._score_consistency(option, tech_data, context)
        self.assertEqual(score, 1.0)  # Perfect consistency

    def test_score_consistency_without_match(self):
        """Test consistency scoring without match."""
        option = {"name": "FastAPI"}
        tech_data = {"category": "backend_framework", "ecosystem": "python"}

        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={"language": "javascript"},
            available_options=[],
            constraints={},
            session_id="test",
        )

        score = self.strategy._score_consistency(option, tech_data, context)
        self.assertEqual(score, 0.5)  # Neutral


class TestDecisionMaking(unittest.TestCase):
    """Test main decision-making logic."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_decide_web_api_selects_framework(self):
        """Test web API domain selects backend framework."""
        context = DecisionContext(
            prd_requirements={"feature": "REST API"},
            current_state={},
            available_options=[],  # Auto-populate from knowledge base
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIsInstance(decision, Decision)
        self.assertIn(decision.choice, ["Express", "FastAPI", "Django", "Flask"])
        self.assertGreaterEqual(decision.confidence, 0.4)
        self.assertEqual(decision.decision_type, "tech_stack")

    def test_decide_web_ui_selects_framework(self):
        """Test web UI domain selects frontend framework."""
        context = DecisionContext(
            prd_requirements={"feature": "Dashboard UI"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIsInstance(decision, Decision)
        self.assertIn(decision.choice, ["React", "Vue", "Svelte"])
        self.assertGreater(decision.confidence, 0.5)

    def test_decide_cli_tool_selects_framework(self):
        """Test CLI tool domain selects CLI framework."""
        context = DecisionContext(
            prd_requirements={"feature": "Command line tool"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIsInstance(decision, Decision)
        self.assertIn(decision.choice, ["Click", "Typer", "Commander", "clap"])

    def test_decide_with_explicit_category(self):
        """Test decision with explicit category."""
        context = DecisionContext(
            prd_requirements={"feature": "Storage", "category": "database"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIsInstance(decision, Decision)
        self.assertIn(decision.choice, ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite"])

    def test_decide_with_existing_codebase(self):
        """Test decision with existing codebase patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a package.json with Express
            package_json = {
                "name": "test-app",
                "dependencies": {"express": "^4.18.0"}
            }
            package_path = Path(tmpdir) / "package.json"
            with open(package_path, "w") as f:
                json.dump(package_json, f)

            # Create analyze_dependencies mock
            scripts_dir = Path(__file__).parent
            analyze_deps = scripts_dir / "analyze_dependencies.py"

            strategy = TechStackStrategy(tmpdir)

            # Mock the dependency loading since we don't have the actual script
            strategy._dependencies = {"express": "^4.18.0"}

            context = DecisionContext(
                prd_requirements={"feature": "API endpoint"},
                current_state={},
                available_options=[],
                constraints={},
                session_id="test",
            )

            decision = strategy.decide(context)

            # Should prefer Express due to existing usage
            self.assertEqual(decision.choice, "Express")
            self.assertGreaterEqual(decision.confidence, 0.6)

    def test_decide_with_language_constraint(self):
        """Test decision with language constraint."""
        context = DecisionContext(
            prd_requirements={"feature": "API"},
            current_state={"language": "python"},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        # Should prefer Python-based framework
        self.assertIn(decision.choice, ["FastAPI", "Django", "Flask"])

    def test_invalid_context_raises_error(self):
        """Test that invalid context raises error."""
        context = DecisionContext(
            prd_requirements={},  # Empty requirements
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        with self.assertRaises(ValueError):
            self.strategy.decide(context)

    def test_unknown_category_raises_error(self):
        """Test that unknown category raises error."""
        # Mock the _detect_category to return unknown category
        context = DecisionContext(
            prd_requirements={"feature": "API", "category": "unknown_category"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        with self.assertRaises(RuntimeError):
            self.strategy.decide(context)


class TestRationaleBuilding(unittest.TestCase):
    """Test rationale building for decisions."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_rationale_includes_domain(self):
        """Test rationale includes domain information."""
        context = DecisionContext(
            prd_requirements={"feature": "REST API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIn("web_api", decision.rationale.lower())
        self.assertIn(decision.choice, decision.rationale)

    def test_rationale_includes_best_practices(self):
        """Test rationale includes best practices reasoning."""
        context = DecisionContext(
            prd_requirements={"feature": "Dashboard UI"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        # Should mention best practices
        self.assertTrue(
            "best practice" in decision.rationale.lower() or
            "rank" in decision.rationale.lower()
        )

    def test_rationale_includes_maturity(self):
        """Test rationale includes maturity information."""
        context = DecisionContext(
            prd_requirements={"feature": "Database"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        # Should mention maturity or ecosystem
        self.assertTrue(
            "mature" in decision.rationale.lower() or
            "ecosystem" in decision.rationale.lower() or
            "community" in decision.rationale.lower()
        )


class TestScoringBreakdown(unittest.TestCase):
    """Test scoring breakdown metadata."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_scoring_breakdown_includes_all_criteria(self):
        """Test scoring breakdown includes all criteria."""
        context = DecisionContext(
            prd_requirements={"feature": "API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIn("scoring_breakdown", decision.metadata)
        breakdown = decision.metadata["scoring_breakdown"]

        self.assertIn("best_practices", breakdown)
        self.assertIn("existing_patterns", breakdown)
        self.assertIn("simplicity", breakdown)
        self.assertIn("consistency", breakdown)

    def test_scoring_breakdown_values_are_valid(self):
        """Test scoring breakdown values are between 0 and 1."""
        context = DecisionContext(
            prd_requirements={"feature": "API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)
        breakdown = decision.metadata["scoring_breakdown"]

        for criterion, score in breakdown.items():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class TestAlternatives(unittest.TestCase):
    """Test alternatives generation."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_alternatives_includes_top_options(self):
        """Test alternatives includes top competing options."""
        context = DecisionContext(
            prd_requirements={"feature": "API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIsInstance(decision.alternatives, list)
        self.assertGreater(len(decision.alternatives), 0)
        self.assertLessEqual(len(decision.alternatives), 3)  # Max 3 alternatives

    def test_alternatives_different_from_choice(self):
        """Test alternatives are different from selected choice."""
        context = DecisionContext(
            prd_requirements={"feature": "API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertNotIn(decision.choice, decision.alternatives)


class TestConfidenceCalculation(unittest.TestCase):
    """Test confidence calculation logic."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_high_confidence_with_clear_winner(self):
        """Test high confidence when there's a clear winner."""
        # This should get high confidence due to best practices + existing patterns
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy = TechStackStrategy(tmpdir)
            strategy._dependencies = {"express": "^4.18.0"}

            context = DecisionContext(
                prd_requirements={"feature": "REST API"},
                current_state={"language": "javascript"},
                available_options=[],
                constraints={},
                session_id="test",
            )

            decision = strategy.decide(context)
            self.assertGreaterEqual(decision.confidence, 0.5)

    def test_reasonable_confidence_without_existing(self):
        """Test reasonable confidence even without existing patterns."""
        context = DecisionContext(
            prd_requirements={"feature": "REST API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)
        self.assertGreaterEqual(decision.confidence, 0.4)
        self.assertLessEqual(decision.confidence, 1.0)


class TestValidation(unittest.TestCase):
    """Test context validation."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_validate_context_success(self):
        """Test successful validation."""
        context = DecisionContext(
            prd_requirements={"feature": "API"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        self.assertTrue(self.strategy.validate_context(context))

    def test_validate_context_none_fails(self):
        """Test validation fails with None context."""
        self.assertFalse(self.strategy.validate_context(None))

    def test_validate_context_empty_requirements_fails(self):
        """Test validation fails with empty requirements."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        with self.assertRaises(ValueError):
            self.strategy.validate_context(context)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for realistic scenarios."""

    def setUp(self):
        """Set up test strategy."""
        self.strategy = TechStackStrategy()

    def test_web_api_scenario(self):
        """Test complete web API tech stack selection."""
        context = DecisionContext(
            prd_requirements={
                "feature": "User authentication API",
                "requirements": ["OAuth 2.0", "JWT tokens", "REST endpoints"],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id="web-api-test",
        )

        decision = self.strategy.decide(context)

        # Verify decision structure
        self.assertIsNotNone(decision.choice)
        self.assertIsNotNone(decision.rationale)
        self.assertGreaterEqual(decision.confidence, 0.4)
        self.assertGreater(len(decision.alternatives), 0)

        # Verify metadata
        self.assertIn("domain", decision.metadata)
        self.assertEqual(decision.metadata["domain"], "web_api")
        self.assertIn("category", decision.metadata)

    def test_full_stack_scenario(self):
        """Test full-stack application tech stack selection."""
        context = DecisionContext(
            prd_requirements={
                "feature": "Full-stack dashboard",
                "requirements": ["React UI", "Python backend", "PostgreSQL database"],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id="full-stack-test",
        )

        decision = self.strategy.decide(context)

        # Should select a language/framework for full-stack
        self.assertIn(decision.metadata["domain"], ["full_stack", "web_ui", "web_api"])
        self.assertIsNotNone(decision.rationale)

    def test_cli_tool_scenario(self):
        """Test CLI tool tech stack selection."""
        context = DecisionContext(
            prd_requirements={
                "feature": "Developer productivity CLI",
                "requirements": ["Command arguments", "Help system", "Terminal output"],
            },
            current_state={"language": "python"},
            available_options=[],
            constraints={},
            session_id="cli-test",
        )

        decision = self.strategy.decide(context)

        # Should select Python CLI framework
        self.assertIn(decision.choice, ["Click", "Typer"])
        self.assertEqual(decision.metadata["domain"], "cli_tool")

    def test_database_selection_scenario(self):
        """Test database selection for different use cases."""
        context = DecisionContext(
            prd_requirements={
                "feature": "User session storage",
                "category": "database",
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id="db-test",
        )

        decision = self.strategy.decide(context)

        # Should select a database
        self.assertIn(decision.choice, ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite"])
        self.assertEqual(decision.metadata["category"], "database")


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTechStackStrategyInit))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestDomainDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestScoringCriteria))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionMaking))
    suite.addTests(loader.loadTestsFromTestCase(TestRationaleBuilding))
    suite.addTests(loader.loadTestsFromTestCase(TestScoringBreakdown))
    suite.addTests(loader.loadTestsFromTestCase(TestAlternatives))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    result = run_tests()
    import sys
    sys.exit(0 if result.wasSuccessful() else 1)
