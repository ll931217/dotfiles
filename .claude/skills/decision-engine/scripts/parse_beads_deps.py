#!/usr/bin/env python3
"""
Parse beads dependency graph for task ordering.

Extracts dependency information from beads issues to build
a dependency graph for topological sorting and parallel execution detection.
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Set, Tuple


def get_beads_issues() -> List[Dict]:
    """Get all issues from beads database."""
    try:
        result = subprocess.run(
            ["bd", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def get_issue_dependencies(issue_id: str) -> Dict:
    """Get dependency information for a specific issue."""
    try:
        result = subprocess.run(
            ["bd", "show", "--json", issue_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "id": data.get("id"),
                "title": data.get("title"),
                "status": data.get("status"),
                "type": data.get("type"),
                "priority": data.get("priority"),
                "blocks": data.get("blocks", []),
                "depends_on": data.get("depends_on", []),
                "parent": data.get("parent"),
                "children": data.get("children", []),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def build_dependency_graph() -> Dict:
    """Build complete dependency graph from beads."""
    issues = get_beads_issues()

    graph = {
        "nodes": [],
        "edges": [],
        "foundational": [],  # Tasks with no dependencies
        "terminal": [],  # Tasks that nothing depends on
    }

    # Build adjacency list
    adj = {}
    reverse_adj = {}

    for issue in issues:
        issue_id = issue.get("id")
        if not issue_id or issue.get("status") == "closed":
            continue

        graph["nodes"].append(issue_id)
        depends_on = issue.get("depends_on", [])
        adj[issue_id] = depends_on

        # Track reverse dependencies (what depends on this)
        for dep in depends_on:
            if dep not in reverse_adj:
                reverse_adj[dep] = []
            reverse_adj[dep].append(issue_id)

    # Build edges
    for issue_id, deps in adj.items():
        for dep in deps:
            graph["edges"].append((dep, issue_id))

    # Find foundational (no deps) and terminal (nothing depends on it)
    all_ids = set(graph["nodes"])
    has_deps = set()
    for _, dep_id in graph["edges"]:
        has_deps.add(dep_id)

    graph["foundational"] = list(all_ids - has_deps)

    is_depended_on = set()
    for dep_id, _ in graph["edges"]:
        is_depended_on.add(dep_id)

    graph["terminal"] = list(all_ids - is_depended_on)

    # Detect parallel groups (tasks with same dependencies)
    parallel_groups = {}
    for issue_id in adj:
        deps_tuple = tuple(sorted(adj[issue_id]))
        if deps_tuple not in parallel_groups:
            parallel_groups[deps_tuple] = []
        parallel_groups[deps_tuple].append(issue_id)

    graph["parallel_groups"] = {
        f"group_{i}": tasks for i, tasks in enumerate(parallel_groups.values()) if len(tasks) > 1
    }

    return graph


def topological_sort(graph: Dict) -> List:
    """Perform topological sort on dependency graph."""
    in_degree = {}
    adj = {}

    # Initialize
    for node in graph["nodes"]:
        in_degree[node] = 0
        adj[node] = []

    # Build adjacency and in-degree
    for src, dst in graph["edges"]:
        adj[src].append(dst)
        in_degree[dst] += 1

    # Kahn's algorithm
    queue = [node for node in graph["nodes"] if in_degree[node] == 0]
    result = []

    while queue:
        node = queue.pop(0)
        result.append(node)

        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(graph["nodes"]):
        # Cycle detected
        return result  # Partial result

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse beads dependency graph")
    args = parser.parse_args()

    graph = build_dependency_graph()

    if graph["nodes"]:
        ordered = topological_sort(graph)
        graph["execution_order"] = ordered

    print(json.dumps(graph, indent=2))
