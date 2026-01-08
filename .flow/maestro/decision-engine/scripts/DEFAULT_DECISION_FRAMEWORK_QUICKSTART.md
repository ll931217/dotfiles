# DefaultDecisionFramework Quick Reference

## What is it?

A fallback decision framework that applies a systematic hierarchy to select the best option when specialized strategies can't determine a clear winner.

## Decision Hierarchy

1. **Best Practices** (35%) - Industry standards
2. **Existing Patterns** (30%) - What's already in the codebase
3. **Simplicity** (20%) - Simplest viable option
4. **Consistency** (15%) - Match existing code style

## Basic Usage

```python
from decision_strategy import DecisionContext
from default_decision_framework import DefaultDecisionFramework

framework = DefaultDecisionFramework()

context = DecisionContext(
    prd_requirements={"feature": "authentication"},
    current_state={
        "primary_language": "JavaScript",
        "ecosystem": "nodejs",
    },
    available_options=[
        {"name": "Passport.js", "category": "authentication"},
        {"name": "Auth0", "category": "authentication"},
    ],
    constraints={},
    session_id="my-decision"
)

decision = framework.decide(context)

print(f"Selected: {decision.choice}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Rationale:\n{decision.rationale}")
```

## Option Format

Options are dictionaries with these optional fields:

```python
{
    "name": "Option Name",              # Required (or "id")
    "category": "authentication",       # For best practices lookup
    "language": "Python",               # For consistency checking
    "framework": "FastAPI",             # For consistency checking
    "ecosystem": "python",              # For consistency checking
    "complexity": "LOW|MEDIUM|HIGH",    # For simplicity scoring
    "lines_of_code": 100,               # For simplicity scoring
    "cognitive_load": 5,                # For simplicity scoring (1-10)
    "detect_patterns": ["pattern1"],    # For pattern detection
}
```

## Built-in Best Practices

The framework includes best practices knowledge for:

- **Authentication**: Passport.js, Auth.js, Auth0, custom JWT
- **Database**: PostgreSQL, MySQL, MongoDB, SQLite, Redis
- **Testing**: pytest, unittest, nose2
- **API Frameworks**: FastAPI, Flask, Django REST

## Understanding the Decision Output

```python
decision.choice          # Selected option
decision.confidence      # 0.0-1.0 confidence score
decision.rationale       # Detailed explanation
decision.alternatives    # List of other options considered

# Score breakdown
decision.metadata["scores"][option_name] = {
    "total": 0.75,              # Overall weighted score
    "best_practices": 1.0,      # Industry standard score
    "existing_patterns": 0.8,   # Codebase pattern match
    "simplicity": 0.6,          # Simplicity score
    "consistency": 0.9,         # Consistency with existing code
}
```

## Integration with Registry

```python
from decision_strategy import register_strategy, get_global_registry

# Register the framework
register_strategy("default", DefaultDecisionFramework())

# Use via registry
registry = get_global_registry()
framework = registry.select_strategy(
    decision_type="tech_stack",
    preference="default"
)

decision = framework.decide(context)
```

## Supported Decision Types

- `tech_stack` - Technology selection
- `task_ordering` - Task sequencing
- `approach` - Implementation approaches
- `architecture` - Architectural patterns
- `generic` - Any other decision type

## Tips for Best Results

1. **Provide category** - Enables best practices lookup
2. **Include detect_patterns** - Improves pattern matching accuracy
3. **Set complexity level** - Helps simplicity assessment
4. **Specify ecosystem** - Improves consistency checking
5. **Add constraints** - Influences final decision

## Common Patterns

### Selecting an Authentication Library

```python
context = DecisionContext(
    prd_requirements={"feature": "authentication"},
    current_state={"primary_language": "JavaScript", "ecosystem": "nodejs"},
    available_options=[
        {"name": "Passport.js", "category": "authentication", "ecosystem": "nodejs"},
        {"name": "Auth0", "category": "authentication"},
    ],
    constraints={},
    session_id="auth-select"
)
```

### Selecting a Database

```python
context = DecisionContext(
    prd_requirements={"feature": "database", "requirements": ["ACID compliance"]},
    current_state={"primary_language": "Python"},
    available_options=[
        {"name": "PostgreSQL", "category": "database", "complexity": "MEDIUM"},
        {"name": "MongoDB", "category": "database", "complexity": "LOW"},
    ],
    constraints={},
    session_id="db-select"
)
```

### Selecting a Testing Framework

```python
context = DecisionContext(
    prd_requirements={"feature": "testing"},
    current_state={"primary_language": "Python"},
    available_options=[
        {"name": "pytest", "category": "testing", "complexity": "LOW"},
        {"name": "unittest", "category": "testing", "complexity": "MEDIUM"},
    ],
    constraints={},
    session_id="test-select"
)
```

## Debugging

To see detailed scoring information:

```python
decision = framework.decide(context)

# Print score breakdown
for option, scores in decision.metadata["scores"].items():
    print(f"{option}:")
    print(f"  Total: {scores['total']:.2f}")
    print(f"  Best Practices: {scores['best_practices']:.2f}")
    print(f"  Existing Patterns: {scores['existing_patterns']:.2f}")
    print(f"  Simplicity: {scores['simplicity']:.2f}")
    print(f"  Consistency: {scores['consistency']:.2f}")
```

## Testing

Run the test suite:

```bash
python test_default_decision_framework.py
```

Expected output: 27/27 tests passing (100%)

## See Also

- `DEFAULT_DECISION_FRAMEWORK_SUMMARY.md` - Detailed implementation guide
- `example_default_decision_framework.py` - Usage examples
- `test_default_decision_framework.py` - Test examples
