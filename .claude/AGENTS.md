# Custom Agents Reference

This directory contains custom AI agent definitions for Claude Code, each specialized for specific development tasks.

---

## Table of Contents

1. [Architecture & Review](#architecture--review)
2. [Backend Development](#backend-development)
3. [Frontend Development](#frontend-development)
4. [Data & Analytics](#data--analytics)
5. [Infrastructure & DevOps](#infrastructure--devops)
6. [Security & Performance](#security--performance)
7. [Process & Context Management](#process--context-management)

---

## Architecture & Review

### architect-reviewer
**Reviews architectural consistency and design patterns**

- Validates SOLID principles adherence
- Checks for proper layer separation
- Identifies architectural debt
- Reviews pattern consistency across codebase

**Use when**: Making structural changes, introducing new patterns, or reviewing architectural decisions.

### code-reviewer
**Reviews code for quality, security, and maintainability**

- Proactive review after code completion
- Checks for bugs, logic errors, and vulnerabilities
- Validates adherence to project conventions
- Reviews code before commits/PRs

**Use when**: After writing significant code changes, before creating pull requests.

---

## Backend Development

### backend-architect
**Designs RESTful APIs, microservices, and database schemas**

- API endpoint design
- Microservice boundary definition
- Database schema design
- Reviews system architecture for scalability

**Use when**: Creating new backend services, designing APIs, or planning database structure.

### api-documenter
**Creates OpenAPI/Swagger specs and generates SDKs**

- OpenAPI/Swagger specification generation
- SDK documentation
- API versioning and examples
- Interactive documentation

**Use when**: Documenting APIs, generating SDKs, or creating API references.

---

## Frontend Development

### frontend-developer
**Builds React components and handles client-side state**

- Responsive layouts implementation
- Client-side state management
- Frontend performance optimization
- Accessibility compliance

**Use when**: Creating UI components, fixing frontend issues, or managing client state.

### react-pro
**React specialization with hooks, components, and patterns**

- React best practices
- Component composition
- State management (Context, Redux)
- Performance optimization

**Use when**: Working specifically with React applications.

---

## Data & Analytics

### data-engineer
**Builds ETL pipelines and data warehouses**

- High-performance data processing
- Storage optimization
- ETL pipeline development
- Analytics visualization

**Use when**: Working with data pipelines, warehouses, or analytics infrastructure.

### data-scientist
**Data analysis with SQL, BigQuery, and insights**

- SQL and BigQuery operations
- Data analysis and insights
- Statistical analysis

**Use when**: Analyzing data, running queries, or extracting insights from datasets.

---

## Infrastructure & DevOps

### deployment-engineer
**Configures CI/CD, Docker, and cloud deployments**

- GitHub Actions workflows
- Docker containerization
- Kubernetes deployment
- Infrastructure automation

**Use when**: Setting up CI/CD, containerizing apps, or configuring deployments.

### devops-troubleshooter
**Debugs production issues and analyzes logs**

- Production debugging
- Log analysis
- Incident response
- Root cause analysis

**Use when**: Debugging production issues, analyzing logs, or handling incidents.

### terraform-specialist
**Writes Terraform modules and manages IaC**

- Infrastructure as Code
- State file management
- Module development
- Drift detection

**Use when**: Managing cloud infrastructure with Terraform.

---

## Security & Performance

### security-auditor
**Reviews for vulnerabilities and implements security**

- OWASP compliance
- JWT/OAuth2 implementation
- CORS/CSP configuration
- Security best practices

**Use when**: Implementing auth, reviewing for vulnerabilities, or configuring security.

### performance-engineer
**Profiles apps, optimizes bottlenecks, implements caching**

- Application profiling
- Bottleneck identification
- Caching strategies
- Load testing

**Use when**: Optimizing performance, profiling apps, or implementing caching.

### database-admin
**Manages DB operations, backups, replication**

- Database operations
- Backup and recovery
- Replication management
- User permissions

**Use when**: Database setup, operational issues, or recovery procedures.

### database-optimizer
**Optimizes SQL queries, designs indexes**

- Query optimization
- Index design
- N+1 problem resolution
- Caching implementation

**Use when**: Database performance issues, slow queries, or schema optimization.

---

## Programming Language Specialists

### javascript-pro
**Modern JavaScript (ES6+) and Node.js**

- ES6+ patterns
- Async/await, promises
- Browser/Node compatibility
- Event loop understanding

**Use when**: JavaScript optimization or complex JS patterns.

### python-pro
**Idiomatic Python with decorators, generators, async**

- Decorators and generators
- Async/await patterns
- Type hints
- Performance optimization

**Use when**: Python refactoring, optimization, or advanced features.

### typescript-pro
**TypeScript specialization**

- Type system design
- Generic programming
- Type-safe patterns

**Use when**: Working with TypeScript codebases.

### sql-pro
**Complex SQL queries, CTEs, window functions**

- Complex query design
- CTEs and window functions
- Stored procedures
- Normalized schema design

**Use when**: Query optimization or complex database operations.

---

## Specialized Domains

### ai-engineer
**Builds LLM applications, RAG systems, prompts**

- LLM application development
- RAG system implementation
- Prompt pipeline design
- AI API integrations

**Use when**: Building AI features, RAG systems, or LLM applications.

### flutter-expert
**Flutter and Dart mobile development**

- Mobile app development
- Flutter patterns
- Cross-platform optimization

**Use when**: Developing Flutter applications.

### network-engineer
**Network connectivity, load balancers, DNS**

- Network debugging
- Load balancing configuration
- DNS and SSL/TLS setup

**Use when**: Network issues or infrastructure configuration.

### quant-analyst
**Financial models, trading strategies, risk metrics**

- Financial modeling
- Trading strategy backtesting
- Risk assessment
- Portfolio optimization

**Use when**: Quantitative finance or trading systems.

### risk-manager
**Monitors portfolio risk, position limits**

- Risk metrics tracking
- Position limit management
- Hedging strategies
- Expectancy calculation

**Use when**: Risk management in trading systems.

---

## Process & Context Management

### context-manager
**Manages context across multi-agent sessions**

- Multi-agent workflow coordination
- Context preservation
- Session management

**Use when**: Projects exceed 10k tokens or require multi-agent coordination.

### debugger
**Specializes in errors, test failures, bugs**

- Error detection and fixing
- Test failure diagnosis
- Bug reproduction

**Use when**: Encountering errors or test failures.

### error-detective
**Searches logs and code for error patterns**

- Error pattern recognition
- Log analysis
- Stack trace investigation

**Use when**: Investigating production errors or log anomalies.

### legacy-modernizer
**Refactors legacy code, migrates frameworks**

- Legacy codebase refactoring
- Framework migrations
- Technical debt reduction

**Use when**: Modernizing old code or migrating frameworks.

### prompt-engineer
**Optimizes prompts for LLMs and AI systems**

- Prompt pattern design
- AI system optimization
- Agent prompt refinement

**Use when**: Building AI features or optimizing agent prompts.

### test-automator
**Creates unit, integration, and e2e test suites**

- Comprehensive test creation
- CI pipeline integration
- Mocking strategies
- Test data management

**Use when**: Setting up tests or improving coverage.

---

## Usage Guidelines

### When to Invoke Agents

1. **Proactively**: Use agents proactively when their description matches your task
2. **After code changes**: Run `code-reviewer` after significant code changes
3. **Before commits**: Use review agents before creating pull requests
4. **For complex tasks**: Use specialized agents for domain-specific work

### Agent Coordination

Some tasks may require multiple agents in sequence:

```
architect-reviewer → backend-architect → code-reviewer → test-automator
```

### Available via Claude Code

These agents are available as subagents in the Task tool:

```python
Task(
    subagent_type="code-reviewer",
    prompt="Review the recent changes",
    description="Review code changes"
)
```

---

## Agent Categories Summary

| Category | Agents |
|----------|--------|
| Architecture | architect-reviewer, backend-architect |
| Code Quality | code-reviewer, debugger, error-detective |
| Frontend | frontend-developer, react-pro |
| Backend | backend-architect, api-documenter |
| Data | data-engineer, data-scientist |
| DevOps | deployment-engineer, devops-troubleshooter |
| Security | security-auditor |
| Performance | performance-engineer, database-optimizer |
| Languages | javascript-pro, python-pro, typescript-pro, sql-pro |
| Specialized | ai-engineer, flutter-expert, quant-analyst, risk-manager |
| Process | context-manager, legacy-modernizer, test-automator |

---

## Adding New Agents

To add a new custom agent:

1. Create a new file in `agents/` directory: `domain-role.md`
2. Follow the naming pattern: `[domain]-[role].md`
3. Include clear description of when to use the agent
4. Define specialized capabilities and tools available

Example agent structure:

```markdown
# my-specialist

**Purpose**: Brief description of what this agent does

**Specializes in**:
- Area of expertise 1
- Area of expertise 2

**Use when**: Specific scenarios for invoking this agent

**Tools available**:
- List of specialized tools
```
