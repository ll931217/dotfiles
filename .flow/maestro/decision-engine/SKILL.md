---
name: decision-engine
description: Autonomous decision-making engine for technical choices in technology selection, architecture patterns, and task ordering. Use when Maestro orchestrator needs to make decisions without human input for choosing libraries/frameworks based on existing codebase, selecting architectural patterns based on complexity and requirements, and optimizing task execution order based on dependency analysis. Analyzes codebase context, applies scoring rubrics, and returns structured decisions with rationale.
---

# Decision Engine

Autonomous decision-making for technical choices during implementation.

## Quick Start

```bash
# Technology stack selection
Decision: tech_stack("user authentication")
→ Analyzes codebase → Recommends Passport.js + PostgreSQL

# Architecture pattern selection
Decision: architecture_pattern("API rate limiting")
→ Analyzes complexity → Recommends middleware pattern

# Task ordering
Decision: task_ordering([taskA, taskB, taskC])
→ Analyzes dependencies → Recommends execution order
```

## Decision Types

### 1. Technology Stack Selection

Analyzes existing dependencies and codebase patterns to recommend technologies.

**Process:**
1. Scan existing dependency files (package.json, requirements.txt, go.mod, etc.)
2. Search codebase for existing implementations
3. Score options using rubric (see [references/tech-stack-rubric.md](references/tech-stack-rubric.md))
4. Return decision with rationale

**Usage:**
```
Input: "Need OAuth library for authentication"
Output: {
  "decision": "Passport.js",
  "rationale": "Already in package.json, mature ecosystem, 20K+ stars",
  "confidence": "high",
  "alternatives": ["auth0", "custom implementation"]
}
```

### 2. Architecture Pattern Selection

Selects appropriate architectural patterns based on complexity and requirements.

**Process:**
1. Analyze feature complexity (simple/medium/complex)
2. Check existing patterns in codebase
3. Match to pattern using rubric (see [references/architecture-patterns.md](references/architecture-patterns.md))
4. Return recommendation with rationale

**Usage:**
```
Input: "Implement file upload feature"
Output: {
  "pattern": "Service layer pattern",
  "rationale": "Medium complexity, existing service layer, separation of concerns",
  "confidence": "high"
}
```

### 3. Task Ordering with Dependency Resolution

Optimizes task execution order based on dependency analysis.

**Process:**
1. Parse beads dependency graph
2. Identify foundational tasks (no dependencies)
3. Detect parallel execution opportunities
4. Apply ordering strategies (see [references/task-ordering-strategies.md](references/task-ordering-strategies.md))
5. Return optimized sequence

**Usage:**
```
Input: ["implement schema", "create API", "write tests", "build UI"]
Output: {
  "sequence": [
    "implement schema",  # foundational
    ["create API", "build UI"],  # parallel group
    "write tests"  # depends on API
  ],
  "rationale": "Schema is foundational, API and UI can run in parallel"
}
```

## Scripts

### `scripts/analyze_dependencies.py`

Scans project for existing dependencies to inform tech decisions.

```bash
# Usage
python3 scripts/analyze_dependencies.py <project-root>

# Output
{
  "package_managers": ["npm", "pip"],
  "existing_deps": {
    "express": "^4.18.0",
    "passport": "^0.6.0"
  }
}
```

### `scripts/detect_patterns.py`

Grep codebase for existing architectural patterns.

```bash
# Usage
python3 scripts/detect_patterns.py <project-root> <pattern-type>

# Pattern types: middleware, service-layer, repository, factory, etc.
```

### `scripts/parse_beads_deps.py`

Parses beads dependency graph for task ordering.

```bash
# Usage
python3 scripts/parse_beads_deps.py

# Output: Dependency graph ready for topological sort
```

## Reference Documentation

- **[tech-stack-rubric.md](references/tech-stack-rubric.md)** - Scoring criteria for technology decisions
- **[architecture-patterns.md](references/architecture-patterns.md)** - Pattern descriptions and usage guidelines
- **[task-ordering-strategies.md](references/task-ordering-strategies.md)** - Dependency resolution algorithms

## Output Schema

All decisions follow this structure:

```json
{
  "decision_type": "tech_stack|architecture|task_ordering",
  "input": "<user request>",
  "output": {
    "decision": "<recommended choice>",
    "rationale": "<explanation>",
    "confidence": "high|medium|low",
    "alternatives": ["<option1>", "<option2>"],
    "context": {
      "existing_patterns": ["<found in codebase>"],
      "complexity": "simple|medium|complex",
      "dependencies": ["<related choices>"]
    }
  }
}
```

## Integration with Maestro

The decision engine is invoked by Maestro during:

1. **Planning phase** - Before generating tasks, analyze codebase for architectural context
2. **Task execution** - Before each task, make technical decisions
3. **Dependency resolution** - When generating task order

Example integration:
```python
# In Maestro orchestrator
decision = query_decision_engine("Need database for user sessions")
tech_choice = decision["output"]["decision"]
# Use tech_choice in task generation
```

## Principles

1. **Prefer existing** - Favor technologies already in the codebase
2. **Match patterns** - Follow established architectural patterns
3. **Enable parallelism** - Maximize independent task execution
4. **Document rationale** - All decisions include reasoning
5. **Provide alternatives** - Always list fallback options
