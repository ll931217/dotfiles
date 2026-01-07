# Session Lifecycle Manager

## Overview

The Session Lifecycle Manager provides comprehensive session management for Maestro orchestration, including creation, state transitions, persistence, and querying capabilities.

## Architecture

### Components

- **SessionManager**: Main class managing all session operations
- **Session**: Dataclass representing a session with all metadata
- **SessionStatus**: Enum defining all valid session states
- **SessionPhase**: Enum defining execution phases
- **GitContext**: Captures git repository state
- **PRDReference**: Links to generated PRD documents
- **SessionStatistics**: Tracks execution metrics
- **SessionConfiguration**: Stores session settings

### State Machine

```
initializing -> planning -> generating_tasks -> implementing
    -> validating -> generating_report -> completed
                                              |
                                              v
                                           failed

    (paused state available from most states)
```

## File Structure

```
.flow/maestro/
├── sessions/
│   └── <session-id>/
│       └── metadata.json
├── scripts/
│   ├── session_manager.py       # Main implementation
│   ├── test_session_manager.py  # Unit tests
│   └── example_session_manager.py # Usage examples
└── schemas/
    └── session-metadata.schema.json # JSON Schema
```

## Session States

| State | Description | Terminal |
|-------|-------------|----------|
| `initializing` | Session created, initializing | No |
| `planning` | PRD generation phase | No |
| `generating_tasks` | Breaking down tasks | No |
| `implementing` | Executing tasks | No |
| `validating` | Testing and validation | No |
| `generating_report` | Creating completion report | No |
| `completed` | Successfully finished | Yes |
| `failed` | Session failed | Yes |
| `paused` | User paused session | No |

## API Reference

### SessionManager

#### `__init__(repo_root: Optional[str] = None)`

Initialize the session manager.

```python
manager = SessionManager()  # Auto-detect repo root
manager = SessionManager("/path/to/repo")  # Explicit path
```

#### `create_session(feature_request: str, configuration: Optional[SessionConfiguration] = None) -> Session`

Create a new session.

```python
session = manager.create_session(
    "Add user authentication",
    configuration=SessionConfiguration(
        max_iterations=3,
        timeout_minutes=120,
        auto_checkpoint=True,
    ),
)
```

#### `get_session(session_id: str) -> Session`

Retrieve a session by ID.

```python
session = manager.get_session(session_id)
```

#### `update_session(session_id: str, updates: Dict[str, Any]) -> Session`

Update session fields.

```python
session = manager.update_session(
    session_id,
    {
        "current_phase": SessionPhase.IMPLEMENT,
        "statistics": {
            "total_tasks": 10,
            "completed_tasks": 5,
        },
    },
)
```

#### `transition_state(session_id: str, new_state: SessionStatus) -> Session`

Transition session to a new state.

```python
session = manager.transition_state(
    session_id,
    SessionStatus.IMPLEMENTING,
)
```

#### `query_sessions(...) -> List[Session]`

Query sessions with filters.

```python
# All sessions
sessions = manager.query_sessions()

# By status
planning = manager.query_sessions(status=SessionStatus.PLANNING)

# By branch
main_branch = manager.query_sessions(branch="main")

# By date range
recent = manager.query_sessions(
    created_after="2026-01-01T00:00:00Z",
    created_before="2026-01-31T23:59:59Z",
)

# With limit
last_10 = manager.query_sessions(limit=10)
```

#### `list_active_sessions() -> List[Session]`

Get all non-terminal sessions.

```python
active = manager.list_active_sessions()
```

#### `get_recent_sessions(count: int = 10) -> List[Session]`

Get most recent sessions.

```python
recent = manager.get_recent_sessions(count=5)
```

#### `delete_session(session_id: str) -> None`

Delete a session.

```python
manager.delete_session(session_id)
```

## Data Models

### Session

```python
@dataclass
class Session:
    session_id: str                              # UUID v4
    feature_request: str                          # User's request
    status: SessionStatus                         # Current state
    created_at: str                               # ISO 8601 timestamp
    git_context: GitContext                       # Git state
    current_phase: Optional[SessionPhase]         # Execution phase
    updated_at: Optional[str]                     # Last update
    completed_at: Optional[str]                   # Completion time
    prd_reference: Optional[PRDReference]         # PRD link
    statistics: SessionStatistics                 # Metrics
    configuration: SessionConfiguration           # Settings
```

### GitContext

```python
@dataclass
class GitContext:
    branch: str                # Branch name
    commit: str                # Commit SHA
    repo_root: str             # Repository path
    is_worktree: bool          # Worktree flag
    worktree_name: Optional[str] # Worktree name
```

### SessionStatistics

```python
@dataclass
class SessionStatistics:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    decisions_made: int = 0
    checkpoints_created: int = 0
    error_recovery_count: int = 0
    duration_seconds: float = 0.0
```

### SessionConfiguration

```python
@dataclass
class SessionConfiguration:
    max_iterations: int = 3
    timeout_minutes: int = 120
    auto_checkpoint: bool = True
    error_recovery_enabled: bool = True
```

## Usage Examples

### Basic Workflow

```python
from session_manager import SessionManager, SessionStatus

# Initialize
manager = SessionManager()

# Create session
session = manager.create_session("Build REST API")

# Transition through states
manager.transition_state(session.session_id, SessionStatus.PLANNING)
manager.transition_state(session.session_id, SessionStatus.GENERATING_TASKS)
manager.transition_state(session.session_id, SessionStatus.IMPLEMENTING)

# Update statistics
manager.update_session(
    session.session_id,
    {"statistics": {"total_tasks": 10, "completed_tasks": 5}},
)

# Complete session
manager.transition_state(session.session_id, SessionStatus.COMPLETED)
```

### Pause and Resume

```python
# Pause during execution
manager.transition_state(session.session_id, SessionStatus.PAUSED)

# Later, resume
manager.transition_state(session.session_id, SessionStatus.IMPLEMENTING)
```

### Query Sessions

```python
# Get all planning sessions
planning = manager.query_sessions(status=SessionStatus.PLANNING)

# Get active sessions
active = manager.list_active_sessions()

# Get recent sessions
recent = manager.get_recent_sessions(count=5)

# Filter by branch
main_branch = manager.query_sessions(branch="main")
```

### PRD Tracking

```python
# Attach PRD to session
manager.update_session(
    session.session_id,
    {
        "prd_reference": {
            "filename": "prd.md",
            "path": "/path/to/prd.md",
            "version": "1.0.0",
        },
    },
)
```

## CLI Usage

The session manager includes a CLI for basic operations:

```bash
# Create session
python3 session_manager.py create --feature-request "Add authentication"

# Get session
python3 session_manager.py get --session-id <uuid> --output pretty

# List sessions
python3 session_manager.py list --branch main --limit 10 --output pretty

# Transition state
python3 session_manager.py transition --session-id <uuid> --status planning

# Delete session
python3 session_manager.py delete --session-id <uuid>
```

## State Transitions

### Valid Transitions

Each state has specific allowed transitions:

- **initializing**: planning, failed, paused
- **planning**: generating_tasks, failed, paused
- **generating_tasks**: implementing, failed, paused
- **implementing**: validating, failed, paused
- **validating**: generating_report, implementing, failed, paused
- **generating_report**: completed, failed, paused
- **completed**: (terminal)
- **failed**: (terminal)
- **paused**: planning, generating_tasks, implementing, validating, generating_report, failed, completed

### Transition Validation

The manager validates all transitions:

```python
# This will raise ValueError
manager.transition_state(
    session_id,
    SessionStatus.COMPLETED  # Can't skip to completed
)
```

## Persistence

Sessions are persisted as JSON files following the schema in
`.flow/maestro/schemas/session-metadata.schema.json`.

### File Structure

```
.flow/maestro/sessions/<session-id>/metadata.json
```

### Example Metadata

```json
{
  "session_id": "3f01b541-5cc9-47a7-9f8b-d884159c705f",
  "feature_request": "Add user authentication",
  "status": "implementing",
  "created_at": "2026-01-07T13:02:57.119275Z",
  "updated_at": "2026-01-07T13:03:15.123456Z",
  "current_phase": "implement",
  "git_context": {
    "branch": "feature/auth",
    "commit": "abc123def456",
    "repo_root": "/path/to/repo",
    "is_worktree": true,
    "worktree_name": "feature-auth"
  },
  "statistics": {
    "total_tasks": 10,
    "completed_tasks": 5,
    "decisions_made": 3
  },
  "configuration": {
    "max_iterations": 3,
    "timeout_minutes": 120
  }
}
```

## Testing

Run the unit tests:

```bash
cd .flow/maestro/scripts
python3 -m unittest test_session_manager -v
```

Run the examples:

```bash
python3 example_session_manager.py
```

## Error Handling

### FileNotFoundError

Raised when session doesn't exist:

```python
try:
    session = manager.get_session("nonexistent")
except FileNotFoundError:
    print("Session not found")
```

### ValueError

Raised for invalid transitions or updates:

```python
try:
    manager.transition_state(session_id, invalid_state)
except ValueError as e:
    print(f"Invalid transition: {e}")
```

## Best Practices

1. **Always check return values**: Session methods return updated Session objects
2. **Use type hints**: The API includes full type annotations
3. **Handle exceptions**: Wrap operations in try/except for robustness
4. **Query efficiently**: Use filters to limit query results
5. **Clean up**: Delete old sessions to manage disk space

## Integration with Maestro

The session manager integrates with Maestro workflows:

1. **Plan Phase**: Create session, attach PRD
2. **Generate Tasks**: Transition to generating_tasks
3. **Implement**: Update statistics during task execution
4. **Validate**: Transition through validation
5. **Cleanup**: Generate report, complete session

## Future Enhancements

Potential improvements:

- Session search by feature request content
- Session export/import
- Session templates
- Multi-repo session tracking
- Session metrics dashboard
- Automatic cleanup of old sessions
