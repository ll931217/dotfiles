# Maestro State Persistence Schema Design Summary

## Overview

This document provides a comprehensive summary of the Maestro orchestrator state persistence schema design. The schemas define the structure for all persisted data during autonomous execution sessions.

## Architecture Principles

### Design Goals

1. **Validation-First**: All data structures validated against JSON schemas
2. **Backward Compatible**: New fields optional, existing structures remain valid
3. **Learning-Enabled**: Historical schemas support pattern recognition
4. **Replayable**: Complete decision log enables session replay
5. **Debuggable**: Rich metadata and context for troubleshooting

### Data Flow

```
Session Start → Metadata Creation
                ↓
Planning Phase → Decisions Logged → Historical Patterns Updated
                ↓
Task Generation → Task Ordering Logged → Historical Patterns Updated
                ↓
Implementation → Decisions Logged → Checkpoints Created
                ↓
Validation → Results Logged → Final Report Generated
                ↓
Session Complete → All State Persisted
```

## Schema Hierarchy

### Level 1: Session Data (Per-Session)

Stored in: `.flow/maestro/sessions/<session-id>/`

| Schema | File | Purpose | Size |
|--------|------|---------|------|
| session-metadata | metadata.json | Session info, status, timestamps | ~1KB |
| decisions | decisions.json | All decisions with rationale | ~10-50KB |
| checkpoints | checkpoints.json | Git commit references | ~2-5KB |
| execution-log | execution-log.md | Detailed execution log | ~5-20KB |
| final-report | final-report.md | Generated report | ~10-30KB |

### Level 2: Historical Data (Cross-Session)

Stored in: `.flow/maestro/decisions/`

| Schema | File | Purpose | Growth |
|--------|------|---------|--------|
| historical-tech-stack | tech-stack.json | Tech decisions history | ~500B per decision |
| historical-architecture | architecture.json | Architecture patterns history | ~1KB per decision |
| historical-task-ordering | task-ordering.json | Task ordering history | ~2KB per session |

### Level 3: Configuration (Global)

Stored in: `.flow/maestro/`

| Schema | File | Purpose | Updates |
|--------|------|---------|---------|
| config | config.yaml | Maestro configuration | User edits |

## Schema Relationships

```
config.yaml
    ↓
    ├── influences → decision_engine settings
    └── defines → execution behavior

session-metadata.json
    ↓
    ├── references → prd file
    └── tracks → git_context

decisions.json
    ↓
    ├── categorized by → category enum
    ├── provides rationale for → all actions
    └── feeds into → historical learning

checkpoints.json
    ↓
    ├── references → git commits
    ├── snapshot of → session state
    └── enables → rollback capability

historical-*.json
    ↓
    ├── aggregates from → all sessions
    ├── identifies → preferred patterns
    └── feeds back into → decision engine
```

## Key Data Structures

### Decision Object

Core structure for all autonomous decisions:

```json
{
  "decision_id": "string",
  "timestamp": "ISO8601",
  "category": "enum",
  "phase": "enum",
  "decision": "string",
  "rationale": "string",
  "alternatives_considered": [...],
  "context": {
    "sources": [...],
    "confidence": "enum"
  },
  "impact": {
    "scope": "enum",
    "risk_level": "enum",
    "reversibility": "enum"
  }
}
```

### Checkpoint Object

Git commit tracking for rollback:

```json
{
  "checkpoint_id": "string",
  "timestamp": "ISO8601",
  "commit_sha": "git-hash",
  "commit_message": "string",
  "description": "string",
  "phase": "enum",
  "checkpoint_type": "enum",
  "state_snapshot": {...},
  "tags": [...],
  "rollback_used": boolean,
  "rollback_count": integer
}
```

### Historical Pattern Object

Learned patterns from past sessions:

```json
{
  "patterns": {
    "preferred_by_category": {
      "category": {
        "technology": "string",
        "success_rate": 0-1,
        "usage_count": integer
      }
    },
    "avoid_list": [
      {
        "technology": "string",
        "reason": "string",
        "failure_count": integer
      }
    ]
  }
}
```

## Validation Strategy

### Schema Validation

- **Format**: JSON Schema Draft 07
- **Tool**: Custom Node.js validator (validate.js)
- **Enforcement**: Runtime validation on all read/write operations
- **Error Reporting**: Detailed error messages with property path and constraint

### Validation Rules

| Constraint | Type | Example |
|------------|------|---------|
| Required fields | Schema validation | session_id must exist |
| Type checking | Runtime type check | timestamp must be string |
| Enum values | Whitelist | status must be valid enum value |
| Pattern matching | Regex | commit_sha must match git hash pattern |
| Range constraints | Min/max | confidence must be 0-1 |
| Format validation | Regex patterns | UUID, ISO8601, email formats |

## Learning System

### Pattern Extraction

Historical schemas enable learning through:

1. **Decision Aggregation**: All decisions logged with outcomes
2. **Success Correlation**: Identify patterns in successful decisions
3. **Failure Analysis**: Detect and avoid anti-patterns
4. **Confidence Scoring**: Track and use confidence levels

### Learning Feedback Loop

```
Session Execution
    ↓
Decisions Logged with Outcomes
    ↓
Pattern Analysis (post-session)
    ↓
Historical Patterns Updated
    ↓
Next Session Benefits from Learning
```

### Example Learning Rules

Derived from historical schemas:

1. **Technology Selection**:
   - Prefer existing dependencies (confidence: 0.97)
   - Avoid custom auth implementations (failure_count: 3)

2. **Architecture**:
   - Match existing patterns (success_rate: 0.95)
   - Use middleware for auth (usage_count: 15)

3. **Task Ordering**:
   - Database schema first (supporting_evidence: 28)
   - Backend before frontend (supporting_evidence: 22)

## Persistence Strategy

### Write Patterns

| Data Type | Write Frequency | Sync Strategy | Backup |
|-----------|-----------------|---------------|--------|
| Session metadata | On status change | Immediate | Git commit |
| Decisions | On each decision | Immediate | Git commit |
| Checkpoints | On checkpoint creation | Immediate | Git tag |
| Historical data | Session end | Batch | Git commit |
| Execution log | Continuous | Buffered | Git commit |

### Read Patterns

| Operation | Frequency | Cache Strategy |
|-----------|-----------|----------------|
| Session status check | Every phase | Memory cache |
| Decision retrieval | On recovery | Direct read |
| Historical patterns | Planning phase | Memory cache |
| Checkpoint lookup | On rollback | Direct read |

## Storage Considerations

### Space Estimation

Per Session:
- Metadata: ~1KB
- Decisions: ~10-50KB (depends on complexity)
- Checkpoints: ~2-5KB
- Execution log: ~5-20KB
- Total: ~20-80KB per session

Historical (100 sessions):
- Tech stack: ~50KB
- Architecture: ~100KB
- Task ordering: ~200KB
- Total: ~350KB for 100 sessions

### Retention Policy

Configurable via `config.yaml`:

```yaml
persistence:
  retention_days: 90  # Default
  compress_old_sessions: false
```

Recommendations:
- Active sessions: Keep indefinitely
- Completed sessions: 90 days default
- Historical patterns: Keep indefinitely
- Archive old sessions to cold storage

## Error Handling

### Validation Failures

Strategy:
1. Log validation error with context
2. Attempt graceful degradation
3. Fall back to safe state
4. Alert user if critical

### Recovery Scenarios

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| Corrupted session file | Validation on load | Restore from last checkpoint |
| Missing required field | Schema validation | Use default or fail gracefully |
| Invalid enum value | Runtime check | Log error, use safe default |
| Git commit not found | Checkpoint validation | Warn user, mark as invalid |

## Security Considerations

### Data Sensitivity

Session data may contain:
- Feature requests (user intent)
- Code snippets (implementation details)
- Git history (repository state)
- Decision rationale (internal logic)

**Recommendation**: Do not commit `.flow/maestro/` to public repositories

### Access Control

Schemas themselves are read-only reference:
- No authentication required for schema access
- Validation script does not write data
- Session data follows repository permissions

## Testing

### Validation Testing

All example files validated:

```bash
cd .flow/maestro/schemas
node validate.js session-metadata examples/session-metadata.example.json
node validate.js decisions examples/decisions.example.json
node validate.js checkpoints examples/checkpoints.example.json
node validate.js historical-tech-stack examples/historical-tech-stack.example.json
node validate.js historical-architecture examples/historical-architecture.example.json
node validate.js historical-task-ordering examples/historical-task-ordering.example.json
```

### Schema Testing

Coverage:
- All required fields tested
- All enum values validated
- All format patterns verified
- All constraints checked

## Future Enhancements

### Potential Improvements

1. **JSON Schema Validation Library**: Replace custom validator with ajv or similar
2. **Schema Versioning**: Add version field for migration support
3. **Compression**: Compress old session data automatically
4. **Indexing**: Add search indexes for historical data
5. **Metrics**: Track schema usage and performance

### Extension Points

Schemas designed for:
- New decision categories (add to enum)
- New checkpoint types (add to enum)
- Additional metadata (add optional fields)
- Custom validation rules (extend validator)

## Related Documentation

- [Schema README](./README.md) - Detailed schema documentation
- [Maestro PRD](../../.flow/prd-maestro-orchestrator-v1.md) - System design
- [Validation Script](./validate.js) - Implementation details
- [Example Files](./examples/) - Reference implementations

## Maintenance

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-07 | Initial schema design |

### Change Process

1. Update schema file
2. Increment version in historical schemas
3. Update examples
4. Update this documentation
5. Test validation with all examples
6. Commit with descriptive message
