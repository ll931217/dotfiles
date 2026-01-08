# Checkpoint Rollback - Quick Reference

## TL;DR

Rollback with validation and logging now returns a `RollbackOperation` object instead of `bool`.

## Basic Usage

```python
from checkpoint_manager import CheckpointManager

manager = CheckpointManager()

# Rollback to a checkpoint
rollback_op = manager.rollback_to_checkpoint(
    session_id="session-uuid",
    checkpoint_id="checkpoint-uuid",
    hard_reset=True,  # or False for --mixed
)

# Check if successful
if rollback_op.success:
    print("✅ Rollback successful")
    print(f"Restored to: {rollback_op.checkpoint_description}")
    print(f"State: {rollback_op.state_snapshot_restored}")
else:
    print("❌ Rollback failed")
    print(f"Errors: {rollback_op.validation_errors}")
```

## RollbackOperation Fields

| Field | Type | Description |
|-------|------|-------------|
| `operation_id` | str | Unique ID for this rollback operation |
| `timestamp` | str | ISO 8601 timestamp of rollback |
| `session_id` | str | Session UUID |
| `checkpoint_id` | str | Target checkpoint UUID |
| `checkpoint_description` | str | Human-readable checkpoint name |
| `checkpoint_sha` | str | Git commit SHA of checkpoint |
| `rollback_mode` | str | "hard" or "mixed" |
| `pre_rollback_head` | str | Git SHA before rollback |
| `post_rollback_head` | str | Git SHA after rollback |
| `validation_passed` | bool | Whether post-rollback validation passed |
| `state_snapshot_restored` | StateSnapshot? | State at checkpoint time |
| `validation_errors` | List[str] | Validation errors (if any) |
| `validation_warnings` | List[str] | Validation warnings (if any) |
| `success` | bool | Overall success status |
| `error_message` | str? | Error message if failed |

## CLI Commands

### Create Checkpoint
```bash
python checkpoint_manager.py create \
  --session-id <uuid> \
  --description "Before risky changes" \
  --phase implement \
  --checkpoint-type pre_risky_operation
```

### Rollback to Checkpoint
```bash
python checkpoint_manager.py rollback \
  --session-id <uuid> \
  --checkpoint-id <uuid> \
  --hard-reset
```

### View Rollback History
```bash
python checkpoint_manager.py rollback_history \
  --session-id <uuid> \
  --output pretty
```

### List Checkpoints
```bash
python checkpoint_manager.py list \
  --session-id <uuid>
```

## Validation Rules

### Pre-Rollback Checks
✅ Repository must be clean (no uncommitted changes)
✅ Checkpoint must exist
✅ Git must be available

### Post-Rollback Checks
✅ HEAD SHA must match checkpoint SHA
⚠️ Working directory should be clean (warning if not)
⚠️ Tests should pass (warning if not)

## Error Handling

### Uncommitted Changes
```python
try:
    rollback_op = manager.rollback_to_checkpoint(session_id, checkpoint_id)
except ValueError as e:
    if "uncommitted changes" in str(e):
        print("Commit or stash changes first")
    else:
        print(f"Error: {e}")
```

### Checkpoint Not Found
```python
from checkpoint_manager import CheckpointManager, FileNotFoundError

manager = CheckpointManager()

try:
    rollback_op = manager.rollback_to_checkpoint(session_id, checkpoint_id)
except FileNotFoundError:
    print("Checkpoint not found")
```

### Validation Failed
```python
rollback_op = manager.rollback_to_checkpoint(session_id, checkpoint_id)

if not rollback_op.validation_passed:
    print("Validation failed:")
    for error in rollback_op.validation_errors:
        print(f"  ❌ {error}")
    for warning in rollback_op.validation_warnings:
        print(f"  ⚠️  {warning}")
```

## Rollback History

### Get All Rollback Operations
```python
history = manager.get_rollback_history(session_id)

for op in history:
    print(f"{op.timestamp}: {op.checkpoint_description}")
    print(f"  Mode: {op.rollback_mode}")
    print(f"  Success: {op.success}")
    print(f"  Validated: {op.validation_passed}")
```

### Analyze Failed Rollbacks
```python
history = manager.get_rollback_history(session_id)

failed = [op for op in history if not op.success]

for op in failed:
    print(f"{op.timestamp}: {op.error_message}")
    print(f"  Errors: {op.validation_errors}")
```

### Count Rollbacks by Checkpoint
```python
from collections import Counter

history = manager.get_rollback_history(session_id)

checkpoint_counts = Counter(op.checkpoint_id for op in history)

for checkpoint_id, count in checkpoint_counts.most_common():
    print(f"{checkpoint_id}: {count} rollback(s)")
```

## StateSnapshot

### Access Restored State
```python
rollback_op = manager.rollback_to_checkpoint(session_id, checkpoint_id)

if rollback_op.state_snapshot_restored:
    state = rollback_op.state_snapshot_restored
    print(f"Tasks completed: {state.tasks_completed}")
    print(f"Files modified: {state.files_modified}")
    print(f"Tests passing: {state.tests_passing}")
    print(f"Tests failing: {state.tests_failing}")
```

### Create Checkpoint with State
```python
from checkpoint_manager import CheckpointManager, StateSnapshot, CheckpointPhase

manager = CheckpointManager()

# Capture current state
snapshot = StateSnapshot(
    tasks_completed=10,
    decisions_made=5,
    files_modified=15,
    files_created=8,
    tests_passing=20,
    tests_failing=0,
)

# Create checkpoint with state
checkpoint = manager.create_checkpoint(
    session_id=session_id,
    description="Feature implementation complete",
    phase=CheckpointPhase.IMPLEMENT,
    state_snapshot=snapshot,
)
```

## Common Patterns

### Safe Experimentation
```python
# Create checkpoint before risky changes
checkpoint = manager.create_checkpoint(
    session_id,
    "Before refactoring",
    CheckpointPhase.IMPLEMENT,
    CheckpointType.PRE_RISKY_OPERATION,
)

try:
    # Do risky work
    risky_operation()
except Exception as e:
    # Rollback on failure
    rollback_op = manager.rollback_to_checkpoint(
        session_id,
        checkpoint.checkpoint_id,
        hard_reset=True,
    )
    if rollback_op.success:
        print("Recovered successfully")
    raise
```

### Recovery with Analysis
```python
def recover_from_failure(session_id, last_known_good_checkpoint_id):
    # Rollback to last known good state
    rollback_op = manager.rollback_to_checkpoint(
        session_id,
        last_known_good_checkpoint_id,
        hard_reset=True,
    )

    # Analyze the rollback
    if not rollback_op.success:
        logger.error(f"Rollback failed: {rollback_op.error_message}")
        return False

    # Check state
    if rollback_op.state_snapshot_restored:
        state = rollback_op.state_snapshot_restored
        logger.info(f"Restored to state: {state.tasks_completed} tasks complete")

    # Verify validation
    if not rollback_op.validation_passed:
        logger.warning(f"Validation warnings: {rollback_op.validation_warnings}")

    return True
```

## Troubleshooting

### "Cannot rollback with uncommitted changes"
**Solution:** Commit or stash changes first
```bash
git status
git commit -am "Save current work"
# or
git stash
```

### "Post-rollback validation failed"
**Cause:** HEAD doesn't match checkpoint SHA
**Check:**
```python
print(f"Expected: {rollback_op.checkpoint_sha}")
print(f"Got: {rollback_op.post_rollback_head}")
```

### Rollback history is empty
**Cause:** No rollbacks performed yet for this session
**Check:**
```python
checkpoints = manager.list_checkpoints(session_id)
print(f"Available checkpoints: {len(checkpoints)}")
```

## Best Practices

1. **Create checkpoints before risky operations**
   ```python
   checkpoint = manager.create_checkpoint(
       session_id,
       "Before database migration",
       CheckpointPhase.IMPLEMENT,
       CheckpointType.PRE_RISKY_OPERATION,
   )
   ```

2. **Use descriptive checkpoint descriptions**
   ```python
   # Good
   description="After implementing user auth, tests passing"

   # Bad
   description="checkpoint 1"
   ```

3. **Capture state snapshots**
   ```python
   snapshot = StateSnapshot(
       tasks_completed=len(completed_tasks),
       tests_passing=passing_tests,
       tests_failing=failing_tests,
   )
   ```

4. **Handle validation warnings**
   ```python
   if rollback_op.validation_warnings:
       logger.warning(f"Rollback warnings: {rollback_op.validation_warnings}")
   ```

5. **Log rollback operations**
   ```python
   logger.info(
       f"Rollback {rollback_op.operation_id}: "
       f"{rollback_op.checkpoint_description} "
       f"({'success' if rollback_op.success else 'failed'})"
   )
   ```

## Integration with ErrorHandler

```python
from error_handler import ErrorHandler, ErrorCategory

error_handler = ErrorHandler()
checkpoint_manager = CheckpointManager()

# Create checkpoint before risky operation
checkpoint = checkpoint_manager.create_checkpoint(
    session_id,
    "Before risky operation",
    CheckpointPhase.IMPLEMENT,
    CheckpointType.PRE_RISKY_OPERATION,
)

try:
    risky_operation()
except CriticalError as e:
    # Log error
    error_handler.log_error(
        session_id,
        ErrorCategory.EXECUTION,
        str(e),
        context={"checkpoint_id": checkpoint.checkpoint_id},
    )

    # Attempt rollback
    rollback_op = checkpoint_manager.rollback_to_checkpoint(
        session_id,
        checkpoint.checkpoint_id,
        hard_reset=True,
    )

    if rollback_op.success:
        logger.info("Recovered from critical error")
    else:
        logger.error(f"Recovery failed: {rollback_op.error_message}")
```

## Resources

- Full implementation: `.flow/maestro/scripts/checkpoint_manager.py`
- Unit tests: `.flow/maestro/scripts/test_checkpoint_manager.py`
- Detailed summary: `.flow/maestro/scripts/ROLLBACK_ENHANCEMENT_SUMMARY.md`
