# TDD (Test-Driven Development) Principles

## Overview

These TDD principles enforce a strict test-first workflow where:
1. **Tests are written BEFORE implementation** - This ensures tests exist and fail (RED) initially
2. **Tests MUST pass before continuing** - Implementation proceeds only when tests pass (GREEN)
3. **ALL tests MUST pass** - No cleanup or merge allowed until all tests pass

## Red/Green Status Convention

- 🔴 **RED (FAIL)**: Tests failing, cannot proceed
- 🟢 **PASS**: Tests passing, can proceed
- **Status Display**: When displaying task status, always include test status with color indicators

## Workflow

### Phase 1: PRD Planning (`/flow:plan`)

**Test Creation Step (New in Phase 5):**

When generating PRD with clarifying questions, add a test creation step:

```
**5.5. Generate tests** - Create failing tests for each requirement before implementation

**TDD enforcement:** This step MUST precede "Get approval" step to ensure tests exist before any implementation begins
```

### Phase 2: Task Generation (`/flow:generate-tasks`)

**Test-First Priority in Task Structure:**

For each epic/sub-issue generated, include test tasks BEFORE implementation tasks:

```markdown
## Task: [Implementation Task Title]
### Agent Assignment
- **Primary Subagent:** [subagent type]
- **Fallback Agents:** [alternative agents]
- **Applicable Skills:** [relevant skills]

### Dependencies
- **Test for [Feature]:** This task MUST be completed before [Implementation Task]
- Type: `blocks` dependency (blocking)
- **Reason:** "TDD requirement: Tests must exist and pass before implementation"

### Task: [Test Task Title]
### Agent Assignment
- **Primary Subagent:** `test-automator`
- **Fallback Agents:** `debugger` (if tests fail)

### Relevant Files
| File | Lines | Purpose |
|------|-------|---------|
| `path/to/test.ts` | 1-100 | Test file for [Feature] |
```

**Implementation Pattern:**
- Test task creates failing test
- Implementation task has blocking dependency on test task
- This ensures test exists first and fails initially
- Implementation proceeds only after tests pass

### Phase 3: Implementation (`/flow:implement`)

**TDD Cycle Enforcement:**

1. **Before Implementation Task**:
   ```
   AI checks if corresponding test task exists
   If NO test task exists:
     - 🚨 Error: "No tests found for [Feature]! Creating failing tests first..."
     - Create failing test task with high priority
   - DO NOT proceed to implementation until test is written
   ```

2. **During Implementation**:
   ```
   Run tests immediately after implementation
   If tests fail (RED):
     - 🚨 STOP implementation
     - 🐛 Fix implementation until tests pass
     - DO NOT mark implementation task as complete
     - Use Ralph loops or iterative development
   If tests pass (GREEN):
     - ✅ Mark test task as complete
     - ✅ Mark implementation task as complete
     - Proceed to next task
   ```

3. **After Implementation Task**:
   ```
   Run full test suite
   If ALL tests pass:
     - ✅ Mark implementation task complete
     - ✅ Mark corresponding test task complete
   Else:
     - 🔴 Mark implementation task as incomplete (tests blocking)
     - 🚨 Do NOT proceed to next implementation task
   ```

### Phase 4: Cleanup (`/flow:cleanup`)

**Test Verification Gate (MANDATORY):**

Before allowing merge or cleanup, verify ALL tests pass:

```bash
# Check test status for all PRD tasks
bd list --format="Title,Status" | grep -i "task.*test\|Status:"
```

**Test Status Display Convention:**
- 🔴 **Test task INCOMPLETE** (status: `open` or `in_progress`)
- 🟢 **Test task PENDING** (status: `pending`)
- ✅ **Test task COMPLETE** (status: `closed`)

**Action if tests not passing:**
- Display summary with failing tests
- Ask user: "❌ Tests are failing. Fix before merge?"
  - Options: "Fix and retest", "Proceed anyway (risky)", "Exit to fix manually"

**Action if all tests pass:**
- Display summary with all green indicators
- Proceed with merge/cleanup

```

## Benefits

1. **Quality Assurance**: Tests guarantee implementation matches requirements
2. **Fail Fast**: Issues caught early, before code accumulation
3. **Documentation**: Tests serve as living documentation of expected behavior
4. **Safety**: No broken features deployed without tests

## Examples

### Example Workflow (TDD)

```
Epic: User Authentication System
├─ Task: Define user schema [P1]
├─ Task: Write tests for schema [P1] [blocks by: Define user schema]
├─ Task: Implement user schema [P2] [blocks by: Write tests for schema]
│   └── Task: Run full test suite [blocks by both test tasks]
└── Task: Mark both test tasks complete

Result:
- Tests fail initially (expected) ✅
- Schema implementation passes tests ✅
- All tests passing ✅
```

## Testing Approaches Comparison

| Approach | Test Creation Order | Dependency Pattern | When to Use |
|---------|-----------------|-------------------|----------|
| **TDD** | **Before implementation** | Tests block implementation | Quality-first | Complex features |
| **Sequential** | **After all implementation** | Tests validate implementation | Standard features | Simple features |
| **Parallel** | Tests run concurrently | No dependencies | Fast iteration | Simple prototypes |

**Default Behavior:** Use **TDD** approach unless PRD explicitly specifies otherwise

## Notes

- **Critical Quality Gate**: Tests failing = STOP implementation. No exceptions.
- **Progressive Disclosure**: Show test status at each checkpoint for transparency
- **Ralph Loops**: For tasks requiring iteration until success, use automated test cycles
- **Coverage Target**: Aim for 80%+ test coverage, not 100% (maintains momentum)
