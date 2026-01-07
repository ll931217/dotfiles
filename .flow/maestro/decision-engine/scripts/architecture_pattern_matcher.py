#!/usr/bin/env python3
"""
Architecture Pattern Matcher

Analyzes feature complexity and codebase patterns to recommend appropriate
architectural patterns. Integrates with detect_patterns.py for codebase analysis.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class PatternRecommendation:
    """Represents a pattern recommendation with metadata."""
    pattern: str
    complexity: str
    confidence: str
    rationale: List[str]
    existing_patterns_used: List[str]
    scalability_assessment: str
    alternatives: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary, replacing rationale list with joined string."""
        data = asdict(self)
        data['rationale'] = '; '.join(self.rationale)
        return data


# Pattern knowledge base with complexity mappings and indicators
PATTERN_KNOWLEDGE_BASE = {
    'simple_function': {
        'name': 'Simple Function',
        'complexity': 'low',
        'indicators': [
            'single responsibility',
            'no state management',
            'no side effects',
            'pure function',
            'stateless operation',
        ],
        'use_when': [
            'data transformation',
            'validation',
            'calculation',
            'format conversion',
            'utility function',
        ],
        'avoid_when': [
            'multiple operations',
            'state management',
            'external dependencies',
            'business logic coordination',
        ],
        'scalability': 'high - easily composable and testable',
        'alternatives': ['service-layer', 'decorator'],
    },
    'service_layer': {
        'name': 'Service Layer',
        'complexity': 'medium',
        'indicators': [
            'multiple operations coordinated',
            'business rules enforcement',
            'cross-component communication',
            'transactional operations',
            'external dependencies',
        ],
        'use_when': [
            'business logic',
            'data access coordination',
            'complex operations',
            'multiple repositories',
            'transaction management',
        ],
        'avoid_when': [
            'trivial CRUD',
            'simple data access',
            'single operation',
        ],
        'scalability': 'medium - requires careful dependency management',
        'alternatives': ['simple_function', 'repository'],
    },
    'repository': {
        'name': 'Repository Pattern',
        'complexity': 'medium',
        'indicators': [
            'database operations',
            'multiple data sources',
            'query abstraction',
            'testing requires mocking',
            'data access layer',
        ],
        'use_when': [
            'database access',
            'complex queries',
            'multiple data sources',
            'orm abstraction',
            'data caching',
        ],
        'avoid_when': [
            'simple queries',
            'direct database access',
            'single data source',
        ],
        'scalability': 'medium - adds abstraction layer',
        'alternatives': ['simple_function', 'service-layer'],
    },
    'factory': {
        'name': 'Factory Pattern',
        'complexity': 'low-medium',
        'indicators': [
            'object type determined at runtime',
            'multiple object variants',
            'complex initialization logic',
            'future extensibility needed',
            'object creation',
        ],
        'use_when': [
            'creating objects with variants',
            'runtime object selection',
            'complex initialization',
            'extensible object creation',
        ],
        'avoid_when': [
            'single object type',
            'simple constructors',
            'fixed object types',
        ],
        'scalability': 'high - easy to add new types',
        'alternatives': ['simple_function', 'builder'],
    },
    'strategy': {
        'name': 'Strategy Pattern',
        'complexity': 'medium',
        'indicators': [
            'multiple valid algorithms',
            'runtime algorithm selection',
            'algorithm varies by context',
            'interchangeable behavior',
        ],
        'use_when': [
            'interchangeable algorithms',
            'runtime behavior selection',
            'multiple implementations',
            'algorithm testing',
        ],
        'avoid_when': [
            'fixed algorithm',
            'single implementation',
            'no variation needed',
        ],
        'scalability': 'high - easy to add new strategies',
        'alternatives': ['simple_function', 'factory'],
    },
    'middleware': {
        'name': 'Middleware Pattern',
        'complexity': 'medium',
        'indicators': [
            'sequential processing steps',
            'request/response transformation',
            'cross-cutting concerns',
            'composable operations',
            'pipeline processing',
        ],
        'use_when': [
            'request/response pipeline',
            'authentication',
            'logging',
            'rate limiting',
            'data transformation',
        ],
        'avoid_when': [
            'simple transformations',
            'direct handling',
            'no pipeline needed',
        ],
        'scalability': 'high - easy to add/remove middleware',
        'alternatives': ['decorator', 'service-layer'],
    },
    'observer': {
        'name': 'Observer Pattern',
        'complexity': 'medium',
        'indicators': [
            'one-to-many communication',
            'loose coupling required',
            'event-driven behavior',
            'asynchronous updates',
            'notification system',
        ],
        'use_when': [
            'event-driven updates',
            'loose coupling',
            'notifications',
            'cache invalidation',
            'async processing',
        ],
        'avoid_when': [
            'tight coupling acceptable',
            'direct calls preferred',
            'synchronous processing',
        ],
        'scalability': 'medium - requires careful event management',
        'alternatives': ['simple_function', 'middleware'],
    },
    'decorator': {
        'name': 'Decorator Pattern',
        'complexity': 'low-medium',
        'indicators': [
            'add behavior without modification',
            'composable enhancements',
            'runtime decoration',
            'separation of concerns',
            'behavior extension',
        ],
        'use_when': [
            'adding behavior dynamically',
            'caching',
            'validation',
            'logging',
            'behavior composition',
        ],
        'avoid_when': [
            'static behavior',
            'direct implementation',
            'no composition needed',
        ],
        'scalability': 'high - easily composable',
        'alternatives': ['simple_function', 'middleware'],
    },
}


class ComplexityAssessor:
    """Assesses feature complexity from natural language descriptions."""

    COMPLEXITY_KEYWORDS = {
        'low': [
            'simple', 'basic', 'single', 'straightforward', 'trivial',
            'validate', 'format', 'convert', 'calculate', 'transform',
            'utility', 'helper', 'pure function', 'stateless',
        ],
        'medium': [
            'create', 'update', 'delete', 'manage', 'process',
            'multiple', 'coordinate', 'business logic', 'service',
            'repository', 'data access', 'api', 'endpoint',
            'authentication', 'authorization', 'transaction',
        ],
        'high': [
            'complex', 'orchestrate', 'workflow', 'pipeline',
            'multiple services', 'distributed', 'async', 'event-driven',
            'integration', 'microservices', 'scalability', 'high load',
            'real-time', 'streaming', 'batch processing',
        ],
    }

    @classmethod
    def assess(cls, description: str) -> str:
        """
        Assess complexity from natural language description.

        Returns: 'low', 'medium', or 'high'
        """
        description_lower = description.lower()

        # Count keyword matches for each complexity level
        scores = {
            'low': sum(1 for kw in cls.COMPLEXITY_KEYWORDS['low'] if kw in description_lower),
            'medium': sum(1 for kw in cls.COMPLEXITY_KEYWORDS['medium'] if kw in description_lower),
            'high': sum(1 for kw in cls.COMPLEXITY_KEYWORDS['high'] if kw in description_lower),
        }

        # Weight high complexity more heavily
        scores['high'] *= 3
        scores['medium'] *= 2

        # Return highest scoring complexity
        if scores['high'] > 0:
            return 'high'
        elif scores['medium'] > 0 or scores['low'] > 0:
            if scores['medium'] >= scores['low']:
                return 'medium'
            return 'low'
        else:
            # Default to medium if no keywords found
            return 'medium'


class ScalabilityEvaluator:
    """Evaluates scalability implications of patterns."""

    SCALABILITY_ASSESSMENTS = {
        'simple_function': 'high - stateless, easily composable',
        'service_layer': 'medium - requires careful dependency management',
        'repository': 'medium - adds abstraction layer but enables testing',
        'factory': 'high - easy to add new types',
        'strategy': 'high - easy to add new strategies',
        'middleware': 'high - easy to add/remove middleware',
        'observer': 'medium - requires careful event management',
        'decorator': 'high - easily composable',
    }

    @classmethod
    def evaluate(cls, pattern: str) -> str:
        """Evaluate scalability for a given pattern."""
        return cls.SCALABILITY_ASSESSMENTS.get(pattern, 'unknown')


class ArchitecturePatternMatcher:
    """Main architecture pattern matching engine."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.existing_patterns = self._load_existing_patterns()

    def _load_existing_patterns(self) -> Dict:
        """Load existing architectural patterns from detect_patterns.py."""
        scripts_dir = Path(__file__).parent
        detect_patterns_path = scripts_dir / "detect_patterns.py"

        if not detect_patterns_path.exists():
            return {}

        try:
            result = subprocess.run(
                ["python3", str(detect_patterns_path), str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return {}

    def _get_pattern_complexity(self, pattern_key: str) -> str:
        """Get complexity level for a pattern."""
        return PATTERN_KNOWLEDGE_BASE.get(pattern_key, {}).get('complexity', 'medium')

    def _score_pattern_match(
        self,
        pattern_key: str,
        feature_description: str,
        complexity: str,
        existing_patterns: Dict,
    ) -> Tuple[int, List[str]]:
        """
        Score a pattern match against the feature requirements.

        Returns: (score, rationale_list)
        """
        pattern_data = PATTERN_KNOWLEDGE_BASE.get(pattern_key, {})
        if not pattern_data:
            return 0, ["Unknown pattern"]

        score = 0
        rationale = []

        description_lower = feature_description.lower()

        # 1. Complexity match (40 points max)
        pattern_complexity = self._get_pattern_complexity(pattern_key)
        complexity_map = {'low': 0, 'medium': 1, 'high': 2}
        complexity_diff = abs(complexity_map.get(pattern_complexity, 1) - complexity_map.get(complexity, 1))

        if complexity_diff == 0:
            score += 40
            rationale.append(f"Complexity match: {complexity}")
        elif complexity_diff == 1:
            score += 20
            rationale.append(f"Complexity close: {pattern_complexity} vs {complexity}")
        else:
            rationale.append(f"Complexity mismatch: {pattern_complexity} vs {complexity}")

        # 2. Use when keywords (40 points max)
        use_when = pattern_data.get('use_when', [])
        use_when_matches = sum(1 for kw in use_when if kw in description_lower)
        if use_when_matches > 0:
            match_score = min(40, use_when_matches * 10)
            score += match_score
            rationale.append(f"Matches use case: {use_when_matches} indicators")

        # 3. Existing pattern alignment (20 points max)
        # Map pattern keys to detect_patterns.py output keys
        pattern_mapping = {
            'service_layer': 'service-layer',
            'repository': 'repository',
            'middleware': 'middleware',
            'factory': 'factory',
            'observer': 'observer',
            'strategy': 'strategy',
            'decorator': 'decorator',
        }

        detected_key = pattern_mapping.get(pattern_key)
        if detected_key and detected_key in existing_patterns:
            score += 20
            pattern_count = existing_patterns[detected_key].get('total_matches', 0)
            rationale.append(f"Existing pattern in codebase ({pattern_count} matches)")
        elif pattern_key == 'simple_function' and not existing_patterns:
            # Simple function is good when no patterns exist
            score += 10
            rationale.append("No existing patterns - start simple")

        # 4. Avoid when penalty (automatic disqualification)
        avoid_when = pattern_data.get('avoid_when', [])
        avoid_matches = [kw for kw in avoid_when if kw in description_lower]
        if avoid_matches:
            score = max(0, score - 30)
            rationale.append(f"Warning: Avoid for {', '.join(avoid_matches)}")

        return score, rationale

    def _select_best_pattern(
        self,
        scored_patterns: List[Tuple[str, int, List[str]]],
        complexity: str,
    ) -> PatternRecommendation:
        """
        Select the best pattern from scored candidates.

        Args:
            scored_patterns: List of (pattern_key, score, rationale) tuples
            complexity: Assessed feature complexity

        Returns:
            PatternRecommendation object
        """
        if not scored_patterns:
            # Default to simple_function if nothing matches
            return PatternRecommendation(
                pattern='Simple Function',
                complexity=complexity,
                confidence='low',
                rationale=['No clear pattern match, defaulting to simple'],
                existing_patterns_used=[],
                scalability_assessment=ScalabilityEvaluator.evaluate('simple_function'),
                alternatives=['service-layer', 'repository'],
            )

        # Sort by score
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        best_pattern_key, best_score, best_rationale = scored_patterns[0]

        # Determine confidence
        if best_score >= 80:
            confidence = 'high'
        elif best_score >= 50:
            confidence = 'medium'
        else:
            confidence = 'low'

        # Get existing patterns used
        pattern_mapping = {
            'service_layer': 'service-layer',
            'repository': 'repository',
            'middleware': 'middleware',
            'factory': 'factory',
            'observer': 'observer',
            'strategy': 'strategy',
            'decorator': 'decorator',
        }
        detected_key = pattern_mapping.get(best_pattern_key)
        existing_used = []
        if detected_key and detected_key in self.existing_patterns:
            existing_used.append(detected_key)

        # Get alternatives
        alternatives = PATTERN_KNOWLEDGE_BASE.get(best_pattern_key, {}).get('alternatives', [])

        return PatternRecommendation(
            pattern=PATTERN_KNOWLEDGE_BASE[best_pattern_key]['name'],
            complexity=complexity,
            confidence=confidence,
            rationale=best_rationale,
            existing_patterns_used=existing_used,
            scalability_assessment=ScalabilityEvaluator.evaluate(best_pattern_key),
            alternatives=alternatives,
        )

    def match_pattern(self, feature_description: str, complexity: Optional[str] = None) -> Dict:
        """
        Main entry point for pattern matching.

        Args:
            feature_description: Natural language feature description
            complexity: Optional complexity override ('low', 'medium', 'high')

        Returns:
            Structured pattern recommendation with rationale
        """
        # Assess complexity if not provided
        if not complexity:
            complexity = ComplexityAssessor.assess(feature_description)

        # Score all patterns
        scored_patterns = []
        for pattern_key in PATTERN_KNOWLEDGE_BASE.keys():
            score, rationale = self._score_pattern_match(
                pattern_key,
                feature_description,
                complexity,
                self.existing_patterns,
            )
            if score > 0:
                scored_patterns.append((pattern_key, score, rationale))

        # Select best pattern
        recommendation = self._select_best_pattern(scored_patterns, complexity)

        # Build output
        return {
            "decision_type": "architecture_pattern",
            "input": feature_description,
            "output": {
                "decision": recommendation.pattern,
                "rationale": recommendation.to_dict()['rationale'],
                "confidence": recommendation.confidence,
                "context": {
                    "complexity": complexity,
                    "existing_patterns_detected": list(self.existing_patterns.keys()),
                    "existing_patterns_used": recommendation.existing_patterns_used,
                    "scalability_assessment": recommendation.scalability_assessment,
                },
                "alternatives": recommendation.alternatives,
                "all_scored_patterns": [
                    {
                        "pattern": PATTERN_KNOWLEDGE_BASE[key]['name'],
                        "score": score,
                        "rationale": '; '.join(rationale),
                    }
                    for key, score, rationale in sorted(scored_patterns, key=lambda x: x[1], reverse=True)[:5]
                ],
            },
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Architecture pattern matcher for autonomous pattern decisions"
    )
    parser.add_argument("project_root", help="Path to project root directory")
    parser.add_argument("feature_description", help="Feature description (e.g., 'Implement user authentication')")
    parser.add_argument(
        "--complexity",
        choices=['low', 'medium', 'high'],
        help="Override complexity assessment",
        default=None,
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "pretty"],
        default="pretty",
        help="Output format",
    )

    args = parser.parse_args()

    # Run pattern matching
    matcher = ArchitecturePatternMatcher(args.project_root)
    result = matcher.match_pattern(args.feature_description, args.complexity)

    # Output
    if args.output_format == "pretty":
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
