# Maestro State Persistence Schemas

This directory contains JSON Schema definitions for all Maestro orchestrator state persistence files.

## Directory Structure

```
.flow/maestro/schemas/
├── README.md                              # This file
├── validate.js                            # Validation utility script
├── session-metadata.schema.json           # Session metadata schema
├── decisions.schema.json                  # Decision log schema
├── checkpoints.schema.json                # Checkpoint tracking schema
├── historical-tech-stack.schema.json      # Historical tech decisions schema
├── historical-architecture.schema.json    # Historical architecture decisions schema
├── historical-task-ordering.schema.json   # Historical task ordering schema
├── config.schema.json                     # Configuration schema
└── examples/                              # Example files
    ├── session-metadata.example.json
    ├── decisions.example.json
    ├── checkpoints.example.json
    ├── historical-tech-stack.example.json
    ├── historical-architecture.example.json
    ├── historical-task-ordering.example.json
    └── config.example.yaml
```

## Schema Overview

### Session Metadata Schema

**File:** `session-metadata.schema.json`
**Usage:** `.flow/maestro/sessions/<session-id>/metadata.json`

Defines the structure for session metadata including:
- Session identifier (UUID v4)
- Feature request description
- Current status and phase
- Timestamps (created, updated, completed)
- Git context (branch, commit, repo root)
- PRD reference
- Execution statistics
- Configuration snapshot

**Status Values:**
- `initializing` - Session is being set up
- `planning` - PRD generation phase
- `generating_tasks` - Task creation phase
- `implementing` - Active implementation phase
- `validating` - Validation and testing phase
- `generating_report` - Report generation phase
- `completed` - Session finished successfully
- `failed` - Session failed
- `paused` - Session paused for human input

### Decisions Schema

**File:** `decisions.schema.json`
**Usage:** `.flow/maestro/sessions/<session-id>/decisions.json`

Defines the structure for the complete decision log including:
- Array of all decisions made during session
- Each decision includes:
  - Decision ID and timestamp
  - Category (tech_stack, architecture, task_ordering, error_recovery, subagent_delegation, validation, checkpoint)
  - Execution phase
  - Decision description
  - Detailed rationale
  - Alternatives considered
  - Context (sources, confidence level)
  - Impact assessment (scope, risk, reversibility)
- Summary statistics

### Checkpoints Schema

**File:** `checkpoints.schema.json`
**Usage:** `.flow/maestro/sessions/<session-id>/checkpoints.json`

Defines the structure for git checkpoint tracking including:
- Array of all checkpoints created
- Each checkpoint includes:
  - Checkpoint ID and timestamp
  - Git commit SHA and message
  - Description of checkpoint state
  - Execution phase
  - Checkpoint type (phase_complete, task_group_complete, safe_state, pre_risky_operation, error_recovery, manual)
  - State snapshot (tasks, decisions, files, tests)
  - Associated git tags
  - Rollback usage tracking
- Summary statistics

**Checkpoint Types:**
- `phase_complete` - End of a complete execution phase
- `task_group_complete` - Completion of a parallel task group
- `safe_state` - All tests passing, stable state
- `pre_risky_operation` - Before potentially breaking changes
- `error_recovery` - After error recovery rollback
- `manual` - Manually requested checkpoint

### Historical Tech Stack Schema

**File:** `historical-tech-stack.schema.json`
**Usage:** `.flow/maestro/decisions/tech-stack.json`

Defines the structure for historical technology stack decisions including:
- Array of all tech stack decisions across sessions
- Each decision includes:
  - Category (language, framework, library, database, testing_framework, build_tool, deployment, monitoring, other)
  - Technology chosen and version
  - Rationale and decision factors
  - Alternatives considered
  - Outcome (successful, issues, would choose again)
  - Context (feature description, project type, constraints)
- Learned patterns:
  - Preferred technologies by category with success rates
  - Avoid list based on negative outcomes

### Historical Architecture Schema

**File:** `historical-architecture.schema.json`
**Usage:** `.flow/maestro/decisions/architecture.json`

Defines the structure for historical architecture decisions including:
- Array of all architecture/pattern decisions
- Each decision includes:
  - Pattern type (creational, structural, behavioral, architectural, design_principle, data_flow, layering)
  - Pattern name and description
  - Rationale and context
  - Implementation location
  - Principles applied (SOLID, DRY, KISS, etc.)
  - Alternatives considered
  - Outcome (maintainability impact, code reuse, lessons learned)
- Learned patterns:
  - Codebase fingerprints (existing patterns with usage frequency)
  - Preferred patterns by scenario
  - Anti-patterns to avoid

### Historical Task Ordering Schema

**File:** `historical-task-ordering.schema.json`
**Usage:** `.flow/maestro/decisions/task-ordering.json`

Defines the structure for historical task ordering decisions including:
- Array of all session task orderings
- Each session includes:
  - Ordering strategy (primary approach, grouping method, parallelization level)
  - Task groups with execution order and dependencies
  - Critical path identification
  - Dependency analysis
  - Outcome (completion, reordering required, blocking issues, parallel efficiency)
- Learned patterns:
  - Effective patterns with success rates
  - Ordering rules with confidence levels
  - Anti-patterns to avoid
  - Category best practices

**Ordering Strategies:**
- `foundational_first` - Database and foundational tasks first
- `risk_early` - High-risk tasks done early
- `dependency_driven` - Strict dependency ordering
- `parallel_maximization` - Maximize parallel execution
- `hybrid` - Combination of strategies

### Configuration Schema

**File:** `config.schema.json`
**Usage:** `.flow/maestro/config.yaml`

Defines the structure for Maestro configuration (YAML format):
- Execution settings (timeouts, iterations, checkpoints, parallelization)
- Decision engine configuration (tech stack, architecture, task ordering strategies)
- Validation and quality gates
- Logging configuration
- State persistence settings
- Subagent mapping
- Reporting options

## Validation

### Using the Validation Script

```bash
# Validate a session metadata file
node .flow/maestro/schemas/validate.js session-metadata ./sessions/xyz/metadata.json

# Validate a decisions file
node .flow/maestro/schemas/validate.js decisions ./sessions/xyz/decisions.json

# Validate checkpoints
node .flow/maestro/schemas/validate.js checkpoints ./sessions/xyz/checkpoints.json

# Validate historical tech stack
node .flow/maestro/schemas/validate.js historical-tech-stack ./decisions/tech-stack.json

# Validate historical architecture
node .flow/maestro/schemas/validate.js historical-architecture ./decisions/architecture.json

# Validate historical task ordering
node .flow/maestro/schemas/validate.js historical-task-ordering ./decisions/task-ordering.json
```

### Programmatic Validation

```javascript
const { validate, loadSchema } = require('./validate.js');

// Load schema
const schema = loadSchema('session-metadata');

// Load your data
const data = JSON.parse(fs.readFileSync('metadata.json', 'utf8'));

// Validate
const result = validate(data, schema, 'session-metadata');

if (!result.valid) {
  console.error('Validation errors:', result.errors);
}
```

## Schema Design Principles

1. **Validation Over Documentation**: Schemas enforce data structure and catch errors early
2. **Backward Compatibility**: New fields are optional, existing structures remain valid
3. **Clear Semantics**: Enum values restrict options and prevent typos
4. **Comprehensive Examples**: Each schema has a corresponding example file
5. **Pattern Recognition**: Historical schemas support learning from past decisions

## Common Patterns

### UUID Format

All session IDs use UUID v4 format:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Timestamp Format

All timestamps use ISO 8601 format:
```json
{
  "created_at": "2026-01-07T10:00:00Z"
}
```

### Git Commit SHA

Short (7-char) or full (40-char) SHA accepted:
```json
{
  "commit_sha": "b9dc8fd"  // or full 40-char hash
}
```

### Status Enums

All status fields use restricted enums to prevent invalid values:
- Session status: `initializing`, `planning`, `generating_tasks`, `implementing`, `validating`, `generating_report`, `completed`, `failed`, `paused`
- Decision category: `tech_stack`, `architecture`, `task_ordering`, `error_recovery`, `subagent_delegation`, `validation`, `checkpoint`
- Checkpoint type: `phase_complete`, `task_group_complete`, `safe_state`, `pre_risky_operation`, `error_recovery`, `manual`

## Learning and Pattern Recognition

Historical schemas (tech-stack, architecture, task-ordering) support pattern recognition through:

1. **Decision Tracking**: Every decision is logged with full context
2. **Outcome Recording**: Success/failure and lessons learned
3. **Pattern Extraction**: High-confidence rules derived from historical data
4. **Anti-Pattern Detection**: Identify and avoid problematic approaches

Example pattern learned from historical data:
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
      "technology": "Custom authentication",
      "reason": "High maintenance burden, security risks",
      "failure_count": 3
    }
  ]
}
```

## Maintenance

When updating schemas:

1. **Increment version** in historical schemas
2. **Add new fields as optional** to maintain backward compatibility
3. **Update examples** to demonstrate new fields
4. **Update this README** with new patterns or structures
5. **Test validation** with both old and new data files

## Related Documentation

- [Maestro PRD](../../.flow/prd-maestro-orchestrator-v1.md) - Full system design
- [WORKFLOW.md](../../../WORKFLOW.md) - Flow command workflow
- [COMMANDS.md](../../../COMMANDS.md) - Command documentation
