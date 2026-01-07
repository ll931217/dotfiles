#!/usr/bin/env python3
"""
Example: Session Manager Integration

Demonstrates how to use the SessionManager for a typical workflow.
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from session_manager import (
    SessionManager,
    SessionStatus,
    SessionPhase,
    SessionConfiguration,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_session_info(session, title: str = "Session"):
    """Print session information."""
    print(f"\n{title}:")
    print(f"  ID: {session.session_id}")
    print(f"  Status: {session.status.value}")
    print(f"  Feature Request: {session.feature_request}")
    print(f"  Created: {session.created_at}")
    if session.current_phase:
        print(f"  Phase: {session.current_phase.value}")
    if session.completed_at:
        print(f"  Completed: {session.completed_at}")


def example_basic_workflow():
    """Demonstrate basic session lifecycle."""
    print_section("Example 1: Basic Session Lifecycle")

    # Initialize manager (auto-detects repo root)
    manager = SessionManager()

    # Create a new session
    print("\n1. Creating new session...")
    session = manager.create_session(
        "Add user authentication with OAuth support",
        configuration=SessionConfiguration(
            max_iterations=3,
            auto_checkpoint=True,
        ),
    )
    print_session_info(session, "Created Session")

    # Transition through states
    print("\n2. Transitioning to PLANNING...")
    session = manager.transition_state(session.session_id, SessionStatus.PLANNING)
    print(f"   Status: {session.status.value}")

    print("\n3. Transitioning to GENERATING_TASKS...")
    session = manager.transition_state(
        session.session_id,
        SessionStatus.GENERATING_TASKS,
    )
    print(f"   Status: {session.status.value}")

    # Update with task statistics
    print("\n4. Adding task statistics...")
    session = manager.update_session(
        session.session_id,
        {
            "current_phase": SessionPhase.IMPLEMENT,
            "statistics": {
                "total_tasks": 8,
                "completed_tasks": 3,
                "decisions_made": 2,
            },
        },
    )
    print(f"   Phase: {session.current_phase.value}")
    print(f"   Tasks: {session.statistics.completed_tasks}/{session.statistics.total_tasks}")

    print("\n5. Transitioning to IMPLEMENTING...")
    session = manager.transition_state(session.session_id, SessionStatus.IMPLEMENTING)
    print(f"   Status: {session.status.value}")

    print("\n6. Transitioning to VALIDATING...")
    session = manager.transition_state(session.session_id, SessionStatus.VALIDATING)
    print(f"   Status: {session.status.value}")

    print("\n7. Transitioning to GENERATING_REPORT...")
    session = manager.transition_state(
        session.session_id,
        SessionStatus.GENERATING_REPORT,
    )
    print(f"   Status: {session.status.value}")

    print("\n8. Completing session...")
    session = manager.transition_state(session.session_id, SessionStatus.COMPLETED)
    print_session_info(session, "Completed Session")


def example_pause_and_resume():
    """Demonstrate pause and resume functionality."""
    print_section("Example 2: Pause and Resume")

    manager = SessionManager()

    # Create and start session
    print("\n1. Creating session...")
    session = manager.create_session("Build REST API for user management")
    print(f"   Status: {session.status.value}")

    print("\n2. Starting planning...")
    session = manager.transition_state(session.session_id, SessionStatus.PLANNING)
    print(f"   Status: {session.status.value}")

    print("\n3. Pausing session...")
    session = manager.transition_state(session.session_id, SessionStatus.PAUSED)
    print(f"   Status: {session.status.value}")

    # Simulate time passing and user resuming
    print("\n4. Resuming session...")
    session = manager.transition_state(session.session_id, SessionStatus.PLANNING)
    print(f"   Status: {session.status.value}")


def example_query_sessions():
    """Demonstrate session querying."""
    print_section("Example 3: Query Sessions")

    manager = SessionManager()

    # Create multiple sessions
    print("\n1. Creating multiple sessions...")
    s1 = manager.create_session("Feature A")
    manager.update_session(s1.session_id, {"status": "planning"})

    s2 = manager.create_session("Feature B")
    manager.update_session(s2.session_id, {"status": "implementing"})

    s3 = manager.create_session("Feature C")
    manager.update_session(s3.session_id, {"status": "planning"})

    # Mark one as completed
    manager.transition_state(s3.session_id, SessionStatus.GENERATING_TASKS)
    manager.transition_state(s3.session_id, SessionStatus.IMPLEMENTING)
    manager.transition_state(s3.session_id, SessionStatus.VALIDATING)
    manager.transition_state(s3.session_id, SessionStatus.GENERATING_REPORT)
    manager.transition_state(s3.session_id, SessionStatus.COMPLETED)

    # Query all sessions
    print("\n2. All sessions (newest first):")
    all_sessions = manager.query_sessions(limit=5)
    for s in all_sessions:
        print(f"   - {s.session_id[:8]}... ({s.status.value})")

    # Query by status
    print("\n3. Active sessions:")
    active = manager.list_active_sessions()
    for s in active:
        print(f"   - {s.session_id[:8]}... ({s.status.value})")

    # Query planning sessions
    print("\n4. Sessions in PLANNING status:")
    planning = manager.query_sessions(status=SessionStatus.PLANNING)
    for s in planning:
        print(f"   - {s.session_id[:8]}... {s.feature_request}")

    # Recent sessions
    print("\n5. Most recent 2 sessions:")
    recent = manager.get_recent_sessions(count=2)
    for s in recent:
        print(f"   - {s.session_id[:8]}... {s.feature_request}")


def example_error_handling():
    """Demonstrate error state and recovery."""
    print_section("Example 4: Error Handling")

    manager = SessionManager()

    print("\n1. Creating session...")
    session = manager.create_session("Complex data processing pipeline")
    print(f"   Status: {session.status.value}")

    print("\n2. Starting implementation...")
    manager.transition_state(session.session_id, SessionStatus.PLANNING)
    manager.transition_state(session.session_id, SessionStatus.GENERATING_TASKS)
    session = manager.transition_state(
        session.session_id,
        SessionStatus.IMPLEMENTING,
    )
    print(f"   Status: {session.status.value}")

    # Update with error statistics
    print("\n3. Recording error recovery...")
    session = manager.update_session(
        session.session_id,
        {
            "statistics": {
                "total_tasks": 5,
                "completed_tasks": 2,
                "failed_tasks": 1,
                "error_recovery_count": 3,
            },
        },
    )
    print(f"   Error recovery count: {session.statistics.error_recovery_count}")

    # Mark as failed
    print("\n4. Marking session as failed...")
    session = manager.transition_state(session.session_id, SessionStatus.FAILED)
    print_session_info(session, "Failed Session")


def example_prd_tracking():
    """Demonstrate PRD reference tracking."""
    print_section("Example 5: PRD Reference Tracking")

    manager = SessionManager()

    print("\n1. Creating session...")
    session = manager.create_session("E-commerce checkout flow")
    print(f"   Session ID: {session.session_id}")

    print("\n2. Attaching PRD reference...")
    session = manager.update_session(
        session.session_id,
        {
            "prd_reference": {
                "filename": "prd-ecommerce-checkout.md",
                "path": str(
                    manager.repo_root
                    / ".flow"
                    / "maestro"
                    / "prd-ecommerce-checkout.md"
                ),
                "version": "1.2.0",
            },
        },
    )

    if session.prd_reference:
        print(f"   PRD: {session.prd_reference.filename}")
        print(f"   Version: {session.prd_reference.version}")
        print(f"   Path: {session.prd_reference.path}")


def example_full_lifecycle():
    """Demonstrate complete session lifecycle with all features."""
    print_section("Example 6: Complete Session Lifecycle")

    manager = SessionManager()

    # Initialize
    print("\n1. INITIALIZING")
    session = manager.create_session(
        "Real-time chat application with WebSocket support",
        configuration=SessionConfiguration(
            max_iterations=5,
            timeout_minutes=180,
            auto_checkpoint=True,
            error_recovery_enabled=True,
        ),
    )
    print_session_info(session)

    # Planning
    print("\n2. PLANNING")
    session = manager.transition_state(session.session_id, SessionStatus.PLANNING)
    session = manager.update_session(
        session.session_id,
        {
            "current_phase": SessionPhase.PLAN,
            "prd_reference": {
                "filename": "prd-chat-app.md",
                "path": str(manager.repo_root / ".flow/maestro/prd-chat-app.md"),
                "version": "1.0.0",
            },
            "statistics": {
                "decisions_made": 5,
            },
        },
    )
    print(f"   Phase: {session.current_phase.value}")
    print(f"   PRD: {session.prd_reference.filename}")
    print(f"   Decisions: {session.statistics.decisions_made}")

    # Task Generation
    print("\n3. GENERATING_TASKS")
    session = manager.transition_state(
        session.session_id,
        SessionStatus.GENERATING_TASKS,
    )
    session = manager.update_session(
        session.session_id,
        {
            "current_phase": SessionPhase.GENERATE_TASKS,
            "statistics": {
                "total_tasks": 15,
            },
        },
    )
    print(f"   Tasks generated: {session.statistics.total_tasks}")

    # Implementation
    print("\n4. IMPLEMENTING")
    session = manager.transition_state(
        session.session_id,
        SessionStatus.IMPLEMENTING,
    )
    session = manager.update_session(
        session.session_id,
        {
            "current_phase": SessionPhase.IMPLEMENT,
            "statistics": {
                "completed_tasks": 10,
                "checkpoints_created": 3,
            },
        },
    )
    print(f"   Progress: {session.statistics.completed_tasks}/{session.statistics.total_tasks}")
    print(f"   Checkpoints: {session.statistics.checkpoints_created}")

    # Validation
    print("\n5. VALIDATING")
    session = manager.transition_state(session.session_id, SessionStatus.VALIDATING)
    session = manager.update_session(
        session.session_id,
        {
            "current_phase": SessionPhase.VALIDATE,
            "statistics": {
                "completed_tasks": 15,
            },
        },
    )
    print(f"   All tasks completed")

    # Report Generation
    print("\n6. GENERATING_REPORT")
    session = manager.transition_state(
        session.session_id,
        SessionStatus.GENERATING_REPORT,
    )
    session = manager.update_session(
        session.session_id,
        {
            "current_phase": SessionPhase.CLEANUP,
        },
    )

    # Completion
    print("\n7. COMPLETED")
    session = manager.transition_state(session.session_id, SessionStatus.COMPLETED)
    print_session_info(session, "Final Session State")

    # Show full session data
    print("\n8. Full Session Data:")
    print(json.dumps(session.to_dict(), indent=2))


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("  Session Manager Integration Examples")
    print("=" * 60)

    examples = [
        example_basic_workflow,
        example_pause_and_resume,
        example_query_sessions,
        example_error_handling,
        example_prd_tracking,
        example_full_lifecycle,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("  Examples Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
