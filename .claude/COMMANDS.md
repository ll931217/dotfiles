# Custom Commands Reference

This directory contains custom slash commands for Claude Code, extending its functionality for specialized workflows.

---

## Table of Contents

1. [PRD Workflow Commands](#prd-workflow-commands)
2. [Git Commands](#git-commands)
3. [Tools & Utilities](#tools--utilities)

---

## PRD Workflow Commands

The PRD (Product Requirements Document) system provides a structured approach to requirements-driven development.

### `/flow:plan`

**Create a Product Requirements Document with auto-generated tasks**

**Features**:
- Validates required tools (git, bd, gwq/worktrunk)
- Detects and creates git worktrees as needed
- Gathers clarifying questions systematically
- Implements priority inference (P0-P4) from requirements
- Creates structured YAML frontmatter with git context
- Manages PRD review cycles with version control

**YAML Frontmatter Structure**:
```yaml
---
title: "Feature Name"
author: "author-name"
date: 2024-01-15
status: draft  # draft, review, approved, implemented
priority: 1  # 0-4 (P0 = urgent, P4 = low)
assignee: unassigned
prd_id: PRD-001
branch: feat/feature-name
related_issues: []
---
```

**Usage Example**:
```
/flow:plan
> I need to add user authentication with JWT tokens
```

**Process**:
1. Validates environment and tools
2. Detects or creates appropriate worktree
3. Asks clarifying questions about requirements
4. Infers priority from requirement descriptions
5. Generates PRD with structured frontmatter
6. Creates in `docs/prd/` directory

**Priority Inference**:
- **P0** (Critical): Keywords like "urgent", "blocking", "security", "data loss"
- **P1** (High): Keywords like "important", "priority", "user-facing"
- **P2** (Medium): Default for standard features
- **P3** (Low): Keywords like "nice-to-have", "optional"
- **P4** (Backlog): Keywords like "maybe", "someday", "consider"

### `/flow:implement`

**Implement an approved PRD**

**Features**:
- Links approved PRD to implementation phase
- Tracks progress through beads integration
- Manages task dependencies
- Creates implementation tasks from requirements

**Usage Example**:
```
/flow:implement PRD-001
```

**Process**:
1. Validates PRD exists and is approved
2. Loads PRD requirements and dependencies
3. Creates implementation tasks in beads
4. Sets up task dependencies
5. Begins implementation workflow

### `/flow:generate-tasks`

**Generate implementation tasks from an approved PRD**

**Features**:
- Parses PRD requirements into actionable tasks
- Creates beads issues for each task
- Sets up task dependencies
- Assigns appropriate priorities

**Usage Example**:
```
/flow:generate-tasks PRD-001
```

**Generated Task Types**:
- **Setup tasks**: Environment preparation, dependencies
- **Core tasks**: Main feature implementation
- **Testing tasks**: Unit tests, integration tests
- **Documentation tasks**: Code comments, API docs

### `/flow:summary`

**Show PRD status and history**

**Features**:
- Lists all PRDs with their status
- Shows related tasks and implementation progress
- Displays PRD history and versions
- Provides quick status overview

**Usage Example**:
```
/flow:summary
```

**Output Example**:
```
## Active PRDs

### PRD-001: User Authentication
- **Status**: approved
- **Priority**: P0
- **Assignee**: agent-1
- **Branch**: feat/user-auth
- **Tasks**: 5 total, 2 in progress, 1 completed

### PRD-002: Dashboard Redesign
- **Status**: review
- **Priority**: P1
- **Assignee**: unassigned
- **Tasks**: Not yet generated
```

---

## Git Commands

### `/gh:create-commit`

**Create a git commit with standard format**

**Features**:
- Streamlines commit creation process
- Integrates with development workflow
- Supports conventional commit format
- Links to beads issues

**Usage Example**:
```
/gh:create-commit
> Add user login functionality
```

**Commit Format**:
```
feat: add user login functionality (bd-abc)

- Implement JWT authentication
- Add login form component
- Create auth middleware

Refs: bd-abc
```

**Supported Commit Types**:
- `feat`: New feature
- `fix`: Bug fix
- `chore`: Maintenance task
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `perf`: Performance improvements

---

## Tools & Utilities

### `/tools:debug`

**Debugging assistance tool**

**Features**:
- Error analysis and diagnosis
- Stack trace interpretation
- Bug reproduction guidance
- Solution suggestions

**Usage Example**:
```
/tools:debug
> I'm getting a null pointer exception in the auth service
```

### `/tools:parallel-analyze`

**Spawn multiple concurrent agents for collaborative analysis**

**Features**:
- Runs multiple specialized agents simultaneously
- Combines findings from different perspectives
- Useful for complex problems requiring multiple domains
- Reduces analysis time through parallelization

**Usage Example**:
```
/tools:parallel-analyze
> Analyze this codebase for security and performance issues
```

**Agent Combinations**:
- `security-auditor` + `performance-engineer`: Security and performance review
- `code-reviewer` + `architect-reviewer`: Code quality and architecture review
- `frontend-developer` + `backend-architect`: Full-stack analysis

### `/tools:refractor`

**Refactor code following best practices and design patterns**

**Features**:
- Applies SOLID principles
- Follows DRY (Don't Repeat Yourself)
- Improves code readability
- Maintains functionality

**Usage Example**:
```
/tools:refractor
> Refactor this function to be more maintainable
```

**Refactoring Principles**:
- **Single Responsibility**: Each function does one thing
- **DRY**: Eliminate duplicate code
- **Meaningful Names**: Variables and functions reveal intent
- **Small Functions**: Functions should be short and focused
- **Few Arguments**: Limit to 2-3 parameters when possible

### `/tools:ultrathink`

**Deep thinking mode for complex problems**

**Features**:
- Extended reasoning chain
- Multi-step problem analysis
- Hypothesis generation and verification
- Comprehensive solution exploration

**Usage Example**:
```
/tools:ultrathink
> Design a scalable architecture for a multi-tenant SaaS application
```

**When to Use**:
- Complex architectural decisions
- Multi-faceted problems
- Requirements with many constraints
- Problems needing thorough analysis

---

## Command Development

### Creating Custom Commands

To add a new custom command:

1. **Create directory structure**: `commands/category/command-name.md`
2. **Add command metadata**:
   ```yaml
   ---
   name: "my-command"
   description: "What this command does"
   ---
   ```
3. **Implement command logic** with clear instructions
4. **Test command** before regular use

### Command Best Practices

- **Clear descriptions**: Users should understand what the command does
- **Validation**: Check required tools and environment
- **Error handling**: Provide helpful error messages
- **Integration**: Use existing tools (beads, worktrunk, git)
- **Documentation**: Update this reference when adding commands

### Example Command Template

```markdown
---
name: "my-command"
description: "Brief description of what this command does"
---

# My Custom Command

## Purpose
Explain what this command accomplishes

## Prerequisites
- Tool 1: version X or higher
- Tool 2: configured and available

## Usage
```
/my-command
> Your input here
```

## Process
1. Validate environment
2. Perform step 1
3. Perform step 2
4. Return results

## Output Format
Describe what the command returns

## Error Handling
List common errors and solutions
```

---

## Command Integration

### With Beads

Commands can integrate with beads for task tracking:

```bash
# Create task from command
bd create "Task from command" -p 1

# Update task status
bd update <id> --status in_progress

# Close task
bd close <id> --reason "Completed via /my-command"
```

### With Worktrunk

Commands can use worktrees for isolation:

```bash
# Create worktree for command
wt switch -c feat/my-command-work

# Run command in isolated environment
# ...

# Merge when done
wt merge
```

### With Git Hooks

Commands can trigger git hooks:

```bash
# Pre-commit validation
# Post-merge notifications
# Pre-push checks
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/flow:plan` | Create PRD with tasks |
| `/flow:implement` | Implement approved PRD |
| `/flow:generate-tasks` | Generate tasks from PRD |
| `/flow:summary` | Show PRD status |
| `/gh:create-commit` | Create git commit |
| `/tools:debug` | Debugging assistance |
| `/tools:parallel-analyze` | Multi-agent analysis |
| `/tools:refractor` | Refactor code |
| `/tools:ultrathink` | Deep thinking mode |

---

## See Also

- [WORKFLOW.md](WORKFLOW.md) - Complete workflow guide
- [AGENTS.md](AGENTS.md) - Custom agents reference
- [CLAUDE.md](CLAUDE.md) - Global project guidelines
