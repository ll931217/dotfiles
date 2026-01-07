#!/usr/bin/env python3
"""
Maestro Session Lifecycle Manager

Handles session creation, updates, termination, and persistence for
Maestro orchestration sessions. Implements session state transitions
and provides a query interface for session management.
"""

import json
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from uuid import uuid4


class SessionStatus(str, Enum):
    """Session status states matching the JSON schema."""
    INITIALIZING = "initializing"
    PLANNING = "planning"
    GENERATING_TASKS = "generating_tasks"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class SessionPhase(str, Enum):
    """Session execution phases."""
    PLAN = "plan"
    GENERATE_TASKS = "generate_tasks"
    IMPLEMENT = "implement"
    VALIDATE = "validate"
    CLEANUP = "cleanup"


@dataclass
class GitContext:
    """Git repository context at session start."""
    branch: str
    commit: str
    repo_root: str
    is_worktree: bool = False
    worktree_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling None values."""
        data = asdict(self)
        # Remove worktree_name if None
        if data.get('worktree_name') is None:
            data.pop('worktree_name', None)
        return data


@dataclass
class PRDReference:
    """Reference to generated PRD."""
    filename: str
    path: str
    version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling None values."""
        data = asdict(self)
        if data.get('version') is None:
            data.pop('version', None)
        return data


@dataclass
class SessionStatistics:
    """Session execution statistics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    decisions_made: int = 0
    checkpoints_created: int = 0
    error_recovery_count: int = 0
    duration_seconds: float = 0.0


@dataclass
class SessionConfiguration:
    """Session configuration."""
    max_iterations: int = 3
    timeout_minutes: int = 120
    auto_checkpoint: bool = True
    error_recovery_enabled: bool = True


@dataclass
class Session:
    """Maestro orchestration session."""
    session_id: str
    feature_request: str
    status: SessionStatus
    created_at: str
    git_context: GitContext
    current_phase: Optional[SessionPhase] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    prd_reference: Optional[PRDReference] = None
    statistics: SessionStatistics = field(default_factory=SessionStatistics)
    configuration: SessionConfiguration = field(default_factory=SessionConfiguration)

    def __post_init__(self):
        """Convert string status to enum if needed."""
        if isinstance(self.status, str):
            self.status = SessionStatus(self.status)
        if isinstance(self.current_phase, str):
            self.current_phase = SessionPhase(self.current_phase)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        data = {
            "session_id": self.session_id,
            "feature_request": self.feature_request,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "git_context": self.git_context.to_dict(),
        }

        # Add optional fields
        if self.current_phase:
            data["current_phase"] = self.current_phase.value
        if self.prd_reference:
            data["prd_reference"] = self.prd_reference.to_dict()

        # Add nested objects
        data["statistics"] = asdict(self.statistics)
        data["configuration"] = asdict(self.configuration)

        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


class SessionManager:
    """Main session lifecycle manager."""

    # Valid state transitions
    STATE_TRANSITIONS = {
        SessionStatus.INITIALIZING: [
            SessionStatus.PLANNING,
            SessionStatus.FAILED,
            SessionStatus.PAUSED,
        ],
        SessionStatus.PLANNING: [
            SessionStatus.GENERATING_TASKS,
            SessionStatus.FAILED,
            SessionStatus.PAUSED,
        ],
        SessionStatus.GENERATING_TASKS: [
            SessionStatus.IMPLEMENTING,
            SessionStatus.FAILED,
            SessionStatus.PAUSED,
        ],
        SessionStatus.IMPLEMENTING: [
            SessionStatus.VALIDATING,
            SessionStatus.FAILED,
            SessionStatus.PAUSED,
        ],
        SessionStatus.VALIDATING: [
            SessionStatus.GENERATING_REPORT,
            SessionStatus.IMPLEMENTING,  # Back to implementation if fixes needed
            SessionStatus.FAILED,
            SessionStatus.PAUSED,
        ],
        SessionStatus.GENERATING_REPORT: [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.PAUSED,
        ],
        SessionStatus.COMPLETED: [],  # Terminal state
        SessionStatus.FAILED: [],  # Terminal state
        SessionStatus.PAUSED: [
            SessionStatus.PLANNING,
            SessionStatus.GENERATING_TASKS,
            SessionStatus.IMPLEMENTING,
            SessionStatus.VALIDATING,
            SessionStatus.GENERATING_REPORT,
            SessionStatus.FAILED,
            SessionStatus.COMPLETED,
        ],
    }

    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize session manager.

        Args:
            repo_root: Repository root path. If None, auto-detected from git.
        """
        if repo_root:
            self.repo_root = Path(repo_root).absolute()
        else:
            self.repo_root = Path(__file__).parent.parent.parent.parent.absolute()

        self.sessions_dir = self.repo_root / ".flow" / "maestro" / "sessions"
        self._ensure_sessions_dir()

    def _ensure_sessions_dir(self):
        """Create sessions directory if it doesn't exist."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_dir(self, session_id: str) -> Path:
        """Get directory path for a session."""
        return self.sessions_dir / session_id

    def _get_metadata_path(self, session_id: str) -> Path:
        """Get metadata file path for a session."""
        return self._get_session_dir(session_id) / "metadata.json"

    def _get_current_git_context(self) -> GitContext:
        """Capture current git repository context."""
        try:
            # Get branch name
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
            branch = branch_result.stdout.strip()

            # Get commit SHA
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
            commit = commit_result.stdout.strip()

            # Check if we're in a worktree
            worktree_result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
            is_worktree = worktree_result.stdout.strip() == "true"

            worktree_name = None
            if is_worktree:
                # Try to get worktree name
                git_dir_result = subprocess.run(
                    ["git", "rev-parse", "--git-dir"],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_root,
                )
                git_dir = Path(git_dir_result.stdout.strip())
                if "worktrees" in str(git_dir):
                    worktree_name = git_dir.parent.name

            return GitContext(
                branch=branch,
                commit=commit,
                repo_root=str(self.repo_root),
                is_worktree=is_worktree,
                worktree_name=worktree_name,
            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            # Fallback if git commands fail
            return GitContext(
                branch="unknown",
                commit="unknown",
                repo_root=str(self.repo_root),
                is_worktree=False,
            )

    def _generate_session_id(self) -> str:
        """Generate a unique session ID using UUID v4."""
        return str(uuid4())

    def _current_timestamp(self) -> str:
        """Get current ISO 8601 timestamp."""
        return datetime.utcnow().isoformat() + "Z"

    def create_session(
        self,
        feature_request: str,
        configuration: Optional[SessionConfiguration] = None,
    ) -> Session:
        """
        Create a new session.

        Args:
            feature_request: User's feature request description
            configuration: Optional session configuration

        Returns:
            Created Session object

        Raises:
            FileExistsError: If session ID collision occurs (should be extremely rare)
        """
        session_id = self._generate_session_id()
        now = self._current_timestamp()
        git_context = self._get_current_git_context()

        if configuration is None:
            configuration = SessionConfiguration()

        session = Session(
            session_id=session_id,
            feature_request=feature_request,
            status=SessionStatus.INITIALIZING,
            created_at=now,
            updated_at=now,
            git_context=git_context,
            configuration=configuration,
        )

        # Create session directory
        session_dir = self._get_session_dir(session_id)
        session_dir.mkdir(exist_ok=True)

        # Save metadata
        self._save_metadata(session)

        return session

    def _save_metadata(self, session: Session):
        """Save session metadata to disk."""
        metadata_path = self._get_metadata_path(session.session_id)

        with open(metadata_path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def _load_metadata(self, session_id: str) -> Dict[str, Any]:
        """Load session metadata from disk."""
        metadata_path = self._get_metadata_path(session_id)

        if not metadata_path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        with open(metadata_path) as f:
            return json.load(f)

    def _dict_to_session(self, data: Dict[str, Any]) -> Session:
        """Convert dictionary to Session object."""
        git_context = GitContext(**data["git_context"])

        prd_reference = None
        if "prd_reference" in data and data["prd_reference"]:
            prd_reference = PRDReference(**data["prd_reference"])

        statistics = SessionStatistics()
        if "statistics" in data and data["statistics"]:
            statistics = SessionStatistics(**data["statistics"])

        configuration = SessionConfiguration()
        if "configuration" in data and data["configuration"]:
            configuration = SessionConfiguration(**data["configuration"])

        return Session(
            session_id=data["session_id"],
            feature_request=data["feature_request"],
            status=data["status"],
            created_at=data["created_at"],
            git_context=git_context,
            current_phase=data.get("current_phase"),
            updated_at=data.get("updated_at"),
            completed_at=data.get("completed_at"),
            prd_reference=prd_reference,
            statistics=statistics,
            configuration=configuration,
        )

    def get_session(self, session_id: str) -> Session:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session object

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        data = self._load_metadata(session_id)
        return self._dict_to_session(data)

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> Session:
        """
        Update session fields.

        Args:
            session_id: Session UUID
            updates: Dictionary of fields to update

        Returns:
            Updated Session object

        Raises:
            FileNotFoundError: If session doesn't exist
            ValueError: If invalid update fields provided
        """
        session = self.get_session(session_id)

        # Apply updates
        for key, value in updates.items():
            if not hasattr(session, key):
                raise ValueError(f"Invalid session field: {key}")

            # Handle special cases
            if key == "status" and isinstance(value, str):
                value = SessionStatus(value)
            elif key == "current_phase" and isinstance(value, str):
                value = SessionPhase(value)
            elif key == "git_context" and isinstance(value, dict):
                value = GitContext(**value)
            elif key == "prd_reference" and isinstance(value, dict):
                value = PRDReference(**value)
            elif key == "statistics" and isinstance(value, dict):
                current_stats = session.statistics
                value = SessionStatistics(**{**asdict(current_stats), **value})
            elif key == "configuration" and isinstance(value, dict):
                current_config = session.configuration
                value = SessionConfiguration(**{**asdict(current_config), **value})

            setattr(session, key, value)

        # Update timestamp
        session.updated_at = self._current_timestamp()

        # Save changes
        self._save_metadata(session)

        return session

    def transition_state(
        self,
        session_id: str,
        new_state: SessionStatus,
    ) -> Session:
        """
        Transition session to a new state.

        Args:
            session_id: Session UUID
            new_state: New state to transition to

        Returns:
            Updated Session object

        Raises:
            FileNotFoundError: If session doesn't exist
            ValueError: If state transition is invalid
        """
        session = self.get_session(session_id)
        current_state = session.status

        # Check if transition is valid
        if new_state not in self.STATE_TRANSITIONS.get(current_state, []):
            raise ValueError(
                f"Invalid state transition: {current_state.value} -> {new_state.value}. "
                f"Valid transitions from {current_state.value}: "
                f"{[s.value for s in self.STATE_TRANSITIONS[current_state]]}"
            )

        # Build updates dict
        updates = {"status": new_state}

        # If transitioning to a terminal state, set completed_at
        if new_state in [SessionStatus.COMPLETED, SessionStatus.FAILED]:
            updates["completed_at"] = self._current_timestamp()

        # Update state
        return self.update_session(session_id, updates)

    def query_sessions(
        self,
        status: Optional[SessionStatus] = None,
        phase: Optional[SessionPhase] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        branch: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Session]:
        """
        Query sessions with filters.

        Args:
            status: Filter by status
            phase: Filter by current phase
            created_after: ISO 8601 timestamp for lower bound
            created_before: ISO 8601 timestamp for upper bound
            branch: Filter by git branch
            limit: Maximum number of results

        Returns:
            List of matching Session objects
        """
        results = []

        # Iterate through session directories
        for session_dir in self.sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue

            metadata_path = session_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                data = self._load_metadata(session_dir.name)
                session = self._dict_to_session(data)

                # Apply filters
                if status and session.status != status:
                    continue
                if phase and session.current_phase != phase:
                    continue
                if created_after and session.created_at < created_after:
                    continue
                if created_before and session.created_at > created_before:
                    continue
                if branch and session.git_context.branch != branch:
                    continue

                results.append(session)

            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted sessions
                continue

        # Sort by created_at descending (newest first)
        results.sort(key=lambda s: s.created_at, reverse=True)

        # Apply limit
        if limit:
            results = results[:limit]

        return results

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and its data.

        Args:
            session_id: Session UUID

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        session_dir = self._get_session_dir(session_id)

        if not session_dir.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Remove session directory and all contents
        for item in session_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                for sub_item in item.iterdir():
                    sub_item.unlink()
                item.rmdir()

        session_dir.rmdir()

    def list_active_sessions(self) -> List[Session]:
        """
        Get all non-terminal sessions.

        Returns:
            List of active Session objects
        """
        terminal_states = {SessionStatus.COMPLETED, SessionStatus.FAILED}

        return [
            s for s in self.query_sessions()
            if s.status not in terminal_states
        ]

    def get_recent_sessions(self, count: int = 10) -> List[Session]:
        """
        Get most recent sessions.

        Args:
            count: Number of sessions to return

        Returns:
            List of recent Session objects
        """
        return self.query_sessions(limit=count)


def main():
    """CLI entry point for session management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Maestro Session Lifecycle Manager"
    )
    parser.add_argument(
        "action",
        choices=["create", "get", "list", "delete", "transition"],
        help="Action to perform",
    )
    parser.add_argument("--session-id", help="Session ID (for get/delete/transition)")
    parser.add_argument("--feature-request", help="Feature request (for create)")
    parser.add_argument("--status", help="New status (for transition)")
    parser.add_argument("--branch", help="Filter by branch (for list)")
    parser.add_argument("--limit", type=int, default=10, help="Limit results (for list)")
    parser.add_argument("--output", choices=["json", "pretty"], default="json",
                        help="Output format")

    args = parser.parse_args()

    manager = SessionManager()

    if args.action == "create":
        if not args.feature_request:
            parser.error("--feature-request required for create action")

        session = manager.create_session(args.feature_request)
        output = session.to_dict()

    elif args.action == "get":
        if not args.session_id:
            parser.error("--session-id required for get action")

        session = manager.get_session(args.session_id)
        output = session.to_dict()

    elif args.action == "list":
        sessions = manager.query_sessions(
            branch=args.branch,
            limit=args.limit,
        )
        output = [s.to_dict() for s in sessions]

    elif args.action == "delete":
        if not args.session_id:
            parser.error("--session-id required for delete action")

        manager.delete_session(args.session_id)
        output = {"deleted": args.session_id}

    elif args.action == "transition":
        if not args.session_id:
            parser.error("--session-id required for transition action")
        if not args.status:
            parser.error("--status required for transition action")

        session = manager.transition_state(args.session_id, SessionStatus(args.status))
        output = session.to_dict()

    # Print output
    if args.output == "pretty":
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
