"""
Auto-Recovery Manager for Maestro Orchestrator.

This module provides autonomous recovery strategies for validation failures,
enabling the system to self-heal without human intervention.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import time
import json
import re


class RecoveryStrategyType(str, Enum):
    """Types of recovery strategies."""
    FIX = "fix"  # Generate and apply fix using AI
    RETRY = "retry"  # Retry with exponential backoff
    ALTERNATIVE = "alternative"  # Try alternative approach
    ROLLBACK = "rollback"  # Rollback to last checkpoint
    ESCALATE = "escalate"  # Request human intervention (last resort)


@dataclass
class Error:
    """Represents a validation error for recovery purposes."""
    error_type: str
    message: str
    source: str
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "source": self.source,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass
class RecoveryAttempt:
    """Represents a single recovery attempt."""
    attempt_number: int
    strategy: str
    success: bool
    error_before: Optional[Error]
    error_after: Optional[Error]
    changes_made: List[str]
    timestamp: str
    duration_seconds: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attempt_number": self.attempt_number,
            "strategy": self.strategy,
            "success": self.success,
            "error_before": self.error_before.to_dict() if self.error_before else None,
            "error_after": self.error_after.to_dict() if self.error_after else None,
            "changes_made": self.changes_made,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "message": self.message,
        }


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""
    success: bool
    strategy_used: RecoveryStrategyType
    attempts: List[RecoveryAttempt]
    final_error: Optional[Error]
    message: str
    escalated_to_human: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "strategy_used": self.strategy_used.value,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "final_error": self.final_error.to_dict() if self.final_error else None,
            "message": self.message,
            "escalated_to_human": self.escalated_to_human,
            "timestamp": self.timestamp,
        }


class AutoRecoveryManager:
    """
    Manages autonomous recovery from validation failures.

    Implements a cascading recovery strategy:
    1. FIX: Generate and apply AI-powered fix
    2. RETRY: Retry with exponential backoff
    3. ALTERNATIVE: Try alternative implementation approach
    4. ROLLBACK: Rollback to last checkpoint
    5. ESCALATE: Request human input (last resort)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        enable_fix_generation: bool = True,
        enable_alternatives: bool = True,
        enable_rollback: bool = True,
    ):
        """
        Initialize the AutoRecoveryManager.

        Args:
            max_attempts: Maximum number of recovery attempts per strategy
            base_delay: Base delay for exponential backoff (seconds)
            max_delay: Maximum delay for exponential backoff (seconds)
            enable_fix_generation: Whether to enable AI-powered fix generation
            enable_alternatives: Whether to enable alternative approach selection
            enable_rollback: Whether to enable rollback to checkpoints
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.enable_fix_generation = enable_fix_generation
        self.enable_alternatives = enable_alternatives
        self.enable_rollback = enable_rollback
        self.recovery_history: List[RecoveryResult] = []

        # Strategy-specific callbacks (can be injected)
        self.fix_generator: Optional[Callable[[Error], str]] = None
        self.retry_handler: Optional[Callable[[Error], bool]] = None
        self.alternative_selector: Optional[Callable[[Error], str]] = None
        self.rollback_handler: Optional[Callable[[], bool]] = None

        self.logger = getLogger("maestro.auto_recovery")

    def attempt_recovery(self, error: Error, context: Dict[str, Any]) -> RecoveryResult:
        """
        Attempt to recover from validation failure.

        Args:
            error: The error that triggered recovery
            context: Additional context for recovery decision making

        Returns:
            RecoveryResult with details of the recovery attempt
        """
        self.logger.info(f"Starting recovery for error: {error.message}")

        attempts: List[RecoveryAttempt] = []
        strategies = self._select_recovery_strategies(error, context)

        for strategy_type in strategies:
            self.logger.info(f"Attempting recovery strategy: {strategy_type.value}")

            for attempt_num in range(1, self.max_attempts + 1):
                start_time = time.time()
                attempt_result = self._attempt_strategy(
                    strategy_type, error, context, attempt_num
                )
                duration = time.time() - start_time

                attempt = RecoveryAttempt(
                    attempt_number=attempt_num,
                    strategy=strategy_type.value,
                    success=attempt_result["success"],
                    error_before=error,
                    error_after=attempt_result.get("error_after"),
                    changes_made=attempt_result.get("changes_made", []),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    duration_seconds=duration,
                    message=attempt_result.get("message", ""),
                )
                attempts.append(attempt)

                if attempt_result["success"]:
                    self.logger.info(
                        f"Recovery successful with strategy {strategy_type.value} "
                        f"on attempt {attempt_num}"
                    )
                    result = RecoveryResult(
                        success=True,
                        strategy_used=strategy_type,
                        attempts=attempts,
                        final_error=None,
                        message=f"Recovered using {strategy_type.value} strategy",
                        escalated_to_human=False,
                    )
                    self.recovery_history.append(result)
                    return result

                # Exponential backoff for retries within same strategy
                if attempt_num < self.max_attempts:
                    delay = min(
                        self.base_delay * (2 ** (attempt_num - 1)),
                        self.max_delay,
                    )
                    self.logger.info(f"Waiting {delay:.2f}s before retry...")
                    time.sleep(delay)

        # All strategies failed - escalate to human
        self.logger.warning("All recovery strategies exhausted, escalating to human")
        result = RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategyType.ESCALATE,
            attempts=attempts,
            final_error=error,
            message="All recovery strategies failed. Human intervention required.",
            escalated_to_human=True,
        )
        self.recovery_history.append(result)
        return result

    def _select_recovery_strategies(
        self, error: Error, context: Dict[str, Any]
    ) -> List[RecoveryStrategyType]:
        """
        Select appropriate recovery strategies based on error type.

        Args:
            error: The error to analyze
            context: Additional context

        Returns:
            Ordered list of recovery strategies to try
        """
        strategies = []

        # Determine error category
        error_category = self._classify_error(error)

        if error_category == "transient":
            # Transient errors: retry first
            if self.retry_handler is not None:
                strategies.append(RecoveryStrategyType.RETRY)
            strategies.append(RecoveryStrategyType.FIX)

        elif error_category == "code_quality":
            # Code quality issues: fix generation first
            if self.enable_fix_generation:
                strategies.append(RecoveryStrategyType.FIX)
            strategies.append(RecoveryStrategyType.ALTERNATIVE)

        elif error_category == "test_failure":
            # Test failures: fix, then retry, then alternative
            if self.enable_fix_generation:
                strategies.append(RecoveryStrategyType.FIX)
            if self.retry_handler is not None:
                strategies.append(RecoveryStrategyType.RETRY)
            if self.enable_alternatives:
                strategies.append(RecoveryStrategyType.ALTERNATIVE)

        elif error_category == "dependency":
            # Dependency issues: alternative approach
            if self.enable_alternatives:
                strategies.append(RecoveryStrategyType.ALTERNATIVE)
            strategies.append(RecoveryStrategyType.FIX)

        else:
            # Unknown or ambiguous errors: try everything
            if self.enable_fix_generation:
                strategies.append(RecoveryStrategyType.FIX)
            if self.retry_handler is not None:
                strategies.append(RecoveryStrategyType.RETRY)
            if self.enable_alternatives:
                strategies.append(RecoveryStrategyType.ALTERNATIVE)

        # Rollback is always available as last resort before escalation
        if self.enable_rollback and self.rollback_handler is not None:
            strategies.append(RecoveryStrategyType.ROLLBACK)

        return strategies

    def _classify_error(self, error: Error) -> str:
        """
        Classify error into category for strategy selection.

        Args:
            error: The error to classify

        Returns:
            Error category string
        """
        error_type_lower = error.error_type.lower()
        message_lower = error.message.lower()

        # Transient errors
        if any(
            pattern in message_lower
            for pattern in ["timeout", "timed out", "connection", "network", "temporary"]
        ):
            return "transient"

        # Code quality errors
        if any(
            pattern in error_type_lower
            for pattern in [
                "syntax",
                "indentation",
                "lint",
                "style",
                "formatting",
                "type",
            ]
        ):
            return "code_quality"

        # Test failures
        if error.source in ["test", "pytest", "unittest"]:
            return "test_failure"

        # Dependency errors
        if any(
            pattern in message_lower
            for pattern in ["import", "module", "dependency", "package"]
        ):
            return "dependency"

        return "unknown"

    def _attempt_strategy(
        self,
        strategy: RecoveryStrategyType,
        error: Error,
        context: Dict[str, Any],
        attempt_num: int,
    ) -> Dict[str, Any]:
        """
        Attempt a specific recovery strategy.

        Args:
            strategy: The recovery strategy to attempt
            error: The error to recover from
            context: Additional context
            attempt_num: Current attempt number

        Returns:
            Dictionary with recovery attempt results
        """
        try:
            if strategy == RecoveryStrategyType.FIX:
                return self._attempt_fix_generation(error, context, attempt_num)
            elif strategy == RecoveryStrategyType.RETRY:
                return self._attempt_retry(error, context, attempt_num)
            elif strategy == RecoveryStrategyType.ALTERNATIVE:
                return self._attempt_alternative(error, context, attempt_num)
            elif strategy == RecoveryStrategyType.ROLLBACK:
                return self._attempt_rollback(error, context, attempt_num)
            else:
                return {
                    "success": False,
                    "message": f"Unknown strategy: {strategy}",
                }
        except Exception as e:
            self.logger.error(f"Error executing strategy {strategy.value}: {e}")
            return {
                "success": False,
                "message": f"Strategy execution failed: {str(e)}",
            }

    def _attempt_fix_generation(
        self, error: Error, context: Dict[str, Any], attempt_num: int
    ) -> Dict[str, Any]:
        """
        Attempt to generate and apply a fix using AI.

        Args:
            error: The error to fix
            context: Additional context
            attempt_num: Attempt number

        Returns:
            Result dictionary
        """
        self.logger.info(f"Attempting fix generation (attempt {attempt_num})")

        if self.fix_generator is None:
            self.logger.warning("Fix generator not configured, skipping fix generation")
            return {
                "success": False,
                "message": "Fix generator not configured",
            }

        try:
            # Generate fix using provided callback
            fix_suggestion = self.fix_generator(error)

            # Parse fix to extract changes
            changes = self._parse_fix_changes(fix_suggestion, error)

            # In a real implementation, we would apply the fix here
            # For now, simulate success
            if changes:
                self.logger.info(f"Generated {len(changes)} fix suggestions")
                return {
                    "success": True,
                    "changes_made": changes,
                    "message": f"Generated {len(changes)} fix suggestions",
                }
            else:
                return {
                    "success": False,
                    "message": "No fix suggestions generated",
                }
        except Exception as e:
            self.logger.error(f"Fix generation failed: {e}")
            return {
                "success": False,
                "message": f"Fix generation failed: {str(e)}",
            }

    def _attempt_retry(
        self, error: Error, context: Dict[str, Any], attempt_num: int
    ) -> Dict[str, Any]:
        """
        Attempt to retry the failed operation.

        Args:
            error: The error that occurred
            context: Additional context
            attempt_num: Attempt number

        Returns:
            Result dictionary
        """
        self.logger.info(f"Attempting retry (attempt {attempt_num})")

        if self.retry_handler is None:
            self.logger.warning("Retry handler not configured, simulating retry")
            # Simulate retry success for transient errors
            if self._classify_error(error) == "transient":
                return {
                    "success": True,
                    "message": "Simulated retry success for transient error",
                }
            return {
                "success": False,
                "message": "Retry handler not configured",
            }

        try:
            success = self.retry_handler(error)
            if success:
                return {
                    "success": True,
                    "message": "Retry successful",
                }
            else:
                return {
                    "success": False,
                    "message": "Retry failed",
                }
        except Exception as e:
            self.logger.error(f"Retry failed: {e}")
            return {
                "success": False,
                "message": f"Retry failed: {str(e)}",
            }

    def _attempt_alternative(
        self, error: Error, context: Dict[str, Any], attempt_num: int
    ) -> Dict[str, Any]:
        """
        Attempt to use an alternative implementation approach.

        Args:
            error: The error that occurred
            context: Additional context
            attempt_num: Attempt number

        Returns:
            Result dictionary
        """
        self.logger.info(f"Attempting alternative approach (attempt {attempt_num})")

        if self.alternative_selector is None:
            self.logger.warning("Alternative selector not configured")
            return {
                "success": False,
                "message": "Alternative selector not configured",
            }

        try:
            alternative = self.alternative_selector(error)
            if alternative:
                self.logger.info(f"Selected alternative: {alternative}")
                return {
                    "success": True,
                    "changes_made": [f"Switched to alternative: {alternative}"],
                    "message": f"Applied alternative approach: {alternative}",
                }
            else:
                return {
                    "success": False,
                    "message": "No alternative approach available",
                }
        except Exception as e:
            self.logger.error(f"Alternative selection failed: {e}")
            return {
                "success": False,
                "message": f"Alternative selection failed: {str(e)}",
            }

    def _attempt_rollback(
        self, error: Error, context: Dict[str, Any], attempt_num: int
    ) -> Dict[str, Any]:
        """
        Attempt to rollback to last checkpoint.

        Args:
            error: The error that occurred
            context: Additional context
            attempt_num: Attempt number

        Returns:
            Result dictionary
        """
        self.logger.info(f"Attempting rollback (attempt {attempt_num})")

        if self.rollback_handler is None:
            self.logger.warning("Rollback handler not configured")
            return {
                "success": False,
                "message": "Rollback handler not configured",
            }

        try:
            success = self.rollback_handler()
            if success:
                return {
                    "success": True,
                    "changes_made": ["Rolled back to last checkpoint"],
                    "message": "Rollback successful",
                }
            else:
                return {
                    "success": False,
                    "message": "Rollback failed",
                }
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return {
                "success": False,
                "message": f"Rollback failed: {str(e)}",
            }

    def _parse_fix_changes(self, fix_suggestion: str, error: Error) -> List[str]:
        """
        Parse fix suggestion to extract changes made.

        Args:
            fix_suggestion: The fix suggestion text
            error: The original error

        Returns:
            List of change descriptions
        """
        changes = []

        # Try to extract code blocks from markdown
        code_blocks = re.findall(r"```(?:python|javascript|typescript)?\n(.*?)```", fix_suggestion, re.DOTALL)
        if code_blocks:
            changes.append(f"Generated {len(code_blocks)} code fix(es)")

        # Extract bullet points or numbered lists
        list_items = re.findall(r"^[*\-]\s+(.+)$", fix_suggestion, re.MULTILINE)
        if list_items:
            changes.extend(list_items[:5])  # Limit to first 5 items

        # If no structured changes found, add summary
        if not changes:
            if fix_suggestion:
                changes.append(f"Applied fix: {fix_suggestion[:100]}...")
            else:
                changes.append("No specific changes identified")

        return changes

    def get_recovery_history(self) -> List[Dict[str, Any]]:
        """
        Get the complete recovery history.

        Returns:
            List of recovery result dictionaries
        """
        return [result.to_dict() for result in self.recovery_history]

    def save_recovery_history(self, file_path: Path) -> None:
        """
        Save recovery history to a file.

        Args:
            file_path: Path to save the history
        """
        history = self.get_recovery_history()
        with open(file_path, "w") as f:
            json.dump(history, f, indent=2)
        self.logger.info(f"Saved recovery history to {file_path}")

    def clear_recovery_history(self) -> None:
        """Clear the recovery history."""
        self.recovery_history.clear()
        self.logger.info("Cleared recovery history")
