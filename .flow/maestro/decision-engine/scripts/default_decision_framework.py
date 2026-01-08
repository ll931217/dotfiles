#!/usr/bin/env python3
"""
Default Decision Framework for Autonomous Decision-Making

Implements the default decision hierarchy for ambiguous decisions when
specialized strategies cannot determine a clear winner. Provides a
systematic approach to evaluating options based on:
1. Best practices: Industry standards and established patterns
2. Existing patterns: Follow what's already in the codebase
3. Simplicity: Choose the simplest viable option
4. Consistency: Match existing code style and architecture
"""

import re
import os
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from decision_strategy import DecisionStrategy, DecisionContext, Decision


@dataclass
class BestPracticeScore:
    """
    Score for an option based on industry best practices.

    Attributes:
        option_name: Name of the option being scored
        practice_score: Score based on best practices (0.0-1.0)
        practice_rank: Rank in best practices (1=best)
        reasons: List of reasons for the score
    """
    option_name: str
    practice_score: float
    practice_rank: int
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "option_name": self.option_name,
            "practice_score": self.practice_score,
            "practice_rank": self.practice_rank,
            "reasons": self.reasons,
        }


@dataclass
class PatternMatchScore:
    """
    Score for an option based on existing codebase patterns.

    Attributes:
        option_name: Name of the option being scored
        pattern_score: Score based on pattern matching (0.0-1.0)
        match_count: Number of pattern matches found
        file_examples: List of files with matching patterns
    """
    option_name: str
    pattern_score: float
    match_count: int
    file_examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "option_name": self.option_name,
            "pattern_score": self.pattern_score,
            "match_count": self.match_count,
            "file_examples": self.file_examples,
        }


@dataclass
class SimplicityScore:
    """
    Score for an option based on simplicity.

    Attributes:
        option_name: Name of the option being scored
        simplicity_score: Score based on simplicity (0.0-1.0)
        lines_of_code: Estimated lines of code
        complexity_metrics: Dictionary of complexity metrics
    """
    option_name: str
    simplicity_score: float
    lines_of_code: Optional[int]
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "option_name": self.option_name,
            "simplicity_score": self.simplicity_score,
            "lines_of_code": self.lines_of_code,
            "complexity_metrics": self.complexity_metrics,
        }


@dataclass
class ConsistencyScore:
    """
    Score for an option based on consistency with existing code.

    Attributes:
        option_name: Name of the option being scored
        consistency_score: Score based on consistency (0.0-1.0)
        style_matches: List of style aspects that match
        inconsistencies: List of inconsistencies found
    """
    option_name: str
    consistency_score: float
    style_matches: List[str] = field(default_factory=list)
    inconsistencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "option_name": self.option_name,
            "consistency_score": self.consistency_score,
            "style_matches": self.style_matches,
            "inconsistencies": self.inconsistencies,
        }


class DefaultDecisionFramework(DecisionStrategy):
    """
    Implements the default decision hierarchy for ambiguous decisions.

    When specialized strategies (TechStackStrategy, TaskOrderingStrategy, etc.)
    cannot determine a clear winner, this framework applies a systematic
    evaluation based on:

    Hierarchy (in order of priority):
    1. Best practices: Industry standards, established patterns
    2. Existing patterns: Follow what's already in the codebase
    3. Simplicity: Choose the simplest viable option
    4. Consistency: Match existing code style and architecture

    Each option is scored across all four dimensions, then weighted
    according to the hierarchy. The option with the highest overall
    score is selected.

    Example:
        context = DecisionContext(
            prd_requirements={"feature": "user authentication"},
            current_state={"project_root": "/path/to/project"},
            available_options=[
                {"name": "Passport.js", "category": "authentication"},
                {"name": "Auth0", "category": "authentication"},
            ],
            constraints={},
            session_id="session-123"
        )

        framework = DefaultDecisionFramework()
        decision = framework.decide(context)
        # decision.choice == "Passport.js"
        # decision.rationale explains why based on the hierarchy
    """

    # Weights for each decision dimension (must sum to 1.0)
    WEIGHT_BEST_PRACTICES = 0.35
    WEIGHT_EXISTING_PATTERNS = 0.30
    WEIGHT_SIMPLICITY = 0.20
    WEIGHT_CONSISTENCY = 0.15

    # Best practices knowledge base (simplified subset)
    BEST_PRACTICES = {
        'authentication': {
            'Passport.js': {'rank': 1, 'reasons': ['Industry standard for Node.js', 'Extensive provider support', 'Battle-tested']},
            'Auth.js': {'rank': 2, 'reasons': ['Modern Next.js auth', 'TypeScript-first', 'Growing community']},
            'Auth0': {'rank': 3, 'reasons': ['Managed service', 'Enterprise features', 'Higher complexity']},
            'custom JWT': {'rank': 4, 'reasons': ['Maintenance burden', 'Security risks', 'Reinventing the wheel']},
        },
        'database': {
            'PostgreSQL': {'rank': 1, 'reasons': ['ACID compliance', 'Extensive feature set', 'Open source']},
            'MySQL': {'rank': 2, 'reasons': ['Widely used', 'Good performance', 'Mature ecosystem']},
            'MongoDB': {'rank': 3, 'reasons': ['Flexible schema', 'Good for prototyping', 'Different paradigm']},
            'SQLite': {'rank': 4, 'reasons': ['Embedded database', 'Limited for production', 'Single-file constraints']},
        },
        'testing': {
            'pytest': {'rank': 1, 'reasons': ['Python standard', 'Powerful fixtures', 'Plugin ecosystem']},
            'unittest': {'rank': 2, 'reasons': ['Built-in', 'Limited features', 'Boilerplate heavy']},
            'nose2': {'rank': 3, 'reasons': ['Less popular', 'Smaller community', 'Limited plugins']},
        },
        'api_framework': {
            'FastAPI': {'rank': 1, 'reasons': ['Modern async', 'Automatic docs', 'Type hints']},
            'Flask': {'rank': 2, 'reasons': ['Mature', 'Flexible', 'Manual sync']},
            'Django REST': {'rank': 3, 'reasons': ['Batteries included', 'Heavier weight', 'Monolithic']},
        },
    }

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "default_decision_framework"

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return (
            "Default decision framework applying hierarchy: "
            "best practices > existing patterns > simplicity > consistency"
        )

    def get_supported_decision_types(self) -> List[str]:
        """Return supported decision types."""
        return [
            "tech_stack",
            "task_ordering",
            "approach",
            "architecture",
            "generic",
        ]

    def decide(self, context: DecisionContext) -> Decision:
        """
        Apply default decision hierarchy to select best option.

        Args:
            context: Decision context containing options and requirements

        Returns:
            Decision with selected option and detailed rationale

        Raises:
            ValueError: If context is invalid or no options available
            RuntimeError: If decision cannot be made
        """
        # Validate context
        self.validate_context(context)

        # Extract options from context
        options = context.available_options
        if not options:
            raise ValueError("No available options in context")

        # Score each option across all dimensions
        scored_options = []
        for option in options:
            option_name = option.get("name") or option.get("id", str(option))

            # Get scores for each dimension
            practice_score = self._evaluate_best_practices(option, context)
            pattern_score = self._evaluate_existing_patterns(option, context)
            simplicity_score = self._evaluate_simplicity(option, context)
            consistency_score = self._evaluate_consistency(option, context)

            # Calculate weighted total score
            total_score = (
                practice_score.practice_score * self.WEIGHT_BEST_PRACTICES +
                pattern_score.pattern_score * self.WEIGHT_EXISTING_PATTERNS +
                simplicity_score.simplicity_score * self.WEIGHT_SIMPLICITY +
                consistency_score.consistency_score * self.WEIGHT_CONSISTENCY
            )

            scored_options.append({
                "name": option_name,
                "total_score": total_score,
                "practice": practice_score,
                "pattern": pattern_score,
                "simplicity": simplicity_score,
                "consistency": consistency_score,
            })

        # Sort by total score (descending)
        scored_options.sort(key=lambda x: x["total_score"], reverse=True)

        # Get top choice and runner-up
        top_choice = scored_options[0]
        second_score = scored_options[1]["total_score"] if len(scored_options) > 1 else 0.0

        # Calculate confidence
        confidence = self.get_confidence(
            top_choice["total_score"],
            second_score,
            len(scored_options)
        )

        # Build rationale
        rationale = self._build_rationale(top_choice, scored_options)

        # Get list of alternatives
        alternatives = [opt["name"] for opt in scored_options[1:]]

        # Create and return decision
        return Decision(
            choice=top_choice["name"],
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
            context_snapshot=context.to_dict(),
            decision_type=self._get_decision_type(context),
            metadata={
                "scores": {
                    opt["name"]: {
                        "total": opt["total_score"],
                        "best_practices": opt["practice"].practice_score,
                        "existing_patterns": opt["pattern"].pattern_score,
                        "simplicity": opt["simplicity"].simplicity_score,
                        "consistency": opt["consistency"].consistency_score,
                    }
                    for opt in scored_options
                },
                "framework": "default_decision_hierarchy",
            }
        )

    def _evaluate_best_practices(
        self,
        option: Dict[str, Any],
        context: DecisionContext
    ) -> BestPracticeScore:
        """
        Evaluate option against industry best practices.

        Args:
            option: Option to evaluate
            context: Decision context

        Returns:
            BestPracticeScore with practice evaluation
        """
        option_name = option.get("name") or option.get("id", str(option))
        category = option.get("category", "")

        # Look up in best practices knowledge base
        practice_info = None

        # Try direct category match
        if category in self.BEST_PRACTICES:
            category_practices = self.BEST_PRACTICES[category]
            if option_name in category_practices:
                practice_info = category_practices[option_name]

        # If not found, try to infer category from context
        if not practice_info:
            for cat, practices in self.BEST_PRACTICES.items():
                if option_name in practices:
                    practice_info = practices[option_name]
                    break

        if practice_info:
            rank = practice_info['rank']
            # Convert rank to score (1 -> 1.0, higher ranks -> lower scores)
            score = max(0.0, 1.0 - (rank - 1) * 0.2)
            return BestPracticeScore(
                option_name=option_name,
                practice_score=score,
                practice_rank=rank,
                reasons=practice_info['reasons']
            )

        # No specific best practice info, give neutral score
        return BestPracticeScore(
            option_name=option_name,
            practice_score=0.5,
            practice_rank=999,
            reasons=["No specific best practice information available"]
        )

    def _evaluate_existing_patterns(
        self,
        option: Dict[str, Any],
        context: DecisionContext
    ) -> PatternMatchScore:
        """
        Evaluate option based on existing codebase patterns.

        Searches for patterns in the codebase that match this option
        to determine if it's already being used.

        Args:
            option: Option to evaluate
            context: Decision context

        Returns:
            PatternMatchScore with pattern evaluation
        """
        option_name = option.get("name") or option.get("id", str(option))
        project_root = context.current_state.get("project_root", os.getcwd())

        # Detect patterns for this option
        detect_patterns = option.get("detect_patterns", [])
        if not detect_patterns:
            # Generate common patterns from option name
            detect_patterns = self._generate_detect_patterns(option_name)

        # Search for patterns in codebase
        matches = []
        file_examples = []

        if os.path.exists(project_root):
            for pattern in detect_patterns:
                # Use grep to search for pattern
                try:
                    result = subprocess.run(
                        ["grep", "-r", "-l", pattern, project_root],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        matched_files = result.stdout.strip().split('\n')
                        matches.extend([pattern] * len(matched_files))
                        file_examples.extend(matched_files[:3])  # Keep first 3 examples
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

        # Calculate score based on match count
        match_count = len(matches)
        if match_count > 10:
            score = 1.0
        elif match_count > 5:
            score = 0.8
        elif match_count > 2:
            score = 0.6
        elif match_count > 0:
            score = 0.4
        else:
            score = 0.0

        return PatternMatchScore(
            option_name=option_name,
            pattern_score=score,
            match_count=match_count,
            file_examples=list(set(file_examples))  # Remove duplicates
        )

    def _evaluate_simplicity(
        self,
        option: Dict[str, Any],
        context: DecisionContext
    ) -> SimplicityScore:
        """
        Evaluate option based on simplicity.

        Simpler options are preferred. Factors include:
        - Lines of code (if provided)
        - Complexity metrics (if provided)
        - Inferred complexity from option characteristics

        Args:
            option: Option to evaluate
            context: Decision context

        Returns:
            SimplicityScore with simplicity evaluation
        """
        option_name = option.get("name") or option.get("id", str(option))

        # Get explicit metrics if available
        lines_of_code = option.get("lines_of_code")
        cognitive_load = option.get("cognitive_load")
        complexity = option.get("complexity", "MEDIUM").upper()

        # Calculate simplicity score
        score = 0.5  # Default neutral score

        # Consider lines of code
        if lines_of_code is not None:
            if lines_of_code < 100:
                score = 1.0
            elif lines_of_code < 500:
                score = 0.8
            elif lines_of_code < 1000:
                score = 0.6
            else:
                score = 0.4

        # Consider cognitive load
        if cognitive_load is not None:
            if cognitive_load <= 3:
                load_score = 1.0
            elif cognitive_load <= 5:
                load_score = 0.7
            elif cognitive_load <= 7:
                load_score = 0.4
            else:
                load_score = 0.2
            # Average with existing score
            score = (score + load_score) / 2

        # Consider complexity level
        complexity_scores = {"LOW": 1.0, "MEDIUM": 0.6, "HIGH": 0.3}
        if complexity in complexity_scores:
            complexity_score = complexity_scores[complexity]
            score = (score + complexity_score) / 2

        # Build complexity metrics dict
        metrics = {
            "complexity": complexity,
        }
        if lines_of_code is not None:
            metrics["lines_of_code"] = lines_of_code
        if cognitive_load is not None:
            metrics["cognitive_load"] = cognitive_load

        return SimplicityScore(
            option_name=option_name,
            simplicity_score=score,
            lines_of_code=lines_of_code,
            complexity_metrics=metrics
        )

    def _evaluate_consistency(
        self,
        option: Dict[str, Any],
        context: DecisionContext
    ) -> ConsistencyScore:
        """
        Evaluate option based on consistency with existing code.

        Checks if the option matches existing code style, architecture,
        and conventions.

        Args:
            option: Option to evaluate
            context: Decision context

        Returns:
            ConsistencyScore with consistency evaluation
        """
        option_name = option.get("name") or option.get("id", str(option))
        project_root = context.current_state.get("project_root", os.getcwd())

        style_matches = []
        inconsistencies = []

        # Check language consistency
        option_language = option.get("language", "")
        if option_language:
            project_language = context.current_state.get("primary_language", "")
            if project_language:
                if option_language.lower() == project_language.lower():
                    style_matches.append(f"Matches project language: {project_language}")
                else:
                    inconsistencies.append(f"Language mismatch: {option_language} vs {project_language}")

        # Check framework consistency
        option_framework = option.get("framework", "")
        if option_framework:
            existing_frameworks = context.current_state.get("frameworks", [])
            if option_framework in existing_frameworks:
                style_matches.append(f"Uses existing framework: {option_framework}")
            elif existing_frameworks:
                inconsistencies.append(f"New framework: {option_framework} (existing: {', '.join(existing_frameworks)})")

        # Check ecosystem consistency
        option_ecosystem = option.get("ecosystem", "")
        if option_ecosystem:
            project_ecosystem = context.current_state.get("ecosystem", "")
            if project_ecosystem:
                if option_ecosystem.lower() == project_ecosystem.lower():
                    style_matches.append(f"Matches ecosystem: {project_ecosystem}")
                else:
                    inconsistencies.append(f"Ecosystem mismatch: {option_ecosystem} vs {project_ecosystem}")

        # Calculate score based on matches vs inconsistencies
        total_factors = len(style_matches) + len(inconsistencies)
        if total_factors == 0:
            score = 0.5  # Neutral if no information
        else:
            score = len(style_matches) / total_factors if total_factors > 0 else 0.5

        return ConsistencyScore(
            option_name=option_name,
            consistency_score=score,
            style_matches=style_matches,
            inconsistencies=inconsistencies
        )

    def _generate_detect_patterns(self, option_name: str) -> List[str]:
        """
        Generate search patterns for detecting option usage in codebase.

        Args:
            option_name: Name of the option

        Returns:
            List of search patterns
        """
        patterns = []

        # Add exact name
        patterns.append(option_name)

        # Add name with common variations
        name_lower = option_name.lower().replace('.', '-').replace('_', '-')
        patterns.append(name_lower)

        # Add package name variations
        if '.' not in option_name:
            patterns.append(f'@{option_name}/')
            patterns.append(f'{option_name}-')

        return patterns

    def _build_rationale(
        self,
        top_choice: Dict[str, Any],
        all_scores: List[Dict[str, Any]]
    ) -> str:
        """
        Build detailed rationale for the decision.

        Args:
            top_choice: The top-scoring option with all scores
            all_scores: All scored options for comparison

        Returns:
            Detailed rationale string
        """
        name = top_choice["name"]
        total_score = top_choice["total_score"]

        rationale_parts = [
            f"Selected '{name}' based on default decision hierarchy.",
            "",
            "## Score Breakdown:",
        ]

        # Add individual dimension scores
        practice = top_choice["practice"]
        rationale_parts.append(
            f"- **Best Practices**: {practice.practice_score:.2f} "
            f"(rank {practice.practice_rank})"
        )
        if practice.reasons:
            rationale_parts.append(f"  - Reasons: {', '.join(practice.reasons[:2])}")

        pattern = top_choice["pattern"]
        rationale_parts.append(
            f"- **Existing Patterns**: {pattern.pattern_score:.2f} "
            f"({pattern.match_count} matches)"
        )

        simplicity = top_choice["simplicity"]
        rationale_parts.append(
            f"- **Simplicity**: {simplicity.simplicity_score:.2f}"
        )
        if simplicity.lines_of_code:
            rationale_parts.append(f"  - Estimated LOC: {simplicity.lines_of_code}")

        consistency = top_choice["consistency"]
        rationale_parts.append(
            f"- **Consistency**: {consistency.consistency_score:.2f}"
        )
        if consistency.style_matches:
            rationale_parts.append(f"  - Matches: {', '.join(consistency.style_matches)}")
        if consistency.inconsistencies:
            rationale_parts.append(f"  - Concerns: {', '.join(consistency.inconsistencies)}")

        rationale_parts.append("")
        rationale_parts.append(f"**Total Weighted Score**: {total_score:.2f}")

        # Add comparison to alternatives
        if len(all_scores) > 1:
            rationale_parts.append("")
            rationale_parts.append("## Comparison to Alternatives:")
            for opt in all_scores[1:3]:  # Show top 2 alternatives
                rationale_parts.append(
                    f"- {opt['name']}: {opt['total_score']:.2f}"
                )

        return "\n".join(rationale_parts)

    def _get_decision_type(self, context: DecisionContext) -> str:
        """
        Infer decision type from context.

        Args:
            context: Decision context

        Returns:
            Decision type string
        """
        # Check metadata first
        if "decision_type" in context.metadata:
            return context.metadata["decision_type"]

        # Try to infer from options
        options = context.available_options
        if options:
            first_option = options[0]

            # Check for tech stack indicators
            if any(key in first_option for key in ["category", "language", "framework", "ecosystem"]):
                return "tech_stack"

            # Check for task indicators
            if any(key in first_option for key in ["task_id", "depends_on", "priority"]):
                return "task_ordering"

            # Check for approach indicators
            if any(key in first_option for key in ["complexity", "performance", "maintainability"]):
                return "approach"

            # Check for architecture indicators
            if any(key in first_option for key in ["pattern_type", "category", "architectural_style"]):
                return "architecture"

        return "generic"
