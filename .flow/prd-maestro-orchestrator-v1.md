---
prd:
  version: v1
  feature_name: maestro-orchestrator
  status: implementing
git:
  branch: feat-orchestrate-flow
  branch_type: feature
  created_at_commit: b9dc8fd
  updated_at_commit: b9dc8fd35ba862a6b43a7fb1f681f09eba00b4d7
worktree:
  is_worktree: true
  name: dotfiles.feat-orchestrate-flow
  path: /home/ll931217/GitHub/dotfiles/.git/worktrees/dotfiles.feat-orchestrate-flow
  repo_root: /home/ll931217/GitHub/dotfiles.feat-orchestrate-flow
metadata:
  created_at: 2025-01-07T10:00:00Z
  updated_at: 2026-01-07T12:37:18Z
  created_by: ll931217
  filename: prd-maestro-orchestrator-v1.md
beads:
  related_issues: [dotfiles-246.1, dotfiles-246.2, dotfiles-246.3, dotfiles-246.4, dotfiles-duu.1, dotfiles-duu.2, dotfiles-duu.3, dotfiles-e5e.1, dotfiles-e5e.2, dotfiles-e5e.3, dotfiles-z1j.1, dotfiles-z1j.2, dotfiles-z1j.3, dotfiles-ahr.1, dotfiles-ahr.2, dotfiles-ahr.3, dotfiles-ahr.4, dotfiles-b0z.1, dotfiles-b0z.2, dotfiles-b0z.3, dotfiles-wl5.1, dotfiles-wl5.2, dotfiles-wl5.3, dotfiles-wl5.4, dotfiles-wl5.5]
  related_epics: [dotfiles-b0z, dotfiles-246, dotfiles-duu, dotfiles-e5e, dotfiles-z1j, dotfiles-ahr, dotfiles-wl5]
code_references:
  - path: ".claude/commands/flow/implement.md"
    lines: "538-632"
    reason: "Parallel task execution patterns with [P:Group-X] flags"
  - path: ".claude/commands/flow/implement.md"
    lines: "1118-1121"
    reason: "Autonomous execution pattern - continuous without permission"
  - path: ".claude/commands/flow/README.md"
    lines: "184-292"
    reason: "Skill integration workflow and invocation protocol"
  - path: ".claude/commands/flow/plan.md"
    lines: "372-410"
    reason: "PRD frontmatter structure for state tracking"
  - path: ".claude/commands/flow/shared/protocols/auto-compaction-detection.md"
    lines: "9-58"
    reason: "Context refresh and recovery protocols"
priorities:
  enabled: true
  default: P2
  inference_method: ai_inference_with_review
  requirements:
    - id: FR-1
      text: "Orchestrator executes end-to-end workflow autonomously (plan → implement → cleanup)"
      priority: P0
      confidence: high
      inferred_from: "Core feature requirement - primary autonomy goal"
      user_confirmed: false
    - id: FR-2
      text: "Orchestrator makes autonomous decisions for technology stack selection"
      priority: P1
      confidence: high
      inferred_from: "Explicit user requirement: 'Tech choices' as decision scope"
      user_confirmed: false
    - id: FR-3
      text: "Orchestrator makes autonomous decisions for architecture patterns and design approaches"
      priority: P1
      confidence: high
      inferred_from: "Explicit user requirement: 'Architecture' as decision scope"
      user_confirmed: false
    - id: FR-4
      text: "Orchestrator autonomously orders and prioritizes tasks with dependency resolution"
      priority: P1
      confidence: high
      inferred_from: "Explicit user requirement: 'Task ordering' as decision scope"
      user_confirmed: false
    - id: FR-5
      text: "Orchestrator implements smart error recovery with fallback strategies (retry, alternative approach, rollback)"
      priority: P0
      confidence: high
      inferred_from: "Critical for autonomous operation - cannot proceed without error handling"
      user_confirmed: false
    - id: FR-6
      text: "New command /flow:autonomous triggers the orchestrator"
      priority: P1
      confidence: high
      inferred_from: "User's explicit choice for invocation method"
      user_confirmed: false
    - id: FR-7
      text: "Orchestrator provides detailed logging with full transparency (all actions, decisions, rationale)"
      priority: P2
      confidence: high
      inferred_from: "User's explicit choice for visibility level"
      user_confirmed: false
    - id: FR-8
      text: "Orchestrator maintains full persistence of decisions, rationale, and intermediate results"
      priority: P1
      confidence: high
      inferred_from: "User's explicit choice for state management - enables replayability and learning"
      user_confirmed: false
    - id: FR-9
      text: "Orchestrator creates git checkpoints at safe points for rollback capability"
      priority: P0
      confidence: high
      inferred_from: "User's explicit choice for rollback strategy - critical for recovery"
      user_confirmed: false
    - id: FR-10
      text: "Orchestrator validates implementation with test suite, PRD requirements, and quality gates before completion"
      priority: P2
      confidence: high
      inferred_from: "User's explicit choices for validation gates"
      user_confirmed: false
    - id: FR-11
      text: "Orchestrator generates comprehensive report with all decisions, changes, and testing results"
      priority: P2
      confidence: medium
      inferred_from: "User's explicit choice for handoff method"
      user_confirmed: false
    - id: FR-12
      text: "Orchestrator implements iterative refinement pattern with continuous improvement"
      priority: P1
      confidence: high
      inferred_from: "User's explicit choice for execution pattern"
      user_confirmed: false
    - id: FR-13
      text: "Decision engine skill provides autonomous decision-making capabilities"
      priority: P2
      confidence: medium
      inferred_from: "User selected 'Decision engine skill' as capability to create"
      user_confirmed: false
    - id: FR-14
      text: "Orchestrator leverages existing subagents (frontend-developer, backend-architect, test-automator, etc.)"
      priority: P1
      confidence: high
      inferred_from: "User explicitly wants to use existing subagents - reduces implementation complexity"
      user_confirmed: false
    - id: FR-15
      text: "Orchestrator-specific skills created for coordination and decision-making"
      priority: P3
      confidence: low
      inferred_from: "User selected this but existing patterns may be sufficient"
      user_confirmed: false
---

# Product Requirements Document: Maestro Orchestrator

## 1. Introduction/Overview

The **Maestro Orchestrator** is an autonomous implementation system that transforms Claude from an interactive assistant into a self-directing development engine. Maestro takes a feature request from concept to completion without human intervention, making implementation decisions autonomously and only presenting results for final review.

### Problem Statement

Current flow commands require significant human interaction:
- `/flow:plan` requires answering clarifying questions
- `/flow:generate-tasks` requires manual invocation
- `/flow:implement` requires continuous monitoring and intervention
- Human must coordinate between phases and make technical decisions

### Solution

Maestro orchestrates the entire flow command lifecycle autonomously:
- Accepts a feature request
- Generates PRD through autonomous discovery
- Creates and executes implementation tasks
- Makes technical decisions without human input
- Validates and presents comprehensive results

### Goal

Enable fully autonomous feature implementation where the human provides initial intent and receives a completed, tested, validated implementation.

## 2. Goals

1. **End-to-End Autonomy**: Execute entire flow command lifecycle (plan → implement → cleanup) without human intervention
2. **Autonomous Decision-Making**: Make intelligent technical decisions for technology selection, architecture, and task ordering
3. **Smart Recovery**: Handle errors and ambiguities with self-recovery strategies
4. **Full Transparency**: Provide detailed logging of all actions, decisions, and rationale
5. **Safe Execution**: Maintain git checkpoints for rollback capability
6. **Quality Assurance**: Validate all implementations with tests, PRD compliance, and quality gates
7. **Continuous Improvement**: Learn from each execution through iterative refinement

## 3. User Stories

- **As a developer**, I want to provide a feature request and receive a complete implementation, so that I can focus on high-level architecture rather than coordination
- **As a developer**, I want to understand all decisions made during implementation, so that I can maintain context and trust the autonomous process
- **As a developer**, I want the ability to rollback to safe states if something goes wrong, so that I can experiment with autonomous implementation without risk
- **As a developer**, I want comprehensive validation before accepting changes, so that I can trust the quality of autonomous work
- **As a developer**, I want visibility into the autonomous process, so that I can interrupt and take manual control if needed

## 4. Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-1 | Orchestrator executes end-to-end workflow autonomously (plan → implement → cleanup) | P0 | Core feature |
| FR-2 | Orchestrator makes autonomous decisions for technology stack selection | P1 | Decision engine |
| FR-3 | Orchestrator makes autonomous decisions for architecture patterns and design approaches | P1 | Decision engine |
| FR-4 | Orchestrator autonomously orders and prioritizes tasks with dependency resolution | P1 | Task coordination |
| FR-5 | Orchestrator implements smart error recovery with fallback strategies (retry, alternative approach, rollback) | P0 | Critical for autonomy |
| FR-6 | New command `/flow:autonomous` triggers the orchestrator | P1 | User interface |
| FR-7 | Orchestrator provides detailed logging with full transparency (all actions, decisions, rationale) | P2 | Visibility |
| FR-8 | Orchestrator maintains full persistence of decisions, rationale, and intermediate results | P1 | Replayability |
| FR-9 | Orchestrator creates git checkpoints at safe points for rollback capability | P0 | Safety |
| FR-10 | Orchestrator validates implementation with test suite, PRD requirements, and quality gates before completion | P2 | Quality |
| FR-11 | Orchestrator generates comprehensive report with all decisions, changes, and testing results | P2 | Handoff |
| FR-12 | Orchestrator implements iterative refinement pattern with continuous improvement | P1 | Execution pattern |
| FR-13 | Decision engine skill provides autonomous decision-making capabilities | P2 | New skill |
| FR-14 | Orchestrator leverages existing subagents (frontend-developer, backend-architect, test-automator, etc.) | P1 | Reuse existing |
| FR-15 | Orchestrator-specific skills created for coordination and decision-making | P3 | Extension |

## 5. Non-Goals (Out of Scope)

- **Real-time collaboration**: Maestro operates autonomously without collaborative editing
- **Multi-user coordination**: Single-developer workflow only
- **Deployment automation**: Stops at local implementation completion
- **Production monitoring**: No runtime monitoring or alerting
- **Natural language processing**: Does not generate natural language documentation or comments
- **Code review approval**: Does not replace human code review process
- **Custom workflow definition**: Does not provide workflow customization DSL

## 6. Assumptions

- User has git installed and configured
- User has flow commands available (or they will be created alongside Maestro)
- User has beads installed for task persistence
- Repository has existing test infrastructure
- Codebase follows conventional commit patterns
- Human will review implementation before merging to main branch

## 7. Dependencies

- **Flow Commands**: `/flow:plan`, `/flow:generate-tasks`, `/flow:implement`, `/flow:cleanup`
- **Beads (bd)**: Task persistence and dependency tracking
- **Subagent System**: Existing specialized subagents
- **Skills System**: Skill invocation framework
- **Git**: Version control for checkpoint/rollback
- **Test Infrastructure**: Existing test suite for validation

## 8. Acceptance Criteria

**FR-1: End-to-End Autonomy**
- Given: User provides feature request to `/flow:autonomous`
- When: Maestro executes
- Then: Complete implementation is produced without human intervention
- And: All phases (plan, generate-tasks, implement, cleanup) execute automatically

**FR-5: Smart Error Recovery**
- Given: Error occurs during implementation
- When: Maestro encounters error
- Then: Attempt recovery with fallback strategy (retry → alternative → rollback)
- And: Log all recovery attempts with rationale
- And: Only pause if all recovery strategies fail

**FR-9: Git Checkpoints**
- Given: Maestro is executing autonomously
- When: Safe point is reached (test passing, feature complete)
- Then: Create git commit with descriptive message
- And: Tag commit for easy rollback
- And: Log checkpoint location

**FR-10: Validation Gates**
- Given: Implementation is complete
- When: Maestro enters validation phase
- Then: Run test suite and verify all tests pass
- And: Validate all PRD requirements are met
- And: Run quality gates (linting, type checking, security scan)
- And: Only proceed to handoff if all gates pass

**FR-14: Existing Subagent Integration**
- Given: Task requires specialized expertise
- When: Maestro delegates to subagent
- Then: Select appropriate subagent based on task category
- And: Invoke relevant skills before subagent execution
- And: Pass context and requirements to subagent
- And: Incorporate subagent results back into orchestration

## 9. Design Considerations

### Command Interface

```bash
/flow:autonomous "Implement user authentication with OAuth support"
```

### Logging Output Format

```
[Maestro] Starting autonomous implementation...
[Maestro] Phase 1: Planning
[Maestro]   → Analyzing codebase for authentication patterns...
[Maestro]   → Decision: Using Passport.js for OAuth (existing dependency)
[Maestro]   → Decision: PostgreSQL for user sessions (existing database)
[Maestro]   ✓ PRD generated: prd-oauth-authentication-v1.md
[Maestro] Phase 2: Task Generation
[Maestro]   → Created 12 tasks across 3 parallel groups
[Maestro] Phase 3: Implementation
[Maestro]   → [Group-1] Executing 5 tasks in parallel...
[Maestro]       → Task bd-xxx: frontend-developer implementing OAuth UI
[Maestro]       → Task bd-yyy: backend-architect designing auth endpoints
[Maestro]       → ...
[Maestro]   ✓ Checkpoint: git commit -m "feat: OAuth authentication phase 1"
[Maestro]   → [Group-2] Executing 4 tasks...
[Maestro]       → Error in task bd-zzz: Test failure
[Maestro]       → Recovery: Re-running tests with verbose output
[Maestro]       → Recovery: Fixed test fixture issue
[Maestro]       → ✓ Task completed
[Maestro]   ✓ Checkpoint: git commit -m "feat: OAuth authentication complete"
[Maestro] Phase 4: Validation
[Maestro]   → Running test suite... 127/127 tests passed ✓
[Maestro]   → Validating PRD requirements... all 8 requirements met ✓
[Maestro]   → Quality gates... linting ✓, type-check ✓, security ✓
[Maestro] Phase 5: Handoff
[Maestro]   → Generating implementation report...
[Maestro] ✓ Autonomous implementation complete!
```

### Report Format

```markdown
# Maestro Implementation Report

## Summary
- Feature: OAuth Authentication
- Duration: 47 minutes
- Tasks Completed: 12/12
- Tests Passed: 127/127
- Checkpoints: 2

## Decisions Made
### Technology Stack
- OAuth Library: Passport.js (existing dependency, mature ecosystem)
- Session Store: PostgreSQL (existing database infrastructure)
- Token Strategy: JWT (stateless, scalable)

### Architecture
- Pattern: Middleware-based auth flow
- Route Structure: /api/auth/* endpoints
- Frontend Integration: React Context Provider

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

## 10. Technical Considerations

### State Persistence

Maestro state will be persisted in `.flow/maestro/`:

```
.flow/maestro/
├── sessions/
│   └── <session-id>/
│       ├── metadata.json          # Session info, status, timestamps
│       ├── decisions.json          # All decisions made with rationale
│       ├── checkpoints.json        # Git commit references
│       ├── execution-log.md        # Detailed execution log
│       └── final-report.md         # Generated report
├── decisions/
│   ├── tech-stack.json            # Historical tech decisions
│   ├── architecture.json           # Historical architecture decisions
│   └── task-ordering.json          # Historical task ordering patterns
└── config.yaml                     # Maestro configuration
```

### Decision Engine Architecture

The Decision Engine skill will implement:

```yaml
decision_engine:
  tech_stack_selection:
    sources:
      - existing_dependencies: "Scan package.json, requirements.txt"
      - codebase_patterns: "Grep for existing implementations"
      - ecosystem_maturity: "Evaluate npm/pypi stability"
    strategy: "prefer_existing > mature_new > experimental"

  architecture_patterns:
    sources:
      - codebase_analysis: "Find existing patterns"
      - complexity_assessment: "Evaluate feature complexity"
      - scalability_requirements: "Assess future needs"
    strategy: "match_existing > appropriate_new > over_engineered"

  task_ordering:
    sources:
      - dependency_analysis: "Parse beads dependency graph"
      - risk_assessment: "Identify high-risk tasks"
      - parallelization_opportunity: "Find independent task groups"
    strategy: "foundational_first > risk_early > parallel_where_possible"
```

### Error Recovery Strategies

```yaml
error_recovery:
  strategies:
    - name: "retry_with_backoff"
      triggers: ["network_timeout", "transient_error"]
      max_attempts: 3
      backoff: "exponential"

    - name: "alternative_approach"
      triggers: ["implementation_failure", "test_failure"]
      fallback: "switch_algorithm_or_pattern"

    - name: "rollback_to_checkpoint"
      triggers: ["critical_failure", "all_recovery_failed"]
      action: "git_reset_to_last_checkpoint"

    - name: "request_human_input"
      triggers: ["ambiguous_requirement", "conflicting_constraints"]
      action: "pause_and_create_decision_request"
```

### Integration with Existing Subagents

```yaml
subagent_mapping:
  frontend:
    subagent: "frontend-developer"
    skills: ["frontend-design"]
    triggers: ["ui", "component", "frontend", "react", "vue"]

  backend:
    subagent: "backend-architect"
    skills: []
    triggers: ["api", "endpoint", "service", "controller"]

  database:
    subagent: "database-admin"
    skills: []
    triggers: ["schema", "migration", "query", "database"]

  testing:
    subagent: "test-automator"
    skills: ["webapp-testing"]
    triggers: ["test", "spec", "coverage", "tdd"]

  documentation:
    subagent: "api-documenter"
    skills: ["document-skills"]
    triggers: ["docs", "api-spec", "readme"]
```

### Iterative Refinement Pattern

```yaml
iterative_refinement:
  loop:
    - phase: "plan"
      output: "prd"

    - phase: "implement"
      output: "code"

    - phase: "validate"
      output: "test_results"

    - phase: "review"
      output: "improvement_opportunities"
      decision: "refine_or_complete"

  completion_criteria:
    - all_tests_passing
    - all_prd_requirements_met
    - quality_gates_passed
    - no_critical_issues
```

## 11. Architecture Patterns

### Pattern Checklist

**SOLID Principles:**
- [x] **Single Responsibility**: Maestro orchestrates, subagents execute, skills guide - clear separation
- [x] **Open/Closed**: New decision strategies can be added without modifying orchestrator core
- [x] **Liskov Substitution**: Any subagent can be swapped for another with same interface
- [x] **Interface Segregation**: Orchestrator uses minimal interfaces (execute, report, checkpoint)
- [x] **Dependency Inversion**: Maestro depends on abstractions (subagent protocol) not concrete implementations

**Creational Patterns:**
- [x] **Factory Pattern**: Subagent factory creates appropriate subagent based on task category
- [x] **Abstract Factory**: Decision engine factory for different decision types (tech, architecture, ordering)
- [ ] **Builder**: Not needed - decision objects are simple JSON structures

**Structural Patterns:**
- [x] **Registry Pattern**: Subagent registry maps task categories to subagent types
- [x] **Adapter**: Existing flow commands adapted for autonomous invocation
- [ ] **Decorator**: Not needed - logging is built into orchestrator

**Inversion of Control / Dependency Injection:**
- [x] **Constructor Injection**: Orchestrator receives dependencies (flow commands, beads, git)
- [x] **Service Locator**: Subagent registry for lookup (appropriate for this use case)

### Key Architectural Decisions

1. **Orchestration Layer Separation**: Maestro is a thin orchestration layer that coordinates existing flow commands
2. **Decision Engine as Skill**: Decision-making is encapsulated as a reusable skill
3. **State-Based Checkpoints**: Git commits serve as atomic state checkpoints for rollback
4. **Parallel Group Execution**: Leverage existing `[P:Group-X]` pattern from `/flow:implement`
5. **Persistent Decision Log**: All decisions logged for replayability and learning

## 12. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Maestro makes poor technical decisions | High | Medium | Decision engine uses codebase analysis to prefer existing patterns; human can review report before accepting |
| Infinite loop in iterative refinement | High | Low | Max iteration limits; timeout mechanisms; checkpoint rollback |
| Test suite passes but implementation incorrect | High | Medium | PRD requirement validation; quality gates; human review in handoff |
| Conflicts with manual development | Medium | Medium | Worktree isolation; clear checkpoint markers; merge conflict detection |
| Resource exhaustion (tokens, time) | Medium | Low | Context refresh protocols; periodic summaries; cost monitoring |
| Poor error recovery leads to corrupted state | High | Low | Git checkpoints before risky operations; atomic phase transitions |

## 13. Success Metrics

- **Autonomy Success Rate**: Percentage of sessions that complete without human intervention (Target: >80%)
- **Decision Quality**: Percentage of decisions retained after human review (Target: >90%)
- **Test Pass Rate**: Percentage of Maestro implementations with passing tests (Target: >95%)
- **Recovery Success Rate**: Percentage of errors successfully recovered without human input (Target: >70%)
- **Session Duration**: Average time from feature request to complete implementation (Baseline: existing flow)
- **Checkpoint Utility**: Percentage of checkpoints used for rollback (Target: <10% indicates good forward progress)

## 14. Priority/Timeline

- **P0 (Critical)**: Core orchestration, error recovery, git checkpoints - Must have for MVP
- **P1 (High)**: Decision-making, state persistence, subagent integration - Must have for MVP
- **P2 (Normal)**: Logging, validation, reporting - Should have for MVP
- **P3 (Low)**: Orchestrator-specific skills - Nice to have for V2

Target: Initial MVP in current feature branch

## 15. Open Questions

1. Should Maestro create a new worktree automatically, or expect user to create one?
2. How should Maestro handle merge conflicts when integrating with main branch?
3. Should Maestro support incremental feature requests (e.g., "add OAuth to the existing auth system")?
4. What is the maximum session duration before Maestro should pause for human continuation?

## 16. Glossary

- **Autonomous**: Operating without human intervention
- **Checkpoint**: Git commit representing a safe, consistent state
- **Decision Engine**: Skill that makes technical decisions autonomously
- **Flow Commands**: Existing workflow commands (plan, generate-tasks, implement, cleanup)
- **Iterative Refinement**: Plan-implement-validate-review loop
- **Maestro**: The orchestrator system
- **Smart Recovery**: Self-healing error handling with fallback strategies
- **Subagent**: Specialized AI agent for specific task categories

## 17. Changelog

| Version | Date | Summary of Changes |
| ------- | ---- | ------------------- |
| 1 | 2025-01-07 | Initial PRD |
