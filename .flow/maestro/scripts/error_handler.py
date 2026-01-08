#!/usr/bin/env python3
"""
Error Handler for Maestro Orchestrator

Detects, classifies, and handles errors during task execution.
Provides intelligent recovery strategy selection and execution.
"""

import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field

from retry_manager import RetryManager


class ErrorCategory(str, Enum):
    """Error classification categories."""
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    AMBIGUOUS = "ambiguous"


class ErrorType(str, Enum):
    """Specific error types for detailed classification."""
    # Transient errors
    TIMEOUT = "timeout"
    NETWORK = "network"
    RESOURCE_TEMPORARILY_UNAVAILABLE = "resource_temporarily_unavailable"
    RATE_LIMITED = "rate_limited"
    SUBPROCESS_TIMEOUT = "subprocess_timeout"

    # Permanent errors
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    TYPE_ERROR = "type_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    LOGIC_ERROR = "logic_error"
    DEPENDENCY_MISSING = "dependency_missing"
    CONFIGURATION_ERROR = "configuration_error"

    # Ambiguous errors
    GENERIC_EXCEPTION = "generic_exception"
    UNKNOWN = "unknown"
    REQUIREMENTS_UNCLEAR = "requirements_unclear"
    CONFLICTING_INFORMATION = "conflicting_information"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error categories."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    ALTERNATIVE_APPROACH = "alternative_approach"
    ROLLBACK_TO_CHECKPOINT = "rollback_to_checkpoint"
    REQUEST_HUMAN_INPUT = "request_human_input"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ESCALATE = "escalate"


@dataclass
class Error:
    """Represents a detected error with full context."""
    error_id: str
    timestamp: str
    error_type: ErrorType
    category: ErrorCategory
    message: str
    source: str  # Where the error originated (subprocess, test, filesystem, etc.)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    exit_code: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["error_type"] = self.error_type.value
        data["category"] = self.category.value
        return data


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    strategy: RecoveryStrategy
    success: bool
    message: str
    retry_count: int = 0
    next_action: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["strategy"] = self.strategy.value
        return data


class ErrorHandler:
    """
    Main error handling system.

    Features:
    - Detect errors from subprocess output, test failures, file system issues
    - Classify errors as transient, permanent, or ambiguous
    - Select appropriate recovery strategy
    - Execute recovery actions with backoff and retry logic
    """

    # Error patterns for detection and classification
    TRANSIENT_PATTERNS = [
        r"timeout",
        r"timed out",
        r"connection.*refused",
        r"connection.*reset",
        r"network.*unreachable",
        r"temporary.*failure",
        r"temporarily.*unavailable",
        r"rate.*limit",
        r"too.*many.*requests",
        r"resource.*temporarily",
        r"operation.*timed out",
        r"deadline.*exceeded",
    ]

    PERMANENT_PATTERNS = [
        r"syntaxError",
        r"indentationError",
        r"tabError",
        r"importError",
        r"moduleNotFound",
        r"nameError",
        r"typeError",
        r"attributeError",
        r"keyError",
        r"valueError",
        r"file.*not.*found",
        r"no such file",
        r"permission denied",
        r"access denied",
        r"unauthorized",
        r"forbidden",
        r"invalid.*token",
        r"authentication.*failed",
        r"dependency.*not.*found",
        r"package.*not.*installed",
        r"module.*not.*found",
        r"undefined.*symbol",
        r"undefined.*reference",
    ]

    AMBIGUOUS_PATTERNS = [
        r"error",
        r"exception",
        r"failed",
        r"failure",
    ]

    def __init__(
        self,
        session_id: Optional[str] = None,
        base_path: Optional[Path] = None,
    ):
        """
        Initialize the error handler.

        Args:
            session_id: Optional session ID for logging
            base_path: Base path for storage (defaults to .flow/maestro)
        """
        self.session_id = session_id
        self.base_path = base_path or Path.cwd() / ".flow" / "maestro"
        self.session_dir = self.base_path / "sessions" / session_id if session_id else None
        self.error_log: List[Error] = []

        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0  # seconds

        # Initialize retry manager
        self.retry_manager = RetryManager(
            max_retries=self.max_retries,
            backoff_base=2.0,
            initial_delay=self.base_delay,
            max_delay=self.max_delay,
        )

        # Compile regex patterns for efficiency
        self._transient_regex = re.compile(
            "|".join(self.TRANSIENT_PATTERNS),
            re.IGNORECASE
        )
        self._permanent_regex = re.compile(
            "|".join(self.PERMANENT_PATTERNS),
            re.IGNORECASE
        )
        self._ambiguous_regex = re.compile(
            "|".join(self.AMBIGUOUS_PATTERNS),
            re.IGNORECASE
        )

    def detect_error(
        self,
        output: str,
        source: str = "unknown",
        exit_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Error]:
        """
        Detect an error from output or context.

        Args:
            output: Output string to analyze (stdout, stderr, logs, etc.)
            source: Source of the output (subprocess, test, filesystem, etc.)
            exit_code: Process exit code if applicable
            context: Additional context about the error

        Returns:
            Error object if error detected, None otherwise
        """
        if not output:
            # Check exit code
            if exit_code is not None and exit_code != 0:
                return self._create_error(
                    error_type=ErrorType.UNKNOWN,
                    category=ErrorCategory.AMBIGUOUS,
                    message=f"Process exited with code {exit_code}",
                    source=source,
                    exit_code=exit_code,
                    context=context or {},
                )
            return None

        # Check for transient error patterns
        transient_match = self._transient_regex.search(output)
        if transient_match:
            error_type = self._classify_transient_error(output)
            return self._create_error(
                error_type=error_type,
                category=ErrorCategory.TRANSIENT,
                message=transient_match.group(0),
                source=source,
                exit_code=exit_code,
                context=context or {},
                stack_trace=output,
            )

        # Check for permanent error patterns
        permanent_match = self._permanent_regex.search(output)
        if permanent_match:
            error_type = self._classify_permanent_error(output)
            return self._create_error(
                error_type=error_type,
                category=ErrorCategory.PERMANENT,
                message=permanent_match.group(0),
                source=source,
                exit_code=exit_code,
                context=context or {},
                stack_trace=output,
            )

        # Check for ambiguous error patterns
        ambiguous_match = self._ambiguous_regex.search(output)
        if ambiguous_match:
            return self._create_error(
                error_type=ErrorType.GENERIC_EXCEPTION,
                category=ErrorCategory.AMBIGUOUS,
                message=ambiguous_match.group(0),
                source=source,
                exit_code=exit_code,
                context=context or {},
                stack_trace=output,
            )

        # No error detected
        return None

    def _classify_transient_error(self, output: str) -> ErrorType:
        """Classify transient error type from output."""
        output_lower = output.lower()

        if "timeout" in output_lower or "timed out" in output_lower:
            return ErrorType.TIMEOUT
        elif "rate limit" in output_lower:
            return ErrorType.RATE_LIMITED
        elif any(term in output_lower for term in ["network", "connection", "unreachable"]):
            return ErrorType.NETWORK
        elif "temporarily" in output_lower or "temporary" in output_lower:
            return ErrorType.RESOURCE_TEMPORARILY_UNAVAILABLE
        else:
            return ErrorType.SUBPROCESS_TIMEOUT

    def _classify_permanent_error(self, output: str) -> ErrorType:
        """Classify permanent error type from output."""
        output_lower = output.lower()

        if "syntaxerror" in output_lower or "indentation" in output_lower:
            return ErrorType.SYNTAX_ERROR
        elif any(term in output_lower for term in ["importerror", "modulenotfound", "no module"]):
            return ErrorType.IMPORT_ERROR
        elif "typeerror" in output_lower:
            return ErrorType.TYPE_ERROR
        elif any(term in output_lower for term in ["file not found", "no such file"]):
            return ErrorType.FILE_NOT_FOUND
        elif any(term in output_lower for term in ["permission denied", "access denied", "forbidden"]):
            return ErrorType.PERMISSION_DENIED
        elif any(term in output_lower for term in ["dependency", "package", "not installed"]):
            return ErrorType.DEPENDENCY_MISSING
        elif "configuration" in output_lower or "config" in output_lower:
            return ErrorType.CONFIGURATION_ERROR
        else:
            return ErrorType.LOGIC_ERROR

    def _create_error(
        self,
        error_type: ErrorType,
        category: ErrorCategory,
        message: str,
        source: str,
        exit_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
    ) -> Error:
        """Create an Error object with generated ID and timestamp."""
        import uuid
        error_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()

        # Add suggestion based on error type
        suggestion = self._generate_suggestion(error_type, category)

        return Error(
            error_id=error_id,
            timestamp=timestamp,
            error_type=error_type,
            category=category,
            message=message,
            source=source,
            exit_code=exit_code,
            context=context or {},
            stack_trace=stack_trace,
            suggestion=suggestion,
        )

    def _generate_suggestion(self, error_type: ErrorType, category: ErrorCategory) -> str:
        """Generate a helpful suggestion for the error."""
        suggestions = {
            ErrorType.TIMEOUT: "Increase timeout duration or check if the operation is hanging.",
            ErrorType.NETWORK: "Check network connectivity and remote service availability.",
            ErrorType.RATE_LIMITED: "Implement exponential backoff and retry later.",
            ErrorType.SYNTAX_ERROR: "Review code syntax and fix syntax errors.",
            ErrorType.IMPORT_ERROR: "Install missing dependencies or fix import paths.",
            ErrorType.FILE_NOT_FOUND: "Verify file paths and ensure required files exist.",
            ErrorType.PERMISSION_DENIED: "Check file permissions and access rights.",
            ErrorType.DEPENDENCY_MISSING: "Install missing dependencies using package manager.",
            ErrorType.CONFIGURATION_ERROR: "Review and fix configuration settings.",
        }

        if category == ErrorCategory.AMBIGUOUS:
            return "Error needs investigation. Check logs and context for more details."

        return suggestions.get(
            error_type,
            "Review the error context and consider appropriate recovery action.",
        )

    def classify_error(self, error: Error) -> ErrorCategory:
        """
        Classify an error into a category.

        Args:
            error: Error object to classify

        Returns:
            ErrorCategory (already set in error object, returned for convenience)
        """
        # The error is already classified during detection
        # This method exists for API completeness and potential reclassification
        return error.category

    def select_recovery_strategy(
        self,
        error: Error,
        context: Optional[Dict[str, Any]] = None,
    ) -> RecoveryStrategy:
        """
        Select appropriate recovery strategy for an error.

        Args:
            error: Error object
            context: Additional context for strategy selection

        Returns:
            Selected RecoveryStrategy
        """
        ctx = context or {}

        # Transient errors: retry with backoff
        if error.category == ErrorCategory.TRANSIENT:
            # Check if we've exceeded retry limit
            retry_count = ctx.get("retry_count", 0)
            if retry_count >= self.max_retries:
                return RecoveryStrategy.ESCALATE
            return RecoveryStrategy.RETRY_WITH_BACKOFF

        # Permanent errors: alternative approach or rollback
        if error.category == ErrorCategory.PERMANENT:
            # Check if we have a checkpoint to rollback to
            has_checkpoint = ctx.get("has_checkpoint", False)
            if has_checkpoint:
                return RecoveryStrategy.ROLLBACK_TO_CHECKPOINT
            return RecoveryStrategy.ALTERNATIVE_APPROACH

        # Ambiguous errors: request human input
        if error.category == ErrorCategory.AMBIGUOUS:
            # Check if we can skip this error
            can_skip = ctx.get("can_skip", False)
            if can_skip:
                return RecoveryStrategy.SKIP_AND_CONTINUE
            return RecoveryStrategy.REQUEST_HUMAN_INPUT

        # Default fallback
        return RecoveryStrategy.REQUEST_HUMAN_INPUT

    def execute_recovery(
        self,
        strategy: RecoveryStrategy,
        context: Dict[str, Any],
    ) -> RecoveryResult:
        """
        Execute a recovery strategy.

        Args:
            strategy: Recovery strategy to execute
            context: Context containing:
                - retry_count: Current retry attempt number
                - command: Command to retry (for retry strategy)
                - checkpoint_id: Checkpoint to rollback to (for rollback strategy)
                - error: The original error object

        Returns:
            RecoveryResult with outcome and next action
        """
        retry_count = context.get("retry_count", 0)
        error = context.get("error")

        if strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
            return self._execute_retry_with_backoff(context, retry_count)

        elif strategy == RecoveryStrategy.ALTERNATIVE_APPROACH:
            return self._execute_alternative_approach(context, error)

        elif strategy == RecoveryStrategy.ROLLBACK_TO_CHECKPOINT:
            return self._execute_rollback(context, error)

        elif strategy == RecoveryStrategy.REQUEST_HUMAN_INPUT:
            return self._execute_request_human_input(context, error)

        elif strategy == RecoveryStrategy.SKIP_AND_CONTINUE:
            return self._execute_skip_and_continue(context, error)

        elif strategy == RecoveryStrategy.ESCALATE:
            return self._execute_escalate(context, error)

        else:
            return RecoveryResult(
                strategy=strategy,
                success=False,
                message=f"Unknown recovery strategy: {strategy}",
                next_action="request_human_input",
            )

    def _execute_retry_with_backoff(
        self,
        context: Dict[str, Any],
        retry_count: int,
    ) -> RecoveryResult:
        """
        Execute retry with exponential backoff.

        Calculates delay and provides next action for retry.
        Uses RetryManager for consistent backoff calculation.
        """
        # Use RetryManager for backoff calculation
        delay = self.retry_manager.calculate_delay(retry_count)

        command = context.get("command")
        operation_name = context.get("operation_name", command or "unknown_operation")
        next_action = "retry"

        if command:
            message = f"Retry {retry_count + 1}/{self.max_retries} after {delay:.1f}s delay for command: {command}"
        else:
            message = f"Retry {retry_count + 1}/{self.max_retries} after {delay:.1f}s delay"

        # Track retry attempt in manager
        retry_attempt = {
            "attempt_number": retry_count + 1,
            "delay_seconds": delay,
            "success": False,  # Will be updated after retry
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return RecoveryResult(
            strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            success=True,  # Strategy execution successful (not the retry itself)
            message=message,
            retry_count=retry_count + 1,
            next_action=next_action,
        )

    def execute_with_retry(
        self,
        func: Callable,
        context: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute a function with retry logic using RetryManager.

        Args:
            func: Function to execute
            context: Context dictionary containing operation_name and other params
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            Exception if all retries are exhausted
        """
        operation_name = context.get("operation_name", "unknown_operation")

        # Add retry history to context for decision logging
        try:
            result = self.retry_manager.execute_with_retry(
                func,
                context=context,
                *args,
                **kwargs,
            )

            # Add retry history to context
            retry_history = self.retry_manager.get_retry_history(operation_name)
            context["retry_history"] = retry_history

            return result

        except Exception as e:
            # Add retry history to context even on failure
            retry_history = self.retry_manager.get_retry_history(operation_name)
            context["retry_history"] = retry_history
            raise

    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        Get retry statistics from the retry manager.

        Returns:
            Dictionary containing retry statistics for all operations
        """
        return self.retry_manager.get_retry_statistics()

    def get_retry_history(self) -> Dict[str, Any]:
        """
        Get retry history from the retry manager.

        Returns:
            Dictionary containing retry history for all operations
        """
        return self.retry_manager.get_retry_history()

    def _execute_alternative_approach(
        self,
        context: Dict[str, Any],
        error: Optional[Error],
    ) -> RecoveryResult:
        """
        Signal that an alternative approach should be tried.

        This doesn't execute the alternative itself, but signals
        the orchestrator to try a different implementation strategy.
        """
        message = "Switching to alternative approach due to permanent error"

        if error:
            message += f": {error.error_type.value} - {error.message}"

        return RecoveryResult(
            strategy=RecoveryStrategy.ALTERNATIVE_APPROACH,
            success=True,
            message=message,
            next_action="try_alternative",
        )

    def _execute_rollback(
        self,
        context: Dict[str, Any],
        error: Optional[Error],
    ) -> RecoveryResult:
        """
        Signal rollback to a checkpoint.

        This doesn't execute the rollback itself, but signals
        the orchestrator to rollback to the specified checkpoint.
        """
        checkpoint_id = context.get("checkpoint_id", "unknown")

        message = f"Rolling back to checkpoint: {checkpoint_id}"

        if error:
            message += f" due to error: {error.error_type.value}"

        return RecoveryResult(
            strategy=RecoveryStrategy.ROLLBACK_TO_CHECKPOINT,
            success=True,
            message=message,
            next_action=f"rollback_to_checkpoint:{checkpoint_id}",
        )

    def _execute_request_human_input(
        self,
        context: Dict[str, Any],
        error: Optional[Error],
    ) -> RecoveryResult:
        """
        Signal that human input is required.

        Formats the error for human review and provides context.
        """
        message = "Human input required to resolve error"

        if error:
            message += f"\n\nError: {error.error_type.value}\n"
            message += f"Message: {error.message}\n"
            message += f"Source: {error.source}"

            if error.suggestion:
                message += f"\n\nSuggestion: {error.suggestion}"

            if error.stack_trace:
                message += f"\n\nStack trace:\n{error.stack_trace[:500]}"

        return RecoveryResult(
            strategy=RecoveryStrategy.REQUEST_HUMAN_INPUT,
            success=False,
            message=message,
            next_action="wait_for_human_input",
        )

    def _execute_skip_and_continue(
        self,
        context: Dict[str, Any],
        error: Optional[Error],
    ) -> RecoveryResult:
        """
        Signal to skip this error and continue.

        Used for non-critical errors that don't block progress.
        """
        message = "Skipping error and continuing with next task"

        if error:
            message += f": {error.message}"

        return RecoveryResult(
            strategy=RecoveryStrategy.SKIP_AND_CONTINUE,
            success=True,
            message=message,
            next_action="continue_to_next_task",
        )

    def _execute_escalate(
        self,
        context: Dict[str, Any],
        error: Optional[Error],
    ) -> RecoveryResult:
        """
        Signal escalation after exhausting recovery options.

        Used when retries are exhausted and no other strategy applies.
        """
        message = "Escalating error - recovery options exhausted"

        if error:
            retry_count = context.get("retry_count", 0)
            message += f"\n\nError after {retry_count} retries: {error.error_type.value}"
            message += f"\nMessage: {error.message}"

        return RecoveryResult(
            strategy=RecoveryStrategy.ESCALATE,
            success=False,
            message=message,
            next_action="escalate_to_human",
        )

    def handle_subprocess_result(
        self,
        result: subprocess.CompletedProcess,
        command: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Error], Optional[RecoveryResult]]:
        """
        Handle a subprocess result - detect error and select recovery.

        Args:
            result: Subprocess result to analyze
            command: Command that was executed
            context: Additional context

        Returns:
            Tuple of (Error or None, RecoveryResult or None)
        """
        ctx = context or {}
        ctx["command"] = command

        # Combine stdout and stderr for analysis
        output = ""
        if result.stdout:
            output += result.stdout.decode("utf-8", errors="replace")
        if result.stderr:
            output += result.stderr.decode("utf-8", errors="replace")

        # Detect error
        error = self.detect_error(
            output=output,
            source="subprocess",
            exit_code=result.returncode,
            context=ctx,
        )

        if error is None:
            return None, None

        # Log the error
        self.error_log.append(error)

        # Select and execute recovery strategy
        strategy = self.select_recovery_strategy(error, ctx)
        recovery_result = self.execute_recovery(strategy, {**ctx, "error": error})

        return error, recovery_result

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors encountered.

        Returns:
            Dictionary with error statistics and details
        """
        if not self.error_log:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_type": {},
                "recent_errors": [],
            }

        by_category: Dict[str, int] = {}
        by_type: Dict[str, int] = {}

        for error in self.error_log:
            by_category[error.category.value] = by_category.get(error.category.value, 0) + 1
            by_type[error.error_type.value] = by_type.get(error.error_type.value, 0) + 1

        return {
            "total_errors": len(self.error_log),
            "by_category": by_category,
            "by_type": by_type,
            "recent_errors": [e.to_dict() for e in self.error_log[-10:]],
        }

    def save_error_log(self, filepath: Optional[Path] = None) -> Path:
        """
        Save error log to file.

        Args:
            filepath: Optional filepath to save to. Defaults to session directory.

        Returns:
            Path where error log was saved
        """
        if filepath is None:
            if self.session_dir:
                filepath = self.session_dir / "error_log.json"
            else:
                filepath = Path(tempfile.gettempdir()) / "maestro_error_log.json"

        error_data = {
            "session_id": self.session_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "errors": [e.to_dict() for e in self.error_log],
            "summary": self.get_error_summary(),
        }

        with open(filepath, "w") as f:
            json.dump(error_data, f, indent=2)

        return filepath


def main():
    """CLI entry point for error handler."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Maestro Error Handler"
    )
    parser.add_argument(
        "action",
        choices=["analyze", "summary"],
        help="Action to perform",
    )
    parser.add_argument("--output", help="Output file for analysis results")
    parser.add_argument("--text", help="Text to analyze for errors")

    args = parser.parse_args()

    handler = ErrorHandler()

    if args.action == "analyze":
        if not args.text:
            parser.error("--text required for analyze action")

        error = handler.detect_error(args.text, source="cli")
        if error:
            result = {
                "error_detected": True,
                "error": error.to_dict(),
            }

            strategy = handler.select_recovery_strategy(error)
            result["suggested_strategy"] = strategy.value

            recovery = handler.execute_recovery(strategy, {"error": error})
            result["recovery_result"] = recovery.to_dict()
        else:
            result = {"error_detected": False}

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))

    elif args.action == "summary":
        summary = handler.get_error_summary()
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
