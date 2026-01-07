# ErrorHandler - Quick Reference Guide

## Task: dotfiles-e5e.1 - Implement error detection and classification

### Status: ✅ COMPLETE

All deliverables implemented and tested.

## File Locations

```
.flow/maestro/scripts/
├── error_handler.py                          # Main implementation (26KB)
├── test_error_handler.py                     # Pytest tests (20KB)
├── test_error_handler_standalone.py          # Standalone tests (23KB)
├── example_error_handler.py                  # Usage examples (7.8KB)
├── ERROR_HANDLER.md                          # Full documentation (11KB)
└── ERROR_HANDLER_IMPLEMENTATION_SUMMARY.md   # Implementation summary
```

## Quick Start

```python
from error_handler import ErrorHandler

# Initialize
handler = ErrorHandler()

# Detect error from output
error = handler.detect_error("Operation timed out")

# Get recovery strategy
strategy = handler.select_recovery_strategy(error)

# Execute recovery
result = handler.execute_recovery(strategy, {"error": error})
```

## API Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `detect_error(output, source, exit_code, context)` | Detect error from output | `Error` or `None` |
| `classify_error(error)` | Classify error category | `ErrorCategory` |
| `select_recovery_strategy(error, context)` | Select recovery strategy | `RecoveryStrategy` |
| `execute_recovery(strategy, context)` | Execute recovery | `RecoveryResult` |
| `handle_subprocess_result(result, command, context)` | Handle subprocess | `(Error, RecoveryResult)` |
| `get_error_summary()` | Get error statistics | `dict` |
| `save_error_log(filepath)` | Save error log | `Path` |

## Error Categories

| Category | Description | Recovery Strategy |
|----------|-------------|-------------------|
| `TRANSIENT` | Temporary errors (timeout, network) | `RETRY_WITH_BACKOFF` |
| `PERMANENT` | Code errors (syntax, import) | `ROLLBACK_TO_CHECKPOINT` or `ALTERNATIVE_APPROACH` |
| `AMBIGUOUS` | Unclear cause | `REQUEST_HUMAN_INPUT` |

## Test Results

```
Tests: 42
Passed: 42 ✅
Failed: 0
```

All error detection, classification, and recovery tests pass.

## CLI Usage

```bash
# Analyze error
python error_handler.py analyze --text "Operation timed out"

# Get summary
python error_handler.py summary

# Run tests
python test_error_handler_standalone.py

# Run examples
python example_error_handler.py
```

## Integration

The ErrorHandler integrates with:
- Session Manager (logs to session directory)
- Decision Engine (uses error history)
- Task Executor (handles subprocess results)
- Checkpoint System (supports rollback)

## Key Features

✅ Pattern-based error detection
✅ Three-category classification (transient, permanent, ambiguous)
✅ Six recovery strategies
✅ Exponential backoff retry
✅ Checkpoint rollback support
✅ Human input escalation
✅ Error logging and summary
✅ CLI interface
✅ Comprehensive tests (42/42 passing)

## Documentation

- Full API documentation: `ERROR_HANDLER.md`
- Implementation summary: `ERROR_HANDLER_IMPLEMENTATION_SUMMARY.md`
- Usage examples: `example_error_handler.py`

## Verification

All components verified:
✅ Error detection from various sources
✅ Error classification by category
✅ Recovery strategy selection
✅ Recovery execution with context
✅ Subprocess result handling
✅ Error logging and summary
✅ JSON serialization
✅ CLI interface
