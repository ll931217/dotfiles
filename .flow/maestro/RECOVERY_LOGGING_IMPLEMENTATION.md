# Recovery Logging and Audit Trail Implementation

## Overview

This document describes the comprehensive recovery logging and audit trail system implemented for the Maestro Orchestrator's auto-recovery functionality.

## Implementation Details

### 1. New Data Structures

#### RecoveryAuditEntry
A comprehensive data structure that captures all details of a recovery attempt:

```python
@dataclass
class RecoveryAuditEntry:
    entry_id: str                          # Unique identifier for the entry
    timestamp: str                          # ISO timestamp of the attempt
    session_id: str                         # Recovery session identifier
    error_type: str                         # Type of error that triggered recovery
    strategy: str                           # Recovery strategy used
    attempt_number: int                     # Attempt number within the session
    success: bool                           # Whether the recovery was successful
    changes_made: List[str]                 # List of changes made during recovery
    files_modified: List[str]               # Files that were modified
    rollback_performed: bool                # Whether a rollback was performed
    next_action: str                        # Next action to take
    duration_seconds: float                 # Time taken for the attempt
    error_message: str                      # Original error message
    recovery_message: str                   # Recovery operation message
```

### 2. RecoveryAuditLogger Class

The `RecoveryAuditLogger` provides comprehensive audit trail functionality:

#### Key Methods

**Session Management**
- `start_session(session_id=None)`: Start a new recovery session
- `get_all_session_ids()`: Get all session IDs with entries

**Logging**
- `log_recovery_attempt(attempt, session_id, ...)`: Log a recovery attempt with full details
- `_write_entry_to_file(entry)`: Persist entry to JSONL file immediately

**Retrieval**
- `get_recovery_history(session_id)`: Get all audit entries for a session
- `get_recovery_statistics(session_id)`: Calculate comprehensive statistics

**Export**
- `export_audit_trail(session_id, format)`: Export to JSON or CSV
- `generate_recovery_report(session_id, output_path)`: Generate detailed report

**Cleanup**
- `clear_session(session_id)`: Clear specific session
- `clear_all_sessions()`: Clear all sessions

#### Features

1. **Immediate Persistence**: Audit entries are written to disk immediately using JSONL format
2. **Session-Based Organization**: Each recovery operation is organized into sessions
3. **Multiple Export Formats**: Support for JSON and CSV export
4. **Comprehensive Statistics**: Calculate success rates, strategy usage, error distribution, etc.

### 3. Integration with AutoRecoveryManager

The `AutoRecoveryManager` has been enhanced with audit logging:

#### New Initialization Parameters

```python
AutoRecoveryManager(
    ... existing parameters ...
    audit_dir=Path,              # Directory for audit files
    enable_audit_logging=True    # Enable/disable audit logging
)
```

#### New Methods

- `get_audit_trail(session_id)`: Get audit entries
- `export_audit_trail(session_id, format)`: Export audit trail
- `get_recovery_statistics(session_id)`: Get recovery statistics
- `generate_recovery_report(session_id, output_path)`: Generate report
- `start_new_session(session_id)`: Start new audit session
- `clear_audit_history(session_id)`: Clear audit history

#### Automatic Logging

All recovery attempts are automatically logged when audit logging is enabled:

1. Session is created automatically on first recovery attempt
2. Each attempt is logged with full context
3. Files modified and rollback status are tracked
4. Statistics are calculated in real-time

### 4. Recovery Statistics

The system calculates comprehensive statistics for each session:

```python
{
    "session_id": "session_abc123",
    "session_start": "2024-01-01T00:00:00Z",
    "total_attempts": 10,
    "successful_attempts": 7,
    "failed_attempts": 3,
    "success_rate": 70.0,
    "strategies_used": {
        "fix": 5,
        "retry": 3,
        "alternative": 2
    },
    "error_type_distribution": {
        "SyntaxError": 4,
        "ImportError": 3,
        "TypeError": 3
    },
    "total_duration_seconds": 15.5,
    "average_duration_seconds": 1.55,
    "files_modified_count": 8,
    "files_modified": ["file1.py", "file2.py", ...],
    "rollback_count": 1,
    "first_attempt_timestamp": "2024-01-01T00:00:00Z",
    "last_attempt_timestamp": "2024-01-01T00:00:10Z"
}
```

## Test Coverage

### Comprehensive Test Suite

The implementation includes 35 comprehensive tests covering:

1. **RecoveryAuditEntry Tests** (3 tests)
   - Entry creation and data structure
   - Dictionary conversion
   - JSON serialization

2. **RecoveryAuditLogger Tests** (15 tests)
   - Logger initialization
   - Session management
   - Recovery attempt logging
   - Multiple attempt handling
   - History retrieval
   - Export to JSON and CSV
   - Statistics calculation
   - Report generation
   - Session cleanup
   - File persistence

3. **AutoRecoveryManager Integration Tests** (11 tests)
   - Audit logging enable/disable
   - Automatic logging during recovery
   - Multiple attempt logging
   - Statistics retrieval
   - Export functionality
   - Report generation
   - Session management
   - Failed recovery logging

4. **Statistics Calculation Tests** (4 tests)
   - Success rate calculation
   - Duration statistics
   - Error type distribution
   - Files modified tracking

### Test Results

```
Ran 35 tests in 5.017s
OK
```

All tests pass successfully, including the original 33 auto-recovery tests.

## Usage Examples

### Basic Usage

```python
from auto_recovery import AutoRecoveryManager, Error

# Create manager with audit logging enabled
manager = AutoRecoveryManager(
    audit_dir=Path("/var/log/maestro/audit"),
    enable_audit_logging=True
)

# Attempt recovery (automatically logged)
error = Error(
    error_type="SyntaxError",
    message="Invalid syntax",
    source="linter"
)
result = manager.attempt_recovery(error, {})

# Get statistics
stats = manager.get_recovery_statistics()
print(f"Success rate: {stats['success_rate']}%")
```

### Advanced Usage

```python
# Start a named session
session_id = manager.start_new_session("my_recovery_session")

# Perform multiple recovery operations
for error in errors:
    manager.attempt_recovery(error, {})

# Generate comprehensive report
report_path = manager.generate_recovery_report()
print(f"Report saved to: {report_path}")

# Export to different formats
json_path = manager.export_audit_trail(format="json")
csv_path = manager.export_audit_trail(format="csv")

# Get detailed history
history = manager.get_audit_trail()
for entry in history:
    print(f"{entry['timestamp']}: {entry['strategy']} - {entry['success']}")
```

### Direct Logger Usage

```python
from auto_recovery import RecoveryAuditLogger, RecoveryAttempt, Error

# Create logger
logger = RecoveryAuditLogger(audit_dir=Path("/var/log/audit"))

# Start session
session_id = logger.start_session()

# Create and log attempt
error = Error(error_type="TestError", message="Test", source="test")
attempt = RecoveryAttempt(
    attempt_number=1,
    strategy="fix",
    success=True,
    error_before=error,
    error_after=None,
    changes_made=["Fixed syntax error"],
    timestamp=datetime.now(timezone.utc).isoformat(),
    duration_seconds=1.5,
    message="Recovery successful"
)

entry_id = logger.log_recovery_attempt(
    attempt,
    session_id,
    files_modified=["test.py"],
    rollback_performed=False,
    next_action="complete"
)

# Get statistics
stats = logger.get_recovery_statistics(session_id)
print(f"Total attempts: {stats['total_attempts']}")
print(f"Success rate: {stats['success_rate']}%")
```

## File Structure

```
.flow/maestro/
├── scripts/
│   └── auto_recovery.py          # Enhanced with audit logging
├── tests/
│   ├── test_recovery_logging.py  # Comprehensive test suite
│   └── test_auto_recovery.py     # Original tests (still passing)
└── RECOVERY_LOGGING_IMPLEMENTATION.md  # This document
```

## Key Features

1. **Comprehensive Logging**: Every recovery attempt is logged with full context
2. **Session Organization**: Recovery operations are organized into sessions
3. **Immediate Persistence**: Audit entries are written to disk immediately
4. **Multiple Export Formats**: Support for JSON and CSV
5. **Rich Statistics**: Calculate detailed statistics for each session
6. **Flexible Integration**: Can be enabled/disabled per instance
7. **Backward Compatible**: All existing functionality preserved
8. **Well Tested**: 35 comprehensive tests with 100% pass rate

## Benefits

1. **Debugging**: Complete audit trail for troubleshooting recovery issues
2. **Analytics**: Understand recovery patterns and success rates
3. **Compliance**: Maintain detailed records of all recovery operations
4. **Optimization**: Identify common failure patterns and optimize strategies
5. **Reporting**: Generate reports for review and analysis
6. **Transparency**: Full visibility into recovery operations

## Future Enhancements

Potential future improvements:

1. **Database Backend**: Option to store audit trail in a database
2. **Real-time Monitoring**: WebSocket or streaming API for live monitoring
3. **Advanced Analytics**: Machine learning for recovery optimization
4. **Alerting**: Automatic alerts for repeated failures
5. **Dashboard**: Web UI for visualizing recovery statistics
6. **Retention Policies**: Automatic cleanup of old audit entries
7. **Encryption**: Encrypt sensitive audit data
8. **Aggregation**: Aggregate statistics across multiple sessions

## Conclusion

The recovery logging and audit trail system provides comprehensive visibility into the auto-recovery process. It maintains a complete record of all recovery attempts, enables detailed analysis, and supports multiple export formats for integration with other systems.

The implementation is fully tested, backward compatible, and ready for production use.
