#!/usr/bin/env python3
"""
Unit tests for ApproachStrategy implementation.

Tests cover:
- Simple vs complex approach selection
- Performance vs maintainability tradeoffs
- Testability evaluation
- Default decision hierarchy application
- Auto-recovery scenario (fallback approach)
"""

import unittest
from typing import Dict, List, Any

from decision_strategy import DecisionContext, Decision
from approach_strategy import (
    ApproachStrategy,
    ImplementationAlternative,
    create_simple_alternative,
    select_fallback_approach,
)


class TestImplementationAlternative(unittest.TestCase):
    """Test ImplementationAlternative dataclass."""

    def test_create_alternative(self):
        """Test creating a basic alternative."""
        alt = ImplementationAlternative(
            name="simple_approach",
            description="A simple implementation approach",
            complexity="LOW",
            performance="FAST",
            maintainability="HIGH",
            testability="HIGH"
        )

        self.assertEqual(alt.name, "simple_approach")
        self.assertEqual(alt.complexity, "LOW")
        self.assertEqual(alt.performance, "FAST")

    def test_to_dict(self):
        """Test converting alternative to dictionary."""
        alt = ImplementationAlternative(
            name="test_alt",
            description="Test alternative",
            complexity="MEDIUM",
            performance="MODERATE",
            maintainability="MEDIUM",
            testability="MEDIUM",
            lines_of_code=100,
            cognitive_load=5
        )

        result = alt.to_dict()

        self.assertEqual(result["name"], "test_alt")
        self.assertEqual(result["lines_of_code"], 100)
        self.assertEqual(result["cognitive_load"], 5)

    def test_optional_fields(self):
        """Test alternative with optional fields omitted."""
        alt = ImplementationAlternative(
            name="minimal_alt",
            description="Minimal alternative",
            complexity="LOW",
            performance="FAST",
            maintainability="HIGH",
            testability="HIGH"
        )

        self.assertIsNone(alt.lines_of_code)
        self.assertIsNone(alt.cognitive_load)


class TestApproachStrategy(unittest.TestCase):
    """Test ApproachStrategy decision-making."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ApproachStrategy()

    def create_context(
        self,
        alternatives: List[Dict[str, Any]],
        requirements: Dict[str, Any] = None,
        current_state: Dict[str, Any] = None
    ) -> DecisionContext:
        """Helper to create a decision context."""
        return DecisionContext(
            prd_requirements=requirements or {},
            current_state=current_state or {},
            available_options=alternatives,
            constraints={},
            session_id="test-session"
        )

    def test_strategy_metadata(self):
        """Test strategy name and description."""
        self.assertEqual(
            self.strategy.get_strategy_name(),
            "approach_hierarchy"
        )

        self.assertIn("hierarchy", self.strategy.get_strategy_description().lower())

        self.assertIn(
            "approach_selection",
            self.strategy.get_supported_decision_types()
        )

    def test_simple_vs_complex_selection(self):
        """Test selecting simple approach over complex one."""
        alternatives = [
            {
                "name": "simple_approach",
                "description": "Simple, straightforward implementation",
                "complexity": "LOW",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "HIGH"
            },
            {
                "name": "complex_approach",
                "description": "Complex implementation with many edge cases",
                "complexity": "HIGH",
                "performance": "FAST",
                "maintainability": "LOW",
                "testability": "LOW"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        # Should prefer simple approach
        self.assertEqual(decision.choice, "simple_approach")
        self.assertIn("Low implementation complexity", decision.rationale)
        self.assertGreater(decision.confidence, 0.6)

    def test_performance_vs_maintainability_tradeoff(self):
        """Test performance vs maintainability tradeoff."""
        alternatives = [
            {
                "name": "performance_optimized",
                "description": "Highly optimized but complex code",
                "complexity": "HIGH",
                "performance": "FAST",
                "maintainability": "LOW",
                "testability": "MEDIUM"
            },
            {
                "name": "maintainable_approach",
                "description": "Clean, maintainable code",
                "complexity": "LOW",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        # Maintainability should win due to hierarchy bonuses
        self.assertEqual(decision.choice, "maintainable_approach")
        self.assertIn("maintainability", decision.rationale.lower())

    def test_testability_evaluation(self):
        """Test testability as a decision factor."""
        alternatives = [
            {
                "name": "hard_to_test",
                "description": "Implementation that's difficult to test",
                "complexity": "MEDIUM",
                "performance": "FAST",
                "maintainability": "MEDIUM",
                "testability": "LOW"
            },
            {
                "name": "easy_to_test",
                "description": "Testable implementation",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        # Should prefer testable approach
        self.assertEqual(decision.choice, "easy_to_test")
        self.assertIn("testability", decision.rationale.lower())

    def test_best_practices_bonus(self):
        """Test best practices hierarchy bonus."""
        alternatives = [
            {
                "name": "best_practice_approach",
                "description": "Industry standard best practice approach",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "HIGH"
            },
            {
                "name": "custom_approach",
                "description": "Custom implementation",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            }
        ]

        requirements = {"prefer_best_practices": True}
        context = self.create_context(alternatives, requirements=requirements)
        decision = self.strategy.decide(context)

        self.assertEqual(decision.choice, "best_practice_approach")
        self.assertIn("best practice", decision.rationale.lower())

    def test_existing_patterns_bonus(self):
        """Test existing patterns hierarchy bonus."""
        alternatives = [
            {
                "name": "consistent_approach",
                "description": "Approach consistent with existing patterns",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "MEDIUM"
            },
            {
                "name": "novel_approach",
                "description": "New and different approach",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            }
        ]

        current_state = {
            "existing_patterns": ["consistent", "patterns"]
        }
        context = self.create_context(alternatives, current_state=current_state)
        decision = self.strategy.decide(context)

        self.assertEqual(decision.choice, "consistent_approach")
        self.assertIn("existing", decision.rationale.lower())

    def test_architecture_consistency_bonus(self):
        """Test architecture consistency hierarchy bonus."""
        alternatives = [
            {
                "name": "architecture_consistent",
                "description": "Maintains layered architecture pattern",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "MEDIUM"
            },
            {
                "name": "architecture_breaking",
                "description": "Breaks architectural patterns",
                "complexity": "MEDIUM",
                "performance": "FAST",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            }
        ]

        current_state = {"architecture": {"style": "layered"}}
        context = self.create_context(alternatives, current_state=current_state)
        decision = self.strategy.decide(context)

        self.assertEqual(decision.choice, "architecture_consistent")

    def test_confidence_calculation(self):
        """Test confidence calculation based on score gap."""
        alternatives = [
            {
                "name": "clear_winner",
                "description": "Clearly superior approach",
                "complexity": "LOW",
                "performance": "FAST",
                "maintainability": "HIGH",
                "testability": "HIGH"
            },
            {
                "name": "inferior",
                "description": "Clearly inferior approach",
                "complexity": "HIGH",
                "performance": "SLOW",
                "maintainability": "LOW",
                "testability": "LOW"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        # High confidence due to clear winner
        self.assertGreater(decision.confidence, 0.7)
        self.assertEqual(decision.get_confidence_level(), "high")

    def test_low_confidence_tied_scores(self):
        """Test low confidence when alternatives are tied."""
        alternatives = [
            {
                "name": "approach_a",
                "description": "Approach A",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            },
            {
                "name": "approach_b",
                "description": "Approach B",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        # Lower confidence due to tied scores
        self.assertLess(decision.confidence, 0.8)

    def test_alternatives_in_decision(self):
        """Test that rejected alternatives are included."""
        alternatives = [
            {
                "name": "selected",
                "description": "Selected approach",
                "complexity": "LOW",
                "performance": "FAST",
                "maintainability": "HIGH",
                "testability": "HIGH"
            },
            {
                "name": "rejected1",
                "description": "Rejected approach 1",
                "complexity": "HIGH",
                "performance": "SLOW",
                "maintainability": "LOW",
                "testability": "LOW"
            },
            {
                "name": "rejected2",
                "description": "Rejected approach 2",
                "complexity": "HIGH",
                "performance": "SLOW",
                "maintainability": "LOW",
                "testability": "LOW"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        self.assertEqual(decision.choice, "selected")
        self.assertIn("rejected1", decision.alternatives)
        self.assertIn("rejected2", decision.alternatives)

    def test_decision_metadata(self):
        """Test that decision includes comprehensive metadata."""
        alternatives = [
            {
                "name": "test_approach",
                "description": "Test approach",
                "complexity": "LOW",
                "performance": "FAST",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        context = self.create_context(alternatives)
        decision = self.strategy.decide(context)

        # Check metadata
        self.assertIn("selected_alternative", decision.metadata)
        self.assertIn("score", decision.metadata)
        self.assertIn("all_scores", decision.metadata)

        # Check all_scores contains all alternatives
        self.assertEqual(len(decision.metadata["all_scores"]), 1)

    def test_invalid_context_no_options(self):
        """Test validation with no available options."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test"
        )

        with self.assertRaises(ValueError):
            self.strategy.decide(context)

    def test_invalid_context_none(self):
        """Test validation with None context."""
        with self.assertRaises(ValueError):
            self.strategy.validate_context(None)

    def test_parse_alternative_objects(self):
        """Test parsing ImplementationAlternative objects from context."""
        alt1 = ImplementationAlternative(
            name="alt1",
            description="Alternative 1",
            complexity="LOW",
            performance="FAST",
            maintainability="HIGH",
            testability="HIGH"
        )

        alt2 = ImplementationAlternative(
            name="alt2",
            description="Alternative 2",
            complexity="HIGH",
            performance="SLOW",
            maintainability="LOW",
            testability="LOW"
        )

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[alt1, alt2],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        self.assertEqual(decision.choice, "alt1")

    def test_mixed_alternative_formats(self):
        """Test parsing mixed dict and object alternatives."""
        alt1 = {
            "name": "dict_alt",
            "description": "Dict alternative",
            "complexity": "LOW",
            "performance": "FAST",
            "maintainability": "HIGH",
            "testability": "HIGH"
        }

        alt2 = ImplementationAlternative(
            name="object_alt",
            description="Object alternative",
            complexity="HIGH",
            performance="SLOW",
            maintainability="LOW",
            testability="LOW"
        )

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[alt1, alt2],
            constraints={},
            session_id="test"
        )

        decision = self.strategy.decide(context)

        self.assertEqual(decision.choice, "dict_alt")


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""

    def test_create_simple_alternative(self):
        """Test creating a simple alternative."""
        alt = create_simple_alternative(
            name="simple",
            description="Simple approach"
        )

        self.assertEqual(alt.name, "simple")
        self.assertEqual(alt.complexity, "MEDIUM")  # Default
        self.assertEqual(alt.performance, "MODERATE")  # Default

    def test_create_simple_alternative_custom(self):
        """Test creating alternative with custom values."""
        alt = create_simple_alternative(
            name="custom",
            description="Custom approach",
            complexity="LOW",
            performance="FAST",
            maintainability="HIGH",
            testability="HIGH"
        )

        self.assertEqual(alt.complexity, "LOW")
        self.assertEqual(alt.performance, "FAST")


class TestAutoRecovery(unittest.TestCase):
    """Test auto-recovery fallback selection."""

    def test_select_fallback_approach(self):
        """Test selecting a fallback approach."""
        strategy = ApproachStrategy()

        alternatives = [
            {
                "name": "primary_approach",
                "description": "Primary approach that may fail",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            },
            {
                "name": "fallback_approach",
                "description": "Simple fallback approach",
                "complexity": "LOW",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=alternatives,
            constraints={},
            session_id="recovery-session"
        )

        # When primary approach fails, fallback should be selected
        fallback = select_fallback_approach("primary_approach", context)

        self.assertEqual(fallback, "fallback_approach")

    def test_no_fallback_when_only_one_option(self):
        """Test fallback behavior with single alternative."""
        alternatives = [
            {
                "name": "only_approach",
                "description": "Only available approach",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            }
        ]

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=alternatives,
            constraints={},
            session_id="recovery-session"
        )

        # No fallback available
        fallback = select_fallback_approach("only_approach", context)

        self.assertIsNone(fallback)

    def test_fallback_prefers_different_approach(self):
        """Test that fallback doesn't select the same failed approach."""
        strategy = ApproachStrategy()

        alternatives = [
            {
                "name": "best_approach",
                "description": "Best approach",
                "complexity": "LOW",
                "performance": "FAST",
                "maintainability": "HIGH",
                "testability": "HIGH"
            },
            {
                "name": "second_best",
                "description": "Second best",
                "complexity": "MEDIUM",
                "performance": "MODERATE",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            }
        ]

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=alternatives,
            constraints={},
            session_id="recovery-session"
        )

        # If best approach failed, should get second best
        fallback = select_fallback_approach("best_approach", context)

        self.assertEqual(fallback, "second_best")


class TestScoringCriteria(unittest.TestCase):
    """Test individual scoring criteria."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ApproachStrategy()

    def test_complexity_scoring(self):
        """Test complexity scoring."""
        low_complexity = ImplementationAlternative(
            name="low",
            description="Low complexity",
            complexity="LOW",
            performance="MODERATE",
            maintainability="MEDIUM",
            testability="MEDIUM"
        )

        high_complexity = ImplementationAlternative(
            name="high",
            description="High complexity",
            complexity="HIGH",
            performance="MODERATE",
            maintainability="MEDIUM",
            testability="MEDIUM"
        )

        low_score = self.strategy._score_complexity(low_complexity)
        high_score = self.strategy._score_complexity(high_complexity)

        self.assertGreater(low_score, high_score)
        self.assertEqual(low_score, 1.0)
        self.assertEqual(high_score, 0.3)

    def test_performance_scoring(self):
        """Test performance scoring."""
        fast = ImplementationAlternative(
            name="fast",
            description="Fast",
            complexity="MEDIUM",
            performance="FAST",
            maintainability="MEDIUM",
            testability="MEDIUM"
        )

        slow = ImplementationAlternative(
            name="slow",
            description="Slow",
            complexity="MEDIUM",
            performance="SLOW",
            maintainability="MEDIUM",
            testability="MEDIUM"
        )

        fast_score = self.strategy._score_performance(fast)
        slow_score = self.strategy._score_performance(slow)

        self.assertGreater(fast_score, slow_score)
        self.assertEqual(fast_score, 1.0)
        self.assertEqual(slow_score, 0.4)

    def test_maintainability_scoring(self):
        """Test maintainability scoring."""
        high = ImplementationAlternative(
            name="high",
            description="High maintainability",
            complexity="MEDIUM",
            performance="MODERATE",
            maintainability="HIGH",
            testability="MEDIUM"
        )

        low = ImplementationAlternative(
            name="low",
            description="Low maintainability",
            complexity="MEDIUM",
            performance="MODERATE",
            maintainability="LOW",
            testability="MEDIUM"
        )

        high_score = self.strategy._score_maintainability(high)
        low_score = self.strategy._score_maintainability(low)

        self.assertGreater(high_score, low_score)
        self.assertEqual(high_score, 1.0)
        self.assertEqual(low_score, 0.3)

    def test_testability_scoring(self):
        """Test testability scoring."""
        high = ImplementationAlternative(
            name="high",
            description="High testability",
            complexity="MEDIUM",
            performance="MODERATE",
            maintainability="MEDIUM",
            testability="HIGH"
        )

        low = ImplementationAlternative(
            name="low",
            description="Low testability",
            complexity="MEDIUM",
            performance="MODERATE",
            maintainability="MEDIUM",
            testability="LOW"
        )

        high_score = self.strategy._score_testability(high)
        low_score = self.strategy._score_testability(low)

        self.assertGreater(high_score, low_score)
        self.assertEqual(high_score, 1.0)
        self.assertEqual(low_score, 0.3)


class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ApproachStrategy()

    def test_authentication_implementation_selection(self):
        """Test selecting authentication implementation approach."""
        alternatives = [
            {
                "name": "jwt_custom",
                "description": "Custom JWT implementation",
                "complexity": "HIGH",
                "performance": "FAST",
                "maintainability": "MEDIUM",
                "testability": "MEDIUM"
            },
            {
                "name": "passport_library",
                "description": "Passport.js library (industry standard)",
                "complexity": "LOW",
                "performance": "FAST",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        requirements = {"prefer_best_practices": True}
        context = DecisionContext(
            prd_requirements=requirements,
            current_state={},
            available_options=alternatives,
            constraints={},
            session_id="auth-selection"
        )

        decision = self.strategy.decide(context)

        # Should prefer library (best practice + low complexity)
        self.assertEqual(decision.choice, "passport_library")
        self.assertGreater(decision.confidence, 0.7)

    def test_database_migration_strategy(self):
        """Test selecting database migration approach."""
        alternatives = [
            {
                "name": "manual_sql",
                "description": "Manual SQL scripts",
                "complexity": "MEDIUM",
                "performance": "FAST",
                "maintainability": "LOW",
                "testability": "LOW"
            },
            {
                "name": "orm_migrations",
                "description": "ORM-based migration tool",
                "complexity": "LOW",
                "performance": "MODERATE",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=alternatives,
            constraints={},
            session_id="db-migration"
        )

        decision = self.strategy.decide(context)

        # Should prefer ORM for maintainability and testability
        self.assertEqual(decision.choice, "orm_migrations")

    def test_api_error_handling_selection(self):
        """Test selecting error handling approach."""
        alternatives = [
            {
                "name": "try_catch_everywhere",
                "description": "Try-catch around every function",
                "complexity": "HIGH",
                "performance": "SLOW",
                "maintainability": "LOW",
                "testability": "LOW"
            },
            {
                "name": "global_error_handler",
                "description": "Centralized error handling middleware",
                "complexity": "LOW",
                "performance": "FAST",
                "maintainability": "HIGH",
                "testability": "HIGH"
            }
        ]

        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=alternatives,
            constraints={},
            session_id="error-handling"
        )

        decision = self.strategy.decide(context)

        # Should prefer centralized handler
        self.assertEqual(decision.choice, "global_error_handler")
        self.assertIn("Low implementation complexity", decision.rationale)


def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestImplementationAlternative))
    suite.addTests(loader.loadTestsFromTestCase(TestApproachStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoRecovery))
    suite.addTests(loader.loadTestsFromTestCase(TestScoringCriteria))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
