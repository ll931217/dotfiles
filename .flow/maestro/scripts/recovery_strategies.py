#!/usr/bin/env python3
"""
Maestro Recovery Strategies

Provides retry with exponential backoff, alternative approach selection,
rollback to checkpoint, and human input request strategies for handling
failures during Maestro orchestration sessions.
"""

import json
import subprocess
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
import sys


class RecoveryStrategyType(str, Enum):
    """Recovery strategy types."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    ALTERNATIVE_APPROACH = "alternative_approach"
    ROLLBACK_TO_CHECKPOINT = "rollback_to_checkpoint"
    REQUEST_HUMAN_INPUT = "request_human_input"


class CheckpointType(str, Enum):
    """Checkpoint types matching the JSON schema."""
    PHASE_COMPLETE = "phase_complete"
    TASK_GROUP_COMPLETE = "task_group_complete"
    SAFE_STATE = "safe_state"
    PRE_RISKY_OPERATION = "pre_risky_operation"
    ERROR_RECOVERY = "error_recovery"
    MANUAL = "manual"


@dataclass
class RetryConfig:
    """Configuration for retry with backoff."""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RetryResult:
    """Result from a retry attempt."""
    success: bool
    attempts_made: int
    total_time_seconds: float
    final_error: Optional[str] = None
    result: Optional[Any] = None


@dataclass
class AlternativeApproach:
    """Alternative approach for failed operations."""
    approach_id: str
    name: str
    description: str
    implementation_pattern: str
    required_changes: List[str] = field(default_factory=list)
    risk_level: str = "medium"  # low, medium, high


@dataclass
class Checkpoint:
    """Git checkpoint for rollback capability."""
    checkpoint_id: str
    commit_sha: str
    timestamp: str
    description: str
    phase: str
    checkpoint_type: CheckpointType
    commit_message: Optional[str] = None
    state_snapshot: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    rollback_used: bool = False
    rollback_count: int = 0


@dataclass
class HumanInputRequest:
    """Structured request for human input."""
    request_id: str
    issue_description: str
    context: Dict[str, Any]
    options: List[str]
    default_option: Optional[str] = None
    requires_justification: bool = False
    timeout_seconds: Optional[int] = None


@dataclass
class RecoveryResult:
    """Result from recovery strategy execution."""
    strategy_used: RecoveryStrategyType
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class RecoveryStrategies:
    """
    Main recovery strategies class.

    Provides four recovery strategies:
    1. Retry with exponential backoff
    2. Alternative approach selection
    3. Rollback to checkpoint
    4. Human input request
    """

    # Predefined alternative approaches for common failure scenarios
    ALTERNATIVE_APPROACHES = {
        "test_failure": [
            AlternativeApproach(
                approach_id="tdd_fix",
                name="Test-Driven Fix",
                description="Fix failing tests by implementing minimal code to pass",
                implementation_pattern="tdd",
                required_changes=["update_implementation", "run_tests", "verify_passing"],
                risk_level="low"
            ),
            AlternativeApproach(
                approach_id="mock_dependencies",
                name="Mock External Dependencies",
                description="Mock external dependencies that cause test flakiness",
                implementation_pattern="mocking",
                required_changes=["create_mocks", "update_tests", "verify_isolation"],
                risk_level="low"
            ),
            AlternativeApproach(
                approach_id="refactor_test",
                name="Refactor Test Logic",
                description="Refactor test logic to be more robust",
                implementation_pattern="refactoring",
                required_changes=["analyze_test", "refactor_assertions", "verify_clarity"],
                risk_level="medium"
            ),
        ],
        "implementation_failure": [
            AlternativeApproach(
                approach_id="simplify_implementation",
                name="Simplify Implementation",
                description="Break down complex implementation into smaller steps",
                implementation_pattern="incremental",
                required_changes=["decompose_task", "implement_stepwise", "integrate"],
                risk_level="low"
            ),
            AlternativeApproach(
                approach_id="use_library",
                name="Use Established Library",
                description="Replace custom implementation with well-tested library",
                implementation_pattern="library_replacement",
                required_changes=["identify_library", "replace_code", "adapt_tests"],
                risk_level="low"
            ),
            AlternativeApproach(
                approach_id="change_pattern",
                name="Change Design Pattern",
                description="Switch to a different design pattern better suited for task",
                implementation_pattern="pattern_switch",
                required_changes=["analyze_pattern", "select_alternative", "refactor"],
                risk_level="high"
            ),
        ],
        "dependency_conflict": [
            AlternativeApproach(
                approach_id="update_dependencies",
                name="Update Dependencies",
                description="Update conflicting dependencies to compatible versions",
                implementation_pattern="dependency_update",
                required_changes=["check_versions", "update_manifest", "resolve_conflicts"],
                risk_level="medium"
            ),
            AlternativeApproach(
                approach_id="use_shim_layer",
                name="Use Shim Layer",
                description="Create abstraction layer to isolate conflicting dependencies",
                implementation_pattern="adapter",
                required_changes=["design_shim", "implement_adapter", "update_callers"],
                risk_level="medium"
            ),
            AlternativeApproach(
                approach_id="replace_dependency",
                name="Replace Conflicting Dependency",
                description="Find and use alternative dependency without conflicts",
                implementation_pattern="replacement",
                required_changes=["find_alternative", "migrate_code", "update_tests"],
                risk_level="high"
            ),
        ],
    }

    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize recovery strategies.

        Args:
            repo_root: Repository root path. If None, auto-detected from git.
        """
        if repo_root:
            self.repo_root = Path(repo_root).absolute()
        else:
            self.repo_root = Path(__file__).parent.parent.parent.parent.absolute()

        self.checkpoints_dir = self.repo_root / ".flow" / "maestro" / "checkpoints"
        self._ensure_checkpoints_dir()

    def _ensure_checkpoints_dir(self):
        """Create checkpoints directory if it doesn't exist."""
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_file(self, session_id: str) -> Path:
        """Get checkpoint file path for a session."""
        return self.checkpoints_dir / f"{session_id}.json"

    def _generate_checkpoint_id(self) -> str:
        """Generate a unique checkpoint ID."""
        return f"cp-{int(datetime.utcnow().timestamp())}"

    def _calculate_backoff(self, attempt: int, config: RetryConfig) -> float:
        """
        Calculate exponential backoff delay with optional jitter.

        Args:
            attempt: Current attempt number (1-indexed)
            config: Retry configuration

        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff: base_delay * (base ^ (attempt - 1))
        delay = config.base_delay_seconds * (config.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, config.max_delay_seconds)

        # Add jitter if enabled (±25% randomness)
        if config.jitter:
            import random
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def retry_with_backoff(
        self,
        operation: Callable,
        config: Optional[RetryConfig] = None,
        operation_name: str = "operation",
        retry_on: Tuple = (Exception,),
    ) -> RetryResult:
        """
        Execute operation with exponential backoff retry strategy.

        Args:
            operation: Callable to execute
            config: Retry configuration (uses defaults if None)
            operation_name: Human-readable name for logging
            retry_on: Tuple of exception types to retry on

        Returns:
            RetryResult with success status and metadata

        Example:
            >>> result = strategies.retry_with_backoff(
            ...     lambda: subprocess.run(["pytest"], check=True),
            ...     operation_name="run tests",
            ...     config=RetryConfig(max_attempts=5)
            ... )
            >>> if result.success:
            ...     print(f"Success after {result.attempts_made} attempts")
        """
        if config is None:
            config = RetryConfig()

        start_time = time.time()
        last_error = None

        for attempt in range(1, config.max_attempts + 1):
            try:
                # Execute operation
                result = operation()

                # Success
                elapsed = time.time() - start_time
                return RetryResult(
                    success=True,
                    attempts_made=attempt,
                    total_time_seconds=elapsed,
                    result=result,
                )

            except Exception as e:
                # Check if this exception type should be retried
                should_retry = isinstance(e, retry_on)

                if should_retry:
                    last_error = e
                    elapsed = time.time() - start_time

                    # Check if we should retry
                    if attempt < config.max_attempts:
                        # Calculate backoff delay
                        delay = self._calculate_backoff(attempt, config)

                        print(
                            f"[Retry] {operation_name} failed (attempt {attempt}/{config.max_attempts}): {e}",
                            file=sys.stderr,
                        )
                        print(f"[Retry] Waiting {delay:.2f}s before retry...", file=sys.stderr)

                        # Wait before retry
                        time.sleep(delay)
                    else:
                        # Final attempt failed
                        print(
                            f"[Retry] {operation_name} failed after {attempt} attempts",
                            file=sys.stderr,
                        )
                else:
                    # Exception not in retry_on, fail immediately
                    return RetryResult(
                        success=False,
                        attempts_made=attempt,
                        total_time_seconds=time.time() - start_time,
                        final_error=str(e),
                    )

        # All retry attempts exhausted (only reached if we exhausted retries)
        return RetryResult(
            success=False,
            attempts_made=config.max_attempts,
            total_time_seconds=time.time() - start_time,
            final_error=str(last_error),
        )

    def try_alternative_approach(
        self,
        context: Dict[str, Any],
        failure_info: Dict[str, Any],
    ) -> RecoveryResult:
        """
        Select and attempt alternative approach for failed operation.

        Args:
            context: Execution context including task type, phase, etc.
            failure_info: Details about the failure (error type, message, etc.)

        Returns:
            RecoveryResult with approach suggestions and status

        Example:
            >>> result = strategies.try_alternative_approach(
            ...     context={"task_type": "test_failure"},
            ...     failure_info={"error": "AssertionError: test fails intermittently"}
            ... )
            >>> if result.success:
            ...     print(f"Suggested approach: {result.details['approach_name']}")
        """
        # Determine failure category
        failure_type = self._categorize_failure(failure_info)

        # Get alternative approaches for this failure type
        approaches = self.ALTERNATIVE_APPROACHES.get(failure_type, [])

        if not approaches:
            return RecoveryResult(
                strategy_used=RecoveryStrategyType.ALTERNATIVE_APPROACH,
                success=False,
                message=f"No alternative approaches available for failure type: {failure_type}",
                details={"failure_type": failure_type},
            )

        # Select best approach based on context
        selected_approach = self._select_approach(approaches, context, failure_info)

        return RecoveryResult(
            strategy_used=RecoveryStrategyType.ALTERNATIVE_APPROACH,
            success=True,
            message=f"Recommended alternative approach: {selected_approach.name}",
            details={
                "approach_id": selected_approach.approach_id,
                "approach_name": selected_approach.name,
                "description": selected_approach.description,
                "implementation_pattern": selected_approach.implementation_pattern,
                "required_changes": selected_approach.required_changes,
                "risk_level": selected_approach.risk_level,
                "failure_type": failure_type,
                "all_available_approaches": [
                    {
                        "id": a.approach_id,
                        "name": a.name,
                        "risk_level": a.risk_level,
                    }
                    for a in approaches
                ],
            },
        )

    def _categorize_failure(self, failure_info: Dict[str, Any]) -> str:
        """
        Categorize failure into known types.

        Args:
            failure_info: Failure details

        Returns:
            Failure type string
        """
        error_message = failure_info.get("error", "").lower()
        error_type = failure_info.get("error_type", "").lower()

        # Check for test failures
        if any(keyword in error_message for keyword in ["test", "assert", "pytest", "unittest"]):
            return "test_failure"

        # Check for implementation failures
        if any(keyword in error_message for keyword in ["notimplemented", "attribute", "import"]):
            return "implementation_failure"

        # Check for dependency conflicts
        if any(keyword in error_message for keyword in ["dependency", "version", "conflict", "requirement"]):
            return "dependency_conflict"

        # Default
        return "test_failure"  # Most common fallback

    def _select_approach(
        self,
        approaches: List[AlternativeApproach],
        context: Dict[str, Any],
        failure_info: Dict[str, Any],
    ) -> AlternativeApproach:
        """
        Select best approach based on context and failure info.

        Args:
            approaches: List of available approaches
            context: Execution context
            failure_info: Failure details

        Returns:
            Selected AlternativeApproach
        """
        # Prefer low-risk approaches by default
        low_risk = [a for a in approaches if a.risk_level == "low"]
        if low_risk:
            return low_risk[0]

        # Fall back to first approach if no low-risk options
        return approaches[0]

    def create_checkpoint(
        self,
        session_id: str,
        description: str,
        phase: str,
        checkpoint_type: CheckpointType,
        state_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        """
        Create a git checkpoint for rollback capability.

        Args:
            session_id: Session identifier
            description: Human-readable description
            phase: Current execution phase
            checkpoint_type: Type of checkpoint
            state_snapshot: Optional state snapshot at checkpoint

        Returns:
            Created Checkpoint object

        Example:
            >>> checkpoint = strategies.create_checkpoint(
            ...     session_id="abc-123",
            ...     description="Before refactoring core module",
            ...     phase="implement",
            ...     checkpoint_type=CheckpointType.PRE_RISKY_OPERATION
            ... )
        """
        # Get current git state
        commit_info = self._get_current_commit()

        # Create checkpoint
        checkpoint = Checkpoint(
            checkpoint_id=self._generate_checkpoint_id(),
            commit_sha=commit_info["sha"],
            timestamp=datetime.utcnow().isoformat() + "Z",
            description=description,
            phase=phase,
            checkpoint_type=checkpoint_type,
            commit_message=commit_info["message"],
            state_snapshot=state_snapshot or {},
        )

        # Save checkpoint to file
        self._save_checkpoint(session_id, checkpoint)

        return checkpoint

    def _get_current_commit(self) -> Dict[str, str]:
        """Get current git commit information."""
        try:
            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                check=True,
            )
            sha = sha_result.stdout.strip()

            # Get commit message
            msg_result = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                check=True,
            )
            message = msg_result.stdout.strip()

            return {"sha": sha, "message": message}

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get git commit info: {e}")

    def _save_checkpoint(self, session_id: str, checkpoint: Checkpoint):
        """Save checkpoint to file."""
        checkpoint_file = self._get_checkpoint_file(session_id)

        # Load existing checkpoints or create new structure
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                data = json.load(f)
        else:
            data = {
                "session_id": session_id,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "checkpoints": [],
                "summary": {
                    "total_checkpoints": 0,
                    "checkpoints_by_type": {},
                    "checkpoints_used_for_rollback": 0,
                },
            }

        # Add new checkpoint
        checkpoint_dict = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "timestamp": checkpoint.timestamp,
            "commit_sha": checkpoint.commit_sha,
            "commit_message": checkpoint.commit_message,
            "description": checkpoint.description,
            "phase": checkpoint.phase,
            "checkpoint_type": checkpoint.checkpoint_type.value,
            "state_snapshot": checkpoint.state_snapshot,
            "tags": checkpoint.tags,
            "rollback_used": checkpoint.rollback_used,
            "rollback_count": checkpoint.rollback_count,
        }

        data["checkpoints"].append(checkpoint_dict)

        # Update summary
        data["summary"]["total_checkpoints"] += 1
        data["summary"]["latest_checkpoint"] = checkpoint.commit_sha

        cp_type = checkpoint.checkpoint_type.value
        data["summary"]["checkpoints_by_type"][cp_type] = \
            data["summary"]["checkpoints_by_type"].get(cp_type, 0) + 1

        # Save to file
        with open(checkpoint_file, "w") as f:
            json.dump(data, f, indent=2)

    def rollback_to_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
    ) -> bool:
        """
        Rollback repository to a previous checkpoint.

        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint to rollback to

        Returns:
            True if rollback successful, False otherwise

        Example:
            >>> success = strategies.rollback_to_checkpoint(
            ...     session_id="abc-123",
            ...     checkpoint_id="cp-1234567890"
            ... )
        """
        try:
            # Load checkpoint
            checkpoint = self._load_checkpoint(session_id, checkpoint_id)
            if not checkpoint:
                print(f"[Rollback] Checkpoint not found: {checkpoint_id}", file=sys.stderr)
                return False

            # Reset to checkpoint commit
            subprocess.run(
                ["git", "reset", "--hard", checkpoint.commit_sha],
                capture_output=True,
                cwd=self.repo_root,
                check=True,
            )

            # Update checkpoint metadata
            self._mark_checkpoint_rolled_back(session_id, checkpoint_id)

            print(
                f"[Rollback] Successfully rolled back to checkpoint {checkpoint_id}",
                f"(commit {checkpoint.commit_sha[:7]}): {checkpoint.description}",
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"[Rollback] Git reset failed: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[Rollback] Rollback failed: {e}", file=sys.stderr)
            return False

    def _load_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from file."""
        checkpoint_file = self._get_checkpoint_file(session_id)

        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file) as f:
            data = json.load(f)

        for cp_dict in data["checkpoints"]:
            if cp_dict["checkpoint_id"] == checkpoint_id:
                return Checkpoint(
                    checkpoint_id=cp_dict["checkpoint_id"],
                    commit_sha=cp_dict["commit_sha"],
                    timestamp=cp_dict["timestamp"],
                    description=cp_dict["description"],
                    phase=cp_dict["phase"],
                    checkpoint_type=CheckpointType(cp_dict["checkpoint_type"]),
                    commit_message=cp_dict.get("commit_message"),
                    state_snapshot=cp_dict.get("state_snapshot", {}),
                    tags=cp_dict.get("tags", []),
                    rollback_used=cp_dict.get("rollback_used", False),
                    rollback_count=cp_dict.get("rollback_count", 0),
                )

        return None

    def _mark_checkpoint_rolled_back(self, session_id: str, checkpoint_id: str):
        """Mark checkpoint as used for rollback."""
        checkpoint_file = self._get_checkpoint_file(session_id)

        if not checkpoint_file.exists():
            return

        with open(checkpoint_file) as f:
            data = json.load(f)

        # Find and update checkpoint
        for cp_dict in data["checkpoints"]:
            if cp_dict["checkpoint_id"] == checkpoint_id:
                cp_dict["rollback_used"] = True
                cp_dict["rollback_count"] = cp_dict.get("rollback_count", 0) + 1

        # Update summary
        data["summary"]["checkpoints_used_for_rollback"] = \
            sum(1 for cp in data["checkpoints"] if cp.get("rollback_used", False))

        # Save changes
        with open(checkpoint_file, "w") as f:
            json.dump(data, f, indent=2)

    def request_human_input(
        self,
        issue: str,
        options: List[str],
        context: Optional[Dict[str, Any]] = None,
        default_option: Optional[str] = None,
        requires_justification: bool = False,
    ) -> str:
        """
        Request structured human input for ambiguous situations.

        Args:
            issue: Description of the issue requiring human input
            options: List of possible options/solutions
            context: Optional context about the situation
            default_option: Default option if user just presses enter
            requires_justification: Whether to ask user for justification

        Returns:
            Selected option

        Example:
            >>> selected = strategies.request_human_input(
            ...     issue="Multiple design patterns available for this task",
            ...     options=["Use Factory Pattern", "Use Builder Pattern", "Use Prototype Pattern"],
            ...     default_option="Use Factory Pattern"
            ... )
        """
        request_id = f"req-{int(datetime.utcnow().timestamp())}"

        print("\n" + "=" * 70, file=sys.stderr)
        print("HUMAN INPUT REQUIRED", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"\nRequest ID: {request_id}", file=sys.stderr)
        print(f"\nIssue:\n{issue}\n", file=sys.stderr)

        if context:
            print("Context:", file=sys.stderr)
            for key, value in context.items():
                print(f"  {key}: {value}", file=sys.stderr)
            print()

        print("Available Options:", file=sys.stderr)
        for i, option in enumerate(options, 1):
            marker = " (default)" if option == default_option else ""
            print(f"  {i}. {option}{marker}", file=sys.stderr)
        print()

        while True:
            try:
                if default_option:
                    prompt = f"Select option [1-{len(options)}] (or press Enter for default): "
                else:
                    prompt = f"Select option [1-{len(options)}]: "

                response = input(prompt).strip()

                # Handle default
                if not response and default_option:
                    selected = default_option
                    print(f"\nSelected: {selected}\n", file=sys.stderr)
                    return selected

                # Handle numeric selection
                try:
                    index = int(response)
                    if 1 <= index <= len(options):
                        selected = options[index - 1]
                        print(f"\nSelected: {selected}\n", file=sys.stderr)

                        # Optionally request justification
                        if requires_justification:
                            justification = input("Justification (optional): ").strip()
                            if justification:
                                print(f"Justification: {justification}\n", file=sys.stderr)

                        return selected
                except ValueError:
                    pass

                print(f"Invalid selection. Please enter a number between 1 and {len(options)}", file=sys.stderr)

            except (EOFError, KeyboardInterrupt):
                print("\nInput interrupted. Using default option.", file=sys.stderr)
                if default_option:
                    return default_option
                # If no default, use first option
                return options[0]


def main():
    """CLI entry point for recovery strategies."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Maestro Recovery Strategies"
    )
    parser.add_argument(
        "action",
        choices=["checkpoint", "rollback", "approaches"],
        help="Action to perform",
    )
    parser.add_argument("--session-id", help="Session ID")
    parser.add_argument("--checkpoint-id", help="Checkpoint ID")
    parser.add_argument("--description", help="Checkpoint description")
    parser.add_argument("--phase", help="Execution phase")
    parser.add_argument("--type", help="Checkpoint type", default="manual")
    parser.add_argument("--failure-type", help="Failure type for alternative approaches")

    args = parser.parse_args()

    strategies = RecoveryStrategies()

    if args.action == "checkpoint":
        if not args.session_id or not args.description or not args.phase:
            parser.error("--session-id, --description, and --phase required for checkpoint action")

        checkpoint = strategies.create_checkpoint(
            session_id=args.session_id,
            description=args.description,
            phase=args.phase,
            checkpoint_type=CheckpointType(args.type),
        )

        output = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "commit_sha": checkpoint.commit_sha,
            "timestamp": checkpoint.timestamp,
        }

    elif args.action == "rollback":
        if not args.session_id or not args.checkpoint_id:
            parser.error("--session-id and --checkpoint-id required for rollback action")

        success = strategies.rollback_to_checkpoint(
            session_id=args.session_id,
            checkpoint_id=args.checkpoint_id,
        )

        output = {
            "success": success,
            "session_id": args.session_id,
            "checkpoint_id": args.checkpoint_id,
        }

    elif args.action == "approaches":
        if not args.failure_type:
            parser.error("--failure-type required for approaches action")

        result = strategies.try_alternative_approach(
            context={},
            failure_info={"error_type": args.failure_type},
        )

        output = {
            "failure_type": args.failure_type,
            "approaches": result.details.get("all_available_approaches", []),
        }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
