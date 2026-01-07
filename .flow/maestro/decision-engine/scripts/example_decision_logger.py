#!/usr/bin/env python3
"""
Example: Using the Decision Logger

Demonstrates the complete workflow of logging decisions, aggregating to historical,
and learning from past decisions to inform new choices.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from decision_logger import DecisionLogger


def example_tech_stack_decisions():
    """Example: Logging tech stack decisions."""
    print("=" * 60)
    print("Example 1: Logging Tech Stack Decisions")
    print("=" * 60)

    logger = DecisionLogger()

    # Log framework decision
    logger.log_decision(
        decision_type="tech_stack",
        decision={
            "decision": "Use FastAPI for REST API backend",
            "rationale": (
                "Modern async framework with automatic OpenAPI generation, "
                "built-in validation, and excellent performance"
            ),
            "phase": "plan",
            "alternatives_considered": [
                {
                    "option": "Flask",
                    "reason_rejected": "Requires additional libraries for async and validation",
                },
                {
                    "option": "Django REST Framework",
                    "reason_rejected": "Heavier weight than needed for this service",
                },
            ],
            "context": {
                "confidence": "high",
                "sources": ["FastAPI documentation", "Benchmark comparisons"],
                "choice": "FastAPI",
                "category": "framework",
                "ecosystem_maturity": "stable",
                "community_size": "large",
            },
            "impact": {
                "scope": "codebase",
                "risk_level": "low",
                "reversibility": "moderate",
            },
        },
    )

    # Log database decision
    logger.log_decision(
        decision_type="tech_stack",
        decision={
            "decision": "Use PostgreSQL as primary database",
            "rationale": (
                "ACID compliance required for transactions, "
                "complex query support needed, and existing team expertise"
            ),
            "phase": "plan",
            "alternatives_considered": [
                {
                    "option": "MongoDB",
                    "reason_rejected": "Relational data model更适合",
                },
                {
                    "option": "MySQL",
                    "reason_rejected": "PostgreSQL has better JSON support and advanced features",
                },
            ],
            "context": {
                "confidence": "high",
                "choice": "PostgreSQL",
                "category": "database",
                "performance_requirements": "High",
            },
            "impact": {
                "scope": "codebase",
                "risk_level": "medium",
                "reversibility": "difficult",
            },
        },
    )

    print(f"\n✓ Logged 2 tech stack decisions for session {logger.session_id}")

    # Export summary
    summary = logger.export_summary()
    print(f"\nSession Summary:")
    print(f"  Total decisions: {summary['total_decisions']}")
    print(f"  Categories: {list(summary['decisions_by_category'].keys())}")

    return logger


def example_architecture_decisions(logger):
    """Example: Logging architecture decisions."""
    print("\n" + "=" * 60)
    print("Example 2: Logging Architecture Decisions")
    print("=" * 60)

    # Log pattern decision
    logger.log_decision(
        decision_type="architecture",
        decision={
            "decision": "Implement Repository pattern for data access",
            "rationale": (
                "Separates business logic from data access logic, "
                "makes testing easier, and provides flexibility for data sources"
            ),
            "phase": "plan",
            "alternatives_considered": [
                {
                    "option": "Active Record pattern",
                    "reason_rejected": "Tight coupling between domain and data models",
                },
                {
                    "option": "Data Mapper pattern",
                    "reason_rejected": "Additional complexity not needed at this stage",
                },
            ],
            "context": {
                "confidence": "high",
                "existing_patterns": True,
                "consistency_with_codebase": "matches",
                "complexity_level": "moderate",
            },
            "impact": {
                "scope": "codebase",
                "risk_level": "low",
                "reversibility": "moderate",
            },
        },
    )

    print("\n✓ Logged architecture decision")


def example_aggregate_to_historical(logger):
    """Example: Aggregating decisions to historical records."""
    print("\n" + "=" * 60)
    print("Example 3: Aggregating to Historical Records")
    print("=" * 60)

    logger.aggregate_to_historical()

    print("\n✓ Aggregated decisions to historical files")
    print("\nHistorical files created:")
    for hist_file in logger.decisions_dir.glob("historical-*.json"):
        data = json.loads(hist_file.read_text())
        print(f"  {hist_file.name}: {len(data['decisions'])} decisions")


def example_query_historical():
    """Example: Querying historical decisions."""
    print("\n" + "=" * 60)
    print("Example 4: Querying Historical Decisions")
    print("=" * 60)

    logger = DecisionLogger()

    # Query tech stack decisions
    tech_stack_history = logger.get_historical_decisions(
        category="tech_stack",
        limit=5,
    )

    print(f"\nFound {len(tech_stack_history)} tech stack decisions:")
    for decision in tech_stack_history:
        print(f"\n  • {decision['decision']}")
        print(f"    Rationale: {decision['rationale'][:80]}...")
        print(f"    Session: {decision.get('session_id', 'unknown')}")

    return logger


def example_learn_from_past(logger):
    """Example: Learning from past decisions."""
    print("\n" + "=" * 60)
    print("Example 5: Learning from Past Decisions")
    print("=" * 60)

    # Context for new decision
    context = {
        "category": "tech_stack",
        "project_type": "web_api",
        "feature_description": "REST API for e-commerce platform",
        "keywords": ["async", "api", "framework", "performance"],
    }

    print("\nContext:")
    print(f"  Project type: {context['project_type']}")
    print(f"  Feature: {context['feature_description']}")
    print(f"  Keywords: {', '.join(context['keywords'])}")

    # Learn from past
    relevant = logger.learn_from_past(context)

    print(f"\nFound {len(relevant)} relevant past decisions:")
    for i, decision in enumerate(relevant[:3], 1):
        print(f"\n{i}. {decision['decision']}")
        print(f"   Relevance score: {decision.get('relevance_score', 0):.2f}")
        print(f"   Rationale: {decision['rationale'][:80]}...")


def example_session_workflow():
    """Example: Complete session workflow."""
    print("\n" + "=" * 60)
    print("Example 6: Complete Session Workflow")
    print("=" * 60)

    # New session: Building a real-time notification service
    print("\nNew Session: Building real-time notification service")

    logger = DecisionLogger()

    # Decision 1: Framework
    print("\n📋 Making decision 1...")
    logger.log_decision(
        decision_type="tech_stack",
        decision={
            "decision": "Use FastAPI with WebSocket support",
            "rationale": "Native async support for real-time features",
            "phase": "plan",
            "context": {
                "confidence": "high",
                "choice": "FastAPI",
                "category": "framework",
            },
        },
    )

    # Decision 2: Message broker
    print("📋 Making decision 2...")
    logger.log_decision(
        decision_type="tech_stack",
        decision={
            "decision": "Use Redis as message broker",
            "rationale": "Fast pub/sub for real-time notifications",
            "phase": "plan",
            "context": {
                "confidence": "high",
                "choice": "Redis",
                "category": "database",
            },
        },
    )

    # Decision 3: Architecture pattern
    print("📋 Making decision 3...")
    logger.log_decision(
        decision_type="architecture",
        decision={
            "decision": "Event-driven architecture with pub/sub",
            "rationale": "Scales well for notification distribution",
            "phase": "plan",
            "context": {
                "confidence": "medium",
                "complexity_level": "moderate",
            },
        },
    )

    print(f"\n✓ Made 3 decisions for session {logger.session_id}")

    # Check if similar past decisions exist
    print("\n🔍 Checking for similar past decisions...")
    context = {
        "category": "tech_stack",
        "keywords": ["real-time", "websocket", "async"],
    }

    relevant = logger.learn_from_past(context)

    if relevant:
        print(f"Found {len(relevant)} similar decisions from past sessions")
        for decision in relevant[:2]:
            print(f"  • {decision['decision']}")
    else:
        print("No similar past decisions found - this is new territory!")

    # Aggregate to historical
    print("\n💾 Aggregating to historical for future learning...")
    logger.aggregate_to_historical()

    print("✓ Session complete")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)

    logger = DecisionLogger()

    # Missing required field
    try:
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                # Missing 'rationale'
            },
        )
    except ValueError as e:
        print(f"\n✓ Caught expected error: {e}")

    # Missing decision field
    try:
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "rationale": "Some rationale",
                # Missing 'decision'
            },
        )
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Decision Logger - Complete Examples")
    print("=" * 60)

    # Example 1: Tech stack decisions
    logger = example_tech_stack_decisions()

    # Example 2: Architecture decisions
    example_architecture_decisions(logger)

    # Example 3: Aggregate to historical
    example_aggregate_to_historical(logger)

    # Example 4: Query historical
    logger = example_query_historical()

    # Example 5: Learn from past
    example_learn_from_past(logger)

    # Example 6: Complete session workflow
    example_session_workflow()

    # Example 7: Error handling
    example_error_handling()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)

    print("\nKey Takeaways:")
    print("  • Log decisions with full rationale and context")
    print("  • Aggregate to historical for cross-session learning")
    print("  • Query historical to inform new decisions")
    print("  • Learn from past to avoid repeating mistakes")
    print("  • Use relevance scoring to find applicable past decisions")


if __name__ == "__main__":
    main()
