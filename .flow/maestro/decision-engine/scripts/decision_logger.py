#!/usr/bin/env python3
"""
Decision Logger for Maestro Orchestrator

Logs decisions with rationale and context, enables learning from past decisions.
Supports session-based logging and historical aggregation across sessions.

Enhanced with:
- Decision lineage tracking (parent-child relationships)
- Decision impact assessment
- Comprehensive query interface
- Export functionality (JSON, CSV)
"""

import csv
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceLevel(Enum):
    """Confidence level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DecisionLineage:
    """Tracks decision dependencies and relationships."""
    parent_decision_id: Optional[str] = None
    child_decision_ids: List[str] = field(default_factory=list)
    related_decisions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionLineage":
        """Create from dictionary."""
        return cls(
            parent_decision_id=data.get("parent_decision_id"),
            child_decision_ids=data.get("child_decision_ids", []),
            related_decisions=data.get("related_decisions", []),
        )


@dataclass
class DecisionImpact:
    """Assesses decision impact with detailed metrics."""
    files_modified: List[str] = field(default_factory=list)
    tests_affected: List[str] = field(default_factory=list)
    risk_level: str = RiskLevel.MEDIUM.value
    rollback_available: bool = False
    scope: str = "unknown"  # codebase, tests, config, docs
    reversibility: str = "unknown"  # easy, moderate, difficult

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionImpact":
        """Create from dictionary."""
        return cls(
            files_modified=data.get("files_modified", []),
            tests_affected=data.get("tests_affected", []),
            risk_level=data.get("risk_level", RiskLevel.MEDIUM.value),
            rollback_available=data.get("rollback_available", False),
            scope=data.get("scope", "unknown"),
            reversibility=data.get("reversibility", "unknown"),
        )

    def calculate_risk_score(self) -> float:
        """Calculate overall risk score (0.0 to 1.0)."""
        score = 0.5  # Base score

        # Risk level contribution
        risk_weights = {RiskLevel.LOW.value: 0.0, RiskLevel.MEDIUM.value: 0.3, RiskLevel.HIGH.value: 0.6}
        score += risk_weights.get(self.risk_level, 0.3)

        # File count contribution
        file_count = len(self.files_modified)
        if file_count > 20:
            score += 0.3
        elif file_count > 10:
            score += 0.2
        elif file_count > 5:
            score += 0.1

        # Test impact contribution
        test_count = len(self.tests_affected)
        if test_count > 10:
            score += 0.2
        elif test_count > 5:
            score += 0.1

        # Rollback availability reduces risk
        if self.rollback_available:
            score -= 0.2

        # Reversibility contribution
        reversibility_weights = {"easy": -0.1, "moderate": 0.0, "difficult": 0.2}
        score += reversibility_weights.get(self.reversibility, 0.0)

        return max(0.0, min(1.0, score))


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
    lineage: DecisionLineage = field(default_factory=DecisionLineage)
    impact_assessment: Optional[DecisionImpact] = None
    confidence: str = ConfidenceLevel.MEDIUM.value

    def __post_init__(self):
        """Extract confidence from context if not explicitly provided."""
        # For backward compatibility: if confidence is still MEDIUM (default)
        # but context contains confidence, use that instead
        if self.confidence == ConfidenceLevel.MEDIUM.value and "confidence" in self.context:
            self.confidence = self.context["confidence"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling datetime serialization."""
        data = asdict(self)
        # Convert nested dataclasses
        if self.lineage:
            data["lineage"] = self.lineage.to_dict()
        if self.impact_assessment:
            data["impact_assessment"] = self.impact_assessment.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """Create from dictionary."""
        lineage_data = data.pop("lineage", {})
        impact_data = data.pop("impact_assessment", None)

        lineage = DecisionLineage.from_dict(lineage_data) if lineage_data else DecisionLineage()
        impact = DecisionImpact.from_dict(impact_data) if impact_data else None

        return cls(
            **data,
            lineage=lineage,
            impact_assessment=impact,
        )

    def get_risk_score(self) -> float:
        """Get decision risk score."""
        if self.impact_assessment:
            return self.impact_assessment.calculate_risk_score()

        # Fallback to basic impact data
        risk_level = self.impact.get("risk_level", RiskLevel.MEDIUM.value)
        # Handle both uppercase (enum) and lowercase (legacy) values
        risk_level_normalized = risk_level.upper() if isinstance(risk_level, str) else risk_level
        risk_weights = {
            RiskLevel.LOW.value: 0.2,
            "LOW": 0.2,
            RiskLevel.MEDIUM.value: 0.5,
            "MEDIUM": 0.5,
            RiskLevel.HIGH.value: 0.8,
            "HIGH": 0.8,
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
        }
        return risk_weights.get(risk_level, 0.5)


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
        total_risk_score = 0.0

        for decision in self.decisions:
            by_category[decision.category] += 1
            if decision.confidence == ConfidenceLevel.HIGH.value:
                high_confidence += 1

            risk_score = decision.get_risk_score()
            total_risk_score += risk_score
            if risk_score > 0.7:
                high_risk += 1

        avg_risk_score = total_risk_score / total if total > 0 else 0.0

        self.summary = {
            "total_decisions": total,
            "decisions_by_category": dict(by_category),
            "high_confidence_decisions": high_confidence,
            "high_risk_decisions": high_risk,
            "average_risk_score": round(avg_risk_score, 2),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "generated_at": self.generated_at,
            "decisions": [d.to_dict() for d in self.decisions],
            "summary": self.summary,
        }


class DecisionQuery:
    """Query interface for decision history."""

    def __init__(self, decisions: List[Decision]):
        """Initialize with a list of decisions."""
        self.decisions = decisions

    def filter_by_type(self, decision_type: str) -> "DecisionQuery":
        """Filter by decision type/category."""
        filtered = [d for d in self.decisions if d.category == decision_type]
        return DecisionQuery(filtered)

    def filter_by_time_range(
        self, start_time: str, end_time: str
    ) -> "DecisionQuery":
        """Filter by time range (ISO format strings)."""
        filtered = [
            d
            for d in self.decisions
            if start_time <= d.timestamp <= end_time
        ]
        return DecisionQuery(filtered)

    def filter_by_confidence(self, min_confidence: str) -> "DecisionQuery":
        """Filter by minimum confidence level."""
        confidence_order = [ConfidenceLevel.LOW.value, ConfidenceLevel.MEDIUM.value, ConfidenceLevel.HIGH.value]
        min_idx = confidence_order.index(min_confidence)

        filtered = [
            d for d in self.decisions
            if confidence_order.index(d.confidence) >= min_idx
        ]
        return DecisionQuery(filtered)

    def filter_by_impact_level(self, max_risk_score: float) -> "DecisionQuery":
        """Filter by maximum risk score."""
        filtered = [
            d for d in self.decisions
            if d.get_risk_score() <= max_risk_score
        ]
        return DecisionQuery(filtered)

    def filter_by_phase(self, phase: str) -> "DecisionQuery":
        """Filter by execution phase."""
        filtered = [d for d in self.decisions if d.phase == phase]
        return DecisionQuery(filtered)

    def filter_by_risk_level(self, risk_level: str) -> "DecisionQuery":
        """Filter by specific risk level."""
        filtered = [
            d for d in self.decisions
            if d.impact.get("risk_level") == risk_level
            or (d.impact_assessment and d.impact_assessment.risk_level == risk_level)
        ]
        return DecisionQuery(filtered)

    def trace_lineage(self, decision_id: str) -> List[Decision]:
        """Trace decision lineage (ancestors and descendants)."""
        lineage_decisions = []

        # Find the decision
        target = None
        for d in self.decisions:
            if d.decision_id == decision_id:
                target = d
                break

        if not target:
            return lineage_decisions

        # Add parent decision
        if target.lineage.parent_decision_id:
            for d in self.decisions:
                if d.decision_id == target.lineage.parent_decision_id:
                    lineage_decisions.append(d)
                    break

        # Add child decisions
        for child_id in target.lineage.child_decision_ids:
            for d in self.decisions:
                if d.decision_id == child_id:
                    lineage_decisions.append(d)
                    break

        # Add related decisions
        for related_id in target.lineage.related_decisions:
            for d in self.decisions:
                if d.decision_id == related_id:
                    lineage_decisions.append(d)
                    break

        return lineage_decisions

    def sort_by_time(self, descending: bool = True) -> "DecisionQuery":
        """Sort decisions by timestamp."""
        sorted_decisions = sorted(
            self.decisions,
            key=lambda d: d.timestamp,
            reverse=descending,
        )
        return DecisionQuery(sorted_decisions)

    def sort_by_risk(self, descending: bool = True) -> "DecisionQuery":
        """Sort decisions by risk score."""
        sorted_decisions = sorted(
            self.decisions,
            key=lambda d: d.get_risk_score(),
            reverse=descending,
        )
        return DecisionQuery(sorted_decisions)

    def limit(self, count: int) -> "DecisionQuery":
        """Limit results to specified count."""
        return DecisionQuery(self.decisions[:count])

    def to_list(self) -> List[Decision]:
        """Get decisions as a list."""
        return self.decisions

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Get decisions as a list of dictionaries."""
        return [d.to_dict() for d in self.decisions]

    def count(self) -> int:
        """Get count of decisions in query result."""
        return len(self.decisions)


class DecisionLogger:
    """
    Main decision logging system.

    Features:
    - Log decisions with full rationale and context
    - Track decision lineage and dependencies
    - Assess decision impact
    - Query decisions with multiple filters
    - Export to JSON/CSV formats
    - Persist to session-specific files
    - Aggregate decisions across sessions into historical records
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

        # Decision ID counter for generating unique IDs
        self._decision_counter = 0

        # Load existing session decisions if available
        self._load_session_decisions()

    def log_decision(
        self,
        decision_type: str,
        decision: Dict[str, Any],
        parent_decision_id: Optional[str] = None,
        impact_assessment: Optional[Dict[str, Any]] = None,
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
            parent_decision_id: ID of parent decision (for lineage tracking)
            impact_assessment: Detailed impact assessment dict containing:
                - files_modified: List of modified file paths
                - tests_affected: List of affected test files
                - risk_level: LOW, MEDIUM, or HIGH
                - rollback_available: Whether rollback is possible
                - scope: Scope of impact (codebase, tests, config, docs)
                - reversibility: easy, moderate, or difficult

        Returns:
            The decision ID

        Raises:
            ValueError: If required fields are missing
        """
        if "decision" not in decision:
            raise ValueError("Decision must contain 'decision' field")
        if "rationale" not in decision:
            raise ValueError("Decision must contain 'rationale' field")

        # Generate decision ID
        self._decision_counter += 1
        decision_id = f"decision-{self._decision_counter:03d}"

        # Create lineage if parent provided
        lineage = DecisionLineage(parent_decision_id=parent_decision_id)

        # Add this decision as child to parent
        if parent_decision_id:
            self._add_child_to_parent(parent_decision_id, decision_id)

        # Create impact assessment if provided
        impact_obj = None
        if impact_assessment:
            impact_obj = DecisionImpact(
                files_modified=impact_assessment.get("files_modified", []),
                tests_affected=impact_assessment.get("tests_affected", []),
                risk_level=impact_assessment.get("risk_level", RiskLevel.MEDIUM.value),
                rollback_available=impact_assessment.get("rollback_available", False),
                scope=impact_assessment.get("scope", "unknown"),
                reversibility=impact_assessment.get("reversibility", "unknown"),
            )

        # Get confidence from context
        confidence = decision.get("context", {}).get("confidence", ConfidenceLevel.MEDIUM.value)

        # Validate confidence
        if confidence not in [e.value for e in ConfidenceLevel]:
            confidence = ConfidenceLevel.MEDIUM.value

        # Create decision object
        decision_obj = Decision(
            decision_id=decision_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            category=decision_type,
            decision=decision["decision"],
            rationale=decision["rationale"],
            phase=decision.get("phase"),
            alternatives_considered=decision.get("alternatives_considered", []),
            context=decision.get("context", {}),
            impact=decision.get("impact", {}),
            lineage=lineage,
            impact_assessment=impact_obj,
            confidence=confidence,
        )

        # Add to log
        self._decision_log.add_decision(decision_obj)

        # Persist to file
        self._save_session_decisions()

        return decision_id

    def _add_child_to_parent(self, parent_id: str, child_id: str) -> None:
        """Add child decision ID to parent's lineage."""
        for decision in self._decision_log.decisions:
            if decision.decision_id == parent_id:
                decision.lineage.child_decision_ids.append(child_id)
                break

    def trace_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Trace a decision's lineage (ancestors and descendants).

        Args:
            decision_id: ID of decision to trace

        Returns:
            Dictionary with:
                - decision: The target decision
                - parent: Parent decision (if any)
                - children: List of child decisions
                - related: List of related decisions
                - lineage_chain: Full chain from root to this decision
        """
        # Find the decision
        target = None
        for d in self._decision_log.decisions:
            if d.decision_id == decision_id:
                target = d
                break

        if not target:
            return {"error": f"Decision {decision_id} not found"}

        # Build lineage chain (walk up to root)
        lineage_chain = []
        current = target
        while current:
            lineage_chain.insert(0, current.to_dict())
            if current.lineage.parent_decision_id:
                for d in self._decision_log.decisions:
                    if d.decision_id == current.lineage.parent_decision_id:
                        current = d
                        break
            else:
                current = None

        # Get parent
        parent = None
        if target.lineage.parent_decision_id:
            for d in self._decision_log.decisions:
                if d.decision_id == target.lineage.parent_decision_id:
                    parent = d.to_dict()
                    break

        # Get children
        children = []
        for child_id in target.lineage.child_decision_ids:
            for d in self._decision_log.decisions:
                if d.decision_id == child_id:
                    children.append(d.to_dict())
                    break

        # Get related decisions
        related = []
        for related_id in target.lineage.related_decisions:
            for d in self._decision_log.decisions:
                if d.decision_id == related_id:
                    related.append(d.to_dict())
                    break

        return {
            "decision": target.to_dict(),
            "parent": parent,
            "children": children,
            "related": related,
            "lineage_chain": lineage_chain,
        }

    def query_decisions(
        self,
        decision_type: Optional[str] = None,
        time_range: Optional[Dict[str, str]] = None,
        min_confidence: Optional[str] = None,
        max_risk_score: Optional[float] = None,
        phase: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query decisions with multiple filters.

        Args:
            decision_type: Filter by decision type
            time_range: Dict with 'start' and 'end' ISO format timestamps
            min_confidence: Minimum confidence level (low, medium, high)
            max_risk_score: Maximum risk score (0.0 to 1.0)
            phase: Filter by execution phase
            risk_level: Filter by specific risk level (LOW, MEDIUM, HIGH)
            limit: Maximum number of results

        Returns:
            List of decision dictionaries matching filters
        """
        query = DecisionQuery(self._decision_log.decisions)

        # Apply filters
        if decision_type:
            query = query.filter_by_type(decision_type)

        if time_range:
            query = query.filter_by_time_range(
                time_range["start"],
                time_range["end"],
            )

        if min_confidence:
            query = query.filter_by_confidence(min_confidence)

        if max_risk_score is not None:
            query = query.filter_by_impact_level(max_risk_score)

        if phase:
            query = query.filter_by_phase(phase)

        if risk_level:
            query = query.filter_by_risk_level(risk_level)

        # Sort by time (newest first)
        query = query.sort_by_time(descending=True)

        # Apply limit
        if limit:
            query = query.limit(limit)

        return query.to_dict_list()

    def export_decisions(
        self,
        format: str = "json",
        output_path: Optional[Path] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Export decisions to file.

        Args:
            format: Export format ('json' or 'csv')
            output_path: Path to export file (defaults to session directory)
            filters: Optional filters to apply before export

        Returns:
            Path to exported file

        Raises:
            ValueError: If format is not supported
        """
        # Get decisions to export
        if filters:
            decisions = self.query_decisions(**filters)
        else:
            decisions = [d.to_dict() for d in self._decision_log.decisions]

        # Generate output path if not provided
        if not output_path:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            if format == "json":
                output_path = self.session_dir / f"decisions_export_{timestamp}.json"
            elif format == "csv":
                output_path = self.session_dir / f"decisions_export_{timestamp}.csv"
            else:
                raise ValueError(f"Unsupported format: {format}")

        # Export based on format
        if format == "json":
            self._export_json(decisions, output_path)
        elif format == "csv":
            self._export_csv(decisions, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(output_path)

    def _export_json(self, decisions: List[Dict[str, Any]], output_path: Path) -> None:
        """Export decisions to JSON format."""
        export_data = {
            "session_id": self.session_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_decisions": len(decisions),
            "decisions": decisions,
        }

        output_path.write_text(json.dumps(export_data, indent=2))

    def _export_csv(self, decisions: List[Dict[str, Any]], output_path: Path) -> None:
        """Export decisions to CSV format."""
        if not decisions:
            # Write empty CSV with headers
            output_path.write_text("decision_id,timestamp,category,decision,rationale,confidence,risk_score\n")
            return

        # Flatten decision data for CSV
        flat_data = []
        for d in decisions:
            # Calculate risk score
            risk_score = 0.5
            if d.get("impact_assessment"):
                impact = DecisionImpact.from_dict(d["impact_assessment"])
                risk_score = impact.calculate_risk_score()
            elif d.get("impact", {}).get("risk_level"):
                risk_weights = {
                    RiskLevel.LOW.value: 0.2,
                    RiskLevel.MEDIUM.value: 0.5,
                    RiskLevel.HIGH.value: 0.8,
                }
                risk_score = risk_weights.get(d["impact"]["risk_level"], 0.5)

            flat_data.append({
                "decision_id": d["decision_id"],
                "timestamp": d["timestamp"],
                "category": d["category"],
                "decision": d["decision"],
                "rationale": d["rationale"],
                "phase": d.get("phase", ""),
                "confidence": d.get("confidence", "medium"),
                "risk_score": round(risk_score, 2),
                "parent_id": d.get("lineage", {}).get("parent_decision_id", ""),
                "files_modified": len(d.get("impact_assessment", {}).get("files_modified", [])),
                "tests_affected": len(d.get("impact_assessment", {}).get("tests_affected", [])),
            })

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if flat_data:
                writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
                writer.writeheader()
                writer.writerows(flat_data)

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
            for hist_file in self.decisions_dir.glob("historical-*.json"):
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
            "version": "2.0",
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
            choice = decision.get("context", {}).get("choice", "unknown")
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
                Decision.from_dict(d) for d in decisions
            ]
            self._decision_log.summary = data.get("summary", {})
            self._decision_log.generated_at = data.get("generated_at", "")

            # Update counter
            if self._decision_log.decisions:
                max_id = max(
                    int(d.decision_id.split("-")[1])
                    for d in self._decision_log.decisions
                )
                self._decision_counter = max_id

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
            return [Decision.from_dict(d) for d in data.get("decisions", [])]
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
                "confidence": decision.confidence,
                "risk_score": round(decision.get_risk_score(), 2),
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
    parser.add_argument(
        "--export",
        help="Export decisions to file (format: json or csv)",
    )
    parser.add_argument(
        "--output",
        help="Output path for export",
    )
    parser.add_argument(
        "--trace",
        help="Trace decision lineage by ID",
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

    elif args.export:
        # Export decisions
        output_path = Path(args.output) if args.output else None
        exported_path = logger.export_decisions(format=args.export, output_path=output_path)
        print(f"Exported decisions to: {exported_path}")

    elif args.trace:
        # Trace decision lineage
        lineage = logger.trace_decision(args.trace)
        print(json.dumps(lineage, indent=2))

    else:
        # Interactive mode
        print(f"Decision Logger - Session: {logger.session_id}")
        print("Use --query, --learn, --aggregate, --summary, --export, or --trace")


if __name__ == "__main__":
    main()
