#!/usr/bin/env python3
"""
Example usage of ErrorHandler for Maestro Orchestrator

Demonstrates error detection, classification, and recovery strategy selection.
"""

import subprocess
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorType,
    RecoveryStrategy,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def example_1_subprocess_handling():
    """Example 1: Handling subprocess errors."""
    print_section("Example 1: Subprocess Error Handling")

    handler = ErrorHandler()

    # Simulate a failing subprocess
    result = subprocess.CompletedProcess(
        args=["npm", "install"],
        returncode=1,
        stdout=b"",
        stderr=b"npm ERR! network timeout at https://registry.npmjs.org",
    )

    error, recovery = handler.handle_subprocess_result(
        result=result,
        command="npm install",
    )

    if error:
        print(f"\nError Detected:")
        print(f"  Type: {error.error_type.value}")
        print(f"  Category: {error.category.value}")
        print(f"  Message: {error.message}")
        print(f"  Suggestion: {error.suggestion}")

    if recovery:
        print(f"\nRecovery Strategy:")
        print(f"  Strategy: {recovery.strategy.value}")
        print(f"  Message: {recovery.message}")
        print(f"  Next Action: {recovery.next_action}")
        print(f"  Retry Count: {recovery.retry_count}")


def example_2_syntax_error():
    """Example 2: Detecting syntax errors."""
    print_section("Example 2: Syntax Error Detection")

    handler = ErrorHandler()

    error_output = """
Traceback (most recent call last):
  File "app.py", line 42
    print("hello"
          ^
SyntaxError: unexpected EOF while parsing
"""

    error = handler.detect_error(
        output=error_output,
        source="python",
        exit_code=1,
    )

    if error:
        print(f"\nError Detected:")
        print(f"  Type: {error.error_type.value}")
        print(f"  Category: {error.category.value}")
        print(f"  Source: {error.source}")
        print(f"  Message: {error.message}")
        print(f"  Suggestion: {error.suggestion}")

        # Select recovery strategy
        strategy = handler.select_recovery_strategy(
            error,
            context={"has_checkpoint": True},
        )
        print(f"\nSuggested Strategy: {strategy.value}")


def example_3_retry_with_backoff():
    """Example 3: Retry with exponential backoff."""
    print_section("Example 3: Retry with Exponential Backoff")

    handler = ErrorHandler()

    # Simulate a timeout error
    error = handler.detect_error("Operation timed out after 30s")

    if error:
        print(f"\nError: {error.error_type.value} - {error.category.value}")

        # Simulate multiple retry attempts
        retry_count = 0
        while retry_count < 3:
            strategy = handler.select_recovery_strategy(
                error,
                context={"retry_count": retry_count},
            )

            recovery = handler.execute_recovery(
                strategy,
                context={
                    "error": error,
                    "retry_count": retry_count,
                    "command": "pytest tests/",
                },
            )

            print(f"\nAttempt {retry_count + 1}:")
            print(f"  Strategy: {recovery.strategy.value}")
            print(f"  Message: {recovery.message}")

            retry_count = recovery.retry_count


def example_4_error_summary():
    """Example 4: Error logging and summary."""
    print_section("Example 4: Error Logging and Summary")

    handler = ErrorHandler()

    # Simulate multiple errors during a session
    errors = [
        "Operation timed out",
        "SyntaxError: invalid syntax",
        "Connection refused",
        "ImportError: No module named 'requests'",
        "Operation timed out",
    ]

    for error_msg in errors:
        error = handler.detect_error(error_msg)
        if error:
            handler.error_log.append(error)

    # Get summary
    summary = handler.get_error_summary()

    print(f"\nError Summary:")
    print(f"  Total Errors: {summary['total_errors']}")
    print(f"  By Category: {summary['by_category']}")
    print(f"  By Type: {summary['by_type']}")

    print(f"\nRecent Errors:")
    for error_data in summary['recent_errors']:
        print(f"  - [{error_data['error_type']}] {error_data['message']}")


def example_5_ambiguous_error_with_human_input():
    """Example 5: Ambiguous error requiring human input."""
    print_section("Example 5: Ambiguous Error - Human Input Required")

    handler = ErrorHandler()

    error = handler.detect_error(
        "An error occurred during deployment",
        source="deployment",
    )

    if error:
        print(f"\nError Detected:")
        print(f"  Type: {error.error_type.value}")
        print(f"  Category: {error.category.value}")
        print(f"  Message: {error.message}")

        # Select recovery strategy
        strategy = handler.select_recovery_strategy(error)

        recovery = handler.execute_recovery(
            strategy,
            context={"error": error},
        )

        print(f"\nRecovery Result:")
        print(f"  Strategy: {recovery.strategy.value}")
        print(f"  Success: {recovery.success}")
        print(f"  Next Action: {recovery.next_action}")
        print(f"\n  Message for Human:")
        print(f"  {recovery.message}")


def example_6_checkpoint_rollback():
    """Example 6: Rollback to checkpoint on permanent error."""
    print_section("Example 6: Rollback to Checkpoint")

    handler = ErrorHandler()

    # Permanent error with checkpoint available
    error = handler.detect_error("ImportError: No module named 'tensorflow'")

    if error:
        print(f"\nError: {error.error_type.value} - {error.category.value}")

        # Select recovery strategy with checkpoint
        strategy = handler.select_recovery_strategy(
            error,
            context={"has_checkpoint": True, "checkpoint_id": "checkpoint-abc123"},
        )

        recovery = handler.execute_recovery(
            strategy,
            context={
                "error": error,
                "checkpoint_id": "checkpoint-abc123",
            },
        )

        print(f"\nRecovery Strategy: {recovery.strategy.value}")
        print(f"Next Action: {recovery.next_action}")
        print(f"Message: {recovery.message}")


def example_7_command_line_interface():
    """Example 7: Using the CLI interface."""
    print_section("Example 7: Command Line Interface")

    print("\nThe error handler can be used from the command line:")
    print("\n1. Analyze error text:")
    print("   $ python error_handler.py analyze --text 'Operation timed out'")

    print("\n2. Analyze error from file:")
    print("   $ python error_handler.py analyze --text '$(cat error.log)'")

    print("\n3. Get error summary:")
    print("   $ python error_handler.py summary")

    print("\n4. Save analysis to file:")
    print("   $ python error_handler.py analyze --text 'SyntaxError' --output analysis.json")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print(" Maestro ErrorHandler - Usage Examples")
    print("="*60)

    example_1_subprocess_handling()
    example_2_syntax_error()
    example_3_retry_with_backoff()
    example_4_error_summary()
    example_5_ambiguous_error_with_human_input()
    example_6_checkpoint_rollback()
    example_7_command_line_interface()

    print("\n" + "="*60)
    print(" Examples completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
