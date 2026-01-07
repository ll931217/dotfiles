# Parallel Coordinator Quick Reference

## What is it?

A system for executing [P:Group-X] marked tasks in parallel through four phases:
1. **Pre-execution**: Context refresh, dependency check
2. **Concurrent**: Launch tasks with skill pre-invocation
3. **Coordination**: Monitor progress via beads
4. **Post-execution**: Validate, test, close tasks

## Quick Start

### 1. Mark Tasks for Parallel Execution

```python
tasks = [
    {"id": "task-1", "description": "[P:Group-infra] Setup database"},
    {"id": "task-2", "description": "[P:Group-infra] Setup cache"},
    {"id": "task-3", "description": "[P:Group-auth] Implement login"},
]
```

### 2. Detect Groups

```python
from parallel_coordinator import ParallelCoordinator

coordinator = ParallelCoordinator()
groups = coordinator.detect_groups(tasks)

# Returns: {"infra": [task-1, task-2], "auth": [task-3]}
```

### 3. Execute Parallel Group

```python
group_tasks = groups["infra"]
result = coordinator.execute_parallel_group(group_tasks, "infra")

# Check results
print(f"Status: {result.status}")  # TaskStatus.COMPLETED
print(f"Results: {len(result.results)} tasks completed")
```

## API Cheat Sheet

### Core Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `detect_groups(tasks)` | Find [P:Group-X] markers | `Dict[str, List[Dict]]` |
| `execute_parallel_group(tasks, id)` | Run parallel workflow | `GroupMetadata` |
| `refresh_context_before_group()` | Run /flow:summary | `bool` |
| `wait_for_group_completion(id, timeout)` | Wait for finish | `bool` |
| `get_group(id)` | Get group metadata | `GroupMetadata` |
| `list_groups(status=None)` | List all groups | `List[GroupMetadata]` |

### Task Status

| Status | Meaning |
|--------|---------|
| `PENDING` | Not started |
| `IN_PROGRESS` | Currently executing |
| `COMPLETED` | Finished successfully |
| `FAILED` | Finished with errors |
| `BLOCKED` | Dependencies not met |

### Group Phases

| Phase | Meaning |
|-------|---------|
| `PRE_EXECUTION` | Checking dependencies |
| `CONCURRENT_EXECUTION` | Launching tasks |
| `COORDINATION` | Monitoring progress |
| `POST_EXECUTION` | Validating results |

## CLI Commands

```bash
# Detect groups
python parallel_coordinator.py detect --tasks-file tasks.json

# Execute group
python parallel_coordinator.py execute --group-id infra --tasks-file tasks.json

# List groups
python parallel_coordinator.py list --status pending

# Get status
python parallel_coordinator.py status --group-id infra

# Wait for completion
python parallel_coordinator.py wait --group-id infra --timeout 3600
```

## Marker Format

```
[P:Group-<group-id>] Task description
```

Examples:
- `[P:Group-infrastructure] Setup database`
- `[P:Group-auth-flow] Implement login`
- `[P:Group-testing] Write tests`

## Subagent Auto-Detection

| Description Contains | Detected Subagent |
|---------------------|-------------------|
| API, backend, server | `backend-architect` |
| UI, component, React | `frontend-developer` |
| test, pytest, coverage | `test-automator` |
| security, auth, audit | `security-auditor` |
| database, migration | `database-architect` |

## File Structure

```
.flow/maestro/parallel_groups/
    ├── <group-id>/
    │   └── metadata.json
    └── ...
```

## Beads Integration

### Task Metadata

```yaml
metadata:
  subagent_type: "backend-architect"
  fallback_agents: ["database-architect"]
  applicable_skills: ["mcp-builder"]
```

### Dependencies

```yaml
dependencies:
  - id: "dep-task-id"
    dependency_type: "blocks"
```

## Common Patterns

### Execute All Groups

```python
coordinator = ParallelCoordinator()
tasks = load_tasks_from_file()
groups = coordinator.detect_groups(tasks)

for group_id, group_tasks in groups.items():
    if group_id != "_sequential":
        result = coordinator.execute_parallel_group(group_tasks, group_id)
        print(f"Group {group_id}: {result.status}")
```

### Check Completion

```python
group = coordinator.get_group("infrastructure")

if group.status == TaskStatus.COMPLETED:
    print("All tasks done!")
elif group.status == TaskStatus.FAILED:
    print(f"Errors: {group.errors}")
```

### Wait with Timeout

```python
success = coordinator.wait_for_group_completion(
    "infrastructure",
    timeout_seconds=1800  # 30 minutes
)

if not success:
    print("Group timed out")
```

## Error Handling

```python
try:
    result = coordinator.execute_parallel_group(tasks, "mygroup")
except ValueError as e:
    print(f"Validation failed: {e}")

if result.errors:
    print(f"Errors occurred: {result.errors}")
```

## Testing

```bash
# Run unit tests
python test_parallel_coordinator.py

# Run examples
python example_parallel_coordinator.py
```

## Best Practices

1. **Always use pre-group refresh** - Required before ANY [P:Group-X] execution
2. **Design independent tasks** - No shared state between parallel tasks
3. **Use descriptive group IDs** - e.g., `infrastructure` not `group1`
4. **Specify subagent metadata** - For optimal task routing
5. **Check group status** - Always verify after execution

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tasks not detected | Check [P:Group-X] marker format |
| Context timeout | Verify Claude Code is accessible |
| Tasks blocked | Wait for dependencies to close |
| Tests failing | Check test suite before running groups |

## Related Files

- `parallel_coordinator.py` - Implementation
- `test_parallel_coordinator.py` - Unit tests
- `example_parallel_coordinator.py` - Usage examples
- `PARALLEL_COORDINATOR.md` - Full documentation
- `.claude/commands/flow/implement.md` - Workflow spec
