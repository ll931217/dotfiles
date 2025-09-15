# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code.

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
- Use TDD (Test driven development), first create tests on what you expect the\
  code to do, and create code to pass those tests.
- Commit code for fixes, refactors, minor and major fixes.
- Keep code change summaries inside a CHANGELOG.md file in the project's root directory.
- Always use Claude Code sub-agents for research before implementing.
- When in plan mode, always try to group tasks that can be processed in parallel together. When the user is satisfied and want you to implement it, try to work on as many tasks on the todo list as possible by delegating tasks to appropriate sub-agents

## MCP Servers available

The following are MCP servers that I have provided which you should use when needed:

- Context7 MCP Server: This is used to get documentation data for languages and \
  frameworks that we will use.
