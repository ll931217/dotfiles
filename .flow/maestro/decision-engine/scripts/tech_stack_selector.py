#!/usr/bin/env python3
"""
Tech Stack Selection Algorithm

Analyzes codebase for autonomous technology stack decisions.
Integrates dependency scanning, pattern detection, and scoring rubric.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class TechOption:
    """Represents a technology option with its metadata."""
    name: str
    category: str
    existing_usage_score: int
    maturity_score: int
    community_score: int
    fit_score: int
    total_score: int
    confidence: str
    rationale: List[str]
    alternatives: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary, replacing rationale list with joined string."""
        data = asdict(self)
        data['rationale'] = '; '.join(self.rationale)
        return data


# Technology knowledge base with predefined scoring
TECH_KNOWLEDGE_BASE = {
    'authentication': {
        'Passport.js': {
            'category': 'authentication',
            'maturity_score': 25,  # 20K+ stars
            'community_score': 15,  # Active, frequent updates
            'fit_score': 20,  # Perfect for OAuth
            'alternatives': ['Auth.js', 'Auth0', 'custom JWT'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['passport', 'passport-', 'passport-local'],
        },
        'Auth.js': {
            'category': 'authentication',
            'maturity_score': 20,  # Growing popularity
            'community_score': 12,  # Moderate community
            'fit_score': 20,  # Modern web OAuth
            'alternatives': ['Passport.js', 'Auth0', 'custom JWT'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['next-auth', '@auth/core', 'authjs'],
        },
        'Auth0': {
            'category': 'authentication',
            'maturity_score': 25,  # Mature service
            'community_score': 15,  # Active
            'fit_score': 15,  # Third-party, cost involved
            'alternatives': ['Passport.js', 'Auth.js', 'custom implementation'],
            'ecosystem': 'any',
            'detect_patterns': ['auth0', '@auth0/'],
        },
        'custom JWT': {
            'category': 'authentication',
            'maturity_score': 20,  # Standard approach
            'community_score': 10,  # Well documented
            'fit_score': 15,  # Requires implementation
            'alternatives': ['Passport.js', 'Auth.js', 'Auth0'],
            'ecosystem': 'any',
            'detect_patterns': ['jsonwebtoken', 'jwt', 'jwt.verify'],
        },
    },
    'database': {
        'PostgreSQL': {
            'category': 'database',
            'maturity_score': 25,  # 10K+ stars, mature
            'community_score': 15,  # Very active
            'fit_score': 20,  # Relational, feature-rich
            'alternatives': ['MySQL', 'MongoDB', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['pg', 'postgres', 'postgresql', 'psycopg'],
        },
        'MySQL': {
            'category': 'database',
            'maturity_score': 25,  # Very mature
            'community_score': 15,  # Active
            'fit_score': 20,  # Relational
            'alternatives': ['PostgreSQL', 'MongoDB', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['mysql', 'mysql2'],
        },
        'MongoDB': {
            'category': 'database',
            'maturity_score': 25,  # Popular
            'community_score': 15,  # Active
            'fit_score': 18,  # Document, flexible
            'alternatives': ['PostgreSQL', 'Redis', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['mongodb', 'mongoose', 'mongo'],
        },
        'Redis': {
            'category': 'database',
            'maturity_score': 25,  # Popular
            'community_score': 15,  # Active
            'fit_score': 20,  # Perfect for sessions/cache
            'alternatives': ['PostgreSQL', 'Memcached', 'SQLite'],
            'ecosystem': 'any',
            'detect_patterns': ['redis', '@redis/', 'ioredis'],
        },
        'SQLite': {
            'category': 'database',
            'maturity_score': 20,  # Mature but embedded
            'community_score': 10,  # Stable, less active
            'fit_score': 12,  # Limited scalability
            'alternatives': ['PostgreSQL', 'MongoDB', 'Redis'],
            'ecosystem': 'any',
            'detect_patterns': ['sqlite', 'sqlite3', 'better-sqlite3'],
        },
    },
    'frontend_framework': {
        'React': {
            'category': 'frontend_framework',
            'maturity_score': 25,  # 200K+ stars
            'community_score': 15,  # Very active
            'fit_score': 20,  # Flexible, ecosystem
            'alternatives': ['Vue', 'Svelte', 'Vanilla'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['react', 'react-dom', '@react/', 'useState', 'useEffect'],
        },
        'Vue': {
            'category': 'frontend_framework',
            'maturity_score': 25,  # Popular
            'community_score': 15,  # Active
            'fit_score': 18,  # Simpler learning curve
            'alternatives': ['React', 'Svelte', 'Vanilla'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['vue', '@vue/', 'Vue.', 'v-if', 'v-for'],
        },
        'Svelte': {
            'category': 'frontend_framework',
            'maturity_score': 20,  # Growing
            'community_score': 12,  # Moderate
            'fit_score': 18,  # Performance-focused
            'alternatives': ['React', 'Vue', 'Vanilla'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['svelte', '@svelte/', 'svelte-'],
        },
    },
    'backend_framework': {
        'Express': {
            'category': 'backend_framework',
            'maturity_score': 25,  # 60K+ stars
            'community_score': 15,  # Very active
            'fit_score': 20,  # Flexible, minimal
            'alternatives': ['FastAPI', 'Django', 'Go stdlib'],
            'ecosystem': 'nodejs',
            'detect_patterns': ['express', 'express()', 'app.use', 'app.get'],
        },
        'FastAPI': {
            'category': 'backend_framework',
            'maturity_score': 20,  # Growing fast
            'community_score': 12,  # Active
            'fit_score': 20,  # Modern, async
            'alternatives': ['Express', 'Django', 'Flask'],
            'ecosystem': 'python',
            'detect_patterns': ['fastapi', 'FastAPI', '@app.', 'APIRouter'],
        },
        'Django': {
            'category': 'backend_framework',
            'maturity_score': 25,  # 70K+ stars
            'community_score': 15,  # Very active
            'fit_score': 18,  # Full-featured
            'alternatives': ['FastAPI', 'Flask', 'Express'],
            'ecosystem': 'python',
            'detect_patterns': ['django', 'Django', 'from django', 'models.Model'],
        },
        'Flask': {
            'category': 'backend_framework',
            'maturity_score': 25,  # 65K+ stars
            'community_score': 15,  # Active
            'fit_score': 18,  # Microframework
            'alternatives': ['Django', 'FastAPI', 'Express'],
            'ecosystem': 'python',
            'detect_patterns': ['flask', 'Flask', 'app.route', 'Flask(__name__)'],
        },
    },
}


class TechStackSelector:
    """Main tech stack selection engine."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependencies = self._load_dependencies()
        self.patterns = self._load_patterns()

    def _load_dependencies(self) -> Dict[str, str]:
        """Load existing dependencies from the project."""
        # Import the analyze_dependencies module
        scripts_dir = Path(__file__).parent
        analyze_deps_path = scripts_dir / "analyze_dependencies.py"

        if not analyze_deps_path.exists():
            return {}

        # Run the analyze_dependencies script
        try:
            result = subprocess.run(
                ["python3", str(analyze_deps_path), str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("existing_deps", {})
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return {}

    def _load_patterns(self) -> Dict:
        """Load detected architectural patterns."""
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

    def _check_existing_tech(self, patterns: List[str]) -> bool:
        """Check if any of the given patterns exist in dependencies."""
        for pattern in patterns:
            # Check in dependencies
            for dep in self.dependencies.keys():
                if pattern.lower() in dep.lower():
                    return True

            # Check in codebase patterns
            for category, data in self.patterns.items():
                if 'patterns' in data:
                    for detected_pattern in data['patterns'].keys():
                        if pattern.lower() in detected_pattern.lower():
                            return True

        return False

    def _score_existing_usage(self, tech_name: str, tech_data: Dict) -> int:
        """Score existing usage (40 points max)."""
        patterns = tech_data.get('detect_patterns', [])

        if self._check_existing_tech(patterns):
            return 40  # Already in codebase - full score

        # Check ecosystem compatibility
        ecosystem = tech_data.get('ecosystem', 'any')
        if ecosystem == 'nodejs':
            if any(dep.startswith(('react', 'vue', 'express', 'next')) for dep in self.dependencies):
                return 30  # Compatible with existing stack
        elif ecosystem == 'python':
            if any(dep.startswith(('django', 'flask', 'fastapi', 'sqlalchemy')) for dep in self.dependencies):
                return 30

        # Check if it's a standard choice
        standard_choices = ['Express', 'React', 'PostgreSQL', 'Passport.js', 'Django']
        if tech_name in standard_choices:
            return 10  # Standard choice but new to project

        return 0  # New and experimental

    def _select_best_option(self, options: List[TechOption]) -> TechOption:
        """Select the best option from scored candidates."""
        # Sort by total score
        options.sort(key=lambda x: x.total_score, reverse=True)

        # Determine confidence level
        top_score = options[0].total_score
        if top_score >= 90:
            options[0].confidence = "high"
        elif top_score >= 70:
            options[0].confidence = "medium"
        else:
            options[0].confidence = "low"

        return options[0]

    def select_tech_stack(self, requirement: str, category: Optional[str] = None) -> Dict:
        """
        Main entry point for tech stack selection.

        Args:
            requirement: Natural language requirement (e.g., "Need OAuth library for authentication")
            category: Specific category to search (optional, auto-detected if not provided)

        Returns:
            Structured decision with rationale
        """
        # Auto-detect category if not provided
        if not category:
            category = self._detect_category_from_requirement(requirement)

        # Normalize category
        category = category.lower().replace('-', '_').replace(' ', '_')

        # Get options for category
        if category not in TECH_KNOWLEDGE_BASE:
            return {
                "error": f"Unknown category: {category}",
                "available_categories": list(TECH_KNOWLEDGE_BASE.keys()),
            }

        category_options = TECH_KNOWLEDGE_BASE[category]

        # Score each option
        scored_options = []
        for tech_name, tech_data in category_options.items():
            existing_score = self._score_existing_usage(tech_name, tech_data)
            maturity_score = tech_data.get('maturity_score', 10)
            community_score = tech_data.get('community_score', 10)
            fit_score = tech_data.get('fit_score', 10)

            total_score = existing_score + maturity_score + community_score + fit_score

            # Build rationale
            rationale = []
            if existing_score == 40:
                rationale.append("Already in codebase")
            elif existing_score == 30:
                rationale.append("Compatible with existing stack")
            elif existing_score == 10:
                rationale.append("Standard choice")

            if maturity_score >= 25:
                rationale.append("Mature ecosystem (10K+ stars/1M+ downloads)")
            elif maturity_score >= 20:
                rationale.append("Strong community support")

            if fit_score >= 20:
                rationale.append("Perfect fit for requirements")
            elif fit_score >= 15:
                rationale.append("Good fit with minor workarounds")

            option = TechOption(
                name=tech_name,
                category=category,
                existing_usage_score=existing_score,
                maturity_score=maturity_score,
                community_score=community_score,
                fit_score=fit_score,
                total_score=total_score,
                confidence="",  # Will be set by _select_best_option
                rationale=rationale,
                alternatives=tech_data.get('alternatives', []),
            )
            scored_options.append(option)

        # Select best option
        best_option = self._select_best_option(scored_options)

        # Build output
        return {
            "decision_type": "tech_stack",
            "input": requirement,
            "category": category,
            "output": {
                "decision": best_option.name,
                "rationale": best_option.to_dict()['rationale'],
                "confidence": best_option.confidence,
                "alternatives": best_option.alternatives,
                "context": {
                    "existing_dependencies": list(self.dependencies.keys())[:20],  # Limit output
                    "dependency_count": len(self.dependencies),
                    "detected_patterns": list(self.patterns.keys()),
                    "scoring_breakdown": {
                        "existing_usage": best_option.existing_usage_score,
                        "maturity": best_option.maturity_score,
                        "community": best_option.community_score,
                        "fit": best_option.fit_score,
                        "total": best_option.total_score,
                    },
                },
                "all_options": [opt.to_dict() for opt in scored_options],
            },
        }

    def _detect_category_from_requirement(self, requirement: str) -> str:
        """Auto-detect category from natural language requirement."""
        requirement_lower = requirement.lower()

        # Keywords for each category - ordered by specificity
        # More specific keywords first
        category_keywords = {
            'database': ['session storage', 'data store', 'persistent storage', 'database', 'postgresql', 'mysql', 'mongodb', 'sqlite', 'redis', 'db ', 'sql', 'nosql', 'orm', 'query', 'migration'],
            'authentication': ['oauth', 'login', 'authentication', 'jwt', 'passport', 'auth ', 'token', 'user session'],
            'frontend_framework': ['frontend', 'ui framework', 'react', 'vue', 'svelte', 'component', 'jsx', 'tsx'],
            'backend_framework': ['backend', 'api framework', 'server', 'express', 'django', 'flask', 'fastapi', 'web framework'],
        }

        # Score each category based on keyword matches
        # Use weighted scoring: exact phrase matches get higher weight
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in requirement_lower:
                    # Multi-word phrases get higher weight
                    weight = len(keyword.split())
                    score += weight

            if score > 0:
                category_scores[category] = score

        # Return highest scoring category, or default to authentication
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        # Default fallback
        return 'authentication'


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Tech stack selection algorithm for autonomous technology decisions"
    )
    parser.add_argument("project_root", help="Path to project root directory")
    parser.add_argument("requirement", help="Technology requirement (e.g., 'Need OAuth library')")
    parser.add_argument(
        "--category",
        help="Technology category (authentication, database, frontend_framework, backend_framework)",
        default=None,
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "pretty"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    # Run selection
    selector = TechStackSelector(args.project_root)
    result = selector.select_tech_stack(args.requirement, args.category)

    # Output
    if args.output_format == "pretty":
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
