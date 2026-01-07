#!/usr/bin/env python3
"""
Tests for Decision Logger

Comprehensive test suite for decision logging, historical aggregation,
and learning from past decisions.
"""

import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from decision_logger import (
    Decision,
    DecisionLog,
    DecisionLogger,
)


class TestDecision(unittest.TestCase):
    """Test Decision dataclass."""

    def test_decision_creation(self):
        """Test creating a decision."""
        decision = Decision(
            decision_id="decision-001",
            timestamp="2024-01-01T00:00:00",
            category="tech_stack",
            decision="Use Python for backend",
            rationale="Team has extensive Python experience",
        )

        self.assertEqual(decision.decision_id, "decision-001")
        self.assertEqual(decision.category, "tech_stack")
        self.assertEqual(decision.decision, "Use Python for backend")

    def test_decision_to_dict(self):
        """Test converting decision to dictionary."""
        decision = Decision(
            decision_id="decision-001",
            timestamp="2024-01-01T00:00:00",
            category="architecture",
            decision="Use repository pattern",
            rationale="Separates business logic from data access",
            alternatives_considered=[
                {"option": "Active Record", "reason_rejected": "Tight coupling"},
            ],
            context={"confidence": "high"},
            impact={"scope": "codebase", "risk_level": "low"},
        )

        data = decision.to_dict()

        self.assertEqual(data["decision_id"], "decision-001")
        self.assertEqual(len(data["alternatives_considered"]), 1)
        self.assertEqual(data["context"]["confidence"], "high")
        self.assertEqual(data["impact"]["risk_level"], "low")


class TestDecisionLog(unittest.TestCase):
    """Test DecisionLog functionality."""

    def test_log_creation(self):
        """Test creating a decision log."""
        log = DecisionLog(session_id="test-session")

        self.assertEqual(log.session_id, "test-session")
        self.assertEqual(len(log.decisions), 0)
        self.assertIsInstance(log.generated_at, str)

    def test_add_decision(self):
        """Test adding decisions to log."""
        log = DecisionLog(session_id="test-session")

        decision = Decision(
            decision_id="decision-001",
            timestamp="2024-01-01T00:00:00",
            category="tech_stack",
            decision="Use PostgreSQL",
            rationale="ACID compliance required",
        )

        log.add_decision(decision)

        self.assertEqual(len(log.decisions), 1)
        self.assertEqual(log.decisions[0].decision_id, "decision-001")

    def test_summary_updates(self):
        """Test summary statistics update."""
        log = DecisionLog(session_id="test-session")

        # Add high confidence decision
        log.add_decision(
            Decision(
                decision_id="d1",
                timestamp="2024-01-01T00:00:00",
                category="tech_stack",
                decision="Decision 1",
                rationale="Rationale 1",
                context={"confidence": "high"},
                impact={"risk_level": "low"},
            )
        )

        # Add low confidence, high risk decision
        log.add_decision(
            Decision(
                decision_id="d2",
                timestamp="2024-01-01T00:00:00",
                category="architecture",
                decision="Decision 2",
                rationale="Rationale 2",
                context={"confidence": "low"},
                impact={"risk_level": "high"},
            )
        )

        summary = log.summary

        self.assertEqual(summary["total_decisions"], 2)
        self.assertEqual(summary["decisions_by_category"]["tech_stack"], 1)
        self.assertEqual(summary["decisions_by_category"]["architecture"], 1)
        self.assertEqual(summary["high_confidence_decisions"], 1)
        self.assertEqual(summary["high_risk_decisions"], 1)

    def test_to_dict(self):
        """Test converting log to dictionary."""
        log = DecisionLog(session_id="test-session")
        log.add_decision(
            Decision(
                decision_id="d1",
                timestamp="2024-01-01T00:00:00",
                category="tech_stack",
                decision="Decision 1",
                rationale="Rationale 1",
            )
        )

        data = log.to_dict()

        self.assertEqual(data["session_id"], "test-session")
        self.assertEqual(len(data["decisions"]), 1)
        self.assertIn("summary", data)


class TestDecisionLogger(unittest.TestCase):
    """Test DecisionLogger main functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir) / ".flow" / "maestro"
        self.session_id = "test-session-123"

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_logger_initialization(self):
        """Test logger initialization creates directories."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        self.assertTrue(logger.base_path.exists())
        self.assertTrue(logger.session_dir.exists())
        self.assertTrue(logger.decisions_dir.exists())
        self.assertEqual(logger.session_id, self.session_id)

    def test_log_decision_basic(self):
        """Test basic decision logging."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        decision_id = logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use FastAPI framework",
                "rationale": "Modern async support with automatic OpenAPI",
            },
        )

        self.assertTrue(decision_id.startswith("decision-"))
        self.assertEqual(len(logger.get_session_decisions()), 1)

    def test_log_decision_with_full_context(self):
        """Test logging decision with full context."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        decision_id = logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Implement service layer pattern",
                "rationale": "Separates business logic from controllers",
                "phase": "plan",
                "alternatives_considered": [
                    {
                        "option": "Business logic in controllers",
                        "reason_rejected": "Violates single responsibility",
                    },
                ],
                "context": {
                    "confidence": "high",
                    "sources": ["SOLID principles", "Clean Architecture"],
                },
                "impact": {
                    "scope": "codebase",
                    "risk_level": "low",
                    "reversibility": "moderate",
                },
            },
        )

        decisions = logger.get_session_decisions()
        self.assertEqual(len(decisions), 1)

        decision = decisions[0]
        self.assertEqual(decision.phase, "plan")
        self.assertEqual(len(decision.alternatives_considered), 1)
        self.assertEqual(decision.context["confidence"], "high")
        self.assertEqual(decision.impact["reversibility"], "moderate")

    def test_log_decision_validation(self):
        """Test validation of required fields."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Missing 'decision' field
        with self.assertRaises(ValueError):
            logger.log_decision(
                decision_type="tech_stack",
                decision={"rationale": "Some rationale"},
            )

        # Missing 'rationale' field
        with self.assertRaises(ValueError):
            logger.log_decision(
                decision_type="tech_stack",
                decision={"decision": "Some decision"},
            )

    def test_decision_persistence(self):
        """Test decisions are persisted to file."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use TypeScript",
                "rationale": "Type safety reduces bugs",
            },
        )

        # Create new logger instance (simulating new session)
        logger2 = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        decisions = logger2.get_session_decisions()
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].decision, "Use TypeScript")

    def test_historical_aggregation(self):
        """Test aggregation to historical files."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Log tech stack decision
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use React",
                "rationale": "Component-based UI",
                "context": {"choice": "React", "category": "framework"},
            },
        )

        # Aggregate
        logger.aggregate_to_historical()

        # Check historical file exists
        historical_file = logger._get_historical_file("tech_stack")
        self.assertTrue(historical_file.exists())

        # Load and verify
        data = json.loads(historical_file.read_text())
        self.assertIn("decisions", data)
        self.assertEqual(len(data["decisions"]), 1)
        self.assertEqual(data["decisions"][0]["decision"], "Use React")

    def test_get_historical_decisions(self):
        """Test querying historical decisions."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Add some decisions and aggregate
        logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Use repository pattern",
                "rationale": "Separates concerns",
            },
        )

        logger.aggregate_to_historical()

        # Query historical
        historical = logger.get_historical_decisions(
            category="architecture",
            limit=10,
        )

        self.assertEqual(len(historical), 1)
        self.assertEqual(historical[0]["decision"], "Use repository pattern")

    def test_learn_from_past(self):
        """Test learning from past decisions."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Add some historical decisions
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use PostgreSQL for relational data",
                "rationale": "ACID compliance and complex queries",
                "context": {
                    "project_type": "web_api",
                    "feature_description": "E-commerce backend",
                },
            },
        )

        logger.aggregate_to_historical()

        # Query with similar context
        context = {
            "category": "tech_stack",
            "project_type": "web_api",
            "feature_description": "Online store backend",
            "keywords": ["database", "relational"],
        }

        relevant = logger.learn_from_past(context)

        # Should find the past decision
        self.assertGreater(len(relevant), 0)
        self.assertIn("relevance_score", relevant[0])
        self.assertGreater(relevant[0]["relevance_score"], 0)

    def test_relevance_scoring(self):
        """Test relevance score calculation."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Test exact match
        decision = {
            "category": "tech_stack",
            "decision": "Use Redis for caching",
            "rationale": "Fast in-memory operations",
        }

        context = {
            "category": "tech_stack",
            "keywords": ["Redis", "caching", "fast"],
            "project_type": "web_api",
            "feature_description": "Caching layer for API",
        }

        score = logger._calculate_relevance_score(decision, context)

        # Score should be significant due to multiple matches
        self.assertGreater(score, 0.3)

    def test_export_summary(self):
        """Test exporting session summary."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Add multiple decisions
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use Python",
                "rationale": "Team experience",
                "context": {"confidence": "high"},
            },
        )

        logger.log_decision(
            decision_type="architecture",
            decision={
                "decision": "MVC pattern",
                "rationale": "Separation of concerns",
                "context": {"confidence": "medium"},
            },
        )

        summary = logger.export_summary()

        self.assertEqual(summary["session_id"], self.session_id)
        self.assertEqual(summary["total_decisions"], 2)
        self.assertIn("tech_stack", summary["decisions_by_category"])
        self.assertIn("architecture", summary["decisions_by_category"])

    def test_multiple_sessions(self):
        """Test handling decisions from multiple sessions."""
        # Create first session
        logger1 = DecisionLogger(
            session_id="session-1",
            base_path=self.base_path,
        )

        logger1.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Node.js",
                "rationale": "JavaScript everywhere",
            },
        )

        # Create second session
        logger2 = DecisionLogger(
            session_id="session-2",
            base_path=self.base_path,
        )

        logger2.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Python",
                "rationale": "Data science capabilities",
            },
        )

        # Aggregate both
        logger1.aggregate_to_historical()
        logger2.aggregate_to_historical()

        # Query should see both
        historical = logger2.get_historical_decisions(category="tech_stack")
        self.assertEqual(len(historical), 2)

    def test_patterns_update(self):
        """Test pattern learning from historical data."""
        logger = DecisionLogger(
            session_id=self.session_id,
            base_path=self.base_path,
        )

        # Add decisions with outcomes
        logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use PostgreSQL",
                "rationale": "Relational data",
                "context": {
                    "choice": "PostgreSQL",
                    "category": "database",
                },
            },
        )

        logger.aggregate_to_historical()

        # Check patterns were created
        historical_file = logger._get_historical_file("tech_stack")
        data = json.loads(historical_file.read_text())

        self.assertIn("patterns", data)
        self.assertIn("preferred_by_category", data["patterns"])


class TestDecisionLoggerIntegration(unittest.TestCase):
    """Integration tests for decision logger workflow."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_path = Path(self.temp_dir) / ".flow" / "maestro"

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_full_workflow(self):
        """Test complete workflow from logging to learning."""
        # Session 1: Make decisions
        logger1 = DecisionLogger(base_path=self.base_path)

        logger1.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": "Use FastAPI",
                "rationale": "Modern async framework",
                "context": {"confidence": "high", "choice": "FastAPI", "category": "framework"},
            },
        )

        logger1.log_decision(
            decision_type="architecture",
            decision={
                "decision": "Repository pattern",
                "rationale": "Clean separation of concerns",
            },
        )

        # Aggregate
        logger1.aggregate_to_historical()

        # Session 2: Learn from past
        logger2 = DecisionLogger(base_path=self.base_path)

        context = {
            "category": "tech_stack",
            "project_type": "web_api",
            "keywords": ["async", "framework", "api"],
        }

        relevant = logger2.learn_from_past(context)

        # Should find the FastAPI decision
        self.assertGreater(len(relevant), 0)
        self.assertIn("FastAPI", relevant[0]["decision"])

        # Should also have historical architecture decisions
        arch_history = logger2.get_historical_decisions(category="architecture")
        self.assertGreater(len(arch_history), 0)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[""], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()
