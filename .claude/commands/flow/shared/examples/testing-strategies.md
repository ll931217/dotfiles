# Testing Strategy Examples

## Overview

Concrete examples showing the three testing strategy approaches available in the flow system.

---

## Sequential Testing (DEFAULT)

**When to Use:** Most projects (default approach unless PRD explicitly specifies otherwise)

**How it Works:**
- Testing Strategy epic is created and blocks on ALL implementation epics
- Implementation epics complete first, then testing begins
- Simple, straightforward dependency management

### Concrete Example

**Epic Structure:**

```
Epic: Core Authentication Architecture (proj-auth-core)
├── Define database schema
├── Create base services
└── Setup authentication middleware

Epic: Authentication Endpoints (proj-auth-api)
├── POST /auth/login
├── POST /auth/register
└── POST /auth/refresh

Epic: Testing Strategy (proj-auth-test) [blocks: proj-auth-core, proj-auth-api]
├── Write unit tests
├── Write integration tests
└── Write E2E tests
```

**Result:** Testing epic will NOT appear as ready until both implementation epics are complete.

**Ready Task Sequence:**

```
Phase 1: Implementation
├─ Ready: Define database schema
├─ Ready: Create base services
└─ Ready: Setup authentication middleware

[After proj-auth-core complete]

Phase 2: Implementation continues
├─ Ready: POST /auth/login
├─ Ready: POST /auth/register
└─ Ready: POST /auth/refresh

[After all implementation complete]

Phase 3: Testing (now unblocked)
├─ Ready: Write unit tests
├─ Ready: Write integration tests
└─ Ready: Write E2E tests
```

### When to Choose Sequential Testing

- **Most projects** - This is the default
- **Complex features** - Where implementation must be complete before testing
- **Team preference** - When team prefers to implement then test
- **Clear requirements** - When the feature is well-understood

---

## Incremental Testing (TDD Approach)

**When to Use:** PRD explicitly requests test-driven development or wants tests written alongside implementation

**How it Works:**
- For each implementation task, create a corresponding test task
- Use `related` dependencies (not blocking) between implementation and test pairs
- Implementation and its tests can be worked on in parallel or sequentially

### Concrete Example

**Epic Structure:**

```
Epic: Authentication Endpoints (proj-auth-api)
├── Implement login endpoint [parent-child]
│   └── Write tests for login endpoint [parent-child] [related: login endpoint]
├── Implement registration endpoint [parent-child]
│   └── Write tests for registration endpoint [parent-child] [related: registration endpoint]
└── Implement refresh endpoint [parent-child]
    └── Write tests for refresh endpoint [parent-child] [related: refresh endpoint]
```

**Result:** Implementation and test tasks appear together in ready list. Developer can choose to implement first, test first, or work on them in parallel.

**Ready Task Sequence:**

```
All tasks appear in ready list simultaneously:

├─ Ready: Implement login endpoint
├─ Ready: Write tests for login endpoint [related to login]
├─ Ready: Implement registration endpoint
├─ Ready: Write tests for registration endpoint [related to registration]
├─ Ready: Implement refresh endpoint
└─ Ready: Write tests for refresh endpoint [related to refresh]
```

**TDD Workflow:**

```
1. Write test first (Red)
   ↓
2. Implement feature (Green)
   ↓
3. Refactor (Refactor)
   ↓
4. Move to next task
```

### When to Choose Incremental Testing

- **TDD workflow** - When team practices test-driven development
- **PRD explicitly requests** - When requirements mention TDD
- "Follow TDD approach"
- "Write tests alongside implementation"
- "Test-driven development"

---

## Parallel Testing

**When to Use:** Very simple features, fast iteration needed, PRD explicitly requests minimal testing overhead

**How it Works:**
- No dependencies between testing and implementation
- Both can be worked on immediately
- Fastest iteration, highest risk of integration issues

### Concrete Example

**Epic Structure:**

```
Epic: Simple UI Component (proj-ui-button)
├── Implement button component [parent-child]
└── Write tests for button component [parent-child]
```

**Result:** No blocking dependencies - both tasks appear in ready list immediately. Developer can work on them in any order.

**Ready Task Sequence:**

```
Both tasks ready immediately:

├─ Ready: Implement button component
└─ Ready: Write tests for button component
```

**Potential Issues:**
- Risk of integration issues if implementation and test drift apart
- No guarantee tests will pass when implementation is done
- Requires discipline to keep tests and implementation in sync

### When to Choose Parallel Testing

- **Very simple features** - Low complexity, low risk
- **Fast iteration** - When speed is more important than comprehensive testing
- **PRD explicitly requests** - When requirements mention minimal testing overhead
- "Fast iteration needed"
- "Minimal testing overhead"
- "Simple feature"

---

## Decision Matrix

| Approach | When to Use | Dependency Pattern | Ready Tasks Behavior |
|----------|-------------|-------------------|---------------------|
| **Sequential testing** | **DEFAULT** - most projects | Testing epic `blocks` on all implementation epics | Implementation tasks appear first, then testing tasks after all implementations complete |
| **Incremental testing** | TDD workflow, PRD explicitly requests | `related` dependencies between impl + test pairs | Implementation and test tasks appear together |
| **Parallel testing** | Very simple features, fast iteration | No dependencies between testing and implementation | All tasks appear immediately |

---

## Default Behavior

**Use Sequential testing unless the PRD explicitly specifies otherwise.**

When the PRD includes statements like:

- "Follow TDD approach"
- "Write tests alongside implementation"
- "Test-driven development"

Then use **Incremental Testing** approach with `related` dependencies.

Otherwise, default to **Sequential Testing** with blocking dependencies.

---

## Testing Strategy in PRD

The PRD should specify the testing approach in the **Functional Requirements** section:

```markdown
### Functional Requirements

**Testing Approach:** Incremental (TDD)

1. The system shall allow users to authenticate with email/password
   - Tests written before implementation
   - Each feature paired with corresponding test
2. ...
```

Or explicitly state in the **Testing Strategy** section:

```markdown
## Testing Strategy

**Approach:** Sequential

Testing will be performed after all implementation is complete:
1. Unit tests after each epic is complete
2. Integration tests after all epics are complete
3. E2E tests before cleanup
```

---

## Epic Dependency Examples

### Sequential Testing Dependencies

```bash
# Using beads command line
bd add-depends-on proj-auth-test proj-auth-core
bd add-depends-on proj-auth-test proj-auth-api

# Result: proj-auth-test is blocked by both implementation epics
```

### Incremental Testing Dependencies

```bash
# Using related dependencies (non-blocking)
bd add-related proj-auth-1-test proj-auth-1-impl
bd add-related proj-auth-2-test proj-auth-2-impl

# Result: Test tasks reference implementation tasks, but don't block
```

### Parallel Testing Dependencies

```bash
# No dependencies needed
# Both tasks are immediately ready

# Result: No blocking dependencies - both tasks appear immediately
```
