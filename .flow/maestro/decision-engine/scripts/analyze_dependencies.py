#!/usr/bin/env python3
"""
Analyze project dependencies to inform technology stack decisions.

Scans for common dependency files (package.json, requirements.txt, go.mod, etc.)
and extracts existing packages/libraries to inform decision-making.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


def detect_package_managers(project_root: Path) -> List[str]:
    """Detect which package managers are used in the project."""
    managers = []
    checks = [
        ("npm", "package.json"),
        ("yarn", "yarn.lock"),
        ("pip", "requirements.txt"),
        ("pip", "pyproject.toml"),
        ("go", "go.mod"),
        ("cargo", "Cargo.toml"),
        ("composer", "composer.json"),
        ("maven", "pom.xml"),
        ("gradle", "build.gradle"),
    ]

    for manager, file in checks:
        if (project_root / file).exists():
            managers.append(manager)

    return managers


def parse_package_json(project_root: Path) -> Dict[str, str]:
    """Parse package.json for dependencies."""
    package_json = project_root / "package.json"
    if not package_json.exists():
        return {}

    with open(package_json) as f:
        data = json.load(f)

    deps = {}
    for key in ["dependencies", "devDependencies"]:
        if key in data:
            deps.update(data[key])

    return deps


def parse_requirements_txt(project_root: Path) -> Dict[str, str]:
    """Parse requirements.txt for dependencies."""
    req_file = project_root / "requirements.txt"
    if not req_file.exists():
        return {}

    deps = {}
    with open(req_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Parse "package==version" or "package>=version"
                parts = line.split("==") if "==" in line else line.split(">=")
                if len(parts) == 2:
                    deps[parts[0].strip()] = parts[1].strip()
                elif len(parts) == 1:
                    deps[parts[0].strip()] = "any"

    return deps


def parse_go_mod(project_root: Path) -> Dict[str, str]:
    """Parse go.mod for dependencies."""
    go_mod = project_root / "go.mod"
    if not go_mod.exists():
        return {}

    deps = {}
    with open(go_mod) as f:
        in_require = False
        for line in f:
            line = line.strip()
            if line == "require (":
                in_require = True
                continue
            if in_require and line == ")":
                in_require = False
                continue
            if in_require or line.startswith("require "):
                parts = line.split()
                if len(parts) >= 2:
                    deps[parts[1]] = parts[2] if len(parts) > 2 else "any"

    return deps


def analyze_project(project_root: str) -> Dict:
    """Main analysis function."""
    root = Path(project_root)

    if not root.exists():
        return {"error": f"Project root not found: {project_root}"}

    # Detect package managers
    managers = detect_package_managers(root)

    # Parse dependencies
    all_deps = {}
    if "npm" in managers or "yarn" in managers:
        all_deps.update(parse_package_json(root))
    if "pip" in managers:
        all_deps.update(parse_requirements_txt(root))
    if "go" in managers:
        all_deps.update(parse_go_mod(root))

    return {
        "package_managers": managers,
        "existing_deps": all_deps,
        "dependency_count": len(all_deps),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze project dependencies")
    parser.add_argument("project_root", help="Path to project root directory")
    args = parser.parse_args()

    result = analyze_project(args.project_root)
    print(json.dumps(result, indent=2))
