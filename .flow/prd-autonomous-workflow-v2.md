---
prd:
  version: v2
  feature_name: autonomous-workflow
  status: implementing
git:
  branch: feat-orchestrate-flow
  branch_type: feature
  created_at_commit: bfe5735
  updated_at_commit: bfe5735c6859fae896fd5b335ca25a2677669979
worktree:
  is_worktree: true
  name: feat-orchestrate-flow
  path: /home/ll931217/GitHub/dotfiles.feat-orchestrate-flow/.git/worktrees/feat-orchestrate-flow
  repo_root: /home/ll931217/GitHub/dotfiles.feat-orchestrate-flow
metadata:
  created_at: 2025-01-08T12:00:00Z
  updated_at: 2025-01-08T15:30:00Z
  created_by: ll931217 <ll931217@users.noreply.github.com>
  filename: prd-autonomous-workflow-v2.md
beads:
  related_issues: [dotfiles-p6s.1, dotfiles-p6s.2, dotfiles-p6s.3, dotfiles-p6s.4, dotfiles-p6s.5, dotfiles-cwj.1, dotfiles-cwj.2, dotfiles-cwj.3, dotfiles-cwj.4, dotfiles-5pl.1, dotfiles-5pl.2, dotfiles-5pl.3, dotfiles-5pl.4, dotfiles-5pl.5, dotfiles-5pl.6, dotfiles-1dc.1, dotfiles-1dc.2, dotfiles-1dc.3, dotfiles-1dc.4, dotfiles-d6g.1, dotfiles-d6g.2, dotfiles-d6g.3, dotfiles-d6g.4]
  related_epics: [dotfiles-p6s, dotfiles-cwj, dotfiles-5pl, dotfiles-1dc, dotfiles-d6g]
code_references:
  - path: .flow/maestro/scripts/orchestrator.py
    lines: 233-280
    reason: Current workflow phase orchestration with iterative refinement
  - path: .flow/maestro/scripts/orchestrator.py
    lines: 293-311
    reason: TODO markers for autonomous PRD generation integration
  - path: .flow/maestro/scripts/orchestrator.py
    lines: 323-371
    reason: TODO markers for autonomous implementation and task execution
  - path: .flow/maestro/scripts/session_manager.py
    lines: 20-30
    reason: SessionStatus enum with PAUSED state currently unused
  - path: .flow/maestro/scripts/error_handler.py
    lines: 377-419
    reason: Recovery strategy selection logic for autonomous error handling
  - path: .flow/maestro/scripts/error_handler.py
    lines: 549-577
    reason: Human input request mechanism that needs autonomous fallback
  - path: .flow/maestro/scripts/phase_manager.py
    lines: 100-153
    reason: Phase configurations and transitions for autonomous flow
priorities:
  enabled: true
  default: P2
  inference_method: ai_inference_with_review
  requirements:
    - id: FR-1
      text: "Planning phase accepts human input once, then becomes autonomous"
      priority: P0
      confidence: high
      inferred_from: "User explicitly specified one-time planning as critical requirement"
      user_confirmed: false
    - id: FR-2
      text: "Implementation phase runs without human intervention"
      priority: P0
      confidence: high
      inferred_from: "Core requirement for true autonomy after planning"
      user_confirmed: false
    - id: FR-3
      text: "Validation phase auto-recovers from failures without human input"
      priority: P0
      confidence: high
      inferred_from: "User explicitly selected auto-recover for validation failures"
      user_confirmed: false
    - id: FR-4
      text: "Decision engine makes autonomous tech stack choices"
      priority: P1
      confidence: high
      inferred_from: "User selected tech selection as enhancement area"
      user_confirmed: false
    - id: FR-5
      text: "Decision engine autonomously orders implementation tasks"
      priority: P1
      confidence: high
      inferred_from: "User selected task ordering as enhancement area"
      user_confirmed: false
    - id: FR-6
      text: "Ambiguous decisions use sensible defaults without human input"
      priority: P1
      confidence: high
      inferred_from: "User explicitly chose 'Use defaults' for ambiguity handling"
      user_confirmed: false
    - id: FR-7
      text: "System includes automatic rollback capability on failure"
      priority: P0
      confidence: high
      inferred_from: "User selected rollback as critical safeguard"
      user_confirmed: false
    - id: FR-8
      text: "Resource limits constrain time, tokens, and API calls"
      priority: P0
      confidence: high
      inferred_from: "User selected resource limits as critical safeguard"
      user_confirmed: false
    - id: FR-9
      text: "Comprehensive logging tracks all autonomous decisions"
      priority: P1
      confidence: high
      inferred_from: "User selected comprehensive logging as safeguard"
      user_confirmed: false
    - id: FR-10
      text: "Decision engine selects alternative approaches autonomously"
      priority: P2
      confidence: medium
      inferred_from: "User selected approach selection as enhancement area"
      user_confirmed: false
    - id: FR-11
      text: "Decision engine makes autonomous architectural decisions"
      priority: P2
      confidence: medium
      inferred_from: "User selected architecture as enhancement area"
      user_confirmed: false
    - id: FR-12
      text: "Report generation runs autonomously without human review"
      priority: P2
      confidence: medium
      inferred_from: "Part of full autonomy scope"
      user_confirmed: false
    - id: FR-13
      text: "Checkpoint system supports automatic rollback"
      priority: P1
      confidence: medium
      inferred_from: "Required for rollback safeguard implementation"
      user_confirmed: false
    - id: FR-14
      text: "Quality gates use auto-recovery strategies on failure"
      priority: P1
      confidence: medium
      inferred_from: "Supports auto-recover requirement for validation"
      user_confirmed: false
---

# PRD: Autonomous Workflow Enhancement for Maestro Orchestrator

## Introduction

This PRD describes enhancements to the Maestro Orchestrator to enable **true autonomous operation** after an initial human-guided planning phase. Currently, the orchestrator has TODO markers and placeholder implementations that require human intervention. This enhancement will complete the autonomous workflow, allowing the system to operate independently from planning through completion.

### Current State

The Maestro Orchestrator v1 implements:
- Session and state management
- Error detection and recovery strategies
- Checkpoint system for rollback capability
- Subagent coordination layer
- Decision engine skill integration (partial)

However, critical workflow phases have TODO markers:
```python
# TODO: Invoke /flow:plan in autonomous mode
# TODO: Invoke /flow:generate-tasks with decision engine
# TODO: Execute tasks with parallel coordinator
# TODO: Execute test suite
# TODO: Validate against PRD
# TODO: Execute quality gates
```

### Goal

Transform Maestro Orchestrator into a **fully autonomous system** that:
1. Accepts human input **once** during the planning phase
2. Executes **all subsequent phases without human intervention**
3. Makes autonomous decisions using the decision engine
4. Auto-recovers from validation failures
5. Includes comprehensive safeguards (rollback, resource limits, logging)

## Goals

1. **Single Human Interaction Point**: Planning phase is the only phase requiring human input
2. **Full Autonomous Execution**: Implementation, validation, and reporting run without intervention
3. **Autonomous Decision-Making**: System makes technical choices independently using defaults
4. **Resilient Execution**: Auto-recovery from failures without human input
5. **Comprehensive Safeguards**: Rollback, resource limits, and audit logging protect against runaway processes

## User Stories

1. **As a developer**, I want to provide requirements once during planning, so that the system implements the entire feature autonomously.
2. **As a developer**, I want the system to recover from errors automatically, so that I don't need to monitor execution constantly.
3. **As a developer**, I want comprehensive logging of autonomous decisions, so that I can understand what the system did and why.
4. **As a developer**, I want automatic rollback on critical failures, so that my codebase doesn't get into a broken state.
5. **As a developer**, I want resource limits to prevent runaway autonomous processes, so that the system doesn't consume excessive time or tokens.

## Functional Requirements

| ID   | Requirement                                                            | Priority | Notes                              |
|------|------------------------------------------------------------------------|----------|------------------------------------|
| FR-1 | Planning phase accepts human input once, then becomes autonomous       | P0       | Single interaction point            |
| FR-2 | Implementation phase runs without human intervention                  | P0       | Core autonomy requirement            |
| FR-3 | Validation phase auto-recovers from failures without human input       | P0       | Resilient execution                 |
| FR-4 | Decision engine makes autonomous tech stack choices                   | P1       | Enhanced decision-making             |
| FR-5 | Decision engine autonomously orders implementation tasks              | P1       | Enhanced decision-making             |
| FR-6 | Ambiguous decisions use sensible defaults without human input          | P1       | Default-based autonomy               |
| FR-7 | System includes automatic rollback capability on failure               | P0       | Critical safeguard                   |
| FR-8 | Resource limits constrain time, tokens, and API calls                 | P0       | Critical safeguard                   |
| FR-9 | Comprehensive logging tracks all autonomous decisions                  | P1       | Audit trail requirement              |
| FR-10 | Decision engine selects alternative approaches autonomously          | P2       | Enhanced decision-making             |
| FR-11 | Decision engine makes autonomous architectural decisions               | P2       | Enhanced decision-making             |
| FR-12 | Report generation runs autonomously without human review              | P2       | Complete autonomy                    |
| FR-13 | Checkpoint system supports automatic rollback                         | P1       | Required for rollback safeguard       |
| FR-14 | Quality gates use auto-recovery strategies on failure                | P1       | Supports validation auto-recovery    |

## Non-Goals (Out of Scope)

- **Real-time monitoring dashboard**: The system will log comprehensively, but a live monitoring UI is out of scope
- **Human approval gates**: After planning, no phase requires human approval to proceed
- **Interactive debugging**: Debugging autonomous failures happens post-hoc via logs, not interactively
- **Multi-user collaboration**: Autonomous workflow assumes single-user context
- **Dynamic re-planning**: Once planning completes, the PRD is not modified mid-execution

## Assumptions

1. **Decision engine skill is available**: The existing decision-engine skill will be used for autonomous choices
2. **Git repository is available**: Checkpoint system requires git for rollback capability
3. **Test suite exists**: Validation phase expects tests to be present
4. **Quality gates are defined**: System expects quality gate configuration
5. **User has git write access**: Autonomous commits require write permissions

## Dependencies

1. **Existing Maestro Orchestrator v1**: Builds upon completed orchestrator infrastructure
2. **Decision Engine Skill**: Must be installed and accessible
3. **Error Recovery System**: Uses existing error handler and checkpoint manager
4. **Subagent Coordination Layer**: Uses existing parallel coordinator
5. **Session Management**: Uses existing session and phase managers

## Acceptance Criteria

### AC-1: One-Time Planning Phase
- **Given**: A new feature request is submitted
- **When**: The planning phase executes
- **Then**: Human is prompted for clarifying questions exactly once
- **And**: All subsequent phases proceed without human input
- **And**: Planning output is saved as PRD that guides autonomous execution

### AC-2: Autonomous Implementation
- **Given**: Planning phase completed with approved PRD
- **When**: Implementation phase executes
- **Then**: Tasks are generated and ordered automatically
- **When**: Subagents execute tasks
- **Then**: No human input is requested during execution
- **And**: Progress is tracked via checkpoints
- **And**: Failures trigger recovery strategies without human intervention

### AC-3: Auto-Recovery on Validation Failure
- **Given**: Validation phase executes
- **When**: Quality gate or test fails
- **Then**: System attempts recovery (fix, retry, alternative approach)
- **And**: Only requests human input if all recovery strategies exhausted
- **And**: Recovery attempts are logged with rationale

### AC-4: Autonomous Decision-Making
- **Given**: Implementation requires technical choices (tech stack, architecture, approach)
- **When**: Decision is needed
- **Then**: Decision engine is invoked automatically
- **And**: Decision is logged with rationale
- **And**: Execution proceeds with selected option

### AC-5: Rollback on Critical Failure
- **Given**: Critical error occurs during autonomous execution
- **When**: Error is unrecoverable (all strategies exhausted)
- **Then**: System rolls back to last checkpoint
- **And**: Session is marked as failed
- **And**: Failure details are logged comprehensively

### AC-6: Resource Limits Enforcement
- **Given**: Autonomous execution is running
- **When**: Resource limits are approached (time, tokens, API calls)
- **Then**: Execution pauses and assesses progress
- **And**: If near completion, continues with remaining budget
- **And**: If not near completion, stops gracefully with partial results

### AC-7: Comprehensive Logging
- **Given**: Autonomous execution is in progress
- **When**: Any autonomous decision is made
- **Then**: Decision is logged with: timestamp, context, options considered, choice, rationale
- **And**: All errors are logged with: error type, recovery strategy attempted, outcome
- **And**: Logs are structured and queryable

## Technical Considerations

### Current Architecture Gaps

The orchestrator has placeholder implementations that need completion:

**File: `.flow/maestro/scripts/orchestrator.py`**
- Lines 293-304: `_phase_planning` needs to invoke `/flow:plan` autonomously
- Lines 313-322: `_phase_task_generation` needs to invoke decision engine
- Lines 342-350: `_phase_implementation` needs parallel coordinator integration
- Lines 373-381: `_phase_validation` needs test execution and auto-recovery
- Lines 409-416: `_phase_review` needs autonomous continuation logic

### Decision Engine Integration

The decision engine must be enhanced to support:
1. **Tech stack selection**: Choose languages, frameworks, libraries based on PRD requirements
2. **Task ordering**: Optimize task sequence for parallel execution
3. **Approach selection**: Choose between implementation alternatives
4. **Architecture decisions**: Make architectural pattern choices

### Default Decision Framework

When ambiguous decisions arise, use this hierarchy:
1. **Best practices**: Apply industry-standard patterns
2. **Existing patterns**: Follow patterns already in codebase
3. **Simplicity**: Choose simplest viable option
4. **Consistency**: Match existing code style and structure

### Resource Limit Configuration

```yaml
resource_limits:
  max_duration_seconds: 3600  # 1 hour max
  max_tokens: 1000000          # 1M tokens max
  max_api_calls: 1000          # API call budget
  checkpoint_interval: 300     # Checkpoint every 5 minutes
```

### Rollback Strategy

- **Pre-risky-operation checkpoint**: Before any destructive operation (git push, file deletion)
- **Auto-rollback triggers**: Unrecoverable errors, resource exhaustion, validation failure after N attempts
- **Rollback method**: Git reset to last checkpoint SHA

## Architecture Patterns

### SOLID Principles

- [x] **Single Responsibility**: Each phase handler (planning, implementation, validation) has one clear job
- [x] **Open/Closed**: New recovery strategies can be added without modifying existing handlers
- [ ] **Liskov Substitution**: Phase handlers should be substitutable (needs interface)
- [x] **Interface Segregation**: Decision engine exposes only needed methods
- [x] **Dependency Inversion**: Orchestrator depends on phase manager abstractions

### Creational Patterns

- [x] **Factory Pattern**: `SubagentFactory` creates appropriate subagents for tasks
- [ ] **Abstract Factory**: Could use for different PRD types (consider for v3)
- [ ] **Builder**: Could use for complex session configuration (consider for v3)

### Structural Patterns

- [x] **Registry Pattern**: `PhaseManager` registers and executes phases
- [x] **Adapter**: `ErrorHandler` adapts different error types to recovery strategies
- [ ] **Decorator**: Could add logging/monitoring decorators to phase execution (v3)

### Strategy Pattern (Key Enhancement)

The **Strategy Pattern** is central to autonomous decision-making:

```python
class DecisionStrategy(ABC):
    @abstractmethod
    def decide(self, context: DecisionContext) -> Decision:
        pass

class TechStackStrategy(DecisionStrategy):
    def decide(self, context: DecisionContext) -> Decision:
        # Analyze PRD requirements
        # Select appropriate tech stack
        # Return decision with rationale

class TaskOrderingStrategy(DecisionStrategy):
    def decide(self, context: DecisionContext) -> Decision:
        # Analyze task dependencies
        # Optimize for parallel execution
        # Return ordered task list
```

### Inversion of Control

- [x] **Constructor Injection**: Phase managers injected into orchestrator
- [ ] **Service Locator**: Could use for strategy lookup (consider for v3)
- [x] **DI Container**: Not using a framework, but following DI principles

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Runaway autonomous process** | High (resource waste) | Resource limits enforced, checkpoint rollback |
| **Poor autonomous decisions** | High (bad code quality) | Comprehensive logging, decision rationale tracking |
| **Infinite recovery loops** | Medium (stuck execution) | Max retry limits, escalation to human after N attempts |
| **Git repository corruption** | High (data loss) | Pre-operation checkpoints, tested rollback logic |
| **Resource exhaustion** | Medium (failed execution) | Budget tracking, graceful degradation |
| **Ambiguous decision deadlocks** | Medium (stuck execution) | Default decision framework, timeout with fallback |
| **Loss of audit trail** | Low (debugging difficulty) | Structured logging, immutable decision log |

## Success Metrics

1. **Autonomy Ratio**: Percentage of workflow executed without human input
   - Target: >95% (only planning phase requires input)
2. **Recovery Success Rate**: Percentage of failures auto-recovered
   - Target: >80% (most issues resolved autonomously)
3. **Decision Quality**: Percentage of autonomous decisions judged appropriate in post-hoc review
   - Target: >85% (decisions follow best practices)
4. **Resource Utilization**: Percentage of resource limits used in successful executions
   - Target: <90% (headroom for edge cases)
5. **Rollback Success Rate**: Percentage of rollbacks that restore working state
   - Target: 100% (rollback must be reliable)

## Implementation Phases

### Phase 1: Decision Engine Enhancement (P1)
- Integrate decision-engine skill for autonomous choices
- Implement default decision framework
- Add comprehensive decision logging

### Phase 2: Autonomous Phase Execution (P0)
- Complete TODO placeholders in orchestrator.py
- Implement auto-recovery for validation failures
- Add resource limit enforcement

### Phase 3: Safeguards Implementation (P0)
- Enhance checkpoint system for automatic rollback
- Implement comprehensive logging framework
- Add resource monitoring and limits

### Phase 4: Testing & Validation (P1)
- Unit tests for autonomous decision-making
- Integration tests for auto-recovery scenarios
- E2E tests for full autonomous workflow

## Open Questions

1. **Default decision library**: Should we maintain a curated library of default decisions for common scenarios?
2. **Human escalation criteria**: What specific conditions should trigger human input despite autonomy goal?
3. **Partial execution handling**: How should the system handle resource limits reached mid-task?
4. **Decision confidence thresholds**: Should low-confidence autonomous decisions trigger human review?
5. **Multi-PRD coordination**: If multiple autonomous workflows run in parallel, how are conflicts resolved?

## Changelog

| Version | Date | Summary of Changes |
|---------|------|-------------------|
| 2 | 2025-01-08 | Initial PRD for autonomous workflow enhancement |
