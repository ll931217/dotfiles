# Task List Management - Enhanced Concurrent Execution

Advanced guidelines for managing task lists with parallel/concurrent execution capabilities to efficiently complete PRD implementation tasks.

## Task Implementation

### Sequential Task Flow
- **One sub-task at a time:**
  - Do **NOT** start the next sub-task until you ask the user for permission and they say "yes" or "y"
  - Exception: If the next sub-task is a parallel sub-task, indicated with "[P]", run them all in parallel with their specialized sub-agents

### Concurrent Execution Engine
- **Identify parallel execution groups** by scanning for `[P]` flags within the same phase
- **Execute [P] tasks concurrently** when no dependencies block them
- **State management using atomic updates:**
  - `[ ]` → `[>]` → `[x]` (successful completion)
  - `[ ]` → `[>]` → `[!]` (failed/blocked)
  - Use `sed` commands for atomic checkbox updates in task files

### Parallel Execution Management
- **Phase-based execution:**
  - Group [P] tasks within same phase boundary
  - Execute using multiple Task tool invocations in parallel
  - Wait for all parallel tasks to complete before proceeding to next phase
- **Context file communication:**
  - Always update context files when completing changes
  - Read context files from other sub-agents before starting work
  - Context files located at `/tasks/context/{task_number}_{description}.md`
- **Atomic task updates:**
  ```bash
  # Mark as in progress
  sed -i 's/- \[ \] TaskID/- [>] TaskID/' tasks-file.md
  
  # Execute task with Task tool
  Task "specialized-agent" "task description with context"
  
  # Mark as complete or failed
  sed -i 's/- \[>\] TaskID/- [x] TaskID/' tasks-file.md  # success
  sed -i 's/- \[>\] TaskID/- [!] TaskID/' tasks-file.md  # failure
  ```
### Completion Protocol
- **Sub-task completion:**
  - When you finish a **sub-task**, immediately mark it as completed using `sed`:
    ```bash
    sed -i 's/- \[>\] TaskID/- [x] TaskID/' tasks-file.md
    ```
- **Parent task completion (when all sub-tasks are `[x]`):**
  - **First**: Run the full test suite (`pytest`, `npm test`, `bin/rails test`, etc.)
  - **Only if all tests pass**: Stage changes (`git add .`) 
  - **Clean up**: Remove any temporary files and temporary code before committing
  - **Commit**: Use a descriptive commit message with conventional format:
    ```bash
    git commit -m "feat: add payment validation logic" \
               -m "- Validates card type and expiry" \
               -m "- Adds unit tests for edge cases" \
               -m "Related to T123 in PRD"
    ```
  - **Mark parent task complete:**
    ```bash
    sed -i 's/- \[ \] ParentTaskID/- [x] ParentTaskID/' tasks-file.md
    ```

### Resume Capability
- **Parse existing task states** to resume from interruption:
  - Find last completed task (`[x]`)
  - Resume from first pending (`[ ]`) or failed (`[!]`) task
  - Re-run failed tasks marked with `[!]`
  - Respect phase boundaries (don't skip phases)

### Error Handling and Recovery
- **Failed task management:**
  ```bash
  # Mark task as failed
  sed -i 's/- \[>\] TaskID/- [!] TaskID/' tasks-file.md
  
  # Log detailed error in context file
  echo "## Error Log - $(date)" >> /tasks/context/TaskID_name.md
  echo "Task: TaskID - [task description]" >> /tasks/context/TaskID_name.md
  echo "Error: [detailed error description]" >> /tasks/context/TaskID_name.md
  echo "Exit code: $?" >> /tasks/context/TaskID_name.md
  echo "Recovery steps: [specific actions needed]" >> /tasks/context/TaskID_name.md
  echo "Dependencies: [list of blocking/blocked tasks]" >> /tasks/context/TaskID_name.md
  ```
- **Enhanced recovery strategies:**
  - **Analyze failure**: Check logs, test outputs, error messages, and exit codes
  - **Test failure handling**: Use test-automator for comprehensive test debugging
    ```bash
    # For test failures, get detailed analysis
    Task "test-automator" "Analyze and fix failing tests in TaskID [Context: /tasks/context/TaskID_name.md]"
    ```
  - **Dependency management**: Identify which tasks are blocked by failures
    ```bash
    # Check task dependencies before retry
    grep -A 5 -B 5 "TaskID" tasks-file.md | grep -E "\[(x|!)\]"
    ```
  - **Retry with fixes**: Address root cause before re-attempting
  - **Parallel task recovery**: Handle failures in concurrent execution gracefully
  - **Skip blocked tasks**: Continue with non-dependent tasks when possible
  - **Escalate if needed**: Mark as `[!]` and provide clear recovery guidance
- **Never leave tasks in `[>]` state** on exit - always resolve to `[x]` or `[!]`
- **Test-specific failure patterns:**
  ```bash
  # Handle TDD violations (tests not failing when they should)
  if ! npm test 2>&1 | grep -q "FAIL"; then
    echo "TDD VIOLATION: Contract tests must fail before implementation" >> /tasks/context/TaskID_name.md
    sed -i 's/- \[>\] TaskID/- [!] TaskID/' tasks-file.md
  fi
  
  # Handle post-implementation test failures  
  if npm test 2>&1 | grep -q "FAIL"; then
    echo "IMPLEMENTATION INCOMPLETE: Tests still failing after implementation" >> /tasks/context/TaskID_name.md
    Task "test-automator" "Fix failing tests after implementation [Context: /tasks/context/TaskID_name.md]"
  fi
  ```

### TDD Enforcement & Constitutional Compliance
- **NON-NEGOTIABLE TDD RULE**: Tests MUST fail before implementation
  - **Before any implementation task**: Verify contract tests exist and fail
  - **Block progression** until all tests exist and fail as expected
  - **Never skip failed tests** - TDD is mandatory
- **Contract test validation sequence:**
  ```bash
  # 1. Verify tests exist and fail
  npm test 2>&1 | grep -E "(FAIL|failed|error)" || echo "ERROR: Tests must fail before implementation"
  
  # 2. Only proceed if tests fail appropriately
  if [[ $? -eq 0 ]]; then
    echo "✓ Contract tests failing as expected - proceeding with implementation"
  else
    echo "✗ BLOCKED: Tests must fail before implementation"
    exit 1
  fi
  ```
- **Phase validation (after each phase)**:
  - Run package validation commands (`npm run lint`, `npm test`, `npm run check:all`)
  - Verify all tests pass after implementation
  - Check constitutional compliance
- **Before completion**: Run full compliance validation and ensure 100% test pass rate

- Stop after each sub‑task and wait for the user's go-ahead, unless it is a parallel sub-task.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## Phase-Based Execution Workflow

### Phase Execution Strategy
1. **Parse task file** for phase boundaries and task dependencies
2. **Execute tasks within phases:**
   - Sequential phases (Phase 1 → Phase 2 → Phase 3)
   - Parallel tasks within same phase (marked with `[P]`)
3. **Phase validation** after each phase completion:
   - Run relevant test suites
   - Verify all tasks in phase are `[x]`
   - Check constitutional compliance if applicable

### Parallel Execution Example
```bash
# Phase 2.1: Database Setup (Parallel Tasks)
sed -i 's/- \[ \] T014/- [>] T014/' tasks-file.md  # Create User model
sed -i 's/- \[ \] T015/- [>] T015/' tasks-file.md  # Create Auth service  
sed -i 's/- \[ \] T016/- [>] T016/' tasks-file.md  # Create API routes

# Execute in parallel using Task tool
Task "database-admin" "Create User model with validation [Context: /tasks/context/T014_user_model.md]" &
Task "backend-architect" "Create Auth service [Context: /tasks/context/T015_auth_service.md]" &  
Task "api-documenter" "Create API routes [Context: /tasks/context/T016_api_routes.md]" &
wait

# Mark all as complete after verification
sed -i 's/- \[>\] T014/- [x] T014/' tasks-file.md
sed -i 's/- \[>\] T015/- [x] T015/' tasks-file.md  
sed -i 's/- \[>\] T016/- [x] T016/' tasks-file.md

# Phase validation
npm test
```

## AI Instructions

### Enhanced Concurrent Execution Protocol

When working with task lists, the AI must:

1. **State management:** Use atomic updates with `sed` commands for task state changes
2. **Parallel execution:** Execute `[P]` tasks concurrently within same phase using multiple Task tool invocations
3. **Context awareness:** Read and update context files for inter-agent communication
4. **Phase respect:** Complete all tasks in a phase before proceeding to next phase
5. **Resume capability:** Parse existing states to resume from interruption points
6. **Error handling:** Mark failed tasks with `[!]` and provide recovery guidance
7. **Validation:** Run tests and compliance checks after each phase
8. **Documentation:** Keep "Relevant Files" accurate and up to date
9. **TDD compliance:** CRITICAL - Never skip failed tests, use test-automator and relevant language subagents for test failures
10. **Simplicity:** Maintain DRY principle and avoid overcomplication

### Usage Examples

**Basic concurrent execution:**
```bash
# Execute multiple [P] tasks in parallel
Task "frontend-developer" "Create login component [Context: /tasks/context/T001_login.md]" &
Task "backend-architect" "Create auth API [Context: /tasks/context/T002_auth_api.md]" &
Task "database-admin" "Setup user schema [Context: /tasks/context/T003_user_schema.md]" &
wait
```

**State-aware resumption:**
```bash
# Check current task states before resuming
grep -E "\[(x|!|>| )\]" tasks-file.md
# Resume from first pending task
# Execute failed tasks marked with [!]
```

**Context file communication:**
```bash
# Read context from other agents before starting
cat /tasks/context/T001_shared_state.md
# Update context after completion
echo "## Agent: backend-architect\nCompleted API endpoint: /auth/login\nDatabase table: users" >> /tasks/context/T002_auth_api.md
```

**TDD enforcement example:**
```bash
# Phase 3.2: Contract Tests (TDD) - CRITICAL PHASE
sed -i 's/- \[ \] T005/- [>] T005/' tasks-file.md  # Contract test creation

# Execute test creation with test-automator
Task "test-automator" "Create failing contract test for user authentication [Context: /tasks/context/T005_auth_test.md]"

# MANDATORY: Verify test fails before proceeding
npm test 2>&1 | grep "FAIL.*auth" && echo "✓ Test failing correctly" || { echo "✗ BLOCKED: Test must fail first"; exit 1; }

sed -i 's/- \[>\] T005/- [x] T005/' tasks-file.md  # Mark test creation complete

# Only after ALL contract tests fail, proceed to implementation phase
```
