# ApproachStrategy Documentation

## Overview

The `ApproachStrategy` implements the DecisionStrategy pattern for selecting between alternative implementation approaches. It evaluates alternatives based on complexity, performance, maintainability, and testability, applying a decision hierarchy to choose the best approach.

## Use Cases

- **Auto-Recovery**: When an initial implementation approach fails, select a fallback approach
- **Implementation Planning**: Choose between different implementation strategies before coding
- **Refactoring Decisions**: Select the best refactoring approach from multiple alternatives
- **Architecture Decisions**: Choose between architectural patterns or implementation styles

## Architecture

```
DecisionContext (Input)
    ↓
ApproachStrategy.decide()
    ↓
Parse ImplementationAlternatives
    ↓
Score Each Alternative (Complexity, Performance, Maintainability, Testability)
    ↓
Apply Decision Hierarchy (Best Practices → Existing → Simplicity → Consistency)
    ↓
Select Best Approach
    ↓
Decision (Output with Rationale)
```

## ImplementationAlternative

Represents an alternative implementation approach with evaluation criteria:

```python
@dataclass
class ImplementationAlternative:
    name: str                          # Unique identifier
    description: str                   # Human-readable description
    complexity: str                    # LOW, MEDIUM, HIGH
    performance: str                   # FAST, MODERATE, SLOW
    maintainability: str               # HIGH, MEDIUM, LOW
    testability: str                   # HIGH, MEDIUM, LOW
    lines_of_code: Optional[int]       # Estimated LOC
    cognitive_load: Optional[int]      # Cognitive complexity (1-10)
```

### Criteria Levels

**Complexity:**
- `LOW`: Simple, straightforward implementation (< 100 LOC)
- `MEDIUM`: Moderate complexity with some edge cases (100-500 LOC)
- `HIGH`: Complex implementation with many edge cases (> 500 LOC)

**Performance:**
- `FAST`: Optimized for speed, minimal resource usage
- `MODERATE`: Acceptable performance for most use cases
- `SLOW`: Lower performance but acceptable for specific scenarios

**Maintainability:**
- `HIGH`: Clean code, well-structured, easy to modify
- `MEDIUM`: Maintainable with some effort
- `LOW`: Difficult to maintain, high coupling

**Testability:**
- `HIGH`: Easy to test, minimal mocking required
- `MEDIUM`: Testable with some setup
- `LOW`: Difficult to test, complex mocking required

## Scoring System

The strategy scores each alternative based on four criteria (total 1.0):

### 1. Complexity (30% weight)

Lower complexity = higher score
- LOW complexity: 1.0 points
- MEDIUM complexity: 0.6 points
- HIGH complexity: 0.3 points

```python
LOW complexity → 1.0 * 0.30 = 0.30
MEDIUM complexity → 0.6 * 0.30 = 0.18
HIGH complexity → 0.3 * 0.30 = 0.09
```

### 2. Performance (25% weight)

Better performance = higher score
- FAST: 1.0 points → 0.25
- MODERATE: 0.7 points → 0.175
- SLOW: 0.4 points → 0.10

### 3. Maintainability (25% weight)

Higher maintainability = higher score
- HIGH: 1.0 points → 0.25
- MEDIUM: 0.6 points → 0.15
- LOW: 0.3 points → 0.075

### 4. Testability (20% weight)

Higher testability = higher score
- HIGH: 1.0 points → 0.20
- MEDIUM: 0.6 points → 0.12
- LOW: 0.3 points → 0.06

## Decision Hierarchy

After base scoring, the strategy applies hierarchy bonuses:

### 1. Best Practices (+15%)

Applied when the alternative follows industry standards or best practices.

**Triggers:**
- `prefer_best_practices` is True in requirements
- AND maintainability is HIGH
- AND testability is HIGH
- OR description contains "standard", "best practice", "recommended", "idiomatic", "clean code", "solid"

### 2. Existing Patterns (+10%)

Applied when the alternative matches existing codebase patterns.

**Triggers:**
- `existing_patterns` in current_state
- AND alternative name/description matches existing patterns

### 3. Simplicity Bonus (+10%)

Applied when complexity is LOW (regardless of other factors).

This implements the "simplicity first" principle.

### 4. Consistency Bonus (+5%)

Applied when the alternative maintains architectural consistency.

**Triggers:**
- `architecture` in current_state
- AND description contains "consistent", "architecture", "pattern", "modular", "layered", "separation"

## Usage Examples

### Basic Usage

```python
from approach_strategy import ApproachStrategy, create_simple_alternative
from decision_strategy import DecisionContext

# Create strategy
strategy = ApproachStrategy()

# Define alternatives
alternatives = [
    create_simple_alternative(
        name="simple_approach",
        description="Simple, straightforward implementation",
        complexity="LOW",
        performance="MODERATE",
        maintainability="HIGH",
        testability="HIGH"
    ),
    create_simple_alternative(
        name="complex_approach",
        description="Complex but highly optimized",
        complexity="HIGH",
        performance="FAST",
        maintainability="LOW",
        testability="LOW"
    )
]

# Create context
context = DecisionContext(
    prd_requirements={"feature": "user authentication"},
    current_state={},
    available_options=alternatives,
    constraints={},
    session_id="session-123"
)

# Make decision
decision = strategy.decide(context)

print(f"Selected: {decision.choice}")
print(f"Rationale: {decision.rationale}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Alternatives: {decision.alternatives}")
```

### Auto-Recovery Scenario

```python
from approach_strategy import select_fallback_approach
from decision_strategy import DecisionContext

# Define alternatives including primary and fallback
alternatives = [
    {
        "name": "primary_approach",
        "description": "Primary implementation approach",
        "complexity": "MEDIUM",
        "performance": "MODERATE",
        "maintainability": "MEDIUM",
        "testability": "MEDIUM"
    },
    {
        "name": "fallback_approach",
        "description": "Simple fallback approach",
        "complexity": "LOW",
        "performance": "MODERATE",
        "maintainability": "HIGH",
        "testability": "HIGH"
    }
]

context = DecisionContext(
    prd_requirements={},
    current_state={},
    available_options=alternatives,
    constraints={},
    session_id="recovery-session"
)

# When primary approach fails, select fallback
fallback = select_fallback_approach("primary_approach", context)

if fallback:
    print(f"Using fallback: {fallback}")
else:
    print("No suitable fallback available")
```

### With Best Practices Preference

```python
requirements = {
    "feature": "authentication",
    "prefer_best_practices": True
}

current_state = {
    "existing_patterns": ["middleware", "passport"]
}

alternatives = [
    {
        "name": "passport_strategy",
        "description": "Use Passport.js (industry standard)",
        "complexity": "LOW",
        "performance": "FAST",
        "maintainability": "HIGH",
        "testability": "HIGH"
    },
    {
        "name": "custom_jwt",
        "description": "Custom JWT implementation",
        "complexity": "HIGH",
        "performance": "FAST",
        "maintainability": "MEDIUM",
        "testability": "MEDIUM"
    }
]

context = DecisionContext(
    prd_requirements=requirements,
    current_state=current_state,
    available_options=alternatives,
    constraints={},
    session_id="auth-selection"
)

decision = strategy.decide(context)
# Should select passport_strategy due to:
# - Best practices bonus (+15%)
# - Existing patterns bonus (+10%)
# - Simplicity bonus (+10%)
```

### Using ImplementationAlternative Objects

```python
from approach_strategy import ImplementationAlternative

alternatives = [
    ImplementationAlternative(
        name="orm_approach",
        description="Use ORM for database access",
        complexity="LOW",
        performance="MODERATE",
        maintainability="HIGH",
        testability="HIGH",
        lines_of_code=150,
        cognitive_load=3
    ),
    ImplementationAlternative(
        name="raw_sql",
        description="Use raw SQL queries",
        complexity="MEDIUM",
        performance="FAST",
        maintainability="MEDIUM",
        testability="LOW",
        lines_of_code=300,
        cognitive_load=6
    )
]

context = DecisionContext(
    prd_requirements={},
    current_state={},
    available_options=alternatives,
    constraints={},
    session_id="db-selection"
)

decision = strategy.decide(context)
```

## Decision Rationale

The strategy provides detailed rationale for each decision:

```python
# Example rationale:
"passport_strategy: Use Passport.js (industry standard). Selected due to:
Low implementation complexity, Excellent performance characteristics,
High maintainability, Excellent testability, Follows industry best practices,
Consistent with existing codebase patterns. (Score: 0.95)"
```

The rationale includes:
- Selected alternative name and description
- Key reasons for selection (complexity, performance, etc.)
- Any hierarchy bonuses applied
- Final score

## Confidence Calculation

Confidence is calculated using the base `DecisionStrategy.get_confidence()` method:

```python
confidence = (top_score * 0.6) + min((top_score - second_score) * 0.4, 0.4)

if option_count >= 3:
    confidence *= 1.1
elif option_count < 2:
    confidence *= 0.8

confidence = min(confidence, 1.0)
```

**Confidence Levels:**
- **High** (>= 0.8): Clear winner with strong score gap
- **Medium** (0.5 - 0.79): Moderate confidence, closer scores
- **Low** (< 0.5): Low confidence, tied or very close scores

## Integration with Decision Logger

```python
from decision_logger import DecisionLogger

# Make decision
decision = strategy.decide(context)

# Log decision
logger = DecisionLogger()
logger.log_decision(
    "approach_selection",
    {
        "decision": decision.choice,
        "rationale": decision.rationale,
        "context": {
            "confidence": decision.get_confidence_level(),
            "complexity": decision.metadata["selected_alternative"]["complexity"],
            "performance": decision.metadata["selected_alternative"]["performance"],
            **decision.context_snapshot
        },
        "alternatives_considered": [
            {
                "option": alt,
                "score": score_data["score"]
            }
            for alt, score_data in zip(
                decision.alternatives,
                decision.metadata["all_scores"][1:]
            )
        ]
    }
)
```

## Testing

Run the comprehensive test suite:

```bash
cd /path/to/decision-engine/scripts
python3 test_approach_strategy.py
```

**Test Coverage:**
- `TestImplementationAlternative`: 3 tests
- `TestApproachStrategy`: 13 tests
- `TestHelperFunctions`: 2 tests
- `TestAutoRecovery`: 3 tests
- `TestScoringCriteria`: 4 tests
- `TestIntegrationScenarios`: 3 tests

**Total:** 30 tests covering all functionality

### Test Categories

1. **Unit Tests**: Test individual methods and scoring
2. **Integration Tests**: Test real-world scenarios
3. **Edge Cases**: Test boundary conditions and error handling
4. **Auto-Recovery**: Test fallback selection logic

## Best Practices

### 1. Defining Alternatives

- Use descriptive names that clearly indicate the approach
- Provide detailed descriptions explaining the implementation
- Be honest about complexity and maintainability
- Consider all four criteria when defining alternatives

### 2. Setting Requirements

- Use `prefer_best_practices=True` when industry standards exist
- Include `existing_patterns` when consistency is important
- Define `architecture` when architectural consistency matters

### 3. Interpreting Results

- High confidence (> 0.8): Clear winner, proceed with confidence
- Medium confidence (0.5-0.8): Good choice, but consider tradeoffs
- Low confidence (< 0.5): Close alternatives, manual review recommended

### 4. Auto-Recovery

- Always include a simple fallback approach
- Order alternatives by preference
- Use `select_fallback_approach()` helper for recovery scenarios

## Common Patterns

### Pattern 1: Library vs Custom Implementation

```python
alternatives = [
    {
        "name": "library_approach",
        "description": "Use established library (best practice)",
        "complexity": "LOW",
        "performance": "FAST",
        "maintainability": "HIGH",
        "testability": "HIGH"
    },
    {
        "name": "custom_approach",
        "description": "Custom implementation",
        "complexity": "HIGH",
        "performance": "FAST",
        "maintainability": "MEDIUM",
        "testability": "MEDIUM"
    }
]
```

### Pattern 2: Simple vs Optimized

```python
alternatives = [
    {
        "name": "simple_approach",
        "description": "Simple but slower implementation",
        "complexity": "LOW",
        "performance": "MODERATE",
        "maintainability": "HIGH",
        "testability": "HIGH"
    },
    {
        "name": "optimized_approach",
        "description": "Complex but optimized",
        "complexity": "HIGH",
        "performance": "FAST",
        "maintainability": "MEDIUM",
        "testability": "MEDIUM"
    }
]
```

### Pattern 3: Centralized vs Distributed

```python
alternatives = [
    {
        "name": "centralized",
        "description": "Centralized error handling",
        "complexity": "LOW",
        "performance": "FAST",
        "maintainability": "HIGH",
        "testability": "HIGH"
    },
    {
        "name": "distributed",
        "description": "Distributed error handling",
        "complexity": "HIGH",
        "performance": "MODERATE",
        "maintainability": "LOW",
        "testability": "LOW"
    }
]
```

## API Reference

### ApproachStrategy

```python
class ApproachStrategy(DecisionStrategy):
    def decide(self, context: DecisionContext) -> Decision:
        """Select best approach from alternatives."""

    def get_strategy_name(self) -> str:
        """Return 'approach_hierarchy'."""

    def get_strategy_description(self) -> str:
        """Return strategy description."""

    def get_supported_decision_types(self) -> List[str]:
        """Return ['approach_selection', 'implementation_alternative', 'auto_recovery']."""
```

### Helper Functions

```python
def create_simple_alternative(
    name: str,
    description: str,
    complexity: str = "MEDIUM",
    performance: str = "MODERATE",
    maintainability: str = "MEDIUM",
    testability: str = "MEDIUM"
) -> ImplementationAlternative:
    """Create a simple implementation alternative."""

def select_fallback_approach(
    failed_approach: str,
    context: DecisionContext
) -> Optional[str]:
    """Select a fallback approach when initial implementation fails."""
```

## Future Enhancements

### Planned Features

1. **Learning from History**: Track which approaches succeed/fail
2. **Adaptive Scoring**: Adjust weights based on project-specific patterns
3. **Risk Assessment**: Add risk scoring to evaluation criteria
4. **Cost Estimation**: Include development time/cost in scoring
5. **Team Expertise**: Factor in team familiarity with approaches

### Extension Points

1. **Custom Scoring Functions**: Override scoring methods for project-specific needs
2. **Additional Criteria**: Add new evaluation criteria (e.g., security, scalability)
3. **Custom Hierarchy**: Modify hierarchy order for specific contexts
4. **Confidence Calibration**: Adjust confidence calculation based on outcomes

## License

Part of the Maestro Orchestrator project.
