#!/usr/bin/env python3
"""
Architecture Strategy for Autonomous Architectural Pattern Selection

Implements DecisionStrategy for selecting architectural patterns based on PRD
requirements, best practices, and existing codebase architecture.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from decision_strategy import DecisionStrategy, DecisionContext, Decision


@dataclass
class ArchitecturalPattern:
    """
    Represents an architectural pattern.

    Attributes:
        name: Pattern name
        category: Pattern category (UI, API, DISTRIBUTED, ASYNC)
        description: Brief description of the pattern
        use_cases: Common use cases for this pattern
        benefits: Benefits of using this pattern
        drawbacks: Drawbacks and limitations of this pattern
    """
    name: str
    category: str
    description: str
    use_cases: List[str]
    benefits: List[str]
    drawbacks: List[str]


# Architectural pattern knowledge base
ARCHITECTURAL_PATTERNS = {
    'MVC': ArchitecturalPattern(
        name='MVC',
        category='UI',
        description='Model-View-Controller: Separates application logic into three interconnected components.',
        use_cases=[
            'Traditional web applications',
            'Applications with clear separation of concerns',
            'Server-side rendered applications',
        ],
        benefits=[
            'Clear separation of concerns',
            'Well-established pattern with extensive documentation',
            'Easy to test individual components',
            'Multiple developers can work on separate components simultaneously',
        ],
        drawbacks=[
            'Can lead to excessive controller logic',
            'Views often contain logic, blurring the separation',
            'Not ideal for complex interactive UIs',
        ],
    ),
    'MVP': ArchitecturalPattern(
        name='MVP',
        category='UI',
        description='Model-View-Presenter: Similar to MVC but with a presenter that handles all UI logic.',
        use_cases=[
            'Desktop applications',
            'Mobile applications',
            'Applications requiring extensive UI testing',
        ],
        benefits=[
            'Better testability than MVC',
            'Clearer separation between view and logic',
            'Passive view makes testing easier',
        ],
        drawbacks=[
            'Can create complex presenter classes',
            'More boilerplate than simpler patterns',
            'View and presenter can become tightly coupled',
        ],
    ),
    'MVVM': ArchitecturalPattern(
        name='MVVM',
        category='UI',
        description='Model-View-ViewModel: Uses data binding to synchronize view with viewmodel.',
        use_cases=[
            'Modern reactive applications',
            'Applications with complex UI state management',
            'Cross-platform applications',
        ],
        benefits=[
            'Excellent for reactive programming',
            'Data binding reduces boilerplate',
            'Great for designer-developer workflow',
            'Testable viewmodels without UI dependencies',
        ],
        drawbacks=[
            'Data binding can be hard to debug',
            'Memory leaks if not careful with bindings',
            'Overkill for simple applications',
        ],
    ),
    'Component-Based': ArchitecturalPattern(
        name='Component-Based',
        category='UI',
        description='Architecture built from reusable, self-contained components.',
        use_cases=[
            'Single Page Applications',
            'Design system implementations',
            'Applications with many reusable UI elements',
        ],
        benefits=[
            'High reusability',
            'Clear component boundaries',
            'Easy to compose complex UIs from simple parts',
            'Natural fit with modern frameworks (React, Vue)',
        ],
        drawbacks=[
            'Prop drilling can make state management complex',
            'Over-abstraction can reduce readability',
            'Can lead to component hierarchy complexity',
        ],
    ),
    'Layered': ArchitecturalPattern(
        name='Layered',
        category='API',
        description='Organizes code into layers (presentation, business, data) with unidirectional dependencies.',
        use_cases=[
            'Enterprise applications',
            'Applications with clear business logic',
            'Traditional REST APIs',
        ],
        benefits=[
            'Clear separation of concerns',
            'Easy to understand and navigate',
            'Well-established pattern',
            'Layers can be swapped independently',
        ],
        drawbacks=[
            'Can lead to pass-through layers',
            'Changes often require modifications across layers',
            'Can create unnecessary abstractions',
        ],
    ),
    'Hexagonal': ArchitecturalPattern(
        name='Hexagonal',
        category='API',
        description='Ports and adapters architecture isolating core logic from external concerns.',
        use_cases=[
            'Applications requiring high testability',
            'Systems with multiple external integrations',
            'Domain-driven design projects',
        ],
        benefits=[
            'Core business logic isolated from infrastructure',
            'Highly testable domain logic',
            'Easy to swap external implementations',
            'Clear boundaries between concerns',
        ],
        drawbacks=[
            'Steeper learning curve',
            'Can be overkill for simple applications',
            'More boilerplate and indirection',
        ],
    ),
    'GraphQL': ArchitecturalPattern(
        name='GraphQL',
        category='API',
        description='Query language for APIs allowing clients to request exactly the data they need.',
        use_cases=[
            'Applications with complex data requirements',
            'Mobile applications needing efficient data fetching',
            'Applications with many different client needs',
        ],
        benefits=[
            'Clients get exactly the data they need',
            'Strongly typed schema',
            'Excellent for complex, interconnected data',
            'Single endpoint for all operations',
        ],
        drawbacks=[
            'More complex than REST for simple APIs',
            'Caching and security can be challenging',
            'Over-fetching can still occur with poor queries',
        ],
    ),
    'Microservices': ArchitecturalPattern(
        name='Microservices',
        category='DISTRIBUTED',
        description='Architecture where services are loosely coupled and independently deployable.',
        use_cases=[
            'Large, complex applications',
            'Applications requiring independent scaling',
            'Teams with different tech stacks',
        ],
        benefits=[
            'Independent deployment and scaling',
            'Technology diversity',
            'Fault isolation',
            'Team autonomy',
        ],
        drawbacks=[
            'Increased operational complexity',
            'Distributed system challenges',
            'Data consistency complexity',
            'Network latency and reliability',
        ],
    ),
    'Event-Driven': ArchitecturalPattern(
        name='Event-Driven',
        category='DISTRIBUTED',
        description='Architecture where services communicate through events asynchronously.',
        use_cases=[
            'Applications requiring real-time updates',
            'Systems with loose coupling requirements',
            'High scalability requirements',
        ],
        benefits=[
            'Loose coupling between services',
            'Excellent for real-time processing',
            'Natural fit for message queues',
            'Asynchronous processing',
        ],
        drawbacks=[
            'Debugging can be difficult',
            'Event schema versioning challenges',
            'Eventual consistency complexity',
            'Harder to reason about flow',
        ],
    ),
    'CQRS': ArchitecturalPattern(
        name='CQRS',
        category='DISTRIBUTED',
        description='Command Query Responsibility Segregation: Separates read and write operations.',
        use_cases=[
            'High-performance applications',
            'Applications with complex read/write needs',
            'Domain-driven design projects',
        ],
        benefits=[
            'Optimized for different read/write patterns',
            'Scales reads and writes independently',
            'Clear separation of concerns',
            'Better for complex domains',
        ],
        drawbacks=[
            'Increased complexity',
            'Eventual consistency challenges',
            'More code to maintain',
            'Overkill for simple CRUD',
        ],
    ),
    'Reactive': ArchitecturalPattern(
        name='Reactive',
        category='ASYNC',
        description='Architecture based on asynchronous data streams and change propagation.',
        use_cases=[
            'Real-time applications',
            'Applications with high concurrency',
            'User interface with live updates',
        ],
        benefits=[
            'Excellent for real-time updates',
            'Efficient resource usage',
            'Natural handling of async operations',
            'Backpressure handling',
        ],
        drawbacks=[
            'Steeper learning curve',
            'Debugging can be challenging',
            'Memory leaks if not careful',
            'Overkill for simple operations',
        ],
    ),
    'Pub-Sub': ArchitecturalPattern(
        name='Pub-Sub',
        category='ASYNC',
        description='Publish-subscribe pattern for message passing between components.',
        use_cases=[
            'Event notification systems',
            'Loosely coupled communication',
            'Broadcast scenarios',
        ],
        benefits=[
            'Loose coupling between publishers and subscribers',
            'Scalable to many subscribers',
            'Flexible communication pattern',
            'Natural fit for message brokers',
        ],
        drawbacks=[
            'Harder to debug message flow',
            'No guarantee of delivery without additional infrastructure',
            'Message ordering challenges',
        ],
    ),
    'Actor Model': ArchitecturalPattern(
        name='Actor Model',
        category='ASYNC',
        description='Architecture where actors communicate through message passing.',
        use_cases=[
            'Distributed systems',
            'Highly concurrent applications',
            'Fault-tolerant systems',
        ],
        benefits=[
            'Excellent for concurrency',
            'Fault tolerance through supervision',
            'Distributed by nature',
            'No shared state',
        ],
        drawbacks=[
            'Steep learning curve',
            'Debugging distributed actors is hard',
            'Message ordering can be complex',
            'Overhead for simple applications',
        ],
    ),
}

# Category to patterns mapping
PATTERNS_BY_CATEGORY = {
    'UI': ['MVC', 'MVP', 'MVVM', 'Component-Based'],
    'API': ['Layered', 'Hexagonal', 'GraphQL'],
    'DISTRIBUTED': ['Microservices', 'Event-Driven', 'CQRS'],
    'ASYNC': ['Reactive', 'Pub-Sub', 'Actor Model'],
}

# Problem domain to architectural pattern mappings
DOMAIN_PATTERN_MAPPINGS = {
    'web_ui': {
        'primary': ['Component-Based', 'MVVM'],
        'secondary': ['MVC'],
    },
    'web_api': {
        'primary': ['Layered', 'Hexagonal'],
        'secondary': ['GraphQL'],
    },
    'distributed_system': {
        'primary': ['Microservices', 'Event-Driven'],
        'secondary': ['CQRS'],
    },
    'real_time': {
        'primary': ['Reactive', 'Event-Driven'],
        'secondary': ['Pub-Sub'],
    },
    'mobile_app': {
        'primary': ['MVVM', 'MVP'],
        'secondary': ['Component-Based'],
    },
    'enterprise': {
        'primary': ['Hexagonal', 'Layered', 'CQRS'],
        'secondary': ['Event-Driven'],
    },
}


class ArchitectureStrategy(DecisionStrategy):
    """
    Strategy for making architectural pattern decisions.

    Applies default decision hierarchy:
    1. Problem domain requirements (from PRD)
    2. Existing codebase patterns (consistency)
    3. Best practices (industry standards)
    4. Simplicity (choose simplest viable option)
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize ArchitectureStrategy.

        Args:
            project_root: Optional path to project root for pattern detection
        """
        self.project_root = Path(project_root) if project_root else None
        self._existing_patterns: Optional[Dict[str, List[str]]] = None

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "architecture_autonomous"

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return (
            "Autonomous architectural pattern selection based on PRD requirements, "
            "problem domain, existing codebase patterns, and best practices. "
            "Applies hierarchy: domain requirements → existing patterns → best practices → simplicity"
        )

    def get_supported_decision_types(self) -> List[str]:
        """Return supported decision types."""
        return [
            "architecture",
            "architectural_pattern",
            "ui_architecture",
            "api_architecture",
            "distributed_architecture",
            "async_architecture",
        ]

    def validate_context(self, context: DecisionContext) -> bool:
        """
        Validate decision context.

        Args:
            context: Decision context to validate

        Returns:
            True if valid

        Raises:
            ValueError: If context is invalid
        """
        if not context:
            raise ValueError("Context cannot be None or empty")

        if not context.prd_requirements:
            raise ValueError("PRD requirements are required for architectural pattern selection")

        return True

    def decide(self, context: DecisionContext) -> Decision:
        """
        Select architectural pattern based on PRD requirements and decision hierarchy.

        Args:
            context: Decision context with PRD requirements, current state, and options

        Returns:
            Decision with selected architectural pattern and rationale

        Raises:
            ValueError: If context is invalid
            RuntimeError: If decision cannot be made
        """
        # Validate context
        self.validate_context(context)

        # Detect problem domain from PRD requirements
        domain = self._detect_domain(context.prd_requirements)

        # Detect category from PRD requirements or domain
        category = self._detect_category(context.prd_requirements, domain)

        # Get candidate patterns for category
        candidate_patterns = self._get_candidate_patterns(category, context)

        if not candidate_patterns:
            raise RuntimeError(f"No viable architectural patterns found for category: {category}")

        # Load existing patterns if project root is provided
        if self.project_root:
            self._load_existing_patterns()

        # Score each pattern based on decision hierarchy
        scored_patterns = []
        for pattern_name in candidate_patterns:
            pattern = ARCHITECTURAL_PATTERNS.get(pattern_name)
            if not pattern:
                continue

            score = self.score_pattern(pattern, context, domain)
            scored_patterns.append((score, pattern))

        # Sort by score descending
        scored_patterns.sort(key=lambda x: x[0], reverse=True)

        # Get top choice
        if not scored_patterns:
            raise RuntimeError("No viable architectural patterns could be scored")

        top_score, top_pattern = scored_patterns[0]
        second_score = scored_patterns[1][0] if len(scored_patterns) > 1 else 0.0

        # Calculate confidence
        confidence = self.get_confidence(top_score, second_score, len(scored_patterns))

        # Build rationale
        rationale = self._build_rationale(top_pattern, top_score, context, domain)

        # Extract alternatives
        alternatives = [
            pattern.name for score, pattern in scored_patterns[1:4]
        ]  # Top 3 alternatives

        return Decision(
            choice=top_pattern.name,
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
            context_snapshot=context.to_dict(),
            decision_type="architecture",
            metadata={
                "category": category,
                "domain": domain,
                "score": top_score,
                "scoring_breakdown": self._get_scoring_breakdown(top_pattern, context, domain),
            },
        )

    def score_pattern(
        self,
        pattern: ArchitecturalPattern,
        context: DecisionContext,
        domain: str
    ) -> float:
        """
        Score an architectural pattern based on decision hierarchy.

        Scoring criteria (1.0 max):
        - 0.40: Domain requirements (problem domain fit)
        - 0.30: Existing patterns (consistency with codebase)
        - 0.20: Best practices (industry standards)
        - 0.10: Simplicity (ease of implementation)

        Args:
            pattern: Architectural pattern to score
            context: Decision context
            domain: Detected problem domain

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0

        # 1. Domain requirements (40 points)
        domain_score = self._score_domain_requirements(pattern, domain, context)
        score += domain_score * 0.40

        # 2. Existing patterns (30 points)
        existing_score = self._score_existing_patterns(pattern)
        score += existing_score * 0.30

        # 3. Best practices (20 points)
        best_practice_score = self._score_best_practices(pattern, domain)
        score += best_practice_score * 0.20

        # 4. Simplicity (10 points)
        simplicity_score = self._score_simplicity(pattern)
        score += simplicity_score * 0.10

        return min(score, 1.0)

    def _detect_domain(self, prd_requirements: Dict[str, Any]) -> str:
        """
        Detect problem domain from PRD requirements.

        Args:
            prd_requirements: PRD requirements dictionary

        Returns:
            Detected domain name
        """
        requirements_text = str(prd_requirements).lower()

        # Domain detection keywords (ordered by specificity)
        domain_keywords = {
            'distributed_system': [
                'microservice', 'microservices', 'distributed system',
                'scalable architecture', 'service mesh',
            ],
            'real_time': [
                'real-time', 'realtime', 'live streaming', 'streaming application',
                'websocket', 'push notification', 'actor model',
            ],
            'mobile_app': [
                'mobile app', 'ios and android', 'mobile application',
            ],
            'enterprise': [
                'enterprise system', 'domain-driven', 'ddd',
                'complex business logic', 'cqrs',
            ],
            'web_ui': [
                'user interface', 'frontend', 'dashboard application',
                'spa', 'single page', 'component-based',
            ],
            'web_api': [
                'rest api', 'backend api', 'web service', 'graphql',
                'api server', 'service layer',
            ],
        }

        # Score each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in requirements_text)
            if score > 0:
                domain_scores[domain] = score

        # Return highest scoring domain or default
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]

        return 'web_api'  # Default domain

    def _detect_category(self, prd_requirements: Dict[str, Any], domain: str) -> str:
        """
        Detect architectural category from PRD requirements and domain.

        Args:
            prd_requirements: PRD requirements
            domain: Detected problem domain

        Returns:
            Detected category name
        """
        # Check if category is explicitly specified
        if 'category' in prd_requirements:
            category = prd_requirements['category'].upper()
            if category in PATTERNS_BY_CATEGORY:
                return category

        # Map domain to category
        domain_to_category = {
            'web_ui': 'UI',
            'mobile_app': 'UI',
            'web_api': 'API',
            'enterprise': 'API',
            'distributed_system': 'DISTRIBUTED',
            'real_time': 'ASYNC',
        }

        return domain_to_category.get(domain, 'API')

    def _get_candidate_patterns(self, category: str, context: DecisionContext) -> List[str]:
        """
        Get candidate patterns for a category.

        Args:
            category: Architectural pattern category
            context: Decision context

        Returns:
            List of pattern names
        """
        # Use available options if provided
        if context.available_options:
            return [
                opt.get("name") or opt.get("pattern", opt.get("choice"))
                for opt in context.available_options
                if opt.get("name") or opt.get("pattern") or opt.get("choice")
            ]

        # Otherwise, get all patterns for category
        return PATTERNS_BY_CATEGORY.get(category, list(ARCHITECTURAL_PATTERNS.keys()))

    def _load_existing_patterns(self) -> None:
        """Load existing architectural patterns from codebase."""
        if not self.project_root:
            return

        self._existing_patterns = {
            'UI': [],
            'API': [],
            'DISTRIBUTED': [],
            'ASYNC': [],
        }

        # Detect patterns in codebase
        scripts_dir = Path(__file__).parent
        detect_patterns_path = scripts_dir / "detect_patterns.py"

        if detect_patterns_path.exists():
            try:
                result = subprocess.run(
                    ["python3", str(detect_patterns_path), str(self.project_root)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    patterns_data = json.loads(result.stdout)
                    self._existing_patterns = patterns_data.get("architectural_patterns", self._existing_patterns)
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                pass

    def _score_domain_requirements(
        self,
        pattern: ArchitecturalPattern,
        domain: str,
        context: DecisionContext
    ) -> float:
        """
        Score based on domain requirements fit.

        Args:
            pattern: Architectural pattern
            domain: Problem domain
            context: Decision context

        Returns:
            Score from 0.0 to 1.0
        """
        domain_mappings = DOMAIN_PATTERN_MAPPINGS.get(domain, {})

        # Check if pattern is a primary fit for domain
        if pattern.name in domain_mappings.get('primary', []):
            return 1.0

        # Check if pattern is a secondary fit
        if pattern.name in domain_mappings.get('secondary', []):
            return 0.7

        # Check if pattern category matches domain
        domain_to_category = {
            'web_ui': 'UI',
            'mobile_app': 'UI',
            'web_api': 'API',
            'enterprise': 'API',
            'distributed_system': 'DISTRIBUTED',
            'real_time': 'ASYNC',
        }

        expected_category = domain_to_category.get(domain)
        if pattern.category == expected_category:
            return 0.5

        return 0.2  # Poor fit

    def _score_existing_patterns(self, pattern: ArchitecturalPattern) -> float:
        """
        Score based on existing patterns in codebase.

        Args:
            pattern: Architectural pattern

        Returns:
            Score from 0.0 to 1.0
        """
        if not self._existing_patterns:
            return 0.5  # Neutral if no codebase data

        category_patterns = self._existing_patterns.get(pattern.category, [])

        if pattern.name in category_patterns:
            return 1.0  # Already in codebase

        # Check for patterns in same category (consistency)
        if category_patterns:
            return 0.7  # Same category, different pattern

        return 0.5  # No existing patterns in this category

    def _score_best_practices(self, pattern: ArchitecturalPattern, domain: str) -> float:
        """
        Score based on industry best practices.

        Args:
            pattern: Architectural pattern
            domain: Problem domain

        Returns:
            Score from 0.0 to 1.0
        """
        # Best practice rankings for each category
        best_practice_rankings = {
            'UI': {
                'Component-Based': 1,  # Modern standard
                'MVVM': 2,
                'MVC': 3,
                'MVP': 4,
            },
            'API': {
                'Layered': 1,  # Time-tested
                'Hexagonal': 2,  # Growing adoption
                'GraphQL': 3,  # Specialized use
            },
            'DISTRIBUTED': {
                'Event-Driven': 1,  # Modern standard
                'Microservices': 2,  # Overused but valid
                'CQRS': 3,  # Specialized
            },
            'ASYNC': {
                'Reactive': 1,  # Modern standard
                'Pub-Sub': 2,
                'Actor Model': 3,  # Complex but powerful
            },
        }

        rankings = best_practice_rankings.get(pattern.category, {})
        rank = rankings.get(pattern.name, 5)

        # Return score based on rank (1.0, 0.8, 0.6, 0.4, 0.2)
        return max(0.2, 1.0 - ((rank - 1) * 0.2))

    def _score_simplicity(self, pattern: ArchitecturalPattern) -> float:
        """
        Score based on simplicity and ease of implementation.

        Args:
            pattern: Architectural pattern

        Returns:
            Score from 0.0 to 1.0
        """
        # Simplicity rankings (simpler = higher score)
        simplicity_rankings = {
            'UI': {
                'Component-Based': 0.9,
                'MVC': 0.8,
                'MVVM': 0.7,
                'MVP': 0.6,
            },
            'API': {
                'Layered': 0.9,
                'GraphQL': 0.7,
                'Hexagonal': 0.5,
            },
            'DISTRIBUTED': {
                'Event-Driven': 0.7,
                'Microservices': 0.5,
                'CQRS': 0.4,
            },
            'ASYNC': {
                'Pub-Sub': 0.8,
                'Reactive': 0.6,
                'Actor Model': 0.4,
            },
        }

        rankings = simplicity_rankings.get(pattern.category, {})
        return rankings.get(pattern.name, 0.5)

    def _build_rationale(
        self,
        pattern: ArchitecturalPattern,
        score: float,
        context: DecisionContext,
        domain: str
    ) -> str:
        """
        Build human-readable rationale for decision.

        Args:
            pattern: Selected pattern
            score: Final score
            context: Decision context
            domain: Problem domain

        Returns:
            Rationale string
        """
        parts = [f"Selected {pattern.name} architectural pattern for {domain} development."]

        # Add domain fit rationale
        domain_mappings = DOMAIN_PATTERN_MAPPINGS.get(domain, {})
        if pattern.name in domain_mappings.get('primary', []):
            parts.append(f"It's a primary fit for {domain} applications.")
        elif pattern.name in domain_mappings.get('secondary', []):
            parts.append(f"It's a viable option for {domain} applications.")

        # Add existing patterns rationale
        if self._existing_patterns:
            category_patterns = self._existing_patterns.get(pattern.category, [])
            if pattern.name in category_patterns:
                parts.append("Already used in the codebase, ensuring consistency.")

        # Add best practices rationale
        best_practice_score = self._score_best_practices(pattern, domain)
        if best_practice_score >= 0.8:
            parts.append("Considered a best practice for this category.")

        # Add simplicity rationale
        simplicity_score = self._score_simplicity(pattern)
        if simplicity_score >= 0.8:
            parts.append("Chosen for its relative simplicity and ease of implementation.")
        elif simplicity_score <= 0.5:
            parts.append("Note: This pattern adds complexity but provides significant benefits.")

        # Add key benefits
        if pattern.benefits:
            top_benefit = pattern.benefits[0]
            parts.append(f"Key benefit: {top_benefit.lower()}")

        return " ".join(parts)

    def _get_scoring_breakdown(
        self,
        pattern: ArchitecturalPattern,
        context: DecisionContext,
        domain: str
    ) -> Dict[str, float]:
        """
        Get detailed scoring breakdown for a pattern.

        Args:
            pattern: Architectural pattern
            context: Decision context
            domain: Problem domain

        Returns:
            Dictionary with scoring breakdown
        """
        return {
            "domain_requirements": self._score_domain_requirements(pattern, domain, context),
            "existing_patterns": self._score_existing_patterns(pattern),
            "best_practices": self._score_best_practices(pattern, domain),
            "simplicity": self._score_simplicity(pattern),
        }
