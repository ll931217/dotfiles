# Subagent Factory Documentation

## Overview

The Subagent Factory is an intelligent task-to-subagent mapping system that automatically selects appropriate specialized agents based on task descriptions and metadata. It implements a taxonomy-based approach using the `subagent-types.yaml` configuration to match tasks to specialized agents with appropriate skills.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SubagentFactory                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │ TaskCategory    │    │  Subagent        │               │
│  │ Parser          │───▶│  Selector        │               │
│  └─────────────────┘    └──────────────────┘               │
│         │                        │                          │
│         │                        │                          │
│         ▼                        ▼                          │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │ Keyword         │    │  Pattern         │               │
│  │ Extraction      │    │  Matching        │               │
│  └─────────────────┘    └──────────────────┘               │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         FallbackAgentHandler                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. TaskCategoryParser

Analyzes task descriptions to extract relevant keywords and categorize tasks.

**Key Methods:**
- `extract_keywords(task_description)`: Extracts technical terms, file extensions, and phrases
- `categorize_task(task_description, task_metadata)`: Returns category analysis

**Features:**
- File extension detection (`.py`, `.tsx`, `.sql`, etc.)
- Technical term extraction (camelCase, snake_case, kebab-case)
- Common technical phrase recognition
- Task characteristic flags (`has_tests`, `has_ui`, `has_backend`)

### 2. SubagentSelector

Selects appropriate subagent based on category analysis and pattern matching.

**Key Methods:**
- `match_patterns(task_description, category_analysis, patterns)`: Calculates confidence scores
- `select_category(task_description, category_analysis)`: Selects best matching category
- `select_subagent(task_description, task_metadata)`: Returns DetectionResult

**Pattern Matching:**
- Regex-based pattern matching against task descriptions
- Confidence score calculation (0.0 to 1.0)
- Priority-based category selection
- Automatic fallback chain generation

### 3. FallbackAgentHandler

Manages fallback agent selection when primary agents are unavailable.

**Key Methods:**
- `get_fallback_agents(subagent_type, category)`: Returns fallback agent list
- `select_fallback(failed_agent, category, attempted_agents, available_agents)`: Selects next available fallback

**Features:**
- Automatic fallback chain traversal
- Attempted agent tracking
- Exhaustion detection

### 4. SubagentFactory

Main factory orchestrating all components.

**Key Methods:**
- `detect_subagent_type(task_description)`: Quick subagent type detection
- `detect_subagent_detailed(task_description, task_metadata)`: Full detection with metadata
- `detect_skill(task_description)`: Skill trigger detection
- `select_subagent(task_metadata)`: Subagent selection from metadata
- `get_fallback_agents(subagent_type)`: Get fallback chain
- `create_agent_config(subagent_type, task_context)`: Generate complete agent configuration

## Usage Examples

### Basic Usage

```python
from subagent_factory import SubagentFactory

# Initialize factory
factory = SubagentFactory()

# Detect subagent type
subagent_type = factory.detect_subagent_type(
    "Create React component for user authentication"
)
# Returns: "frontend-developer"

# Detailed detection
result = factory.detect_subagent_detailed(
    "Implement REST API endpoint for user management",
    {"files": ["user_service.py"], "dependencies": ["fastapi"]}
)
# Returns: DetectionResult with subagent_type, category, confidence, skill, etc.
```

### Creating Agent Configurations

```python
# Create agent configuration for Task tool
task_context = {
    "description": "Create responsive UI component",
    "prd": "Build user management system",
    "code_patterns": "Component-based architecture",
    "confidence": 0.8,
    "matched_patterns": ["component", "ui|interface"]
}

agent_config = factory.create_agent_config(
    "frontend-developer",
    task_context
)

# Use with Task tool
# task_tool.invoke(
#     subagent_type=agent_config.subagent_type,
#     system_prompt=agent_config.system_prompt,
#     context=agent_config.context
# )
```

### Fallback Handling

```python
# Get fallback agents for a subagent
fallback_agents = factory.get_fallback_agents("frontend-developer")
# Returns: ["react-pro", "javascript-pro", "typescript-pro"]

# Simulate agent failure and select fallback
available_agents = ["react-pro", "javascript-pro", "typescript-pro"]
attempted_agents = ["frontend-developer"]

fallback = factory.fallback_handler.select_fallback(
    "frontend-developer",
    "frontend",
    attempted_agents,
    available_agents
)
# Returns: "react-pro"
```

### CLI Usage

```bash
# Test subagent detection from command line
python .flow/maestro/scripts/subagent_factory.py "Create React component for user authentication"

# Output:
# === Subagent Detection ===
#
# Task: Create React component for user authentication
#
# Subagent Type: frontend-developer
# Category: frontend
# Confidence: 0.22
# Skill: frontend-design
# Matched Patterns: ['component', 'react|vue|angular|svelte']
# Fallback Agents: ['react-pro', 'javascript-pro', 'typescript-pro']
```

## Configuration

The subagent factory is configured via `.claude/subagent-types.yaml`:

```yaml
task_categories:
  frontend:
    subagent: frontend-developer
    skill: frontend-design
    patterns:
      - "component"
      - "ui|interface"
      - "react|vue|angular|svelte"
    fallback_agents:
      - react-pro
      - javascript-pro
      - typescript-pro

  backend:
    subagent: backend-architect
    patterns:
      - "api|endpoint"
      - "service|controller"
    fallback_agents:
      - api-documenter
      - database-admin

detection_config:
  priority_order:
    - security
    - testing
    - frontend
    - backend
  confidence_threshold: 0.6
  max_fallback_attempts: 3
```

## Category Taxonomy

The factory supports the following task categories:

### Development Categories
- **frontend**: UI components, interfaces, styling, React/Vue/Angular
- **backend**: APIs, services, controllers, databases
- **architecture**: Design patterns, system design, scalability
- **security**: Authentication, authorization, encryption, vulnerabilities

### Quality Categories
- **testing**: Unit tests, integration tests, E2E tests, mocking
- **review**: Code review, refactoring, technical debt
- **performance**: Optimization, caching, profiling

### Data Categories
- **data**: ETL, data warehouses, analytics, SQL queries
- **ai**: LLMs, RAG, embeddings, AI agents

### Operations Categories
- **devops**: Deployment, Docker, Kubernetes, CI/CD
- **documentation**: README, API docs, OpenAPI specs

### Language-Specific Categories
- **python**: Python code, Django/Flask/FastAPI
- **javascript**: JavaScript/TypeScript, Node.js
- **sql**: Database queries, migrations

### Special Categories
- **debug**: Error diagnosis, troubleshooting
- **legacy**: Legacy code modernization
- **context**: Multi-agent coordination
- **default**: Fallback for uncategorized tasks

## Skill Integration

The factory integrates with Agent Skills for domain-specific guidance:

```yaml
skill_mappings:
  frontend-design:
    triggers:
      - "create.*ui"
      - "build.*interface"
    prompt_template: |
      Create distinctive, production-grade frontend UI for: {task_description}

      Requirements:
      - Avoid generic AI aesthetics
      - Use creative, polished design patterns

  webapp-testing:
    triggers:
      - "test.*web.*app"
      - "e2e.*test"
    prompt_template: |
      Test web application: {task_description}

      Requirements:
      - Use Playwright for browser automation
      - Test on multiple browsers
```

When a skill is triggered, it's invoked before subagent execution and the result is passed as additional context.

## Detection Algorithm

1. **Keyword Extraction**: Extract technical terms, file extensions, and phrases from task description
2. **Category Analysis**: Analyze task characteristics (has_tests, has_ui, has_backend)
3. **Pattern Matching**: Match against category-specific regex patterns
4. **Confidence Scoring**: Calculate confidence based on match ratio
5. **Priority Selection**: Select highest priority category with sufficient confidence
6. **Subagent Assignment**: Map category to subagent type
7. **Skill Detection**: Check for skill trigger patterns
8. **Fallback Chain**: Build fallback agent list

## Performance Considerations

- **Caching**: Configuration is loaded once at initialization
- **Regex Precompilation**: Patterns are matched using Python's `re` module
- **Early Termination**: Priority order allows early exit when high-confidence match found
- **Context Efficiency**: Keyword extraction is optimized to minimize token usage

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python .flow/maestro/scripts/test_subagent_factory.py

# Run specific test class
python .flow/maestro/scripts/test_subagent_factory.py TestTaskCategoryParser

# Run with verbose output
python .flow/maestro/scripts/test_subagent_factory.py -v
```

Test coverage includes:
- Keyword extraction for various task types
- Category detection and analysis
- Pattern matching with confidence scoring
- Subagent selection with priority ordering
- Fallback agent handling
- Agent configuration generation
- Skill detection and invocation
- End-to-end integration workflows

## Integration with Maestro

The subagent factory integrates with Maestro's task execution flow:

```python
# In Maestro task executor
from subagent_factory import SubagentFactory

factory = SubagentFactory()

# For each task
task = get_next_task()
detection_result = factory.detect_subagent_detailed(
    task.description,
    {"files": task.files, "dependencies": task.dependencies}
)

agent_config = factory.create_agent_config(
    detection_result.subagent_type,
    {"description": task.description, "prd": prd_context}
)

# Execute with appropriate subagent
result = execute_with_subagent(
    subagent_type=agent_config.subagent_type,
    system_prompt=agent_config.system_prompt,
    context=agent_config.context,
    skill_config=agent_config.skill_config
)

# Handle failures with fallback
if result.failed and agent_config.fallback_chain:
    fallback = factory.fallback_handler.select_fallback(
        detection_result.subagent_type,
        detection_result.category,
        [detection_result.subagent_type],
        available_agents
    )
    # Retry with fallback
```

## Error Handling

The factory provides robust error handling:

- **Configuration Loading**: Raises `FileNotFoundError` if config not found
- **Invalid Patterns**: Logs warnings and skips invalid regex patterns
- **Missing Categories**: Defaults to "general-purpose" subagent
- **Fallback Exhaustion**: Returns `None` when no fallback agents available

## Extending the Factory

### Adding New Categories

1. Add category to `subagent-types.yaml`:
   ```yaml
   new_category:
     subagent: specialized-agent
     patterns:
       - "pattern1"
       - "pattern2"
     fallback_agents:
       - fallback1
   ```

2. Add to `priority_order` in `detection_config` if priority needed

### Adding New Skills

1. Add skill mapping to `subagent-types.yaml`:
   ```yaml
   skill_mappings:
     new-skill:
       triggers:
         - "trigger.*pattern"
       prompt_template: |
         Skill prompt for: {task_description}
   ```

2. Associate with category if automatic invocation desired:
   ```yaml
   some_category:
     subagent: some-agent
     skill: new-skill
   ```

## Best Practices

1. **Pattern Specificity**: Use specific patterns to avoid false positives
2. **Priority Ordering**: Place high-specificity categories (security, testing) first
3. **Fallback Chains**: Provide 2-3 fallback agents for reliability
4. **Skill Templates**: Include task context in skill prompt templates
5. **Confidence Thresholds**: Adjust threshold based on pattern quality
6. **Testing**: Test new categories with realistic task descriptions

## Troubleshooting

### Low Confidence Scores

**Problem**: Tasks getting assigned to "general-purpose" instead of specific agents

**Solutions**:
- Add more specific patterns to category
- Adjust `confidence_threshold` in config
- Improve pattern specificity
- Add more trigger variations

### Wrong Category Selection

**Problem**: Tasks assigned to incorrect category

**Solutions**:
- Check priority order in config
- Review pattern specificity
- Add negative patterns to exclude false matches
- Adjust confidence scoring logic

### Skill Not Triggering

**Problem**: Expected skill not being invoked

**Solutions**:
- Verify skill trigger patterns match task description
- Check skill is associated with correct category
- Ensure skill execution mode is "auto" or "conditional"
- Review skill template formatting

## Future Enhancements

Potential improvements to the subagent factory:

1. **Machine Learning**: Use ML models for better task classification
2. **Context-Aware Detection**: Consider project structure and history
3. **Dynamic Pattern Learning**: Learn patterns from successful task executions
4. **Multi-Category Tasks**: Support tasks spanning multiple categories
5. **Agent Performance Tracking**: Track agent success rates for better selection
6. **Custom Taxonomies**: Support project-specific category taxonomies

## References

- [Subagent Types Configuration](/.claude/subagent-types.yaml)
- [Maestro Architecture](./ARCHITECTURE.md)
- [Task Management](./task_management.md)
- [Checkpoint Manager](./scripts/checkpoint_manager.py)
- [Error Handler](./scripts/error_handler.py)
