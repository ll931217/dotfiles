# Tech Stack Selection Algorithm

Autonomous technology stack selection for the Maestro orchestrator.

## Overview

The tech stack selection algorithm analyzes a codebase and recommends technologies using a weighted scoring system. It integrates dependency scanning, pattern detection, and a knowledge base of technology options to make autonomous decisions.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   TechStackSelector                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐    ┌────────────────────┐         │
│  │  Dependency     │───▶│  Pattern           │         │
│  │  Scanner        │    │  Detector          │         │
│  └─────────────────┘    └────────────────────┘         │
│         │                        │                       │
│         └────────────┬───────────┘                       │
│                      ▼                                   │
│         ┌─────────────────────────────┐                 │
│         │  Tech Knowledge Base        │                 │
│         │  - Scoring rubric           │                 │
│         │  - Tech options             │                 │
│         │  - Detection patterns       │                 │
│         └─────────────────────────────┘                 │
│                      │                                   │
│                      ▼                                   │
│         ┌─────────────────────────────┐                 │
│         │  Scoring Engine             │                 │
│         │  - Existing usage (40%)     │                 │
│         │  - Maturity (25%)           │                 │
│         │  - Community (15%)          │                 │
│         │  - Fit (20%)                │                 │
│         └─────────────────────────────┘                 │
│                      │                                   │
│                      ▼                                   │
│         ┌─────────────────────────────┐                 │
│         │  Decision Output            │                 │
│         │  - Recommendation           │                 │
│         │  - Rationale                │                 │
│         │  - Confidence               │                 │
│         │  - Alternatives             │                 │
│         └─────────────────────────────┘                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Dependency Scanner (`analyze_dependencies.py`)

Scans the project for existing dependency files:
- **Node.js**: package.json, yarn.lock
- **Python**: requirements.txt, pyproject.toml
- **Go**: go.mod
- **Ruby**: Gemfile
- **Java**: pom.xml, build.gradle
- **Rust**: Cargo.toml

Returns a dictionary of installed packages with versions.

### 2. Pattern Detector (`detect_patterns.py`)

Uses grep to search the codebase for architectural patterns:
- Middleware patterns
- Service layers
- Repository patterns
- Factory patterns
- Singleton patterns
- Observer patterns
- Strategy patterns
- Decorator patterns

Returns pattern counts by category.

### 3. Tech Knowledge Base

Built-in knowledge base with predefined scoring for:

#### Categories:
- **Authentication**: Passport.js, Auth.js, Auth0, custom JWT
- **Database**: PostgreSQL, MySQL, MongoDB, Redis, SQLite
- **Frontend Frameworks**: React, Vue, Svelte
- **Backend Frameworks**: Express, FastAPI, Django, Flask

Each technology entry includes:
- **Maturity score** (0-25): Based on GitHub stars, downloads, maintenance
- **Community score** (0-15): Based on activity, documentation
- **Fit score** (0-20): How well it matches typical requirements
- **Detection patterns**: Keywords to find in dependencies/code
- **Ecosystem**: Language/ecosystem compatibility
- **Alternatives**: List of substitute options

### 4. Scoring System

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Existing Usage** | 40% | Already in codebase = 40 points |
| **Maturity** | 25% | GitHub stars, downloads, updates |
| **Community** | 15% | Activity, documentation quality |
| **Fit** | 20% | Matches specific requirements |

**Total Score**: 0-100 points

### 5. Confidence Levels

- **High** (90+ score): Clear winner, proceed confidently
- **Medium** (70-89 score): Good choice, monitor for issues
- **Low** (<70 score): Consider alternatives

## Usage

### Command Line

```bash
# Basic usage - auto-detect category
python3 scripts/tech_stack_selector.py /path/to/project "Need OAuth library for authentication"

# Specify category explicitly
python3 scripts/tech_stack_selector.py /path/to/project "Need database" --category database

# Pretty output
python3 scripts/tech_stack_selector.py /path/to/project "Need backend framework" --output-format pretty
```

### Python API

```python
from tech_stack_selector import TechStackSelector

# Initialize with project path
selector = TechStackSelector("/path/to/project")

# Get recommendation
result = selector.select_tech_stack("Need authentication")

# Access decision
decision = result["output"]["decision"]
rationale = result["output"]["rationale"]
confidence = result["output"]["confidence"]
alternatives = result["output"]["alternatives"]
```

## Output Schema

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
      "detected_patterns": [],
      "scoring_breakdown": {
        "existing_usage": 40,
        "maturity": 25,
        "community": 15,
        "fit": 20,
        "total": 100
      }
    },
    "all_options": [
      {
        "name": "Passport.js",
        "category": "authentication",
        "existing_usage_score": 40,
        "maturity_score": 25,
        "community_score": 15,
        "fit_score": 20,
        "total_score": 100,
        "confidence": "high",
        "rationale": "Already in codebase; Mature ecosystem (10K+ stars/1M+ downloads); Perfect fit for requirements",
        "alternatives": ["Auth.js", "Auth0", "custom JWT"]
      },
      // ... more options
    ]
  }
}
```

## Category Auto-Detection

The algorithm auto-detects the technology category from natural language requirements:

| Category | Keywords |
|----------|----------|
| **authentication** | oauth, login, jwt, passport, token |
| **database** | database, postgresql, mysql, mongodb, redis, sql, orm |
| **frontend_framework** | frontend, ui, react, vue, component, jsx |
| **backend_framework** | backend, api, server, express, django, flask |

Uses weighted scoring - more specific phrases get higher weight.

## Examples

### Example 1: Authentication for Node.js App

**Input**: Node.js app with Express and Passport already installed

```bash
python3 scripts/tech_stack_selector.py /path/to/project "Need OAuth"
```

**Output**:
```json
{
  "decision": "Passport.js",
  "confidence": "high",
  "rationale": "Already in codebase; Mature ecosystem (10K+ stars/1M+ downloads); Perfect fit for requirements",
  "scoring_breakdown": {
    "total": 100,
    "existing_usage": 40,
    "maturity": 25,
    "community": 15,
    "fit": 20
  }
}
```

### Example 2: Database for New Project

**Input**: Empty project, need database for sessions

```bash
python3 scripts/tech_stack_selector.py /path/to/empty/project "Need database for sessions"
```

**Output**:
```json
{
  "decision": "PostgreSQL",
  "confidence": "medium",
  "rationale": "Standard choice; Mature ecosystem (10K+ stars/1M+ downloads); Perfect fit for requirements",
  "scoring_breakdown": {
    "total": 70,
    "existing_usage": 10,
    "maturity": 25,
    "community": 15,
    "fit": 20
  }
}
```

## Integration with Maestro

The decision engine integrates with Maestro orchestrator:

```python
# In Maestro orchestrator
from decision_engine.scripts.tech_stack_selector import TechStackSelector

def make_tech_decision(project_path, requirement):
    selector = TechStackSelector(project_path)
    decision = selector.select_tech_stack(requirement)

    # Use decision in task generation
    tech_choice = decision["output"]["decision"]
    confidence = decision["output"]["confidence"]

    if confidence == "high":
        return tech_choice
    else:
        # Ask for confirmation on lower confidence
        return request_confirmation(decision)
```

## Testing

Run the comprehensive test suite:

```bash
python3 scripts/test_tech_stack_selector.py
```

Tests cover:
- TechOption dataclass conversion
- Category detection from natural language
- Existing technology detection
- Scoring calculations
- Decision structure and sorting
- Integration with real project structures

**Coverage**: 23 unit tests, all passing

## Fallback Strategies

When confidence is low or no clear winner:

1. **Provide alternatives**: Always return 2-3 alternative options
2. **Show scoring breakdown**: Transparent decision rationale
3. **Context awareness**: Consider existing stack
4. **Human review**: Low confidence decisions flagged for review

## Extending the Knowledge Base

To add new technology options:

1. Add to `TECH_KNOWLEDGE_BASE` in `tech_stack_selector.py`:

```python
'new_category': {
    'TechName': {
        'category': 'new_category',
        'maturity_score': 25,  # 0-25
        'community_score': 15,  # 0-15
        'fit_score': 20,  # 0-20
        'alternatives': ['Alt1', 'Alt2'],
        'ecosystem': 'nodejs',  # or 'python', 'any'
        'detect_patterns': ['pattern1', 'pattern2'],
    },
}
```

2. Add category keywords to `_detect_category_from_requirement()`:

```python
'new_category': ['keyword1', 'keyword2', 'keyword3'],
```

3. Add tests to `test_tech_stack_selector.py`

## Performance Considerations

- **Dependency scanning**: O(n) where n = number of dependency files
- **Pattern detection**: grep-based, timeout after 30 seconds
- **Scoring**: O(m) where m = number of options per category (typically 3-5)
- **Total runtime**: < 2 seconds for typical projects

## Limitations

1. **Static analysis only**: Doesn't run code or check runtime behavior
2. **Knowledge base scope**: Limited to predefined categories and options
3. **Binary existing detection**: Technology either exists or doesn't (no partial usage)
4. **No version conflicts**: Doesn't check for dependency version incompatibilities
5. **Subjective scoring**: Maturity/community scores are estimates

## Future Enhancements

- [ ] Dynamic knowledge base updates from GitHub/npm APIs
- [ ] Version compatibility checking
- [ ] License compatibility analysis
- [ ] Security vulnerability scanning
- [ ] Performance benchmarking integration
- [ ] Cost analysis (for paid services like Auth0)
- [ ] Learning from past decisions (feedback loop)

## Files

| File | Purpose |
|------|---------|
| `tech_stack_selector.py` | Main selection algorithm |
| `analyze_dependencies.py` | Dependency scanning |
| `detect_patterns.py` | Pattern detection |
| `test_tech_stack_selector.py` | Unit tests |
| `TECH_STACK_ALGORITHM.md` | This documentation |

## References

- [SKILL.md](SKILL.md) - Overall decision engine documentation
- [references/tech-stack-rubric.md](references/tech-stack-rubric.md) - Detailed scoring rubric
