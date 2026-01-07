# Checkpoint Manager

Git-based checkpoint creation and restoration for safe rollback during Maestro orchestration sessions.

## Overview

The Checkpoint Manager provides automated checkpoint creation using git commits and tags, enabling safe rollback at any point during development. It tracks checkpoints with metadata including session state, phase information, and rollback history.

## Features

- **Git-based Checkpoints**: Uses git commits and tags for persistent recovery points
- **State Validation**: Validates repository state before creating checkpoints
- **Rollback Support**: Safe rollback to any previous checkpoint
- **Metadata Tracking**: Tracks session state, phase, and checkpoint usage
- **Checkpoint Types**: Supports different checkpoint types (phase complete, safe state, error recovery, etc.)
- **CLI Interface**: Command-line interface for checkpoint operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Checkpoint Manager                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  create_cp()     │  │  rollback_to_cp()│                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                            │
│  ┌────────▼─────────┐  ┌───────▼──────────┐                │
│  │  validate_state()│  │  git_reset()     │                │
│  └────────┬─────────┘  └──────┬──────────┘                │
│           │                     │                            │
│  ┌────────▼─────────────────────▼──────────┐                │
│  │         Persistence Layer                 │                │
│  │  .flow/maestro/sessions/<id>/            │                │
│  │    └── checkpoints.json                  │                │
│  └──────────────────────────────────────────┘                │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                         Git Layer                            │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ git commit   │  │ git tag      │  │ git reset    │     │
│  │              │  │ checkpoint-<id>│  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Checkpoint

Represents a git checkpoint with metadata.

```python
@dataclass
class Checkpoint:
    checkpoint_id: str                    # Unique checkpoint identifier
    commit_sha: str                       # Git commit SHA
    timestamp: str                        # ISO 8601 timestamp
    description: str                      # Human-readable description
    phase: CheckpointPhase                # Execution phase
    checkpoint_type: CheckpointType       # Type of checkpoint
    commit_message: Optional[str]         # Git commit message
    state_snapshot: Optional[StateSnapshot]  # Session state at checkpoint
    tags: List[str]                       # Git tags
    rollback_used: bool                   # Whether used for rollback
    rollback_count: int                   # Number of rollbacks to this point
```

### CheckpointType

Enum defining checkpoint creation reasons:

- `PHASE_COMPLETE`: Checkpoint at phase completion
- `TASK_GROUP_COMPLETE`: Checkpoint after task group completion
- `SAFE_STATE`: Checkpoint at known good state
- `PRE_RISKY_OPERATION`: Checkpoint before risky operation
- `ERROR_RECOVERY`: Checkpoint created during error recovery
- `MANUAL`: Manually created checkpoint

### CheckpointPhase

Enum defining session phases:

- `PLAN`: Planning phase
- `GENERATE_TASKS`: Task generation phase
- `IMPLEMENT`: Implementation phase
- `VALIDATE`: Validation phase
- `CLEANUP`: Cleanup phase

### StateSnapshot

Snapshot of session state at checkpoint time:

```python
@dataclass
class StateSnapshot:
    tasks_completed: int = 0
    decisions_made: int = 0
    files_modified: int = 0
    files_created: int = 0
    tests_passing: int = 0
    tests_failing: int = 0
```

## API Reference

### CheckpointManager

Main class for checkpoint management.

#### `__init__(repo_root: Optional[str] = None, session_id: Optional[str] = None)`

Initialize checkpoint manager.

- `repo_root`: Repository root path (auto-detected if None)
- `session_id`: Session UUID (can be set later)

#### `validate_checkpoint_state() -> ValidationResult`

Validate current repository state before creating checkpoint.

Returns `ValidationResult` with:
- `is_valid`: Whether state is valid for checkpoint
- `errors`: List of validation errors
- `warnings`: List of validation warnings
- `git_status`: Git status output
- `has_uncommitted_changes`: Whether uncommitted changes exist
- `tests_passing`: Whether tests are passing

#### `create_checkpoint(session_id: str, description: str, phase: CheckpointPhase, checkpoint_type: CheckpointType = CheckpointType.MANUAL, state_snapshot: Optional[StateSnapshot] = None, commit_first: bool = True) -> Checkpoint`

Create a git checkpoint.

Parameters:
- `session_id`: Session UUID
- `description`: Human-readable description
- `phase`: Execution phase
- `checkpoint_type`: Type of checkpoint
- `state_snapshot`: Optional session state snapshot
- `commit_first`: Whether to commit changes before tagging

Returns created `Checkpoint` object.

#### `list_checkpoints(session_id: str) -> List[Checkpoint]`

List all checkpoints for a session, sorted by timestamp (newest first).

#### `get_checkpoint(session_id: str, checkpoint_id: str) -> Checkpoint`

Get specific checkpoint by ID.

#### `rollback_to_checkpoint(session_id: str, checkpoint_id: str, hard_reset: bool = False) -> bool`

Rollback repository to a previous checkpoint.

Parameters:
- `session_id`: Session UUID
- `checkpoint_id`: Checkpoint UUID to rollback to
- `hard_reset`: If True, use `git reset --hard`; otherwise `--mixed`

Returns `True` if rollback succeeded.

#### `get_checkpoint_summary(session_id: str) -> CheckpointSummary`

Get summary statistics for session checkpoints.

Returns `CheckpointSummary` with:
- `total_checkpoints`: Total number of checkpoints
- `checkpoints_by_type`: Breakdown by checkpoint type
- `checkpoints_used_for_rollback`: Number of checkpoints used for rollback
- `latest_checkpoint`: SHA of latest checkpoint

#### `delete_checkpoint(session_id: str, checkpoint_id: str, delete_tag: bool = True) -> bool`

Delete a checkpoint from tracking.

Parameters:
- `session_id`: Session UUID
- `checkpoint_id`: Checkpoint UUID to delete
- `delete_tag`: Whether to delete the git tag

## Usage Examples

### Basic Checkpoint Creation

```python
from checkpoint_manager import CheckpointManager, CheckpointPhase, CheckpointType

manager = CheckpointManager()
session_id = "uuid-string"

# Create checkpoint
checkpoint = manager.create_checkpoint(
    session_id=session_id,
    description="Planning phase completed",
    phase=CheckpointPhase.PLAN,
    checkpoint_type=CheckpointType.PHASE_COMPLETE,
    commit_first=False,
)

print(f"Created checkpoint: {checkpoint.checkpoint_id}")
print(f"Commit SHA: {checkpoint.commit_sha}")
```

### Checkpoint with State Snapshot

```python
from checkpoint_manager import StateSnapshot

# Capture session state
state_snapshot = StateSnapshot(
    tasks_completed=15,
    decisions_made=8,
    files_modified=23,
    files_created=12,
    tests_passing=42,
    tests_failing=0,
)

# Create checkpoint with state
checkpoint = manager.create_checkpoint(
    session_id=session_id,
    description="Implementation milestone",
    phase=CheckpointPhase.IMPLEMENT,
    checkpoint_type=CheckpointType.TASK_GROUP_COMPLETE,
    state_snapshot=state_snapshot,
)
```

### Pre-Operation Safety Checkpoint

```python
# Validate before risky operation
validation = manager.validate_checkpoint_state()

if validation.is_valid:
    # Create safety checkpoint
    safety_cp = manager.create_checkpoint(
        session_id=session_id,
        description="Before database migration",
        phase=CheckpointPhase.IMPLEMENT,
        checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
    )

    try:
        # Perform risky operation
        perform_migration()
    except Exception as e:
        # Rollback to safety point
        manager.rollback_to_checkpoint(session_id, safety_cp.checkpoint_id)
```

### Listing Checkpoints

```python
# List all checkpoints
checkpoints = manager.list_checkpoints(session_id)

for i, cp in enumerate(checkpoints, 1):
    print(f"{i}. {cp.description}")
    print(f"   Phase: {cp.phase.value}")
    print(f"   Type: {cp.checkpoint_type.value}")
    print(f"   Time: {cp.timestamp}")

# Get summary
summary = manager.get_checkpoint_summary(session_id)
print(f"Total: {summary.total_checkpoints}")
print(f"By type: {summary.checkpoints_by_type}")
```

### Rollback Workflow

```python
# Create stable checkpoint
stable_cp = manager.create_checkpoint(
    session_id=session_id,
    description="Stable state",
    phase=CheckpointPhase.IMPLEMENT,
    checkpoint_type=CheckpointType.SAFE_STATE,
)

# Make changes
make_changes()

# Something went wrong, rollback
manager.rollback_to_checkpoint(
    session_id=session_id,
    checkpoint_id=stable_cp.checkpoint_id,
    hard_reset=False,  # Use --mixed to preserve working directory
)
```

## CLI Usage

### Create Checkpoint

```bash
python checkpoint_manager.py create \
    --session-id <uuid> \
    --description "Planning complete" \
    --phase plan \
    --checkpoint-type phase_complete
```

### List Checkpoints

```bash
python checkpoint_manager.py list \
    --session-id <uuid> \
    --output pretty
```

### Get Specific Checkpoint

```bash
python checkpoint_manager.py get \
    --session-id <uuid> \
    --checkpoint-id <checkpoint-uuid>
```

### Rollback to Checkpoint

```bash
python checkpoint_manager.py rollback \
    --session-id <uuid> \
    --checkpoint-id <checkpoint-uuid> \
    --hard-reset
```

### Validate State

```bash
python checkpoint_manager.py validate
```

## Checkpoint Log Format

Checkpoint data is stored in `.flow/maestro/sessions/<session-id>/checkpoints.json`:

```json
{
  "session_id": "uuid-string",
  "generated_at": "2024-01-07T13:00:00Z",
  "checkpoints": [
    {
      "checkpoint_id": "uuid-string",
      "commit_sha": "abc123...",
      "timestamp": "2024-01-07T13:00:00Z",
      "description": "Planning phase completed",
      "phase": "plan",
      "checkpoint_type": "phase_complete",
      "tags": ["checkpoint-uuid-string"],
      "rollback_used": false,
      "rollback_count": 0
    }
  ],
  "summary": {
    "total_checkpoints": 1,
    "checkpoints_by_type": {
      "phase_complete": 1
    },
    "checkpoints_used_for_rollback": 0,
    "latest_checkpoint": "abc123..."
  }
}
```

## Testing

Run the unit tests:

```bash
cd .flow/maestro/scripts
python -m unittest test_checkpoint_manager -v
```

Run example usage:

```bash
python example_checkpoint_manager.py
```

## Integration with Session Manager

The checkpoint manager integrates with the session manager's statistics tracking:

```python
from session_manager import SessionManager
from checkpoint_manager import CheckpointManager

session_mgr = SessionManager()
checkpoint_mgr = CheckpointManager()

# Create session
session = session_mgr.create_session("Implement feature")

# Create checkpoint during implementation
checkpoint = checkpoint_mgr.create_checkpoint(
    session_id=session.session_id,
    description="Implementation checkpoint",
    phase=CheckpointPhase.IMPLEMENT,
)

# Update session statistics
session_mgr.update_session(
    session.session_id,
    {
        "statistics": {
            "checkpoints_created": 1,
        }
    },
)
```

## Best Practices

1. **Create Checkpoints Regularly**: Create checkpoints at phase boundaries and before risky operations
2. **Use Descriptive Messages**: Clear descriptions help identify rollback points
3. **Include State Snapshots**: Track session state for better debugging
4. **Validate Before Rollback**: Always check for uncommitted changes before rolling back
5. **Use Appropriate Checkpoint Types**: Helps organize checkpoint history
6. **Clean Up Old Checkpoints**: Remove obsolete checkpoints to reduce clutter

## Error Handling

The checkpoint manager provides clear error messages:

```python
try:
    checkpoint = manager.create_checkpoint(...)
except ValueError as e:
    # Validation failed
    print(f"Cannot create checkpoint: {e}")
except FileNotFoundError as e:
    # Session or checkpoint not found
    print(f"Not found: {e}")
except subprocess.SubprocessError as e:
    # Git command failed
    print(f"Git error: {e}")
```

## Performance Considerations

- **Checkpoint Creation**: O(1) - Single git commit and tag operation
- **Checkpoint Listing**: O(n) - Linear in number of checkpoints
- **Checkpoint Retrieval**: O(1) - Direct file access
- **Rollback**: O(1) - Single git reset operation

## Security Considerations

- Checkpoint IDs are validated as UUIDs
- No relative paths allowed in file operations
- Session directory sandboxing enforced
- Git commands run in controlled repository context

## Troubleshooting

### Checkpoint Creation Fails

If checkpoint creation fails:

1. Check git repository is initialized: `git status`
2. Verify no uncommitted changes if `commit_first=False`
3. Check write permissions for `.flow/maestro/sessions/`
4. Validate checkpoint state first: `validate_checkpoint_state()`

### Rollback Fails

If rollback fails:

1. Check for uncommitted changes
2. Verify checkpoint exists
3. Check git repository state
4. Use `--hard-reset` only if working directory can be discarded

### Missing Checkpoint Logs

If checkpoint logs are missing:

1. Check session directory exists
2. Verify write permissions
3. Check for previous errors in session creation

## Related Documentation

- [Session Manager](SESSION_MANAGER.md) - Session lifecycle management
- [Checkpoint Schema](../schemas/checkpoints.schema.json) - JSON schema for checkpoint data
- [Architecture](ARCHITECTURE.md) - System architecture overview

## License

Part of the Maestro orchestration system. See project license for details.
