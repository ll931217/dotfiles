#!/usr/bin/env python3
"""
Unit tests for tech stack selection algorithm.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tech_stack_selector import TechStackSelector, TechOption, TECH_KNOWLEDGE_BASE


class TestTechOption(unittest.TestCase):
    """Test TechOption dataclass."""

    def test_to_dict(self):
        """Test TechOption.to_dict() converts rationale list to string."""
        option = TechOption(
            name="TestLib",
            category="authentication",
            existing_usage_score=40,
            maturity_score=25,
            community_score=15,
            fit_score=20,
            total_score=100,
            confidence="high",
            rationale=["Reason 1", "Reason 2", "Reason 3"],
            alternatives=["Alt1", "Alt2"],
        )

        result = option.to_dict()

        self.assertIsInstance(result['rationale'], str)
        self.assertEqual(result['rationale'], "Reason 1; Reason 2; Reason 3")
        self.assertEqual(result['name'], "TestLib")
        self.assertEqual(result['total_score'], 100)


class TestTechStackSelectorInit(unittest.TestCase):
    """Test TechStackSelector initialization."""

    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_with_valid_project(self):
        """Test initialization with a valid project directory."""
        selector = TechStackSelector(self.test_dir)
        self.assertIsNotNone(selector)
        self.assertEqual(selector.project_root, Path(self.test_dir))
        self.assertIsInstance(selector.dependencies, dict)
        self.assertIsInstance(selector.patterns, dict)


class TestCategoryDetection(unittest.TestCase):
    """Test category auto-detection from requirements."""

    def setUp(self):
        """Create a test selector instance."""
        self.test_dir = tempfile.mkdtemp()
        self.selector = TechStackSelector(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_detect_auth_category(self):
        """Test detecting authentication category."""
        tests = [
            "Need OAuth library",
            "Implement login",
            "Add JWT authentication",
            "Need passport strategy",
        ]
        for test in tests:
            category = self.selector._detect_category_from_requirement(test)
            self.assertEqual(category, "authentication", f"Failed for: {test}")

    def test_detect_database_category(self):
        """Test detecting database category."""
        tests = [
            "Need database for sessions",
            "Add PostgreSQL support",
            "Need MongoDB for data",
            "Implement Redis caching",
        ]
        for test in tests:
            category = self.selector._detect_category_from_requirement(test)
            self.assertEqual(category, "database", f"Failed for: {test}")

    def test_detect_frontend_category(self):
        """Test detecting frontend framework category."""
        tests = [
            "Need frontend framework",
            "Add React components",
            "Implement Vue UI",
        ]
        for test in tests:
            category = self.selector._detect_category_from_requirement(test)
            self.assertEqual(category, "frontend_framework", f"Failed for: {test}")

    def test_detect_backend_category(self):
        """Test detecting backend framework category."""
        tests = [
            "Need backend API framework",
            "Add Express server",
            "Implement Django REST API",
        ]
        for test in tests:
            category = self.selector._detect_category_from_requirement(test)
            self.assertEqual(category, "backend_framework", f"Failed for: {test}")

    def test_default_category(self):
        """Test default category when no keywords match."""
        category = self.selector._detect_category_from_requirement("Need something generic")
        self.assertEqual(category, "authentication")


class TestExistingTechDetection(unittest.TestCase):
    """Test detection of existing technologies in codebase."""

    def setUp(self):
        """Create a test selector with mocked dependencies."""
        self.test_dir = tempfile.mkdtemp()
        self.selector = TechStackSelector(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_check_existing_passport(self):
        """Test checking for Passport.js in dependencies."""
        # Mock dependencies
        self.selector.dependencies = {"passport": "^0.6.0", "express": "^4.18.0"}

        patterns = ["passport", "passport-", "passport-local"]
        result = self.selector._check_existing_tech(patterns)
        self.assertTrue(result)

    def test_check_existing_react(self):
        """Test checking for React in dependencies."""
        # Mock dependencies
        self.selector.dependencies = {"react": "^18.0.0", "react-dom": "^18.0.0"}

        patterns = ["react", "react-dom", "@react/", "useState", "useEffect"]
        result = self.selector._check_existing_tech(patterns)
        self.assertTrue(result)

    def test_check_non_existing_tech(self):
        """Test checking for technology not in dependencies."""
        # Mock dependencies
        self.selector.dependencies = {"express": "^4.18.0"}

        patterns = ["passport", "passport-", "passport-local"]
        result = self.selector._check_existing_tech(patterns)
        self.assertFalse(result)


class TestScoring(unittest.TestCase):
    """Test scoring calculations."""

    def setUp(self):
        """Create a test selector instance."""
        self.test_dir = tempfile.mkdtemp()
        self.selector = TechStackSelector(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_score_existing_tech_full_points(self):
        """Test scoring existing tech gets full 40 points."""
        # Mock with passport in dependencies
        self.selector.dependencies = {"passport": "^0.6.0"}

        tech_data = TECH_KNOWLEDGE_BASE['authentication']['Passport.js']
        score = self.selector._score_existing_usage("Passport.js", tech_data)
        self.assertEqual(score, 40)

    def test_score_compatible_tech_partial_points(self):
        """Test scoring compatible tech gets 30 points."""
        # Mock with express in dependencies (nodejs ecosystem)
        self.selector.dependencies = {"express": "^4.18.0"}

        tech_data = TECH_KNOWLEDGE_BASE['authentication']['Passport.js']
        score = self.selector._score_existing_usage("Passport.js", tech_data)
        self.assertEqual(score, 30)

    def test_score_standard_choice_minimal_points(self):
        """Test scoring standard choice gets 10 points."""
        # Empty dependencies
        self.selector.dependencies = {}

        tech_data = TECH_KNOWLEDGE_BASE['authentication']['Passport.js']
        score = self.selector._score_existing_usage("Passport.js", tech_data)
        self.assertEqual(score, 10)

    def test_score_experimental_no_points(self):
        """Test scoring experimental tech gets 0 points."""
        # Empty dependencies, non-standard choice
        self.selector.dependencies = {}

        tech_data = TECH_KNOWLEDGE_BASE['authentication']['Auth0']
        score = self.selector._score_existing_usage("Auth0", tech_data)
        self.assertEqual(score, 0)


class TestTechStackSelection(unittest.TestCase):
    """Test the main tech stack selection logic."""

    def setUp(self):
        """Create test directories and selector."""
        self.test_dir = tempfile.mkdtemp()
        self.selector = TechStackSelector(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_select_auth_returns_structure(self):
        """Test authentication selection returns correct structure."""
        result = self.selector.select_tech_stack("Need authentication")

        self.assertIn("decision_type", result)
        self.assertEqual(result["decision_type"], "tech_stack")
        self.assertIn("output", result)
        self.assertIn("decision", result["output"])
        self.assertIn("rationale", result["output"])
        self.assertIn("confidence", result["output"])
        self.assertIn("alternatives", result["output"])
        self.assertIn("context", result["output"])

    def test_select_auth_returns_passport(self):
        """Test authentication selection returns Passport.js by default."""
        result = self.selector.select_tech_stack("Need OAuth library")
        decision = result["output"]["decision"]

        # Should be one of the auth options
        self.assertIn(decision, ["Passport.js", "Auth.js", "Auth0", "custom JWT"])

    def test_select_database_returns_structure(self):
        """Test database selection returns correct structure."""
        result = self.selector.select_tech_stack("Need database", category="database")

        self.assertIn("decision_type", result)
        self.assertEqual(result["decision_type"], "tech_stack")
        self.assertEqual(result["category"], "database")
        self.assertIn("decision", result["output"])

    def test_select_unknown_category_returns_error(self):
        """Test selecting unknown category returns error."""
        result = self.selector.select_tech_stack("Need something", category="unknown_category")

        self.assertIn("error", result)
        self.assertIn("available_categories", result)

    def test_all_options_scored(self):
        """Test that all options in a category are scored."""
        result = self.selector.select_tech_stack("Need authentication")
        all_options = result["output"]["all_options"]

        # Should have 4 authentication options
        self.assertEqual(len(all_options), 4)

        # Each option should have all required fields
        for option in all_options:
            self.assertIn("name", option)
            self.assertIn("total_score", option)
            self.assertIn("existing_usage_score", option)
            self.assertIn("maturity_score", option)
            self.assertIn("community_score", option)
            self.assertIn("fit_score", option)
            self.assertIn("rationale", option)

    def test_scores_sorted_descending(self):
        """Test that options are sorted by score (highest first)."""
        result = self.selector.select_tech_stack("Need authentication")
        all_options = result["output"]["all_options"]

        scores = [opt["total_score"] for opt in all_options]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_confidence_levels(self):
        """Test confidence levels are set correctly."""
        result = self.selector.select_tech_stack("Need authentication")
        top_score = result["output"]["all_options"][0]["total_score"]
        confidence = result["output"]["confidence"]

        if top_score >= 90:
            self.assertEqual(confidence, "high")
        elif top_score >= 70:
            self.assertEqual(confidence, "medium")
        else:
            self.assertEqual(confidence, "low")


class TestIntegrationWithRealProjects(unittest.TestCase):
    """Integration tests with simulated real project structures."""

    def setUp(self):
        """Create test projects."""
        self.test_dirs = []

    def tearDown(self):
        """Clean up all test directories."""
        import shutil
        for test_dir in self.test_dirs:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_nodejs_project_with_passport(self):
        """Test with Node.js project that has Passport."""
        test_dir = tempfile.mkdtemp()
        self.test_dirs.append(test_dir)

        # Create package.json with passport
        package_json = {
            "name": "test-app",
            "dependencies": {
                "express": "^4.18.0",
                "passport": "^0.6.0",
                "passport-local": "^1.0.0",
            }
        }

        with open(os.path.join(test_dir, "package.json"), "w") as f:
            json.dump(package_json, f)

        selector = TechStackSelector(test_dir)
        result = selector.select_tech_stack("Need authentication")

        # Should detect passport and give it 100 points
        passport_option = next(
            (opt for opt in result["output"]["all_options"] if opt["name"] == "Passport.js"),
            None
        )
        self.assertIsNotNone(passport_option)
        self.assertEqual(passport_option["total_score"], 100)
        self.assertEqual(passport_option["existing_usage_score"], 40)

    def test_python_project_with_django(self):
        """Test with Python project that has Django."""
        test_dir = tempfile.mkdtemp()
        self.test_dirs.append(test_dir)

        # Create requirements.txt with django
        requirements = """\nDjango==4.2.0\npsycopg2-binary==2.9.0\ndjangorestframework==3.14.0\n"""

        with open(os.path.join(test_dir, "requirements.txt"), "w") as f:
            f.write(requirements)

        selector = TechStackSelector(test_dir)
        result = selector.select_tech_stack("Need backend framework", category="backend_framework")

        # Should detect Django and give it high score
        django_option = next(
            (opt for opt in result["output"]["all_options"] if opt["name"] == "Django"),
            None
        )
        self.assertIsNotNone(django_option)
        self.assertEqual(django_option["total_score"], 98)  # 40 existing + 25 maturity + 15 community + 18 fit


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTechOption))
    suite.addTests(loader.loadTestsFromTestCase(TestTechStackSelectorInit))
    suite.addTests(loader.loadTestsFromTestCase(TestCategoryDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestExistingTechDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestScoring))
    suite.addTests(loader.loadTestsFromTestCase(TestTechStackSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithRealProjects))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
