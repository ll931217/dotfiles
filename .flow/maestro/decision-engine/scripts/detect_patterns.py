#!/usr/bin/env python3
"""
Detect architectural patterns in the codebase.

Uses grep to search for common patterns like middleware, service layers,
repositories, factories, etc.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


PATTERNS = {
    "middleware": [
        "middleware",
        "app.use\\(",
        "@Middleware",
        "pipe\\(",
    ],
    "service-layer": [
        "service",
        "Service",
        ".service.ts",
        ".service.js",
    ],
    "repository": [
        "repository",
        "Repository",
        ".repo.ts",
        ".repo.js",
        "DAO",
    ],
    "factory": [
        "Factory",
        "create",
        "build",
        "newInstance",
    ],
    "singleton": [
        "getInstance",
        "_instance",
        "self._instance",
        "static instance",
    ],
    "observer": [
        "subscribe",
        "addEventListener",
        "on\\(",
        "emit\\(",
    ],
    "strategy": [
        "Strategy",
        "strategies/",
        ".strategy.",
    ],
    "decorator": [
        "@",
        "decorate",
        "Decorator",
        "__call__",
    ],
}


def grep_pattern(project_root: Path, pattern: str) -> int:
    """Count occurrences of a pattern using grep."""
    try:
        result = subprocess.run(
            ["grep", "-r", "-c", pattern, str(project_root)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Count non-empty matches
            matches = [line for line in result.stdout.split("\n") if line.strip()]
            return len(matches)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return 0


def detect_patterns_in_project(project_root: str, pattern_type: Optional[str] = None) -> Dict:
    """Detect patterns in the codebase."""
    root = Path(project_root)

    if not root.exists():
        return {"error": f"Project root not found: {project_root}"}

    patterns_to_check = (
        {pattern_type: PATTERNS[pattern_type]} if pattern_type else PATTERNS
    )

    results = {}
    for pattern_category, search_patterns in patterns_to_check.items():
        scores = {}
        for search_pattern in search_patterns:
            count = grep_pattern(root, search_pattern)
            if count > 0:
                scores[search_pattern] = count

        if scores:
            results[pattern_category] = {
                "total_matches": sum(scores.values()),
                "patterns": scores,
            }

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect architectural patterns")
    parser.add_argument("project_root", help="Path to project root directory")
    parser.add_argument(
        "pattern_type",
        nargs="?",
        help="Pattern type to detect (middleware, service-layer, repository, etc.)",
    )
    args = parser.parse_args()

    result = detect_patterns_in_project(args.project_root, args.pattern_type)
    print(json.dumps(result, indent=2))
