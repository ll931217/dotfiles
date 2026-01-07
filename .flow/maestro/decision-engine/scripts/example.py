#!/usr/bin/env python3
"""
Example usage of the Architecture Pattern Matcher

This script demonstrates how to use the architecture_pattern_matcher.py
to recommend architectural patterns based on feature descriptions.
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from architecture_pattern_matcher import ArchitecturePatternMatcher


def main():
    """Run example pattern matching scenarios."""

    # Example 1: Simple validation feature (low complexity)
    print("=" * 70)
    print("Example 1: Simple Password Validation")
    print("=" * 70)
    print("Feature: Implement simple password validation")
    print()

    matcher = ArchitecturePatternMatcher("/tmp/project")
    result = matcher.match_pattern("Implement simple password validation")
    print(json.dumps(result, indent=2))
    print()

    # Example 2: User registration with business logic (medium complexity)
    print("=" * 70)
    print("Example 2: User Registration Service")
    print("=" * 70)
    print("Feature: Implement user registration with email verification")
    print()

    result = matcher.match_pattern("Implement user registration with email verification")
    print(json.dumps(result, indent=2))
    print()

    # Example 3: Database access layer (medium complexity)
    print("=" * 70)
    print("Example 3: Data Access Layer")
    print("=" * 70)
    print("Feature: Create database access layer for user CRUD operations")
    print()

    result = matcher.match_pattern("Create database access layer for user CRUD operations")
    print(json.dumps(result, indent=2))
    print()

    # Example 4: API rate limiting middleware (medium complexity)
    print("=" * 70)
    print("Example 4: API Rate Limiting Middleware")
    print("=" * 70)
    print("Feature: Implement API rate limiting middleware")
    print()

    result = matcher.match_pattern("Implement API rate limiting middleware")
    print(json.dumps(result, indent=2))
    print()

    # Example 5: Complex workflow orchestration (high complexity)
    print("=" * 70)
    print("Example 5: Complex Workflow Orchestration")
    print("=" * 70)
    print("Feature: Orchestrate order processing workflow across multiple services")
    print()

    result = matcher.match_pattern("Orchestrate order processing workflow across multiple services")
    print(json.dumps(result, indent=2))
    print()

    # Example 6: With complexity override
    print("=" * 70)
    print("Example 6: With Complexity Override")
    print("=" * 70)
    print("Feature: Implement authentication (complexity overridden to 'high')")
    print()

    result = matcher.match_pattern("Implement authentication", complexity='high')
    print(json.dumps(result, indent=2))
    print()


if __name__ == "__main__":
    main()
