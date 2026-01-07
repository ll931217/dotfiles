# Parallel Execution Coordinator

## Overview

The Parallel Execution Coordinator implements the [P:Group-X] parallel task execution workflow from `implement.md`. It enables concurrent execution of independent tasks through a four-phase process:

1. **Phase 1: Pre-execution Analysis** - Context refresh, dependency checking, task validation
2. **Phase 2: Concurrent Execution** - Subagent selection, skill pre-invocation, parallel launches
3. **Phase 3: Coordination & Monitoring** - Progress tracking, beads coordination, completion waiting
4. **Phase 4: Post-execution Validation** - Verification, test suite, task closure

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Parallel Coordinator                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Group      │  │   Task       │  │  Execution   │     │
│  │  Detection   │  │  Metadata    │  │   Phases     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                        Core Methods                         │
│                                                             │
│  • detect_groups()         • execute_parallel_group()      │
│  • refresh_context()       • wait_for_completion()         │
│  • get_group()             • list_groups()                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Integration Points                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Beads      │  │  Subagents   │  │   Skills     │     │
│  │  Database    │  │  Selection   │  │  Invocation  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Installation

Located at:
```
.flow/maestro/scripts/parallel_coordinator.py
```

## API Reference

### ParallelCoordinator

Main coordinator class for parallel task execution.

#### Constructor

```python
coordinator = ParallelCoordinator(repo_root="/path/to/repo")
```

**Parameters:**
- `repo_root` (str, optional): Repository root path. Auto-detected if not provided.

#### Methods

##### detect_groups()

Detect [P:Group-X] markers in task descriptions and group them.

```python
groups = coordinator.detect_groups(tasks)
```

**Parameters:**
- `tasks` (List[Dict]): List of task dictionaries with 'id' and 'description'

**Returns:**
- `Dict[str, List[Dict]]`: Dictionary mapping group IDs to task lists

**Example:**
```python
tasks = [
    {"id": "task-1", "description": "[P:Group-infra] Setup DB"},
    {"id": "task-2", "description": "[P:Group-infra] Setup cache"},
    {"id": "task-3", "description": "Sequential task"},
]

groups = coordinator.detect_groups(tasks)
# {
#     "infra": [{"id": "task-1", ...}, {"id": "task-2", ...}],
#     "_sequential": [{"id": "task-3", ...}]
# }
```

##### execute_parallel_group()

Execute a group of parallel tasks through the four-phase workflow.

```python
result = coordinator.execute_parallel_group(group_tasks, group_id)
```

**Parameters:**
- `group_tasks` (List[Dict]): Tasks in the parallel group
- `group_id` (str): Identifier for this group

**Returns:**
- `GroupMetadata`: Execution results with status, results, errors

**Raises:**
- `ValueError`: If group validation fails

**Example:**
```python
group_tasks = [
    {"id": "proj-auth.1", "description": "[P:Group-auth] Login API"},
    {"id": "proj-auth.2", "description": "[P:Group-auth] Logout API"},
]

result = coordinator.execute_parallel_group(group_tasks, "auth")
print(f"Status: {result.status}")
print(f"Completed: {len(result.results)}/{len(group_tasks)}")
```

##### refresh_context_before_group()

Execute /flow:summary to refresh context before starting a parallel group.

```python
success = coordinator.refresh_context_before_group()
```

**Returns:**
- `bool`: True if refresh successful, False otherwise

**Note:** This is REQUIRED before starting ANY [P:Group-X] parallel task group.

##### wait_for_group_completion()

Wait for a parallel group to complete execution.

```python
success = coordinator.wait_for_group_completion(group_id, timeout_seconds=3600)
```

**Parameters:**
- `group_id` (str): Group identifier
- `timeout_seconds` (int): Maximum time to wait (default: 1 hour)

**Returns:**
- `bool`: True if group completed successfully, False if timeout or error

##### get_group()

Retrieve group metadata by ID.

```python
group = coordinator.get_group(group_id)
```

**Parameters:**
- `group_id` (str): Group identifier

**Returns:**
- `GroupMetadata` or None: Group metadata or None if not found

##### list_groups()

List all parallel groups, optionally filtered by status.

```python
groups = coordinator.list_groups(status=TaskStatus.PENDING)
```

**Parameters:**
- `status` (TaskStatus, optional): Status filter

**Returns:**
- `List[GroupMetadata]`: List of group metadata objects

## Data Models

### GroupMetadata

Metadata for a parallel task group.

```python
@dataclass
class GroupMetadata:
    group_id: str                              # Unique group identifier
    group_name: str                            # Human-readable name
    phase: GroupPhase                          # Current execution phase
    tasks: List[str]                           # Task IDs in the group
    created_at: str                            # ISO 8601 timestamp
    started_at: Optional[str]                  # Execution start time
    completed_at: Optional[str]                # Execution completion time
    status: TaskStatus                         # Overall status
    results: List[Dict[str, Any]]             # Individual task results
    errors: List[str]                          # Error messages
    pre_group_refresh_completed: bool          # Context refresh status
```

### TaskMetadata

Metadata for a single task within a group.

```python
@dataclass
class TaskMetadata:
    task_id: str                               # Beads issue ID
    title: str                                 # Task title
    description: str                           # Full description
    subagent_type: Optional[str]               # Primary subagent
    fallback_agents: List[str]                 # Alternative subagents
    applicable_skills: List[str]               # Skills to apply
    relevant_files: List[str]                  # Files to modify
    dependencies: List[str]                    # Blocking task IDs
    priority: int                              # Priority level (0-4)
    status: TaskStatus                         # Execution status
```

### GroupPhase

Parallel group execution phases.

```python
class GroupPhase(str, Enum):
    PRE_EXECUTION = "pre_execution"            # Dependency checking
    CONCURRENT_EXECUTION = "concurrent_execution"  # Parallel launches
    COORDINATION = "coordination"              # Progress monitoring
    POST_EXECUTION = "post_execution"          # Validation & closure
```

### TaskStatus

Task execution status.

```python
class TaskStatus(str, Enum):
    PENDING = "pending"                        # Not yet started
    IN_PROGRESS = "in_progress"                # Currently executing
    COMPLETED = "completed"                    # Finished successfully
    FAILED = "failed"                          # Finished with errors
    BLOCKED = "blocked"                        # Blocked by dependencies
```

## Four-Phase Workflow

### Phase 1: Pre-execution Analysis

**Goal:** Ensure tasks are ready for parallel execution.

**Steps:**
1. Execute `/flow:summary` to refresh context (REQUIRED)
2. Check which tasks are unblocked
3. Verify there are no blocking dependencies
4. Review task details and blockers

**Example:**
```python
# Phase 1 is automatically executed by execute_parallel_group()
# It calls refresh_context_before_group() which runs /flow:summary
```

### Phase 2: Concurrent Execution

**Goal:** Launch all tasks in the group simultaneously.

**Steps:**
1. For each task:
   - Select subagent based on metadata
   - Apply applicable skills before launching
   - Launch task via Task tool
2. Update task status to in_progress

**Subagent Selection:**
- Uses `subagent_type` from beads metadata
- Falls back to `fallback_agents` if primary unavailable
- Auto-detects by analyzing task description if no metadata

**Skill Pre-invocation:**
- Skills from `applicable_skills` array are applied first
- Skill output guides subagent's approach

**Example:**
```python
# Task with skill pre-invocation
Skill(skill="frontend-design", args="Create UI for auth")
↓
Task(
    subagent="frontend-developer",
    prompt="Implement React login component... Following design guidelines...",
)
```

### Phase 3: Coordination & Monitoring

**Goal:** Monitor progress and wait for all tasks to complete.

**Steps:**
1. Monitor progress via in-progress task status
2. Use beads database for coordination between parallel tasks
3. Wait for ALL tasks in the group to complete

**Example:**
```python
# Poll beads for task completion status
while not all_tasks_completed:
    for task_id in group_tasks:
        status = get_beads_status(task_id)
        if status == "closed":
            mark_completed(task_id)
```

### Phase 4: Post-execution Validation

**Goal:** Verify completion and clean up.

**Steps:**
1. Verify all group tasks are completed
2. Run test suite if applicable
3. Close completed tasks in beads
4. Update group status to COMPLETED

**Example:**
```python
# Run tests
test_success = coordinator._run_test_suite()

# Close tasks
for task_id in completed_tasks:
    coordinator._close_beads_task(task_id)
```

## CLI Usage

### Detect Groups

```bash
python parallel_coordinator.py detect --tasks-file tasks.json
```

### Execute Parallel Group

```bash
python parallel_coordinator.py execute \
    --group-id infrastructure \
    --tasks-file tasks.json
```

### List Groups

```bash
# List all groups
python parallel_coordinator.py list

# Filter by status
python parallel_coordinator.py list --status pending
```

### Get Group Status

```bash
python parallel_coordinator.py status --group-id infrastructure
```

### Wait for Completion

```bash
python parallel_coordinator.py wait \
    --group-id infrastructure \
    --timeout 3600
```

## Integration with Beads

### Task Metadata

Beads issues can include metadata to guide parallel execution:

```yaml
metadata:
  subagent_type: "backend-architect"
  fallback_agents: ["database-architect"]
  applicable_skills: ["mcp-builder"]
```

### Dependencies

Parallel coordinator checks dependencies before execution:

```yaml
dependencies:
  - id: "proj-auth.0"
    dependency_type: "blocks"
```

If dependency is still open, task is marked as BLOCKED and skipped.

### Status Tracking

Coordinator tracks task status via beads:
- `open` → Task pending or in progress
- `closed` → Task completed

After successful completion, tasks are closed via `bd close <task-id>`.

## Automatic Subagent Detection

If task lacks `subagent_type` metadata, coordinator auto-detects based on description patterns:

| Description Pattern | Detected Subagent |
|---------------------|-------------------|
| API, backend, server, database | `backend-architect` |
| UI, component, frontend, React | `frontend-developer` |
| Test, pytest, coverage | `test-automator` |
| Migration, schema, SQL | `database-architect` |
| Security, auth, audit | `security-auditor` |

## File Path Extraction

Coordinator extracts file paths from task descriptions:

```python
description = """
Implement src/components/Login.tsx with TypeScript
Update src/services/AuthService.ts
"""

files = coordinator._extract_relevant_files(description)
# ["src/components/Login.tsx", "src/services/AuthService.ts"]
```

## Persistence

Group metadata is persisted to disk:

```
.flow/maestro/parallel_groups/
    ├── <group-id>/
    │   └── metadata.json
    └── ...
```

**metadata.json structure:**
```json
{
  "group_id": "infrastructure",
  "group_name": "Parallel Group infrastructure",
  "phase": "post_execution",
  "tasks": ["proj-auth.1", "proj-auth.2"],
  "created_at": "2024-01-01T00:00:00Z",
  "started_at": "2024-01-01T00:01:00Z",
  "completed_at": "2024-01-01T00:05:00Z",
  "status": "completed",
  "results": [
    {
      "task_id": "proj-auth.1",
      "subagent": "backend-architect",
      "status": "completed",
      "started_at": "2024-01-01T00:01:00Z",
      "completed_at": "2024-01-01T00:03:00Z"
    }
  ],
  "errors": [],
  "pre_group_refresh_completed": true
}
```

## Error Handling

### Context Refresh Failure

If `/flow:summary` fails or times out:
- Warning is logged
- Execution continues (context may be stale)
- `pre_group_refresh_completed` flag set to False

### Task Execution Failure

If a task fails during parallel execution:
- Task status marked as FAILED
- Error message added to group metadata
- Group status set to FAILED
- Other tasks continue executing

### Dependency Blocking

If task dependencies are still open:
- Task marked as BLOCKED
- Skipped in parallel execution
- Can be executed later when dependencies clear

## Testing

Run unit tests:

```bash
python test_parallel_coordinator.py
```

Run examples:

```bash
python example_parallel_coordinator.py
```

## Best Practices

### 1. Always Use Pre-Group Refresh

Before starting ANY [P:Group-X] parallel task group:
```python
coordinator.refresh_context_before_group()
```

This ensures accurate context about dependencies and blocking issues.

### 2. Design Independent Tasks

Tasks in a parallel group should be:
- Independent of each other
- Free of shared mutable state
- Safe to execute concurrently

### 3. Use Descriptive Group IDs

Group IDs should be descriptive:
- ✅ `[P:Group-infrastructure]` - Clear
- ✅ `[P:Group-auth-flow]` - Clear
- ❌ `[P:Group-1]` - Not descriptive

### 4. Specify Subagent Metadata

For optimal task routing, specify subagent in beads metadata:
```yaml
metadata:
  subagent_type: "backend-architect"
```

### 5. Handle Failures Gracefully

Always check group status after execution:
```python
result = coordinator.execute_parallel_group(tasks, "mygroup")

if result.status == TaskStatus.COMPLETED:
    print("All tasks completed successfully")
elif result.status == TaskStatus.FAILED:
    print(f"Failed tasks: {result.errors}")
```

## Examples

See `example_parallel_coordinator.py` for complete examples:
- Group detection from task descriptions
- Parallel group execution
- Task metadata extraction
- Subagent auto-detection
- Complete workflow
- CLI usage
- Beads integration

## Troubleshooting

### Issue: Tasks Not Detected as Parallel

**Cause:** [P:Group-X] marker missing or malformed

**Solution:** Ensure marker format is correct:
```python
description = "[P:Group-infra] Setup database"  # Correct
description = "Setup database [P:Group-infra]"  # Wrong order
```

### Issue: Context Refresh Timeout

**Cause:** `/flow:summary` taking too long

**Solution:**
- Check network connectivity
- Verify Claude Code is installed and accessible
- Increase timeout in `refresh_context_before_group()`

### Issue: Tasks Blocked by Dependencies

**Cause:** Dependencies not yet closed

**Solution:**
- Wait for dependencies to complete
- Run `/flow:summary` to check dependency status
- Execute tasks later when dependencies clear

## Related Documentation

- `.claude/commands/flow/implement.md` - Parallel execution workflow specification
- `.flow/maestro/scripts/session_manager.py` - Session lifecycle management
- `.flow/maestro/scripts/error_handler.py` - Error detection and recovery
- `.flow/maestro/scripts/checkpoint_manager.py` - Checkpoint and recovery

## License

Part of the Maestro Orchestrator system.
