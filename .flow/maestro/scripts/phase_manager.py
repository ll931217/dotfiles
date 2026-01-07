#!/usr/bin/env python3
"""
Maestro Phase Manager - Orchestrates phase transitions in the workflow

Manages state transitions between workflow phases:
- Initialization
- Planning (PRD generation)
- Task Generation
- Implementation
- Validation
- Report Generation
- Completion

Each phase has preconditions, execution logic, and postconditions.
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
sys.path.insert(0, str(maestro_root / "scripts"))
sys.path.insert(0, str(maestro_root / "decision-engine" / "scripts"))

from session_manager import SessionManager, SessionStatus
from decision_logger import DecisionLogger
from error_handler import ErrorHandler
from checkpoint_manager import CheckpointManager, CheckpointType, CheckpointPhase


class Phase(Enum):
    """Workflow phases in order of execution."""

    INITIALIZATION = "initialization"
    PLANNING = "planning"
    TASK_GENERATION = "task_generation"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PhaseResult:
    """Result of phase execution."""

    phase: Phase
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    checkpoint: Optional[str] = None


@dataclass
class PhaseConfig:
    """Configuration for a phase."""

    name: Phase
    required_state: SessionStatus
    next_phases: List[Phase]
    create_checkpoint: bool = False
    checkpoint_type: Optional[CheckpointType] = None
    allow_retry: bool = True
    max_retries: int = 3


class PhaseTransitionError(Exception):
    """Raised when phase transition fails."""

    pass


# Map Phase enum to CheckpointPhase enum
PHASE_TO_CHECKPOINT_PHASE = {
    Phase.INITIALIZATION: CheckpointPhase.PLAN,
    Phase.PLANNING: CheckpointPhase.PLAN,
    Phase.TASK_GENERATION: CheckpointPhase.GENERATE_TASKS,
    Phase.IMPLEMENTATION: CheckpointPhase.IMPLEMENT,
    Phase.VALIDATION: CheckpointPhase.VALIDATE,
    Phase.REPORT_GENERATION: CheckpointPhase.CLEANUP,
    Phase.COMPLETED: CheckpointPhase.CLEANUP,
}


class PhaseManager:
    """
    Manages workflow phase transitions with validation and error handling.

    Ensures proper state progression, validates preconditions, and creates
    checkpoints at critical transition points.
    """

    # Phase configurations
    PHASE_CONFIGS = {
        Phase.INITIALIZATION: PhaseConfig(
            name=Phase.INITIALIZATION,
            required_state=SessionStatus.INITIALIZING,
            next_phases=[Phase.PLANNING],
            create_checkpoint=True,
            checkpoint_type=CheckpointType.PRE_RISKY_OPERATION,
        ),
        Phase.PLANNING: PhaseConfig(
            name=Phase.PLANNING,
            required_state=SessionStatus.PLANNING,
            next_phases=[Phase.TASK_GENERATION],
            create_checkpoint=False,
        ),
        Phase.TASK_GENERATION: PhaseConfig(
            name=Phase.TASK_GENERATION,
            required_state=SessionStatus.GENERATING_TASKS,
            next_phases=[Phase.IMPLEMENTATION],
            create_checkpoint=False,
        ),
        Phase.IMPLEMENTATION: PhaseConfig(
            name=Phase.IMPLEMENTATION,
            required_state=SessionStatus.IMPLEMENTING,
            next_phases=[Phase.VALIDATION],
            create_checkpoint=True,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
        ),
        Phase.VALIDATION: PhaseConfig(
            name=Phase.VALIDATION,
            required_state=SessionStatus.VALIDATING,
            next_phases=[Phase.REPORT_GENERATION, Phase.PLANNING],  # Can loop back
            create_checkpoint=False,
        ),
        Phase.REPORT_GENERATION: PhaseConfig(
            name=Phase.REPORT_GENERATION,
            required_state=SessionStatus.GENERATING_REPORT,
            next_phases=[Phase.COMPLETED],
            create_checkpoint=False,
        ),
        Phase.COMPLETED: PhaseConfig(
            name=Phase.COMPLETED,
            required_state=SessionStatus.COMPLETED,
            next_phases=[],
            create_checkpoint=True,
            checkpoint_type=CheckpointType.MANUAL,
        ),
        Phase.FAILED: PhaseConfig(
            name=Phase.FAILED,
            required_state=SessionStatus.FAILED,
            next_phases=[],
            create_checkpoint=False,
            allow_retry=False,
        ),
    }

    def __init__(self, project_root: Path, session_id: str):
        """
        Initialize Phase Manager.

        Args:
            project_root: Root directory of the project
            session_id: Current session ID
        """
        self.project_root = Path(project_root).resolve()
        self.session_id = session_id

        # Initialize components
        self.session_manager = SessionManager(self.project_root)
        self.decision_logger = DecisionLogger(self.project_root)
        self.error_handler = ErrorHandler(self.project_root)
        self.checkpoint_manager = CheckpointManager(self.project_root)

        # Setup logging
        self.logger = logging.getLogger(f"maestro.phasemanager.{session_id[:8]}")

        # Track current phase
        self.current_phase: Optional[Phase] = None

    def can_transition_to(self, target_phase: Phase) -> bool:
        """
        Check if transition to target phase is valid.

        Args:
            target_phase: Phase to transition to

        Returns:
            True if transition is valid
        """
        if self.current_phase is None:
            # Check session status for initial transition
            session = self.session_manager.get_session(self.session_id)
            if session:
                # Map SessionStatus to valid initial phases
                status_to_phase = {
                    SessionStatus.INITIALIZING: Phase.INITIALIZATION,
                    SessionStatus.PLANNING: Phase.PLANNING,
                    SessionStatus.GENERATING_TASKS: Phase.TASK_GENERATION,
                    SessionStatus.IMPLEMENTING: Phase.IMPLEMENTATION,
                    SessionStatus.VALIDATING: Phase.VALIDATION,
                    SessionStatus.GENERATING_REPORT: Phase.REPORT_GENERATION,
                }
                expected_phase = status_to_phase.get(session.status)
                # Can transition to expected phase or its next phases
                if expected_phase:
                    if target_phase == expected_phase:
                        return True
                    # Check if target is a next phase from expected
                    expected_config = self.PHASE_CONFIGS.get(expected_phase)
                    if expected_config and target_phase in expected_config.next_phases:
                        return True
            return False

        current_config = self.PHASE_CONFIGS.get(self.current_phase)
        if not current_config:
            return False

        return target_phase in current_config.next_phases

    def validate_preconditions(self, phase: Phase) -> tuple[bool, List[str]]:
        """
        Validate preconditions for entering a phase.

        Args:
            phase: Phase to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check if transition is valid
        if not self.can_transition_to(phase):
            errors.append(f"Cannot transition from {self.current_phase} to {phase}")
            return False, errors

        # Get session state
        session = self.session_manager.get_session(self.session_id)
        if not session:
            errors.append(f"Session {self.session_id} not found")
            return False, errors

        # Check required state
        phase_config = self.PHASE_CONFIGS[phase]
        # Allow phase if session status matches (for initial phase)
        # OR if we're already in a phase that can transition to this one
        status_matches = session.status.value == phase_config.required_state.value

        # When current_phase is set, check if the transition is valid via can_transition_to
        # The session state will be updated by transition_to(), so we don't need to check it now
        if not status_matches and self.current_phase is not None:
            # If we have a current phase, can_transition_to already validated the path
            # We just need to make sure the target phase's required state is reachable
            pass

        if not status_matches and self.current_phase is None:
            # No current phase but status doesn't match - this is an error
            errors.append(
                f"Session state {session.status.value} does not match "
                f"required state {phase_config.required_state.value}"
            )
            return False, errors

        return True, errors

    def execute_phase(
        self,
        phase: Phase,
        execute_func: Callable[[], Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> PhaseResult:
        """
        Execute a phase with validation and checkpointing.

        Args:
            phase: Phase to execute
            execute_func: Function that executes phase logic
            context: Optional context for phase execution

        Returns:
            PhaseResult with execution outcome
        """
        self.logger.info(f"Executing phase: {phase.value}")

        # Validate preconditions
        is_valid, errors = self.validate_preconditions(phase)
        if not is_valid:
            self.logger.error(f"Phase validation failed: {errors}")
            return PhaseResult(
                phase=phase,
                success=False,
                errors=errors,
            )

        # Update current phase
        previous_phase = self.current_phase
        self.current_phase = phase

        try:
            # Execute phase logic
            result_data = execute_func()

            # Create checkpoint if configured
            checkpoint = None
            phase_config = self.PHASE_CONFIGS[phase]
            if phase_config.create_checkpoint:
                checkpoint = self.checkpoint_manager.create_checkpoint(
                    session_id=self.session_id,
                    description=f"Checkpoint after {phase.value} phase",
                    phase=PHASE_TO_CHECKPOINT_PHASE[phase],
                    checkpoint_type=phase_config.checkpoint_type,
                    state_snapshot={
                        "phase": phase.value,
                        "previous_phase": previous_phase.value if previous_phase else None,
                        "context": context or {},
                    },
                )
                self.logger.info(f"Checkpoint created: {checkpoint['commit_sha'][:8]}")

            # Log phase completion
            # Convert any Path objects to strings for JSON serialization
            safe_context = context.copy() if context else {}
            if "phase" in safe_context:
                safe_context["phase"] = str(safe_context["phase"])

            self.decision_logger.log_decision(
                decision_type="checkpoint",
                decision={
                    "decision": f"Phase completed: {phase.value}",
                    "rationale": f"Successfully executed {phase.value} phase",
                    "phase": phase.value,
                    "checkpoint": checkpoint["commit_sha"] if checkpoint else None,
                },
            )

            return PhaseResult(
                phase=phase,
                success=True,
                data=result_data,
                checkpoint=checkpoint["commit_sha"] if checkpoint else None,
            )

        except Exception as e:
            self.logger.error(f"Phase execution failed: {e}")

            # Handle error with error handler
            error_info = {
                "phase": phase.value,
                "error": str(e),
                "context": context or {},
            }

            # Attempt recovery
            recovery_result = self._attempt_phase_recovery(phase, error_info)

            if not recovery_result.get("recovered", False):
                # Transition to failed state
                self.session_manager.transition_state(
                    session_id=self.session_id,
                    new_state=SessionStatus.FAILED,
                )
                self.current_phase = Phase.FAILED

            return PhaseResult(
                phase=phase,
                success=recovery_result.get("recovered", False),
                errors=[str(e)],
            )

    def transition_to(self, target_phase: Phase, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition to target phase without executing.

        Args:
            target_phase: Phase to transition to
            context: Optional transition context

        Returns:
            True if transition successful
        """
        # Validate preconditions
        is_valid, errors = self.validate_preconditions(target_phase)
        if not is_valid:
            self.logger.error(f"Transition validation failed: {errors}")
            return False

        # Update session state
        phase_config = self.PHASE_CONFIGS[target_phase]
        self.session_manager.transition_state(
            session_id=self.session_id,
            new_state=phase_config.required_state,
        )

        # Update current phase
        self.current_phase = target_phase

        self.logger.info(f"Transitioned to phase: {target_phase.value}")
        return True

    def _attempt_phase_recovery(self, phase: Phase, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to recover from phase execution error.

        Args:
            phase: Phase that failed
            error_info: Error information

        Returns:
            Recovery result with 'recovered' boolean
        """
        self.logger.info(f"Attempting recovery for phase: {phase.value}")

        # Detect and classify error
        detected_error = self.error_handler.detect_error(
            output=error_info.get("error", ""),
            source=f"phase_{phase.value}",
            context=error_info.get("context", {}),
        )

        category = self.error_handler.classify_error(detected_error)
        strategy = self.error_handler.select_recovery_strategy(category)

        # Execute recovery strategy
        recovery_result = self.error_handler.execute_recovery(
            strategy=strategy,
            context={
                "session_id": self.session_id,
                "phase": phase.value,
                **error_info,
            },
        )

        return recovery_result

    def get_phase_progress(self) -> Dict[str, Any]:
        """
        Get current progress through phases.

        Returns:
            Dict with phase progress information
        """
        phase_order = [
            Phase.INITIALIZATION,
            Phase.PLANNING,
            Phase.TASK_GENERATION,
            Phase.IMPLEMENTATION,
            Phase.VALIDATION,
            Phase.REPORT_GENERATION,
            Phase.COMPLETED,
        ]

        current_index = (
            phase_order.index(self.current_phase)
            if self.current_phase in phase_order
            else -1
        )

        return {
            "current_phase": self.current_phase.value if self.current_phase else None,
            "progress_percent": int((current_index + 1) / len(phase_order) * 100)
            if current_index >= 0
            else 0,
            "completed_phases": [p.value for p in phase_order[: current_index + 1]]
            if current_index >= 0
            else [],
            "remaining_phases": [p.value for p in phase_order[current_index + 1 :]]
            if current_index >= 0
            else phase_order,
        }

    def get_next_phase(self) -> Optional[Phase]:
        """
        Get the next phase in the workflow.

        Returns:
            Next phase or None if at terminal phase
        """
        if self.current_phase is None:
            return Phase.PLANNING  # Start with planning when not initialized

        phase_config = self.PHASE_CONFIGS.get(self.current_phase)
        if not phase_config or not phase_config.next_phases:
            return None

        # Return first valid next phase
        return phase_config.next_phases[0]

    def can_retry_phase(self, phase: Phase) -> bool:
        """
        Check if phase can be retried after failure.

        Args:
            phase: Phase to check

        Returns:
            True if phase can be retried
        """
        phase_config = self.PHASE_CONFIGS.get(phase)
        return phase_config.allow_retry if phase_config else False

    def reset_to_phase(self, target_phase: Phase, rollback_checkpoint: Optional[str] = None) -> bool:
        """
        Reset workflow to a specific phase.

        Args:
            target_phase: Phase to reset to
            rollback_checkpoint: Optional checkpoint to rollback to

        Returns:
            True if reset successful
        """
        self.logger.info(f"Resetting to phase: {target_phase.value}")

        # Rollback to checkpoint if provided
        if rollback_checkpoint:
            try:
                self.checkpoint_manager.rollback_to_checkpoint(rollback_checkpoint)
                self.logger.info(f"Rolled back to checkpoint: {rollback_checkpoint[:8]}")
            except Exception as e:
                self.logger.error(f"Rollback failed: {e}")
                return False

        # Reset to target phase
        phase_config = self.PHASE_CONFIGS[target_phase]
        success = self.session_manager.transition_state(
            session_id=self.session_id,
            new_state=phase_config.required_state,
        )

        if success:
            self.current_phase = target_phase
            self.logger.info(f"Reset to phase: {target_phase.value}")

        return success


def main():
    """Example usage of PhaseManager."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python phase_manager.py <session-id>")
        sys.exit(1)

    project_root = Path.cwd()
    session_id = sys.argv[1]

    # Create phase manager
    manager = PhaseManager(project_root, session_id)

    # Example: Execute a phase
    def planning_execution():
        """Example planning phase execution."""
        return {"prd_generated": True, "prd_path": "/path/to/prd.md"}

    result = manager.execute_phase(
        phase=Phase.PLANNING,
        execute_func=planning_execution,
        context={"feature_request": "User authentication"},
    )

    print(f"Phase: {result.phase.value}")
    print(f"Success: {result.success}")
    print(f"Checkpoint: {result.checkpoint}")

    # Get progress
    progress = manager.get_phase_progress()
    print(f"Progress: {progress['progress_percent']}%")


if __name__ == "__main__":
    main()
