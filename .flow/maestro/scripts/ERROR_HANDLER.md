# ErrorHandler Documentation

## Overview

The ErrorHandler is a comprehensive error detection, classification, and recovery system for the Maestro Orchestrator. It automatically detects errors from subprocess output, classifies them by severity and type, and selects appropriate recovery strategies.

## Features

- **Error Detection**: Automatically detects errors from subprocess output, test failures, and file system issues
- **Error Classification**: Classifies errors as transient, permanent, or ambiguous
- **Recovery Strategy Selection**: Intelligently selects the best recovery strategy based on error type and context
- **Retry with Backoff**: Implements exponential backoff for transient errors
- **Checkpoint Rollback**: Supports rollback to previous checkpoints for permanent errors
- **Human Input Escalation**: Escalates to human input when recovery options are exhausted
- **Error Logging**: Maintains a log of all errors with summaries and statistics

## API Reference

### ErrorHandler Class

```python
handler = ErrorHandler(session_id="optional-session-id")
```

#### Methods

##### `detect_error(output, source, exit_code, context)`

Detects an error from output or exit code.

**Parameters:**
- `output` (str): Output string to analyze
- `source` (str): Source of the output (subprocess, test, filesystem, etc.)
- `exit_code` (int, optional): Process exit code
- `context` (dict, optional): Additional context about the error

**Returns:** `Error` object if error detected, `None` otherwise

**Example:**
```python
error = handler.detect_error(
    output="Operation timed out after 30s",
    source="subprocess",
    exit_code=124,
)
```

##### `classify_error(error)`

Classifies an error into a category.

**Parameters:**
- `error` (Error): Error object to classify

**Returns:** `ErrorCategory` enum value

**Example:**
```python
category = handler.classify_error(error)
# Returns: ErrorCategory.TRANSIENT, PERMANENT, or AMBIGUOUS
```

##### `select_recovery_strategy(error, context)`

Selects appropriate recovery strategy for an error.

**Parameters:**
- `error` (Error): Error object
- `context` (dict, optional): Additional context for strategy selection
  - `retry_count`: Current retry attempt number
  - `has_checkpoint`: Whether a checkpoint is available
  - `can_skip`: Whether the error can be skipped

**Returns:** `RecoveryStrategy` enum value

**Example:**
```python
strategy = handler.select_recovery_strategy(
    error,
    context={"retry_count": 2, "has_checkpoint": True},
)
```

##### `execute_recovery(strategy, context)`

Executes a recovery strategy.

**Parameters:**
- `strategy` (RecoveryStrategy): Recovery strategy to execute
- `context` (dict): Context containing:
  - `error`: The original error object
  - `retry_count`: Current retry attempt number
  - `command`: Command to retry (for retry strategy)
  - `checkpoint_id`: Checkpoint to rollback to (for rollback strategy)

**Returns:** `RecoveryResult` object

**Example:**
```python
result = handler.execute_recovery(
    RecoveryStrategy.RETRY_WITH_BACKOFF,
    context={
        "error": error,
        "retry_count": 0,
        "command": "pytest tests/",
    },
)
```

##### `handle_subprocess_result(result, command, context)`

Convenience method to handle subprocess results.

**Parameters:**
- `result` (subprocess.CompletedProcess): Subprocess result
- `command` (str): Command that was executed
- `context` (dict, optional): Additional context

**Returns:** Tuple of (Error or None, RecoveryResult or None)

**Example:**
```python
result = subprocess.run(["npm", "install"], capture_output=True)
error, recovery = handler.handle_subprocess_result(result, "npm install")
```

##### `get_error_summary()`

Gets a summary of all errors encountered.

**Returns:** Dictionary with error statistics and recent errors

**Example:**
```python
summary = handler.get_error_summary()
# {
#     "total_errors": 5,
#     "by_category": {"transient": 3, "permanent": 2},
#     "by_type": {"timeout": 2, "syntax_error": 1, ...},
#     "recent_errors": [...]
# }
```

##### `save_error_log(filepath)`

Saves error log to file.

**Parameters:**
- `filepath` (Path, optional): Filepath to save to. Defaults to session directory.

**Returns:** Path where error log was saved

**Example:**
```python
log_path = handler.save_error_log()
```

## Error Categories

### Transient Errors

Temporary errors that can be resolved by retrying.

**Examples:**
- Timeouts
- Network errors
- Rate limiting
- Temporary resource unavailability

**Recovery Strategy:** `RETRY_WITH_BACKOFF`

### Permanent Errors

Errors that require code changes or intervention.

**Examples:**
- Syntax errors
- Import errors
- File not found
- Permission denied
- Missing dependencies

**Recovery Strategy:** `ROLLBACK_TO_CHECKPOINT` or `ALTERNATIVE_APPROACH`

### Ambiguous Errors

Errors where the cause is unclear.

**Examples:**
- Generic exceptions
- Unknown error types
- Conflicting information

**Recovery Strategy:** `REQUEST_HUMAN_INPUT` or `SKIP_AND_CONTINUE`

## Error Types

The ErrorHandler recognizes specific error types for targeted handling:

| Error Type | Category | Recovery Strategy |
|------------|----------|-------------------|
| `TIMEOUT` | Transient | Retry with backoff |
| `NETWORK` | Transient | Retry with backoff |
| `RATE_LIMITED` | Transient | Retry with backoff |
| `SYNTAX_ERROR` | Permanent | Alternative approach or rollback |
| `IMPORT_ERROR` | Permanent | Install dependencies or fix imports |
| `FILE_NOT_FOUND` | Permanent | Create file or fix path |
| `PERMISSION_DENIED` | Permanent | Fix permissions |
| `DEPENDENCY_MISSING` | Permanent | Install dependencies |
| `LOGIC_ERROR` | Permanent | Alternative approach |
| `CONFIGURATION_ERROR` | Permanent | Fix configuration |
| `GENERIC_EXCEPTION` | Ambiguous | Request human input |

## Recovery Strategies

### RETRY_WITH_BACKOFF

Retry the operation with exponential backoff delay.

**Configuration:**
- `max_retries`: Maximum number of retry attempts (default: 3)
- `base_delay`: Base delay in seconds (default: 1.0)
- `max_delay`: Maximum delay in seconds (default: 60.0)

**Delay Calculation:**
```
delay = min(base_delay * (2 ** retry_count), max_delay)
```

**Example:**
- Retry 1: 1.0s delay
- Retry 2: 2.0s delay
- Retry 3: 4.0s delay
- Retry 4: 8.0s delay (up to max_delay)

### ALTERNATIVE_APPROACH

Try a different implementation approach.

**When to use:**
- Permanent errors without available checkpoint
- Implementation failures
- Code changes required

**Next Action:** `try_alternative`

### ROLLBACK_TO_CHECKPOINT

Rollback to a previous checkpoint.

**When to use:**
- Permanent errors with available checkpoint
- Critical failures
- Unrecoverable state

**Next Action:** `rollback_to_checkpoint:{checkpoint_id}`

### REQUEST_HUMAN_INPUT

Request human intervention to resolve the error.

**When to use:**
- Ambiguous errors
- Unclear error cause
- Recovery options exhausted

**Next Action:** `wait_for_human_input`

### SKIP_AND_CONTINUE

Skip the error and continue with next task.

**When to use:**
- Non-critical errors
- Optional operations
- Errors that don't block progress

**Next Action:** `continue_to_next_task`

### ESCALATE

Escalate after exhausting recovery options.

**When to use:**
- Retries exhausted
- No other strategy applies
- Critical blocking issue

**Next Action:** `escalate_to_human`

## Usage Examples

### Example 1: Basic Error Detection

```python
from error_handler import ErrorHandler

handler = ErrorHandler()

# Detect error from output
error = handler.detect_error("Operation timed out after 30s")

if error:
    print(f"Error: {error.error_type.value}")
    print(f"Category: {error.category.value}")
    print(f"Suggestion: {error.suggestion}")
```

### Example 2: Subprocess Handling

```python
import subprocess
from error_handler import ErrorHandler

handler = ErrorHandler()

# Run command
result = subprocess.run(
    ["npm", "install"],
    capture_output=True,
)

# Handle result
error, recovery = handler.handle_subprocess_result(result, "npm install")

if error:
    print(f"Error: {error.message}")
    print(f"Recovery: {recovery.strategy.value}")
    print(f"Next: {recovery.next_action}")
```

### Example 3: Retry with Backoff

```python
from error_handler import ErrorHandler

handler = ErrorHandler()

# Detect error
error = handler.detect_error("Connection refused")

if error:
    retry_count = 0
    while retry_count < handler.max_retries:
        strategy = handler.select_recovery_strategy(
            error,
            context={"retry_count": retry_count},
        )

        recovery = handler.execute_recovery(
            strategy,
            context={"error": error, "retry_count": retry_count},
        )

        print(f"Retry {retry_count + 1}: {recovery.message}")

        # Implement retry logic here
        # ...

        retry_count = recovery.retry_count
```

### Example 4: Checkpoint Rollback

```python
from error_handler import ErrorHandler

handler = ErrorHandler()

# Permanent error
error = handler.detect_error("SyntaxError: invalid syntax")

if error:
    strategy = handler.select_recovery_strategy(
        error,
        context={"has_checkpoint": True, "checkpoint_id": "ckpt-123"},
    )

    recovery = handler.execute_recovery(
        strategy,
        context={"error": error, "checkpoint_id": "ckpt-123"},
    )

    print(f"Action: {recovery.next_action}")
    # Output: "rollback_to_checkpoint:ckpt-123"
```

### Example 5: Error Summary

```python
from error_handler import ErrorHandler

handler = ErrorHandler()

# Simulate errors
errors = [
    "Operation timed out",
    "SyntaxError: invalid syntax",
    "Connection refused",
]

for error_msg in errors:
    error = handler.detect_error(error_msg)
    if error:
        handler.error_log.append(error)

# Get summary
summary = handler.get_error_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"By category: {summary['by_category']}")
```

## Command Line Interface

The ErrorHandler can be used from the command line:

### Analyze Error Text

```bash
python error_handler.py analyze --text "Operation timed out"
```

### Save Analysis to File

```bash
python error_handler.py analyze --text "SyntaxError" --output analysis.json
```

### Get Error Summary

```bash
python error_handler.py summary
```

## Integration with Maestro

The ErrorHandler integrates with the Maestro Orchestrator workflow:

1. **During Task Execution**
   - Monitor subprocess output for errors
   - Detect and classify errors automatically
   - Select recovery strategy based on error type

2. **Recovery Execution**
   - Retry transient errors with backoff
   - Rollback to checkpoint for permanent errors
   - Request human input for ambiguous errors

3. **Session Management**
   - Log all errors to session directory
   - Generate error summaries
   - Track error patterns across sessions

4. **Decision Making**
   - Use error history to inform decisions
   - Learn from past error patterns
   - Improve error handling over time

## Testing

Run the test suite:

```bash
# Run all tests
python test_error_handler_standalone.py

# Run pytest (if available)
pytest test_error_handler.py -v
```

Run examples:

```bash
python example_error_handler.py
```

## File Locations

- **Implementation:** `.flow/maestro/scripts/error_handler.py`
- **Tests:** `.flow/maestro/scripts/test_error_handler.py`
- **Standalone Tests:** `.flow/maestro/scripts/test_error_handler_standalone.py`
- **Examples:** `.flow/maestro/scripts/example_error_handler.py`
- **Documentation:** `.flow/maestro/scripts/ERROR_HANDLER.md`

## Design Principles

1. **Single Responsibility:** ErrorHandler only handles error detection and recovery
2. **Composability:** Can be used standalone or integrated with other components
3. **Extensibility:** Easy to add new error types and recovery strategies
4. **Testability:** Comprehensive test coverage with clear examples
5. **Clarity:** Clear naming and well-documented API
