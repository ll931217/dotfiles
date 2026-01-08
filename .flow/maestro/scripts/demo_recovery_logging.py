#!/usr/bin/env python3
"""
Demonstration script for Recovery Audit Logging System.

This script demonstrates the key features of the comprehensive recovery
logging and audit trail system.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from auto_recovery import (
    AutoRecoveryManager,
    RecoveryAuditLogger,
    RecoveryAttempt,
    RecoveryStrategyType,
    Error,
)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_logging():
    """Demonstrate basic recovery logging."""
    print_section("1. Basic Recovery Logging")

    # Create a temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Using audit directory: {temp_dir}")

    # Create manager with audit logging
    manager = AutoRecoveryManager(
        max_attempts=3,
        audit_dir=temp_dir / "audit",
        enable_audit_logging=True,
    )
    print("✓ Created AutoRecoveryManager with audit logging enabled")

    # Simulate a recovery scenario
    error = Error(
        error_type="SyntaxError",
        message="Invalid syntax on line 42",
        source="linter",
        file_path="example.py",
        line_number=42,
    )

    print(f"\nAttempting recovery for error: {error.message}")
    result = manager.attempt_recovery(error, {})

    print(f"Recovery result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Strategy used: {result.strategy_used.value}")
    print(f"Total attempts: {len(result.attempts)}")

    # Get audit trail
    audit_trail = manager.get_audit_trail()
    print(f"\n✓ Audit trail entries: {len(audit_trail)}")

    # Get statistics
    stats = manager.get_recovery_statistics()
    print(f"✓ Recovery statistics:")
    print(f"  - Total attempts: {stats.get('total_attempts', 0)}")
    print(f"  - Success rate: {stats.get('success_rate', 0)}%")
    print(f"  - Duration: {stats.get('total_duration_seconds', 0)}s")

    return temp_dir


def demo_multiple_recoveries(temp_dir):
    """Demonstrate multiple recovery operations."""
    print_section("2. Multiple Recovery Operations")

    manager = AutoRecoveryManager(
        max_attempts=2,
        audit_dir=temp_dir / "audit",
        enable_audit_logging=True,
    )

    # Configure fix generator to simulate different outcomes
    attempt_count = [0]

    def simulated_fix(error):
        attempt_count[0] += 1
        if attempt_count[0] <= 2:
            return None  # First attempts fail
        return "Fix applied successfully"

    manager.fix_generator = simulated_fix

    errors = [
        Error(error_type="SyntaxError", message=f"Error {i}", source="test")
        for i in range(1, 4)
    ]

    print(f"Processing {len(errors)} errors...")
    for error in errors:
        result = manager.attempt_recovery(error, {})
        status = "✓" if result.success else "✗"
        print(f"{status} {error.error_type}: {result.message}")

    # Get comprehensive statistics
    stats = manager.get_recovery_statistics()
    print(f"\n✓ Session statistics:")
    print(f"  - Total attempts: {stats['total_attempts']}")
    print(f"  - Successful: {stats['successful_attempts']}")
    print(f"  - Failed: {stats['failed_attempts']}")
    print(f"  - Success rate: {stats['success_rate']}%")
    print(f"  - Strategies used: {stats['strategies_used']}")


def demo_export_functionality(temp_dir):
    """Demonstrate export functionality."""
    print_section("3. Export and Reporting")

    # Create a simple recovery scenario
    manager = AutoRecoveryManager(
        audit_dir=temp_dir / "audit",
        enable_audit_logging=True,
    )

    manager.fix_generator = lambda e: "Fix applied"

    error = Error(error_type="TestError", message="Test", source="test")
    manager.attempt_recovery(error, {})

    # Export to JSON
    json_path = manager.export_audit_trail(format="json")
    print(f"✓ Exported audit trail to JSON: {json_path}")

    # Export to CSV
    csv_path = manager.export_audit_trail(format="csv")
    print(f"✓ Exported audit trail to CSV: {csv_path}")

    # Generate comprehensive report
    report_path = manager.generate_recovery_report()
    print(f"✓ Generated recovery report: {report_path}")

    # Verify files exist
    json_exists = Path(json_path).exists() if json_path else False
    csv_exists = Path(csv_path).exists() if csv_path else False
    report_exists = Path(report_path).exists() if report_path else False

    print(f"\nFile verification:")
    print(f"  - JSON file: {'✓' if json_exists else '✗'}")
    print(f"  - CSV file: {'✓' if csv_exists else '✗'}")
    print(f"  - Report file: {'✓' if report_exists else '✗'}")


def demo_direct_logger_usage(temp_dir):
    """Demonstrate direct usage of RecoveryAuditLogger."""
    print_section("4. Direct Logger Usage")

    logger = RecoveryAuditLogger(audit_dir=temp_dir / "audit_direct")

    # Start a named session
    session_id = logger.start_session("demo_session")
    print(f"✓ Started session: {session_id}")

    # Create and log multiple attempts
    for i in range(3):
        error = Error(
            error_type=["SyntaxError", "ImportError", "TypeError"][i],
            message=f"Error {i+1}",
            source="test",
        )

        attempt = RecoveryAttempt(
            attempt_number=i + 1,
            strategy="fix",
            success=i >= 1,  # Last two succeed
            error_before=error,
            error_after=None,
            changes_made=[f"Change {i+1}"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=1.0 + i * 0.5,
            message=f"Attempt {i+1}",
        )

        entry_id = logger.log_recovery_attempt(
            attempt,
            session_id,
            files_modified=[f"file{i}.py"],
            rollback_performed=False,
            next_action="complete" if i >= 1 else "retry",
        )
        print(f"✓ Logged attempt {i+1}: {entry_id}")

    # Get detailed statistics
    stats = logger.get_recovery_statistics(session_id)
    print(f"\n✓ Session '{session_id}' statistics:")
    print(f"  - Total attempts: {stats['total_attempts']}")
    print(f"  - Success rate: {stats['success_rate']}%")
    print(f"  - Error distribution: {stats['error_type_distribution']}")
    print(f"  - Files modified: {stats['files_modified_count']}")


def demo_session_management(temp_dir):
    """Demonstrate session management."""
    print_section("5. Session Management")

    logger = RecoveryAuditLogger(audit_dir=temp_dir / "audit_sessions")

    # Create multiple sessions
    session1 = logger.start_session("session_1")
    session2 = logger.start_session("session_2")
    session3 = logger.start_session("session_3")

    print(f"✓ Created 3 sessions: {session1}, {session2}, {session3}")

    # Get all session IDs
    all_sessions = logger.get_all_session_ids()
    print(f"✓ Total sessions: {len(all_sessions)}")

    # Clear one session
    logger.clear_session(session2)
    print(f"✓ Cleared session: {session2}")

    # Verify session was cleared
    remaining_sessions = logger.get_all_session_ids()
    print(f"✓ Remaining sessions: {len(remaining_sessions)}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  RECOVERY AUDIT LOGGING SYSTEM - DEMONSTRATION")
    print("=" * 70)

    try:
        # Run demonstrations
        temp_dir = demo_basic_logging()
        demo_multiple_recoveries(temp_dir)
        demo_export_functionality(temp_dir)
        demo_direct_logger_usage(temp_dir)
        demo_session_management(temp_dir)

        print_section("Demonstration Complete")
        print("All features demonstrated successfully!")
        print(f"\nDemo files located in: {temp_dir}")

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n✓ Cleaned up temporary files")

    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
