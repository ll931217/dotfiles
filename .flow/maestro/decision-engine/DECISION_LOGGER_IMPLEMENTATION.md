# Decision Logger Implementation

## Overview

The Decision Logger is a comprehensive system for tracking decisions with full rationale and context, enabling learning from past choices. It supports session-based logging, historical aggregation, and intelligent querying to inform future decisions.

## Architecture

```
Decision Logger
├── Decision (dataclass)
│   ├── decision_id
│   ├── timestamp
│   ├── category
│   ├── decision
│   ├── rationale
│   ├── phase
│   ├── alternatives_considered
│   ├── context
│   └── impact
├── DecisionLog (dataclass)
│   ├── session_id
│   ├── decisions[]
│   ├── generated_at
│   └── summary
└── DecisionLogger (main class)
    ├── log_decision()
    ├── get_session_decisions()
    ├── get_historical_decisions()
    ├── learn_from_past()
    └── aggregate_to_historical()
```

## Storage Structure

```
.flow/maestro/
├── sessions/
│   └── <session-id>/
│       └── decisions.json          # Session decisions
└── decisions/
    ├── historical-tech-stack.json  # Tech stack history
    ├── historical-architecture.json # Architecture history
    └── historical-task-ordering.json # Task ordering history
```

## Decision Categories

### 1. Tech Stack (`tech_stack`)
Technology selection decisions (languages, frameworks, databases, etc.)

**Schema**: `schemas/historical-tech-stack.schema.json`

**Fields**:
- `choice`: Technology selected
- `category`: Technology category
- `decision_factors`: Influencing factors
- `alternatives`: Options considered
- `outcome`: Success/failure data

**Patterns Learned**:
- Preferred technologies by category
- Success rates
- Technologies to avoid

### 2. Architecture (`architecture`)
Design pattern and architectural decisions

**Schema**: `schemas/historical-architecture.schema.json`

**Fields**:
- `pattern_type`: Pattern category (creational, structural, etc.)
- `pattern_name`: Name of pattern
- `principles_applied`: SOLID principles
- `implementation_location`: Files/modules affected

**Patterns Learned**:
- Codebase fingerprints
- Preferred patterns by scenario
- Anti-patterns to avoid

### 3. Task Ordering (`task_ordering`)
Task sequencing and prioritization decisions

**Schema**: `schemas/historical-task-ordering.schema.json`

**Fields**:
- `ordering_strategy`: Primary approach
- `task_groups`: Group structure
- `dependency_analysis`: Dependency graph
- `outcome`: Execution results

**Patterns Learned**:
- Effective ordering patterns
- Learned rules
- Category best practices

### 4. Other Categories
- `error_recovery`: Error handling decisions
- `subagent_delegation`: Task delegation choices
- `validation`: Validation strategy decisions
- `checkpoint`: Checkpoint creation decisions

## API Reference

### DecisionLogger

#### `__init__(session_id=None, base_path=None)`
Initialize the decision logger.

**Parameters**:
- `session_id`: Optional session ID (generated if not provided)
- `base_path`: Base path for storage (defaults to `.flow/maestro`)

#### `log_decision(decision_type, decision)`
Log a decision with full context.

**Parameters**:
- `decision_type`: Category of decision
- `decision`: Dictionary containing:
  - `decision` (required): The decision made
  - `rationale` (required): Why this decision was made
  - `phase` (optional): Execution phase
  - `alternatives_considered` (optional): List of alternatives
  - `context` (optional): Additional context
  - `impact` (optional): Expected impact

**Returns**: Decision ID (e.g., `decision-001`)

**Example**:
```python
logger.log_decision(
    decision_type="tech_stack",
    decision={
        "decision": "Use FastAPI framework",
        "rationale": "Modern async support with automatic OpenAPI",
        "phase": "plan",
        "alternatives_considered": [
            {
                "option": "Flask",
                "reason_rejected": "No native async",
            }
        ],
        "context": {
            "confidence": "high",
            "sources": ["FastAPI docs"],
        },
        "impact": {
            "scope": "codebase",
            "risk_level": "low",
            "reversibility": "moderate",
        },
    },
)
```

#### `get_session_decisions(session_id=None)`
Get all decisions for a session.

**Parameters**:
- `session_id`: Session ID (uses current if not provided)

**Returns**: List of `Decision` objects

#### `get_historical_decisions(category=None, limit=50)`
Query historical decisions across all sessions.

**Parameters**:
- `category`: Filter by category (optional)
- `limit`: Maximum number of decisions (default: 50)

**Returns**: List of decision dictionaries

**Example**:
```python
# Get all tech stack decisions
history = logger.get_historical_decisions(category="tech_stack", limit=10)

for decision in history:
    print(f"{decision['decision']}")
    print(f"  Rationale: {decision['rationale']}")
    print(f"  Confidence: {decision['context'].get('confidence')}")
```

#### `learn_from_past(context)`
Find relevant past decisions to inform new choices.

**Parameters**:
- `context`: Dictionary containing:
  - `category` (required): Decision category
  - `project_type`: Type of project
  - `feature_description`: Current feature
  - `keywords`: Search keywords
  - `constraints`: Any constraints

**Returns**: List of relevant decisions with relevance scores

**Example**:
```python
context = {
    "category": "tech_stack",
    "project_type": "web_api",
    "feature_description": "REST API with real-time updates",
    "keywords": ["async", "websocket", "api"],
}

relevant = logger.learn_from_past(context)

for decision in relevant:
    score = decision.get('relevance_score', 0)
    print(f"[{score:.2f}] {decision['decision']}")
```

#### `aggregate_to_historical()`
Aggregate session decisions into historical records.

Called at the end of a session to update the knowledge base.

**Example**:
```python
# End of session
logger.aggregate_to_historical()
```

#### `export_summary()`
Export session summary with statistics.

**Returns**: Summary dictionary

**Example**:
```python
summary = logger.export_summary()
print(f"Total decisions: {summary['total_decisions']}")
print(f"By category: {summary['decisions_by_category']}")
```

## Relevance Scoring

The `learn_from_past()` method uses relevance scoring to find applicable past decisions:

**Score Components**:
- Category match: +0.3
- Keyword match: +0.1 per keyword
- Project type match: +0.2
- Feature description similarity: Up to +0.4

**Maximum score**: 1.0 (highly relevant)

## Pattern Learning

### Tech Stack Patterns
- **Preferred by category**: Tracks success rates for technologies
- **Avoid list**: Technologies with low success rates (<30%)

### Architecture Patterns
- **Codebase fingerprints**: Pattern usage frequency and consistency
- **Preferred by scenario**: Best patterns for specific situations
- **Anti-patterns**: Patterns to avoid based on failures

### Task Ordering Patterns
- **Effective patterns**: Successful ordering strategies
- **Learned rules**: Rules derived from successful sessions
- **Anti-patterns**: Ordering approaches that failed

## CLI Usage

### Query Historical Decisions
```bash
python3 scripts/decision_logger.py --query --category tech_stack --limit 10
```

### Learn from Past
```bash
python3 scripts/decision_logger.py --learn \
  --context '{"category": "tech_stack", "keywords": ["async", "api"]}'
```

### Aggregate to Historical
```bash
python3 scripts/decision_logger.py --aggregate
```

### Export Summary
```bash
python3 scripts/decision_logger.py --summary
```

## Examples

See `scripts/example_decision_logger.py` for complete examples:

1. Logging tech stack decisions
2. Logging architecture decisions
3. Aggregating to historical
4. Querying historical decisions
5. Learning from past decisions
6. Complete session workflow
7. Error handling

Run examples:
```bash
python3 scripts/example_decision_logger.py
```

## Testing

Run tests:
```bash
python3 scripts/test_decision_logger.py
```

Test coverage:
- Decision dataclass
- Decision log management
- Session persistence
- Historical aggregation
- Query and learning
- Relevance scoring
- Pattern updates
- Multi-session handling

## Integration with Maestro

### Planning Phase
```python
# Log tech stack decisions
logger.log_decision("tech_stack", {
    "decision": "Use FastAPI",
    "rationale": "Modern async framework",
})
```

### Task Generation
```python
# Log ordering decisions
logger.log_decision("task_ordering", {
    "decision": "Use foundational-first ordering",
    "rationale": "Schema must exist before models",
})
```

### Implementation
```python
# Log architecture decisions
logger.log_decision("architecture", {
    "decision": "Repository pattern",
    "rationale": "Separates concerns",
})
```

### Cleanup
```python
# Aggregate for future learning
logger.aggregate_to_historical()
```

## Best Practices

1. **Always provide rationale**: Explain why decisions were made
2. **Document alternatives**: List options that were considered
3. **Include confidence levels**: Helps assess decision quality
4. **Track outcomes**: Update with success/failure data
5. **Use consistent categories**: Enables better pattern learning
6. **Aggregate regularly**: Keep historical knowledge current
7. **Query before deciding**: Learn from past before making new choices

## Schema Compliance

All decision logs validate against JSON schemas:
- `schemas/decisions.schema.json`: Session decisions
- `schemas/historical-tech-stack.schema.json`: Tech stack history
- `schemas/historical-architecture.schema.json`: Architecture history
- `schemas/historical-task-ordering.schema.json`: Task ordering history

## Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Log decision | < 10ms | Includes file persistence |
| Query historical | < 50ms | For 100 decisions |
| Learn from past | < 100ms | Includes relevance scoring |
| Aggregate | < 200ms | Depends on decision count |

## Troubleshooting

### Decisions not persisting
```bash
# Check file permissions
ls -la .flow/maestro/sessions/<session-id>/decisions.json
```

### Historical files not updating
```bash
# Manually trigger aggregation
python3 scripts/decision_logger.py --aggregate
```

### No relevant decisions found
- Check that `category` matches
- Add more keywords to context
- Verify historical data exists

## Future Enhancements

1. **Machine learning**: Improve relevance scoring with ML
2. **Decision trees**: Visualize decision history
3. **Outcome tracking**: Automatic success/failure detection
4. **Collaborative filtering**: Learn from multiple projects
5. **Decision templates**: Reuse proven decision patterns
6. **Confidence calibration**: Adjust based on outcomes

## License

Part of the Maestro autonomous orchestrator system.
