# Tech Stack Selector - Quick Start

## Installation

The tech stack selector is part of the decision-engine skill. No additional installation required.

## Command Line Usage

### Basic Usage

```bash
# Auto-detect category from natural language
python3 scripts/tech_stack_selector.py /path/to/project "Need OAuth library for authentication"

# Specify category explicitly
python3 scripts/tech_stack_selector.py /path/to/project "Need database" --category database

# Pretty JSON output
python3 scripts/tech_stack_selector.py /path/to/project "Need backend framework" --output-format pretty
```

### Available Categories

- `authentication` - Auth libraries, OAuth, JWT
- `database` - SQL, NoSQL, caching
- `frontend_framework` - React, Vue, Svelte
- `backend_framework` - Express, FastAPI, Django, Flask

## Python API Usage

```python
from tech_stack_selector import TechStackSelector

# Initialize
selector = TechStackSelector("/path/to/project")

# Get recommendation (auto-detects category)
result = selector.select_tech_stack("Need authentication")

# Get recommendation for specific category
result = selector.select_tech_stack("Need database", category="database")

# Access results
decision = result["output"]["decision"]
rationale = result["output"]["rationale"]
confidence = result["output"]["confidence"]
alternatives = result["output"]["alternatives"]
score_breakdown = result["output"]["context"]["scoring_breakdown"]

print(f"Recommendation: {decision}")
print(f"Confidence: {confidence}")
print(f"Score: {score_breakdown['total']}/100")
print(f"Rationale: {rationale}")
print(f"Alternatives: {', '.join(alternatives)}")
```

## Example Output

```json
{
  "decision_type": "tech_stack",
  "input": "Need OAuth library for authentication",
  "category": "authentication",
  "output": {
    "decision": "Passport.js",
    "rationale": "Already in codebase; Mature ecosystem (10K+ stars/1M+ downloads); Perfect fit for requirements",
    "confidence": "high",
    "alternatives": ["Auth.js", "Auth0", "custom JWT"],
    "context": {
      "existing_dependencies": ["express", "passport", "pg"],
      "dependency_count": 3,
      "scoring_breakdown": {
        "existing_usage": 40,
        "maturity": 25,
        "community": 15,
        "fit": 20,
        "total": 100
      }
    }
  }
}
```

## Scoring Breakdown

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Existing Usage** | 0-40 | Already in codebase = 40, Compatible = 30, Standard = 10 |
| **Maturity** | 0-25 | Based on GitHub stars, downloads, maintenance |
| **Community** | 0-15 | Activity level, documentation quality |
| **Fit** | 0-20 | How well it matches requirements |
| **Total** | 0-100 | Sum of all criteria |

## Confidence Levels

- **High** (90-100): Clear winner, proceed confidently
- **Medium** (70-89): Good choice, monitor for issues
- **Low** (<70): Consider alternatives, may need reevaluation

## Running Tests

```bash
# Run all tests
python3 scripts/test_tech_stack_selector.py

# Run with verbose output
python3 scripts/test_tech_stack_selector.py -v
```

Expected: 23 tests, all passing

## Common Use Cases

### 1. Authentication Decision

```python
selector = TechStackSelector("/path/to/nodejs/project")
result = selector.select_tech_stack("Need OAuth")
# Returns Passport.js if already in package.json
```

### 2. Database Decision

```python
selector = TechStackSelector("/path/to/project")
result = selector.select_tech_stack("Need database for sessions", category="database")
# Recommends PostgreSQL if already using, or Redis for sessions
```

### 3. Framework Decision

```python
selector = TechStackSelector("/path/to/project")
result = selector.select_tech_stack("Need backend API")
# Recommends Express for Node.js, Django for Python, etc.
```

## Integration with Maestro

```python
# In Maestro orchestrator
from decision_engine.scripts.tech_stack_selector import TechStackSelector

def autonomous_tech_decision(project_path, requirement):
    selector = TechStackSelector(project_path)
    decision = selector.select_tech_stack(requirement)

    tech = decision["output"]["decision"]
    confidence = decision["output"]["confidence"]

    if confidence == "high":
        return tech  # Use automatically
    else:
        # Log for review but still use
        log_decision(decision)
        return tech
```

## Troubleshooting

### No Dependencies Found

If `dependency_count` is 0, check that:
- Project path is correct
- Dependency files exist (package.json, requirements.txt, etc.)
- Files are readable

### Category Not Detected

If category is wrong, use `--category` flag to specify explicitly:
```bash
python3 scripts/tech_stack_selector.py /path "Need something" --category authentication
```

### Low Confidence

Low confidence means no clear winner. Review:
- `all_options` to see all scored candidates
- `scoring_breakdown` to understand why
- `alternatives` for fallback options

## Support

For detailed documentation, see:
- `TECH_STACK_ALGORITHM.md` - Full algorithm documentation
- `SKILL.md` - Decision engine overview
- `references/tech-stack-rubric.md` - Detailed scoring criteria
