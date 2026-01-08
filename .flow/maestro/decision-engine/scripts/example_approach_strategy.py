#!/usr/bin/env python3
"""
Example: Using ApproachStrategy for Implementation Selection

This example demonstrates how to use the ApproachStrategy to select
between alternative implementation approaches for a real-world scenario.
"""

from decision_strategy import DecisionContext
from approach_strategy import (
    ApproachStrategy,
    ImplementationAlternative,
    create_simple_alternative,
)


def example_authentication_selection():
    """
    Example: Selecting authentication implementation approach.

    Scenario: Need to add authentication to a Node.js application.
    Alternatives: Passport.js (library) vs Custom JWT vs Auth0 service.
    """
    print("=" * 70)
    print("Example 1: Authentication Implementation Selection")
    print("=" * 70)

    # Define alternatives
    alternatives = [
        create_simple_alternative(
            name="passport_library",
            description="Use Passport.js (industry standard, 1000+ providers)",
            complexity="LOW",
            performance="FAST",
            maintainability="HIGH",
            testability="HIGH"
        ),
        create_simple_alternative(
            name="custom_jwt",
            description="Custom JWT implementation with manual verification",
            complexity="HIGH",
            performance="FAST",
            maintainability="MEDIUM",
            testability="MEDIUM"
        ),
        create_simple_alternative(
            name="auth0_service",
            description="Use Auth0 cloud service",
            complexity="LOW",
            performance="MODERATE",
            maintainability="HIGH",
            testability="HIGH"
        )
    ]

    # Create context with preference for best practices
    context = DecisionContext(
        prd_requirements={
            "feature": "user authentication",
            "prefer_best_practices": True
        },
        current_state={
            "existing_patterns": ["middleware", "passport"],
            "architecture": {"style": "mvc"}
        },
        available_options=alternatives,
        constraints={
            "timeline": "2 weeks",
            "budget": "low"
        },
        session_id="auth-selection-001"
    )

    # Make decision
    strategy = ApproachStrategy()
    decision = strategy.decide(context)

    # Display results
    print(f"\nSelected Approach: {decision.choice}")
    print(f"Confidence: {decision.confidence:.2f} ({decision.get_confidence_level()})")
    print(f"\nRationale:")
    print(f"  {decision.rationale}")
    print(f"\nAlternatives Considered:")
    for alt in decision.alternatives:
        print(f"  - {alt}")

    # Show scoring details
    print(f"\nScoring Details:")
    for score_info in decision.metadata["all_scores"]:
        print(f"  {score_info['name']}: {score_info['score']:.3f}")

    print()


def example_error_handling_selection():
    """
    Example: Selecting error handling approach.

    Scenario: Need to implement error handling for Express.js API.
    Alternatives: Try-catch everywhere vs Centralized middleware.
    """
    print("=" * 70)
    print("Example 2: Error Handling Approach Selection")
    print("=" * 70)

    # Define alternatives
    alternatives = [
        ImplementationAlternative(
            name="global_middleware",
            description="Centralized error handling middleware (Express pattern)",
            complexity="LOW",
            performance="FAST",
            maintainability="HIGH",
            testability="HIGH",
            lines_of_code=50,
            cognitive_load=2
        ),
        ImplementationAlternative(
            name="try_catch_everywhere",
            description="Try-catch around every route handler",
            complexity="HIGH",
            performance="SLOW",
            maintainability="LOW",
            testability="LOW",
            lines_of_code=500,
            cognitive_load=8
        ),
        ImplementationAlternative(
            name="async_wrapper",
            description="Custom async wrapper function for routes",
            complexity="MEDIUM",
            performance="FAST",
            maintainability="MEDIUM",
            testability="MEDIUM",
            lines_of_code=100,
            cognitive_load=4
        )
    ]

    # Create context
    context = DecisionContext(
        prd_requirements={
            "feature": "error handling",
            "requirement": "Handle all async errors consistently"
        },
        current_state={
            "framework": "express",
            "architecture": {"style": "middleware"}
        },
        available_options=alternatives,
        constraints={},
        session_id="error-handling-001"
    )

    # Make decision
    strategy = ApproachStrategy()
    decision = strategy.decide(context)

    # Display results
    print(f"\nSelected Approach: {decision.choice}")
    print(f"Confidence: {decision.confidence:.2f} ({decision.get_confidence_level()})")
    print(f"\nRationale:")
    print(f"  {decision.rationale}")
    print(f"\nAlternatives Considered:")
    for alt in decision.alternatives:
        print(f"  - {alt}")

    # Show detailed comparison
    print(f"\nDetailed Comparison:")
    selected = next(
        alt for alt in alternatives
        if alt.name == decision.choice
    )
    print(f"  Complexity: {selected.complexity}")
    print(f"  Performance: {selected.performance}")
    print(f"  Maintainability: {selected.maintainability}")
    print(f"  Testability: {selected.testability}")
    if selected.lines_of_code:
        print(f"  Estimated LOC: {selected.lines_of_code}")
    if selected.cognitive_load:
        print(f"  Cognitive Load: {selected.cognitive_load}/10")

    print()


def example_auto_recovery_scenario():
    """
    Example: Auto-recovery when initial approach fails.

    Scenario: Primary approach (complex) fails, need to select fallback.
    """
    print("=" * 70)
    print("Example 3: Auto-Recovery Scenario")
    print("=" * 70)

    # Define alternatives including fallback
    alternatives = [
        create_simple_alternative(
            name="optimized_caching",
            description="Complex multi-layer caching strategy",
            complexity="HIGH",
            performance="FAST",
            maintainability="MEDIUM",
            testability="MEDIUM"
        ),
        create_simple_alternative(
            name="simple_caching",
            description="Simple in-memory cache",
            complexity="LOW",
            performance="MODERATE",
            maintainability="HIGH",
            testability="HIGH"
        ),
        create_simple_alternative(
            name="no_caching",
            description="No caching, direct database queries",
            complexity="LOW",
            performance="SLOW",
            maintainability="HIGH",
            testability="HIGH"
        )
    ]

    # Create context
    context = DecisionContext(
        prd_requirements={
            "feature": "performance optimization",
            "requirement": "Improve response times"
        },
        current_state={},
        available_options=alternatives,
        constraints={"timeline": "1 week"},
        session_id="recovery-001"
    )

    # Simulate initial approach selection
    strategy = ApproachStrategy()
    initial_decision = strategy.decide(context)

    print(f"\nInitial Approach: {initial_decision.choice}")
    print(f"Rationale: {initial_decision.rationale}")

    # Simulate failure of initial approach
    print(f"\n❌ Initial approach '{initial_decision.choice}' failed to implement")

    # Select fallback
    from approach_strategy import select_fallback_approach

    fallback = select_fallback_approach(initial_decision.choice, context)

    if fallback:
        print(f"\n✓ Selected Fallback: {fallback}")

        # Get details of fallback approach
        fallback_alt = next(
            alt for alt in alternatives
            if alt.name == fallback
        )
        print(f"  Description: {fallback_alt.description}")
        print(f"  Complexity: {fallback_alt.complexity}")
        print(f"  Performance: {fallback_alt.performance}")
    else:
        print(f"\n✗ No suitable fallback available")

    print()


def example_performance_vs_maintainability():
    """
    Example: Tradeoff between performance and maintainability.

    Scenario: Database access layer implementation.
    """
    print("=" * 70)
    print("Example 4: Performance vs Maintainability Tradeoff")
    print("=" * 70)

    # Define alternatives with different tradeoffs
    alternatives = [
        create_simple_alternative(
            name="raw_sql",
            description="Raw SQL queries (maximum performance, low maintainability)",
            complexity="MEDIUM",
            performance="FAST",
            maintainability="LOW",
            testability="LOW"
        ),
        create_simple_alternative(
            name="orm",
            description="ORM with abstraction (good performance, high maintainability)",
            complexity="LOW",
            performance="MODERATE",
            maintainability="HIGH",
            testability="HIGH"
        ),
        create_simple_alternative(
            name="query_builder",
            description="Query builder (balanced approach)",
            complexity="MEDIUM",
            performance="MODERATE",
            maintainability="MEDIUM",
            testability="MEDIUM"
        )
    ]

    # Create context
    context = DecisionContext(
        prd_requirements={
            "feature": "database access",
            "priority": "maintainability"
        },
        current_state={
            "existing_patterns": ["orm", "models"]
        },
        available_options=alternatives,
        constraints={},
        session_id="db-access-001"
    )

    # Make decision
    strategy = ApproachStrategy()
    decision = strategy.decide(context)

    # Display results
    print(f"\nSelected Approach: {decision.choice}")
    print(f"Confidence: {decision.confidence:.2f} ({decision.get_confidence_level()})")
    print(f"\nRationale:")
    print(f"  {decision.rationale}")

    # Analyze tradeoff
    print(f"\nTradeoff Analysis:")
    print(f"  The strategy chose maintainability over raw performance.")
    print(f"  This is due to:")
    print(f"    - Lower complexity (ORM: LOW vs Raw SQL: MEDIUM)")
    print(f"    - Higher maintainability (ORM: HIGH vs Raw SQL: LOW)")
    print(f"    - Better testability (ORM: HIGH vs Raw SQL: LOW)")
    print(f"    - Existing patterns bonus (ORM matches codebase)")

    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  ApproachStrategy Examples - Implementation Selection".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Run examples
    example_authentication_selection()
    example_error_handling_selection()
    example_auto_recovery_scenario()
    example_performance_vs_maintainability()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
The ApproachStrategy provides intelligent selection between implementation
alternatives based on:

1. Complexity (30%): Prefer simpler implementations
2. Performance (25%): Consider performance characteristics
3. Maintainability (25%): Favor maintainable code
4. Testability (20%): Prefer testable approaches

Plus hierarchy bonuses:
- Best practices (+15%)
- Existing patterns (+10%)
- Simplicity (+10%)
- Consistency (+5%)

This ensures decisions are well-reasoned and aligned with project goals.
""")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
