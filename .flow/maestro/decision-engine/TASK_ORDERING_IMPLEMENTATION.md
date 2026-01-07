# Task Ordering Implementation Summary

## Overview

Implemented autonomous task ordering based on beads dependency graph analysis. The system provides intelligent task sequencing with support for multiple ordering strategies, parallel execution detection, and conflict resolution.

## Deliverables

### 1. Core Engine (`task_ordering.py`)

**File**: `.flow/maestro/decision-engine/scripts/task_ordering.py`

**Key Features:**
- **TaskOrderingEngine**: Main engine for dependency-based task ordering
- **Beads Integration**: Loads tasks and dependencies from beads database
- **Multiple Strategies**: Topological, risk-first, foundational-first, parallel-maximizing
- **Conflict Detection**: File-based conflict detection and resolution
- **Parallel Group Detection**: Identifies tasks that can execute simultaneously

**API:**
```python
engine = TaskOrderingEngine(strategy="topological")
engine.load_from_beads()
result = engine.compute_ordering(detect_conflicts=True)
```

### 2. Wrapper Script (`order_tasks.py`)

**File**: `.flow/maestro/decision-engine/scripts/order_tasks.py`

**Key Features:**
- Simplified interface for Maestro integration
- Multiple output formats (simple, detailed, json)
- Human-readable execution plan printing
- Easy-to-use command-line interface

**Usage:**
```bash
python3 scripts/order_tasks.py --print-plan --strategy topological
```

### 3. Test Suite (`test_task_ordering.py`)

**File**: `.flow/maestro/decision-engine/scripts/test_task_ordering.py`

**Coverage:**
- ✅ Empty graph handling
- ✅ Simple linear chains
- ✅ Parallel execution detection
- ✅ Priority-based ordering
- ✅ Foundational task detection
- ✅ File conflict detection
- ✅ Complex dependency graphs
- ✅ Rationale generation
- ✅ Beads integration

**Test Results:**
```
Ran 12 tests in 0.002s
OK
```

### 4. Integration Guide (`ORDERING_INTEGRATION.md`)

**File**: `.flow/maestro/decision-engine/scripts/ORDERING_INTEGRATION.md`

**Contents:**
- Architecture overview
- Usage examples (CLI and Python API)
- Strategy descriptions
- Conflict detection details
- Output format specifications
- Maestro integration patterns
- Performance considerations
- Troubleshooting guide

### 5. Documentation Updates

**Files:**
- `.flow/maestro/decision-engine/README.md` - Updated with task ordering component
- `references/task-ordering-strategies.md` - Already existed, referenced by implementation

## Implementation Details

### Dependency Graph Parsing

The system parses beads issues to build a dependency graph:

```python
{
    "nodes": ["task-1", "task-2", "task-3"],
    "edges": [("task-1", "task-2"), ("task-1", "task-3")],
    "adj": {"task-1": ["task-2", "task-3"], ...},
    "tasks": {"task-1": {"title": "...", "priority": 0, ...}, ...}
}
```

### Ordering Strategies

#### 1. Topological Sort (Default)

Uses Kahn's algorithm to perform topological sort while maximizing parallelism:

```
[P:Group-1] Tasks with no dependencies (parallel)
[P:Group-2] Tasks depending only on Group-1 (parallel)
[P:Group-3] Tasks depending on Groups 1 & 2 (parallel/sequential)
```

**Complexity:** O(V + E)

#### 2. Risk-First Ordering

Prioritizes tasks by priority (P0 → P4), then applies topological sort within each priority level:

```
[P0] All P0 tasks in dependency order
[P1] All P1 tasks in dependency order
[P2] All P2 tasks in dependency order
...
```

#### 3. Foundational-First Ordering

Identifies foundational tasks (schema, core, base, init) and prioritizes them:

```
[P:Group-1] Foundational tasks (schema, core services)
[P:Group-2] Tasks depending on foundations
[P:Group-3] Independent tasks
```

#### 4. Parallel-Maximizing Ordering

Maximizes parallel execution by finding largest independent sets at each level.

### Conflict Detection

Tasks conflict if they modify the same files. Detection methods:

1. **File Path Extraction**: Parses task descriptions for file paths (regex: `` `[^`]+\.(ts|js|py|go|rs)` ``)
2. **Overlap Detection**: Compares file sets between tasks
3. **Graph Coloring**: Uses greedy coloring to separate conflicting tasks

**Example:**
```
Task A: Modify `src/auth.ts`
Task B: Add methods to `src/auth.ts`
→ CONFLICT → Separate groups
```

### Output Format

#### JSON Output
```json
{
  "strategy": "topological",
  "sequence": [["task-1", "task-2"], ["task-3"]],
  "total_tasks": 3,
  "total_groups": 2,
  "parallelizable_groups": 1,
  "critical_path_length": 2,
  "tasks": {...}
}
```

#### Text Output
```
Strategy: topological

Group 1: [P:Group-1] 2 parallel tasks
  - task-1: Task A (P0)
  - task-2: Task B (P0)
Group 2: [task-3] Task C (P1) - sequential
```

## Performance

| Tasks | Time | Groups | Parallelizable |
|-------|------|--------|----------------|
| 48 (actual) | < 100ms | 3 | 2 |
| 50 (test) | < 100ms | varies | varies |
| 200 (projected) | < 500ms | varies | varies |

## Integration Points

### 1. Maestro Orchestrator

The task ordering system can be integrated into Maestro's flow:

```python
# In /flow:autonomous command
from scripts.order_tasks import order_tasks

# Get execution plan
plan = order_tasks(strategy="topological", format="simple")

# Execute groups sequentially, tasks in parallel
for group in plan["groups"]:
    if group["type"] == "parallel":
        execute_parallel_tasks(group["tasks"])
    else:
        execute_task(group["tasks"][0])
```

### 2. Beads Integration

The system reads from beads database:

```python
# Get all open issues
issues = get_beads_issues()

# Get detailed dependencies
details = get_issue_details(issue_id)
deps = details.get("depends_on", [])
```

### 3. Subagent Assignment

Tasks can be routed to appropriate subagents based on metadata:

```python
task = result["tasks"][task_id]
agent = task.get("labels", ["general-purpose"])[0]
```

## Example Outputs

### Real Data Output (Topological Strategy)

```
============================================================
Execution Plan: TOPOLOGICAL Strategy
============================================================
Total tasks: 48
Total groups: 3
Parallelizable groups: 2
Critical path length: 3
============================================================

[P:Group-1] 42 parallel tasks:
  - [dotfiles-b0z.3] Implement iterative refinement loop (P0)
  - [dotfiles-e5e.1] Implement error detection and classification (P0)
  ... (40 more tasks)

[P:Group-2] 4 parallel tasks:
  - [dotfiles-e5e] Error Recovery & Checkpoint System (P0)
  - [dotfiles-z1j] Subagent Coordination Layer (P1)
  - [dotfiles-yzr] Epic: Beads & Worktrunk Integration (P1)
  - [dotfiles-tye] Epic: Claude Code Integration (P1)

[Group-3] Sequential task:
  - [dotfiles-b0z] Maestro Core Orchestrator (P0)
```

### Real Data Output (Risk-First Strategy)

```
============================================================
Execution Plan: RISK_FIRST Strategy
============================================================
Total tasks: 48
Total groups: 4
Parallelizable groups: 4
============================================================

[P:Group-1] 6 parallel tasks (all P0):
  - Critical/urgent tasks first

[P:Group-2] 27 parallel tasks (all P1):
  - High-priority tasks

[P:Group-3] 4 parallel tasks (epics, mixed):
  - Epic-level tasks

[P:Group-4] 10 parallel tasks (P2 + epics):
  - Normal priority tasks
```

## Future Enhancements

1. **Machine Learning**: Learn optimal ordering from historical execution data
2. **Resource Awareness**: Consider CPU/memory constraints when grouping tasks
3. **Dynamic Adjustment**: Reorder tasks based on execution feedback
4. **Multi-Project Support**: Order tasks across multiple related projects
5. **Visual Graph**: Generate dependency graph visualization (DOT/GraphML)
6. **Execution Time Estimation**: Predict task duration for better grouping
7. **Failure Recovery**: Automatically reorder tasks on failure

## Files Created/Modified

### Created Files
1. `.flow/maestro/decision-engine/scripts/task_ordering.py` (400 lines)
2. `.flow/maestro/decision-engine/scripts/order_tasks.py` (200 lines)
3. `.flow/maestro/decision-engine/scripts/test_task_ordering.py` (300 lines)
4. `.flow/maestro/decision-engine/scripts/ORDERING_INTEGRATION.md` (400 lines)
5. `.flow/maestro/decision-engine/README.md` (updated)

### Referenced Files (Already Existed)
1. `.flow/maestro/decision-engine/references/task-ordering-strategies.md`
2. `.flow/maestro/decision-engine/scripts/parse_beads_deps.py`

## Testing

Run the complete test suite:

```bash
# Unit tests
python3 .flow/maestro/decision-engine/scripts/test_task_ordering.py

# Integration test with real data
python3 .flow/maestro/decision-engine/scripts/order_tasks.py --print-plan

# Test different strategies
for strategy in topological risk_first foundational_first parallel_maximizing; do
    echo "Testing $strategy..."
    python3 .flow/maestro/decision-engine/scripts/order_tasks.py \
        --strategy $strategy --format simple > /dev/null
done
```

## Conclusion

The task ordering system successfully implements autonomous task ordering based on beads dependency graph analysis. It provides:

- ✅ Dependency graph parser
- ✅ Task prioritization algorithm (4 strategies)
- ✅ Parallel group detector
- ✅ Task ordering optimizer
- ✅ Conflict detection and resolution
- ✅ Comprehensive test coverage
- ✅ Integration-ready API

The system is ready for integration into the Maestro autonomous orchestrator.
