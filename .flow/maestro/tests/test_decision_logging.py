#!/usr/bin/env python3
"""
Comprehensive Tests for Enhanced Decision Logging

Tests for:
- Structured logging with full context
- Decision lineage tracking
- Decision impact assessment
- Decision query interface
- Export functionality (JSON, CSV)
"""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# Add decision-engine scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "decision-engine" / "scripts"))

from decision_logger import (
    Decision,
    DecisionLog,
    DecisionLineage,
    DecisionImpact,
    DecisionQuery,
    DecisionLogger,
    RiskLevel,
    ConfidenceLevel,
)


class TestDecisionLineage(unittest.TestCase):
    """Test DecisionLineage functionality."""

    def test_lineage_creation(self):
        """Test creating lineage."""
        lineage = DecisionLineage(
            parent_decision_id="decision-001",
            child_decision_ids=["decision-002", "decision-003"],
            related_decisions=["decision-004"],
        )

        self.assertEqual(lineage.parent_decision_id, "decision-001")
        self.assertEqual(len(lineage.child_decision_ids), 2)
        self.assertEqual(len(lineage.related_decisions), 1)

    def test_lineage_to_dict(self):
        """Test converting lineage to dictionary."""
        lineage = DecisionLineage(
            parent_decision_id="decision-001",
            child_decision_ids=["decision-002"],
        )

        data = lineage.to_dict()

        self.assertEqual(data["parent_decision_id"], "decision-001")
        self.assertIsInstance(data["child_decision_ids"], list)

    def test_lineage_from_dict(self):
        """Test creating lineage from dictionary."""
        data = {
            "parent_decision_id": "decision-001",
            "child_decision_ids": ["decision-002"],
            "related_decisions": [],
        }

        lineage = DecisionLineage.from_dict(data)

        self.assertEqual(lineage.parent_decision_id, "decision-001")
        self.assertEqual(lineage.child_decision_ids, ["decision-002"])

    def test_empty_lineage(self):
        """Test creating empty lineage."""
        lineage = DecisionLineage()

        self.assertIsNone(lineage.parent_decision_id)
        self.assertEqual(len(lineage.child_decision_ids), 0)
        self.assertEqual(len(lineage.related_decisions), 0)


class TestDecisionImpact(unittest.TestCase):
    """Test DecisionImpact functionality."""

    def test_impact_creation(self):
        """Test creating impact assessment."""
        impact = DecisionImpact(
            files_modified=["src/main.py", "src/utils.py"],
            tests_affected=["test_main.py", "test_utils.py"],
            risk_level=RiskLevel.HIGH.value,
            rollback_available=True,
            scope="codebase",
            reversibility="moderate",
        )

        self.assertEqual(len(impact.files_modified), 2)
        self.assertEqual(len(impact.tests_affected), 2)
        self.assertEqual(impact.risk_level, RiskLevel.HIGH.value)
        self.assertTrue(impact.rollback_available)

    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        # High risk scenario
        impact_high = DecisionImpact(
            files_modified=["file"] * 25,  # > 20 files
            tests_affected=["test"] * 15,  # > 10 tests
            risk_level=RiskLevel.HIGH.value,
            rollback_available=False,
            reversibility="difficult",
        )

        score = impact_high.calculate_risk_score()
        self.assertGreater(score, 0.8)  # Should be very high

        # Low risk scenario
        impact_low = DecisionImpact(
            files_modified=["file1.py"],
            tests_affected=["test1.py"],
            risk_level=RiskLevel.LOW.value,
            rollback_available=True,
            reversibility="easy",
        )

        score = impact_low.calculate_risk_score()
        self.assertLess(score, 0.3)  # Should be low

    def test_impact_to_dict(self):
        """Test converting impact to dictionary."""
        impact = DecisionImpact(
            files_modified=["src/main.py"],
            risk_level=RiskLevel.MEDIUM.value,
        )

        data = impact.to_dict()

        self.assertEqual(data["files_modified"], ["src/main.py"])
        self.assertEqual(data["risk_level"], RiskLevel.MEDIUM.value)

    def test_impact_from_dict(self):
        """Test creating impact from dictionary."""
        data = {
            "files_modified": ["src/main.py"],
            "tests_affected": ["test_main.py"],
            "risk_level": RiskLevel.HIGH.value,
            "rollback_available": True,
            "scope": "codebase",
            "reversibility": "easy",
        }

        impact = DecisionImpact.from_dict(data)

        self.assertEqual(impact.files_modified, ["src/main.py"])
        self.assertTrue(impact.rollback_available)


class TestDecisionEnhanced(unittest.TestCase):
    """Test enhanced Decision functionality."""

    def test_decision_with_lineage(self):
        """Test decision with lineage tracking."""
        lineage = DecisionLineage(
            parent_decision_id="decision-001",
            child_decision_ids=["decision-003"],
        )

        decision = Decision(
            decision_id="decision-002",
            timestamp="2024-01-01T00:00:00",
            category="architecture",
            decision="Use repository pattern",
            rationale="Separates concerns",
            lineage=lineage,
        )

        self.assertEqual(decision.lineage.parent_decision_id, "decision-001")
        self.assertEqual(decision.lineage.child_decision_ids, ["decision-003"])

    def test_decision_with_impact_assessment(self):
        """Test decision with impact assessment."""
        impact = DecisionImpact(
            files_modified=["src/repo.py"],
            tests_affected=["test_repo.py"],
            risk_level=RiskLevel.LOW.value,
            rollback_available=True,
        )

        decision = Decision(
            decision_id="decision-001",
            timestamp="2024-01-01T00:00:00",
            category="architecture",
            decision="Use repository pattern",
            rationale="Separates concerns",
            impact_assessment=impact,
        )

        self.assertIsNotNone(decision.impact_assessment)
        self.assertEqual(len(decision.impact_assessment.files_modified), 1)

    def test_decision_get_risk_score(self):
        """Test getting risk score from decision."""
        impact = DecisionImpact(
            risk_level=RiskLevel.HIGH.value,
            files_modified=["file"] * 25,
        )

        decision = Decision(
            decision_id="decision-001",
            timestamp="2024-01-01T00:00:00",
            category="architecture",
            decision="High risk change",
            rationale="Complex refactoring",
            impact_assessment=impact,
        )

        score = decision.get_risk_score()
        self.assertGreater(score, 0.7)

    def test_decision_to_dict_with_enhancements(self):
        """Test converting enhanced decision to dictionary."""
        lineage = DecisionLineage(parent_decision_id="decision-001")
        impact = DecisionImpact(
            files_modified=["src/main.py"],
            risk_level=RiskLevel.MEDIUM.value,
        )

        decision = Decision(
            decision_id="decision-002",
            timestamp="2024-01-01T00:00:00",
            category="tech_stack",
            decision="Use FastAPI",
            rationale="Modern async framework",
            lineage=lineage,
            impact_assessment=impact,
            confidence=ConfidenceLevel.HIGH.value,
        )

        data = decision.to_dict()

        self.assertIn("lineage", data)
        self.assertIn("impact_assessment", data)
        self.assertEqual(data["confidence"], ConfidenceLevel.HIGH.value)

    def test_decision_from_dict_with_enhancements(self):
        """Test creating enhanced decision from dictionary."""
        data = {
            "decision_id": "decision-001",
            "timestamp": "2024-01-01T00:00:00",
            "category": "tech_stack",
            "decision": "Use PostgreSQL",
            "rationale": "ACID compliance",
            "lineage": {
                "parent_decision_id": None,
                "child_decision_ids": [],
                "related_decisions": [],
            },
            "impact_assessment": {
                "files_modified": ["src/db.py"],
                "tests_affected": ["test_db.py"],
                "risk_level": RiskLevel.MEDIUM.value,
                "rollback_available": True,
                "scope": "codebase",
                "reversibility": "moderate",
            },
            "confidence": ConfidenceLevel.HIGH.value,
        }

        decision = Decision.from_dict(data)

        self.assertIsNotNone(decision.lineage)
        self.assertIsNotNone(decision.impact_assessment)
        self.assertEqual(decision.confidence, ConfidenceLevel.HIGH.value)


class TestDecisionQuery(unittest.TestCase):
    """Test DecisionQuery functionality."""

    def setUp(self):
        """Set up test decisions."""
        self.decisions = [
            Decision(
                decision_id="d1",
                timestamp="2024-01-01T10:00:00",
                category="tech_stack",
                decision="Use Python",
                rationale="Team experience",
                phase="plan",
                confidence=ConfidenceLevel.HIGH.value,
            ),
            Decision(
                decision_id="d2",
                timestamp="2024-01-02T11:00:00",
                category="architecture",
                decision="MVC pattern",
                rationale="Separation of concerns",
                phase="plan",
                confidence=ConfidenceLevel.MEDIUM.value,
            ),
            Decision(
                decision_id="d3",
                timestamp="2024-01-03T12:00:00",
                category="tech_stack",
                decision="Use React",
                rationale="Component-based UI",
                phase="implement",
                confidence=ConfidenceLevel.HIGH.value,
            ),
        ]

    def test_filter_by_type(self):
        """Test filtering by decision type."""
        query = DecisionQuery(self.decisions)
        filtered = query.filter_by_type("tech_stack")

        self.assertEqual(len(filtered.to_list()), 2)
        self.assertEqual(filtered.to_list()[0].category, "tech_stack")

    def test_filter_by_time_range(self):
        """Test filtering by time range."""
        query = DecisionQuery(self.decisions)
        filtered = query.filter_by_time_range(
            "2024-01-01T00:00:00",
            "2024-01-02T23:59:59",
        )

        self.assertEqual(len(filtered.to_list()), 2)

    def test_filter_by_confidence(self):
        """Test filtering by confidence level."""
        query = DecisionQuery(self.decisions)
        filtered = query.filter_by_confidence(ConfidenceLevel.HIGH.value)

        self.assertEqual(len(filtered.to_list()), 2)
        for d in filtered.to_list():
            self.assertEqual(d.confidence, ConfidenceLevel.HIGH.value)

    def test_filter_by_phase(self):
        """Test filtering by phase."""
        query = DecisionQuery(self.decisions)
        filtered = query.filter_by_phase("plan")

        self.assertEqual(len(filtered.to_list()), 2)

    def test_sort_by_time(self):
        """Test sorting by time."""
        query = DecisionQuery(self.decisions)
        sorted_query = query.sort_by_time(descending=True)

        decisions = sorted_query.to_list()
        self.assertEqual(decisions[0].decision_id, "d3")  # Latest

    def test_sort_by_risk(self):
        """Test sorting by risk score."""
        decisions_with_risk = self.decisions.copy()
        # Add impact to create different risk scores
        decisions_with_risk[0].impact_assessment = DecisionImpact(
            risk_level=RiskLevel.LOW.value
        )
        decisions_with_risk[1].impact_assessment = DecisionImpact(
            risk_level=RiskLevel.HIGH.value
        )

        query = DecisionQuery(decisions_with_risk)
        sorted_query = query.sort_by_risk(descending=True)

        decisions = sorted_query.to_list()
        # d2 should be first (highest risk)
        self.assertEqual(decisions[0].decision_id, "d2")

    def test_limit(self):
        """Test limiting results."""
        query = DecisionQuery(self.decisions)
        limited = query.limit(2)

        self.assertEqual(len(limited.to_list()), 2)

    def test_chain_filters(self):
        """Test chaining multiple filters."""
        query = DecisionQuery(self.decisions)
        filtered = (query
                   .filter_by_type("tech_stack")
                   .filter_by_confidence(ConfidenceLevel.HIGH.value)
                   .sort_by_time())

        self.assertEqual(len(filtered.to_list()), 2)
        self.assertEqual(filtered.to_list()[0].category, "tech_stack")


class TestDecisionLoggerEnhanced(unittest.TestCase):
    """Test enhanced DecisionLogger functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir) / ".flow" / "maestro"
        self.session_id = "test-session-123"

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_log_decision_with_lineage(self):
        """Test logging decision with parent-child relationship."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Log parent decision
        parent_id = logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                "rationale": "Team experience",
            },
        )

        # Log child decision
        child_id = logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Use repository pattern",
                "rationale": "Clean separation",
            },
            parent_decision_id=parent_id,
        )

        # Verify lineage
        parent_decision = logger.get_session_decisions()[0]
        self.assertEqual(parent_decision.lineage.child_decision_ids, [child_id])

        child_decision = logger.get_session_decisions()[1]
        self.assertEqual(child_decision.lineage.parent_decision_id, parent_id)

    def test_log_decision_with_impact_assessment(self):
        """Test logging decision with impact assessment."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        decision_id = logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Refactor database layer",
                "rationale": "Improve performance",
            },
            impact_assessment={
                "files_modified": [
                    "src/db/connection.py",
                    "src/db/models.py",
                    "src/db/repositories.py",
                ],
                "tests_affected": [
                    "test/test_connection.py",
                    "test/test_models.py",
                ],
                "risk_level": RiskLevel.HIGH.value,
                "rollback_available": True,
                "scope": "codebase",
                "reversibility": "moderate",
            },
        )

        decisions = logger.get_session_decisions()
        self.assertEqual(len(decisions), 1)

        decision = decisions[0]
        self.assertIsNotNone(decision.impact_assessment)
        self.assertEqual(len(decision.impact_assessment.files_modified), 3)
        self.assertEqual(len(decision.impact_assessment.tests_affected), 2)
        self.assertEqual(decision.impact_assessment.risk_level, RiskLevel.HIGH.value)

    def test_trace_decision(self):
        """Test tracing decision lineage."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Create decision chain: d1 -> d2 -> d3
        d1_id = logger.log_decision(
            decision_type="tech_stack",
            decision={"decision": "D1", "rationale": "Root"},
        )
        d2_id = logger.log_decision(
            decision_type="architecture",
            decision={"decision": "D2", "rationale": "Child of D1"},
            parent_decision_id=d1_id,
        )
        d3_id = logger.log_decision(
            decision_type="architecture",
            decision={"decision": "D3", "rationale": "Child of D2"},
            parent_decision_id=d2_id,
        )

        # Trace d3
        lineage = logger.trace_decision(d3_id)

        self.assertIn("decision", lineage)
        self.assertIn("parent", lineage)
        self.assertIn("lineage_chain", lineage)
        self.assertEqual(len(lineage["lineage_chain"]), 3)  # d1 -> d2 -> d3

    def test_query_decisions_by_type(self):
        """Test querying decisions by type."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={"decision": "Use Python", "rationale": "Team exp"},
        )
        logger.log_decision(
            decision_type="architecture",
            decision={"decision": "MVC", "rationale": "Separation"},
        )
        logger.log_decision(
            decision_type="tech_stack",
            decision={"decision": "Use React", "rationale": "UI"},
        )

        # Query tech_stack decisions
        results = logger.query_decisions(decision_type="tech_stack")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["category"], "tech_stack")

    def test_query_decisions_by_confidence(self):
        """Test querying decisions by confidence."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                "rationale": "Team exp",
                "context": {"confidence": ConfidenceLevel.HIGH.value},
            },
        )
        logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "MVC",
                "rationale": "Separation",
                "context": {"confidence": ConfidenceLevel.LOW.value},
            },
        )

        # Query high confidence decisions
        results = logger.query_decisions(min_confidence=ConfidenceLevel.HIGH.value)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["confidence"], ConfidenceLevel.HIGH.value)

    def test_query_decisions_by_risk_level(self):
        """Test querying decisions by risk level."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="architecture",
            decision={"decision": "Low risk change", "rationale": "Simple"},
            impact_assessment={"risk_level": RiskLevel.LOW.value},
        )
        logger.log_decision(
            decision_type="architecture",
            decision={"decision": "High risk change", "rationale": "Complex"},
            impact_assessment={"risk_level": RiskLevel.HIGH.value},
        )

        # Query low risk decisions
        results = logger.query_decisions(risk_level=RiskLevel.LOW.value)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["impact_assessment"]["risk_level"], RiskLevel.LOW.value)

    def test_query_decisions_with_multiple_filters(self):
        """Test querying with multiple filters."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Create decisions with different attributes
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                "rationale": "Team exp",
                "phase": "plan",
                "context": {"confidence": ConfidenceLevel.HIGH.value},
            },
            impact_assessment={"risk_level": RiskLevel.LOW.value},
        )
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use React",
                "rationale": "UI",
                "phase": "implement",
                "context": {"confidence": ConfidenceLevel.MEDIUM.value},
            },
            impact_assessment={"risk_level": RiskLevel.MEDIUM.value},
        )

        # Query with multiple filters
        results = logger.query_decisions(
            decision_type="tech_stack",
            min_confidence=ConfidenceLevel.HIGH.value,
            phase="plan",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["decision"], "Use Python")

    def test_export_decisions_json(self):
        """Test exporting decisions to JSON."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={"decision": "Use Python", "rationale": "Team exp"},
        )

        output_path = logger.export_decisions(format="json")

        self.assertTrue(Path(output_path).exists())

        # Verify content
        with open(output_path) as f:
            data = json.load(f)

        self.assertIn("session_id", data)
        self.assertIn("decisions", data)
        self.assertEqual(len(data["decisions"]), 1)

    def test_export_decisions_csv(self):
        """Test exporting decisions to CSV."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                "rationale": "Team experience",
                "context": {"confidence": ConfidenceLevel.HIGH.value},
            },
            impact_assessment={
                "files_modified": ["src/main.py"],
                "tests_affected": ["test_main.py"],
                "risk_level": RiskLevel.LOW.value,
            },
        )

        output_path = logger.export_decisions(format="csv")

        self.assertTrue(Path(output_path).exists())

        # Verify content
        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["decision"], "Use Python")
        self.assertEqual(rows[0]["confidence"], ConfidenceLevel.HIGH.value)

    def test_export_decisions_with_filters(self):
        """Test exporting decisions with filters."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={"decision": "Use Python", "rationale": "Team exp"},
        )
        logger.log_decision(
            decision_type="architecture",
            decision={"decision": "MVC", "rationale": "Separation"},
        )

        # Export only tech_stack decisions
        output_path = logger.export_decisions(
            format="json",
            filters={"decision_type": "tech_stack"},
        )

        with open(output_path) as f:
            data = json.load(f)

        self.assertEqual(len(data["decisions"]), 1)
        self.assertEqual(data["decisions"][0]["category"], "tech_stack")

    def test_persistence_with_enhancements(self):
        """Test that enhanced decisions persist correctly."""
        logger1 = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        parent_id = logger1.log_decision(
            decision_type="tech_stack",
            decision={"decision": "Use Python", "rationale": "Team exp"},
        )

        logger1.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Repository pattern",
                "rationale": "Clean separation",
            },
            parent_decision_id=parent_id,
            impact_assessment={
                "files_modified": ["src/repo.py"],
                "risk_level": RiskLevel.MEDIUM.value,
            },
        )

        # Create new logger instance
        logger2 = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        decisions = logger2.get_session_decisions()
        self.assertEqual(len(decisions), 2)

        # Verify lineage persisted
        self.assertEqual(decisions[1].lineage.parent_decision_id, parent_id)
        self.assertEqual(decisions[0].lineage.child_decision_ids, [decisions[1].decision_id])

        # Verify impact persisted
        self.assertIsNotNone(decisions[1].impact_assessment)
        self.assertEqual(decisions[1].impact_assessment.risk_level, RiskLevel.MEDIUM.value)

    def test_enhanced_summary(self):
        """Test enhanced summary with risk scores."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                "rationale": "Team exp",
                "context": {"confidence": ConfidenceLevel.HIGH.value},
            },
            impact_assessment={"risk_level": RiskLevel.LOW.value},
        )
        logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Complex refactor",
                "rationale": "Performance",
                "context": {"confidence": ConfidenceLevel.LOW.value},
            },
            impact_assessment={"risk_level": RiskLevel.HIGH.value},
        )

        summary = logger.export_summary()

        self.assertIn("average_risk_score", summary["summary"])
        self.assertGreater(summary["summary"]["average_risk_score"], 0)


class TestDecisionLoggerIntegration(unittest.TestCase):
    """Integration tests for enhanced decision logger."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir) / ".flow" / "maestro"

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_full_workflow_with_enhancements(self):
        """Test complete workflow with lineage, impact, and querying."""
        # Session 1: Make decisions with relationships
        logger1 = DecisionLogger(base_path=self.base_path)

        # Root decision
        root_id = logger1.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use FastAPI",
                "rationale": "Modern async framework",
                "context": {"confidence": ConfidenceLevel.HIGH.value},
            },
            impact_assessment={
                "files_modified": ["src/api/main.py"],
                "risk_level": RiskLevel.LOW.value,
            },
        )

        # Child decision
        child_id = logger1.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Repository pattern",
                "rationale": "Clean separation",
                "phase": "plan",
            },
            parent_decision_id=root_id,
            impact_assessment={
                "files_modified": [
                    "src/repo/base.py",
                    "src/repo/user.py",
                ],
                "tests_affected": ["test/test_repo.py"],
                "risk_level": RiskLevel.MEDIUM.value,
            },
        )

        # Query high-confidence decisions
        high_conf = logger1.query_decisions(
            min_confidence=ConfidenceLevel.HIGH.value,
        )
        self.assertEqual(len(high_conf), 1)

        # Query tech_stack decisions
        tech_stack = logger1.query_decisions(decision_type="tech_stack")
        self.assertEqual(len(tech_stack), 1)

        # Trace lineage
        lineage = logger1.trace_decision(child_id)
        self.assertEqual(len(lineage["lineage_chain"]), 2)

        # Export to JSON
        json_path = logger1.export_decisions(format="json")
        self.assertTrue(Path(json_path).exists())

        # Export to CSV
        csv_path = logger1.export_decisions(format="csv")
        self.assertTrue(Path(csv_path).exists())

        # Verify export content
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 2)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[""], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
