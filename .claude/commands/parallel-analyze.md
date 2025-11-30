---
description: Spawn multiple concurrent agents to collaboratively analyze problems and combine their findings
---

# Parallel Agent Analysis

## Usage
`/parallel-analyze <COUNT> <AGENT_TYPE> "<PROBLEM_DESCRIPTION>"`

## Parameters
- **COUNT**: Number of concurrent agents to spawn (1-20)
- **AGENT_TYPE**: The type of specialist agent to use (e.g., frontend-developer, security-auditor, database-optimizer)
- **PROBLEM_DESCRIPTION**: The specific problem or question you want analyzed

## Your Role
You are a coordination specialist that orchestrates multiple AI agents to collaboratively analyze complex problems. You spawn the specified number of agents in parallel, collect their findings, and synthesize a comprehensive response.

## Process

### 1. Validation Phase
First, validate the input parameters:
- Ensure COUNT is between 1 and 20
- Verify AGENT_TYPE exists in the available agents
- Confirm PROBLEM_DESCRIPTION is provided

### 2. Parallel Agent Execution
Launch all agents simultaneously using a single message with multiple Task tool calls:
- Each agent receives identical context about the problem
- All agents work independently and in parallel
- Wait for ALL agents to complete before proceeding

### 3. Result Synthesis
After collecting all agent responses:
- Identify common themes and patterns across responses
- Rank solutions/insights by frequency and consensus
- Highlight unique insights that only one agent identified
- Combine findings into a coherent, comprehensive analysis

### 4. Final Report Structure
Present results in this format:

```markdown
## Analysis Summary
[Brief overview of the problem and approach]

## Consensus Findings
[Issues/solutions identified by multiple agents, ranked by frequency]

## Unique Insights
[Notable findings mentioned by only one agent]

## Recommended Actions
[Prioritized list of actionable steps based on all agent input]

## Agent Breakdown
[Summary of what each agent contributed]
```

## Implementation

```markdown
I'll analyze "$ARGUMENTS" using $1 concurrent $2 agents.

**Validation:**
- Agent count: $1 (valid range: 1-20)
- Agent type: $2 (validating availability...)
- Problem: $ARGUMENTS (from position 3 onwards)

**Spawning $1 $2 agents in parallel to analyze:** $ARGUMENTS

[Execute parallel Task tool calls - one for each agent]

**Waiting for all agents to complete...**

[After all responses collected]

**Synthesizing findings from $1 agents:**

## Analysis Summary
The problem "$ARGUMENTS" was analyzed by $1 concurrent $2 agents.

## Consensus Findings
[Combine common themes, rank by frequency]

## Unique Insights
[Highlight singular findings]

## Recommended Actions
[Prioritized action items]

## Agent Breakdown
- Agent 1: [Key contribution]
- Agent 2: [Key contribution]
[etc.]
```

## Example Usage

### Frontend Performance Analysis
```
/parallel-analyze 8 frontend-developer "When the response from the [POST] fill_comparison and [POST] inventory_comparison endpoints gets too big, such as both having over 4500 items, then the webpage slows down to a crawl. Do you know why?"
```

### Security Vulnerability Assessment
```
/parallel-analyze 5 security-auditor "Review our authentication flow for potential security vulnerabilities"
```

### Database Performance Investigation
```
/parallel-analyze 3 database-optimizer "Our user table queries are running extremely slow with over 100k records"
```

### API Design Review
```
/parallel-analyze 4 backend-architect "Evaluate the scalability of our current microservices architecture"
```

## Error Handling

- **Invalid COUNT**: "Error: Agent count must be between 1 and 20"
- **Invalid AGENT_TYPE**: "Error: Agent type '$2' not found. Available agents: [list]"
- **Missing PROBLEM_DESCRIPTION**: "Error: Problem description is required"
- **Agent Failures**: Continue with successful responses, note failed agents in final report

## Notes

- Agents run truly in parallel using multiple Task tool calls in a single message
- All agents receive identical problem context
- Results are automatically deduplicated and synthesized
- Maximum 20 agents to prevent resource exhaustion
- Failed agents don't block the overall analysis