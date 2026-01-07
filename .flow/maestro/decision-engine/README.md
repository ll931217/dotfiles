# Maestro Decision Engine

The Decision Engine provides intelligent analysis and decision-making capabilities for the Maestro autonomous orchestrator.

## Overview

The Decision Engine analyzes project context, dependencies, and task characteristics to optimize autonomous execution workflows.

## Components

### 1. Tech Stack Selector (`tech_stack_selector.py`)

Analyzes project requirements and recommends optimal technology stacks.

**Features:**
- Requirement analysis
- Tech stack scoring
- Fit assessment
- Recommendation generation

**Usage:**
```bash
python3 scripts/tech_stack_selector.py "Build a RESTful API with real-time updates"
```

### 2. Task Ordering (`task_ordering.py`)

Orders tasks based on dependency analysis and execution strategies.

**Features:**
- Dependency graph parsing from beads
- Multiple ordering strategies (topological, risk-first, foundational-first)
- Parallel execution detection
- Conflict resolution

**Usage:**
```bash
# Basic usage
python3 scripts/task_ordering.py --strategy topological

# With human-readable output
python3 scripts/order_tasks.py --print-plan

# Different strategies
python3 scripts/order_tasks.py --strategy risk_first --print-plan
```

**Strategies:**
- `topological`: Dependency-ordered with maximum parallelism (default)
- `risk_first`: Priority-ordered (P0 → P4)
- `foundational_first`: Foundational tasks first (schema, core, base)
- `parallel_maximizing`: Maximum parallel execution

### 3. Dependency Analysis (`analyze_dependencies.py`)

Analyzes project dependencies to inform technology decisions.

**Features:**
- Package manager detection
- Dependency parsing
- Existing tech stack identification

**Usage:**
```bash
python3 scripts/analyze_dependencies.py /path/to/project
```

### 4. Pattern Detection (`detect_patterns.py`)

Detects implementation patterns in code and documentation.

**Features:**
- Architecture pattern recognition
- Design pattern detection
- Code pattern identification

**Usage:**
```bash
python3 scripts/detect_patterns.py /path/to/project
```

### 5. Beads Dependency Parser (`parse_beads_deps.py`)

Parses beads dependency graph for task ordering.

**Features:**
- Dependency graph construction
- Topological sorting
- Foundational task identification
- Parallel group detection

**Usage:**
```bash
python3 scripts/parse_beads_deps.py
```

### 6. Decision Logger (`decision_logger.py`)

Logs decisions with rationale and context, enables learning from past decisions.

**Features:**
- Decision logging with full rationale
- Session-based persistence
- Historical aggregation across sessions
- Intelligent querying with relevance scoring
- Pattern learning from outcomes

**Usage:**
```python
from scripts.decision_logger import DecisionLogger

# Initialize
logger = DecisionLogger()

# Log decision
logger.log_decision(
    decision_type="tech_stack",
    decision={
        "decision": "Use FastAPI framework",
        "rationale": "Modern async support with automatic OpenAPI",
        "context": {"confidence": "high"},
    },
)

# Learn from past
context = {
    "category": "tech_stack",
    "keywords": ["async", "api"],
}
relevant = logger.learn_from_past(context)

# Aggregate to historical at session end
logger.aggregate_to_historical()
```

**CLI:**
```bash
# Query historical decisions
python3 scripts/decision_logger.py --query --category tech_stack

# Learn from past
python3 scripts/decision_logger.py --learn --context '{"category": "tech_stack"}'

# Aggregate to historical
python3 scripts/decision_logger.py --aggregate

# Export summary
python3 scripts/decision_logger.py --summary
```

## Quick Start

### 1. Order Tasks for Execution

```python
from scripts.task_ordering import TaskOrderingEngine

# Create engine
engine = TaskOrderingEngine(strategy="topological")
engine.load_from_beads()

# Compute ordering
result = engine.compute_ordering()

# Execute groups
for i, group in enumerate(result['sequence'], 1):
    if len(group) == 1:
        execute_task(group[0])
    else:
        execute_parallel(group, group_id=i)
```

### 2. Get Tech Stack Recommendation

```python
from scripts.tech_stack_selector import TechStackSelector

selector = TechStackSelector()
recommendation = selector.recommend_tech_stack(
    requirements="Build a real-time chat application",
    project_context={"scale": "large", "team_size": 5}
)

print(recommendation['stack'])
```

### 3. Analyze Project Dependencies

```python
from scripts.analyze_dependencies import analyze_project

result = analyze_project("/path/to/project")
print(f"Package managers: {result['package_managers']}")
print(f"Dependencies: {len(result['existing_deps'])}")
```

## Architecture

```
Decision Engine
├── Tech Stack Selector
│   ├── Requirement Analyzer
│   ├── Tech Stack Scorer
│   └── Fit Calculator
├── Task Ordering
│   ├── Beads Parser
│   ├── Dependency Graph
│   ├── Strategy Selector
│   └── Conflict Detector
├── Dependency Analyzer
│   ├── Package Manager Detector
│   └── Dependency Parser
├── Pattern Detector
│   ├── Architecture Patterns
│   ├── Design Patterns
│   └── Code Patterns
└── Decision Logger
    ├── Decision Tracking
    ├── Historical Aggregation
    ├── Pattern Learning
    └── Relevance Scoring
```

## Integration with Maestro

The Decision Engine integrates with Maestro through the following flow:

1. **Planning Phase**: Tech stack selector recommends technologies, decision logger tracks choices
2. **Task Generation**: Task ordering optimizes execution sequence
3. **Implementation**: Dependency analysis informs decisions, decision logger tracks architecture choices
4. **Pattern Detection**: Identifies implementation patterns
5. **Session End**: Decision logger aggregates to historical for future learning

## Reference Documentation

- [Tech Stack Algorithm](TECH_STACK_ALGORITHM.md) - Tech stack selection algorithm
- [Architecture Patterns](references/architecture-patterns.md) - Architecture pattern reference
- [Task Ordering Strategies](references/task-ordering-strategies.md) - Task ordering strategies
- [Decision Logger Implementation](DECISION_LOGGER_IMPLEMENTATION.md) - Decision logging system
- [API Reference](references/api_reference.md) - Complete API documentation
- [Ordering Integration Guide](scripts/ORDERING_INTEGRATION.md) - Task ordering integration guide
- [Tech Stack Rubric](references/tech-stack-rubric.md) - Technology evaluation criteria

## Testing

Run tests for each component:

```bash
# Test task ordering
python3 scripts/test_task_ordering.py

# Test tech stack selector
python3 scripts/test_tech_stack_selector.py

# Test decision logger
python3 scripts/test_decision_logger.py

# Test all components
python3 -m pytest scripts/test_*.py
```

## Performance

| Component | Input Size | Time |
|-----------|-----------|------|
| Task Ordering | 50 tasks | < 100ms |
| Task Ordering | 200 tasks | < 500ms |
| Tech Stack Selector | Standard | < 200ms |
| Dependency Analysis | 1000 deps | < 500ms |
| Decision Logger (log) | Single | < 10ms |
| Decision Logger (query) | 100 decisions | < 50ms |
| Decision Logger (learn) | 100 decisions | < 100ms |
| Decision Logger (aggregate) | 10 decisions | < 200ms |

## Configuration

Environment variables:

```bash
# Beads configuration
export BEADS_DB_PATH="$HOME/.beads/db.jsonl"

# Decision engine settings
export DECISION_ENGINE_LOG_LEVEL="info"
export DECISION_ENGINE_CACHE_TTL="3600"
```

## Troubleshooting

### Task Ordering Issues

**Problem**: All tasks are sequential
```bash
# Check for conflicts
python3 scripts/order_tasks.py --no-conflicts

# Try different strategy
python3 scripts/order_tasks.py --strategy parallel_maximizing
```

**Problem**: Circular dependencies detected
```bash
# Find the cycle
bd show <issue-id>
# Review and fix depends_on fields
```

### Tech Stack Selector Issues

**Problem**: Poor recommendations
```bash
# Provide more context
python3 scripts/tech_stack_selector.py \
  "Build REST API" \
  --context "existing stack: node, postgres"
```

## Contributing

When adding new decision capabilities:

1. Create script in `scripts/`
2. Add tests in `scripts/test_*.py`
3. Update reference documentation in `references/`
4. Update this README

## License

Part of the Maestro autonomous orchestrator system.
