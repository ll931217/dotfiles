# Beads Installation Warning Template

## Overview

Beads (`bd`) is an optional but recommended tool for persistent task tracking. This warning explains the benefits and provides installation instructions.

## Warning Text

⚠️ **Warning about beads (bd):**

Without beads installed, task context may be lost between sessions. Beads provides:

- **Persistent task storage** across sessions
- **Dependency tracking** between tasks
- **Better visibility** into progress and blockers
- **Integration with PRD frontmatter** for traceability

Consider installing beads for the best experience, especially for larger features with many tasks.

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/steveyeggie/beads/main/scripts/install.sh | bash
```

## Fallback Behavior

If beads is not installed, the AI will use the internal TodoWrite tool for task tracking.

**Limitations without beads:**
- Task context may be lost between sessions
- No persistent dependency tracking
- Manual verification may be needed after context compaction
- Limited task state visibility

## Tool Comparison

| Feature | Beads (bd) | TodoWrite (Fallback) |
|---------|------------|---------------------|
| Persistent storage | ✅ Yes | ❌ No (session-based) |
| Dependency tracking | ✅ Full | ❌ Basic |
| Ready task detection | ✅ Automatic | ❌ Manual |
| PRD integration | ✅ Native | ⚠️ Manual |
| Database | ✅ SQLite | ❌ In-memory |

## Usage in Flow Commands

This warning is displayed in:
- `/flow:plan` - Before PRD creation
- `/flow:generate-tasks` - Before task generation
- `/flow:implement` - Before implementation
- `/flow:cleanup` - Before cleanup

## Check Command

```bash
# Check if beads is installed
which bd

# If installed, verify it works
bd show --help
```

## Initialization

If beads is installed but not initialized:

```bash
# Initialize beads in current repository
bd init

# This creates the .beads/ directory and database
```
