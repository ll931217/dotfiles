# CLAUDE.md

**Note**: This project uses [bd (beads)](https://github.com/steveyegge/beads) for issue tracking and [worktrunk](https://worktrunk.dev/) for git worktree management.

## Documentation Index

- **[WORKFLOW.md](WORKFLOW.md)** - Complete workflow guide for beads, worktrunk, and PRD development
- **[AGENTS.md](AGENTS.md)** - Reference for all custom AI agents
- **[COMMANDS.md](COMMANDS.md)** - Documentation for custom slash commands
- **[HOOKS_SETUP.md](HOOKS_SETUP.md)** - Hook system documentation

This file provides general guidance to Claude Code (claude.ai/code) when working with code.

- Code should be easy to read and understand.
- Keep the code as simple as possible. Avoid unnecessary complexity.
- Use meaningful names for variables, functions, etc. Names should reveal intent.
- Functions should be small and do one thing well. They should not exceed a few lines.
- Function names should describe the action being performed.
- Prefer fewer arguments in functions. Ideally, aim for no more than two or three.
- Only use comments when necessary, as they can become outdated. Instead, strive\
  to make the code self-explanatory.
- When comments are used, they should add useful information that is not readily\
  apparent from the code itself.
- Properly handle errors and exceptions to ensure the software's robustness.
- Use exceptions rather than error codes for handling errors.
- Consider security implications of the code. Implement security best practices\
  to protect against vulnerabilities and attacks.
- Always write correct, best practice, DRY principle (Dont Repeat Yourself), \
  bug free, fully functional and working code
- Leave NO todo’s, placeholders or missing pieces.
- Be concise Minimize any other prose.
- If you think there might not be a correct answer, you say so.
- If you do not know the answer, say so, instead of guessing.
- Follow the user’s requirements carefully & to the letter.
- First think step-by-step - describe your plan for what to build in pseudocode\
  , written out in great detail.
- Always create unit tests for new features, try to keep code coverage above \
  80%. Keep these tests simple and only test the most critical functionality.
- Commit code for fixes, refactors, minor and major fixes.
- Keep code change summaries inside a CHANGELOG.md file in the project's root directory.
- Always use Claude Code sub-agents for research before implementing.
- When in plan mode, always try to group tasks that can be processed in parallel together. When the user is satisfied and want you to implement it, try to work on as many tasks on the todo list as possible by delegating tasks to appropriate sub-agents
- Always use multiple sub-agents when doing research and forming a plan for code implementation
- We are mostly inside the company's internal network without access to the internet, unless using a proxy which only allows certain access mainly to github

## Context-Efficient Code Exploration

**Core Principle**: "做減法" — Provide *relevant* information, not *comprehensive* information. Minimize context usage through targeted search.

### Grep-First Strategy

**ALWAYS prefer Grep over Read for code discovery:**

1. **Find first, read later**: Use `Grep` to locate patterns, then `Read` with `offset`/`limit` for relevant sections only
2. **Priority-based searching**: Start narrow (specific pattern), expand only if needed
3. **Early termination**: Stop searching once you find what you need
4. **Batch operations**: Combine multiple independent searches in parallel

### Grep Tool Usage

| Parameter | Usage |
|-----------|-------|
| `output_mode: "files_with_matches"` | Find which files contain the pattern (default, lowest token cost) |
| `output_mode: "content"` | Get matching lines (use with context flags) |
| `output_mode: "count"` | Quick check of match frequency |
| `-C 5` / `-A 3` / `-B 3` | Context lines (usually 3-5 is sufficient) |
| `glob: "*.ts"` or `type: "py"` | Filter by file type (reduces search scope) |
| `head_limit: 20` | Limit results to prevent context overflow |

### Search Strategy by Task

| Task | Approach |
|------|----------|
| Find function/class | `Grep` pattern: `"(function\|def\|class)\s+Name"` with `-C 3` |
| Find usages | `Grep` pattern: `"functionName\("` with `output_mode: "content"` |
| Explore structure | `Grep` for exports/class definitions, NOT full file read |
| Debug errors | `Grep` for error message or stack trace pattern |

### Token Budget Guidelines

| Complexity | Target Context |
|------------|----------------|
| Simple lookup | < 500 tokens (grep with limited results) |
| Function understanding | < 1,500 tokens (grep + targeted read) |
| Module understanding | < 3,000 tokens (structure first, then details) |

### When Full File Read is Appropriate

- File is small (< 100 lines)
- Making edits requiring full context (imports, class hierarchy)
- Understanding a complete module after initial grep exploration

### Anti-Patterns

- ❌ Reading 500+ line files to find one function
- ❌ Using `Read` to search across multiple files
- ❌ Reading entire files when you only need a section
- ❌ Sequential file reads when parallel grep would work
- ✅ Grep → identify files → Read with offset/limit
- ✅ Use `head_limit` to cap grep results

## Universal Code Quality Principles

Apply these principles consistently across all languages and projects. Focus on intent, clarity, and maintainability.

### SOLID Principles (OOP Context)

Use these guidelines when working with object-oriented code:

- **Single Responsibility Principle**: Each class/module should have one reason to change. Split classes that handle multiple concerns.
- **Open/Closed Principle**: Design for extension without modification. Use interfaces, abstract classes, or strategy patterns for variability.
- **Liskov Substitution Principle**: Subtypes must be substitutable for base types. Don't violate parent class contracts in overrides.
- **Interface Segregation Principle**: Prefer small, focused interfaces over large ones. Clients shouldn't depend on methods they don't use.
- **Dependency Inversion Principle**: Depend on abstractions, not concretions. Use dependency injection for testability and flexibility.

### Clean Code Practices

Write code that reads like prose:

- **Naming**: Use verbs for functions (`saveUser`, `calculateTotal`) and nouns for classes (`UserService`, `Invoice`). Names should reveal intent without abbreviations. Use prefixes like `is/has/can` for booleans.
- **Function Structure**: Keep functions small (under 20 lines). Do one thing well. Use early returns to reduce nesting. Prefer pure functions when possible.
- **Arguments**: Aim for 0-2 arguments. Three or more signals the function does too much or needs an object parameter. Avoid flag arguments that change function behavior.
- **Comments**: Comment "why" not "what." Code should be self-documenting. Delete outdated comments immediately.
- **Magic Numbers/Strings**: Extract to named constants with descriptive names. No bare literals in logic.

### Modular Design

Build systems that are easy to understand and change:

- **High Cohesion**: Group related functionality together. Each module should have a clear, single purpose.
- **Low Coupling**: Minimize dependencies between modules. Use interfaces/protocols to decouple implementation from usage.
- **Composition Over Inheritance**: Prefer composing behavior from small objects over deep inheritance hierarchies.
- **Dependency Injection**: Pass dependencies via constructor/function parameters. Avoid global state and singletons.
- **Layered Architecture**: Separate concerns into distinct layers (presentation, business logic, data access). Dependencies point inward.
- **Law of Demeter**: Don't talk to strangers. Only call methods on immediate dependencies.

### Functional Programming (JavaScript/TypeScript)

Leverage FP concepts in JS/TS codebases:

- **Immutability**: Never modify existing objects/arrays. Use spread operators, `Object.freeze()`, or libraries like Immer.
- **Pure Functions**: Write functions that return output based only on input. No side effects (no I/O, no global state mutation).
- **Side Effects Isolation**: Contain side effects (network calls, file I/O, mutations) at system edges. Keep core logic pure.
- **Higher-Order Functions**: Use `map`, `filter`, `reduce` over for-loops. Chain operations for data transformations.
- **Avoid Shared State**: Pass data explicitly through function arguments. Design data flow clearly.

### Code Organization

Structure projects for clarity and scalability:

- **One Export Per File**: Major components/classes get their own file. Small utilities can be grouped.
- **Barrel Exports**: Use `index.ts`/`index.js` to re-export public APIs. Keep internal implementation private.
- **Import Order**: Group imports: 1) External libraries, 2) Internal modules, 3) Relative imports. Separate groups with blank lines.
- **Directory Layout**: Group by feature or layer. Common patterns: `src/components/`, `src/services/`, `src/utils/`, `src/types/`.
- **File Naming**: Use kebab-case for files (`user-service.ts`) or match the export name (`UserService.ts`). Be consistent.

### Refactoring Guidelines

Improve code structure without changing behavior:

- **Code Smells**: Watch for long functions, duplicate code, deep nesting, shotgun surgery (changes touch many files), and feature envy (methods using other objects more than their own).
- **When to Refactor**: Rule of three (first time, just do it; second time, wince; third time, refactor). Also before adding new features.
- **Refactoring Steps**: 1) Add tests covering existing behavior, 2) Make small changes, 3) Run tests after each change, 4) Commit frequently.
- **Safe Refactoring**: Extract methods/classes, rename for clarity, eliminate duplication, simplify conditionals, replace magic values with constants.
- **Don't Over-Abstract**: YAGNI (You Aren't Gonna Need It). Build for current requirements, not hypothetical future needs.

These principles apply universally. Adapt specifics to language idioms and project conventions.

## Available MCP Servers

The following are MCP servers that I have provided which you should use when needed:

- Context7 MCP Server: This is used to get documentation data for languages and \
  frameworks that we will use.
- Chrome DevTools MCP: Use this to test frontend implementation changes.

## Available Agent Skills

Use the following Claude Code Agent skills when you see fit:

- Document skills: Use this to create the appropriate documents based on user specification. The current document skills you have for this includes: docx, pdf, pptx, xlsx.
- Frontend Design: Use this when you need to create frontend web UIs.
- MCP Builder: Use this when the user wants to create their own custom MCP servers.
- Skill Creator: Use this when the user wants you to create a new Agent Skill.
- Webapp Testing: Use this when you are testing frontend web UI changes. This should be used with the Chrome DevTools MCP to further improve results.

## Memories

You MUST follow these user specified guidelines where necessary:

- Use beads tool to keep track of issues instead of markdown todos list, the `bd` command can provide much more context. See WORKFLOW.md for comprehensive beads documentation, or use `bd quickstart` for a quick rundown.
- Use worktrunk (`wt`) for git worktree management when working with parallel agents or isolated features. See WORKFLOW.md for worktrunk commands and patterns.
- Always use beads to keep track of context.
- Web frontend:
  - You can test changes with Chrome DevTools MCP
  - React: If data is passed down to multiple components, use react context instead
  - React: If there is too many handlers for a single state, use the reducer instead
  - React: Please keep react components compact and focused, do not overcomplicate a single react component
