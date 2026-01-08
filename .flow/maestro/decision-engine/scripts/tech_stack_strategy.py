#!/usr/bin/env python3
"""
Tech Stack Strategy for Autonomous Technology Selection

Implements DecisionStrategy for selecting languages, frameworks, and libraries
based on PRD requirements, best practices, and existing codebase patterns.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from decision_strategy import DecisionStrategy, DecisionContext, Decision


# Technology knowledge base with scoring criteria
TECH_KNOWLEDGE_BASE = {
    'authentication': {
        'Passport.js': {
            'category': 'authentication',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['Auth.js', 'Auth0', 'custom JWT'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['passport', 'passport-', 'passport-local'],
            'best_practice_rank': 1,
        },
        'Auth.js': {
            'category': 'authentication',
            'maturity_score': 20,
            'community_score': 12,
            'fit_score': 20,
            'alternatives': ['Passport.js', 'Auth0', 'custom JWT'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['next-auth', '@auth/core', 'authjs'],
            'best_practice_rank': 2,
        },
        'Auth0': {
            'category': 'authentication',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 15,
            'alternatives': ['Passport.js', 'Auth.js', 'custom implementation'],
            'ecosystem': 'any',
            'detect_patterns': ['auth0', '@auth0/'],
            'best_practice_rank': 3,
        },
        'custom JWT': {
            'category': 'authentication',
            'maturity_score': 20,
            'community_score': 10,
            'fit_score': 15,
            'alternatives': ['Passport.js', 'Auth.js', 'Auth0'],
            'ecosystem': 'any',
            'detect_patterns': ['jsonwebtoken', 'jwt', 'jwt.verify'],
            'best_practice_rank': 4,
        },
    },
    'database': {
        'PostgreSQL': {
            'category': 'database',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['MySQL', 'MongoDB', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['pg', 'postgres', 'postgresql', 'psycopg'],
            'best_practice_rank': 1,
        },
        'MySQL': {
            'category': 'database',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['PostgreSQL', 'MongoDB', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['mysql', 'mysql2'],
            'best_practice_rank': 2,
        },
        'MongoDB': {
            'category': 'database',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 18,
            'alternatives': ['PostgreSQL', 'Redis', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['mongodb', 'mongoose', 'mongo'],
            'best_practice_rank': 3,
        },
        'Redis': {
            'category': 'database',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['PostgreSQL', 'Memcached', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['redis', '@redis/', 'ioredis'],
            'best_practice_rank': 4,
        },
        'SQLite': {
            'category': 'database',
            'maturity_score': 20,
            'community_score': 10,
            'fit_score': 12,
            'alternatives': ['PostgreSQL', 'MongoDB', 'Redis'],
            'ecosystem': 'any',
            'detect_patterns': ['sqlite', 'sqlite3', 'better-sqlite3'],
            'best_practice_rank': 5,
        },
    },
    'frontend_framework': {
        'React': {
            'category': 'frontend_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['Vue', 'Svelte', 'Vanilla'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['react', 'react-dom', '@react/', 'useState', 'useEffect'],
            'best_practice_rank': 1,
        },
        'Vue': {
            'category': 'frontend_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 18,
            'alternatives': ['React', 'Svelte', 'Vanilla'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['vue', '@vue/', 'Vue.', 'v-if', 'v-for'],
            'best_practice_rank': 2,
        },
        'Svelte': {
            'category': 'frontend_framework',
            'maturity_score': 20,
            'community_score': 12,
            'fit_score': 18,
            'alternatives': ['React', 'Vue', 'Vanilla'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['svelte', '@svelte/', 'svelte-'],
            'best_practice_rank': 3,
        },
    },
    'backend_framework': {
        'Express': {
            'category': 'backend_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['FastAPI', 'Django', 'Go stdlib'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['express', 'express()', 'app.use', 'app.get'],
            'best_practice_rank': 1,
        },
        'FastAPI': {
            'category': 'backend_framework',
            'maturity_score': 20,
            'community_score': 12,
            'fit_score': 20,
            'alternatives': ['Express', 'Django', 'Flask'],
            'ecosystem': 'python',
            'detect_patterns': ['fastapi', 'FastAPI', '@app.', 'APIRouter'],
            'best_practice_rank': 2,
        },
        'Django': {
            'category': 'backend_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 18,
            'alternatives': ['FastAPI', 'Flask', 'Express'],
            'ecosystem': 'python',
            'detect_patterns': ['django', 'Django', 'from django', 'models.Model'],
            'best_practice_rank': 3,
        },
        'Flask': {
            'category': 'backend_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 18,
            'alternatives': ['Django', 'FastAPI', 'Express'],
            'ecosystem': 'python',
            'detect_patterns': ['flask', 'Flask', 'app.route', 'Flask(__name__)'],
            'best_practice_rank': 4,
        },
    },
    'language': {
        'Python': {
            'category': 'language',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['JavaScript', 'Go', 'Rust'],
            'ecosystem': 'python',
            'detect_patterns': ['import ', 'from ', 'def ', 'class ', '__init__'],
            'best_practice_rank': 1,
        },
        'JavaScript': {
            'category': 'language',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['Python', 'TypeScript', 'Go'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['const ', 'let ', 'function ', '=>', 'require('],
            'best_practice_rank': 2,
        },
        'TypeScript': {
            'category': 'language',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['JavaScript', 'Python', 'Go'],
            'ecosystem': 'nodejs',
            'detect_patterns': [': string', ': number', 'interface ', 'type ', 'as '],
            'best_practice_rank': 1,
        },
        'Go': {
            'category': 'language',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 18,
            'alternatives': ['Python', 'Rust', 'JavaScript'],
            'ecosystem': 'go',
            'detect_patterns': ['func ', 'package ', 'import "', 'var ', ':='],
            'best_practice_rank': 3,
        },
        'Rust': {
            'category': 'language',
            'maturity_score': 20,
            'community_score': 12,
            'fit_score': 15,
            'alternatives': ['Go', 'C++', 'Python'],
            'ecosystem': 'rust',
            'detect_patterns': ['fn ', 'use ', 'let mut', 'impl ', 'pub fn'],
            'best_practice_rank': 4,
        },
    },
    'cli_framework': {
        'Click': {
            'category': 'cli_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['Typer', 'argparse', 'clap'],
            'ecosystem': 'python',
            'detect_patterns': ['@click.command', '@click.option', 'click.echo'],
            'best_practice_rank': 1,
        },
        'Typer': {
            'category': 'cli_framework',
            'maturity_score': 20,
            'community_score': 12,
            'fit_score': 20,
            'alternatives': ['Click', 'argparse', 'clap'],
            'ecosystem': 'python',
            'detect_patterns': ['@app.command', '@app.option', 'typer.run'],
            'best_practice_rank': 2,
        },
        'clap': {
            'category': 'cli_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 18,
            'alternatives': ['Click', 'Typer', 'argparse'],
            'ecosystem': 'rust',
            'detect_patterns': ['clap::Parser', 'clap::Parser', 'CommandFactory'],
            'best_practice_rank': 3,
        },
        'Commander': {
            'category': 'cli_framework',
            'maturity_score': 25,
            'community_score': 15,
            'fit_score': 20,
            'alternatives': ['Yargs', 'oclif', 'Click'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['commander.', 'program.parse', 'program.command'],
            'best_practice_rank': 1,
        },
    },
}

# Problem domain to best practice mappings
DOMAIN_BEST_PRACTICES = {
    'web_api': {
        'backend_framework': ['FastAPI', 'Express', 'Django'],
        'language': ['Python', 'TypeScript', 'JavaScript'],
    },
    'web_ui': {
        'frontend_framework': ['React', 'Vue', 'Svelte'],
        'language': ['TypeScript', 'JavaScript'],
    },
    'cli_tool': {
        'cli_framework': ['Click', 'Typer', 'Commander'],
        'language': ['Python', 'TypeScript', 'Go'],
    },
    'data_processing': {
        'language': ['Python', 'R', 'Julia'],
    },
    'system_tool': {
        'language': ['Rust', 'Go', 'C++'],
    },
    'full_stack': {
        'backend_framework': ['FastAPI', 'Django', 'Express'],
        'frontend_framework': ['React', 'Vue'],
        'language': ['TypeScript', 'Python'],
    },
}


class TechStackStrategy(DecisionStrategy):
    """
    Strategy for selecting languages, frameworks, and libraries autonomously.

    Applies default decision hierarchy:
    1. Best practices (industry standards)
    2. Existing patterns (follow what's in codebase)
    3. Simplicity (choose simplest viable option)
    4. Consistency (match existing code style)
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize TechStackStrategy.

        Args:
            project_root: Optional path to project root for pattern detection
        """
        self.project_root = Path(project_root) if project_root else None
        self._dependencies: Optional[Dict[str, str]] = None
        self._patterns: Optional[Dict] = None

    def get_strategy_name(self) -> str:
        """Return strategy name."""
        return "tech_stack_autonomous"

    def get_strategy_description(self) -> str:
        """Return strategy description."""
        return (
            "Autonomous technology stack selection based on PRD requirements, "
            "best practices, and existing codebase patterns. "
            "Applies hierarchy: best practices → existing patterns → simplicity → consistency"
        )

    def get_supported_decision_types(self) -> List[str]:
        """Return supported decision types."""
        return [
            "tech_stack",
            "language",
            "framework",
            "library",
            "database",
            "frontend",
            "backend",
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
            return False

        if not context.prd_requirements:
            raise ValueError("PRD requirements are required for tech stack selection")

        return True

    def decide(self, context: DecisionContext) -> Decision:
        """
        Select tech stack based on PRD requirements and default decision hierarchy.

        Args:
            context: Decision context with PRD requirements, current state, and options

        Returns:
            Decision with selected tech stack and rationale

        Raises:
            ValueError: If context is invalid
            RuntimeError: If decision cannot be made
        """
        # Validate context
        self.validate_context(context)

        # Detect problem domain from PRD requirements
        domain = self._detect_domain(context.prd_requirements)

        # Detect category if not specified
        category = context.prd_requirements.get('category') or self._detect_category(
            context.prd_requirements, domain
        )

        # Get available options for category
        if category not in TECH_KNOWLEDGE_BASE:
            raise RuntimeError(
                f"Unknown tech category: {category}. "
                f"Available categories: {list(TECH_KNOWLEDGE_BASE.keys())}"
            )

        category_options = TECH_KNOWLEDGE_BASE[category]

        # Build available options list if not provided
        if not context.available_options:
            available_options = [
                {"name": name, **data}
                for name, data in category_options.items()
            ]
        else:
            available_options = context.available_options

        # Load codebase patterns if project root is provided
        if self.project_root:
            self._load_codebase_context()

        # Score each option based on decision hierarchy
        scored_options = []
        for option in available_options:
            tech_name = option.get("name")
            tech_data = category_options.get(tech_name, option)

            score = self.score_option(option, context, tech_data, domain)
            scored_options.append((score, option, tech_data))

        # Sort by score descending
        scored_options.sort(key=lambda x: x[0], reverse=True)

        # Get top choice
        if not scored_options:
            raise RuntimeError("No viable tech stack options found")

        top_score, top_option, top_data = scored_options[0]
        second_score = scored_options[1][0] if len(scored_options) > 1 else 0.0

        # Calculate confidence
        confidence = self.get_confidence(top_score, second_score, len(scored_options))

        # Build rationale
        rationale = self._build_rationale(top_option, top_data, top_score, context, domain)

        # Extract alternatives
        alternatives = [
            opt[1].get("name")
            for opt in scored_options[1:4]
        ]  # Top 3 alternatives

        return Decision(
            choice=top_option.get("name"),
            rationale=rationale,
            confidence=confidence,
            alternatives=alternatives,
            context_snapshot=context.to_dict(),
            decision_type="tech_stack",
            metadata={
                "category": category,
                "domain": domain,
                "score": top_score,
                "scoring_breakdown": self._get_scoring_breakdown(top_option, top_data, context),
            },
        )

    def score_option(
        self,
        option: Dict[str, Any],
        context: DecisionContext,
        tech_data: Dict[str, Any],
        domain: str
    ) -> float:
        """
        Score a tech stack option based on decision hierarchy.

        Scoring criteria (1.0 max):
        - 0.40: Best practices (industry standards)
        - 0.30: Existing patterns (in codebase)
        - 0.20: Simplicity (ease of use)
        - 0.10: Consistency (matches existing stack)

        Args:
            option: Option to score
            context: Decision context
            tech_data: Tech metadata from knowledge base
            domain: Detected problem domain

        Returns:
            Score from 0.0 to 1.0
        """
        score = 0.0

        # 1. Best practices (40 points)
        best_practice_score = self._score_best_practices(option, tech_data, domain)
        score += best_practice_score * 0.40

        # 2. Existing patterns (30 points)
        existing_score = self._score_existing_patterns(option, tech_data)
        score += existing_score * 0.30

        # 3. Simplicity (20 points)
        simplicity_score = self._score_simplicity(option, tech_data)
        score += simplicity_score * 0.20

        # 4. Consistency (10 points)
        consistency_score = self._score_consistency(option, tech_data, context)
        score += consistency_score * 0.10

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

        # Domain detection keywords
        domain_keywords = {
            'web_api': ['api', 'rest', 'endpoint', 'backend', 'server', 'web service'],
            'web_ui': ['ui', 'frontend', 'interface', 'user interface', 'dashboard', 'web app'],
            'cli_tool': ['cli', 'command line', 'terminal', 'command', 'script'],
            'data_processing': ['data', 'processing', 'analysis', 'etl', 'pipeline'],
            'system_tool': ['system', 'performance', 'low-level', 'embedded'],
            'full_stack': ['full stack', 'full-stack', 'end-to-end', 'complete application'],
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
        Detect tech category from PRD requirements and domain.

        Args:
            prd_requirements: PRD requirements
            domain: Detected problem domain

        Returns:
            Detected category name
        """
        # Check if category is explicitly specified
        if 'category' in prd_requirements:
            return prd_requirements['category']

        requirements_text = str(prd_requirements).lower()

        # Category detection keywords
        category_keywords = {
            'language': ['language', 'programming language', 'using python', 'using javascript'],
            'frontend_framework': ['frontend', 'ui', 'react', 'vue', 'component'],
            'backend_framework': ['backend', 'server', 'api framework', 'express', 'django'],
            'database': ['database', 'storage', 'data store', 'postgresql', 'mongodb'],
            'authentication': ['auth', 'authentication', 'login', 'oauth'],
            'cli_framework': ['cli', 'command', 'terminal'],
        }

        # Score each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in requirements_text)
            if score > 0:
                category_scores[category] = score

        # Return highest scoring category or domain-based default
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        # Domain-based defaults
        domain_defaults = {
            'web_api': 'backend_framework',
            'web_ui': 'frontend_framework',
            'cli_tool': 'cli_framework',
            'full_stack': 'language',
        }

        return domain_defaults.get(domain, 'language')

    def _load_codebase_context(self) -> None:
        """Load dependencies and patterns from codebase."""
        if not self.project_root:
            return

        scripts_dir = Path(__file__).parent

        # Load dependencies
        analyze_deps_path = scripts_dir / "analyze_dependencies.py"
        if analyze_deps_path.exists():
            try:
                result = subprocess.run(
                    ["python3", str(analyze_deps_path), str(self.project_root)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    self._dependencies = data.get("existing_deps", {})
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                self._dependencies = {}
        else:
            self._dependencies = {}

        # Load patterns
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
                    self._patterns = json.loads(result.stdout)
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                self._patterns = {}
        else:
            self._patterns = {}

    def _check_existing_tech(self, patterns: List[str]) -> bool:
        """Check if technology exists in codebase."""
        if not self._dependencies:
            return False

        for pattern in patterns:
            for dep in self._dependencies.keys():
                if pattern.lower() in dep.lower():
                    return True

        # Also check in patterns if loaded
        if self._patterns:
            for category, data in self._patterns.items():
                if 'patterns' in data:
                    for detected_pattern in data['patterns'].keys():
                        for pattern in patterns:
                            if pattern.lower() in detected_pattern.lower():
                                return True

        return False

    def _score_best_practices(
        self,
        option: Dict[str, Any],
        tech_data: Dict[str, Any],
        domain: str
    ) -> float:
        """
        Score based on best practices for problem domain.

        Args:
            option: Tech option
            tech_data: Tech metadata
            domain: Problem domain

        Returns:
            Score from 0.0 to 1.0
        """
        tech_name = option.get("name")

        # Get best practices for domain
        domain_practices = DOMAIN_BEST_PRACTICES.get(domain, {})

        # Check if this tech is a best practice for the domain
        for category, best_techs in domain_practices.items():
            if tech_data.get('category') == category:
                if tech_name in best_techs:
                    # Higher score for higher rank
                    rank = best_techs.index(tech_name)
                    return 1.0 - (rank * 0.2)  # 1.0, 0.8, 0.6, etc.

        # Fall back to global best practice rank
        best_practice_rank = tech_data.get('best_practice_rank', 10)
        return max(0.5, 1.0 - (best_practice_rank * 0.1))

    def _score_existing_patterns(self, option: Dict[str, Any], tech_data: Dict[str, Any]) -> float:
        """
        Score based on existing patterns in codebase.

        Args:
            option: Tech option
            tech_data: Tech metadata

        Returns:
            Score from 0.0 to 1.0
        """
        if not self._dependencies and not self._patterns:
            return 0.5  # Neutral if no codebase data

        patterns = tech_data.get('detect_patterns', [])

        if self._check_existing_tech(patterns):
            return 1.0  # Already in codebase

        # Check ecosystem compatibility
        ecosystem = tech_data.get('ecosystem', 'any')
        if self._dependencies:
            if ecosystem == 'nodejs':
                if any(dep.startswith(('react', 'vue', 'express', 'next'))
                       for dep in self._dependencies):
                    return 0.75  # Compatible ecosystem
            elif ecosystem == 'python':
                if any(dep.startswith(('django', 'flask', 'fastapi', 'sqlalchemy'))
                       for dep in self._dependencies):
                    return 0.75

        return 0.5  # Not incompatible, but not existing either

    def _score_simplicity(self, option: Dict[str, Any], tech_data: Dict[str, Any]) -> float:
        """
        Score based on simplicity and ease of use.

        Args:
            option: Tech option
            tech_data: Tech metadata

        Returns:
            Score from 0.0 to 1.0
        """
        tech_name = option.get("name")

        # Simpler technologies get higher scores
        simple_techs = {
            'Express': 1.0,
            'Flask': 1.0,
            'SQLite': 1.0,
            'Click': 1.0,
            'Python': 0.9,
            'JavaScript': 0.9,
            'React': 0.8,
        }

        return simple_techs.get(tech_name, 0.7)

    def _score_consistency(
        self,
        option: Dict[str, Any],
        tech_data: Dict[str, Any],
        context: DecisionContext
    ) -> float:
        """
        Score based on consistency with existing code style.

        Args:
            option: Tech option
            tech_data: Tech metadata
            context: Decision context

        Returns:
            Score from 0.0 to 1.0
        """
        # Check if current state has language/framework info
        current_lang = context.current_state.get('language', '').lower()
        current_framework = context.current_state.get('framework', '').lower()

        tech_name = option.get("name", "")
        tech_ecosystem = tech_data.get('ecosystem', '')

        # Language consistency
        if current_lang:
            if tech_ecosystem == 'python' and current_lang in ['python', 'py']:
                return 1.0
            if tech_ecosystem == 'nodejs' and current_lang in ['javascript', 'js', 'typescript', 'ts']:
                return 1.0
            if tech_ecosystem == 'go' and current_lang == 'go':
                return 1.0
            if tech_ecosystem == 'rust' and current_lang == 'rust':
                return 1.0

        # Framework consistency
        if current_framework:
            if current_framework in tech_name.lower():
                return 1.0

        return 0.5  # Neutral if no consistency info

    def _build_rationale(
        self,
        option: Dict[str, Any],
        tech_data: Dict[str, Any],
        score: float,
        context: DecisionContext,
        domain: str
    ) -> str:
        """
        Build human-readable rationale for decision.

        Args:
            option: Selected option
            tech_data: Tech metadata
            score: Final score
            context: Decision context
            domain: Problem domain

        Returns:
            Rationale string
        """
        tech_name = option.get("name")
        parts = [f"Selected {tech_name} for {domain} development."]

        # Add best practices rationale
        domain_practices = DOMAIN_BEST_PRACTICES.get(domain, {})
        for category, best_techs in domain_practices.items():
            if tech_data.get('category') == category and tech_name in best_techs:
                parts.append(
                    f"It's a best practice for {domain} projects "
                    f"(rank {best_techs.index(tech_name) + 1})"
                )
                break

        # Add existing patterns rationale
        if self._dependencies and self._check_existing_tech(tech_data.get('detect_patterns', [])):
            parts.append("Already used in the codebase, ensuring consistency.")

        # Add simplicity rationale
        simplicity_score = self._score_simplicity(option, tech_data)
        if simplicity_score >= 0.9:
            parts.append("Chosen for its simplicity and ease of use.")

        # Add maturity rationale
        maturity = tech_data.get('maturity_score', 0)
        if maturity >= 25:
            parts.append("Mature ecosystem with strong community support.")

        return " ".join(parts)

    def _get_scoring_breakdown(
        self,
        option: Dict[str, Any],
        tech_data: Dict[str, Any],
        context: DecisionContext
    ) -> Dict[str, float]:
        """
        Get detailed scoring breakdown for an option.

        Args:
            option: Tech option
            tech_data: Tech metadata
            context: Decision context

        Returns:
            Dictionary with scoring breakdown
        """
        domain = self._detect_domain(context.prd_requirements)

        return {
            "best_practices": self._score_best_practices(option, tech_data, domain),
            "existing_patterns": self._score_existing_patterns(option, tech_data),
            "simplicity": self._score_simplicity(option, tech_data),
            "consistency": self._score_consistency(option, tech_data, context),
        }
