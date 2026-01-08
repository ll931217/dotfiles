#!/usr/bin/env python3
"""
Approach Strategy for Implementation Alternatives

Implements DecisionStrategy for selecting between alternative implementation
approaches based on complexity, performance, maintainability, and testability.
Used during auto-recovery when initial approach fails.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from decision_strategy import DecisionStrategy, DecisionContext, Decision


@dataclass
class ImplementationAlternative:
    """
    Represents an alternative implementation approach.

    Attributes:
        name: Unique identifier for this approach
        description: Human-readable description of the approach
        complexity: Implementation complexity (LOW, MEDIUM, HIGH)
        performance: Expected performance (FAST, MODERATE, SLOW)
        maintainability: Code maintainability (HIGH, MEDIUM, LOW)
        testability: Ease of testing (HIGH, MEDIUM, LOW)
        lines_of_code: Estimated lines of code (optional)
        cognitive_load: Cognitive complexity (1-10 scale, optional)
    """
    name: str
    description: str
    complexity: str  # LOW, MEDIUM, HIGH
    performance: str  # FAST, MODERATE, SLOW
    maintainability: str  # HIGH, MEDIUM, LOW
    testability: str  # HIGH, MEDIUM, LOW
    lines_of_code: Optional[int] = None
    cognitive_load: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alternative to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "complexity": self.complexity,
            "performance": self.performance,
            "maintainability": self.maintainability,
            "testability": self.testability,
            "lines_of_code": self.lines_of_code,
            "cognitive_load": self.cognitive_load,
        }


class ApproachStrategy(DecisionStrategy):
    """
    Strategy for selecting between alternative implementation approaches.

    Evaluates alternatives based on:
    - Code complexity (lines of code, cognitive load)
    - Performance characteristics (execution speed, resource usage)
    - Maintainability (code clarity, modularity)
    - Testing feasibility (test coverage, mocking requirements)

    Applies default decision hierarchy:
    1. Best practices (industry standards, patterns)
    2. Existing patterns (consistency with codebase)
    3. Simplicity (prefer simpler solutions)
    4. Consistency (maintain architectural consistency)
    """

    def decide(self, context: DecisionContext) -> Decision:
        """
        Select the best implementation approach from alternatives.

        Args:
            context: Decision context containing:
                - available_options: List of ImplementationAlternative dicts
                - prd_requirements: Implementation requirements
                - current_state: Current codebase state
                - constraints: Technical and resource constraints

        Returns:
            Decision with selected approach and detailed rationale

        Raises:
            ValueError: If no alternatives provided or context invalid
        """
        # Validate context
        self.validate_context(context)

        # Parse alternatives from context
        alternatives = self._parse_alternatives(context)

        if not alternatives:
            raise ValueError("No implementation alternatives found in context")

        # Score each alternative
        scored_alternatives = []
        for alternative in alternatives:
            score = self._score_alternative(alternative, context)
            scored_alternatives.append((score, alternative))

        # Sort by score (highest first)
        scored_alternatives.sort(key=lambda x: x[0], reverse=True)

        # Extract top choice
        top_score, top_alternative = scored_alternatives[0]
        second_score = scored_alternatives[1][0] if len(scored_alternatives) > 1 else 0.0

        # Calculate confidence
        confidence = self.get_confidence(
            top_score,
            second_score,
            len(scored_alternatives)
        )

        # Build rationale
        rationale = self._build_rationale(
            top_alternative,
            top_score,
            scored_alternatives[1:],
            context
        )

        # Extract alternatives list
        alternative_names = [
            alt.name for _, alt in scored_alternatives[1:]
        ]

        return Decision(
            choice=top_alternative.name,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternative_names,
            context_snapshot=context.to_dict(),
            decision_type="approach_selection",
            metadata={
                "selected_alternative": top_alternative.to_dict(),
                "score": top_score,
                "all_scores": [
                    {"name": alt.name, "score": score}
                    for score, alt in scored_alternatives
                ]
            }
        )

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "approach_hierarchy"

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return (
            "Selects implementation approaches using decision hierarchy: "
            "best practices → existing → simplicity → consistency"
        )

    def get_supported_decision_types(self) -> List[str]:
        """Return supported decision types."""
        return ["approach_selection", "implementation_alternative", "auto_recovery"]

    def validate_context(self, context: DecisionContext) -> bool:
        """
        Validate context has required information.

        Args:
            context: Context to validate

        Returns:
            True if valid

        Raises:
            ValueError: If context missing required data
        """
        if not context:
            raise ValueError("Context cannot be None")

        if not context.available_options:
            raise ValueError("Context must contain available_options with alternatives")

        return True

    def _parse_alternatives(
        self,
        context: DecisionContext
    ) -> List[ImplementationAlternative]:
        """
        Parse implementation alternatives from context.

        Args:
            context: Decision context

        Returns:
            List of ImplementationAlternative objects
        """
        alternatives = []

        for option in context.available_options:
            # Handle both dict and already-parsed alternatives
            if isinstance(option, ImplementationAlternative):
                alternatives.append(option)
            elif isinstance(option, dict):
                alt = ImplementationAlternative(
                    name=option.get("name", "unknown"),
                    description=option.get("description", ""),
                    complexity=option.get("complexity", "MEDIUM"),
                    performance=option.get("performance", "MODERATE"),
                    maintainability=option.get("maintainability", "MEDIUM"),
                    testability=option.get("testability", "MEDIUM"),
                    lines_of_code=option.get("lines_of_code"),
                    cognitive_load=option.get("cognitive_load"),
                )
                alternatives.append(alt)

        return alternatives

    def _score_alternative(
        self,
        alternative: ImplementationAlternative,
        context: DecisionContext
    ) -> float:
        """
        Score an alternative based on multiple criteria.

        Scoring criteria (total 1.0):
        - Complexity (30%): Lower complexity = higher score
        - Performance (25%): Better performance = higher score
        - Maintainability (25%): Higher maintainability = higher score
        - Testability (20%): Higher testability = higher score

        Args:
            alternative: Alternative to score
            context: Decision context for additional scoring factors

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0

        # Complexity score (30%)
        score += self._score_complexity(alternative) * 0.30

        # Performance score (25%)
        score += self._score_performance(alternative) * 0.25

        # Maintainability score (25%)
        score += self._score_maintainability(alternative) * 0.25

        # Testability score (20%)
        score += self._score_testability(alternative) * 0.20

        # Apply decision hierarchy bonuses
        score = self._apply_hierarchy_bonuses(alternative, context, score)

        return min(score, 1.0)

    def _score_complexity(self, alternative: ImplementationAlternative) -> float:
        """
        Score based on implementation complexity.

        Lower complexity = higher score
        - LOW complexity: 1.0
        - MEDIUM complexity: 0.6
        - HIGH complexity: 0.3

        Args:
            alternative: Alternative to score

        Returns:
            Complexity score from 0.0 to 1.0
        """
        complexity_scores = {
            "LOW": 1.0,
            "MEDIUM": 0.6,
            "HIGH": 0.3,
        }
        return complexity_scores.get(alternative.complexity.upper(), 0.5)

    def _score_performance(self, alternative: ImplementationAlternative) -> float:
        """
        Score based on performance characteristics.

        Better performance = higher score
        - FAST: 1.0
        - MODERATE: 0.7
        - SLOW: 0.4

        Args:
            alternative: Alternative to score

        Returns:
            Performance score from 0.0 to 1.0
        """
        performance_scores = {
            "FAST": 1.0,
            "MODERATE": 0.7,
            "SLOW": 0.4,
        }
        return performance_scores.get(alternative.performance.upper(), 0.6)

    def _score_maintainability(self, alternative: ImplementationAlternative) -> float:
        """
        Score based on code maintainability.

        Higher maintainability = higher score
        - HIGH: 1.0
        - MEDIUM: 0.6
        - LOW: 0.3

        Args:
            alternative: Alternative to score

        Returns:
            Maintainability score from 0.0 to 1.0
        """
        maintainability_scores = {
            "HIGH": 1.0,
            "MEDIUM": 0.6,
            "LOW": 0.3,
        }
        return maintainability_scores.get(alternative.maintainability.upper(), 0.5)

    def _score_testability(self, alternative: ImplementationAlternative) -> float:
        """
        Score based on testing feasibility.

        Higher testability = higher score
        - HIGH: 1.0
        - MEDIUM: 0.6
        - LOW: 0.3

        Args:
            alternative: Alternative to score

        Returns:
            Testability score from 0.0 to 1.0
        """
        testability_scores = {
            "HIGH": 1.0,
            "MEDIUM": 0.6,
            "LOW": 0.3,
        }
        return testability_scores.get(alternative.testability.upper(), 0.5)

    def _apply_hierarchy_bonuses(
        self,
        alternative: ImplementationAlternative,
        context: DecisionContext,
        base_score: float
    ) -> float:
        """
        Apply decision hierarchy bonuses to base score.

        Hierarchy:
        1. Best practices: +15% if follows industry standards
        2. Existing patterns: +10% if consistent with codebase
        3. Simplicity: +10% if LOW complexity
        4. Consistency: +5% if matches architecture

        Args:
            alternative: Alternative being scored
            context: Decision context
            base_score: Current base score

        Returns:
            Adjusted score
        """
        score = base_score

        # Best practices bonus
        if self._check_best_practices(alternative, context):
            score += 0.15

        # Existing patterns bonus
        if self._check_existing_patterns(alternative, context):
            score += 0.10

        # Simplicity bonus
        if alternative.complexity == "LOW":
            score += 0.10

        # Consistency bonus
        if self._check_architecture_consistency(alternative, context):
            score += 0.05

        return score

    def _check_best_practices(
        self,
        alternative: ImplementationAlternative,
        context: DecisionContext
    ) -> bool:
        """
        Check if alternative follows industry best practices.

        Args:
            alternative: Alternative to check
            context: Decision context

        Returns:
            True if follows best practices
        """
        # Check if alternative is marked as best practice
        requirements = context.prd_requirements

        # Look for best practice markers
        if requirements.get("prefer_best_practices"):
            return (
                alternative.maintainability == "HIGH" and
                alternative.testability == "HIGH"
            )

        # Check for specific best practice indicators
        description_lower = alternative.description.lower()
        best_practice_keywords = [
            "standard", "best practice", "recommended",
            "idiomatic", "clean code", "solid"
        ]

        return any(keyword in description_lower for keyword in best_practice_keywords)

    def _check_existing_patterns(
        self,
        alternative: ImplementationAlternative,
        context: DecisionContext
    ) -> bool:
        """
        Check if alternative matches existing codebase patterns.

        Args:
            alternative: Alternative to check
            context: Decision context

        Returns:
            True if matches existing patterns
        """
        current_state = context.current_state
        existing_patterns = current_state.get("existing_patterns", [])

        if not existing_patterns:
            return False

        # Check if alternative name or description matches existing patterns
        alt_text = f"{alternative.name} {alternative.description}".lower()

        return any(
            pattern.lower() in alt_text
            for pattern in existing_patterns
        )

    def _check_architecture_consistency(
        self,
        alternative: ImplementationAlternative,
        context: DecisionContext
    ) -> bool:
        """
        Check if alternative is consistent with project architecture.

        Args:
            alternative: Alternative to check
            context: Decision context

        Returns:
            True if architecturally consistent
        """
        current_state = context.current_state
        architecture = current_state.get("architecture", {})

        if not architecture:
            return False

        # Check for architectural alignment
        alt_text = alternative.description.lower()

        # Check if alternative mentions architectural consistency
        consistency_keywords = [
            "consistent", "architecture", "pattern",
            "modular", "layered", "separation"
        ]

        return any(keyword in alt_text for keyword in consistency_keywords)

    def _build_rationale(
        self,
        selected: ImplementationAlternative,
        score: float,
        rejected: List[tuple],
        context: DecisionContext
    ) -> str:
        """
        Build human-readable rationale for decision.

        Args:
            selected: Selected alternative
            score: Score of selected alternative
            rejected: List of (score, alternative) for rejected options
            context: Decision context

        Returns:
            Rationale string explaining the choice
        """
        reasons = []

        # Add complexity rationale
        if selected.complexity == "LOW":
            reasons.append("Low implementation complexity")
        elif selected.complexity == "MEDIUM":
            reasons.append("Manageable complexity")

        # Add performance rationale
        if selected.performance == "FAST":
            reasons.append("Excellent performance characteristics")
        elif selected.performance == "MODERATE":
            reasons.append("Acceptable performance")

        # Add maintainability rationale
        if selected.maintainability == "HIGH":
            reasons.append("High maintainability")

        # Add testability rationale
        if selected.testability == "HIGH":
            reasons.append("Excellent testability")

        # Add hierarchy bonuses
        if self._check_best_practices(selected, context):
            reasons.append("Follows industry best practices")

        if self._check_existing_patterns(selected, context):
            reasons.append("Consistent with existing codebase patterns")

        if self._check_architecture_consistency(selected, context):
            reasons.append("Maintains architectural consistency")

        # Build main rationale
        main_rationale = f"{selected.name}: {selected.description}"

        # Add scoring rationale
        if reasons:
            scoring_rationale = "Selected due to: " + ", ".join(reasons)
            main_rationale += f". {scoring_rationale}"

        # Add score information
        main_rationale += f" (Score: {score:.2f})"

        return main_rationale


# Helper function to create alternatives from common patterns
def create_simple_alternative(
    name: str,
    description: str,
    complexity: str = "MEDIUM",
    performance: str = "MODERATE",
    maintainability: str = "MEDIUM",
    testability: str = "MEDIUM"
) -> ImplementationAlternative:
    """
    Create a simple implementation alternative.

    Args:
        name: Alternative name
        description: Description of the approach
        complexity: Complexity level (LOW, MEDIUM, HIGH)
        performance: Performance level (FAST, MODERATE, SLOW)
        maintainability: Maintainability level (HIGH, MEDIUM, LOW)
        testability: Testability level (HIGH, MEDIUM, LOW)

    Returns:
        ImplementationAlternative object
    """
    return ImplementationAlternative(
        name=name,
        description=description,
        complexity=complexity,
        performance=performance,
        maintainability=maintainability,
        testability=testability
    )


# Auto-recovery helper
def select_fallback_approach(
    failed_approach: str,
    context: DecisionContext
) -> Optional[str]:
    """
    Select a fallback approach when initial implementation fails.

    Common use case during auto-recovery when first approach fails.

    Args:
        failed_approach: Name of the approach that failed
        context: Decision context with available alternatives

    Returns:
        Name of fallback approach or None if no suitable alternative
    """
    strategy = ApproachStrategy()

    try:
        decision = strategy.decide(context)

        # Don't recommend the same approach that failed
        if decision.choice == failed_approach and decision.alternatives:
            return decision.alternatives[0]

        return decision.choice if decision.choice != failed_approach else None
    except Exception:
        return None
