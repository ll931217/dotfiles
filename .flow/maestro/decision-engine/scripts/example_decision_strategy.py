#!/usr/bin/env python3
"""
Example usage of the Decision Strategy Framework.

Demonstrates how to create custom strategies and use them
for autonomous decision-making.
"""

from decision_strategy import (
    DecisionContext,
    Decision,
    DecisionStrategy,
    DecisionRegistry,
    register_strategy,
)


class TechStackExistingFirstStrategy(DecisionStrategy):
    """
    Tech stack strategy that prefers existing technologies.

    Scores options based on:
    1. Existing usage in codebase (highest priority)
    2. Ecosystem maturity
    3. Fit for requirements
    """

    def decide(self, context: DecisionContext) -> Decision:
        """Make tech stack decision preferring existing options."""
        # Validate context
        self.validate_context(context)

        # Score all options
        scored_options = []
        for option in context.available_options:
            score = self._score_option(option, context)
            scored_options.append((score, option))

        # Sort by score (descending)
        scored_options.sort(key=lambda x: x[0], reverse=True)

        # Extract top choices
        top_score, top_option = scored_options[0]
        second_score = scored_options[1][0] if len(scored_options) > 1 else 0.0

        # Calculate confidence
        confidence = self.get_confidence(
            top_score, second_score, len(scored_options)
        )

        # Build rationale
        rationale = self._build_rationale(top_option, top_score, context)

        # Create decision
        return Decision(
            choice=top_option["name"],
            rationale=rationale,
            confidence=confidence,
            alternatives=[opt["name"] for _, opt in scored_options[1:]],
            context_snapshot=context.to_dict(),
            decision_type="tech_stack",
            metadata={
                "strategy": self.get_strategy_name(),
                "top_score": top_score,
                "option_count": len(scored_options),
            },
        )

    def get_strategy_name(self) -> str:
        return "tech_stack_existing_first"

    def get_strategy_description(self) -> str:
        return "Tech stack strategy that prioritizes existing technologies"

    def get_supported_decision_types(self) -> list:
        return ["tech_stack", "database", "framework"]

    def _score_option(self, option: dict, context: DecisionContext) -> float:
        """Score an option based on multiple factors."""
        score = 0.5

        # Existing usage (40 points)
        if self._check_existing(option, context):
            score += 0.4

        # Ecosystem maturity (25 points)
        maturity = option.get("maturity", "medium")
        if maturity == "high":
            score += 0.25
        elif maturity == "medium":
            score += 0.15

        # Fit for requirements (25 points)
        if self._check_fit(option, context):
            score += 0.25

        return min(score, 1.0)

    def _check_existing(self, option: dict, context: DecisionContext) -> bool:
        """Check if option already exists in codebase."""
        existing = context.current_state.get("existing_techs", [])
        option_name = option.get("name", "").lower()

        return any(
            option_name in str(tech).lower()
            for tech in existing
        )

    def _check_fit(self, option: dict, context: DecisionContext) -> bool:
        """Check if option fits requirements."""
        requirements = context.prd_requirements.get("requirements", [])
        features = option.get("features", [])

        return any(req in features for req in requirements)

    def _build_rationale(
        self,
        option: dict,
        score: float,
        context: DecisionContext
    ) -> str:
        """Build human-readable rationale."""
        reasons = []

        if self._check_existing(option, context):
            reasons.append("already in codebase")

        maturity = option.get("maturity", "medium")
        if maturity == "high":
            reasons.append("mature ecosystem")

        if self._check_fit(option, context):
            reasons.append("fits requirements")

        if reasons:
            return f"Selected {option['name']}: " + "; ".join(reasons)
        else:
            return f"Selected {option['name']} by scoring"


def example_tech_stack_decision():
    """Example: Making a tech stack decision."""
    print("=" * 60)
    print("Example: Tech Stack Decision")
    print("=" * 60)

    # Create context
    context = DecisionContext(
        prd_requirements={
            "feature": "User authentication",
            "requirements": ["OAuth 2.0", "social login"],
        },
        current_state={
            "language": "nodejs",
            "framework": "express",
            "existing_techs": ["passport", "express-session"],
        },
        available_options=[
            {
                "name": "Passport.js",
                "maturity": "high",
                "features": ["OAuth 2.0", "social login", "JWT"],
            },
            {
                "name": "Auth.js",
                "maturity": "medium",
                "features": ["OAuth 2.0", "social login"],
            },
            {
                "name": "Auth0",
                "maturity": "high",
                "features": ["OAuth 2.0", "social login", "MFA"],
            },
        ],
        constraints={
            "budget": "low",
            "timeline": "2 weeks",
        },
        session_id="example-session-001",
    )

    print("\nContext:")
    print(f"  Feature: {context.prd_requirements['feature']}")
    print(f"  Current stack: {context.current_state['language']}/{context.current_state['framework']}")
    print(f"  Options: {len(context.available_options)}")

    # Create and register strategy
    strategy = TechStackExistingFirstStrategy()
    register_strategy("tech_existing", strategy)

    # Make decision
    decision = strategy.decide(context)

    print("\nDecision:")
    print(f"  Choice: {decision.choice}")
    print(f"  Confidence: {decision.confidence:.2f} ({decision.get_confidence_level()})")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Alternatives: {', '.join(decision.alternatives)}")
    print(f"  Strategy: {decision.metadata['strategy']}")
    print(f"  Score: {decision.metadata['top_score']:.2f}")


def example_registry_usage():
    """Example: Using the strategy registry."""
    print("\n" + "=" * 60)
    print("Example: Strategy Registry")
    print("=" * 60)

    # Create registry
    registry = DecisionRegistry()

    # Register multiple strategies
    tech_strategy = TechStackExistingFirstStrategy()
    registry.register("tech_stack", tech_strategy)

    # List strategies
    print("\nRegistered strategies:")
    for name in registry.list_strategies():
        desc = registry.describe_strategy(name)
        print(f"  - {name}: {desc['description']}")
        print(f"    Types: {', '.join(desc['supported_types'])}")

    # Select strategy by type
    print("\nSelecting strategy for 'tech_stack':")
    selected = registry.select_strategy("tech_stack")
    print(f"  Selected: {selected.get_strategy_name()}")

    # Export registry state
    print("\nRegistry state:")
    state = registry.export_registry()
    print(f"  Total strategies: {state['total_strategies']}")
    print(f"  Decision types: {', '.join(state['decision_types'])}")


def example_custom_validation():
    """Example: Custom context validation."""
    print("\n" + "=" * 60)
    print("Example: Custom Validation")
    print("=" * 60)

    class StrictTechStackStrategy(TechStackExistingFirstStrategy):
        """Strategy with stricter validation."""

        def validate_context(self, context: DecisionContext) -> bool:
            """Validate context with stricter rules."""
            # Call parent validation
            super().validate_context(context)

            # Additional validation
            if not context.current_state.get("language"):
                raise ValueError("Language must be specified in current_state")

            if not context.constraints.get("budget"):
                raise ValueError("Budget constraint must be specified")

            return True

    # Test with valid context
    try:
        valid_context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={"language": "python"},
            available_options=[{"name": "Test"}],
            constraints={"budget": "low"},
            session_id="test",
        )

        strategy = StrictTechStackStrategy()
        strategy.validate_context(valid_context)
        print("\n✓ Valid context passed validation")

    except ValueError as e:
        print(f"\n✗ Unexpected error: {e}")

    # Test with invalid context
    try:
        invalid_context = DecisionContext(
            prd_requirements={"feature": "auth"},
            current_state={},  # Missing language
            available_options=[{"name": "Test"}],
            constraints={},  # Missing budget
            session_id="test",
        )

        strategy.validate_context(invalid_context)
        print("\n✗ Invalid context should have failed validation")

    except ValueError as e:
        print(f"\n✓ Invalid context rejected: {e}")


def main():
    """Run all examples."""
    example_tech_stack_decision()
    example_registry_usage()
    example_custom_validation()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
