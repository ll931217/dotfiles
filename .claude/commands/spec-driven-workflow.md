# Spec-Driven Development Workflow with TDD Enforcement

Complete workflow for implementing features using specification-driven development with mandatory TDD practices and concurrent execution capabilities.

## Overview

This workflow combines the best practices from both traditional PRD-based development and advanced spec-driven development, with non-negotiable TDD enforcement and sophisticated parallel execution.

## 4-Phase Development Lifecycle

### Phase 1: Specification (`/specify`)
**Goal**: Create comprehensive feature specification
- Run feature specification creation process
- Define requirements, user stories, and acceptance criteria  
- Establish success metrics and technical constraints
- Output: `/specs/feature-name.md`

### Phase 2: Planning (`/plan`) 
**Goal**: Create implementation plan with design documents
- Analyze specification and technical requirements
- Generate design documents: `data-model.md`, `contracts/`, `quickstart.md`
- Create research documentation for technical decisions
- Output: Complete design artifact set in `/specs/feature-name/`

### Phase 3: Task Generation (`/generate-tasks`)
**Goal**: Break down plan into executable TDD-compliant tasks
- Parse design documents and create structured task list
- **CRITICAL**: Structure with mandatory TDD phases:
  - Phase X.1: Setup & Dependencies
  - **Phase X.2: Contract Tests (TDD) - MANDATORY FAILING TESTS** 
  - Phase X.3: Core Implementation
  - Phase X.4: Integration & Validation
- Mark parallel tasks with `[P]` flags
- Generate context files for inter-agent communication
- Output: `/tasks/tasks-feature-name.md`

### Phase 4: Implementation (`/process-task-list`)
**Goal**: Execute tasks with TDD enforcement and concurrent execution
- **NON-NEGOTIABLE TDD RULE**: Tests MUST fail before implementation
- Execute tasks with atomic state management (`[ ]` → `[>]` → `[x]`/`[!]`)
- Run parallel tasks concurrently within phases using multiple Task agents
- Validate at phase boundaries with constitutional compliance checks
- Output: Implemented feature with 100% test coverage

## TDD Enforcement Rules

### Contract Test Phase (Phase X.2) - CRITICAL
```bash
# MANDATORY: All contract tests must fail before implementation
npm test 2>&1 | grep -E "(FAIL|failed|error)" || {
  echo "✗ BLOCKED: Contract tests must fail before implementation"
  exit 1
}
```

### Implementation Phases (Phase X.3+)
```bash
# Only proceed after verifying tests fail appropriately
if [[ $(npm test 2>&1 | grep -c "FAIL") -gt 0 ]]; then
  echo "✓ Proceeding with implementation - tests failing as expected"
else
  echo "✗ ERROR: No failing tests found - TDD violation"
  exit 1
fi
```

### Post-Implementation Validation
```bash
# After implementation: ALL tests must pass
npm test && echo "✓ All tests passing" || {
  echo "✗ Implementation incomplete - tests still failing"
  exit 1
}
```

## Parallel Execution Patterns

### Contract Test Creation (Parallel)
```bash
# Phase X.2: Execute contract tests in parallel
sed -i 's/- \[ \] T005/- [>] T005/' tasks-file.md  # API test
sed -i 's/- \[ \] T006/- [>] T006/' tasks-file.md  # Model test  
sed -i 's/- \[ \] T007/- [>] T007/' tasks-file.md  # Service test

# Execute parallel test creation
Task "test-automator" "Create failing API contract test [Context: /tasks/context/T005_api_test.md]" &
Task "test-automator" "Create failing model contract test [Context: /tasks/context/T006_model_test.md]" &
Task "backend-architect" "Create failing service contract test [Context: /tasks/context/T007_service_test.md]" &
wait

# Verify ALL tests fail before marking complete
npm test 2>&1 | grep -c "FAIL" | grep -E "^[3-9]|^[1-9][0-9]" && {
  sed -i 's/- \[>\] T005/- [x] T005/' tasks-file.md
  sed -i 's/- \[>\] T006/- [x] T006/' tasks-file.md  
  sed -i 's/- \[>\] T007/- [x] T007/' tasks-file.md
} || {
  echo "✗ Not all contract tests failing - marking as blocked"
  sed -i 's/- \[>\] T005/- [!] T005/' tasks-file.md
}
```

### Implementation Phase (Parallel where possible)
```bash
# Phase X.3: Parallel implementation (different files only)
Task "database-admin" "Implement User model [Context: /tasks/context/T010_user_model.md]" &
Task "backend-architect" "Implement Auth service [Context: /tasks/context/T011_auth_service.md]" &  
Task "api-documenter" "Implement API routes [Context: /tasks/context/T012_api_routes.md]" &
wait
```

## State Management & Recovery

### Task States
- `[ ]` - Pending task
- `[>]` - In progress (atomically updated)
- `[x]` - Completed successfully
- `[!]` - Failed/blocked (requires intervention)

### Recovery Patterns
```bash
# Resume from interruption - parse existing states
grep -E "\[(x|!|>| )\]" tasks-file.md | head -20

# Re-run failed tasks marked [!]
grep "\[!\]" tasks-file.md | while read line; do
  echo "Failed task requires attention: $line"
done

# Never leave tasks in [>] state on exit
find_in_progress_tasks() {
  if grep -q "\[>\]" tasks-file.md; then
    echo "WARNING: Tasks left in progress state - resolving..."
    # Either complete or mark as failed
  fi
}
```

## Constitutional Compliance & Validation

### Phase Boundary Checks
```bash
# After each phase completion
run_phase_validation() {
  local phase=$1
  echo "Validating Phase $phase completion..."
  
  # Run package validation
  npm run lint && npm run typecheck && npm test || {
    echo "✗ Phase $phase validation failed"
    return 1
  }
  
  # Verify all tasks in phase are complete
  local incomplete=$(grep -c "\[ \].*Phase $phase" tasks-file.md || echo 0)
  if [[ $incomplete -gt 0 ]]; then
    echo "✗ Phase $phase has $incomplete incomplete tasks"
    return 1
  fi
  
  echo "✓ Phase $phase validation passed"
}
```

### Constitutional Compliance
- **TDD is NON-NEGOTIABLE**: Never skip failing tests
- **Test coverage**: Maintain above 80% coverage
- **Code quality**: All linting and type checks must pass
- **Documentation**: Update relevant files section in task list

## Usage Examples

### Full Workflow Execution
```bash
# 1. Create specification
/specify "User authentication system with JWT tokens"

# 2. Generate implementation plan  
/plan "Based on auth spec, create technical design"

# 3. Generate TDD-compliant task list
/generate-tasks "From auth plan, create executable tasks"

# 4. Execute with TDD enforcement
/process-task-list "Implement auth system following TDD"
```

### Mid-workflow Recovery
```bash
# Resume from existing task list
/process-task-list "Resume auth implementation from interruption"

# System will:
# - Parse existing task states
# - Resume from first [ ] or [!] task  
# - Re-run contract test validation
# - Continue with parallel execution where appropriate
```

## Integration with Existing Commands

This workflow enhances your existing commands:
- **`create-prd.md`** → Use for initial requirements gathering, then transition to `/specify`
- **`generate-tasks.md`** → Enhanced with TDD phases and parallel execution patterns
- **`process-task-list.md`** → Enhanced with concurrent execution and TDD enforcement

The workflow maintains backward compatibility while adding sophisticated TDD enforcement and parallel execution capabilities.