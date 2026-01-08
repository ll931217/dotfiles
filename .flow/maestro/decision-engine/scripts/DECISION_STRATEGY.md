# Decision Strategy Framework

The Decision Strategy Framework provides a flexible, extensible foundation for autonomous decision-making in the Maestro Orchestrator. It implements the Strategy Pattern to support various decision types including tech stack selection, task ordering, architecture decisions, and more.

## Overview

The framework consists of three main components:

1. **DecisionContext**: Captures all relevant information for making a decision
2. **Decision**: Represents the outcome of a decision with full rationale
3. **DecisionStrategy**: Base class for implementing custom decision strategies
4. **DecisionRegistry**: Centralized registry for managing strategies

## Architecture

```
DecisionContext (Input)
    ↓
DecisionStrategy (Processing)
    ↓
Decision (Output)
```

### Key Classes

#### DecisionContext

Encapsulates all information needed for autonomous decision-making:

```python
context = DecisionContext(
    prd_requirements={"feature": "authentication"},
    current_state={"language": "python", "framework": "fastapi"},
    available_options=[
        {"name": "Passport.js", "oauth_support": True},
        {"name": "Auth0", "oauth_support": True},
    ],
    constraints={"timeline": "2 weeks", "budget": "low"},
    session_id="session-123"
)
```

**Attributes:**
- `prd_requirements`: Requirements from the PRD document
- `current_state`: Current state of the codebase/project
- `available_options`: List of viable options to consider
- `constraints`: Technical, business, or resource constraints
- `session_id`: Unique identifier for the session
- `timestamp`: Auto-generated ISO timestamp
- `metadata`: Additional context information

**Methods:**
- `to_dict()`: Serialize to dictionary
- `get_constraint(key, default=None)`: Get constraint value
- `get_requirement(key, default=None)`: Get requirement value
- `has_option(name)`: Check if option exists

#### Decision

Represents an autonomous decision with full rationale and confidence:

```python
decision = Decision(
    choice="Passport.js",
    rationale="Best fit for OAuth 2.0 requirements with existing codebase",
    confidence=0.85,
    alternatives=["Auth.js", "Auth0"],
    context_snapshot=context.to_dict(),
    decision_type="tech_stack"
)
```

**Attributes:**
- `choice`: The selected option
- `rationale`: Explanation of why this choice was made
- `confidence`: Confidence level (0.0 to 1.0)
- `alternatives`: List of alternatives considered
- `context_snapshot`: Snapshot of context at decision time
- `timestamp`: Auto-generated ISO timestamp
- `decision_type`: Type of decision (tech_stack, task_ordering, etc.)
- `metadata`: Additional decision metadata

**Methods:**
- `to_dict()`: Serialize to dictionary
- `get_confidence_level()`: Get human-readable level (high/medium/low)
- `is_high_confidence()`: Check if confidence >= 0.8

**Validation:**
- Confidence must be between 0.0 and 1.0
- Choice cannot be empty
- Rationale cannot be empty

#### DecisionStrategy

Abstract base class for implementing decision strategies:

```python
class TechStackStrategy(DecisionStrategy):
    def decide(self, context: DecisionContext) -> Decision:
        # Score all options
        scored = [
            (self.score_option(opt, context), opt)
            for opt in context.available_options
        ]

        # Select best option
        top_score, top_option = max(scored, key=lambda x: x[0])

        return Decision(
            choice=top_option["name"],
            rationale=f"Best score: {top_score:.2f}",
            confidence=self.get_confidence(...),
            alternatives=[opt["name"] for _, opt in scored[1:]],
            context_snapshot=context.to_dict(),
            decision_type="tech_stack"
        )

    def get_strategy_name(self) -> str:
        return "tech_stack_scorer"

    def get_supported_decision_types(self) -> List[str]:
        return ["tech_stack", "database"]
```

**Required Methods:**
- `decide(context)`: Make and return a Decision
- `get_strategy_name()`: Return unique strategy name

**Optional Override Methods:**
- `validate_context(context)`: Validate context has required data
- `score_option(option, context)`: Score a single option (default: 0.5)
- `get_confidence(top_score, second_score, option_count)`: Calculate confidence
- `get_strategy_description()`: Return strategy description
- `get_supported_decision_types()`: Return list of supported types

#### DecisionRegistry

Centralized registry for managing decision strategies:

```python
# Create registry
registry = DecisionRegistry()

# Register strategies
registry.register("tech_stack", TechStackStrategy())
registry.register("task_ordering", TaskOrderingStrategy())

# Get strategy by name
strategy = registry.get_strategy("tech_stack")

# Get strategies by type
tech_strategies = registry.get_strategies_by_type("tech_stack")

# Select best strategy for context
strategy = registry.select_strategy(
    "tech_stack",
    context=context,
    preference="tech_stack"  # optional
)

# List all strategies
names = registry.list_strategies()

# Export registry state
state = registry.export_registry()
```

**Thread Safety:**
The registry is designed to be thread-safe for concurrent access.

## Confidence Calculation

Confidence is calculated based on three factors:

1. **Top Score Quality** (60% weight): Higher top score = higher confidence
2. **Score Gap** (40% weight): Larger gap between top and second = higher confidence
3. **Option Count** (10% boost if >= 3 options): More options = more confident

**Formula:**
```python
confidence = (top_score * 0.6) + min((top_score - second_score) * 0.4, 0.4)

if option_count >= 3:
    confidence *= 1.1
elif option_count < 2:
    confidence *= 0.8

confidence = min(confidence, 1.0)
```

**Confidence Levels:**
- **High**: >= 0.8 (clear winner with high score)
- **Medium**: 0.5 - 0.79 (moderate confidence)
- **Low**: < 0.5 (uncertain or limited data)

## Global Registry

A global registry instance is available for convenience:

```python
from decision_strategy import (
    register_strategy,
    get_strategy,
    list_strategies,
    get_global_registry
)

# Register strategy
register_strategy("my_strategy", MyStrategy())

# Get strategy
strategy = get_strategy("my_strategy")

# List all strategies
strategies = list_strategies()

# Access global registry directly
registry = get_global_registry()
```

## Implementation Example

### Complete Tech Stack Strategy

```python
class TechStackStrategy(DecisionStrategy):
    """Autonomous tech stack selection strategy."""

    def decide(self, context: DecisionContext) -> Decision:
        # Validate context
        self.validate_context(context)

        # Score all options
        scored_options = []
        for option in context.available_options:
            score = self._score_option(option, context)
            scored_options.append((score, option))

        # Sort by score
        scored_options.sort(key=lambda x: x[0], reverse=True)

        # Extract results
        top_score, top_option = scored_options[0]
        second_score = scored_options[1][0] if len(scored_options) > 1 else 0.0

        # Calculate confidence
        confidence = self.get_confidence(
            top_score, second_score, len(scored_options)
        )

        # Build rationale
        rationale = self._build_rationale(top_option, top_score, context)

        return Decision(
            choice=top_option["name"],
            rationale=rationale,
            confidence=confidence,
            alternatives=[opt["name"] for _, opt in scored_options[1:]],
            context_snapshot=context.to_dict(),
            decision_type="tech_stack"
        )

    def get_strategy_name(self) -> str:
        return "tech_stack_existing_first"

    def get_supported_decision_types(self) -> List[str]:
        return ["tech_stack", "database", "framework"]

    def _score_option(self, option: Dict, context: DecisionContext) -> float:
        """Score an option based on multiple factors."""
        score = 0.5

        # Existing usage (40 points)
        if self._check_existing(option, context):
            score += 0.4

        # Maturity (25 points)
        score += self._score_maturity(option) * 0.25

        # Fit (25 points)
        score += self._score_fit(option, context) * 0.25

        return min(score, 1.0)

    def _check_existing(self, option: Dict, context: DecisionContext) -> bool:
        """Check if option already exists in codebase."""
        existing = context.current_state.get("existing", [])
        return any(option["name"].lower() in str(e).lower() for e in existing)

    def _score_maturity(self, option: Dict) -> float:
        """Score based on ecosystem maturity."""
        stars = option.get("github_stars", 0)
        if stars >= 50000:
            return 1.0
        elif stars >= 10000:
            return 0.8
        elif stars >= 1000:
            return 0.5
        else:
            return 0.2

    def _score_fit(self, option: Dict, context: DecisionContext) -> float:
        """Score based on fit for requirements."""
        requirements = context.prd_requirements.get("requirements", [])
        features = option.get("features", [])

        matches = sum(1 for req in requirements if req in features)
        return matches / len(requirements) if requirements else 0.5

    def _build_rationale(
        self,
        option: Dict,
        score: float,
        context: DecisionContext
    ) -> str:
        """Build human-readable rationale."""
        reasons = []

        if self._check_existing(option, context):
            reasons.append("Already in codebase")

        if self._score_maturity(option) >= 0.8:
            reasons.append("Mature ecosystem")

        if self._score_fit(option, context) >= 0.8:
            reasons.append("Excellent fit for requirements")

        return "; ".join(reasons) if reasons else "Selected by scoring"
```

## Testing

The framework includes comprehensive unit tests:

```bash
# Run all tests
python3 test_decision_strategy.py

# Run specific test class
python3 test_decision_strategy.py TestDecisionStrategy

# Run with verbose output
python3 test_decision_strategy.py -v
```

**Test Coverage:**
- DecisionContext: 11 tests
- Decision: 9 tests
- DecisionStrategy: 8 tests
- DecisionRegistry: 18 tests
- GlobalRegistry: 5 tests
- IntegrationScenarios: 4 tests

**Total:** 50+ tests covering all functionality

## Best Practices

### 1. Strategy Design

- **Keep strategies stateless**: Strategies should be thread-safe and reusable
- **Use clear naming**: Follow pattern `<category>_<strategy>` (e.g., `tech_stack_existing_first`)
- **Document supported types**: Clearly list which decision types the strategy handles
- **Validate inputs**: Override `validate_context()` for custom validation

### 2. Confidence Scoring

- **Use multiple factors**: Combine existing usage, maturity, fit, etc.
- **Weight appropriately**: Most important factors should have highest weights
- **Cap at 1.0**: Ensure scores never exceed 1.0
- **Document rationale**: Explain why scores are calculated this way

### 3. Decision Context

- **Include all relevant data**: PRD requirements, current state, constraints
- **Use structured data**: Lists and dictionaries instead of free text
- **Add metadata**: Include any additional context that might be useful
- **Snapshot context**: Always include context snapshot in decisions

### 4. Decision Output

- **Provide clear rationale**: Explain why the choice was made
- **Include alternatives**: List other options that were considered
- **Calculate confidence**: Use the provided confidence calculation or custom
- **Set decision type**: Always specify the decision type

### 5. Registry Usage

- **Use global registry**: For most cases, use the global registry
- **Register early**: Register strategies at application startup
- **Use descriptive names**: Strategy names should be self-documenting
- **Handle missing strategies**: Always check for None when getting strategies

## Integration with Existing Components

### Decision Logger

The Decision class is compatible with the existing DecisionLogger:

```python
from decision_logger import DecisionLogger
from decision_strategy import DecisionStrategy, DecisionContext

# Make decision
strategy = MyStrategy()
context = DecisionContext(...)
decision = strategy.decide(context)

# Log decision
logger = DecisionLogger()
logger.log_decision(
    "tech_stack",
    {
        "decision": decision.choice,
        "rationale": decision.rationale,
        "context": {
            "confidence": decision.get_confidence_level(),
            **decision.context_snapshot
        },
        "alternatives_considered": [
            {"option": alt, "reason_rejected": "Lower score"}
            for alt in decision.alternatives
        ]
    }
)
```

### Tech Stack Selector

Integrate with existing tech stack selector:

```python
from tech_stack_selector import TechStackSelector
from decision_strategy import DecisionStrategy

class EnhancedTechStackStrategy(DecisionStrategy):
    def decide(self, context: DecisionContext) -> Decision:
        # Use existing selector
        selector = TechStackSelector(context.current_state.get("project_root"))
        result = selector.select_tech_stack(
            context.prd_requirements.get("requirement"),
            context.prd_requirements.get("category")
        )

        return Decision(
            choice=result["output"]["decision"],
            rationale=result["output"]["rationale"],
            confidence=self._map_confidence(result["output"]["confidence"]),
            alternatives=result["output"]["alternatives"],
            context_snapshot=context.to_dict(),
            decision_type="tech_stack"
        )
```

## Future Enhancements

### Planned Features

1. **Strategy Chaining**: Combine multiple strategies for complex decisions
2. **Learning from History**: Integrate with DecisionLogger for adaptive strategies
3. **Confidence Calibration**: Improve confidence calculation based on outcomes
4. **Parallel Strategy Execution**: Run multiple strategies and compare results
5. **Strategy Composition**: Build complex strategies from simple components

### Extension Points

1. **Custom Scoring Functions**: Plug in different scoring algorithms
2. **Confidence Calculators**: Use domain-specific confidence models
3. **Context Enrichers**: Automatically enhance context with additional data
4. **Decision Validators**: Post-decision validation and adjustment
5. **Strategy Selectors**: Advanced strategy selection based on context

## API Reference

### DecisionContext

```python
DecisionContext(
    prd_requirements: Dict[str, Any],
    current_state: Dict[str, Any],
    available_options: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    session_id: str,
    timestamp: str = <auto-generated>,
    metadata: Dict[str, Any] = {}
)
```

### Decision

```python
Decision(
    choice: str,
    rationale: str,
    confidence: float,  # 0.0 to 1.0
    alternatives: List[str],
    context_snapshot: Dict[str, Any],
    timestamp: str = <auto-generated>,
    decision_type: str = "generic",
    metadata: Dict[str, Any] = {}
)
```

### DecisionStrategy

```python
class DecisionStrategy(ABC):
    @abstractmethod
    def decide(self, context: DecisionContext) -> Decision:
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        pass

    def validate_context(self, context: DecisionContext) -> bool:
        pass

    def score_option(self, option: Dict, context: DecisionContext) -> float:
        pass

    def get_confidence(self, top_score: float, second_score: float, option_count: int) -> float:
        pass
```

### DecisionRegistry

```python
class DecisionRegistry:
    def register(self, name: str, strategy: DecisionStrategy) -> None:
        pass

    def unregister(self, name: str) -> None:
        pass

    def get_strategy(self, name: str) -> Optional[DecisionStrategy]:
        pass

    def get_strategies_by_type(self, decision_type: str) -> List[DecisionStrategy]:
        pass

    def select_strategy(self, decision_type: str, context: Optional[DecisionContext] = None, preference: Optional[str] = None) -> Optional[DecisionStrategy]:
        pass

    def list_strategies(self) -> List[str]:
        pass

    def list_decision_types(self) -> List[str]:
        pass
```

## Contributing

When adding new strategies:

1. **Inherit from DecisionStrategy**: Implement all required methods
2. **Follow naming conventions**: Use `<category>_<strategy>` pattern
3. **Add comprehensive tests**: Test all decision paths
4. **Document the strategy**: Explain when and how to use it
5. **Register with global registry**: Make strategy discoverable

## License

Part of the Maestro Orchestrator project.
