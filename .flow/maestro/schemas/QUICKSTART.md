# Maestro Schema Quick Reference

## Quick Start

### Validate a JSON File

```bash
cd .flow/maestro/schemas
node validate.js <schema-name> <json-file>

# Example:
node validate.js session-metadata ../sessions/abc-123/metadata.json
```

### Available Schemas

| Schema Name | Usage | File Location |
|-------------|-------|---------------|
| `session-metadata` | Session info | `sessions/<id>/metadata.json` |
| `decisions` | Decision log | `sessions/<id>/decisions.json` |
| `checkpoints` | Git checkpoints | `sessions/<id>/checkpoints.json` |
| `historical-tech-stack` | Tech decisions | `decisions/tech-stack.json` |
| `historical-architecture` | Architecture patterns | `decisions/architecture.json` |
| `historical-task-ordering` | Task ordering | `decisions/task-ordering.json` |
| `config` | Configuration | `config.yaml` |

## Common Values

### Session Status

```
initializing → planning → generating_tasks → implementing → validating → generating_report → completed
                                    ↓
                                failed / paused
```

### Decision Categories

- `tech_stack` - Technology choices
- `architecture` - Design patterns
- `task_ordering` - Task prioritization
- `error_recovery` - Recovery actions
- `subagent_delegation` - Task delegation
- `validation` - Quality gates
- `checkpoint` - Checkpoint creation

### Checkpoint Types

- `phase_complete` - End of phase
- `task_group_complete` - Parallel group done
- `safe_state` - All tests passing
- `pre_risky_operation` - Before risky changes
- `error_recovery` - After recovery
- `manual` - User requested

### Phases

- `plan` - PRD generation
- `generate_tasks` - Task creation
- `implement` - Implementation
- `validate` - Testing and validation
- `cleanup` - Finalization

## Format Patterns

### UUID (Session IDs)

```
Format: 8-4-4-4-12 hexadecimal characters
Example: 550e8400-e29b-41d4-a716-446655440000
Pattern: ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

### Git Commit SHA

```
Short: 7 hexadecimal characters
Long: 40 hexadecimal characters
Example: b9dc8fd or b9dc8fd35ba862a6b43a7fb1f681f09eba00b4d7
Pattern: ^[0-9a-f]{7,40}$
```

### Timestamp (ISO 8601)

```
Format: YYYY-MM-DDTHH:MM:SSZ
Example: 2026-01-07T10:00:00Z
Pattern: date-time format
```

## Directory Structure

```
.flow/maestro/
├── sessions/
│   └── <session-id>/
│       ├── metadata.json          # Session metadata
│       ├── decisions.json          # All decisions
│       ├── checkpoints.json        # Git checkpoints
│       ├── execution-log.md        # Detailed log
│       └── final-report.md         # Final report
├── decisions/
│   ├── tech-stack.json            # Historical tech decisions
│   ├── architecture.json           # Historical architecture
│   └── task-ordering.json          # Historical task ordering
├── config.yaml                     # Configuration
└── schemas/                        # Schema definitions
    ├── *.schema.json              # Schema files
    ├── validate.js                # Validator
    ├── examples/                  # Examples
    └── *.md                       # Documentation
```

## Example Decision Object

```json
{
  "decision_id": "decision-001",
  "timestamp": "2026-01-07T10:05:12Z",
  "category": "tech_stack",
  "phase": "plan",
  "decision": "Use Passport.js for OAuth",
  "rationale": "Existing dependency, mature ecosystem",
  "alternatives_considered": [
    {
      "option": "Manual implementation",
      "reason_rejected": "High maintenance burden"
    }
  ],
  "context": {
    "sources": ["package.json", "codebase"],
    "confidence": "high"
  },
  "impact": {
    "scope": "session",
    "risk_level": "low",
    "reversibility": "moderate"
  }
}
```

## Example Checkpoint Object

```json
{
  "checkpoint_id": "checkpoint-001",
  "timestamp": "2026-01-07T10:28:15Z",
  "commit_sha": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
  "commit_message": "feat: OAuth backend complete",
  "description": "Backend implementation with all tests passing",
  "phase": "implement",
  "checkpoint_type": "task_group_complete",
  "state_snapshot": {
    "tasks_completed": 7,
    "decisions_made": 5,
    "tests_passing": 89
  },
  "tags": ["maestro-checkpoint-1"],
  "rollback_used": false
}
```

## Validation Errors

### Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| Required property missing | Missing field | Add required field |
| Expected type X, got Y | Wrong data type | Correct the type |
| Does not match pattern | Invalid format | Fix format (UUID, SHA, etc.) |
| Not one of: [...] | Invalid enum value | Use valid enum value |
| Less than minimum | Value too small | Increase value |
| Greater than maximum | Value too large | Decrease value |

### Debugging

```bash
# Get detailed error messages
node validate.js session-metadata metadata.json

# Check if file is valid JSON
cat metadata.json | jq .

# View specific field
cat metadata.json | jq .session_id
```

## Learning Patterns

### Historical Tech Stack

```json
{
  "preferred_by_category": {
    "library": {
      "technology": "Passport.js",
      "success_rate": 1.0,
      "usage_count": 5
    }
  },
  "avoid_list": [
    {
      "technology": "Custom auth",
      "reason": "Security risks",
      "failure_count": 3
    }
  ]
}
```

### Historical Architecture

```json
{
  "codebase_fingerprints": {
    "middleware_composition": {
      "pattern_name": "Express Middleware",
      "usage_frequency": 15,
      "consistency_score": 0.95
    }
  }
}
```

### Historical Task Ordering

```json
{
  "ordering_rules": [
    {
      "rule": "Database schema first",
      "priority": "high",
      "confidence": 0.97,
      "supporting_evidence": 28
    }
  ]
}
```

## Programmatic Usage

```javascript
const { validate, loadSchema } = require('./validate.js');

// Load schema
const schema = loadSchema('session-metadata');

// Validate data
const result = validate(data, schema);

if (!result.valid) {
  console.error('Errors:', result.errors);
  result.errors.forEach(err => {
    console.log(`  - ${err.property}: ${err.message}`);
  });
}
```

## Configuration

### Key Settings

```yaml
execution:
  max_iterations: 3
  timeout_minutes: 120
  auto_checkpoint: true
  parallel_execution: true

decision_engine:
  tech_stack_selection:
    strategy: prefer_existing
    require_confidence: high

validation:
  test_suite: true
  test_coverage_threshold: 80
  prd_validation: true
```

## Maintenance

### Adding New Fields

1. Add to schema as optional field
2. Update examples
3. Document in README
4. Test validation

### Schema Versioning

Historical schemas include version field:

```json
{
  "version": "1.0",
  "last_updated": "2026-01-07T10:00:00Z",
  ...
}
```

### Backup Strategy

- Session data: Git commits
- Historical data: Aggregate and compress
- Configuration: Version in repository

## Troubleshooting

### Schema Not Found

```bash
# List available schemas
ls .flow/maestro/schemas/*.schema.json
```

### Validation Fails

1. Check JSON syntax: `cat file.json | jq .`
2. Verify required fields present
3. Check enum values are valid
4. Validate formats (UUID, SHA, timestamps)
5. Review error messages carefully

### Example Doesn't Validate

```bash
# Re-validate example
cd .flow/maestro/schemas
node validate.js <schema> examples/<example>
```

## Resources

- [README.md](./README.md) - Full documentation
- [SCHEMA_SUMMARY.md](./SCHEMA_SUMMARY.md) - Technical details
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Implementation guide
- [Maestro PRD](../../.flow/prd-maestro-orchestrator-v1.md) - System design

## Tips

1. **Always validate** JSON files before using in production
2. **Use examples** as templates for new files
3. **Update schemas** carefully to maintain backward compatibility
4. **Document changes** in schema files and README
5. **Test validation** with both valid and invalid data
6. **Version schemas** when making breaking changes
7. **Compress old sessions** to save space
8. **Review historical patterns** regularly for insights
