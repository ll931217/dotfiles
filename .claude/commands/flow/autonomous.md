# Maestro Autonomous Orchestrator

End-to-end autonomous implementation workflow that executes plan → generate-tasks → implement → cleanup without human intervention.

## Quick Start

```
/flow:autonomous "Implement user authentication with OAuth support"
```

**CRITICAL: Autonomous Execution Mode**
- Phase 1 (Planning) requires human interaction - clarifying questions are asked
- Phases 2-5 run completely autonomously - NO checkpoints, NO pauses, NO confirmations
- After planning is approved, execution continues through completion without stopping
- Only stops for critical errors that require human intervention

Maestro will:
1. **Planning phase**: Interactive - ask clarifying questions, refine requirements
2. **Task Generation**: Autonomous (no "Go" confirmation)
3. **Implementation**: Autonomous (no task-by-task confirmations)
4. **Validation**: Autonomous (auto-recover on failures)
5. **Handoff**: Present final report

**Human interaction required ONLY during Phase 1 (Planning).**

## Overview

Maestro is the autonomous orchestrator that transforms Claude from an interactive assistant into a self-directing development engine. It leverages all existing flow commands plus the decision-engine skill to make intelligent technical decisions without human input.

### Key Features

- **End-to-End Autonomy**: Executes entire flow lifecycle without intervention
- **Autonomous Decision-Making**: Chooses tech stack, architecture patterns, and task ordering
- **Smart Error Recovery**: Self-healing with retry, alternative approaches, and rollback
- **Full Transparency**: Detailed logging of all actions and decisions
- **Git Checkpoints**: Safe rollback capability at any point
- **Quality Assurance**: Tests, PRD validation, and quality gates before completion

## Architecture

Maestro orchestrates these components:

```
┌─────────────────────────────────────────────────────────────┐
│                        Maestro Core                          │
│  - Session lifecycle management                              │
│  - Phase orchestration                                       │
│  - Iterative refinement loop                                 │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Decision Engine  │  │ State Manager    │  │ Error Handler    │
│ - Tech stack     │  │ - Session track  │  │ - Recovery       │
│ - Architecture   │  │ - Decision log   │  │ - Checkpoints    │
│ - Task ordering  │  │ - Persistence    │  │ - Fallback       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Subagent Factory │  │ Skill Orch.      │  │ Parallel Coord.  │
│ - 20+ categories │  │ - 5 built-in     │  │ - [P:Group-X]    │
│ - Auto-detection │  │ - Pre-invocation │  │ - Concurrent     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Detection Method

Check if this workflow is running in autonomous mode:

**Detection Rules:**
- Check if invoked from `/flow:autonomous` (look for parent workflow or explicit autonomous flag)
- Check if current conversation context indicates autonomous execution
- Check for `[Maestro]` log format or explicit autonomous mode flags
- If ANY pattern matches → Set autonomous_mode = true
- If NO patterns match → Set autonomous_mode = false (fallback to interactive)
- Log detection result: `[Maestro] Autonomous mode detected: {autonomous_mode}`
- Note: This flag is passed to downstream commands to control their behavior

**If autonomous mode is TRUE:**
- **SKIP** all "Wait for Go" confirmations - proceed directly
- **SKIP** AskUserQuestion checkpoints (except critical errors)

**If autonomous mode is FALSE:**
- Follow interactive mode with AskUserQuestion for confirmations

## Prerequisites

**Required:**
- git installed and configured
- beads (`bd`) installed for task persistence
- Existing test infrastructure

**Verified automatically:**
```bash
# Check beads availability
bd quickstart

# Check git status
git status

# Verify test suite
# (project-specific)
```

## Workflow

### Phase 1: Initialization

1. **Create session** - Generate unique session ID
2. **Initialize state** - Create session directory and metadata
3. **Create checkpoint** - Git checkpoint before starting
4. **Load config** - Read `.flow/maestro/config.yaml`

```bash
mkdir -p .flow/maestro/sessions/<session-id>
# Session metadata initialized
# Initial git checkpoint created
```

### Phase 2: Planning (INTERACTIVE)

1. **Auto-discovery** - Analyze codebase for context
2. **Ask questions** - Use AskUserQuestion for clarifying requirements
3. **Make decisions** - Decision engine selects tech/architecture (with human input)
4. **Generate PRD** - Create PRD with requirements gathered interactively
5. **Get approval** - Wait for user to approve the PRD
6. **Log decisions** - Record all decisions with rationale

```bash
[Maestro] Phase 1: Planning (INTERACTIVE)
[Maestro]   → Analyzing codebase...
[Maestro]   → Question: Which OAuth providers should be supported?
[Maestro]   → Decision: Tech stack - React + TypeScript (existing)
[Maestro]   → Decision: Architecture - Service layer pattern
[Maestro]   → Generating PRD...
[Maestro]   ✓ PRD approved by user: prd-feature-v1.md
[Maestro] → Switching to autonomous mode for remaining phases...
```

### Phase 3: Task Generation (AUTONOMOUS)

1. **Read PRD** - Parse requirements and priorities
2. **Generate epics** - 5-7 high-level epics
3. **Generate sub-tasks** - Detailed tasks with dependencies
4. **Order tasks** - Optimize for parallel execution

```bash
[Maestro] Phase 2: Task Generation
[Maestro]   → Created 6 epics with 23 sub-tasks
[Maestro]   → Ordered into 4 parallel groups
[Maestro]   ✓ Tasks ready for execution
```

### Phase 4: Implementation (AUTONOMOUS)

1. **Execute parallel groups** - [P:Group-X] markers
2. **Delegate to subagents** - Auto-detect specialized agents
3. **Invoke skills** - Pre-invoke applicable skills
4. **Handle errors** - Smart recovery with fallbacks
5. **Create checkpoints** - Git commits at safe points

```bash
[Maestro] Phase 3: Implementation
[Maestro]   → [P:Group-1] Executing 5 tasks in parallel...
[Maestro]       → Task dotfiles-xxx: frontend-developer implementing UI
[Maestro]       → Task dotfiles-yyy: backend-architect designing API
[Maestro]   ✓ Checkpoint: git commit -m "feat: Phase 1 complete"
[Maestro]   → [P:Group-2] Executing 4 tasks...
```

### Phase 5: Validation (AUTONOMOUS)

1. **Run test suite** - Verify all tests pass
2. **Validate PRD** - Check all requirements met
3. **Quality gates** - Linting, type checking, security
4. **Iterate if needed** - Refine until gates pass

```bash
[Maestro] Phase 4: Validation
[Maestro]   → Running test suite... 127/127 tests passed ✓
[Maestro]   → Validating PRD requirements... all 8 met ✓
[Maestro]   → Quality gates... lint ✓, type-check ✓, security ✓
```

### Phase 6: Handoff

1. **Generate report** - Comprehensive implementation report
2. **Final checkpoint** - Git commit for complete feature
3. **Update PRD** - Status → implemented
4. **Present results** - Show report to human

```bash
[Maestro] Phase 5: Handoff
[Maestro]   → Generating implementation report...
[Maestro] ✓ Autonomous implementation complete!
[Maestro]   → Report: .flow/maestro/sessions/<session-id>/final-report.md
```

## Decision Engine Integration

Maestro uses the decision-engine skill for all technical decisions:

### Tech Stack Selection

```python
from decision_engine.scripts.tech_stack_selector import TechStackSelector

selector = TechStackSelector(project_root)
decision = selector.select_technology("OAuth library", requirements={
    "language": "javascript",
    "framework": "Express",
    "existing_deps": ["passport"]
})

# Returns:
# {
#   "decision": "Passport.js",
#   "rationale": "Already in package.json, mature ecosystem, perfect fit",
#   "confidence": "high",
#   "alternatives": ["Auth.js", "Auth0"]
# }
```

### Architecture Pattern Selection

```python
from decision_engine.scripts.architecture_pattern_matcher import ArchitecturePatternMatcher

matcher = ArchitecturePatternMatcher(project_root)
decision = matcher.select_pattern("User authentication", complexity="medium")

# Returns:
# {
#   "pattern": "Middleware pattern",
#   "rationale": "Medium complexity, existing middleware in codebase",
#   "confidence": "high"
# }
```

### Task Ordering

```python
from decision_engine.scripts.task_ordering import TaskOrdering

ordering = TaskOrdering()
sequence = ordering.order_tasks(tasks, strategy="parallel-maximizing")

# Returns:
# {
#   "sequence": [
#     ["task-1", "task-2"],  # [P:Group-1]
#     ["task-3", "task-4"],  # [P:Group-2]
#     "task-5"                # Sequential
#   ],
#   "rationale": "Foundational tasks first, maximize parallelism"
# }
```

## Error Recovery

Maestro implements smart error recovery:

### Recovery Strategies

1. **Retry with Backoff** - Transient errors (network, timeout)
2. **Alternative Approach** - Implementation failures
3. **Rollback to Checkpoint** - Critical failures
4. **Request Human Input** - Ambiguous requirements (last resort)

### Error Classification

```python
from maestro.scripts.error_handler import ErrorHandler

handler = ErrorHandler()
error_info = handler.detect_error(error_message, context)
category = handler.classify_error(error_info)
strategy = handler.select_recovery_strategy(category)
result = handler.execute_recovery(strategy, context)
```

### Example Recovery

```bash
[Maestro] Error in task dotfiles-xxx: Test failure
[Maestro]   → Classifying error... test_failure
[Maestro]   → Strategy: alternative_approach
[Maestro]   → Attempting: Re-run tests with verbose output
[Maestro]   → Fixed: Test fixture issue
[Maestro]   ✓ Task completed
```

## State Persistence

All Maestro state is persisted in `.flow/maestro/`:

```
.flow/maestro/
├── sessions/
│   └── <session-id>/
│       ├── metadata.json          # Session info, status, timestamps
│       ├── decisions.json          # All decisions with rationale
│       ├── checkpoints.json        # Git commit references
│       ├── execution-log.md        # Detailed execution log
│       └── final-report.md         # Generated report
├── decisions/
│   ├── tech-stack.json            # Historical tech decisions
│   ├── architecture.json           # Historical architecture decisions
│   └── task-ordering.json          # Historical task ordering
└── config.yaml                     # Maestro configuration
```

### Session Metadata

```json
{
  "session_id": "uuid",
  "feature_request": "Implement user authentication",
  "status": "implementing",
  "current_phase": "implementation",
  "start_time": "2025-01-07T10:00:00Z",
  "git_context": {
    "branch": "feat-auth",
    "worktree": "feature-auth",
    "initial_commit": "abc123"
  },
  "statistics": {
    "tasks_completed": 8,
    "tasks_remaining": 4,
    "checkpoints_created": 2,
    "errors_recovered": 1
  }
}
```

## Subagent Coordination

Maestro auto-detects and delegates to specialized subagents:

### Supported Categories (20+)

| Category | Subagent | Skills |
|----------|----------|--------|
| Frontend UI | frontend-developer | frontend-design |
| Backend API | backend-architect | - |
| Database | database-admin | - |
| Testing | test-automator | webapp-testing |
| Security | security-auditor | - |
| DevOps | deployment-engineer | - |
| Documentation | api-documenter | document-skills |
| Performance | performance-engineer | - |
| ... | ... | ... |

### Delegation Pattern

```python
from maestro.scripts.subagent_factory import SubagentFactory

factory = SubagentFactory()
subagent_type = factory.select_subagent(task_description)
agent_config = factory.create_agent_config(subagent_type, task_context)

# Delegate to subagent
result = invoke_subagent(subagent_type, agent_config)
```

### Parallel Execution

```python
from maestro.scripts.parallel_coordinator import ParallelCoordinator

coordinator = ParallelCoordinator()
groups = coordinator.detect_groups(tasks)

for group in groups:
    coordinator.execute_parallel_group(group, skills, subagents)
    coordinator.wait_for_group_completion()
    coordinator.refresh_context_before_group()
```

## Iterative Refinement

Maestro implements plan-implement-validate-review loop:

```yaml
iterative_refinement:
  max_iterations: 3
  completion_criteria:
    - all_tests_passing
    - all_prd_requirements_met
    - quality_gates_passed
    - no_critical_issues

  loop:
    - phase: plan
      action: generate_prd

    - phase: implement
      action: execute_tasks

    - phase: validate
      action: run_validation_gates

    - phase: review
      action: check_completion_criteria
      decision: refine_or_complete
```

### Refinement Example

```bash
[Maestro] Iteration 1
[Maestro]   → Plan: PRD generated
[Maestro]   → Implement: 8/12 tasks completed
[Maestro]   → Validate: 2 tests failing
[Maestro]   → Review: Not complete - test failures

[Maestro] Iteration 2
[Maestro]   → Plan: Fix test failures
[Maestro]   → Implement: Tests fixed, all tasks complete
[Maestro]   → Validate: All tests passing ✓
[Maestro]   → Review: Complete - all criteria met
```

## Configuration

Maestro behavior is configurable via `.flow/maestro/config.yaml`:

```yaml
orchestrator:
  max_iterations: 3
  max_task_duration: 1800  # 30 minutes per task
  checkpoint_frequency: "phase_complete"
  parallel_execution: true
  context_refresh_interval: 5  # tasks

decision_engine:
  prefer_existing: true
  maturity_threshold: 0.7
  confidence_threshold: 0.6

error_recovery:
  max_retry_attempts: 3
  backoff_multiplier: 2
  enable_rollback: true
  request_human_on_ambiguous: false  # Stay autonomous

logging:
  level: "info"  # debug, info, warn, error
  include_rationale: true
  log_to_file: true

validation:
  run_tests: true
  validate_prd: true
  quality_gates: ["lint", "typecheck", "security"]
  fail_on_gate_violation: true
```

## Report Format

Maestro generates comprehensive implementation reports:

```markdown
# Maestro Implementation Report

## Summary
- Feature: User Authentication with OAuth
- Duration: 47 minutes
- Tasks Completed: 12/12
- Tests Passed: 127/127
- Checkpoints: 2

## Decisions Made
### Technology Stack
- OAuth Library: Passport.js (existing dependency, mature)
- Session Store: PostgreSQL (existing database)
- Token Strategy: JWT (stateless, scalable)

### Architecture
- Pattern: Middleware-based auth flow
- Route Structure: /api/auth/* endpoints
- Frontend: React Context Provider

### Task Ordering
1. Database schema (foundational)
2. Backend routes (depends on schema)
3. Frontend UI (parallel with routes)
4. Testing (after implementation)
5. Documentation (final phase)

## Changes Made
### Files Modified: 8
- src/routes/auth.ts (+127 lines)
- src/middleware/passport.ts (+84 lines)
- src/components/AuthProvider.tsx (+56 lines)
- ...

### Files Created: 5
- src/services/oauth.service.ts
- src/types/auth.d.ts
- tests/integration/oauth.test.ts
- ...

## Testing
- Unit Tests: 89 passed
- Integration Tests: 38 passed
- Coverage: 94%

## Quality Gates
- ESLint: 0 errors, 3 warnings (addressed)
- TypeScript: No type errors
- Security Audit: 0 vulnerabilities

## Checkpoints
- commit 1a2b3c4: feat: OAuth authentication phase 1
- commit 5d6e7f8: feat: OAuth authentication complete

## Next Steps
- Review implementation
- Run manual testing if desired
- Merge to main when ready
```

## Integration with Flow Commands

Maestro orchestrates existing flow commands:

```yaml
maestro_workflow:
  - phase: "Planning"
    command: "/flow:plan"
    autonomous_mode: true  # Skip clarifying questions

  - phase: "Task Generation"
    command: "/flow:generate-tasks"
    use_decision_engine: true  # Optimize task ordering

  - phase: "Implementation"
    command: "/flow:implement"
    enable_error_recovery: true
    parallel_execution: true

  - phase: "Validation"
    command: "/flow:summary"
    run_tests: true
    validate_prd: true

  - phase: "Handoff"
    command: "/flow:cleanup"
    generate_report: true
```

## Usage Examples

### Basic Usage

```bash
/flow:autonomous "Implement user authentication"
```

### With Context

```bash
/flow:autonomous "Add OAuth Google login to the existing auth system"
```

### Complex Feature

```bash
/flow:autonomous "Build a real-time dashboard with WebSocket support and data visualization"
```

## Troubleshooting

### Session Recovery

If Maestro is interrupted, recover the session:

```bash
# List sessions
ls -la .flow/maestro/sessions/

# View session status
cat .flow/maestro/sessions/<session-id>/metadata.json

# Resume session (manual)
# Use the session ID to continue where left off
```

### Manual Intervention

If Maestro pauses for human input:

```bash
# View execution log
cat .flow/maestro/sessions/<session-id>/execution-log.md

# Review decisions
cat .flow/maestro/sessions/<session-id>/decisions.json

# Provide input and continue
# (Manual intervention required)
```

### Rollback

If implementation goes wrong, rollback to checkpoint:

```bash
# List checkpoints
cat .flow/maestro/sessions/<session-id>/checkpoints.json

# Rollback to specific checkpoint
git checkout <checkpoint-sha>

# Resume Maestro
/flow:autonomous --resume <session-id>
```

## Best Practices

1. **Start Small**: Test Maestro with simple features first
2. **Review Reports**: Always review the final report before accepting
3. **Check Test Coverage**: Ensure tests pass before merging
4. **Use Worktrees**: Isolate Maestro work in separate worktrees
5. **Monitor Sessions**: Keep an eye on session progress
6. **Validate Decisions**: Review technical decisions in the report

## Limitations

- **Single-Developer**: Maestro doesn't support multi-user coordination
- **Local Only**: No deployment or production monitoring
- **Codebase Size**: Performance degrades with very large codebases (>100K files)
- **Context Window**: May need periodic refresh for long-running sessions
- **Human Review**: Still requires human review before merging to main

## Future Enhancements

- [ ] Multi-repository support
- [ ] Distributed task execution
- [ ] Natural language documentation generation
- [ ] Advanced code review integration
- [ ] Performance optimization for large codebases
- [ ] Custom workflow definition DSL

## AI Execution Instructions

When this command is invoked, execute the following workflow:

### CRITICAL EXECUTION RULES

**MODE SWITCH:**
- **Phase 1 (Planning)**: INTERACTIVE - Ask clarifying questions, use AskUserQuestion
- **Phases 2-5**: AUTONOMOUS - NO checkpoints, NO pauses, NO confirmations

**AFTER PLANNING IS APPROVED:**
- DO NOT pause for any confirmations
- DO NOT use AskUserQuestion tool (except for critical errors)
- DO NOT wait for "Go" signals
- DO NOT stop at checkpoints
- Continue execution from task generation through completion without interruption
- Only stop for critical errors that absolutely require human intervention

**EXECUTION PHASES:**

### Phase 1: Planning (INTERACTIVE)
1. Analyze the user's feature request
2. Explore codebase to understand existing patterns
3. **ASK clarifying questions** - Use AskUserQuestion for:
   - Ambiguous requirements
   - Multiple valid approaches where user preference matters
   - Missing information
   - Conflicting specifications
4. Invoke decision-engine skill for technical decisions (with human review)
5. Generate PRD with `status: approved`
6. **WAIT for user approval** of the PRD before proceeding
7. Save PRD to `.flow/prd-{feature}-v1.md`

**Transition to Autonomous:** Once PRD is approved, switch to autonomous mode for remaining phases.

### Phase 2: Task Generation (AUTONOMOUS)
1. Read the approved PRD
2. Generate 5-7 epics based on requirements
3. Generate sub-tasks with dependencies
4. **SKIP the "Wait for Go" checkpoint** - proceed directly to sub-task generation
5. Assign priorities based on PRD frontmatter
6. Create tasks in beads (or TodoWrite fallback)
7. Update PRD frontmatter with related_issues

### Phase 3: Implementation (AUTONOMOUS)
1. Execute tasks continuously without pausing
2. Use specialized subagents via Task tool
3. Execute parallel groups via concurrent Task invocations
4. **DO NOT pause** between tasks for permission
5. **DO NOT pause** at phase boundaries
6. Continue until all tasks are complete
7. Auto-recover from failures using alternative approaches

### Phase 4: Validation (AUTONOMOUS)
1. Run test suite
2. Validate PRD requirements are met
3. Run quality gates (lint, typecheck, security)
4. If gates fail, attempt auto-recovery:
   - Fix linting errors
   - Fix type errors
   - Fix test failures
   - Retry up to 3 times
5. Only pause if all recovery strategies exhausted

### Phase 5: Handoff
1. Generate implementation report
2. Run `/flow:cleanup` to finalize
3. Present final report to user
4. Mark PRD status as `implemented`

**ERROR HANDLING:**
- On transient errors: Retry with backoff
- On implementation failures: Try alternative approach
- On critical errors: Rollback to checkpoint, log failure, notify user

**LOGGING FORMAT:**
```
[Maestro] Phase N: {phase_name}
[Maestro]   → {action_description}
[Maestro] ✓ {completion_status}
```

**EXECUTION CONTINUES UNTIL:**
- All tasks complete successfully
- OR critical error with no recovery options
- OR resource limits exceeded

**PHASE 1 (PLANNING) - INTERACTIVE:**
- Use AskUserQuestion for clarifications
- Wait for PRD approval before proceeding
- Get human input on technical decisions

**PHASES 2-5 - AUTONOMOUS:**
- DO NOT stop for task confirmations
- DO NOT pause at phase boundaries
- DO NOT pause for checkpoint reviews
- DO NOT wait for progress updates
- DO NOT wait for Go signals
- DO NOT wait for user approvals

**ONLY STOP FOR (after Phase 1):**
- Critical unrecoverable errors
- Resource exhaustion
- Ambiguous requirements not covered by approved PRD
- Conflicting specifications discovered during implementation

## See Also

- **Decision Engine**: `.claude/skills/decision-engine/SKILL.md`
- **State Manager**: `.flow/maestro/scripts/session_manager.py`
- **Error Handler**: `.flow/maestro/scripts/error_handler.py`
- **Subagent Factory**: `.flow/maestro/scripts/subagent_factory.py`
- **Parallel Coordinator**: `.flow/maestro/scripts/parallel_coordinator.py`
- **Validation System**: `.flow/maestro/scripts/validator.py`
