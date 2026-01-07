# Recovery Strategies

## Overview

The `recovery_strategies.py` module provides four core recovery strategies for handling failures during Maestro orchestration sessions:

1. **Retry with Backoff** - Exponential backoff for transient errors
2. **Alternative Approach** - Switch algorithm/pattern when implementation fails
3. **Rollback to Checkpoint** - Git-based rollback capability for critical failures
4. **Human Input Request** - Structured request for ambiguous situations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  RecoveryStrategies                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Retry with       │  │ Alternative      │                │
│  │ Backoff          │  │ Approach         │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Rollback to      │  │ Human Input      │                │
│  │ Checkpoint       │  │ Request          │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### 1. Retry with Exponential Backoff

```python
from recovery_strategies import RecoveryStrategies, RetryConfig

strategies = RecoveryStrategies()

# Simple retry
def flaky_operation():
    return subprocess.run(["pytest"], check=True)

result = strategies.retry_with_backoff(
    flaky_operation,
    operation_name="run tests"
)

if result.success:
    print(f"Success after {result.attempts_made} attempts")
else:
    print(f"Failed: {result.final_error}")

# Custom retry configuration
config = RetryConfig(
    max_attempts=5,
    base_delay_seconds=2.0,
    max_delay_seconds=60.0,
    exponential_base=2.0,
    jitter=True,
)

result = strategies.retry_with_backoff(
    flaky_operation,
    config=config,
    operation_name="run tests with custom config",
    retry_on=(subprocess.CalledProcessError, IOError),
)
```

### 2. Alternative Approach Selection

```python
# Get alternative approaches for a failure
result = strategies.try_alternative_approach(
    context={"task_type": "testing"},
    failure_info={"error": "AssertionError: test fails intermittently"}
)

if result.success:
    print(f"Recommended: {result.details['approach_name']}")
    print(f"Pattern: {result.details['implementation_pattern']}")
    print(f"Required changes: {result.details['required_changes']}")
```

Available failure types:
- `test_failure` - Test failures and assertion errors
- `implementation_failure` - Missing implementations and import errors
- `dependency_conflict` - Version conflicts and dependency issues

### 3. Rollback to Checkpoint

```python
from recovery_strategies import CheckpointType

# Create a checkpoint before risky operation
checkpoint = strategies.create_checkpoint(
    session_id="session-123",
    description="Before refactoring core module",
    phase="implement",
    checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
    state_snapshot={
        "tasks_completed": 5,
        "decisions_made": 2,
    }
)

# Perform risky operations...

# If something goes wrong, rollback
success = strategies.rollback_to_checkpoint(
    session_id="session-123",
    checkpoint_id=checkpoint.checkpoint_id,
)
```

Checkpoint types:
- `PHASE_COMPLETE` - After completing a phase
- `TASK_GROUP_COMPLETE` - After completing a task group
- `SAFE_STATE` - Known good state
- `PRE_RISKY_OPERATION` - Before risky operation
- `ERROR_RECOVERY` - After recovering from error
- `MANUAL` - Manually created checkpoint

### 4. Human Input Request

```python
# Request human input for ambiguous situations
selected = strategies.request_human_input(
    issue="Multiple design patterns available for this task",
    options=[
        "Use Factory Pattern",
        "Use Builder Pattern",
        "Use Prototype Pattern",
    ],
    default_option="Use Factory Pattern",
    requires_justification=True,
)

print(f"User selected: {selected}")
```

## Data Models

### RetryConfig

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
```

### RetryResult

```python
@dataclass
class RetryResult:
    success: bool
    attempts_made: int
    total_time_seconds: float
    final_error: Optional[str] = None
    result: Optional[Any] = None
```

### Checkpoint

```python
@dataclass
class Checkpoint:
    checkpoint_id: str
    commit_sha: str
    timestamp: str
    description: str
    phase: str
    checkpoint_type: CheckpointType
    commit_message: Optional[str] = None
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    rollback_used: bool = False
    rollback_count: int = 0
```

### RecoveryResult

```python
@dataclass
class RecoveryResult:
    strategy_used: RecoveryStrategyType
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recovered_at: str
```

## CLI Usage

The module can also be used from the command line:

```bash
# Create a checkpoint
python3 recovery_strategies.py checkpoint \
    --session-id abc-123 \
    --description "Before refactoring" \
    --phase implement \
    --type manual

# Rollback to checkpoint
python3 recovery_strategies.py rollback \
    --session-id abc-123 \
    --checkpoint-id cp-1234567890

# List alternative approaches for a failure type
python3 recovery_strategies.py approaches \
    --failure-type test_failure
```

## Testing

Run the comprehensive test suite:

```bash
python3 test_recovery_strategies.py
```

Tests cover:
- Exponential backoff calculations
- Jitter randomness
- Exception filtering
- Alternative approach selection
- Checkpoint creation and persistence
- Rollback functionality
- Human input interaction
- Integration workflows

## Integration with Session Manager

The recovery strategies integrate with the session manager to track error recovery:

```python
from session_manager import SessionManager
from recovery_strategies import RecoveryStrategies

session_mgr = SessionManager()
recovery = RecoveryStrategies()

# Create session
session = session_mgr.create_session("Implement feature X")

# Create checkpoint before work
checkpoint = recovery.create_checkpoint(
    session_id=session.session_id,
    description="Before implementation",
    phase="implement",
    checkpoint_type=CheckpointType.SAFE_STATE,
)

# Attempt work with retry
result = recovery.retry_with_backoff(
    lambda: implement_feature(),
    config=RetryConfig(max_attempts=3)
)

if not result.success:
    # Get alternative approaches
    alternatives = recovery.try_alternative_approach(
        context={"task": "implement_feature"},
        failure_info={"error": str(result.final_error)}
    )

    # Rollback if needed
    recovery.rollback_to_checkpoint(
        session_id=session.session_id,
        checkpoint_id=checkpoint.checkpoint_id,
    )

    # Update session statistics
    session_mgr.update_session(
        session.session_id,
        {
            "statistics": {
                "error_recovery_count": session.statistics.error_recovery_count + 1
            }
        }
    )
```

## File Structure

```
.flow/maestro/
├── scripts/
│   ├── recovery_strategies.py       # Main implementation
│   ├── test_recovery_strategies.py  # Comprehensive tests
│   └── RECOVERY_STRATEGIES.md       # This documentation
└── checkpoints/                      # Checkpoint data storage
    ├── {session-id}.json            # Per-session checkpoint logs
```

## Design Principles

1. **Separation of Concerns** - Each strategy is independent and can be used standalone
2. **Composability** - Strategies can be combined (e.g., retry → rollback → human input)
3. **Testability** - Comprehensive test coverage with mocked dependencies
4. **Type Safety** - Uses dataclasses and enums for clear data structures
5. **Observability** - Detailed logging and result tracking

## Error Handling

The recovery strategies follow this error handling flow:

```
┌──────────────┐
│ Try Operation│
└──────┬───────┘
       │
       ▼
  ┌─────────┐
  │ Success?│
  └────┬────┘
       │ No
       ▼
┌─────────────────┐
│ Is Transient?   │──Yes──► Retry with Backoff
└─────────────────┘
       │ No
       ▼
┌─────────────────┐
│ Has Alternative?│──Yes──► Try Alternative Approach
└─────────────────┘
       │ No
       ▼
┌─────────────────┐
│ Has Checkpoint? │──Yes──► Rollback to Checkpoint
└─────────────────┘
       │ No
       ▼
┌─────────────────┐
│ Is Ambiguous?   │──Yes──► Request Human Input
└─────────────────┘
       │ No
       ▼
  ┌──────────┐
  │ Fail     │
  └──────────┘
```

## Performance Considerations

- **Retry overhead**: Each retry attempt adds latency (configurable via backoff)
- **Checkpoint storage**: Checkpoints are stored as JSON (~1KB per checkpoint)
- **Git operations**: Rollback uses `git reset --hard` which is fast for small repos
- **Human input**: Blocks execution until user responds (use timeout to prevent hangs)

## Future Enhancements

Potential improvements for future versions:

1. **Automatic checkpoint creation** - Auto-create checkpoints at phase boundaries
2. **Parallel retry strategies** - Try multiple alternatives in parallel
3. **Machine learning approach selection** - Learn which approaches work best
4. **Distributed checkpoint storage** - Store checkpoints in S3/GCS for large teams
5. **Checkpoint compression** - Compress state snapshots for large checkpoints
6. **Async human input** - Non-blocking input requests with web UI
