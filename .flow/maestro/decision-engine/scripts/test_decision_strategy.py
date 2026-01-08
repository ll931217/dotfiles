#!/usr/bin/env python3
"""
Tests for Decision Strategy Framework

Comprehensive test suite for Strategy Pattern implementation,
including base classes, registry, and concrete strategy examples.
"""

import unittest
from datetime import datetime, timezone
from decision_strategy import (
    DecisionContext,
    Decision,
    DecisionStrategy,
    DecisionRegistry,
    get_global_registry,
    register_strategy,
    get_strategy,
    list_strategies,
)


class MockTechStackStrategy(DecisionStrategy):
    """Mock tech stack decision strategy for testing."""

    def decide(self, context: DecisionContext) -> Decision:
        """Simple decision strategy for testing."""
        # Score all options
        scored_options = []
        for option in context.available_options:
            score = self.score_option(option, context)
            scored_options.append((score, option))

        # Sort by score
        scored_options.sort(key=lambda x: x[0], reverse=True)

        # Get top choice
        top_score, top_option = scored_options[0]
        second_score = scored_options[1][0] if len(scored_options) > 1 else 0.0

        choice = top_option.get("name", "unknown")
        confidence = self.get_confidence(top_score, second_score, len(scored_options))

        return Decision(
            choice=choice,
            rationale=f"Selected {choice} with score {top_score:.2f}",
            confidence=confidence,
            alternatives=[opt.get("name") for score, opt in scored_options[1:]],
            context_snapshot=context.to_dict(),
            decision_type="tech_stack",
        )

    def get_strategy_name(self) -> str:
        return "mock_tech_stack"

    def get_supported_decision_types(self) -> list:
        return ["tech_stack", "database"]

    def score_option(self, option: dict, context: DecisionContext) -> float:
        """Score based on simple heuristics."""
        score = 0.5

        # Boost if option matches constraints
        if context.constraints.get("preferred") == option.get("name"):
            score += 0.3

        # Boost if option exists in current state
        if option.get("name") in str(context.current_state.get("existing", [])):
            score += 0.2

        return min(score, 1.0)


class MockTaskOrderingStrategy(DecisionStrategy):
    """Mock task ordering strategy for testing."""

    def decide(self, context: DecisionContext) -> Decision:
        """Simple task ordering decision for testing."""
        # Just return first option as decision
        top_option = context.available_options[0]
        choice = top_option.get("name", "sequential")

        return Decision(
            choice=choice,
            rationale=f"Using {choice} ordering based on dependencies",
            confidence=0.7,
            alternatives=[opt.get("name") for opt in context.available_options[1:]],
            context_snapshot=context.to_dict(),
            decision_type="task_ordering",
        )

    def get_strategy_name(self) -> str:
        return "mock_task_ordering"

    def get_supported_decision_types(self) -> list:
        return ["task_ordering"]


class TestDecisionContext(unittest.TestCase):
    """Test DecisionContext dataclass."""

    def test_context_creation(self):
        """Test creating a decision context."""
        context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={"language": "python"},
            available_options=[{"name": "Passport.js"}],
            constraints={"timeline": "2 weeks"},
            session_id="test-session",
        )

        self.assertEqual(context.prd_requirements["feature"], "auth")
        self.assertEqual(context.current_state["language"], "python")
        self.assertEqual(len(context.available_options), 1)
        self.assertEqual(context.session_id, "test-session")

    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={"language": "python"},
            available_options=[{"name": "Passport.js"}],
            constraints={},
            session_id="test-session",
        )

        data = context.to_dict()

        self.assertEqual(data["prd_requirements"]["feature"], "auth")
        self.assertEqual(data["current_state"]["language"], "python")
        self.assertEqual(len(data["available_options"]), 1)

    def test_get_constraint(self):
        """Test getting constraint values."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={"timeline": "2 weeks", "budget": "low"},
            session_id="test",
        )

        self.assertEqual(context.get_constraint("timeline"), "2 weeks")
        self.assertEqual(context.get_constraint("budget"), "low")
        self.assertIsNone(context.get_constraint("nonexistent"))
        self.assertEqual(context.get_constraint("nonexistent", "default"), "default")

    def test_get_requirement(self):
        """Test getting requirement values."""
        context = DecisionContext(
            prd_requirements={"feature": "auth", "priority": "high"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        self.assertEqual(context.get_requirement("feature"), "auth")
        self.assertEqual(context.get_requirement("priority"), "high")
        self.assertIsNone(context.get_requirement("nonexistent"))

    def test_has_option(self):
        """Test checking if option exists."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[
                {"name": "Passport.js"},
                {"id": "auth0", "name": "Auth0"},
            ],
            constraints={},
            session_id="test",
        )

        self.assertTrue(context.has_option("Passport.js"))
        self.assertTrue(context.has_option("auth0"))
        self.assertFalse(context.has_option("Nonexistent"))

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        self.assertIsInstance(context.timestamp, str)
        # Should be valid ISO format
        datetime.fromisoformat(context.timestamp.replace("Z", "+00:00"))


class TestDecision(unittest.TestCase):
    """Test Decision dataclass."""

    def test_decision_creation(self):
        """Test creating a decision."""
        decision = Decision(
            choice="Passport.js",
            rationale="Best fit for OAuth requirements",
            confidence=0.85,
            alternatives=["Auth.js", "Auth0"],
            context_snapshot={},
            decision_type="tech_stack",
        )

        self.assertEqual(decision.choice, "Passport.js")
        self.assertEqual(decision.confidence, 0.85)
        self.assertEqual(len(decision.alternatives), 2)
        self.assertEqual(decision.decision_type, "tech_stack")

    def test_decision_validation_confidence_range(self):
        """Test that confidence must be between 0.0 and 1.0."""
        with self.assertRaises(ValueError):
            Decision(
                choice="Test",
                rationale="Test",
                confidence=1.5,
                alternatives=[],
                context_snapshot={},
            )

        with self.assertRaises(ValueError):
            Decision(
                choice="Test",
                rationale="Test",
                confidence=-0.1,
                alternatives=[],
                context_snapshot={},
            )

    def test_decision_validation_empty_choice(self):
        """Test that choice cannot be empty."""
        with self.assertRaises(ValueError):
            Decision(
                choice="",
                rationale="Test",
                confidence=0.5,
                alternatives=[],
                context_snapshot={},
            )

    def test_decision_validation_empty_rationale(self):
        """Test that rationale cannot be empty."""
        with self.assertRaises(ValueError):
            Decision(
                choice="Test",
                rationale="",
                confidence=0.5,
                alternatives=[],
                context_snapshot={},
            )

    def test_decision_to_dict(self):
        """Test converting decision to dictionary."""
        decision = Decision(
            choice="Passport.js",
            rationale="Best fit for OAuth",
            confidence=0.85,
            alternatives=["Auth.js"],
            context_snapshot={"prd": "auth"},
            decision_type="tech_stack",
            metadata={"source": "test"},
        )

        data = decision.to_dict()

        self.assertEqual(data["choice"], "Passport.js")
        self.assertEqual(data["confidence"], 0.85)
        self.assertEqual(data["metadata"]["source"], "test")

    def test_get_confidence_level(self):
        """Test confidence level categorization."""
        high_conf = Decision(
            choice="A", rationale="Test", confidence=0.85, alternatives=[], context_snapshot={}
        )
        med_conf = Decision(
            choice="A", rationale="Test", confidence=0.65, alternatives=[], context_snapshot={}
        )
        low_conf = Decision(
            choice="A", rationale="Test", confidence=0.3, alternatives=[], context_snapshot={}
        )

        self.assertEqual(high_conf.get_confidence_level(), "high")
        self.assertEqual(med_conf.get_confidence_level(), "medium")
        self.assertEqual(low_conf.get_confidence_level(), "low")

    def test_is_high_confidence(self):
        """Test high confidence check."""
        high_conf = Decision(
            choice="A", rationale="Test", confidence=0.85, alternatives=[], context_snapshot={}
        )
        low_conf = Decision(
            choice="A", rationale="Test", confidence=0.75, alternatives=[], context_snapshot={}
        )

        self.assertTrue(high_conf.is_high_confidence())
        self.assertFalse(low_conf.is_high_confidence())

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated."""
        decision = Decision(
            choice="A", rationale="Test", confidence=0.5, alternatives=[], context_snapshot={}
        )

        self.assertIsInstance(decision.timestamp, str)
        # Should be valid ISO format
        datetime.fromisoformat(decision.timestamp.replace("Z", "+00:00"))


class TestDecisionStrategy(unittest.TestCase):
    """Test DecisionStrategy base class."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = MockTechStackStrategy()

    def test_strategy_name(self):
        """Test getting strategy name."""
        self.assertEqual(self.strategy.get_strategy_name(), "mock_tech_stack")

    def test_strategy_description(self):
        """Test getting strategy description."""
        desc = self.strategy.get_strategy_description()
        self.assertIn("mock_tech_stack", desc)

    def test_supported_types(self):
        """Test getting supported decision types."""
        types = self.strategy.get_supported_decision_types()
        self.assertIn("tech_stack", types)
        self.assertIn("database", types)

    def test_validate_context_success(self):
        """Test context validation success."""
        context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={},
            available_options=[{"name": "A"}],
            constraints={},
            session_id="test",
        )

        self.assertTrue(self.strategy.validate_context(context))

    def test_validate_context_empty_context(self):
        """Test context validation with empty context."""
        self.assertFalse(self.strategy.validate_context(None))

    def test_validate_context_no_requirements(self):
        """Test context validation without PRD requirements."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[{"name": "A"}],
            constraints={},
            session_id="test",
        )

        with self.assertRaises(ValueError):
            self.strategy.validate_context(context)

    def test_validate_context_no_options(self):
        """Test context validation without available options."""
        context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        with self.assertRaises(ValueError):
            self.strategy.validate_context(context)

    def test_score_option_default(self):
        """Test default option scoring."""
        # Create base strategy with default scoring
        class BaseStrategy(DecisionStrategy):
            def decide(self, context):
                pass

            def get_strategy_name(self):
                return "base"

        base = BaseStrategy()
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id="test",
        )

        score = base.score_option({"name": "test"}, context)
        self.assertEqual(score, 0.5)

    def test_get_confidence_calculation(self):
        """Test confidence calculation logic."""
        # High confidence: clear winner with high score
        # Formula: 0.95 * 0.6 + (0.95 - 0.5) * 0.4 * 1.1 = 0.87
        conf = self.strategy.get_confidence(0.95, 0.5, 3)
        self.assertGreater(conf, 0.8)

        # Medium confidence: closer scores
        # Formula: 0.7 * 0.6 + (0.7 - 0.6) * 0.4 * 1.1 = 0.46
        conf = self.strategy.get_confidence(0.7, 0.6, 3)
        self.assertGreater(conf, 0.4)
        self.assertLess(conf, 0.6)

        # Lower confidence: only one option
        # Formula: 0.7 * 0.6 * 0.8 = 0.336
        conf = self.strategy.get_confidence(0.7, 0.0, 1)
        self.assertLess(conf, 0.5)

    def test_decide_creates_valid_decision(self):
        """Test that decide creates a valid decision."""
        context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={},
            available_options=[
                {"name": "Passport.js"},
                {"name": "Auth.js"},
            ],
            constraints={},
            session_id="test",
        )

        decision = self.strategy.decide(context)

        self.assertIsInstance(decision, Decision)
        self.assertIn(decision.choice, ["Passport.js", "Auth.js"])
        self.assertGreater(decision.confidence, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)
        self.assertIsInstance(decision.alternatives, list)


class TestDecisionRegistry(unittest.TestCase):
    """Test DecisionRegistry functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = DecisionRegistry()
        self.strategy1 = MockTechStackStrategy()
        self.strategy2 = MockTaskOrderingStrategy()

    def test_register_strategy(self):
        """Test registering a strategy."""
        self.registry.register("mock1", self.strategy1)

        self.assertEqual(len(self.registry.list_strategies()), 1)
        self.assertIn("mock1", self.registry.list_strategies())

    def test_register_duplicate_name(self):
        """Test that duplicate names are rejected."""
        self.registry.register("mock1", self.strategy1)

        with self.assertRaises(ValueError):
            self.registry.register("mock1", self.strategy2)

    def test_register_invalid_name(self):
        """Test that invalid names are rejected."""
        with self.assertRaises(ValueError):
            self.registry.register("", self.strategy1)

        with self.assertRaises(ValueError):
            self.registry.register(None, self.strategy1)

    def test_register_invalid_strategy(self):
        """Test that non-strategy objects are rejected."""
        with self.assertRaises(ValueError):
            self.registry.register("invalid", "not a strategy")

    def test_unregister_strategy(self):
        """Test unregistering a strategy."""
        self.registry.register("mock1", self.strategy1)
        self.registry.unregister("mock1")

        self.assertEqual(len(self.registry.list_strategies()), 0)
        self.assertNotIn("mock1", self.registry.list_strategies())

    def test_unregister_nonexistent(self):
        """Test that unregistering nonexistent strategy raises error."""
        with self.assertRaises(KeyError):
            self.registry.unregister("nonexistent")

    def test_get_strategy(self):
        """Test getting a strategy by name."""
        self.registry.register("mock1", self.strategy1)

        strategy = self.registry.get_strategy("mock1")
        self.assertEqual(strategy, self.strategy1)

    def test_get_strategy_nonexistent(self):
        """Test getting nonexistent strategy returns None."""
        strategy = self.registry.get_strategy("nonexistent")
        self.assertIsNone(strategy)

    def test_get_strategies_by_type(self):
        """Test getting strategies by decision type."""
        self.registry.register("tech", self.strategy1)
        self.registry.register("task", self.strategy2)

        tech_strategies = self.registry.get_strategies_by_type("tech_stack")
        task_strategies = self.registry.get_strategies_by_type("task_ordering")

        self.assertEqual(len(tech_strategies), 1)
        self.assertEqual(len(task_strategies), 1)
        self.assertIn(self.strategy1, tech_strategies)
        self.assertIn(self.strategy2, task_strategies)

    def test_list_strategies(self):
        """Test listing all strategies."""
        self.registry.register("mock1", self.strategy1)
        self.registry.register("mock2", self.strategy2)

        strategies = self.registry.list_strategies()
        self.assertEqual(len(strategies), 2)
        self.assertIn("mock1", strategies)
        self.assertIn("mock2", strategies)

    def test_list_decision_types(self):
        """Test listing all decision types."""
        self.registry.register("mock1", self.strategy1)
        self.registry.register("mock2", self.strategy2)

        types = self.registry.list_decision_types()
        self.assertIn("tech_stack", types)
        self.assertIn("task_ordering", types)
        self.assertIn("database", types)

    def test_describe_strategy(self):
        """Test describing a strategy."""
        self.registry.register("mock1", self.strategy1)

        desc = self.registry.describe_strategy("mock1")

        self.assertIsNotNone(desc)
        self.assertEqual(desc["name"], "mock1")
        self.assertIn("tech_stack", desc["supported_types"])

    def test_describe_nonexistent_strategy(self):
        """Test describing nonexistent strategy returns None."""
        desc = self.registry.describe_strategy("nonexistent")
        self.assertIsNone(desc)

    def test_describe_all(self):
        """Test describing all strategies."""
        self.registry.register("mock1", self.strategy1)
        self.registry.register("mock2", self.strategy2)

        all_desc = self.registry.describe_all()

        self.assertEqual(len(all_desc), 2)
        self.assertIn("mock1", all_desc)
        self.assertIn("mock2", all_desc)

    def test_select_strategy_by_type(self):
        """Test selecting strategy by decision type."""
        self.registry.register("tech", self.strategy1)
        self.registry.register("task", self.strategy2)

        strategy = self.registry.select_strategy("tech_stack")
        self.assertEqual(strategy, self.strategy1)

    def test_select_strategy_with_preference(self):
        """Test selecting strategy with preference."""
        self.registry.register("tech1", self.strategy1)
        self.registry.register("tech2", MockTechStackStrategy())

        # Prefer tech2
        strategy = self.registry.select_strategy(
            "tech_stack", preference="tech2"
        )
        self.assertEqual(strategy.get_strategy_name(), "mock_tech_stack")

    def test_select_strategy_no_match(self):
        """Test selecting strategy when no match exists."""
        strategy = self.registry.select_strategy("nonexistent_type")
        self.assertIsNone(strategy)

    def test_export_registry(self):
        """Test exporting registry state."""
        self.registry.register("mock1", self.strategy1)
        self.registry.register("mock2", self.strategy2)

        export = self.registry.export_registry()

        self.assertEqual(export["total_strategies"], 2)
        self.assertIn("mock1", export["strategies"])
        self.assertIn("tech_stack", export["decision_types"])


class TestGlobalRegistry(unittest.TestCase):
    """Test global registry functions."""

    def test_get_global_registry(self):
        """Test getting global registry."""
        registry = get_global_registry()
        self.assertIsInstance(registry, DecisionRegistry)

    def test_global_registry_singleton(self):
        """Test that global registry is a singleton."""
        reg1 = get_global_registry()
        reg2 = get_global_registry()
        self.assertIs(reg1, reg2)

    def test_register_strategy(self):
        """Test registering strategy via global function."""
        strategy = MockTechStackStrategy()
        register_strategy("global_test", strategy)

        self.assertIn("global_test", list_strategies())

    def test_get_strategy(self):
        """Test getting strategy via global function."""
        strategy = MockTechStackStrategy()
        register_strategy("global_test2", strategy)

        retrieved = get_strategy("global_test2")
        self.assertEqual(retrieved, strategy)

    def test_list_strategies(self):
        """Test listing strategies via global function."""
        strategies = list_strategies()
        self.assertIsInstance(strategies, list)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for common scenarios."""

    def test_complete_decision_workflow(self):
        """Test complete workflow from context to decision."""
        # Create context
        context = DecisionContext(
            prd_requirements={
                "feature": "authentication",
                "requirements": ["OAuth 2.0", "social login"],
            },
            current_state={
                "language": "nodejs",
                "framework": "express",
                "existing": ["passport"],
            },
            available_options=[
                {"name": "Passport.js", "oauth_support": True},
                {"name": "Auth.js", "oauth_support": True},
                {"name": "Auth0", "oauth_support": True},
            ],
            constraints={"preferred": "Passport.js"},
            session_id="integration-test",
        )

        # Register and use strategy
        registry = DecisionRegistry()
        strategy = MockTechStackStrategy()
        registry.register("tech", strategy)

        selected = registry.select_strategy("tech_stack", context)
        decision = selected.decide(context)

        # Verify decision
        self.assertEqual(decision.choice, "Passport.js")  # Preferred option
        self.assertGreater(decision.confidence, 0.6)  # Should be reasonably confident
        self.assertEqual(decision.decision_type, "tech_stack")
        self.assertGreater(len(decision.alternatives), 0)

    def test_multi_strategy_scenario(self):
        """Test using multiple strategies for different decision types."""
        registry = DecisionRegistry()

        # Register multiple strategies
        tech_strategy = MockTechStackStrategy()
        task_strategy = MockTaskOrderingStrategy()

        registry.register("tech", tech_strategy)
        registry.register("task", task_strategy)

        # Make tech stack decision
        tech_context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={},
            available_options=[{"name": "A"}],
            constraints={},
            session_id="test",
        )
        tech_decision = registry.select_strategy("tech_stack").decide(tech_context)

        # Make task ordering decision
        task_context = DecisionContext(
            prd_requirements={"feature": "ordering"},
            current_state={},
            available_options=[{"name": "sequential"}],
            constraints={},
            session_id="test",
        )
        task_decision = registry.select_strategy("task_ordering").decide(task_context)

        # Verify both decisions
        self.assertEqual(tech_decision.decision_type, "tech_stack")
        self.assertEqual(task_decision.decision_type, "task_ordering")

    def test_strategy_with_low_options(self):
        """Test decision-making with limited options."""
        context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={},
            available_options=[{"name": "OnlyOption"}],
            constraints={},
            session_id="test",
        )

        strategy = MockTechStackStrategy()
        decision = strategy.decide(context)

        self.assertEqual(decision.choice, "OnlyOption")
        # Should have lower confidence with only one option
        self.assertLess(decision.confidence, 0.8)


if __name__ == "__main__":
    unittest.main()
