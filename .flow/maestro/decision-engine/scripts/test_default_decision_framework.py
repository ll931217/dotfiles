#!/usr/bin/env python3
"""
Comprehensive Tests for DefaultDecisionFramework

Tests all aspects of the default decision framework:
- Best practices evaluation
- Existing pattern matching
- Simplicity assessment
- Consistency checking
- Weighted scoring
- Strategy integration
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision_strategy import DecisionContext
from default_decision_framework import (
    DefaultDecisionFramework,
    BestPracticeScore,
    PatternMatchScore,
    SimplicityScore,
    ConsistencyScore,
)


class TestBestPracticesEvaluation:
    """Test best practices evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

    def test_best_practices_rank_conversion(self):
        """Test that best practice ranks are converted to scores correctly."""
        # Use empty temp directory to avoid pattern detection from test files
        import tempfile
        temp_dir = tempfile.mkdtemp()

        try:
            context = DecisionContext(
                prd_requirements={"feature": "authentication"},
                current_state={"project_root": temp_dir},
                available_options=[
                    {"name": "Passport.js", "category": "authentication"},
                    {"name": "Auth0", "category": "authentication"},
                    {"name": "custom JWT", "category": "authentication"},
                ],
                constraints={},
                session_id="test-123"
            )

            decision = self.framework.decide(context)

            # Passport.js should win (rank 1)
            assert decision.choice == "Passport.js"

            # Check that custom JWT has lower score
            scores = decision.metadata["scores"]
            assert scores["Passport.js"]["best_practices"] > scores["custom JWT"]["best_practices"]
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_best_practices_unknown_category(self):
        """Test handling of unknown categories."""
        context = DecisionContext(
            prd_requirements={"feature": "unknown"},
            current_state={},
            available_options=[
                {"name": "UnknownOption", "category": "unknown_category"},
            ],
            constraints={},
            session_id="test-456"
        )

        decision = self.framework.decide(context)

        # Should still make a decision with neutral best practice score
        assert decision.choice == "UnknownOption"
        assert decision.metadata["scores"]["UnknownOption"]["best_practices"] == 0.5

    def test_best_practices_multiple_categories(self):
        """Test best practices across multiple categories."""
        context = DecisionContext(
            prd_requirements={
                "features": ["authentication", "database"]
            },
            current_state={},
            available_options=[
                {"name": "Passport.js", "category": "authentication"},
                {"name": "PostgreSQL", "category": "database"},
                {"name": "Auth0", "category": "authentication"},
            ],
            constraints={},
            session_id="test-789"
        )

        decision = self.framework.decide(context)

        # Should pick based on overall score, not just best practices
        assert decision.choice in ["Passport.js", "PostgreSQL", "Auth0"]
        assert "best_practices" in decision.metadata["scores"][decision.choice]


class TestExistingPatternMatching:
    """Test existing pattern matching."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

        # Create temporary directory with sample code
        self.temp_dir = tempfile.mkdtemp()
        self._create_sample_files()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_sample_files(self):
        """Create sample files with known patterns."""
        # Create a file with Passport.js usage
        passport_file = Path(self.temp_dir) / "auth.js"
        passport_file.write_text("""
const passport = require('passport');
const LocalStrategy = require('passport-local').Strategy;

passport.use(new LocalStrategy({
    usernameField: 'email',
    passwordField: 'password'
}, async (email, password, done) => {
    // Authentication logic
}));
""")

        # Create a file with PostgreSQL usage
        db_file = Path(self.temp_dir) / "database.js"
        db_file.write_text("""
const { Pool } = require('pg');

const pool = new Pool({
    host: 'localhost',
    database: 'myapp',
    max: 20,
});

module.exports = pool;
""")

    def test_pattern_detection_existing(self):
        """Test detection of existing patterns."""
        context = DecisionContext(
            prd_requirements={"feature": "authentication"},
            current_state={"project_root": self.temp_dir},
            available_options=[
                {
                    "name": "Passport.js",
                    "category": "authentication",
                    "detect_patterns": ["passport", "passport-local"]
                },
                {
                    "name": "Auth0",
                    "category": "authentication",
                    "detect_patterns": ["auth0"]
                },
            ],
            constraints={},
            session_id="test-pattern-1"
        )

        decision = self.framework.decide(context)

        # Passport.js should get higher pattern score
        scores = decision.metadata["scores"]
        assert scores["Passport.js"]["existing_patterns"] > scores["Auth0"]["existing_patterns"]

    def test_pattern_detection_none(self):
        """Test when no patterns exist."""
        context = DecisionContext(
            prd_requirements={"feature": "authentication"},
            current_state={"project_root": self.temp_dir},
            available_options=[
                {
                    "name": "Auth0",
                    "category": "authentication",
                    "detect_patterns": ["auth0", "@auth0/"]
                },
            ],
            constraints={},
            session_id="test-pattern-2"
        )

        decision = self.framework.decide(context)

        # Should have zero pattern score
        assert decision.metadata["scores"]["Auth0"]["existing_patterns"] == 0.0

    def test_pattern_auto_generation(self):
        """Test automatic pattern generation."""
        # Create a new temp directory with specific file
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()

        try:
            # Create files with patterns that will be auto-generated
            # The framework generates: 'Passport.js', 'passport-js', '@passport.js/', 'passport.js-'
            test_file = Path(temp_dir) / "package.json"
            test_file.write_text('{"passport-js": "latest"}')

            context = DecisionContext(
                prd_requirements={"feature": "authentication"},
                current_state={"project_root": temp_dir},
                available_options=[
                    {
                        "name": "Passport.js",
                        "category": "authentication"
                        # No detect_patterns provided
                    },
                ],
                constraints={},
                session_id="test-pattern-3"
            )

            decision = self.framework.decide(context)

            # Should still detect patterns using auto-generated ones
            scores = decision.metadata["scores"]
            assert "existing_patterns" in scores["Passport.js"]
            # Should find some patterns since we created a file with passport-js
            assert scores["Passport.js"]["existing_patterns"] > 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestSimplicityAssessment:
    """Test simplicity assessment."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

    def test_simplicity_by_lines_of_code(self):
        """Test simplicity assessment based on lines of code."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {
                    "name": "SimpleAPI",
                    "category": "api_framework",
                    "lines_of_code": 50
                },
                {
                    "name": "ComplexAPI",
                    "category": "api_framework",
                    "lines_of_code": 1500
                },
            ],
            constraints={},
            session_id="test-simplicity-1"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]
        assert scores["SimpleAPI"]["simplicity"] > scores["ComplexAPI"]["simplicity"]

    def test_simplicity_by_complexity_level(self):
        """Test simplicity assessment based on complexity level."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {
                    "name": "LowComplexity",
                    "complexity": "LOW"
                },
                {
                    "name": "HighComplexity",
                    "complexity": "HIGH"
                },
            ],
            constraints={},
            session_id="test-simplicity-2"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]
        assert scores["LowComplexity"]["simplicity"] > scores["HighComplexity"]["simplicity"]

    def test_simplicity_by_cognitive_load(self):
        """Test simplicity assessment based on cognitive load."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {
                    "name": "SimpleCognitive",
                    "cognitive_load": 2
                },
                {
                    "name": "ComplexCognitive",
                    "cognitive_load": 8
                },
            ],
            constraints={},
            session_id="test-simplicity-3"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]
        assert scores["SimpleCognitive"]["simplicity"] > scores["ComplexCognitive"]["simplicity"]

    def test_simplicity_no_metrics(self):
        """Test simplicity when no metrics provided."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {
                    "name": "UnknownSimplicity",
                    "complexity": "MEDIUM"  # Will default to MEDIUM
                },
            ],
            constraints={},
            session_id="test-simplicity-4"
        )

        decision = self.framework.decide(context)

        # Should have simplicity score based on default MEDIUM complexity
        score = decision.metadata["scores"]["UnknownSimplicity"]["simplicity"]
        assert score > 0.4 and score < 0.8  # Should be around 0.6 for MEDIUM


class TestConsistencyChecking:
    """Test consistency checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

    def test_consistency_language_match(self):
        """Test consistency checking with language match."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={
                "primary_language": "Python"
            },
            available_options=[
                {
                    "name": "FastAPI",
                    "language": "Python",
                },
                {
                    "name": "Express",
                    "language": "JavaScript",
                },
            ],
            constraints={},
            session_id="test-consistency-1"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]
        # FastAPI should have higher consistency score
        assert scores["FastAPI"]["consistency"] > scores["Express"]["consistency"]

    def test_consistency_framework_match(self):
        """Test consistency checking with framework match."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={
                "frameworks": ["React", "Next.js"]
            },
            available_options=[
                {
                    "name": "NextAuth",
                    "framework": "Next.js",
                },
                {
                    "name": "Passport.js",
                    "framework": "Express",
                },
            ],
            constraints={},
            session_id="test-consistency-2"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]
        # NextAuth should have higher consistency score
        assert scores["NextAuth"]["consistency"] > scores["Passport.js"]["consistency"]

    def test_consistency_ecosystem_match(self):
        """Test consistency checking with ecosystem match."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={
                "ecosystem": "nodejs"
            },
            available_options=[
                {
                    "name": "Passport.js",
                    "ecosystem": "nodejs",
                },
                {
                    "name": "Django",
                    "ecosystem": "python",
                },
            ],
            constraints={},
            session_id="test-consistency-3"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]
        # Passport.js should have higher consistency score
        assert scores["Passport.js"]["consistency"] > scores["Django"]["consistency"]

    def test_consistency_no_info(self):
        """Test consistency when no information provided."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {
                    "name": "UnknownFramework",
                },
            ],
            constraints={},
            session_id="test-consistency-4"
        )

        decision = self.framework.decide(context)

        # Should have neutral consistency score
        assert decision.metadata["scores"]["UnknownFramework"]["consistency"] == 0.5


class TestWeightedScoring:
    """Test weighted scoring calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

    def test_weighted_scoring_all_dimensions(self):
        """Test that all dimensions contribute to final score."""
        context = DecisionContext(
            prd_requirements={"feature": "authentication"},
            current_state={
                "primary_language": "JavaScript",
                "ecosystem": "nodejs",
            },
            available_options=[
                {
                    "name": "Passport.js",
                    "category": "authentication",
                    "language": "JavaScript",
                    "ecosystem": "nodejs",
                    "complexity": "MEDIUM",
                },
            ],
            constraints={},
            session_id="test-weight-1"
        )

        decision = self.framework.decide(context)

        scores = decision.metadata["scores"]["Passport.js"]

        # All dimensions should have scores
        assert scores["best_practices"] >= 0.0
        assert scores["existing_patterns"] >= 0.0
        assert scores["simplicity"] >= 0.0
        assert scores["consistency"] >= 0.0

    def test_weighted_scoring_priority(self):
        """Test that best practices has highest priority."""
        context = DecisionContext(
            prd_requirements={"feature": "authentication"},
            current_state={},
            available_options=[
                {
                    "name": "Passport.js",
                    "category": "authentication",
                    "complexity": "HIGH",  # Low simplicity
                },
                {
                    "name": "Auth0",
                    "category": "authentication",
                    "complexity": "LOW",  # High simplicity
                },
            ],
            constraints={},
            session_id="test-weight-2"
        )

        decision = self.framework.decide(context)

        # Passport.js should still win despite higher complexity
        # because best practices has higher weight
        assert decision.choice == "Passport.js"

    def test_weighted_scoring_tiebreaker(self):
        """Test tiebreaker when scores are close."""
        context = DecisionContext(
            prd_requirements={"feature": "authentication"},
            current_state={},
            available_options=[
                {
                    "name": "OptionA",
                    "category": "authentication",
                },
                {
                    "name": "OptionB",
                    "category": "authentication",
                },
            ],
            constraints={},
            session_id="test-weight-3"
        )

        decision = self.framework.decide(context)

        # Should still make a decision
        assert decision.choice in ["OptionA", "OptionB"]
        # Should have alternatives
        assert len(decision.alternatives) >= 1


class TestStrategyIntegration:
    """Test integration with decision strategy framework."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

    def test_strategy_name(self):
        """Test strategy name."""
        assert self.framework.get_strategy_name() == "default_decision_framework"

    def test_strategy_description(self):
        """Test strategy description."""
        description = self.framework.get_strategy_description()
        # Check that description contains key terms
        assert "decision" in description.lower()
        assert len(description) > 0

    def test_supported_decision_types(self):
        """Test supported decision types."""
        types = self.framework.get_supported_decision_types()
        assert "tech_stack" in types
        assert "task_ordering" in types
        assert "approach" in types
        assert "architecture" in types
        assert "generic" in types

    def test_context_validation(self):
        """Test context validation."""
        # Empty available_options should raise error
        try:
            context = DecisionContext(
                prd_requirements={"feature": "test"},  # Add non-empty requirements
                current_state={},
                available_options=[],
                constraints={},
                session_id="test-validation"
            )
            self.framework.decide(context)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "available option" in str(e).lower() or "option" in str(e).lower()

    def test_decision_type_inference(self):
        """Test decision type inference from context."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {
                    "name": "FastAPI",
                    "category": "api_framework",
                },
            ],
            constraints={},
            session_id="test-inference"
        )

        decision = self.framework.decide(context)

        # Should infer tech_stack type
        assert decision.decision_type == "tech_stack"

    def test_decision_rationale_quality(self):
        """Test that decision rationale is comprehensive."""
        context = DecisionContext(
            prd_requirements={"feature": "authentication"},
            current_state={
                "primary_language": "JavaScript",
            },
            available_options=[
                {
                    "name": "Passport.js",
                    "category": "authentication",
                },
            ],
            constraints={},
            session_id="test-rationale"
        )

        decision = self.framework.decide(context)

        # Rationale should contain key sections
        assert "Score Breakdown" in decision.rationale
        assert "Best Practices" in decision.rationale
        assert "Existing Patterns" in decision.rationale
        assert "Simplicity" in decision.rationale
        assert "Consistency" in decision.rationale
        assert "Total Weighted Score" in decision.rationale


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.framework = DefaultDecisionFramework()

    def test_single_option(self):
        """Test with only one option."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {"name": "OnlyOption"},
            ],
            constraints={},
            session_id="test-single"
        )

        decision = self.framework.decide(context)

        assert decision.choice == "OnlyOption"
        assert len(decision.alternatives) == 0
        # With single option, confidence is based on top score * 0.8
        # (penalty for having < 2 options), so should be >= 0.2
        assert decision.confidence >= 0.2 and decision.confidence <= 1.0

    def test_many_options(self):
        """Test with many options."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {"name": f"Option{i}", "category": "api_framework"}
                for i in range(10)
            ],
            constraints={},
            session_id="test-many"
        )

        decision = self.framework.decide(context)

        # Should pick one
        assert decision.choice.startswith("Option")
        # Should have 9 alternatives
        assert len(decision.alternatives) == 9

    def test_option_without_name(self):
        """Test option without explicit name field."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {"id": "option-with-id"},
            ],
            constraints={},
            session_id="test-no-name"
        )

        decision = self.framework.decide(context)

        # Should use id as name
        assert decision.choice == "option-with-id"

    def test_mixed_option_formats(self):
        """Test with mixed option formats."""
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {"name": "NamedOption", "category": "api"},
                {"id": "IdOption", "category": "api"},
                {"description": "Unnamed option", "category": "api"},
            ],
            constraints={},
            session_id="test-mixed"
        )

        decision = self.framework.decide(context)

        # Should handle all formats
        assert decision.choice is not None
        assert len(decision.alternatives) == 2


def run_all_tests():
    """Run all test classes."""
    test_classes = [
        TestBestPracticesEvaluation,
        TestExistingPatternMatching,
        TestSimplicityAssessment,
        TestConsistencyChecking,
        TestWeightedScoring,
        TestStrategyIntegration,
        TestEdgeCases,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)

        instance = test_class()

        # Get all test methods
        test_methods = [
            method for method in dir(instance)
            if method.startswith('test_') and callable(getattr(instance, method))
        ]

        for method_name in test_methods:
            total_tests += 1

            # Setup
            if hasattr(instance, 'setup_method'):
                instance.setup_method()

            try:
                method = getattr(instance, method_name)
                method()
                print(f"  ✓ {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  ✗ {method_name}: {e}")
                failed_tests += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
                failed_tests += 1

            # Teardown
            if hasattr(instance, 'teardown_method'):
                try:
                    instance.teardown_method()
                except:
                    pass

    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)
    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {passed_tests}")
    print(f"Failed:       {failed_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")

    return failed_tests == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
