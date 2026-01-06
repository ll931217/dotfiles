# AskUserQuestion Templates

## Overview

This document contains common AskUserQuestion templates used throughout the flow commands. Copy and adapt these templates for specific contexts.

## Template Guidelines

- **header**: Short label (max 12 chars) displayed as a chip/tag
- **question**: Clear question text ending with a question mark
- **options**: 2-4 options with concise labels and helpful descriptions
- **multiSelect**: Set to `true` when multiple options can apply

The tool automatically provides an "Other" option for custom input.

---

## Worktree Selection Prompt

**Used by:** `/flow:plan`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "PRDs work best in isolated worktrees for better branch/feature management. What would you like to do?",
      header: "Worktree",
      options: [
        {
          label: "Create worktree",
          description: "Create a new git worktree and continue PRD planning there (recommended)"
        },
        {
          label: "Continue without worktree",
          description: "Proceed with PRD planning in the current directory"
        },
        {
          label: "Exit",
          description: "Exit the PRD planning process"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## PRD Action Prompt

**Used by:** `/flow:generate-tasks`, `/flow:cleanup`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "No PRD found matching current context (branch: [branch], worktree: [worktree]). Available PRDs: [list]. What would you like to do?",
      header: "PRD Action",
      options: [
        {
          label: "Create new PRD",
          description: "Run /flow:plan to create a new PRD for this context"
        },
        {
          label: "Select existing PRD",
          description: "Manually select one of the available PRDs"
        },
        {
          label: "Exit",
          description: "Exit the process"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## PRD Status Warning

**Used by:** `/flow:implement`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "PRD status is \"draft\" - this PRD has not been approved yet. What would you like to do?",
      header: "PRD Status",
      options: [
        {
          label: "Continue anyway",
          description: "Proceed with implementation despite draft status"
        },
        {
          label: "Run /flow:generate-tasks",
          description: "Generate tasks and approve the PRD first"
        },
        {
          label: "Exit",
          description: "Exit the implementation process"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## PRD Approval Workflow

**Used by:** `/flow:plan`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "Does the PRD summary above meet your requirements?",
      header: "Approval",
      options: [
        {
          label: "Yes, approve",
          description: "Approve PRD and proceed to task generation"
        },
        {
          label: "Review full PRD",
          description: "Open the complete PRD file for detailed review"
        },
        {
          label: "No, revise",
          description: "Restart from clarifying questions"
        },
        {
          label: "Changes needed",
          description: "Collect feedback and revise"
        }
      ],
      multiSelect: false
    }
  ]
})
```

**Response handling:**
- **"Yes, approve"**: Update PRD status from `draft` to `approved`, add changelog entry, proceed to task generation
- **"Review full PRD"**: Display full PRD path, ask if summary should be re-displayed
- **"No, revise"**: Restart from clarifying questions
- **"Changes needed"**: Collect feedback, increment version, update PRD, repeat approval cycle

---

## Worktree Cleanup Prompt

**Used by:** `/flow:cleanup`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "Worktree detected: [worktree-name]. Merge to [target-branch] and cleanup? This will merge the branch, remove the worktree, and delete the feature branch.",
      header: "Worktree Cleanup",
      options: [
        {
          label: "Merge and cleanup worktree",
          description: "Merge branch to target, remove worktree, and delete feature branch"
        },
        {
          label: "Skip worktree cleanup",
          description: "Only create summary commit, leave worktree intact for manual cleanup"
        },
        {
          label: "Exit",
          description: "Abort cleanup to handle worktree merge manually"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## Cleanup Options (Incomplete Tasks)

**Used by:** `/flow:cleanup`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "Not all tasks are complete yet. Open/In-Progress Issues: [list]. What would you like to do?",
      header: "Cleanup",
      options: [
        {
          label: "Continue anyway",
          description: "Cleanup only completed tasks"
        },
        {
          label: "Exit",
          description: "Complete remaining tasks first"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## Task Generation Update Options

**Used by:** `/flow:generate-tasks`

```javascript
AskUserQuestion({
  questions: [
    {
      question: "Found existing tasks for this PRD. Options:",
      header: "Task Update",
      options: [
        {
          label: "Review and update existing",
          description: "Keep completed tasks, update pending ones"
        },
        {
          label: "Regenerate all",
          description: "Archive existing, create new from scratch"
        },
        {
          label: "Show diff",
          description: "Show PRD changes to understand what needs updating"
        },
        {
          label: "Cancel",
          description: "Cancel task generation"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## PRD Regeneration Prompt

**Used by:** `/flow:plan` (after PRD update)

```javascript
AskUserQuestion({
  questions: [
    {
      question: "Would you like to run /flow:generate-tasks now to create new tasks from the updated PRD?",
      header: "Next Step",
      options: [
        {
          label: "Yes",
          description: "Generate tasks from the updated PRD"
        },
        {
          label: "No",
          description: "Skip task generation for now"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## Clarification Request Template

**Used by:** `/flow:implement` (when encountering ambiguous requirements)

```javascript
AskUserQuestion({
  questions: [
    {
      question: "[Specific question about ambiguous requirement, edge case, or implementation choice]",
      header: "Clarification",
      options: [
        {
          label: "[Option 1]",
          description: "[Clear description of approach 1]"
        },
        {
          label: "[Option 2]",
          description: "[Clear description of approach 2]"
        },
        {
          label: "[Option 3]",
          description: "[Clear description of approach 3]"
        }
      ],
      multiSelect: false
    }
  ]
})
```

**Example:**

```javascript
AskUserQuestion({
  questions: [
    {
      question: "The PRD specifies 'users can upload files' but doesn't define the maximum file size or allowed file types. Which approach should I use?",
      header: "File Upload",
      options: [
        {
          label: "10MB limit, images only",
          description: "Restrict to jpg, png, gif formats with 10MB size limit"
        },
        {
          label: "50MB limit, documents",
          description: "Allow common documents (pdf, doc, images) with 50MB limit"
        },
        {
          label: "No limit, any type",
          description: "Allow any file type with no size restrictions"
        }
      ],
      multiSelect: false
    }
  ]
})
```

---

## Usage Notes

1. **Always include "Other" option**: The AskUserQuestion tool automatically provides this, so don't include it manually
2. **Keep labels concise**: Max 1-5 words per label
3. **Descriptive descriptions**: Each description should clarify the outcome
4. **Multi-select for multiple valid options**: Use `multiSelect: true` when multiple options can apply
5. **Header as chip/tag**: Keep headers short (max 12 characters)
