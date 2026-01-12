# Task Ordering Strategies

Algorithms and heuristics for optimizing task execution order based on dependency analysis.

## Overview

Task ordering optimizes execution sequence to:
- **Minimize total time** - Enable parallel execution where possible
- **Respect dependencies** - Execute tasks only after prerequisites complete
- **Reduce risk** - Execute high-risk tasks early for faster feedback
- **Improve flow** - Group related tasks for better context

## Dependency Graph Analysis

Parse beads dependency graph to identify:

1. **Foundational tasks** - No dependencies, can start immediately
2. **Sequential tasks** - Must wait for prerequisites
3. **Parallel groups** - Independent tasks that can execute simultaneously
4. **Critical path** - Longest dependency chain, determines minimum duration

## Ordering Strategies

### Strategy 1: Topological Sort (Default)

**Description:** Execute tasks in dependency order, parallelize where safe.

**Algorithm:**
1. Identify all foundational tasks (no dependencies)
2. Execute foundational tasks in parallel
3. Remove completed tasks from graph
4. Repeat until all tasks complete

**Example:**
```
Tasks: A (no deps), B (depends on A), C (no deps), D (depends on A), E (depends on B, D)

Group 1: [A, C] - parallel
Group 2: [B, D] - parallel (both depend on A)
Group 3: [E] - sequential (depends on B and D)
```

**Use when:** Standard implementation, no special priorities

### Strategy 2: Risk-First Ordering

**Description:** Execute high-risk tasks before low-risk tasks.

**Risk Categories:**
- **Critical (P0)** - Security, core architecture, blocking issues
- **High (P1)** - Important functionality, urgent bugs
- **Normal (P2)** - Standard features
- **Low (P3)** - Nice-to-have enhancements
- **Lowest (P4)** - Backlog items

**Algorithm:**
1. Sort tasks by priority (P0 → P4)
2. Within each priority, apply topological sort
3. Execute higher priority tasks first

**Example:**
```
Tasks:
- A: P1, no deps
- B: P0, depends on C
- C: P0, no deps
- D: P2, no deps

Order: [C] (P0 foundational) → [B] (P0 depends on C) → [A, D] (P1/P2 parallel)
```

**Use when:** High-risk tasks, tight deadline, critical features

### Strategy 3: Foundational-First Ordering

**Description:** Execute foundational tasks before dependent tasks.

**Foundation Types:**
- Database schema
- Core services
- API endpoints
- Base components

**Algorithm:**
1. Identify tasks that create foundational elements
2. Execute foundational tasks first
3. Execute tasks that depend on foundations
4. Execute independent tasks in parallel

**Example:**
```
Tasks:
- A: Create schema (foundational)
- B: Create API (depends on schema)
- C: Create UI (independent)
- D: Write tests (depends on API and UI)

Order: [A] → [B, C] (parallel) → [D]
```

**Use when:** Clear foundational elements, standard implementation

### Strategy 4: Parallel-Maximizing Ordering

**Description:** Maximize parallel execution to reduce total time.

**Algorithm:**
1. Build dependency graph
2. Find largest set of independent tasks
3. Execute in parallel
4. Repeat until complete

**Example:**
```
Tasks:
- A: Create schema
- B: Create auth API (depends on A)
- C: Create user API (depends on A)
- D: Create auth UI (independent)
- E: Create user UI (independent)
- F: Write tests (depends on all)

Group 1: [A, D, E] - parallel (schema + UIs)
Group 2: [B, C] - parallel (APIs depend on schema)
Group 3: [F] - sequential (tests depend on all)
```

**Use when:** Many independent tasks, time-critical

## Execution Grouping

Mark parallel groups using `[P:Group-X]` notation:

```
[P:Group-1]
- Task A (foundational)
- Task B (foundational)
- Task C (foundational)

[P:Group-2]
- Task D (depends on A)
- Task E (depends on B)
- Task F (depends on C)

[P:Group-3]
- Task G (depends on D, E, F)
```

## Conflict Detection

Tasks conflict if they modify the same files:

**Conflict Rules:**
- Same source files = sequential (add blocking dependency)
- Same test files = sequential
- Same config files = sequential
- Different files = can be parallel

**Example:**
```
Task A: Modify src/auth.ts
Task B: Modify src/auth.ts → CONFLICT, sequential
Task C: Modify src/user.ts → NO CONFLICT, parallel with A/B
Task D: Modify tests/auth.test.ts → parallel with src/ files
```

## Integration with Beads

Parse beads dependency graph:

```python
# Using parse_beads_deps.py script
graph = parse_beads_deps()

# Get execution order
order = topological_sort(graph)

# Get parallel groups
groups = graph["parallel_groups"]

# Get foundational tasks
foundational = graph["foundational"]
```

## Decision Examples

### Example 1: Standard Feature Implementation

**Tasks:**
- A: Create database schema
- B: Implement API endpoints (depends on A)
- C: Create frontend UI (independent)
- D: Write tests (depends on B)

**Order:** [A, C] → [B] → [D]
**Rationale:** Schema and UI are independent, API depends on schema, tests wait for API

### Example 2: Multi-Epic Feature

**Tasks:**
- Epic 1: Authentication
  - A1: Create user table (foundational)
  - A2: Implement login API (depends on A1)
  - A3: Implement registration API (depends on A1)
- Epic 2: UI
  - B1: Create login form (independent)
  - B2: Create registration form (independent)
- Epic 3: Testing
  - C1: Write auth tests (depends on A2, A3, B1, B2)

**Order:**
- [P:Group-1] [A1, B1, B2] - parallel (foundational schema + UIs)
- [P:Group-2] [A2, A3] - parallel (both depend on A1)
- [P:Group-3] [C1] - sequential (tests depend on all)

### Example 3: High-Risk Feature

**Tasks:**
- A: P2 - Add logging (no deps)
- B: P0 - Fix security bug (no deps)
- C: P1 - Add new feature (depends on B)
- D: P2 - Update docs (depends on C)

**Order:** [B] → [C] → [D, A]
**Rationale:** P0 security bug first, then P1 feature, P2 tasks can run in parallel

## Heuristics

1. **Foundational first** - Database schemas, core services go first
2. **Risk early** - High-priority tasks execute before low-priority
3. **Maximize parallelism** - Independent tasks execute simultaneously
4. **Test last** - Tests execute after implementation
5. **Document at end** - Docs after features are stable
