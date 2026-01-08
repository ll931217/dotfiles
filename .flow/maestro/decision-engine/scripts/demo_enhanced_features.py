#!/usr/bin/env python3
"""
Demo script showcasing enhanced decision logging features.
"""

import tempfile
from pathlib import Path
from decision_logger import (
    DecisionLogger,
    RiskLevel,
    ConfidenceLevel,
)


def demo_enhanced_logging():
    """Demonstrate enhanced decision logging capabilities."""
    print("=" * 60)
    print("Enhanced Decision Logging Demo")
    print("=" * 60)

    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    base_path = Path(temp_dir) / ".flow" / "maestro"

    print("\n1. Creating logger...")
    logger = DecisionLogger(base_path=base_path)
    print(f"   Session ID: {logger.session_id}")

    print("\n2. Logging decisions with lineage...")
    # Root decision
    root_id = logger.log_decision(
        decision_type="tech_stack",
        decision={
            "decision": "Use FastAPI for backend API",
            "rationale": "Modern async framework with automatic OpenAPI",
            "context": {"confidence": ConfidenceLevel.HIGH.value},
        },
        impact_assessment={
            "files_modified": ["src/api/main.py"],
            "tests_affected": ["test/test_api.py"],
            "risk_level": RiskLevel.LOW.value,
            "rollback_available": True,
            "scope": "codebase",
            "reversibility": "easy",
        },
    )
    print(f"   Root decision: {root_id}")

    # Child decision
    child_id = logger.log_decision(
        decision_type="architecture",
        decision={
            "decision": "Implement repository pattern",
            "rationale": "Separate business logic from data access",
            "phase": "plan",
        },
        parent_decision_id=root_id,
        impact_assessment={
            "files_modified": [
                "src/repo/base.py",
                "src/repo/user.py",
                "src/repo/product.py",
            ],
            "tests_affected": ["test/test_repositories.py"],
            "risk_level": RiskLevel.MEDIUM.value,
            "rollback_available": True,
            "scope": "codebase",
            "reversibility": "moderate",
        },
    )
    print(f"   Child decision: {child_id}")

    # Another child decision
    child2_id = logger.log_decision(
        decision_type="architecture",
        decision={
            "decision": "Use dependency injection",
            "rationale": "Improve testability and loose coupling",
            "phase": "plan",
        },
        parent_decision_id=root_id,
        impact_assessment={
            "files_modified": ["src/di/container.py"],
            "tests_affected": ["test/test_di.py"],
            "risk_level": RiskLevel.MEDIUM.value,
            "rollback_available": True,
            "scope": "codebase",
            "reversibility": "moderate",
        },
    )
    print(f"   Second child: {child2_id}")

    print("\n3. Tracing decision lineage...")
    lineage = logger.trace_decision(child_id)
    print(f"   Decision: {lineage['decision']['decision']}")
    print(f"   Parent: {lineage['parent']['decision'] if lineage['parent'] else 'None'}")
    print(f"   Children count: {len(lineage['children'])}")
    print(f"   Lineage chain length: {len(lineage['lineage_chain'])}")

    print("\n4. Querying decisions...")
    # Query by type
    tech_decisions = logger.query_decisions(decision_type="tech_stack")
    print(f"   Tech stack decisions: {len(tech_decisions)}")

    # Query by confidence
    high_conf = logger.query_decisions(min_confidence=ConfidenceLevel.HIGH.value)
    print(f"   High confidence decisions: {len(high_conf)}")

    # Query by risk level
    low_risk = logger.query_decisions(risk_level=RiskLevel.LOW.value)
    print(f"   Low risk decisions: {len(low_risk)}")

    # Query with multiple filters
    filtered = logger.query_decisions(
        decision_type="architecture",
        phase="plan",
    )
    print(f"   Architecture decisions in plan phase: {len(filtered)}")

    print("\n5. Exporting decisions...")
    json_path = logger.export_decisions(format="json")
    print(f"   JSON export: {json_path}")

    csv_path = logger.export_decisions(format="csv")
    print(f"   CSV export: {csv_path}")

    print("\n6. Session summary...")
    summary = logger.export_summary()
    print(f"   Total decisions: {summary['total_decisions']}")
    print(f"   Average risk score: {summary['summary']['average_risk_score']}")
    print(f"   High confidence: {summary['summary']['high_confidence_decisions']}")
    print(f"   High risk: {summary['summary']['high_risk_decisions']}")

    print("\n7. Decision details...")
    decisions = logger.get_session_decisions()
    for d in decisions:
        print(f"   {d.decision_id}: {d.decision}")
        print(f"      Risk score: {d.get_risk_score():.2f}")
        print(f"      Confidence: {d.confidence}")
        if d.impact_assessment:
            print(f"      Files: {len(d.impact_assessment.files_modified)}")
            print(f"      Tests: {len(d.impact_assessment.tests_affected)}")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    demo_enhanced_logging()
