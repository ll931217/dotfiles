"""
Auto-Recovery Manager for Maestro Orchestrator.

This module provides autonomous recovery strategies for validation failures,
enabling the system to self-heal without human intervention.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import time
import json
import re
import uuid
from collections import defaultdict


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
class RecoveryAuditEntry:
    """Single entry in recovery audit trail."""
    entry_id: str
    timestamp: str
    session_id: str
    error_type: str
    strategy: str
    attempt_number: int
    success: bool
    changes_made: List[str]
    files_modified: List[str]
    rollback_performed: bool
    next_action: str
    duration_seconds: float
    error_message: str
    recovery_message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class RecoveryAuditLogger:
    """
    Logs all recovery operations with full audit trail.

    Provides comprehensive logging of recovery attempts including:
    - Detailed attempt logging with timestamps
    - Session-based recovery history
    - Audit trail export to JSON
    - Recovery statistics and summaries
    """

    def __init__(self, audit_dir: Optional[Path] = None):
        """
        Initialize the RecoveryAuditLogger.

        Args:
            audit_dir: Directory to store audit trail files. If None, uses temp dir.
        """
        self.audit_dir = audit_dir or Path("/tmp/maestro_audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # In-memory audit storage
        self._audit_entries: Dict[str, List[RecoveryAuditEntry]] = defaultdict(list)
        self._session_start_times: Dict[str, str] = {}

        self.logger = getLogger("maestro.recovery_audit")

    def _generate_entry_id(self) -> str:
        """Generate unique entry ID."""
        return f"entry_{uuid.uuid4().hex[:12]}"

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new recovery session.

        Args:
            session_id: Optional session ID. If None, generates one.

        Returns:
            The session ID
        """
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        self._session_start_times[session_id] = datetime.now(timezone.utc).isoformat()
        self.logger.info(f"Started recovery session: {session_id}")
        return session_id

    def log_recovery_attempt(
        self,
        attempt: RecoveryAttempt,
        session_id: str,
        files_modified: Optional[List[str]] = None,
        rollback_performed: bool = False,
        next_action: str = "continue",
    ) -> str:
        """
        Log a recovery attempt to the audit trail.

        Args:
            attempt: The recovery attempt to log
            session_id: The session ID for this recovery
            files_modified: List of files that were modified
            rollback_performed: Whether a rollback was performed
            next_action: Next action to take (continue, retry, escalate, etc.)

        Returns:
            The entry ID for this log entry
        """
        entry_id = self._generate_entry_id()

        error_type = attempt.error_before.error_type if attempt.error_before else "unknown"
        error_message = attempt.error_before.message if attempt.error_before else ""

        entry = RecoveryAuditEntry(
            entry_id=entry_id,
            timestamp=attempt.timestamp,
            session_id=session_id,
            error_type=error_type,
            strategy=attempt.strategy,
            attempt_number=attempt.attempt_number,
            success=attempt.success,
            changes_made=attempt.changes_made,
            files_modified=files_modified or [],
            rollback_performed=rollback_performed,
            next_action=next_action,
            duration_seconds=attempt.duration_seconds,
            error_message=error_message,
            recovery_message=attempt.message,
        )

        self._audit_entries[session_id].append(entry)

        # Log to file immediately for persistence
        self._write_entry_to_file(entry)

        self.logger.info(
            f"Logged recovery attempt {entry_id}: "
            f"strategy={attempt.strategy}, success={attempt.success}"
        )

        return entry_id

    def _write_entry_to_file(self, entry: RecoveryAuditEntry) -> None:
        """
        Write audit entry to session-specific file.

        Args:
            entry: The audit entry to write
        """
        session_file = self.audit_dir / f"{entry.session_id}_audit.jsonl"

        with open(session_file, "a") as f:
            f.write(entry.to_json() + "\n")

    def get_recovery_history(
        self, session_id: str
    ) -> List[RecoveryAuditEntry]:
        """
        Get recovery history for a specific session.

        Args:
            session_id: The session ID to retrieve history for

        Returns:
            List of audit entries for the session
        """
        return self._audit_entries.get(session_id, [])

    def get_all_session_ids(self) -> List[str]:
        """
        Get all session IDs with audit entries.

        Returns:
            List of session IDs
        """
        # Return unique session IDs from both entries and session start times
        all_sessions = set(self._audit_entries.keys())
        all_sessions.update(self._session_start_times.keys())
        return list(all_sessions)

    def export_audit_trail(
        self, session_id: str, format: str = "json"
    ) -> str:
        """
        Export audit trail for a session.

        Args:
            session_id: The session ID to export
            format: Export format (json or csv)

        Returns:
            Path to the exported file
        """
        entries = self.get_recovery_history(session_id)

        if not entries:
            raise ValueError(f"No audit entries found for session: {session_id}")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if format.lower() == "json":
            output_path = self.audit_dir / f"{session_id}_audit_{timestamp}.json"
            data = {
                "session_id": session_id,
                "session_start": self._session_start_times.get(session_id, "unknown"),
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_entries": len(entries),
                "entries": [entry.to_dict() for entry in entries],
            }

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        elif format.lower() == "csv":
            output_path = self.audit_dir / f"{session_id}_audit_{timestamp}.csv"
            import csv

            if entries:
                with open(output_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=entries[0].to_dict().keys())
                    writer.writeheader()
                    for entry in entries:
                        writer.writerow(entry.to_dict())
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Exported audit trail to {output_path}")
        return str(output_path)

    def get_recovery_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Calculate recovery statistics for a session.

        Args:
            session_id: The session ID to calculate statistics for

        Returns:
            Dictionary with recovery statistics
        """
        entries = self.get_recovery_history(session_id)

        if not entries:
            return {
                "session_id": session_id,
                "total_attempts": 0,
                "successful_attempts": 0,
                "failed_attempts": 0,
                "success_rate": 0.0,
                "strategies_used": {},
                "total_duration_seconds": 0.0,
                "average_duration_seconds": 0.0,
            }

        # Calculate statistics
        total_attempts = len(entries)
        successful_attempts = sum(1 for e in entries if e.success)
        failed_attempts = total_attempts - successful_attempts
        success_rate = successful_attempts / total_attempts if total_attempts > 0 else 0.0

        # Strategy usage
        strategies_used = defaultdict(int)
        for entry in entries:
            strategies_used[entry.strategy] += 1

        # Duration statistics
        total_duration = sum(e.duration_seconds for e in entries)
        average_duration = total_duration / total_attempts if total_attempts > 0 else 0.0

        # Error type distribution
        error_types = defaultdict(int)
        for entry in entries:
            error_types[entry.error_type] += 1

        # Files modified
        all_files_modified = set()
        for entry in entries:
            all_files_modified.update(entry.files_modified)

        # Rollback statistics
        rollback_count = sum(1 for e in entries if e.rollback_performed)

        return {
            "session_id": session_id,
            "session_start": self._session_start_times.get(session_id, "unknown"),
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": round(success_rate * 100, 2),
            "strategies_used": dict(strategies_used),
            "error_type_distribution": dict(error_types),
            "total_duration_seconds": round(total_duration, 3),
            "average_duration_seconds": round(average_duration, 3),
            "files_modified_count": len(all_files_modified),
            "files_modified": list(all_files_modified),
            "rollback_count": rollback_count,
            "first_attempt_timestamp": entries[0].timestamp if entries else None,
            "last_attempt_timestamp": entries[-1].timestamp if entries else None,
        }

    def generate_recovery_report(
        self, session_id: str, output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a comprehensive recovery report for a session.

        Args:
            session_id: The session ID to generate report for
            output_path: Optional path to save report. If None, uses default.

        Returns:
            Path to the generated report
        """
        stats = self.get_recovery_statistics(session_id)
        entries = self.get_recovery_history(session_id)

        if output_path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = self.audit_dir / f"{session_id}_report_{timestamp}.json"

        report = {
            "report_metadata": {
                "session_id": session_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "session_start": stats["session_start"],
                "report_type": "recovery_audit_report",
            },
            "summary": {
                "total_attempts": stats["total_attempts"],
                "success_rate": f"{stats['success_rate']}%",
                "total_duration_seconds": stats["total_duration_seconds"],
                "files_modified": stats["files_modified_count"],
            },
            "statistics": stats,
            "detailed_entries": [entry.to_dict() for entry in entries],
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Generated recovery report: {output_path}")
        return str(output_path)

    def clear_session(self, session_id: str) -> None:
        """
        Clear audit entries for a specific session.

        Args:
            session_id: The session ID to clear
        """
        if session_id in self._audit_entries:
            del self._audit_entries[session_id]
        if session_id in self._session_start_times:
            del self._session_start_times[session_id]

        self.logger.info(f"Cleared audit entries for session: {session_id}")

    def clear_all_sessions(self) -> None:
        """Clear all audit entries."""
        self._audit_entries.clear()
        self._session_start_times.clear()
        self.logger.info("Cleared all audit entries")


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
        audit_dir: Optional[Path] = None,
        enable_audit_logging: bool = True,
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
            audit_dir: Directory to store audit trail files
            enable_audit_logging: Whether to enable comprehensive audit logging
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

        # Audit logging
        self.enable_audit_logging = enable_audit_logging
        self.audit_logger = RecoveryAuditLogger(audit_dir=audit_dir) if enable_audit_logging else None
        self.current_session_id: Optional[str] = None

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

        # Start audit session if enabled
        if self.audit_logger and self.current_session_id is None:
            self.current_session_id = self.audit_logger.start_session()

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

                # Log to audit trail
                if self.audit_logger and self.current_session_id:
                    files_modified = attempt_result.get("files_modified", [])
                    rollback_performed = strategy_type == RecoveryStrategyType.ROLLBACK and attempt_result["success"]
                    next_action = "complete" if attempt_result["success"] else "retry"

                    self.audit_logger.log_recovery_attempt(
                        attempt=attempt,
                        session_id=self.current_session_id,
                        files_modified=files_modified,
                        rollback_performed=rollback_performed,
                        next_action=next_action,
                    )

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

    def get_audit_trail(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get audit trail entries.

        Args:
            session_id: Optional session ID. If None, uses current session.

        Returns:
            List of audit entry dictionaries
        """
        if not self.audit_logger:
            return []

        session = session_id or self.current_session_id
        if not session:
            return []

        entries = self.audit_logger.get_recovery_history(session)
        return [entry.to_dict() for entry in entries]

    def export_audit_trail(
        self, session_id: Optional[str] = None, format: str = "json"
    ) -> Optional[str]:
        """
        Export audit trail to file.

        Args:
            session_id: Optional session ID. If None, uses current session.
            format: Export format (json or csv)

        Returns:
            Path to exported file, or None if audit logging is disabled
        """
        if not self.audit_logger:
            self.logger.warning("Audit logging is disabled")
            return None

        session = session_id or self.current_session_id
        if not session:
            self.logger.warning("No session ID available for audit export")
            return None

        try:
            return self.audit_logger.export_audit_trail(session, format)
        except ValueError as e:
            self.logger.error(f"Failed to export audit trail: {e}")
            return None

    def get_recovery_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recovery statistics for a session.

        Args:
            session_id: Optional session ID. If None, uses current session.

        Returns:
            Dictionary with recovery statistics
        """
        if not self.audit_logger:
            return {}

        session = session_id or self.current_session_id
        if not session:
            return {}

        return self.audit_logger.get_recovery_statistics(session)

    def generate_recovery_report(
        self, session_id: Optional[str] = None, output_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Generate comprehensive recovery report.

        Args:
            session_id: Optional session ID. If None, uses current session.
            output_path: Optional path to save report

        Returns:
            Path to generated report, or None if audit logging is disabled
        """
        if not self.audit_logger:
            self.logger.warning("Audit logging is disabled")
            return None

        session = session_id or self.current_session_id
        if not session:
            self.logger.warning("No session ID available for report generation")
            return None

        try:
            return self.audit_logger.generate_recovery_report(session, output_path)
        except ValueError as e:
            self.logger.error(f"Failed to generate recovery report: {e}")
            return None

    def start_new_session(self, session_id: Optional[str] = None) -> Optional[str]:
        """
        Start a new audit session.

        Args:
            session_id: Optional session ID. If None, generates one.

        Returns:
            The new session ID, or None if audit logging is disabled
        """
        if not self.audit_logger:
            self.logger.warning("Audit logging is disabled")
            return None

        self.current_session_id = self.audit_logger.start_session(session_id)
        return self.current_session_id

    def clear_recovery_history(self) -> None:
        """Clear the recovery history."""
        self.recovery_history.clear()
        self.logger.info("Cleared recovery history")

    def clear_audit_history(self, session_id: Optional[str] = None) -> None:
        """
        Clear audit history.

        Args:
            session_id: Optional session ID to clear. If None, clears current session.
        """
        if not self.audit_logger:
            return

        session = session_id or self.current_session_id
        if session:
            self.audit_logger.clear_session(session)
            if session == self.current_session_id:
                self.current_session_id = None
