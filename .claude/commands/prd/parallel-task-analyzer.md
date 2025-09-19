# Parallel Task Analysis Utility

This utility provides the logic for analyzing sub-tasks and grouping them into conflict-free parallel execution groups.

## File Dependency Analysis Algorithm

### Step 1: Extract File Dependencies
For each sub-task, identify:
- **Create files:** New files that will be created
- **Modify files:** Existing files that will be modified  
- **Read files:** Files that will be read (less critical for conflict detection)

### Step 2: Build Conflict Matrix
Create a matrix showing which tasks have file conflicts:
- Tasks that modify the same file = CONFLICT (cannot run in parallel)
- Tasks that create files with the same name = CONFLICT  
- Tasks that modify different files = NO CONFLICT (can run in parallel)

### Step 3: Group Assignment Algorithm
```
1. Initialize empty groups: Group-A, Group-B, Group-C...
2. For each sub-task:
   a. Check if task can be added to any existing group (no file conflicts)
   b. If yes: Add to the first compatible group
   c. If no: Create new group for this task
3. Optimize: Try to merge groups that have no conflicts between them
```

## Conflict Detection Rules

### High Priority Conflicts (Must be sequential)
- Same source file modified by multiple tasks
- Same configuration file (package.json, tsconfig.json, etc.) modified
- Database schema files modified by multiple tasks
- Build/deployment configuration files

### Medium Priority Conflicts (Can sometimes be parallel)
- Different components in same directory (usually safe)
- Test files vs source files (usually safe to parallel)
- Different API endpoints (usually safe)

### Low Priority Conflicts (Usually safe to parallel)
- Different documentation files
- Different asset files (images, styles in different components)
- Different utility files

## Group Coordination Strategy

### Group Size Optimization
- **Ideal group size:** 2-4 tasks per group
- **Maximum group size:** 6 tasks per group
- **Reasoning:** Too many parallel tasks can overwhelm system resources and make debugging difficult

### Dependency-Based Sequencing
Some tasks must run sequentially even if they don't have file conflicts:
- Database schema creation → Data seeding
- Component creation → Component testing  
- API route creation → API documentation
- Infrastructure setup → Application deployment

## Context File Templates

### Individual Task Context File Template
```markdown
# Task Context: {task_number}_{task_description}

## Task Details
- **Task ID:** {task_number}
- **Group:** {group_id}  
- **Status:** [Not Started | In Progress | Completed | Blocked]
- **Assigned Agent:** {agent_type}

## File Manifest
### Files to Create
- `path/to/new/file1.ext` - Purpose description
- `path/to/new/file2.ext` - Purpose description

### Files to Modify  
- `path/to/existing/file1.ext` - Modification description
- `path/to/existing/file2.ext` - Modification description

### Files to Read
- `path/to/reference/file1.ext` - Why needed

## Progress Log
- `[Timestamp]` Started task
- `[Timestamp]` Created file1.ext  
- `[Timestamp]` Modified file2.ext
- `[Timestamp]` Task completed

## Blockers/Issues
- None / List any issues encountered

## Dependencies
- Must complete after: [list of task IDs]
- Required by: [list of task IDs that depend on this one]
```

### Group Coordination File Template
```markdown
# Group {group_id} Coordination

## Group Overview
- **Group ID:** {group_id}
- **Status:** [Pending | In Progress | Completed]
- **Start Time:** {timestamp}
- **Completion Time:** {timestamp}

## Tasks in Group
1. **{task_id}** - {brief_description} - Status: {status}
2. **{task_id}** - {brief_description} - Status: {status}
3. **{task_id}** - {brief_description} - Status: {status}

## File Usage Map
### Currently Being Modified
- `file1.ext` - Task {task_id} - Agent: {agent_type}
- `file2.ext` - Task {task_id} - Agent: {agent_type}

### Completed Modifications
- `file3.ext` - Task {task_id} - Completed at {timestamp}

### Planned Modifications
- `file4.ext` - Task {task_id} - Scheduled to start

## Inter-Group Dependencies
- **Depends on completion of:** Group-{id}, Group-{id}
- **Required by:** Group-{id}, Group-{id}

## Progress Summary
- Tasks completed: {x}/{total}
- Files modified: {x}/{total}
- Tests passing: {x}/{total}
- Ready for next group: [Yes/No]
```

## Implementation Guidelines

### For Task Generation (generate-tasks.md)
1. Analyze each sub-task to identify file dependencies
2. Use the conflict detection rules to build groups
3. Assign group IDs (Group-A, Group-B, etc.)
4. Generate context file paths for each task
5. Create group coordination file references

### For Task Processing (process-task-list.md)  
1. Before starting a group, create the group coordination file
2. Launch all tasks in the group simultaneously using Task tool
3. Monitor progress via context files
4. Wait for all tasks in group to complete before proceeding
5. Update group coordination file with final status

### Error Handling
- If a task fails, mark entire group as blocked
- Investigate file conflicts via context files
- Reschedule conflicting tasks to different groups
- Update task list with revised groupings