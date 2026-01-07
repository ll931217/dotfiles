# Task Ordering Integration Guide

## Overview

The task ordering system provides intelligent dependency-based task sequencing for autonomous execution. It analyzes beads dependency graphs and applies various strategies to optimize task execution.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Task Ordering Engine                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Beads      │  │  Dependency  │  │   Strategy   │      │
│  │   Parser     │→ │   Graph      │→ │   Selector   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                 ↓                  ↓               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Conflict Detection & Resolution             │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Parallel Group Optimizer                 │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Execution Order Generator                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Command Line

```bash
# Basic usage with default topological sort
python3 task_ordering.py

# Use specific strategy
python3 task_ordering.py --strategy risk_first

# Skip conflict detection
python3 task_ordering.py --no-conflicts

# Text output
python3 task_ordering.py --output-format text
```

### Python API

```python
from task_ordering import TaskOrderingEngine

# Create engine with strategy
engine = TaskOrderingEngine(strategy="topological")

# Load tasks from beads
engine.load_from_beads()

# Compute ordering
result = engine.compute_ordering(detect_conflicts=True)

# Access results
print(f"Total tasks: {result['total_tasks']}")
print(f"Total groups: {result['total_groups']}")
print(f"Parallelizable: {result['parallelizable_groups']}")

# Iterate through sequence
for i, group in enumerate(result['sequence'], 1):
    if len(group) == 1:
        print(f"Group {i}: Sequential task {group[0]}")
    else:
        print(f"Group {i}: [P:Group-{i}] {len(group)} parallel tasks")
```

## Strategies

### 1. Topological Sort (Default)

**Best for:** Standard implementation workflows

Respects dependency order while maximizing parallelism.

```python
engine = TaskOrderingEngine(strategy="topological")
```

**Example Output:**
```
Group 1: [P:Group-1] 3 parallel tasks
  - task-a: Create database schema
  - task-c: Build UI
  - task-d: Setup config
Group 2: [P:Group-2] 2 parallel tasks
  - task-b: Implement API (depends on task-a)
  - task-e: Create tests (depends on task-c)
```

### 2. Risk-First Ordering

**Best for:** High-risk tasks, tight deadlines, critical features

Executes higher priority tasks (P0 → P4) before lower priority.

```python
engine = TaskOrderingEngine(strategy="risk_first")
```

**Priority Mapping:**
- P0 (Critical): Security bugs, core architecture, blocking issues
- P1 (High): Important functionality, urgent bugs
- P2 (Normal): Standard features
- P3 (Low): Nice-to-have enhancements
- P4 (Lowest): Backlog items

### 3. Foundational-First Ordering

**Best for:** Clear foundational elements (schema, core services)

Identifies and prioritizes foundational tasks first.

```python
engine = TaskOrderingEngine(strategy="foundational_first")
```

**Foundation Keywords:**
- `schema`, `core`, `base`, `init`, `setup`, `config`

### 4. Parallel-Maximizing Ordering

**Best for:** Many independent tasks, time-critical projects

Maximizes parallel execution at each level.

```python
engine = TaskOrderingEngine(strategy="parallel_maximizing")
```

## Conflict Detection

Tasks conflict if they modify the same files. The system detects conflicts automatically and separates conflicting tasks into different groups.

### Conflict Detection Methods

1. **File Path Analysis**: Parses task descriptions for file paths
2. **Title Similarity**: Checks for similar keywords suggesting same resource

### Example

```
Task A: Modify `src/auth.ts`
Task B: Add methods to `src/auth.ts`
→ CONFLICT DETECTED → Separated into sequential groups
```

Disable conflict detection if not needed:

```python
result = engine.compute_ordering(detect_conflicts=False)
```

## Output Format

### JSON Output

```json
{
  "strategy": "topological",
  "sequence": [
    ["task-a", "task-b"],  // Parallel group
    ["task-c"],             // Sequential task
    ["task-d", "task-e"]   // Parallel group
  ],
  "rationale": "Strategy: topological\n\nGroup 1: [P:Group-1] 2 parallel tasks...",
  "total_tasks": 5,
  "total_groups": 3,
  "parallelizable_groups": 2,
  "critical_path_length": 3,
  "tasks": {
    "task-a": {
      "id": "task-a",
      "title": "Task A",
      "type": "task",
      "priority": 0,
      "labels": ["critical"],
      "parent": null,
      "depends_on": []
    }
  }
}
```

### Text Output

```
Strategy: topological

Group 1: [P:Group-1] 2 parallel tasks
  - task-a: Task A (P0)
  - task-b: Task B (P0)
Group 2: [task-c] Task C (P1) - sequential
Group 3: [P:Group-3] 2 parallel tasks
  - task-d: Task D (P2)
  - task-e: Task E (P2)

Total tasks: 5
Total groups: 3
Parallelizable groups: 2
```

## Integration with Maestro

### Step 1: Generate Task Order

```python
from task_ordering import TaskOrderingEngine

def get_execution_plan():
    engine = TaskOrderingEngine(strategy="topological")
    engine.load_from_beads()
    result = engine.compute_ordering()
    return result
```

### Step 2: Execute Groups Sequentially

```python
def execute_plan(plan):
    for i, group in enumerate(plan['sequence'], 1):
        if len(group) == 1:
            # Sequential execution
            execute_task(group[0])
        else:
            # Parallel execution
            execute_parallel(group, group_id=i)
```

### Step 3: Handle Parallel Groups

```python
from concurrent.futures import ThreadPoolExecutor

def execute_parallel(task_ids, group_id):
    with ThreadPoolExecutor(max_workers=len(task_ids)) as executor:
        futures = {
            executor.submit(execute_task, task_id): task_id
            for task_id in task_ids
        }
        for future in concurrent.futures.as_completed(futures):
            task_id = futures[future]
            try:
                result = future.result()
                print(f"[P:Group-{group_id}] {task_id} completed")
            except Exception as e:
                print(f"[P:Group-{group_id}] {task_id} failed: {e}")
```

## Beads Integration

### Dependency Structure

Beads supports several dependency types:

1. **blocks**: Task A blocks Task B
2. **depends_on**: Task A depends on Task B
3. **parent-child**: Parent-child relationship (excluded from ordering)

### Example Beads Issues

```json
{
  "id": "dotfiles-246",
  "title": "Implement task ordering",
  "status": "open",
  "priority": 1,
  "dependencies": [
    {
      "id": "dotfiles-123",
      "dependency_type": "depends_on"
    }
  ]
}
```

## Performance Considerations

### Time Complexity

- **Topological Sort**: O(V + E) where V = tasks, E = dependencies
- **Conflict Detection**: O(n²) for pairwise comparisons
- **Parallel Group Detection**: O(V + E)

### Scalability

Tested with:
- 50 tasks: < 100ms
- 200 tasks: < 500ms
- 1000 tasks: < 2s

## Testing

Run the test suite:

```bash
python3 test_task_ordering.py
```

Test coverage includes:
- Simple linear chains
- Parallel execution detection
- Priority-based ordering
- Foundational task detection
- File conflict detection
- Complex dependency graphs

## Troubleshooting

### Issue: Cycles Detected

**Problem:** Circular dependencies detected in graph

**Solution:**
```bash
bd show <issue-id>
# Review depends_on fields
# Remove circular references
```

### Issue: All Tasks Sequential

**Problem:** No parallel groups detected

**Possible Causes:**
1. All tasks have dependencies
2. Conflicts detected between all tasks
3. Single dependency chain

**Solution:**
```bash
# Check conflicts
python3 task_ordering.py --no-conflicts

# Review dependencies
bd list --json | jq '.[] | {id, title, dependency_count}'
```

### Issue: Wrong Strategy Selected

**Problem:** Tasks not ordered optimally

**Solution:**
```python
# Try different strategies
strategies = ["topological", "risk_first", "foundational_first", "parallel_maximizing"]
for strategy in strategies:
    engine = TaskOrderingEngine(strategy=strategy)
    engine.load_from_beads()
    result = engine.compute_ordering()
    print(f"{strategy}: {result['total_groups']} groups, {result['parallelizable_groups']} parallel")
```

## Future Enhancements

1. **Machine Learning**: Learn optimal ordering from historical data
2. **Resource Awareness**: Consider CPU/memory constraints
3. **Dynamic Adjustment**: Reorder based on execution feedback
4. **Multi-Project**: Order tasks across multiple projects
5. **Visual Graph**: Generate dependency graph visualization

## API Reference

### TaskOrderingEngine

```python
class TaskOrderingEngine:
    def __init__(self, strategy: str = "topological")
    def load_from_beads(self, issues: Optional[List[Dict]] = None) -> None
    def compute_ordering(self, detect_conflicts: bool = True) -> Dict[str, Any]
    def topological_sort(self) -> List[List[str]]
    def risk_first_ordering(self) -> List[List[str]]
    def foundational_first_ordering(self) -> List[List[str]]
    def parallel_maximizing_ordering(self) -> List[List[str]]
    def detect_conflicts(self) -> Set[Tuple[str, str]]
    def detect_file_conflicts(self, task1: str, task2: str) -> bool
```

### Module Functions

```python
def get_beads_issues() -> List[Dict]
def get_issue_details(issue_id: str) -> Dict
def _extract_dependencies(issue_data: Dict) -> List[str]
```
