#!/usr/bin/env python3
"""
Retry Manager for Maestro Orchestrator

Implements retry logic with exponential backoff for transient failures.
Tracks retry attempts and provides detailed history for debugging.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryAttempt:
    """Represents a single retry attempt."""
    attempt_number: int
    delay_seconds: float
    error_before: Optional[Exception] = None
    success: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "attempt_number": self.attempt_number,
            "delay_seconds": self.delay_seconds,
            "error_before": str(self.error_before) if self.error_before else None,
            "error_type": type(self.error_before).__name__ if self.error_before else None,
            "success": self.success,
            "timestamp": self.timestamp,
        }


class RetryManager:
    """
    Manages retry logic with exponential backoff.

    Features:
    - Exponential backoff calculation
    - Retry count tracking per operation
    - Transient error detection
    - Detailed retry history logging
    - Configurable retry limits and delays
    """

    # Transient errors that should trigger retries
    TRANSIENT_ERRORS = (
        ConnectionError,
        TimeoutError,
        OSError,  # Covers network and I/O errors
    )

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        """
        Initialize the retry manager.

        Args:
            max_retries: Maximum number of retry attempts (excluding initial attempt)
            backoff_base: Base for exponential backoff calculation
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries in seconds
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.retry_history: Dict[str, List[RetryAttempt]] = {}

    def calculate_delay(self, attempt_number: int) -> float:
        """
        Calculate exponential backoff delay for a given attempt.

        Args:
            attempt_number: The retry attempt number (0-indexed)

        Returns:
            Delay in seconds

        Examples:
            >>> manager = RetryManager(backoff_base=2.0, initial_delay=1.0)
            >>> manager.calculate_delay(0)
            0.0
            >>> manager.calculate_delay(1)
            1.0
            >>> manager.calculate_delay(2)
            2.0
            >>> manager.calculate_delay(3)
            4.0
        """
        if attempt_number == 0:
            return 0.0

        # Calculate exponential backoff: base_delay * (backoff_base ^ (attempt - 1))
        delay = self.initial_delay * (self.backoff_base ** (attempt_number - 1))

        # Cap at max_delay
        return min(delay, self.max_delay)

    def is_transient_error(self, error: Exception) -> bool:
        """
        Determine if an error is transient and should trigger a retry.

        Args:
            error: The exception to check

        Returns:
            True if the error is transient, False otherwise
        """
        # Check if it's a known transient error type
        if isinstance(error, self.TRANSIENT_ERRORS):
            return True

        # Check error message for transient indicators
        error_message = str(error).lower()
        transient_indicators = [
            "timeout",
            "timed out",
            "connection refused",
            "connection reset",
            "network unreachable",
            "temporary failure",
            "temporarily unavailable",
            "rate limit",
            "too many requests",
            "deadline exceeded",
        ]

        return any(indicator in error_message for indicator in transient_indicators)

    def execute_with_retry(
        self,
        func: Callable[..., T],
        context: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute function with retry logic and exponential backoff.

        Args:
            func: Function to execute
            context: Context dictionary containing:
                - operation_name: Name of the operation for tracking
                - retry_on: Optional list of exception types to retry on
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            The last exception if all retries are exhausted
            ValueError if operation_name is not provided in context
        """
        operation_name = context.get("operation_name")
        if not operation_name:
            raise ValueError("operation_name must be provided in context")

        retry_on = context.get("retry_on", self.TRANSIENT_ERRORS)

        # Initialize history for this operation
        if operation_name not in self.retry_history:
            self.retry_history[operation_name] = []

        last_error: Optional[Exception] = None

        # Attempt to execute the function with retries
        for attempt in range(self.max_retries + 1):
            attempt_number = attempt + 1
            delay = self.calculate_delay(attempt)

            # Wait before retry (except for first attempt)
            if attempt > 0:
                logger.info(
                    f"Retry attempt {attempt_number}/{self.max_retries + 1} "
                    f"for '{operation_name}' after {delay:.2f}s delay"
                )
                time.sleep(delay)

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Log successful attempt
                retry_attempt = RetryAttempt(
                    attempt_number=attempt_number,
                    delay_seconds=delay,
                    error_before=last_error,
                    success=True,
                )
                self.retry_history[operation_name].append(retry_attempt)

                logger.info(
                    f"Operation '{operation_name}' succeeded on attempt {attempt_number}"
                )

                return result

            except Exception as e:
                last_error = e

                # Check if we should retry this error
                should_retry = (
                    attempt < self.max_retries
                    and (isinstance(e, retry_on) or self.is_transient_error(e))
                )

                # Log failed attempt
                retry_attempt = RetryAttempt(
                    attempt_number=attempt_number,
                    delay_seconds=delay,
                    error_before=e,
                    success=False,
                )
                self.retry_history[operation_name].append(retry_attempt)

                if should_retry:
                    logger.warning(
                        f"Operation '{operation_name}' failed on attempt {attempt_number}: {e}. "
                        f"Retrying after {self.calculate_delay(attempt + 1):.2f}s delay..."
                    )
                else:
                    # Don't retry - either reached max retries or non-transient error
                    if attempt >= self.max_retries:
                        logger.error(
                            f"Operation '{operation_name}' failed after {attempt_number} attempts. "
                            f"Max retries ({self.max_retries}) exhausted."
                        )
                    else:
                        logger.error(
                            f"Operation '{operation_name}' failed with non-transient error: {e}. "
                            f"Not retrying."
                        )
                    raise

        # This should never be reached, but mypy needs it
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected state in retry logic")

    def get_retry_history(self, operation_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get retry history for operations.

        Args:
            operation_name: Optional operation name to filter by.
                          If None, returns history for all operations.

        Returns:
            Dictionary mapping operation names to their retry attempt history
        """
        if operation_name:
            return {
                operation_name: [
                    attempt.to_dict() for attempt in self.retry_history.get(operation_name, [])
                ]
            }

        return {
            op: [attempt.to_dict() for attempt in attempts]
            for op, attempts in self.retry_history.items()
        }

    def get_retry_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get retry statistics for operations.

        Args:
            operation_name: Optional operation name to filter by.
                          If None, returns statistics for all operations.

        Returns:
            Dictionary containing retry statistics
        """
        if operation_name:
            attempts = self.retry_history.get(operation_name, [])
            total_attempts = len(attempts)
            successful_attempts = sum(1 for a in attempts if a.success)
            failed_attempts = total_attempts - successful_attempts
            total_delay = sum(a.delay_seconds for a in attempts)

            return {
                "operation_name": operation_name,
                "total_attempts": total_attempts,
                "successful_attempts": successful_attempts,
                "failed_attempts": failed_attempts,
                "total_delay_seconds": total_delay,
                "average_delay_per_attempt": total_delay / total_attempts if total_attempts > 0 else 0,
                "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            }

        # Aggregate statistics for all operations
        all_stats = {}
        for op in self.retry_history:
            all_stats[op] = self.get_retry_statistics(op)

        return all_stats

    def clear_history(self, operation_name: Optional[str] = None) -> None:
        """
        Clear retry history.

        Args:
            operation_name: Optional operation name to clear history for.
                          If None, clears all history.
        """
        if operation_name:
            self.retry_history.pop(operation_name, None)
            logger.info(f"Cleared retry history for operation '{operation_name}'")
        else:
            self.retry_history.clear()
            logger.info("Cleared all retry history")


def main():
    """CLI entry point for retry manager."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Maestro Retry Manager"
    )
    parser.add_argument(
        "action",
        choices=["stats", "history", "test"],
        help="Action to perform",
    )
    parser.add_argument("--operation", help="Operation name to filter by")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retry attempts")
    parser.add_argument("--backoff-base", type=float, default=2.0, help="Backoff base multiplier")

    args = parser.parse_args()

    manager = RetryManager(
        max_retries=args.max_retries,
        backoff_base=args.backoff_base,
    )

    if args.action == "stats":
        stats = manager.get_retry_statistics(args.operation)
        print(json.dumps(stats, indent=2))

    elif args.action == "history":
        history = manager.get_retry_history(args.operation)
        print(json.dumps(history, indent=2))

    elif args.action == "test":
        # Test the retry manager with a flaky function
        call_count = {"count": 0}

        def flaky_function():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ConnectionError("Simulated transient error")
            return "Success!"

        try:
            result = manager.execute_with_retry(
                flaky_function,
                context={"operation_name": "test_operation"}
            )
            print(f"Result: {result}")
            print(f"Total attempts: {call_count['count']}")

            # Show retry history
            history = manager.get_retry_history()
            print("\nRetry History:")
            print(json.dumps(history, indent=2))
        except Exception as e:
            print(f"Failed after all retries: {e}")


if __name__ == "__main__":
    main()
