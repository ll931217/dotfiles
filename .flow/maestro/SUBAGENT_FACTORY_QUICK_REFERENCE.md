# Subagent Factory Quick Reference

## Quick Start

```python
from subagent_factory import SubagentFactory

# Initialize
factory = SubagentFactory()

# Detect subagent type
subagent = factory.detect_subagent_type("Create React component")
# Returns: "frontend-developer"

# Create agent config
config = factory.create_agent_config(
    "frontend-developer",
    {"description": "Create UI component", "prd": "..."}
)
```

## Core API

### Detection Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `detect_subagent_type(desc)` | Quick detection | `str` (subagent type) |
| `detect_subagent_detailed(desc, meta)` | Full detection | `DetectionResult` |
| `detect_skill(desc)` | Skill trigger detection | `str` or `None` |
| `select_subagent(metadata)` | Select from metadata | `str` (subagent type) |

### Configuration Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_fallback_agents(type)` | Get fallback chain | `List[str]` |
| `create_agent_config(type, ctx)` | Build agent config | `AgentConfig` |

## Data Structures

### DetectionResult

```python
@dataclass
class DetectionResult:
    subagent_type: str           # Selected subagent
    category: str                # Task category
    confidence: float            # 0.0 to 1.0
    skill: Optional[str]         # Triggered skill
    matched_patterns: List[str]  # Matched regex patterns
    fallback_agents: List[str]   # Fallback chain
```

### AgentConfig

```python
@dataclass
class AgentConfig:
    subagent_type: str               # Subagent name
    system_prompt: str               # System prompt
    context: Dict[str, Any]          # Task context
    skill_config: Optional[Dict]     # Skill configuration
    fallback_chain: List[str]        # Fallback agents
    detection_metadata: Dict[str, Any]  # Detection info
```

## Category Mapping

| Category | Subagent | Skill | Fallbacks |
|----------|----------|-------|-----------|
| frontend | frontend-developer | frontend-design | react-pro, javascript-pro, typescript-pro |
| backend | backend-architect | - | api-documenter, database-admin |
| security | security-auditor | - | - |
| testing | test-automator | webapp-testing | - |
| performance | performance-engineer | - | database-optimizer |
| architecture | architect-review | - | backend-architect, code-reviewer |
| data | data-engineer | - | data-scientist, sql-pro |
| review | code-reviewer | - | architect-review |
| debug | debugger | - | error-detective |
| devops | deployment-engineer | - | terraform-specialist |
| documentation | api-documenter | document-skills | prompt-engineer |
| ai | ai-engineer | - | data-engineer |
| python | python-pro | - | - |
| javascript | javascript-pro | - | react-pro, typescript-pro |
| typescript | typescript-pro | - | javascript-pro |
| sql | sql-pro | - | database-admin, database-optimizer |
| terraform | terraform-specialist | - | deployment-engineer |
| legacy | legacy-modernizer | - | code-reviewer, backend-architect |
| context | context-manager | - | - |
| default | general-purpose | - | - |

## Pattern Examples

### Frontend Patterns
- `component`
- `ui|interface`
- `react|vue|angular|svelte`
- `css|styling|style`
- `responsive`
- `accessibility`

### Backend Patterns
- `api|endpoint`
- `service|controller`
- `microservice`
- `rest|graphql`
- `database|schema`

### Security Patterns
- `auth|authentication|authorization`
- `security|vulnerability|secure`
- `jwt|oauth|saml`
- `encryption|encrypt`

### Testing Patterns
- `test|spec|testing`
- `unit|integration|e2e`
- `mock|stub|fixture`
- `pytest|mocha|jest`

## Skill Triggers

### frontend-design
- `create.*ui`
- `build.*interface`
- `design.*component`
- `front.?end.*design`

### webapp-testing
- `test.*web.*app`
- `e2e.*test`
- `playwright`
- `chrome.*devtool`

### document-skills
- `create.*pdf|docx|xlsx|pptx`
- `generate.*document`
- `export.*report`
- `api.*documentation`

### mcp-builder
- `create.*mcp.*server`
- `build.*integration`
- `mcp.*tool`
- `external.*api.*integration`

### skill-creator
- `create.*skill`
- `new.*agent.*skill`
- `define.*agent`
- `agent.*capability`

## CLI Usage

```bash
# Test detection
python .flow/maestro/scripts/subagent_factory.py "Create React component"

# Test backend task
python .flow/maestro/scripts/subagent_factory.py "Implement REST API"

# Test security task
python .flow/maestro/scripts/subagent_factory.py "Add JWT authentication"
```

## Testing

```bash
# Run all tests
python .flow/maestro/scripts/test_subagent_factory.py

# Run specific test
python .flow/maestro/scripts/test_subagent_factory.py TestTaskCategoryParser

# Verbose output
python .flow/maestro/scripts/test_subagent_factory.py -v
```

## Configuration Location

```
.claude/subagent-types.yaml
```

## Environment Variables

```bash
# Override config path for testing
export SUBAGENT_TYPES_PATH=/path/to/config.yaml
```

## Common Workflows

### 1. Simple Detection

```python
factory = SubagentFactory()
subagent = factory.detect_subagent_type(task_description)
```

### 2. Full Detection with Metadata

```python
result = factory.detect_subagent_detailed(
    task_description,
    {
        "files": ["Component.tsx", "service.py"],
        "dependencies": ["react", "fastapi"]
    }
)

print(f"Subagent: {result.subagent_type}")
print(f"Category: {result.category}")
print(f"Confidence: {result.confidence}")
print(f"Skill: {result.skill}")
```

### 3. Create Agent Config

```python
config = factory.create_agent_config(
    subagent_type="frontend-developer",
    task_context={
        "description": "Create responsive UI",
        "prd": prd_content,
        "code_patterns": "Component architecture",
        "confidence": 0.8
    }
)

# Use with Task tool
# task_tool.invoke(
#     subagent_type=config.subagent_type,
#     system_prompt=config.system_prompt,
#     context=config.context
# )
```

### 4. Handle Fallbacks

```python
# Get fallback chain
fallbacks = factory.get_fallback_agents("frontend-developer")

# Select fallback after failure
fallback = factory.fallback_handler.select_fallback(
    failed_agent="frontend-developer",
    category="frontend",
    attempted_agents=["frontend-developer"],
    available_agents=["react-pro", "javascript-pro"]
)
```

## Troubleshooting

### Task Assigned to Wrong Category

**Check**:
1. Priority order in config
2. Pattern specificity
3. Confidence threshold

### Skill Not Triggering

**Check**:
1. Trigger pattern matches description
2. Skill associated with correct category
3. Execution mode (auto/conditional)

### Low Confidence Scores

**Solutions**:
1. Add more patterns to category
2. Improve pattern specificity
3. Adjust confidence threshold

## Performance Tips

1. **Reuse Factory Instance**: Initialize once, reuse for multiple detections
2. **Batch Detection**: Process multiple tasks in single factory session
3. **Cache Results**: Cache DetectionResult for repeated tasks
4. **Optimize Patterns**: Use specific patterns to reduce false matches

## Integration Pattern

```python
class TaskExecutor:
    def __init__(self):
        self.factory = SubagentFactory()
        self.attempted_agents = []

    def execute_task(self, task):
        # Detect subagent
        result = self.factory.detect_subagent_detailed(
            task.description,
            task.metadata
        )

        # Create config
        config = self.factory.create_agent_config(
            result.subagent_type,
            {"description": task.description}
        )

        # Execute
        try:
            return self._execute_with_agent(config)
        except AgentFailure:
            # Try fallback
            return self._try_fallback(result, config)

    def _try_fallback(self, result, config):
        fallback = self.factory.fallback_handler.select_fallback(
            result.subagent_type,
            result.category,
            self.attempted_agents,
            get_available_agents()
        )

        if fallback:
            self.attempted_agents.append(fallback)
            # Execute with fallback
```

## See Also

- [Full Documentation](./SUBAGENT_FACTORY.md)
- [Configuration](/.claude/subagent-types.yaml)
- [Architecture](./ARCHITECTURE.md)
- [Test Suite](./scripts/test_subagent_factory.py)
