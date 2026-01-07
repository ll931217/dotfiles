# Skill Orchestrator

## Overview

The Skill Orchestrator is a component of the Maestro orchestration system that manages skill invocation before subagent execution. It provides domain-specific guidance by invoking appropriate Agent Skills and passing their output to specialized subagents.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Orchestrator                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Skill      │  │   Skill      │  │   Skill      │     │
│  │  Detector    │──│  Invoker     │──│  Formatter   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Context Enrichment                      │    │
│  │  - Original Context                                  │    │
│  │  - Skill Invocations                                 │    │
│  │  - Skill Guidance                                    │    │
│  │  - Combined Guidance                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Subagent Execution                       │
│  (with enriched context containing skill guidance)           │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Task metadata + task context
2. **Detection**: Identify applicable skills
3. **Invocation**: Prepare skill invocations with formatted prompts
4. **Enrichment**: Combine skill outputs with original context
5. **Output**: Enriched context for subagent

## API Reference

### SkillOrchestrator

Main orchestrator class for skill invocation.

#### Constructor

```python
orchestrator = SkillOrchestrator(repo_root: Optional[str] = None)
```

**Parameters:**
- `repo_root`: Optional repository root path. Auto-detected if not provided.

#### Methods

##### detect_applicable_skills()

Detect applicable skills for a task based on description, category, and metadata.

```python
skills = orchestrator.detect_applicable_skills(
    task_description: str,
    task_category: Optional[str] = None,
    task_metadata: Optional[Dict[str, Any]] = None,
) -> List[str]
```

**Detection Strategy:**
1. Check `task_metadata.applicable_skills` if present (highest priority)
2. Check `task_category` for associated skill
3. Match `task_description` against skill trigger patterns

**Returns:** List of applicable skill names

**Example:**
```python
# From task metadata
skills = orchestrator.detect_applicable_skills(
    task_description="Build component",
    task_metadata={"applicable_skills": ["frontend-design", "webapp-testing"]},
)
# Returns: ["frontend-design", "webapp-testing"]

# From category
skills = orchestrator.detect_applicable_skills(
    task_description="Build component",
    task_category="frontend",
)
# Returns: ["frontend-design"]

# From patterns
skills = orchestrator.detect_applicable_skills(
    task_description="Create UI component for login",
)
# Returns: ["frontend-design"]
```

##### invoke_skill()

Invoke a skill with the given context.

```python
invocation = orchestrator.invoke_skill(
    skill_name: str,
    context: Union[SkillContext, str, Dict[str, Any]],
) -> SkillInvocation
```

**Parameters:**
- `skill_name`: Name of the skill to invoke
- `context`: Skill context (SkillContext object, dict, or string)

**Returns:** SkillInvocation object with prepared invocation

**Note:** This method prepares the skill invocation but does not execute the Skill tool directly. The actual skill execution happens when Claude Code processes the invocation.

**Example:**
```python
# With string context
invocation = orchestrator.invoke_skill(
    skill_name="frontend-design",
    context="Create a login form",
)

# With dict context
invocation = orchestrator.invoke_skill(
    skill_name="frontend-design",
    context={
        "task_description": "Build dashboard",
        "prd_context": "Analytics dashboard",
        "existing_patterns": "Dark theme",
    },
)

# With SkillContext object
context = SkillContext(
    task_description="Build dashboard",
    prd_context="Analytics dashboard",
)
invocation = orchestrator.invoke_skill(
    skill_name="frontend-design",
    context=context,
)
```

##### apply_skills_before_subagent()

Main orchestration method that applies applicable skills and enriches context.

```python
enriched = orchestrator.apply_skills_before_subagent(
    task_metadata: Dict[str, Any],
    task_context: Dict[str, Any],
) -> EnrichedContext
```

**Parameters:**
- `task_metadata`: Task metadata from beads (description, category, applicable_skills, etc.)
- `task_context`: Current task context to pass to subagent

**Returns:** EnrichedContext object with:
- Original context
- Skill invocations
- Skill guidance
- Combined guidance

**Example:**
```python
task_metadata = {
    "description": "Create UI component for user profile",
    "category": "frontend",
}

task_context = {
    "prd_context": "User profile management",
    "existing_patterns": "Use shadcn/ui",
}

enriched = orchestrator.apply_skills_before_subagent(
    task_metadata=task_metadata,
    task_context=task_context,
)

# Access enriched data
print(enriched.skill_guidance["frontend-design"])
print(enriched.combined_guidance)
```

##### format_skill_prompt()

Format a skill prompt from template and context.

```python
prompt = orchestrator.format_skill_prompt(
    skill_name: str,
    context: SkillContext,
) -> str
```

**Parameters:**
- `skill_name`: Name of the skill
- `context`: Skill context with template variables

**Returns:** Formatted prompt string

**Example:**
```python
context = SkillContext(
    task_description="Create login form",
    prd_context="Authentication flow",
)

prompt = orchestrator.format_skill_prompt(
    skill_name="frontend-design",
    context=context,
)
# Returns formatted prompt with variables replaced
```

##### get_invocation_history()

Query skill invocation history.

```python
history = orchestrator.get_invocation_history(
    skill_name: Optional[str] = None,
    status: Optional[SkillInvocationStatus] = None,
    limit: Optional[int] = None,
) -> List[SkillInvocation]
```

**Parameters:**
- `skill_name`: Filter by skill name
- `status`: Filter by invocation status
- `limit`: Maximum number of results

**Returns:** List of matching skill invocations

**Example:**
```python
# Get all history
all_history = orchestrator.get_invocation_history()

# Filter by skill
frontend_history = orchestrator.get_invocation_history(skill_name="frontend-design")

# Filter by status
failed_invocations = orchestrator.get_invocation_history(
    status=SkillInvocationStatus.FAILED
)

# Limit results
recent = orchestrator.get_invocation_history(limit=10)
```

##### get_available_skills()

Get list of available skills.

```python
skills = orchestrator.get_available_skills() -> List[str]
```

**Returns:** List of skill names

##### get_skill_info()

Get information about a specific skill.

```python
info = orchestrator.get_skill_info(skill_name: str) -> Optional[SkillMapping]
```

**Returns:** SkillMapping object or None if not found

### Data Classes

#### SkillMapping

Configuration for a skill mapping.

```python
@dataclass
class SkillMapping:
    skill_name: str
    triggers: List[str]
    prompt_template: str
    description: Optional[str] = None
```

#### SkillInvocation

Record of a skill invocation.

```python
@dataclass
class SkillInvocation:
    skill_name: str
    args: str
    result: Optional[str] = None
    status: SkillInvocationStatus = SkillInvocationStatus.PENDING
    timestamp: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
```

**Status Values:**
- `PENDING`: Skill invocation prepared but not executed
- `INVOKING`: Skill is being invoked
- `SUCCESS`: Skill executed successfully
- `FAILED`: Skill execution failed
- `SKIPPED`: Skill was skipped

#### SkillContext

Context passed to skill invocation.

```python
@dataclass
class SkillContext:
    task_description: str
    task_category: Optional[str] = None
    prd_context: Optional[str] = None
    code_context: Optional[str] = None
    existing_patterns: Optional[str] = None
    dependencies: Optional[List[str]] = None
    external_api: Optional[str] = None
    auth_method: Optional[str] = None
    doc_type: Optional[str] = None
    app_url: Optional[str] = None
    test_scenarios: Optional[str] = None
    skill_purpose: Optional[str] = None
    workflow_context: Optional[str] = None
    api_spec: Optional[str] = None
```

#### EnrichedContext

Task context enriched with skill outputs.

```python
@dataclass
class EnrichedContext:
    original_context: Dict[str, Any]
    skill_invocations: List[SkillInvocation]
    skill_guidance: Dict[str, str]  # skill_name -> guidance
    combined_guidance: str
    invocation_timestamp: str
```

## Available Skills

The orchestrator includes the following built-in skills:

### frontend-design

**Triggers:**
- `create.*ui`
- `build.*interface`
- `design.*component`
- `front.?end.*design`
- `styling|style.*guide`
- `layout|visual`

**Purpose:** Frontend UI design skill for component creation and styling

**Template Variables:**
- `{task_description}`: The task description
- `{prd_context}`: PRD context
- `{existing_patterns}`: Existing code patterns

**Example:**
```python
skills = orchestrator.detect_applicable_skills(
    task_description="Create UI component for navigation",
)
# Returns: ["frontend-design"]
```

### webapp-testing

**Triggers:**
- `test.*web.*app`
- `e2e.*test`
- `playwright`
- `chrome.*devtool`
- `browser.*test`
- `ui.*test|component.*test`
- `verify.*frontend`

**Purpose:** Web application testing skill using Playwright

**Template Variables:**
- `{task_description}`: The task description
- `{app_url}`: Application URL for testing
- `{test_scenarios}`: Test scenarios to cover

### document-skills

**Triggers:**
- `create.*pdf|docx|xlsx|pptx`
- `generate.*document`
- `export.*report`
- `document.*template`
- `api.*documentation`
- `user.*guide`
- `technical.*spec`

**Purpose:** Document generation skill for reports and documentation

**Template Variables:**
- `{task_description}`: The task description
- `{doc_type}`: Document type (e.g., "OpenAPI/Swagger")
- `{prd_context}`: PRD context
- `{code_context}`: Code context
- `{api_spec}`: API specification

### mcp-builder

**Triggers:**
- `create.*mcp.*server`
- `build.*integration`
- `mcp.*tool`
- `model.?context.?protocol`
- `external.*api.*integration`
- `third.?party.*service`

**Purpose:** MCP server construction skill for integrations

**Template Variables:**
- `{task_description}`: The task description
- `{external_api}`: External API name
- `{auth_method}`: Authentication method

### skill-creator

**Triggers:**
- `create.*skill`
- `new.*agent.*skill`
- `define.*agent`
- `agent.*capability`
- `custom.*skill.*workflow`

**Purpose:** Custom agent skill creation skill

**Template Variables:**
- `{task_description}`: The task description
- `{skill_purpose}`: Purpose of the skill
- `{workflow_context}`: Target workflow context

## Usage Examples

### Basic Skill Detection

```python
from skill_orchestrator import SkillOrchestrator

orchestrator = SkillOrchestrator()

# Detect from task description
skills = orchestrator.detect_applicable_skills(
    task_description="Create UI component for login",
)
print(f"Detected skills: {skills}")
# Output: ['frontend-design']
```

### Full Workflow with Context Enrichment

```python
orchestrator = SkillOrchestrator()

# Prepare task metadata and context
task_metadata = {
    "description": "Create UI component for user profile",
    "category": "frontend",
}

task_context = {
    "prd_context": "User profile management",
    "existing_patterns": "Use shadcn/ui components",
}

# Apply skills before subagent
enriched = orchestrator.apply_skills_before_subagent(
    task_metadata=task_metadata,
    task_context=task_context,
)

# Access enriched context
print(f"Skills invoked: {[inv.skill_name for inv in enriched.skill_invocations]}")
print(f"Guidance: {enriched.skill_guidance['frontend-design']}")

# Pass enriched context to subagent
# (In actual workflow, this is done automatically)
```

### Testing Task Workflow

```python
orchestrator = SkillOrchestrator()

task_metadata = {
    "description": "Generate E2E tests for checkout flow",
    "category": "testing",
}

task_context = {
    "app_url": "https://staging.example.com",
    "test_scenarios": "Add to cart, checkout, payment",
    "prd_context": "E-commerce checkout",
}

enriched = orchestrator.apply_skills_before_subagent(
    task_metadata=task_metadata,
    task_context=task_context,
)

# Skill guidance includes test scenarios and URL
print(enriched.skill_guidance["webapp-testing"])
```

### Documentation Task Workflow

```python
orchestrator = SkillOrchestrator()

task_metadata = {
    "description": "Generate API documentation for user endpoints",
    "category": "documentation",
}

task_context = {
    "doc_type": "OpenAPI/Swagger",
    "api_spec": "User CRUD operations",
    "prd_context": "User management API",
    "code_context": "src/api/users.ts",
}

enriched = orchestrator.apply_skills_before_subagent(
    task_metadata=task_metadata,
    task_context=task_context,
)

# Document type and API spec included in guidance
```

### Manual Skill Invocation

```python
orchestrator = SkillOrchestrator()

# Create skill context
context = SkillContext(
    task_description="Create a responsive navigation bar",
    prd_context="Main site navigation",
    existing_patterns="Use flexbox and mobile-first approach",
)

# Invoke specific skill
invocation = orchestrator.invoke_skill(
    skill_name="frontend-design",
    context=context,
)

# Access invocation details
print(f"Skill: {invocation.skill_name}")
print(f"Status: {invocation.status.value}")
print(f"Prompt: {invocation.args}")
```

### Query Invocation History

```python
orchestrator = SkillOrchestrator()

# Perform some invocations
orchestrator.invoke_skill("frontend-design", "Task 1")
orchestrator.invoke_skill("webapp-testing", "Task 2")

# Query all history
all_history = orchestrator.get_invocation_history()
print(f"Total invocations: {len(all_history)}")

# Filter by skill
frontend_history = orchestrator.get_invocation_history(
    skill_name="frontend-design"
)
print(f"Frontend invocations: {len(frontend_history)}")

# Filter with limit
recent = orchestrator.get_invocation_history(limit=5)
```

## Integration with Maestro

The Skill Orchestrator integrates with the Maestro workflow system:

1. **Task Generation**: When tasks are generated from PRDs, they may include `applicable_skills` metadata
2. **Pre-execution**: Before launching a subagent, Maestro invokes the skill orchestrator
3. **Enrichment**: The orchestrator detects applicable skills and prepares invocations
4. **Context Passing**: Enriched context with skill guidance is passed to the subagent
5. **Execution**: Subagent receives both original context and skill-specific guidance

### Example Workflow

```python
# In Maestro task execution:
task_metadata = beads.get_task_metadata(task_id)
task_context = collect_task_context(task_id)

# Apply skills
orchestrator = SkillOrchestrator()
enriched = orchestrator.apply_skills_before_subagent(
    task_metadata=task_metadata,
    task_context=task_context,
)

# Launch subagent with enriched context
subagent.execute(
    prompt=build_prompt_with_guidance(enriched),
    context=enriched.original_context,
    skill_guidance=enriched.skill_guidance,
)
```

## Error Handling

The skill orchestrator handles errors gracefully:

### Invalid Skill Name

```python
try:
    invocation = orchestrator.invoke_skill(
        skill_name="nonexistent-skill",
        context="Task",
    )
except ValueError as e:
    print(f"Error: {e}")
# Output: Unknown skill: nonexistent-skill. Available skills: [...]
```

### Pattern Matching Errors

Invalid regex patterns in trigger configurations are silently skipped to prevent failures.

### Missing Template Variables

Missing template variables are replaced with empty strings to ensure prompts are always generated.

## Configuration

Skills are configured in `.claude/subagent-types.yaml`:

```yaml
skill_mappings:
  frontend-design:
    triggers:
      - "create.*ui"
      - "build.*interface"
      - "design.*component"
    prompt_template: |
      Create distinctive, production-grade frontend UI for: {task_description}

      Requirements:
      - Avoid generic AI aesthetics
      - Use creative, polished design patterns
      - Ensure accessibility compliance

      Context:
      - PRD: {prd_context}
      - Existing patterns: {existing_patterns}
```

## Best Practices

1. **Explicit Skills**: Always specify `applicable_skills` in task metadata when possible for most reliable detection
2. **Descriptive Tasks**: Use clear, descriptive task descriptions that include relevant keywords for pattern matching
3. **Context Richness**: Provide rich context (PRD, code patterns, dependencies) for better skill guidance
4. **Custom Skills**: Create custom skills for domain-specific workflows using skill-creator
5. **Fallback Handling**: Always handle cases where no skills are applicable

## Testing

Run the test suite:

```bash
cd .flow/maestro/scripts
python -m pytest test_skill_orchestrator.py -v
```

Run examples:

```bash
python example_skill_orchestrator.py
```

## CLI Usage

The skill orchestrator includes a CLI for testing and debugging:

```bash
# List available skills
python skill_orchestrator.py list

# Detect skills for a task
python skill_orchestrator.py detect --description "Create UI component"

# Get skill information
python skill_orchestrator.py info --skill frontend-design

# View invocation history
python skill_orchestrator.py history
```

## Files

- `skill_orchestrator.py`: Main implementation
- `test_skill_orchestrator.py`: Comprehensive test suite
- `example_skill_orchestrator.py`: Usage examples
- `SKILL_ORCHESTRATOR.md`: This documentation
