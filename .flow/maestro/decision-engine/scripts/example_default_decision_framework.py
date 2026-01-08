#!/usr/bin/env python3
"""
Example: Using DefaultDecisionFramework for Autonomous Decision-Making

This example demonstrates how to use the DefaultDecisionFramework to make
autonomous decisions when specialized strategies cannot determine a clear winner.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision_strategy import DecisionContext, Decision, get_global_registry, register_strategy
from default_decision_framework import DefaultDecisionFramework


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 70)
    if title:
        print(f" {title}")
        print("=" * 70)


def print_decision(decision: Decision):
    """Print a decision in a formatted way."""
    print_separator(f"DECISION: {decision.choice}")
    print(f"\nConfidence: {decision.confidence:.2f} ({decision.get_confidence_level()})")
    print(f"\nRationale:\n{decision.rationale}")

    if decision.alternatives:
        print(f"\nAlternatives Considered:")
        for i, alt in enumerate(decision.alternatives, 1):
            print(f"  {i}. {alt}")

    print_separator("Score Breakdown")
    scores = decision.metadata.get("scores", {})
    for option, option_scores in scores.items():
        print(f"\n{option}:")
        print(f"  Total: {option_scores['total']:.2f}")
        print(f"  - Best Practices: {option_scores['best_practices']:.2f}")
        print(f"  - Existing Patterns: {option_scores['existing_patterns']:.2f}")
        print(f"  - Simplicity: {option_scores['simplicity']:.2f}")
        print(f"  - Consistency: {option_scores['consistency']:.2f}")


def example_1_authentication_selection():
    """Example 1: Select authentication library."""
    print_separator("EXAMPLE 1: Authentication Library Selection")

    framework = DefaultDecisionFramework()

    context = DecisionContext(
        prd_requirements={
            "feature": "user authentication",
            "requirements": [
                "Support multiple providers (Google, GitHub, local)",
                "Session management",
                "Token-based auth"
            ]
        },
        current_state={
            "project_root": "/tmp/example_project",
            "primary_language": "JavaScript",
            "ecosystem": "nodejs",
        },
        available_options=[
            {
                "name": "Passport.js",
                "category": "authentication",
                "ecosystem": "nodejs",
                "complexity": "MEDIUM",
            },
            {
                "name": "Auth0",
                "category": "authentication",
                "ecosystem": "any",
                "complexity": "LOW",
            },
            {
                "name": "custom JWT",
                "category": "authentication",
                "ecosystem": "any",
                "complexity": "HIGH",
            },
        ],
        constraints={
            "budget": "open-source preferred",
            "maintenance": "prefer community-supported"
        },
        session_id="example-auth-1"
    )

    decision = framework.decide(context)
    print_decision(decision)


def example_2_database_selection():
    """Example 2: Select database technology."""
    print_separator("EXAMPLE 2: Database Technology Selection")

    framework = DefaultDecisionFramework()

    context = DecisionContext(
        prd_requirements={
            "feature": "data persistence",
            "requirements": [
                "ACID compliance required",
                "Complex relationships",
                "High read throughput"
            ]
        },
        current_state={
            "project_root": "/tmp/example_project",
            "primary_language": "Python",
            "ecosystem": "python",
        },
        available_options=[
            {
                "name": "PostgreSQL",
                "category": "database",
                "ecosystem": "any",
                "complexity": "MEDIUM",
            },
            {
                "name": "MongoDB",
                "category": "database",
                "ecosystem": "any",
                "complexity": "LOW",
            },
            {
                "name": "Redis",
                "category": "database",
                "ecosystem": "any",
                "complexity": "LOW",
            },
        ],
        constraints={
            "scalability": "horizontal scaling required",
            "consistency": "strong consistency preferred"
        },
        session_id="example-db-1"
    )

    decision = framework.decide(context)
    print_decision(decision)


def example_3_testing_framework():
    """Example 3: Select testing framework."""
    print_separator("EXAMPLE 3: Testing Framework Selection")

    framework = DefaultDecisionFramework()

    context = DecisionContext(
        prd_requirements={
            "feature": "testing infrastructure",
            "requirements": [
                "Unit testing",
                "Integration testing",
                "Fixtures support"
            ]
        },
        current_state={
            "project_root": "/tmp/example_project",
            "primary_language": "Python",
            "ecosystem": "python",
        },
        available_options=[
            {
                "name": "pytest",
                "category": "testing",
                "ecosystem": "python",
                "complexity": "LOW",
            },
            {
                "name": "unittest",
                "category": "testing",
                "ecosystem": "python",
                "complexity": "MEDIUM",
            },
        ],
        constraints={
            "standard_library": "can use third-party"
        },
        session_id="example-test-1"
    )

    decision = framework.decide(context)
    print_decision(decision)


def example_4_strategy_integration():
    """Example 4: Integration with decision strategy registry."""
    print_separator("EXAMPLE 4: Strategy Registry Integration")

    # Register the framework in the global registry
    register_strategy("default_framework", DefaultDecisionFramework())

    # Get the registry
    registry = get_global_registry()

    print("\nRegistered Strategies:")
    for strategy_name in registry.list_strategies():
        strategy = registry.get_strategy(strategy_name)
        print(f"  - {strategy_name}")
        print(f"    Description: {strategy.get_strategy_description()}")
        print(f"    Supported types: {', '.join(strategy.get_supported_decision_types())}")

    # Select and use the strategy
    framework = registry.select_strategy(
        decision_type="tech_stack",
        preference="default_framework"
    )

    if framework:
        context = DecisionContext(
            prd_requirements={"feature": "api"},
            current_state={},
            available_options=[
                {"name": "FastAPI", "category": "api_framework"},
                {"name": "Flask", "category": "api_framework"},
            ],
            constraints={},
            session_id="example-integration-1"
        )

        decision = framework.decide(context)
        print_decision(decision)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" DEFAULT DECISION FRAMEWORK - USAGE EXAMPLES")
    print("=" * 70)

    # Run examples
    example_1_authentication_selection()
    example_2_database_selection()
    example_3_testing_framework()
    example_4_strategy_integration()

    print("\n" + "=" * 70)
    print(" All examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
