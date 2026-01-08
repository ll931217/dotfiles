#!/usr/bin/env python3
"""
Maestro Checkpoint Manager

Handles git checkpoint creation, tracking, and restoration for safe rollback
during Maestro orchestration sessions. Uses git commits and tags to create
recovery points throughout the development lifecycle.
"""

import json
import logging
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from uuid import uuid4

# Setup logger
logger = logging.getLogger("maestro.checkpoint")


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


@dataclass
class RollbackOperation:
    """Details of a rollback operation for logging and tracking."""
    operation_id: str
    timestamp: str
    session_id: str
    checkpoint_id: str
    checkpoint_description: str
    checkpoint_sha: str
    rollback_mode: str  # "hard" or "mixed"
    pre_rollback_head: str
    post_rollback_head: str
    validation_passed: bool
    state_snapshot_restored: Optional[StateSnapshot] = None
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.state_snapshot_restored:
            data["state_snapshot_restored"] = self.state_snapshot_restored.to_dict()
        return data


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
        log_rollback: bool = True,
    ) -> RollbackOperation:
        """
        Rollback repository to a previous checkpoint with comprehensive logging and validation.

        This critical safeguard method restores the repository to a known good state,
        validates the rollback was successful, and logs all operations for audit trail.

        Args:
            session_id: Session UUID
            checkpoint_id: Checkpoint UUID to rollback to
            hard_reset: If True, use --hard reset (discard all changes); otherwise use --mixed
            log_rollback: Whether to log the rollback operation to session history

        Returns:
            RollbackOperation object with detailed rollback information

        Raises:
            FileNotFoundError: If checkpoint not found
            ValueError: If validation fails or uncommitted changes present
            subprocess.SubprocessError: If git commands fail
        """
        operation_id = str(uuid4())
        timestamp = self._current_timestamp()

        logger.info(
            f"Starting rollback operation {operation_id} to checkpoint {checkpoint_id}"
        )

        try:
            # Get checkpoint details
            checkpoint = self.get_checkpoint(session_id, checkpoint_id)
            logger.info(
                f"Rolling back to checkpoint: {checkpoint.description} "
                f"(SHA: {checkpoint.commit_sha[:8]})"
            )

            # Capture pre-rollback state
            pre_rollback_result = self._run_git_command(["rev-parse", "HEAD"])
            pre_rollback_head = pre_rollback_result.stdout.strip()
            logger.info(f"Pre-rollback HEAD: {pre_rollback_head[:8]}")

            # Validate current state before rollback (skip for hard reset)
            if not hard_reset:
                validation = self.validate_checkpoint_state()
                if validation.has_uncommitted_changes:
                    error_msg = (
                        "Cannot rollback with uncommitted changes. "
                        "Commit or stash changes first."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            # Perform git reset
            reset_mode = "hard" if hard_reset else "mixed"
            logger.info(f"Executing git reset --{reset_mode} {checkpoint.commit_sha[:8]}")

            reset_result = self._run_git_command(
                ["reset", f"--{reset_mode}", checkpoint.commit_sha]
            )

            if reset_result.returncode != 0:
                error_msg = f"Git reset failed: {reset_result.stderr}"
                logger.error(error_msg)
                # Create failed rollback operation record
                failed_op = RollbackOperation(
                    operation_id=operation_id,
                    timestamp=timestamp,
                    session_id=session_id,
                    checkpoint_id=checkpoint_id,
                    checkpoint_description=checkpoint.description,
                    checkpoint_sha=checkpoint.commit_sha,
                    rollback_mode=reset_mode,
                    pre_rollback_head=pre_rollback_head,
                    post_rollback_head=pre_rollback_head,
                    validation_passed=False,
                    success=False,
                    error_message=error_msg,
                )
                if log_rollback:
                    self._log_rollback_operation(failed_op)
                raise ValueError(error_msg)

            # Capture post-rollback state
            post_rollback_result = self._run_git_command(["rev-parse", "HEAD"])
            post_rollback_head = post_rollback_result.stdout.strip()
            logger.info(f"Post-rollback HEAD: {post_rollback_head[:8]}")

            # Post-rollback validation: Verify HEAD matches checkpoint SHA
            validation_errors = []
            validation_warnings = []
            validation_passed = True

            if post_rollback_head != checkpoint.commit_sha:
                validation_passed = False
                error_msg = (
                    f"Post-rollback validation failed: HEAD {post_rollback_head[:8]} "
                    f"does not match checkpoint SHA {checkpoint.commit_sha[:8]}"
                )
                validation_errors.append(error_msg)
                logger.error(error_msg)

            # Validate working directory state
            post_validation = self.validate_checkpoint_state()
            if post_validation.has_uncommitted_changes:
                validation_warnings.append(
                    "Working directory has uncommitted changes after rollback"
                )
                logger.warning("Uncommitted changes detected after rollback")

            if not post_validation.tests_passing:
                validation_warnings.append(
                    "Tests were failing at rollback point"
                )
                logger.warning("Rolling back to a state with failing tests")

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

            # Create rollback operation record
            rollback_op = RollbackOperation(
                operation_id=operation_id,
                timestamp=timestamp,
                session_id=session_id,
                checkpoint_id=checkpoint_id,
                checkpoint_description=checkpoint.description,
                checkpoint_sha=checkpoint.commit_sha,
                rollback_mode=reset_mode,
                pre_rollback_head=pre_rollback_head,
                post_rollback_head=post_rollback_head,
                validation_passed=validation_passed,
                state_snapshot_restored=checkpoint.state_snapshot,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                success=validation_passed,
            )

            # Log rollback operation
            if log_rollback:
                self._log_rollback_operation(rollback_op)

            if validation_passed:
                logger.info(
                    f"Rollback operation {operation_id} completed successfully. "
                    f"Repository restored to checkpoint: {checkpoint.description}"
                )
            else:
                logger.warning(
                    f"Rollback operation {operation_id} completed with validation warnings"
                )

            return rollback_op

        except Exception as e:
            logger.exception(f"Rollback operation {operation_id} failed with exception")
            raise

    def _log_rollback_operation(self, rollback_op: RollbackOperation) -> None:
        """
        Log rollback operation to session history for audit trail.

        Args:
            rollback_op: RollbackOperation object to log
        """
        session_dir = self.checkpoints_dir / rollback_op.session_id
        session_dir.mkdir(exist_ok=True)

        rollback_log_path = session_dir / "rollback_history.json"

        # Load existing log or create new
        if rollback_log_path.exists():
            with open(rollback_log_path) as f:
                log_data = json.load(f)
        else:
            log_data = {
                "session_id": rollback_op.session_id,
                "generated_at": self._current_timestamp(),
                "rollback_operations": [],
            }

        # Add rollback operation
        log_data["rollback_operations"].append(rollback_op.to_dict())
        log_data["last_updated"] = self._current_timestamp()

        # Save to disk
        with open(rollback_log_path, "w") as f:
            json.dump(log_data, f, indent=2)

        logger.info(
            f"Rollback operation {rollback_op.operation_id} logged to "
            f"{rollback_log_path}"
        )

    def get_rollback_history(self, session_id: str) -> List[RollbackOperation]:
        """
        Retrieve rollback history for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of RollbackOperation objects, sorted by timestamp (newest first)

        Raises:
            FileNotFoundError: If no rollback history exists for session
        """
        session_dir = self.checkpoints_dir / session_id
        rollback_log_path = session_dir / "rollback_history.json"

        if not rollback_log_path.exists():
            return []

        with open(rollback_log_path) as f:
            log_data = json.load(f)

        rollback_ops = []
        for op_data in log_data.get("rollback_operations", []):
            # Reconstruct StateSnapshot if present
            snapshot = None
            if op_data.get("state_snapshot_restored"):
                snapshot = StateSnapshot(**op_data["state_snapshot_restored"])

            rollback_ops.append(
                RollbackOperation(
                    operation_id=op_data["operation_id"],
                    timestamp=op_data["timestamp"],
                    session_id=op_data["session_id"],
                    checkpoint_id=op_data["checkpoint_id"],
                    checkpoint_description=op_data["checkpoint_description"],
                    checkpoint_sha=op_data["checkpoint_sha"],
                    rollback_mode=op_data["rollback_mode"],
                    pre_rollback_head=op_data["pre_rollback_head"],
                    post_rollback_head=op_data["post_rollback_head"],
                    validation_passed=op_data["validation_passed"],
                    state_snapshot_restored=snapshot,
                    validation_errors=op_data.get("validation_errors", []),
                    validation_warnings=op_data.get("validation_warnings", []),
                    success=op_data.get("success", True),
                    error_message=op_data.get("error_message"),
                )
            )

        # Sort by timestamp descending (newest first)
        rollback_ops.sort(key=lambda op: op.timestamp, reverse=True)
        return rollback_ops

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

    def create_pre_operation_checkpoint(
        self,
        session_id: str,
        operation_type: str,
        operation_description: str,
        phase: Optional[CheckpointPhase] = None,
        state_snapshot: Optional[StateSnapshot] = None,
    ) -> Checkpoint:
        """
        Create a checkpoint before executing a risky operation.

        This specialized checkpoint method captures the repository state before
        potentially dangerous operations, ensuring safe rollback capability.

        Args:
            session_id: Session UUID
            operation_type: Type of operation (e.g., 'git_push', 'file_deletion')
            operation_description: Human-readable description of the operation
            phase: Optional execution phase (defaults to IMPLEMENT)
            state_snapshot: Optional snapshot of current session state

        Returns:
            Created Checkpoint object with PRE_RISKY_OPERATION type

        Raises:
            ValueError: If validation fails
            subprocess.SubprocessError: If git commands fail
        """
        if phase is None:
            phase = CheckpointPhase.IMPLEMENT

        # Enhanced description with operation context
        full_description = (
            f"Pre-operation checkpoint before {operation_type}: "
            f"{operation_description}"
        )

        logger.info(
            f"Creating pre-operation checkpoint for {operation_type}: "
            f"{operation_description}"
        )

        # For pre-operation checkpoints, always commit uncommitted changes first
        # to ensure a clean rollback point
        validation = self.validate_checkpoint_state()

        if validation.has_uncommitted_changes:
            logger.info("Committing uncommitted changes before creating checkpoint")
            commit_message = f"checkpoint: Auto-commit before {operation_type}"
            commit_result = self._run_git_command(
                ["commit", "-am", commit_message]
            )
            if commit_result.returncode != 0:
                logger.warning(f"Failed to auto-commit: {commit_result.stderr}")
                # Continue anyway - we'll use current HEAD

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
            description=full_description,
            phase=phase,
            checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
            commit_message=commit_message if validation.has_uncommitted_changes else None,
            state_snapshot=state_snapshot,
        )

        # Store operation context in checkpoint metadata
        checkpoint.operation_context = {
            "operation_type": operation_type,
            "operation_description": operation_description,
            "created_at": self._current_timestamp(),
        }

        # Create git tag
        tag_name = f"{self.TAG_PREFIX}{checkpoint_id}"
        tag_message = f"Pre-operation Checkpoint: {operation_type} - {operation_description}"

        tag_result = self._run_git_command(
            ["tag", "-a", tag_name, "-m", tag_message]
        )
        if tag_result.returncode != 0:
            raise ValueError(f"Failed to create tag: {tag_result.stderr}")

        checkpoint.tags.append(tag_name)

        # Save to checkpoint log
        self._save_checkpoint(session_id, checkpoint)

        logger.info(
            f"Pre-operation checkpoint created: {checkpoint.checkpoint_id[:8]} "
            f"(SHA: {checkpoint.commit_sha[:8]})"
        )

        return checkpoint

    def should_trigger_rollback(
        self,
        error_context: Dict[str, Any],
        attempts: int,
        max_attempts: int = 3,
    ) -> bool:
        """
        Determine if a rollback should be triggered based on error context.

        Rollback is triggered when:
        - All recovery strategies are exhausted (attempts >= max_attempts)
        - Resource exhaustion with partial progress
        - Validation failure after N attempts
        - Unrecoverable errors (permanent failures)

        Args:
            error_context: Dictionary containing error details
                - error_category: Error category (transient/permanent/ambiguous)
                - error_type: Specific error type
                - has_partial_progress: Whether operation made partial progress
                - resource_exhausted: Whether resources were exhausted
                - validation_failed: Whether validation failed
            attempts: Number of recovery attempts already made
            max_attempts: Maximum recovery attempts before rollback (default: 3)

        Returns:
            True if rollback should be triggered
        """
        # Check if we've exhausted recovery attempts
        if attempts >= max_attempts:
            logger.warning(
                f"Recovery attempts exhausted ({attempts}/{max_attempts}), "
                "triggering rollback"
            )
            return True

        # Check for permanent errors (should rollback immediately)
        error_category = error_context.get("error_category", "").lower()
        if error_category == "permanent":
            logger.warning(
                f"Permanent error detected: {error_context.get('error_type')}, "
                "triggering rollback"
            )
            return True

        # Check for resource exhaustion with partial progress
        if error_context.get("resource_exhausted") and error_context.get("has_partial_progress"):
            logger.warning(
                "Resource exhaustion with partial progress detected, "
                "triggering rollback"
            )
            return True

        # Check for validation failures after multiple attempts
        if error_context.get("validation_failed") and attempts >= 2:
            logger.warning(
                f"Validation failed after {attempts} attempts, triggering rollback"
            )
            return True

        # Check for unrecoverable specific error types
        error_type = error_context.get("error_type", "").lower()
        unrecoverable_errors = [
            "disk_full",
            "permission_denied",
            "corruption",
            "database_connection_lost",
            "network_partition",
        ]

        if any(err in error_type for err in unrecoverable_errors):
            logger.warning(
                f"Unrecoverable error type detected: {error_type}, "
                "triggering rollback"
            )
            return True

        return False

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
        choices=["create", "list", "get", "rollback", "rollback_history", "delete", "validate"],
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

        rollback_op = manager.rollback_to_checkpoint(
            args.session_id,
            args.checkpoint_id,
            hard_reset=args.hard_reset,
        )
        output = rollback_op.to_dict()

    elif args.action == "rollback_history":
        rollback_history = manager.get_rollback_history(args.session_id)
        output = [op.to_dict() for op in rollback_history]

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
