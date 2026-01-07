#!/usr/bin/env python3
"""
Decision Logger for Maestro Orchestrator

Logs decisions with rationale and context, enables learning from past decisions.
Supports session-based logging and historical aggregation across sessions.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import re


@dataclass
class Decision:
    """Represents a single decision with full context."""

    decision_id: str
    timestamp: str
    category: str
    decision: str
    rationale: str
    phase: Optional[str] = None
    alternatives_considered: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    impact: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling datetime serialization."""
        data = asdict(self)
        # Ensure nested objects are properly serialized
        return data


@dataclass
class DecisionLog:
    """Complete decision log for a session."""

    session_id: str
    decisions: List[Decision] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: Dict[str, Any] = field(default_factory=dict)

    def add_decision(self, decision: Decision) -> None:
        """Add a decision to the log."""
        self.decisions.append(decision)
        self._update_summary()

    def _update_summary(self) -> None:
        """Update summary statistics."""
        total = len(self.decisions)
        by_category = defaultdict(int)
        high_confidence = 0
        high_risk = 0

        for decision in self.decisions:
            by_category[decision.category] += 1
            if decision.context.get("confidence") == "high":
                high_confidence += 1
            if decision.impact.get("risk_level") == "high":
                high_risk += 1

        self.summary = {
            "total_decisions": total,
            "decisions_by_category": dict(by_category),
            "high_confidence_decisions": high_confidence,
            "high_risk_decisions": high_risk,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "generated_at": self.generated_at,
            "decisions": [d.to_dict() for d in self.decisions],
            "summary": self.summary,
        }


class DecisionLogger:
    """
    Main decision logging system.

    Features:
    - Log decisions with full rationale and context
    - Persist to session-specific files
    - Aggregate decisions across sessions into historical records
    - Query past decisions to inform new choices
    - Learn from historical patterns
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        base_path: Optional[Path] = None,
    ):
        """
        Initialize the decision logger.

        Args:
            session_id: Optional session ID (generated if not provided)
            base_path: Base path for storage (defaults to .flow/maestro)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.base_path = base_path or Path.cwd() / ".flow" / "maestro"
        self.session_dir = self.base_path / "sessions" / self.session_id
        self.decisions_dir = self.base_path / "decisions"

        # Ensure directories exist
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)

        # In-memory decision log
        self._decision_log = DecisionLog(session_id=self.session_id)

        # Load existing session decisions if available
        self._load_session_decisions()

    def log_decision(
        self,
        decision_type: str,
        decision: Dict[str, Any],
    ) -> str:
        """
        Log a decision with full context.

        Args:
            decision_type: Category of decision (tech_stack, architecture, etc.)
            decision: Decision dictionary containing:
                - decision: The decision that was made (required)
                - rationale: Why this decision was made (required)
                - phase: Execution phase (optional)
                - alternatives_considered: List of alternatives (optional)
                - context: Additional context (optional)
                - impact: Expected impact (optional)

        Returns:
            The decision ID

        Raises:
            ValueError: If required fields are missing
        """
        if "decision" not in decision:
            raise ValueError("Decision must contain 'decision' field")
        if "rationale" not in decision:
            raise ValueError("Decision must contain 'rationale' field")

        # Create decision object
        decision_obj = Decision(
            decision_id=f"decision-{len(self._decision_log.decisions) + 1:03d}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=decision_type,
            decision=decision["decision"],
            rationale=decision["rationale"],
            phase=decision.get("phase"),
            alternatives_considered=decision.get("alternatives_considered", []),
            context=decision.get("context", {}),
            impact=decision.get("impact", {}),
        )

        # Add to log
        self._decision_log.add_decision(decision_obj)

        # Persist to file
        self._save_session_decisions()

        return decision_obj.decision_id

    def get_session_decisions(self, session_id: Optional[str] = None) -> List[Decision]:
        """
        Get all decisions for a session.

        Args:
            session_id: Session ID (uses current session if not provided)

        Returns:
            List of decisions for the session
        """
        if session_id and session_id != self.session_id:
            # Load from different session
            return self._load_other_session(session_id)
        return self._decision_log.decisions

    def get_historical_decisions(
        self,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Query historical decisions across all sessions.

        Args:
            category: Filter by decision category (optional)
            limit: Maximum number of decisions to return

        Returns:
            List of historical decisions with context
        """
        historical = []

        # Load historical files by category
        if category:
            historical_file = self._get_historical_file(category)
            if historical_file.exists():
                data = json.loads(historical_file.read_text())
                decisions = data.get("decisions", [])
                # Sort by timestamp (newest first) and limit
                decisions.sort(
                    key=lambda d: d.get("timestamp", ""), reverse=True
                )
                historical = decisions[:limit]
        else:
            # Search all historical files
            for hist_file in self.decisions_dir.glob("historational-*.json"):
                data = json.loads(hist_file.read_text())
                decisions = data.get("decisions", [])
                historical.extend(decisions)

            # Sort by timestamp (newest first) and limit
            historical.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
            historical = historical[:limit]

        return historical

    def learn_from_past(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query past decisions to inform new choices.

        Finds similar contexts and returns relevant historical decisions
        with outcomes and patterns.

        Args:
            context: Context dictionary containing:
                - category: Decision category (required)
                - feature_description: Description of current feature
                - project_type: Type of project
                - constraints: Any constraints
                - keywords: Additional keywords for matching

        Returns:
            List of relevant historical decisions with lessons learned
        """
        category = context.get("category")
        if not category:
            return []

        # Load historical decisions for category
        historical = self.get_historical_decisions(category=category, limit=100)

        # Score relevance based on context similarity
        scored_decisions = []
        for decision in historical:
            score = self._calculate_relevance_score(decision, context)
            if score > 0:
                decision["relevance_score"] = score
                scored_decisions.append(decision)

        # Sort by relevance and return top results
        scored_decisions.sort(key=lambda d: d["relevance_score"], reverse=True)
        return scored_decisions[:10]

    def aggregate_to_historical(self) -> None:
        """
        Aggregate session decisions into historical records.

        Called at the end of a session to update historical knowledge base.
        """
        if not self._decision_log.decisions:
            return

        # Group decisions by category
        by_category = defaultdict(list)
        for decision in self._decision_log.decisions:
            by_category[decision.category].append(decision)

        # Update each category's historical file
        for category, decisions in by_category.items():
            self._update_historical_category(category, decisions)

    def _calculate_relevance_score(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> float:
        """
        Calculate relevance score between a historical decision and current context.

        Higher score = more relevant (0.0 to 1.0)
        """
        score = 0.0

        # Category match (already filtered, but check anyway)
        if decision.get("category") == context.get("category"):
            score += 0.3

        # Keyword matching in rationale and decision
        keywords = context.get("keywords", [])
        decision_text = (
            decision.get("decision", "") + " " + decision.get("rationale", "")
        ).lower()

        for keyword in keywords:
            if keyword.lower() in decision_text:
                score += 0.1

        # Project type match
        decision_context = decision.get("context", {})
        if (
            context.get("project_type")
            and decision_context.get("project_type") == context.get("project_type")
        ):
            score += 0.2

        # Feature description similarity
        if context.get("feature_description"):
            feature_desc = context["feature_description"].lower()
            decision_desc = decision.get("decision", "").lower()
            # Simple word overlap
            feature_words = set(feature_desc.split())
            decision_words = set(decision_desc.split())
            overlap = len(feature_words & decision_words)
            if feature_words:
                score += 0.4 * (overlap / len(feature_words))

        # Cap at 1.0
        return min(score, 1.0)

    def _update_historical_category(
        self,
        category: str,
        new_decisions: List[Decision],
    ) -> None:
        """Update historical file for a category."""
        historical_file = self._get_historical_file(category)

        # Load existing data or create new structure
        if historical_file.exists():
            data = json.loads(historical_file.read_text())
        else:
            data = self._create_historical_structure(category)

        # Add new decisions
        for decision in new_decisions:
            decision_dict = decision.to_dict()
            decision_dict["session_id"] = self.session_id
            data["decisions"].append(decision_dict)

        # Update patterns based on category
        self._update_patterns(data, category)

        # Update metadata
        data["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Save
        historical_file.write_text(json.dumps(data, indent=2))

    def _create_historical_structure(self, category: str) -> Dict[str, Any]:
        """Create initial structure for historical file."""
        return {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "decisions": [],
            "patterns": self._get_empty_patterns(category),
        }

    def _get_empty_patterns(self, category: str) -> Dict[str, Any]:
        """Get empty patterns structure for category."""
        if category == "tech_stack":
            return {
                "preferred_by_category": {},
                "avoid_list": [],
            }
        elif category == "architecture":
            return {
                "codebase_fingerprints": {},
                "preferred_by_scenario": {},
                "anti_patterns": [],
            }
        elif category == "task_ordering":
            return {
                "effective_patterns": [],
                "ordering_rules": [],
                "anti_patterns": [],
                "category_best_practices": {},
            }
        return {}

    def _update_patterns(self, data: Dict[str, Any], category: str) -> None:
        """Update learned patterns based on new decisions."""
        if category == "tech_stack":
            self._update_tech_stack_patterns(data)
        elif category == "architecture":
            self._update_architecture_patterns(data)
        elif category == "task_ordering":
            self._update_task_ordering_patterns(data)

    def _update_tech_stack_patterns(self, data: Dict[str, Any]) -> None:
        """Update patterns for tech stack decisions."""
        preferred = data["patterns"]["preferred_by_category"]
        avoid = data["patterns"]["avoid_list"]

        # Analyze outcomes and update preferences
        by_choice = defaultdict(list)
        for decision in data["decisions"]:
            choice = decision.get("choice", "unknown")
            by_choice[choice].append(decision)

        for choice, decisions in by_choice.items():
            successful = sum(
                1 for d in decisions if d.get("outcome", {}).get("successful", False)
            )
            success_rate = successful / len(decisions) if decisions else 0

            category = decisions[0].get("category", "other")
            if category not in preferred or success_rate > preferred[category]["success_rate"]:
                preferred[category] = {
                    "technology": choice,
                    "success_rate": success_rate,
                    "usage_count": len(decisions),
                }

            # Add to avoid list if consistently failing
            if success_rate < 0.3 and len(decisions) >= 2:
                avoid.append({
                    "technology": choice,
                    "reason": f"Low success rate ({success_rate:.1%})",
                    "failure_count": len(decisions) - successful,
                })

    def _update_architecture_patterns(self, data: Dict[str, Any]) -> None:
        """Update patterns for architecture decisions."""
        patterns = data["patterns"]

        # Update codebase fingerprints
        fingerprints = patterns["codebase_fingerprints"]
        for decision in data["decisions"]:
            pattern_name = decision.get("pattern_name", "unknown")
            if pattern_name not in fingerprints:
                fingerprints[pattern_name] = {
                    "pattern_name": pattern_name,
                    "usage_frequency": 0,
                    "consistency_score": 1.0,
                }
            fingerprints[pattern_name]["usage_frequency"] += 1

        # Update anti-patterns based on outcomes
        for decision in data["decisions"]:
            outcome = decision.get("outcome", {})
            if not outcome.get("successful", False):
                patterns["anti_patterns"].append({
                    "pattern": decision.get("pattern_name", "unknown"),
                    "reason": outcome.get("lessons_learned", "Failed in practice"),
                    "context": decision.get("description", ""),
                })

    def _update_task_ordering_patterns(self, data: Dict[str, Any]) -> None:
        """Update patterns for task ordering decisions."""
        patterns = data["patterns"]

        # Extract effective patterns from successful sessions
        for session in data.get("sessions", data.get("decisions", [])):
            outcome = session.get("outcome", {})
            if outcome.get("all_tasks_completed", False):
                strategy = session.get("ordering_strategy", {})
                patterns["effective_patterns"].append({
                    "pattern": f"{strategy.get('primary_approach', 'unknown')} with {strategy.get('grouping_method', 'no')} grouping",
                    "success_rate": 1.0,
                    "applicable_scenarios": [session.get("feature_summary", "")],
                })

    def _get_historical_file(self, category: str) -> Path:
        """Get path to historical file for category."""
        # Map category to filename
        category_map = {
            "tech_stack": "historical-tech-stack.json",
            "architecture": "historical-architecture.json",
            "task_ordering": "historical-task-ordering.json",
        }
        filename = category_map.get(category, f"historical-{category}.json")
        return self.decisions_dir / filename

    def _load_session_decisions(self) -> None:
        """Load existing decisions from session file."""
        session_file = self.session_dir / "decisions.json"
        if session_file.exists():
            data = json.loads(session_file.read_text())
            decisions = data.get("decisions", [])
            self._decision_log.decisions = [
                Decision(**d) for d in decisions
            ]
            self._decision_log.summary = data.get("summary", {})
            self._decision_log.generated_at = data.get("generated_at", "")

    def _save_session_decisions(self) -> None:
        """Persist decisions to session file."""
        session_file = self.session_dir / "decisions.json"
        session_file.write_text(
            json.dumps(self._decision_log.to_dict(), indent=2)
        )

    def _load_other_session(self, session_id: str) -> List[Decision]:
        """Load decisions from another session."""
        session_path = self.base_path / "sessions" / session_id / "decisions.json"
        if session_path.exists():
            data = json.loads(session_path.read_text())
            return [Decision(**d) for d in data.get("decisions", [])]
        return []

    def export_summary(self) -> Dict[str, Any]:
        """
        Export a summary of all decisions in the current session.

        Returns:
            Summary dictionary with statistics and key decisions
        """
        return {
            "session_id": self.session_id,
            "total_decisions": len(self._decision_log.decisions),
            "summary": self._decision_log.summary,
            "decisions_by_category": self._group_decisions_by_category(),
        }

    def _group_decisions_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group decisions by category for summary."""
        grouped = defaultdict(list)
        for decision in self._decision_log.decisions:
            grouped[decision.category].append({
                "decision_id": decision.decision_id,
                "decision": decision.decision,
                "timestamp": decision.timestamp,
                "confidence": decision.context.get("confidence", "unknown"),
            })
        return dict(grouped)


def main():
    """CLI interface for decision logger."""
    import argparse

    parser = argparse.ArgumentParser(description="Decision Logger for Maestro")
    parser.add_argument(
        "--session-id",
        help="Session ID (generated if not provided)",
    )
    parser.add_argument(
        "--query",
        action="store_true",
        help="Query mode: retrieve historical decisions",
    )
    parser.add_argument(
        "--category",
        help="Filter by category",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit results",
    )
    parser.add_argument(
        "--learn",
        action="store_true",
        help="Learn mode: find relevant past decisions",
    )
    parser.add_argument(
        "--context",
        help="JSON context for learning",
    )
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Aggregate session decisions to historical",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Export session summary",
    )

    args = parser.parse_args()

    # Initialize logger
    logger = DecisionLogger(session_id=args.session_id)

    if args.query:
        # Query historical decisions
        decisions = logger.get_historical_decisions(
            category=args.category,
            limit=args.limit,
        )
        print(json.dumps(decisions, indent=2))

    elif args.learn:
        # Learn from past decisions
        if not args.context:
            print("Error: --context required for learn mode")
            return
        context = json.loads(args.context)
        decisions = logger.learn_from_past(context)
        print(json.dumps(decisions, indent=2))

    elif args.aggregate:
        # Aggregate to historical
        logger.aggregate_to_historical()
        print(f"Aggregated decisions for session {logger.session_id}")

    elif args.summary:
        # Export summary
        summary = logger.export_summary()
        print(json.dumps(summary, indent=2))

    else:
        # Interactive mode
        print(f"Decision Logger - Session: {logger.session_id}")
        print("Use --query, --learn, --aggregate, or --summary")


if __name__ == "__main__":
    main()
