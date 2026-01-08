#!/usr/bin/env python3
"""
Decision Strategy Framework for Maestro Orchestrator

Implements the Strategy Pattern for autonomous decision-making.
Provides base classes and registry for pluggable decision strategies
across tech stack, task ordering, architecture, and approach decisions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class DecisionContext:
    """
    Context for autonomous decision-making.

    Captures all relevant information needed for a decision strategy
    to make an informed choice. Includes PRD requirements, current state,
    available options, and constraints.

    Attributes:
        prd_requirements: Requirements from the PRD document
        current_state: Current state of the codebase/project
        available_options: List of viable options to consider
        constraints: Technical, business, or resource constraints
        session_id: Unique identifier for the current session
        timestamp: When the context was created
        metadata: Additional context information
    """
    prd_requirements: Dict[str, Any]
    current_state: Dict[str, Any]
    available_options: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    session_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "prd_requirements": self.prd_requirements,
            "current_state": self.current_state,
            "available_options": self.available_options,
            "constraints": self.constraints,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def get_constraint(self, key: str, default: Any = None) -> Any:
        """Get a constraint value by key."""
        return self.constraints.get(key, default)

    def get_requirement(self, key: str, default: Any = None) -> Any:
        """Get a requirement value by key."""
        return self.prd_requirements.get(key, default)

    def has_option(self, option_name: str) -> bool:
        """Check if an option exists in available options."""
        return any(
            opt.get("name") == option_name or opt.get("id") == option_name
            for opt in self.available_options
        )


@dataclass
class Decision:
    """
    Represents an autonomous decision with full rationale.

    A decision includes the choice made, the rationale for that choice,
    confidence level, alternatives considered, and a snapshot of the
    context that informed the decision.

    Attributes:
        choice: The selected option/choice
        rationale: Explanation of why this choice was made
        confidence: Confidence level from 0.0 to 1.0
        alternatives: List of alternatives that were considered
        context_snapshot: Snapshot of context at decision time
        timestamp: When the decision was made
        decision_type: Type of decision (tech_stack, task_ordering, etc.)
        metadata: Additional decision metadata
    """
    choice: str
    rationale: str
    confidence: float
    alternatives: List[str]
    context_snapshot: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision_type: str = "generic"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate decision data after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not self.choice:
            raise ValueError("Choice cannot be empty")
        if not self.rationale:
            raise ValueError("Rationale cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for serialization."""
        return {
            "choice": self.choice,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "context_snapshot": self.context_snapshot,
            "timestamp": self.timestamp,
            "decision_type": self.decision_type,
            "metadata": self.metadata,
        }

    def get_confidence_level(self) -> str:
        """Get human-readable confidence level."""
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"

    def is_high_confidence(self) -> bool:
        """Check if decision is high confidence."""
        return self.confidence >= 0.8


class DecisionStrategy(ABC):
    """
    Base class for autonomous decision strategies.

    All decision strategies must inherit from this class and implement
    the decide() and get_strategy_name() methods. Strategies can also
    override validate_context() for custom validation logic.

    Strategies should be stateless and thread-safe, as they may be
    called concurrently from multiple sessions.
    """

    @abstractmethod
    def decide(self, context: DecisionContext) -> Decision:
        """
        Make an autonomous decision based on context.

        This is the main entry point for the strategy. It should analyze
        the context and return a well-reasoned decision with rationale.

        Args:
            context: The decision context containing requirements, state,
                    options, and constraints

        Returns:
            A Decision object with choice, rationale, and confidence

        Raises:
            ValueError: If context is invalid or missing required data
            RuntimeError: If decision cannot be made with available data
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Return the name of this strategy.

        The strategy name should be unique and descriptive, following
        the pattern: <category>_<strategy> (e.g., "tech_stack_existing_first")

        Returns:
            Unique strategy name
        """
        pass

    def get_strategy_description(self) -> str:
        """
        Return a description of this strategy.

        Should explain what the strategy does and when it's best used.

        Returns:
            Human-readable strategy description
        """
        return f"Decision strategy: {self.get_strategy_name()}"

    def get_supported_decision_types(self) -> List[str]:
        """
        Return list of decision types this strategy supports.

        For example: ["tech_stack", "architecture", "task_ordering"]

        Returns:
            List of supported decision type strings
        """
        return ["generic"]

    def validate_context(self, context: DecisionContext) -> bool:
        """
        Validate that context has required information for this strategy.

        Base implementation checks for non-empty context and PRD requirements.
        Subclasses can override for specific validation needs.

        Args:
            context: The context to validate

        Returns:
            True if context is valid, False otherwise

        Raises:
            ValueError: If context is missing critical data
        """
        if not context:
            return False

        if not context.prd_requirements:
            raise ValueError("PRD requirements are required for decision-making")

        if not context.available_options:
            raise ValueError("At least one available option is required")

        return True

    def score_option(self, option: Dict[str, Any], context: DecisionContext) -> float:
        """
        Score a single option based on context.

        Default implementation returns 0.5. Subclasses should override
        to provide actual scoring logic.

        Args:
            option: The option to score
            context: The decision context

        Returns:
            Score from 0.0 to 1.0
        """
        return 0.5

    def get_confidence(
        self,
        top_score: float,
        second_score: float,
        option_count: int
    ) -> float:
        """
        Calculate confidence based on score distribution.

        Higher confidence when:
        - Top score is significantly higher than second place
        - Top score is close to 1.0
        - Multiple options were considered (not just one)

        Args:
            top_score: Score of the top-ranked option
            second_score: Score of the second-ranked option
            option_count: Total number of options scored

        Returns:
            Confidence value from 0.0 to 1.0
        """
        # Base confidence on top score quality
        confidence = top_score * 0.6

        # Boost confidence if top choice is clear winner
        if option_count > 1:
            score_gap = top_score - second_score
            confidence += min(score_gap * 0.4, 0.4)

        # Consider option count (more options = more confident)
        if option_count >= 3:
            confidence *= 1.1
        elif option_count < 2:
            confidence *= 0.8

        return min(confidence, 1.0)


class DecisionRegistry:
    """
    Registry for managing decision strategies.

    Provides a centralized registry for decision strategies with support
    for dynamic registration, lookup, and strategy selection based on
    decision type and context.

    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize the registry with empty strategy storage."""
        self._strategies: Dict[str, DecisionStrategy] = {}
        self._by_type: Dict[str, List[str]] = defaultdict(list)

    def register(self, name: str, strategy: DecisionStrategy) -> None:
        """
        Register a decision strategy.

        Args:
            name: Unique name for the strategy
            strategy: Strategy instance to register

        Raises:
            ValueError: If strategy name already exists or is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Strategy name must be a non-empty string")

        if name in self._strategies:
            raise ValueError(f"Strategy '{name}' is already registered")

        if not isinstance(strategy, DecisionStrategy):
            raise ValueError("Strategy must be an instance of DecisionStrategy")

        self._strategies[name] = strategy

        # Index by decision type
        for decision_type in strategy.get_supported_decision_types():
            self._by_type[decision_type].append(name)

    def unregister(self, name: str) -> None:
        """
        Unregister a decision strategy.

        Args:
            name: Name of the strategy to unregister

        Raises:
            KeyError: If strategy name not found
        """
        if name not in self._strategies:
            raise KeyError(f"Strategy '{name}' not found")

        strategy = self._strategies[name]

        # Remove from type index
        for decision_type in strategy.get_supported_decision_types():
            if name in self._by_type[decision_type]:
                self._by_type[decision_type].remove(name)

        del self._strategies[name]

    def get_strategy(self, name: str) -> Optional[DecisionStrategy]:
        """
        Get a strategy by name.

        Args:
            name: Name of the strategy to retrieve

        Returns:
            Strategy instance or None if not found
        """
        return self._strategies.get(name)

    def get_strategies_by_type(self, decision_type: str) -> List[DecisionStrategy]:
        """
        Get all strategies that support a decision type.

        Args:
            decision_type: The decision type to filter by

        Returns:
            List of strategies supporting the type
        """
        strategy_names = self._by_type.get(decision_type, [])
        return [
            self._strategies[name]
            for name in strategy_names
            if name in self._strategies
        ]

    def list_strategies(self) -> List[str]:
        """
        List all registered strategy names.

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())

    def list_decision_types(self) -> List[str]:
        """
        List all decision types with registered strategies.

        Returns:
            List of decision type strings
        """
        return list(self._by_type.keys())

    def describe_strategy(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a strategy.

        Args:
            name: Strategy name

        Returns:
            Dictionary with strategy details or None if not found
        """
        strategy = self.get_strategy(name)
        if not strategy:
            return None

        return {
            "name": name,
            "description": strategy.get_strategy_description(),
            "supported_types": strategy.get_supported_decision_types(),
        }

    def select_strategy(
        self,
        decision_type: str,
        context: Optional[DecisionContext] = None,
        preference: Optional[str] = None
    ) -> Optional[DecisionStrategy]:
        """
        Select the best strategy for a decision type and context.

        Args:
            decision_type: The type of decision to make
            context: Optional context to inform selection
            preference: Optional preferred strategy name

        Returns:
            Selected strategy or None if no suitable strategy found
        """
        # If preference specified, try that first
        if preference:
            strategy = self.get_strategy(preference)
            if strategy and decision_type in strategy.get_supported_decision_types():
                return strategy

        # Get all strategies for this decision type
        candidates = self.get_strategies_by_type(decision_type)

        if not candidates:
            return None

        # For now, return the first candidate
        # Future: could implement more sophisticated selection based on context
        return candidates[0]

    def describe_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get descriptions of all registered strategies.

        Returns:
            Dictionary mapping strategy names to their descriptions
        """
        return {
            name: self.describe_strategy(name)
            for name in self.list_strategies()
        }

    def export_registry(self) -> Dict[str, Any]:
        """
        Export registry state for debugging/inspection.

        Returns:
            Dictionary with registry information
        """
        return {
            "total_strategies": len(self._strategies),
            "strategies": self.list_strategies(),
            "decision_types": self.list_decision_types(),
            "strategies_by_type": {
                dt: self._by_type[dt]
                for dt in self.list_decision_types()
            },
        }


# Global registry instance
_global_registry: Optional[DecisionRegistry] = None


def get_global_registry() -> DecisionRegistry:
    """
    Get the global decision strategy registry.

    Creates the registry on first call.

    Returns:
        Global registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = DecisionRegistry()
    return _global_registry


def register_strategy(name: str, strategy: DecisionStrategy) -> None:
    """
    Register a strategy in the global registry.

    Convenience function for get_global_registry().register()

    Args:
        name: Strategy name
        strategy: Strategy instance
    """
    get_global_registry().register(name, strategy)


def get_strategy(name: str) -> Optional[DecisionStrategy]:
    """
    Get a strategy from the global registry.

    Convenience function for get_global_registry().get_strategy()

    Args:
        name: Strategy name

    Returns:
        Strategy instance or None
    """
    return get_global_registry().get_strategy(name)


def list_strategies() -> List[str]:
    """
    List all strategies in the global registry.

    Convenience function for get_global_registry().list_strategies()

    Returns:
        List of strategy names
    """
    return get_global_registry().list_strategies()
