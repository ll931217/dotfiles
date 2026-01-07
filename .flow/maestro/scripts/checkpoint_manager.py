#!/usr/bin/env python3
"""
Maestro Checkpoint Manager

Handles git checkpoint creation, tracking, and restoration for safe rollback
during Maestro orchestration sessions. Uses git commits and tags to create
recovery points throughout the development lifecycle.
"""

import json
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from uuid import uuid4


class CheckpointType(str, Enum):
    """Types of checkpoints that can be created."""
    PHASE_COMPLETE = "phase_complete"
    TASK_GROUP_COMPLETE = "task_group_complete"
    SAFE_STATE = "safe_state"
    PRE_RISKY_OPERATION = "pre_risky_operation"
    ERROR_RECOVERY = "error_recovery"
    MANUAL = "manual"


class CheckpointPhase(str, Enum):
    """Session phases when checkpoints can be created."""
    PLAN = "plan"
    GENERATE_TASKS = "generate_tasks"
    IMPLEMENT = "implement"
    VALIDATE = "validate"
    CLEANUP = "cleanup"


@dataclass
class StateSnapshot:
    """Snapshot of session state at checkpoint time."""
    tasks_completed: int = 0
    decisions_made: int = 0
    files_modified: int = 0
    files_created: int = 0
    tests_passing: int = 0
    tests_failing: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Checkpoint:
    """A git checkpoint for rollback capability."""
    checkpoint_id: str
    commit_sha: str
    timestamp: str
    description: str
    phase: CheckpointPhase
    checkpoint_type: CheckpointType = CheckpointType.MANUAL
    commit_message: Optional[str] = None
    state_snapshot: Optional[StateSnapshot] = None
    tags: List[str] = field(default_factory=list)
    rollback_used: bool = False
    rollback_count: int = 0

    def __post_init__(self):
        """Convert string enums to enums if needed."""
        if isinstance(self.phase, str):
            self.phase = CheckpointPhase(self.phase)
        if isinstance(self.checkpoint_type, str):
            self.checkpoint_type = CheckpointType(self.checkpoint_type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for JSON serialization."""
        data = {
            "checkpoint_id": self.checkpoint_id,
            "commit_sha": self.commit_sha,
            "timestamp": self.timestamp,
            "description": self.description,
            "phase": self.phase.value,
            "checkpoint_type": self.checkpoint_type.value,
            "tags": self.tags,
            "rollback_used": self.rollback_used,
            "rollback_count": self.rollback_count,
        }

        # Add optional fields
        if self.commit_message:
            data["commit_message"] = self.commit_message
        if self.state_snapshot:
            data["state_snapshot"] = self.state_snapshot.to_dict()

        return data


@dataclass
class CheckpointSummary:
    """Summary statistics for checkpoints."""
    total_checkpoints: int = 0
    checkpoints_by_type: Dict[str, int] = field(default_factory=dict)
    checkpoints_used_for_rollback: int = 0
    latest_checkpoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ValidationResult:
    """Result of checkpoint state validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    git_status: Optional[str] = None
    has_uncommitted_changes: bool = False
    tests_passing: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CheckpointManager:
    """Manages git checkpoints for session rollback capability."""

    # Tag prefix for checkpoint tags
    TAG_PREFIX = "checkpoint-"

    def __init__(self, repo_root: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize checkpoint manager.

        Args:
            repo_root: Repository root path. If None, auto-detected from git.
            session_id: Session UUID for tracking checkpoints. Can be set later.
        """
        if repo_root:
            self.repo_root = Path(repo_root).absolute()
        else:
            self.repo_root = Path(__file__).parent.parent.parent.parent.absolute()

        self.session_id = session_id
        self.checkpoints_dir = self.repo_root / ".flow" / "maestro" / "sessions"
        self._ensure_checkpoints_dir()

    def _ensure_checkpoints_dir(self):
        """Create checkpoints directory if it doesn't exist."""
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_log_path(self, session_id: str) -> Path:
        """Get checkpoint log file path for a session."""
        session_dir = self.checkpoints_dir / session_id
        return session_dir / "checkpoints.json"

    def _generate_checkpoint_id(self) -> str:
        """Generate a unique checkpoint ID."""
        return str(uuid4())

    def _current_timestamp(self) -> str:
        """Get current ISO 8601 timestamp."""
        return datetime.utcnow().isoformat() + "Z"

    def _run_git_command(
        self,
        args: List[str],
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Run a git command in the repository.

        Args:
            args: Git command arguments
            capture_output: Whether to capture stdout/stderr

        Returns:
            CompletedProcess result

        Raises:
            subprocess.SubprocessError: If git command fails
        """
        cmd = ["git"] + args
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=self.repo_root,
        )

    def validate_checkpoint_state(self) -> ValidationResult:
        """
        Validate current repository state before creating checkpoint.

        Checks:
        - Git repository status
        - Uncommitted changes
        - Test suite status (if tests exist)

        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []
        git_status = None
        has_uncommitted_changes = False

        try:
            # Check git status
            status_result = self._run_git_command(["status", "--porcelain"])
            git_status = status_result.stdout.strip()
            has_uncommitted_changes = len(git_status) > 0

            if has_uncommitted_changes:
                warnings.append(
                    "Repository has uncommitted changes. "
                    "Consider committing before checkpoint."
                )

            # Check if we're in a git repository
            rev_parse_result = self._run_git_command(["rev-parse", "--git-dir"])
            if rev_parse_result.returncode != 0:
                errors.append("Not in a git repository")
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                )

        except (subprocess.SubprocessError, FileNotFoundError) as e:
            errors.append(f"Git command failed: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
            )

        # Check test status if pytest is available
        tests_passing = True
        try:
            test_result = self._run_git_command(
                ["pytest", "--collect-only", "-q"],
                capture_output=True,
            )
            # If pytest exists, try to run tests
            if test_result.returncode == 0:
                run_result = self._run_git_command(["pytest", "-x", "-q"])
                tests_passing = run_result.returncode == 0
                if not tests_passing:
                    warnings.append("Some tests are failing")
        except (subprocess.SubprocessError, FileNotFoundError):
            # No tests configured, not an error
            pass

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            git_status=git_status,
            has_uncommitted_changes=has_uncommitted_changes,
            tests_passing=tests_passing,
        )

    def create_checkpoint(
        self,
        session_id: str,
        description: str,
        phase: CheckpointPhase,
        checkpoint_type: CheckpointType = CheckpointType.MANUAL,
        state_snapshot: Optional[StateSnapshot] = None,
        commit_first: bool = True,
    ) -> Checkpoint:
        """
        Create a git checkpoint for rollback capability.

        Args:
            session_id: Session UUID
            description: Human-readable description of checkpoint state
            phase: Execution phase when checkpoint is created
            checkpoint_type: Type of checkpoint being created
            state_snapshot: Optional snapshot of session state
            commit_first: Whether to create a commit before tagging

        Returns:
            Created Checkpoint object

        Raises:
            ValueError: If validation fails or session_id not set
            subprocess.SubprocessError: If git commands fail
        """
        # Validate state first
        validation = self.validate_checkpoint_state()
        if not validation.is_valid:
            raise ValueError(
                f"Cannot create checkpoint: {', '.join(validation.errors)}"
            )

        # Commit any uncommitted changes if requested
        commit_sha = None
        commit_message = None

        if commit_first and validation.has_uncommitted_changes:
            commit_message = f"checkpoint: {description}"
            commit_result = self._run_git_command(
                ["commit", "-am", commit_message]
            )
            if commit_result.returncode != 0:
                raise ValueError(f"Failed to commit changes: {commit_result.stderr}")
            commit_sha = commit_result.stdout.strip()
        else:
            # Get current HEAD SHA
            rev_parse_result = self._run_git_command(["rev-parse", "HEAD"])
            if rev_parse_result.returncode != 0:
                raise ValueError("Failed to get current commit SHA")
            commit_sha = rev_parse_result.stdout.strip()

        # Create checkpoint object
        checkpoint_id = self._generate_checkpoint_id()
        timestamp = self._current_timestamp()

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            commit_sha=commit_sha,
            timestamp=timestamp,
            description=description,
            phase=phase,
            checkpoint_type=checkpoint_type,
            commit_message=commit_message,
            state_snapshot=state_snapshot,
        )

        # Create git tag
        tag_name = f"{self.TAG_PREFIX}{checkpoint_id}"
        tag_message = f"Checkpoint: {description}"

        tag_result = self._run_git_command(
            ["tag", "-a", tag_name, "-m", tag_message]
        )
        if tag_result.returncode != 0:
            raise ValueError(f"Failed to create tag: {tag_result.stderr}")

        checkpoint.tags.append(tag_name)

        # Save to checkpoint log
        self._save_checkpoint(session_id, checkpoint)

        return checkpoint

    def _save_checkpoint(self, session_id: str, checkpoint: Checkpoint):
        """Save checkpoint to session's checkpoint log."""
        log_path = self._get_checkpoint_log_path(session_id)
        session_dir = log_path.parent
        session_dir.mkdir(exist_ok=True)

        # Load existing log or create new
        if log_path.exists():
            with open(log_path) as f:
                data = json.load(f)
        else:
            data = {
                "session_id": session_id,
                "generated_at": self._current_timestamp(),
                "checkpoints": [],
                "summary": {
                    "total_checkpoints": 0,
                    "checkpoints_by_type": {},
                    "checkpoints_used_for_rollback": 0,
                    "latest_checkpoint": None,
                },
            }

        # Add checkpoint
        data["checkpoints"].append(checkpoint.to_dict())

        # Update summary
        data["summary"]["total_checkpoints"] += 1
        checkpoint_type = checkpoint.checkpoint_type.value
        data["summary"]["checkpoints_by_type"][checkpoint_type] = \
            data["summary"]["checkpoints_by_type"].get(checkpoint_type, 0) + 1
        data["summary"]["latest_checkpoint"] = checkpoint.commit_sha

        # Save to disk
        with open(log_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_checkpoint_log(self, session_id: str) -> Dict[str, Any]:
        """Load checkpoint log from disk."""
        log_path = self._get_checkpoint_log_path(session_id)

        if not log_path.exists():
            raise FileNotFoundError(f"No checkpoint log found for session: {session_id}")

        with open(log_path) as f:
            return json.load(f)

    def _dict_to_checkpoint(self, data: Dict[str, Any]) -> Checkpoint:
        """Convert dictionary to Checkpoint object."""
        state_snapshot = None
        if "state_snapshot" in data and data["state_snapshot"]:
            state_snapshot = StateSnapshot(**data["state_snapshot"])

        return Checkpoint(
            checkpoint_id=data["checkpoint_id"],
            commit_sha=data["commit_sha"],
            timestamp=data["timestamp"],
            description=data["description"],
            phase=data["phase"],
            checkpoint_type=data.get("checkpoint_type", "manual"),
            commit_message=data.get("commit_message"),
            state_snapshot=state_snapshot,
            tags=data.get("tags", []),
            rollback_used=data.get("rollback_used", False),
            rollback_count=data.get("rollback_count", 0),
        )

    def list_checkpoints(self, session_id: str) -> List[Checkpoint]:
        """
        List all checkpoints for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of Checkpoint objects, sorted by timestamp (newest first)

        Raises:
            FileNotFoundError: If session has no checkpoint log
        """
        log_data = self._load_checkpoint_log(session_id)

        checkpoints = [
            self._dict_to_checkpoint(cp_data)
            for cp_data in log_data["checkpoints"]
        ]

        # Sort by timestamp descending (newest first)
        checkpoints.sort(key=lambda cp: cp.timestamp, reverse=True)

        return checkpoints

    def get_checkpoint(self, session_id: str, checkpoint_id: str) -> Checkpoint:
        """
        Get a specific checkpoint by ID.

        Args:
            session_id: Session UUID
            checkpoint_id: Checkpoint UUID

        Returns:
            Checkpoint object

        Raises:
            FileNotFoundError: If checkpoint not found
        """
        checkpoints = self.list_checkpoints(session_id)

        for checkpoint in checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                return checkpoint

        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_id} in session {session_id}"
        )

    def rollback_to_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
        hard_reset: bool = False,
    ) -> bool:
        """
        Rollback repository to a previous checkpoint.

        Args:
            session_id: Session UUID
            checkpoint_id: Checkpoint UUID to rollback to
            hard_reset: If True, use --hard; otherwise use --mixed

        Returns:
            True if rollback succeeded

        Raises:
            FileNotFoundError: If checkpoint not found
            ValueError: If validation fails
            subprocess.SubprocessError: If git commands fail
        """
        # Get checkpoint
        checkpoint = self.get_checkpoint(session_id, checkpoint_id)

        # Validate current state
        validation = self.validate_checkpoint_state()
        if validation.has_uncommitted_changes:
            raise ValueError(
                "Cannot rollback with uncommitted changes. "
                "Commit or stash changes first."
            )

        # Perform git reset
        reset_mode = "--hard" if hard_reset else "--mixed"
        reset_result = self._run_git_command(
            ["reset", reset_mode, checkpoint.commit_sha]
        )

        if reset_result.returncode != 0:
            raise ValueError(f"Git reset failed: {reset_result.stderr}")

        # Update checkpoint metadata
        checkpoint.rollback_used = True
        checkpoint.rollback_count += 1

        # Update checkpoint log
        log_data = self._load_checkpoint_log(session_id)
        for i, cp_data in enumerate(log_data["checkpoints"]):
            if cp_data["checkpoint_id"] == checkpoint_id:
                log_data["checkpoints"][i]["rollback_used"] = True
                log_data["checkpoints"][i]["rollback_count"] = checkpoint.rollback_count
                break

        # Update summary
        log_data["summary"]["checkpoints_used_for_rollback"] += 1

        # Save updated log
        log_path = self._get_checkpoint_log_path(session_id)
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        return True

    def get_checkpoint_summary(self, session_id: str) -> CheckpointSummary:
        """
        Get summary statistics for session checkpoints.

        Args:
            session_id: Session UUID

        Returns:
            CheckpointSummary object

        Raises:
            FileNotFoundError: If session has no checkpoint log
        """
        log_data = self._load_checkpoint_log(session_id)
        summary_data = log_data.get("summary", {})

        return CheckpointSummary(
            total_checkpoints=summary_data.get("total_checkpoints", 0),
            checkpoints_by_type=summary_data.get("checkpoints_by_type", {}),
            checkpoints_used_for_rollback=summary_data.get(
                "checkpoints_used_for_rollback", 0
            ),
            latest_checkpoint=summary_data.get("latest_checkpoint"),
        )

    def delete_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
        delete_tag: bool = True,
    ) -> bool:
        """
        Delete a checkpoint from tracking.

        Args:
            session_id: Session UUID
            checkpoint_id: Checkpoint UUID to delete
            delete_tag: Whether to delete the git tag

        Returns:
            True if deletion succeeded

        Raises:
            FileNotFoundError: If checkpoint not found
        """
        checkpoint = self.get_checkpoint(session_id, checkpoint_id)

        # Delete git tag if requested
        if delete_tag and checkpoint.tags:
            for tag in checkpoint.tags:
                if tag.startswith(self.TAG_PREFIX):
                    self._run_git_command(["tag", "-d", tag])

        # Remove from checkpoint log
        log_data = self._load_checkpoint_log(session_id)
        original_count = len(log_data["checkpoints"])
        log_data["checkpoints"] = [
            cp for cp in log_data["checkpoints"]
            if cp["checkpoint_id"] != checkpoint_id
        ]

        if len(log_data["checkpoints"]) == original_count:
            raise FileNotFoundError(f"Checkpoint not found in log: {checkpoint_id}")

        # Update summary
        log_data["summary"]["total_checkpoints"] -= 1
        checkpoint_type = checkpoint.checkpoint_type.value
        log_data["summary"]["checkpoints_by_type"][checkpoint_type] = \
            log_data["summary"]["checkpoints_by_type"].get(checkpoint_type, 1) - 1

        # Update latest checkpoint if needed
        if log_data["checkpoints"]:
            log_data["summary"]["latest_checkpoint"] = \
                log_data["checkpoints"][-1]["commit_sha"]
        else:
            log_data["summary"]["latest_checkpoint"] = None

        # Save updated log
        log_path = self._get_checkpoint_log_path(session_id)
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        return True


def main():
    """CLI entry point for checkpoint management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Maestro Checkpoint Manager"
    )
    parser.add_argument(
        "action",
        choices=["create", "list", "get", "rollback", "delete", "validate"],
        help="Action to perform",
    )
    parser.add_argument("--session-id", required=True, help="Session ID")
    parser.add_argument("--checkpoint-id", help="Checkpoint ID (for get/rollback/delete)")
    parser.add_argument("--description", help="Checkpoint description (for create)")
    parser.add_argument(
        "--phase",
        choices=["plan", "generate_tasks", "implement", "validate", "cleanup"],
        help="Execution phase (for create)",
    )
    parser.add_argument(
        "--checkpoint-type",
        choices=[
            "phase_complete",
            "task_group_complete",
            "safe_state",
            "pre_risky_operation",
            "error_recovery",
            "manual",
        ],
        default="manual",
        help="Checkpoint type (for create)",
    )
    parser.add_argument(
        "--hard-reset",
        action="store_true",
        help="Use hard reset for rollback",
    )
    parser.add_argument(
        "--output",
        choices=["json", "pretty"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    manager = CheckpointManager()

    if args.action == "create":
        if not args.description:
            parser.error("--description required for create action")
        if not args.phase:
            parser.error("--phase required for create action")

        checkpoint = manager.create_checkpoint(
            args.session_id,
            args.description,
            CheckpointPhase(args.phase),
            CheckpointType(args.checkpoint_type),
        )
        output = checkpoint.to_dict()

    elif args.action == "list":
        checkpoints = manager.list_checkpoints(args.session_id)
        output = [cp.to_dict() for cp in checkpoints]

    elif args.action == "get":
        if not args.checkpoint_id:
            parser.error("--checkpoint-id required for get action")

        checkpoint = manager.get_checkpoint(args.session_id, args.checkpoint_id)
        output = checkpoint.to_dict()

    elif args.action == "rollback":
        if not args.checkpoint_id:
            parser.error("--checkpoint-id required for rollback action")

        success = manager.rollback_to_checkpoint(
            args.session_id,
            args.checkpoint_id,
            hard_reset=args.hard_reset,
        )
        output = {
            "success": success,
            "rolled_back_to": args.checkpoint_id,
        }

    elif args.action == "delete":
        if not args.checkpoint_id:
            parser.error("--checkpoint-id required for delete action")

        success = manager.delete_checkpoint(args.session_id, args.checkpoint_id)
        output = {
            "success": success,
            "deleted": args.checkpoint_id,
        }

    elif args.action == "validate":
        validation = manager.validate_checkpoint_state()
        output = validation.to_dict()

    # Print output
    if args.output == "pretty":
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
