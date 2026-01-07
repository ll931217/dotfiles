# Decision Logger - System Architecture

## Overview

The Decision Logger provides a robust backend system for tracking, storing, and learning from decisions made during software development sessions. It implements a layered architecture with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    CLI       │  │   Library    │  │   Maestro    │          │
│  │   Interface  │  │    API       │  │  Integration │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Decision Logger Core                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  DecisionLogger Class                     │  │
│  │  • log_decision()     • get_session_decisions()          │  │
│  │  • get_historical()   • learn_from_past()                │  │
│  │  • aggregate_to_historical()                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Decision   │  │ DecisionLog  │  │   Summary    │          │
│  │   Dataclass  │  │   Dataclass  │  │  Generator   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage & Persistence Layer                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  Session Store   │  │  Historical Store │                    │
│  │  (decisions.json)│  │  (by category)   │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Learning & Analytics Layer                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Relevance Scoring│  │ Pattern Learning │                    │
│  │  • Text match    │  │  • Success rates │                    │
│  │  • Context match │  │  • Frequencies   │                    │
│  │  • Semantic sim  │  │  • Anti-patterns │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Core API

#### `POST /decisions/log`
Log a new decision.

**Request**:
```json
{
  "decision_type": "tech_stack",
  "decision": {
    "decision": "Use FastAPI framework",
    "rationale": "Modern async support",
    "phase": "plan",
    "alternatives_considered": [...],
    "context": {...},
    "impact": {...}
  }
}
```

**Response**:
```json
{
  "decision_id": "decision-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "logged"
}
```

#### `GET /decisions/session/:session_id`
Get all decisions for a session.

**Response**:
```json
{
  "session_id": "uuid",
  "decisions": [
    {
      "decision_id": "decision-001",
      "category": "tech_stack",
      "decision": "Use FastAPI",
      "rationale": "...",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "summary": {
    "total_decisions": 5,
    "decisions_by_category": {...}
  }
}
```

#### `GET /decisions/historical`
Query historical decisions.

**Query Parameters**:
- `category`: Filter by category
- `limit`: Max results (default: 50)

**Response**:
```json
{
  "decisions": [
    {
      "decision_id": "decision-001",
      "session_id": "uuid",
      "category": "tech_stack",
      "decision": "Use FastAPI",
      "rationale": "...",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### `POST /decisions/learn`
Learn from past decisions.

**Request**:
```json
{
  "context": {
    "category": "tech_stack",
    "project_type": "web_api",
    "keywords": ["async", "api"],
    "feature_description": "REST API backend"
  }
}
```

**Response**:
```json
{
  "relevant_decisions": [
    {
      "decision": "Use FastAPI",
      "rationale": "...",
      "relevance_score": 0.94,
      "session_id": "uuid"
    }
  ]
}
```

#### `POST /decisions/aggregate`
Aggregate session decisions to historical.

**Response**:
```json
{
  "status": "aggregated",
  "decisions_processed": 5,
  "categories_updated": ["tech_stack", "architecture"]
}
```

#### `GET /decisions/summary`
Export session summary.

**Response**:
```json
{
  "session_id": "uuid",
  "total_decisions": 5,
  "summary": {
    "total_decisions": 5,
    "decisions_by_category": {
      "tech_stack": 2,
      "architecture": 2,
      "task_ordering": 1
    },
    "high_confidence_decisions": 4,
    "high_risk_decisions": 1
  },
  "decisions_by_category": {...}
}
```

## Database Schema

### Session Store (decisions.json)

```json
{
  "$schema": "decisions.schema.json",
  "session_id": "uuid",
  "generated_at": "2024-01-01T00:00:00Z",
  "decisions": [
    {
      "decision_id": "decision-001",
      "timestamp": "2024-01-01T00:00:00Z",
      "category": "tech_stack",
      "decision": "Use FastAPI",
      "rationale": "Modern async framework",
      "phase": "plan",
      "alternatives_considered": [
        {
          "option": "Flask",
          "reason_rejected": "No native async"
        }
      ],
      "context": {
        "confidence": "high",
        "sources": ["FastAPI docs"],
        "analysis_results": {}
      },
      "impact": {
        "scope": "codebase",
        "risk_level": "low",
        "reversibility": "moderate"
      }
    }
  ],
  "summary": {
    "total_decisions": 5,
    "decisions_by_category": {...},
    "high_confidence_decisions": 4,
    "high_risk_decisions": 1
  }
}
```

### Historical Store (historical-{category}.json)

#### Tech Stack

```json
{
  "$schema": "historical-tech-stack.schema.json",
  "version": "1.0",
  "last_updated": "2024-01-01T00:00:00Z",
  "decisions": [
    {
      "decision_id": "decision-001",
      "session_id": "uuid",
      "timestamp": "2024-01-01T00:00:00Z",
      "category": "framework",
      "choice": "FastAPI",
      "rationale": "Modern async framework",
      "decision_factors": {
        "existing_dependency": true,
        "codebase_patterns": true,
        "ecosystem_maturity": "stable",
        "community_size": "large"
      },
      "alternatives": ["Flask", "Django"],
      "outcome": {
        "successful": true,
        "issues": [],
        "would_choose_again": true
      }
    }
  ],
  "patterns": {
    "preferred_by_category": {
      "framework": {
        "technology": "FastAPI",
        "success_rate": 0.95,
        "usage_count": 20
      }
    },
    "avoid_list": []
  }
}
```

#### Architecture

```json
{
  "$schema": "historical-architecture.schema.json",
  "version": "1.0",
  "last_updated": "2024-01-01T00:00:00Z",
  "decisions": [
    {
      "decision_id": "decision-002",
      "session_id": "uuid",
      "timestamp": "2024-01-01T00:00:00Z",
      "pattern_type": "architectural",
      "pattern_name": "Repository",
      "description": "Data access abstraction layer",
      "rationale": "Separates concerns",
      "principles_applied": [
        "single_responsibility",
        "dependency_inversion"
      ],
      "outcome": {
        "successful": true,
        "maintainability_impact": "improved"
      }
    }
  ],
  "patterns": {
    "codebase_fingerprints": {
      "Repository": {
        "pattern_name": "Repository",
        "usage_frequency": 15,
        "consistency_score": 0.9
      }
    },
    "anti_patterns": []
  }
}
```

## Performance Characteristics

### Read Operations

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Get session decisions | O(n) | n = decisions in session |
| Query historical | O(m) | m = decisions in category |
| Learn from past | O(m*k) | m = decisions, k = keywords |

### Write Operations

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Log decision | O(1) | In-memory, async persist |
| Aggregate to historical | O(n) | n = session decisions |

### Scalability

- **Session size**: Handles 1000+ decisions per session
- **Historical size**: Optimized for 10,000+ decisions per category
- **Query performance**: < 100ms for typical queries
- **Storage**: JSON files (migrate to DB for > 100K decisions)

## Caching Strategy

### In-Memory Cache

```python
class DecisionLogger:
    def __init__(self):
        self._session_cache = {}  # session_id -> DecisionLog
        self._historical_cache = {}  # category -> decisions

    def get_session_decisions(self, session_id):
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        # Load from file and cache
```

### Cache Invalidation

- Session cache: Invalidated on new decision
- Historical cache: Invalidated after aggregation
- TTL: 5 minutes for historical cache

## Security Considerations

### Input Validation

```python
def log_decision(self, decision_type, decision):
    # Validate required fields
    if "decision" not in decision:
        raise ValueError("Missing required field")

    # Sanitize input
    decision["decision"] = sanitize(decision["decision"])
    decision["rationale"] = sanitize(decision["rationale"])

    # Validate category
    if decision_type not in VALID_CATEGORIES:
        raise ValueError("Invalid category")
```

### Path Traversal Prevention

```python
def _get_session_path(self, session_id):
    # Validate session_id is UUID
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise ValueError("Invalid session ID")

    # Construct path safely
    return self.base_path / "sessions" / session_id
```

## Error Handling

### Error Categories

1. **Validation Errors** (400)
   - Missing required fields
   - Invalid category
   - Malformed data

2. **Not Found Errors** (404)
   - Session doesn't exist
   - Historical file missing

3. **System Errors** (500)
   - File I/O failures
   - Permission denied
   - Corrupted data

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required field: rationale",
    "details": {
      "field": "rationale",
      "expected": "string"
    }
  }
}
```

## Integration Patterns

### With Maestro Orchestrator

```python
class MaestroOrchestrator:
    def __init__(self):
        self.decision_logger = DecisionLogger()

    def plan_phase(self, requirements):
        # Get tech stack recommendation
        stack = self.tech_stack_selector.recommend(requirements)

        # Log decision
        self.decision_logger.log_decision(
            decision_type="tech_stack",
            decision={
                "decision": f"Use {stack['framework']}",
                "rationale": stack['rationale'],
                "phase": "plan",
            }
        )

    def cleanup_phase(self):
        # Aggregate for future learning
        self.decision_logger.aggregate_to_historical()
```

## Future Enhancements

### Phase 1: Database Migration

```python
class DatabaseDecisionLogger(DecisionLogger):
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection

    def log_decision(self, decision_type, decision):
        # Write to database instead of file
        self.db.execute(
            "INSERT INTO decisions (...) VALUES (...)"
        )
```

### Phase 2: Machine Learning

```python
class MLDecisionLogger(DecisionLogger):
    def learn_from_past(self, context):
        # Use ML for relevance scoring
        features = self._extract_features(context)
        scores = self.model.predict(features)
        return self._rank_by_score(scores)
```

### Phase 3: Distributed Decision Logging

```python
class DistributedDecisionLogger(DecisionLogger):
    def __init__(self, cluster_config):
        self.cluster = Cluster(cluster_config)

    def log_decision(self, decision_type, decision):
        # Replicate across cluster
        self.cluster.replicate(decision)
```

## Monitoring & Observability

### Metrics to Track

```python
from prometheus_client import Counter, Histogram

decision_counter = Counter(
    'decisions_logged_total',
    'Total decisions logged',
    ['category', 'confidence']
)

query_duration = Histogram(
    'decision_query_duration_seconds',
    'Decision query duration',
    ['operation']
)
```

### Logging

```python
import logging

logger = logging.getLogger('decision_logger')

def log_decision(self, decision_type, decision):
    logger.info(
        "Logging decision",
        extra={
            "decision_type": decision_type,
            "decision": decision["decision"],
            "session_id": self.session_id,
        }
    )
```

## Summary

The Decision Logger provides a production-ready backend system for:

1. **Tracking decisions**: Full audit trail with rationale
2. **Learning from history**: Pattern recognition and relevance scoring
3. **Scalable storage**: Session-based with historical aggregation
4. **Clean API**: Simple, intuitive interface
5. **Extensible design**: Easy to add new features

The system follows best practices for:
- API design (RESTful principles)
- Data modeling (schema validation)
- Performance (caching, efficient queries)
- Security (input validation, path safety)
- Error handling (clear error categories)
