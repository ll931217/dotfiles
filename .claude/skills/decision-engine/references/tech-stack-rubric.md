# Technology Stack Selection Rubric

Scoring criteria for autonomous technology selection decisions.

## Decision Process

1. **Check existing dependencies** - Prefer technologies already in the codebase
2. **Evaluate maturity** - Consider community support, stars, maintenance
3. **Assess fit** - Match to requirements (performance, security, scalability)
4. **Score options** - Apply rubric below
5. **Return top choice** - With rationale and alternatives

## Scoring Criteria

| Criterion | Weight | Factors |
|-----------|--------|---------|
| **Existing Usage** | 40% | Already in codebase = full score |
| **Maturity** | 25% | GitHub stars, npm downloads, last update |
| **Community** | 15% | Stack Overflow questions, documentation quality |
| **Fit** | 20% | Meets specific requirements |

### Existing Usage (40 points)

- Already in codebase = 40 points
- Compatible with existing stack = 30 points
- New but standard choice = 10 points
- New and experimental = 0 points

### Maturity (25 points)

- >10K GitHub stars / 1M+ npm downloads weekly = 25 points
- >1K stars / 100K+ downloads = 20 points
- >500 stars / 10K+ downloads = 15 points
- >100 stars / 1K+ downloads = 10 points
- <100 stars = 5 points

### Community (15 points)

- Active community, frequent updates = 15 points
- Moderate community, periodic updates = 10 points
- Small community, rare updates = 5 points
- Abandoned = 0 points

### Fit (20 points)

- Perfect match for requirements = 20 points
- Good match with minor workarounds = 15 points
- Partial match requires adaptation = 10 points
- Poor fit = 0 points

## Technology Categories

### Frontend Frameworks

| Framework | Score | Use When |
|-----------|-------|----------|
| React | 95 | Existing React codebase |
| Vue | 85 | Simple apps, existing Vue |
| Svelte | 75 | Performance critical |
| Vanilla | 50 | Very simple UIs |

### Backend Frameworks

| Framework | Score | Use When |
|-----------|-------|----------|
| Express | 90 | Existing Node.js |
| FastAPI | 85 | Python, async needed |
| Django | 80 | Python, full-featured |
| Go stdlib | 85 | Go, performance |
| Rails | 75 | Ruby, rapid prototyping |

### Databases

| Database | Score | Use When |
|----------|-------|----------|
| PostgreSQL | 95 | Relational, existing usage |
| MySQL | 90 | Relational, existing usage |
| SQLite | 70 | Embedded, simple apps |
| MongoDB | 80 | Document, flexible schema |
| Redis | 85 | Caching, sessions |

### Authentication

| Library | Score | Use When |
|---------|-------|----------|
| Passport.js | 90 | Node.js OAuth |
| Auth.js | 85 | Modern web OAuth |
| Auth0 | 80 | Third-party service |
| Custom JWT | 70 | Simple token auth |

## Decision Examples

### Example 1: OAuth Library

**Requirements:** OAuth for Node.js app

**Options:**
1. Passport.js - 95 points (existing, mature, perfect fit)
2. Auth.js - 80 points (not existing, good fit)
3. Auth0 - 70 points (third-party, cost)

**Decision:** Passport.js
**Rationale:** Already in package.json, mature ecosystem (20K+ stars), perfect fit for OAuth

### Example 2: Database

**Requirements:** User sessions for web app

**Options:**
1. PostgreSQL - 95 points (existing, mature, perfect fit)
2. Redis - 90 points (not existing but ideal for sessions)
3. SQLite - 70 points (embedded, limited scalability)

**Decision:** PostgreSQL (if already using) or Redis (if session-specific)
**Rationale:** Prefer existing stack, but Redis is purpose-built for sessions

## Confidence Levels

- **High** (90+ score) - Clear winner, proceed confidently
- **Medium** (70-89 score) - Good choice, monitor for issues
- **Low** (<70 score) - Consider alternatives, may need to reevaluate
