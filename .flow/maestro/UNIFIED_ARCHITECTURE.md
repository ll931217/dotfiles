# Maestro: Unified Architecture v2

> **Merged from two brainstorming sessions combining multi-process orchestration, interactive brainstorming, and web-based monitoring**

---

## Executive Summary

Maestro v2 is a **daemon-based autonomous development system** with three key phases:

1. **Interactive Brainstorming** (Human + AI collaboration)
2. **Automated Planning** (AI generates detailed plan, human approves)
3. **Autonomous Execution** (AI agent implements in isolated worktree)

**Key innovation:** **Web-first interface** for real-time monitoring, control, and collaboration.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Web Interface (React)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Brainstorm  │ │   Plan      │ │   Monitor   │ │   Settings/Config   │  │
│  │   Chat UI   │ │   Review    │ │  Dashboard  │ │                     │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ WebSocket + REST API
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Maestro Daemon (Python/FastAPI)                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ State Machine     │  │ Agent Supervisor │  │  WebSocket Manager      │  │
│  │ - Session states  │  │ - Spawn workers  │  │  - Real-time updates    │  │
│  │ - Transitions     │  │ - Monitor logs   │  │  - Event streaming      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Planning Engine   │  │ Worktree Manager │  │  Safety Layer           │  │
│  │ - Task breakdown  │  │ - Git isolation  │  │  - Approval gates       │  │
│  │ - Dependencies    │  │ - Environment    │  │  - Rollback             │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ↓                       ↓                       ↓
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  PostgreSQL   │       │    Redis      │       │ File System   │
│  - Sessions   │       │  - Job queue  │       │  - Worktrees  │
│  - Plans      │       │  - Pub/sub    │       │  - Logs       │
│  - Decisions  │       │  - Cache      │       │  - Checkpoints│
└───────────────┘       └───────────────┘       └───────────────┘
                                │
                                ↓
                    ┌───────────────────────────┐
                    │   Claude Code Workers     │
                    │  ┌─────┐ ┌─────┐ ┌─────┐ │
                    │  │W-1  │ │W-2  │ │W-3  │ │
                    │  └─────┘ └─────┘ └─────┘ │
                    └───────────────────────────┘
```

---

## Phase 1: Web Interface (Current Focus)

### Tech Stack
- **Frontend:** React + TypeScript + Vite
- **UI Library:** shadcn/ui (Radix UI + Tailwind)
- **Real-time:** Socket.IO client
- **State:** Zustand or Jotai (lightweight)
- **Charts:** Recharts for metrics visualization

### Page Structure

```
/                           → Dashboard (overview of all sessions)
/session                    → Session list
/session/:id                → Session detail (monitor active session)
/session/:id/brainstorm     → Brainstorming chat interface
/session/:id/plan           → Plan review and approval
/session/:id/logs           → Live log streaming
/settings                   → Configuration
```

### Component Hierarchy

```
App
├── Layout
│   ├── Sidebar (navigation)
│   ├── Header (session status, notifications)
│   └── MainContent
├── DashboardPage
│   ├── SessionCard (multiple)
│   └── QuickActions
├── SessionDetailPage
│   ├── PhaseIndicator (current phase)
│   ├── BrainstormView (chat interface)
│   ├── PlanReviewView (task breakdown, approve button)
│   ├── MonitorDashboard
│   │   ├── WorkerGrid (active workers)
│   │   ├── TaskProgress (timeline)
│   │   ├── ResourceCharts (CPU, memory, tokens)
│   │   └── LogStream (live logs)
│   └── ControlPanel (pause, resume, rollback)
└── SettingsPage
    ├── AgentConfig
    ├── ResourceLimits
    └── NotificationPreferences
```

---

## Phase 2: Maestro Daemon (Python/FastAPI)

### Core Modules

```python
maestro/
├── main.py                    # Entry point
├── api/
│   ├── app.py                 # FastAPI app
│   ├── routes/
│   │   ├── sessions.py        # Session CRUD
│   │   ├── websocket.py       # WebSocket endpoint
│   │   └── control.py         # Control commands
│   └── models/
│       ├── session.py         # Session data models
│       └── plan.py            # Plan structures
├── core/
│   ├── state_machine.py       # Session state management
│   ├── planning_engine.py     # Plan generation
│   ├── supervisor.py          # Agent supervision
│   └── safety.py              # Safety checks & rollbacks
├── agents/
│   ├── base.py                # Base agent adapter
│   ├── claude_code.py         # Claude Code adapter
│   └── factory.py             # Agent factory
├── worktrees/
│   └── manager.py             # Git worktree management
├── monitoring/
│   ├── metrics.py             # Resource monitoring
│   ├── logs.py                # Log aggregation
│   └── events.py              # Event publishing
└── db/
    ├── models.py              # SQLAlchemy models
    └── session.py             # Database session
```

### State Machine

```python
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Optional

class SessionState(Enum):
    """Session lifecycle states"""
    IDLE = "idle"
    BRAINSTORMING = "brainstorming"          # Interactive
    PLANNING = "planning"                    # AI generating plan
    PLAN_REVIEW = "plan_review"              # Human review
    APPROVED = "approved"                    # Ready to execute
    EXECUTING = "executing"                  # Agent running
    PAUSED = "paused"                        # User paused
    VALIDATING = "validating"                # Running tests
    COMPLETED = "completed"                  # Success
    FAILED = "failed"                        # With rollback
    CANCELLED = "cancelled"                  # User cancelled

@dataclass
class StateTransition:
    """State transition rule"""
    from_state: SessionState
    event: str
    to_state: SessionState
    action: Optional[Callable] = None
    requires_approval: bool = False

# State transition table
TRANSITIONS = [
    # Brainstorming flow
    StateTransition(IDLE, "start", BRAINSTORMING),
    StateTransition(BRAINSTORMING, "idea_ready", PLANNING),

    # Planning flow
    StateTransition(PLANNING, "plan_ready", PLAN_REVIEW),
    StateTransition(PLAN_REVIEW, "approved", APPROVED),
    StateTransition(PLAN_REVIEW, "regenerate", PLANNING),

    # Execution flow
    StateTransition(APPROVED, "start_execution", EXECUTING),
    StateTransition(EXECUTING, "pause", PAUSED),
    StateTransition(PAUSED, "resume", EXECUTING),
    StateTransition(EXECUTING, "complete", VALIDATING),

    # Validation flow
    StateTransition(VALIDATING, "pass", COMPLETED),
    StateTransition(VALIDATING, "fail", EXECUTING),  # Retry

    # Error handling
    StateTransition(EXECUTING, "error", FAILED, requires_approval=True),
    StateTransition(ANY, "cancel", CANCELLED, requires_approval=True),
]

class StateMachine:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_state = SessionState.IDLE
        self.history: List[StateTransition] = []

    def transition(self, event: str, context: dict = None) -> bool:
        """Attempt state transition"""
        for rule in TRANSITIONS:
            if rule.from_state == self.current_state and rule.event == event:
                if rule.requires_approval and not context.get("approved"):
                    return False

                if rule.action:
                    rule.action(context)

                self.history.append(rule)
                self.current_state = rule.to_state
                self.publish_state_change()
                return True

        return False

    def publish_state_change(self):
        """Notify subscribers of state change"""
        event_bus.publish(f"session:{self.session_id}:state_changed", {
            "session_id": self.session_id,
            "old_state": self.history[-1].from_state if self.history else SessionState.IDLE,
            "new_state": self.current_state,
            "timestamp": datetime.utcnow().isoformat()
        })
```

---

## Phase 3: Database Schema

```sql
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    description TEXT,

    -- Brainstorming phase
    idea_summary TEXT,
    conversation_json JSONB,

    -- Planning phase
    plan_json JSONB,
    plan_approved_at TIMESTAMP WITH TIME ZONE,

    -- Execution phase
    worktree_path VARCHAR(500),
    agent_pid INTEGER,
    agent_type VARCHAR(50) DEFAULT 'claude_code',
    agent_config JSONB,

    -- Results
    result_json JSONB,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,

    -- Safety
    checkpoint_commit VARCHAR(40),
    rollback_commit VARCHAR(40),
);

-- Tasks table (from plan)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id),

    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 2,

    -- Dependencies
    depends_on JSONB,  -- Array of task IDs
    blocks JSONB,      -- Array of task IDs

    -- Execution
    assigned_worker_id VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result_json JSONB,

    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
);

-- Agent logs (for streaming)
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    task_id UUID REFERENCES tasks(id),

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level VARCHAR(20),  -- debug, info, warn, error
    source VARCHAR(100),  -- worker_id, supervisor, etc.
    message TEXT,
    metadata JSONB,

    -- Index for streaming queries
    INDEX idx_session_timestamp (session_id, timestamp),
    INDEX idx_task_timestamp (task_id, timestamp)
);

-- Metrics (for charts)
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    worker_id VARCHAR(100),

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_name VARCHAR(100),
    metric_value FLOAT,
    unit VARCHAR(20),

    INDEX idx_session_metric_time (session_id, metric_name, timestamp)
);

-- Decisions (for learning)
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    task_id UUID REFERENCES tasks(id),

    decision_type VARCHAR(100),  -- tech_stack, approach, library, etc.
    context JSONB,
    options JSONB,  -- Array of options considered
    chosen INTEGER,  -- Index in options array
    rationale TEXT,

    outcome VARCHAR(50),  -- success, partial, failure
    outcome_measured_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
);
```

---

## Phase 4: WebSocket Events

### Client → Server

```typescript
// Control messages
type ClientMessage =
  | { type: "subscribe"; session_id: string }
  | { type: "unsubscribe"; session_id: string }
  | { type: "send_message"; session_id: string; message: string }  // Brainstorming
  | { type: "approve_plan"; session_id: string; plan_id: string }
  | { type: "pause"; session_id: string }
  | { type: "resume"; session_id: string }
  | { type: "cancel"; session_id: string; reason: string }
  | { type: "rollback"; session_id: string; checkpoint: string };
```

### Server → Client

```typescript
// Event stream
type ServerEvent =
  // State changes
  | { type: "state_changed"; session_id: string; from: string; to: string }

  // Brainstorming
  | { type: "message"; session_id: string; role: "user" | "ai"; content: string }

  // Planning
  | { type: "plan_generated"; session_id: string; plan: Plan }
  | { type: "plan_updated"; session_id: string; plan: Plan }

  // Execution
  | { type: "task_started"; session_id: string; task_id: string; worker_id: string }
  | { type: "task_progress"; session_id: string; task_id: string; progress: number }
  | { type: "task_completed"; session_id: string; task_id: string; result: any }
  | { type: "task_failed"; session_id: string; task_id: string; error: string }

  // Workers
  | { type: "worker_spawned"; session_id: string; worker_id: string; pid: number }
  | { type: "worker_terminated"; session_id: string; worker_id: string; exit_code: number }

  // Logs
  | { type: "log_entry"; session_id: string; level: string; message: string; timestamp: string }

  // Metrics
  | { type: "metric"; session_id: string; worker_id: string; name: string; value: number; unit: string }

  // Completion
  | { type: "session_completed"; session_id: string; result: any }
  | { type: "session_failed"; session_id: string; error: string; rollback_commit: string };
```

---

## Implementation Roadmap

### Milestone 1: Web UI Skeleton (Week 1-2)
- [ ] React + Vite + shadcn/ui setup
- [ ] Basic routing and layout
- [ ] Session list page
- [ ] Session detail page skeleton
- [ ] WebSocket connection manager

### Milestone 2: Backend API (Week 2-3)
- [ ] FastAPI project structure
- [ ] Database models and migrations
- [ ] Session CRUD endpoints
- [ ] WebSocket endpoint
- [ ] State machine implementation

### Milestone 3: Brainstorming Flow (Week 3-4)
- [ ] Chat UI component
- [ ] Message storage (database)
- [ ] AI integration (Claude API)
- [ ] Idea summary generation
- [ ] Transition to planning

### Milestone 4: Planning & Review (Week 4-5)
- [ ] Plan generation engine
- [ ] Plan display component
- [ ] Edit/modify plan UI
- [ ] Approval workflow
- [ ] Transition to execution

### Milestone 5: Execution Monitoring (Week 5-6)
- [ ] Worker supervisor
- [ ] Git worktree manager
- [ ] Claude Code adapter
- [ ] Real-time log streaming
- [ ] Task progress visualization

### Milestone 6: Control & Safety (Week 6-7)
- [ ] Pause/resume functionality
- [ ] Rollback mechanism
- [ ] Approval gates
- [ ] Resource monitoring
- [ ] Error handling

### Milestone 7: Polish & Enhancements (Week 7-8)
- [ ] Metrics dashboard
- [ ] Charts and visualization
- [ ] Settings page
- [ ] Notification system
- [ ] Session templates

---

## Quick Start (Development)

```bash
# Clone repository
git clone https://github.com/your-org/maestro.git
cd maestro

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn maestro.api.app:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Open browser
open http://localhost:5173
```

---

## Key Features Summary

| Feature | Description | Status |
|---------|-------------|--------|
| Interactive Brainstorming | Chat-based ideation with AI | 🚧 Planned |
| Automated Planning | AI generates detailed implementation plan | 🚧 Planned |
| Plan Review | Human reviews and approves plan before execution | 🚧 Planned |
| Git Isolation | Worktree-based isolated execution environment | 🚧 Planned |
| Worker Supervision | Spawn and monitor Claude Code workers | 🚧 Planned |
| Real-time Monitoring | Live dashboard with logs, metrics, progress | 🚧 Planned |
| Pause/Resume | User can pause and resume execution | 🚧 Planned |
| Rollback | Automatic rollback on failures | 🚧 Planned |
| Approval Gates | Human approval for critical actions | 🚧 Planned |
| Resource Limits | CPU, memory, API call limits | 🚧 Planned |
| Session Templates | Predefined patterns for common project types | 🚧 Planned |

---

## Future Enhancements (Post-MVP)

- [ ] Multi-repository coordination
- [ ] Decision learning system
- [ ] A/B testing for approaches
- [ ] Plugin system
- [ ] Session templates library
- [ ] Historical analysis and insights
- [ ] Team collaboration features
- [ ] CI/CD integration
