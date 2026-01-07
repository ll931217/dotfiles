# Session Manager Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Maestro Orchestrator                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Session Manager                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │   Session     │  │   Session     │  │   Session     │        │
│  │   Manager     │  │   Manager     │  │   Manager     │        │
│  │   Methods     │  │   Methods     │  │   Methods     │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                         Core Methods                              │
│                                                                   │
│  • create_session()      • get_session()                         │
│  • update_session()      • delete_session()                      │
│  • transition_state()    • query_sessions()                      │
│  • list_active_sessions() • get_recent_sessions()                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Models                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Session    │  │ GitContext  │  │  PRDRef     │              │
│  │             │  │             │  │             │              │
│  │ • id        │  │ • branch    │  │ • filename  │              │
│  │ • status    │  │ • commit    │  │ • path      │              │
│  │ • phase     │  │ • repo_root │  │ • version   │              │
│  │ • stats     │  │ • worktree  │  │             │              │
│  │ • config    │  │             │  │             │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Statistics  │  │ Config      │                               │
│  │             │  │             │                               │
│  │ • tasks     │  │ • max_iter  │                               │
│  │ • decisions │  │ • timeout   │                               │
│  │ • errors    │  │ • checkpoint│                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Persistence Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  .flow/maestro/sessions/                                         │
│      ├── <session-id>/                                           │
│      │   └── metadata.json                                       │
│      ├── <session-id>/                                           │
│      │   └── metadata.json                                       │
│      └── ...                                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## State Machine

```
                    ┌──────────────────┐
                    │  initializing     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     planning      │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │   generating_tasks       │
              └────────┬─────────────────┘
                       │
                       ▼
              ┌──────────────────────────┐
              │     implementing         │◄────────────┐
              └────────┬─────────────────┘             │
                       │                              │
                       ▼                              │
              ┌──────────────────────────┐             │
              │      validating          │─────────────┘
              └────────┬─────────────────┘
                       │
                       ▼
              ┌──────────────────────────┐
              │   generating_report      │
              └────────┬─────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │         completed            │  (terminal)
        └──────────────────────────────┘


    (paused state available from all non-terminal states)

         ┌──────────────────┐
         │      failed      │  (terminal)
         └──────────────────┘
```

## Class Hierarchy

```
SessionManager
    │
    ├── Session (dataclass)
    │   ├── session_id: str
    │   ├── feature_request: str
    │   ├── status: SessionStatus
    │   ├── current_phase: SessionPhase
    │   ├── git_context: GitContext
    │   ├── prd_reference: PRDReference
    │   ├── statistics: SessionStatistics
    │   └── configuration: SessionConfiguration
    │
    ├── SessionStatus (Enum)
    │   ├── INITIALIZING
    │   ├── PLANNING
    │   ├── GENERATING_TASKS
    │   ├── IMPLEMENTING
    │   ├── VALIDATING
    │   ├── GENERATING_REPORT
    │   ├── COMPLETED
    │   ├── FAILED
    │   └── PAUSED
    │
    ├── SessionPhase (Enum)
    │   ├── PLAN
    │   ├── GENERATE_TASKS
    │   ├── IMPLEMENT
    │   ├── VALIDATE
    │   └── CLEANUP
    │
    ├── GitContext (dataclass)
    ├── PRDReference (dataclass)
    ├── SessionStatistics (dataclass)
    └── SessionConfiguration (dataclass)
```

## Method Flow Diagrams

### Session Creation Flow

```
user calls create_session()
        │
        ▼
generate UUID v4
        │
        ▼
capture git context
        │
        ▼
create Session object
        │
        ▼
create session directory
        │
        ▼
save metadata.json
        │
        ▼
return Session object
```

### State Transition Flow

```
user calls transition_state()
        │
        ▼
load session from disk
        │
        ▼
check transition validity
        │
        ├── valid ──▶ set new state
        │              │
        │              ├── terminal ──▶ set completed_at
        │              │
        │              ▼
        │         update timestamp
        │              │
        │              ▼
        │         save to disk
        │              │
        │              ▼
        │         return updated Session
        │
        └── invalid ──▶ raise ValueError
```

### Query Flow

```
user calls query_sessions()
        │
        ▼
iterate session directories
        │
        ▼
load each metadata.json
        │
        ▼
apply filters
        │
        ├── status match?
        ├── phase match?
        ├── date range match?
        └── branch match?
        │
        ▼
sort by created_at DESC
        │
        ▼
apply limit
        │
        ▼
return List[Session]
```

## Data Flow

### Writing Data

```
Application
    │
    │ Session object
    ▼
SessionManager.update_session()
    │
    │ to_dict()
    ▼
JSON serialization
    │
    │ metadata.json
    ▼
File System
```

### Reading Data

```
File System
    │
    │ metadata.json
    ▼
JSON deserialization
    │
    │ dict
    ▼
SessionManager._dict_to_session()
    │
    │ Session object
    ▼
Application
```

## Error Handling

```
┌─────────────────────────────────────────┐
│           Error Handling                │
├─────────────────────────────────────────┤
│                                          │
│  FileNotFoundError                       │
│  ├── Session not found                  │
│  ├── Metadata file missing              │
│  └── Session directory missing          │
│                                          │
│  ValueError                              │
│  ├── Invalid state transition           │
│  ├── Invalid field name                 │
│  └── Invalid enum value                 │
│                                          │
│  JSONDecodeError                         │
│  ├── Corrupted metadata                 │
│  └── Invalid JSON format                │
│                                          │
└─────────────────────────────────────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │     Git     │  │  File Sys   │  │   Schema    │         │
│  │             │  │             │  │  Validator  │         │
│  │ • branch    │  │ • sessions/ │  │             │         │
│  │ • commit    │  │ • metadata  │  │ • JSON      │         │
│  │ • worktree  │  │             │  │   Schema    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┴────────────────┘                 │
│                          │                                  │
│                          ▼                                  │
│              ┌───────────────────────┐                     │
│              │   Session Manager     │                     │
│              └───────────────────────┘                     │
│                          │                                  │
│         ┌────────────────┴────────────────┐                │
│         │                                  │                │
│         ▼                                  ▼                │
│  ┌─────────────┐                    ┌─────────────┐        │
│  │   Plan      │                    │  Implement  │        │
│  │   Phase     │                    │   Phase     │        │
│  └─────────────┘                    └─────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

```
┌─────────────────────────────────────────────────────────────┐
│              Performance Metrics                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Operation              Time Complexity    Space             │
│  ──────────────────     ────────────────  ──────────────   │
│  create_session         O(1)              O(1)              │
│  get_session            O(1)              O(1)              │
│  update_session         O(1)              O(1)              │
│  transition_state       O(1)              O(1)              │
│  query_sessions         O(n)              O(k)              │
│  delete_session         O(1)              O(1)              │
│                                                              │
│  n = total sessions                                         │
│  k = result set size                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

```
┌─────────────────────────────────────────────────────────────┐
│              Security Measures                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Path Traversal Prevention                               │
│     • Session IDs validated as UUID                         │
│     • No relative paths allowed                             │
│     • Session directory sandboxing                          │
│                                                              │
│  2. Input Validation                                        │
│     • Schema validation on write                            │
│     • Type checking on all fields                           │
│     • Enum validation for status/phase                      │
│                                                              │
│  3. State Transition Validation                             │
│     • Whitelist-based transitions                           │
│     • No arbitrary state changes                            │
│     • Terminal state protection                             │
│                                                              │
│  4. Error Handling                                          │
│     • No sensitive data in exceptions                       │
│     • Graceful degradation                                 │
│     • Atomic file operations                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
