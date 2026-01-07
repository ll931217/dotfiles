#!/usr/bin/env python3
"""
Unit tests for Session Manager

Tests session creation, state transitions, persistence, and querying.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from session_manager import (
    Session,
    SessionStatus,
    SessionPhase,
    SessionManager,
    GitContext,
    PRDReference,
    SessionStatistics,
    SessionConfiguration,
)


class TestSessionStatus(unittest.TestCase):
    """Test SessionStatus enum."""

    def test_status_values(self):
        """Test all status values are defined."""
        expected_statuses = [
            "initializing",
            "planning",
            "generating_tasks",
            "implementing",
            "validating",
            "generating_report",
            "completed",
            "failed",
            "paused",
        ]

        for status in expected_statuses:
            self.assertTrue(hasattr(SessionStatus, status.upper()))


class TestSessionPhase(unittest.TestCase):
    """Test SessionPhase enum."""

    def test_phase_values(self):
        """Test all phase values are defined."""
        expected_phases = [
            "plan",
            "generate_tasks",
            "implement",
            "validate",
            "cleanup",
        ]

        for phase in expected_phases:
            self.assertTrue(hasattr(SessionPhase, phase.upper()))


class TestGitContext(unittest.TestCase):
    """Test GitContext dataclass."""

    def test_to_dict(self):
        """Test GitContext serialization."""
        ctx = GitContext(
            branch="main",
            commit="abc123",
            repo_root="/tmp/repo",
            is_worktree=False,
        )

        data = ctx.to_dict()

        self.assertEqual(data["branch"], "main")
        self.assertEqual(data["commit"], "abc123")
        self.assertEqual(data["repo_root"], "/tmp/repo")
        self.assertEqual(data["is_worktree"], False)
        self.assertNotIn("worktree_name", data)

    def test_to_dict_with_worktree(self):
        """Test GitContext with worktree."""
        ctx = GitContext(
            branch="feature",
            commit="def456",
            repo_root="/tmp/repo",
            is_worktree=True,
            worktree_name="feature-branch",
        )

        data = ctx.to_dict()

        self.assertEqual(data["is_worktree"], True)
        self.assertEqual(data["worktree_name"], "feature-branch")


class TestPRDReference(unittest.TestCase):
    """Test PRDReference dataclass."""

    def test_to_dict(self):
        """Test PRDReference serialization."""
        prd = PRDReference(
            filename="prd.md",
            path="/tmp/repo/.flow/prd.md",
        )

        data = prd.to_dict()

        self.assertEqual(data["filename"], "prd.md")
        self.assertEqual(data["path"], "/tmp/repo/.flow/prd.md")
        self.assertNotIn("version", data)

    def test_to_dict_with_version(self):
        """Test PRDReference with version."""
        prd = PRDReference(
            filename="prd.md",
            path="/tmp/repo/.flow/prd.md",
            version="1.0.0",
        )

        data = prd.to_dict()

        self.assertEqual(data["version"], "1.0.0")


class TestSession(unittest.TestCase):
    """Test Session dataclass."""

    def test_session_creation(self):
        """Test basic session creation."""
        session_id = str(uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        git_ctx = GitContext(
            branch="main",
            commit="abc123",
            repo_root="/tmp/repo",
        )

        session = Session(
            session_id=session_id,
            feature_request="Add user authentication",
            status=SessionStatus.INITIALIZING,
            created_at=now,
            git_context=git_ctx,
        )

        self.assertEqual(session.session_id, session_id)
        self.assertEqual(session.feature_request, "Add user authentication")
        self.assertEqual(session.status, SessionStatus.INITIALIZING)

    def test_to_dict(self):
        """Test session serialization."""
        session_id = str(uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        git_ctx = GitContext(
            branch="main",
            commit="abc123",
            repo_root="/tmp/repo",
        )

        session = Session(
            session_id=session_id,
            feature_request="Add user authentication",
            status=SessionStatus.PLANNING,
            created_at=now,
            git_context=git_ctx,
            current_phase=SessionPhase.PLAN,
        )

        data = session.to_dict()

        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(data["status"], "planning")
        self.assertEqual(data["current_phase"], "plan")
        self.assertIn("git_context", data)
        self.assertIn("statistics", data)
        self.assertIn("configuration", data)


class TestSessionManager(unittest.TestCase):
    """Test SessionManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SessionManager(repo_root=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_session(self):
        """Test session creation."""
        feature_request = "Implement OAuth login"

        session = self.manager.create_session(feature_request)

        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.feature_request, feature_request)
        self.assertEqual(session.status, SessionStatus.INITIALIZING)
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.git_context)

    def test_create_session_with_configuration(self):
        """Test session creation with custom configuration."""
        config = SessionConfiguration(
            max_iterations=5,
            timeout_minutes=60,
            auto_checkpoint=False,
        )

        session = self.manager.create_session("Test feature", config)

        self.assertEqual(session.configuration.max_iterations, 5)
        self.assertEqual(session.configuration.timeout_minutes, 60)
        self.assertEqual(session.configuration.auto_checkpoint, False)

    def test_get_session(self):
        """Test retrieving a session."""
        created = self.manager.create_session("Test feature")
        retrieved = self.manager.get_session(created.session_id)

        self.assertEqual(created.session_id, retrieved.session_id)
        self.assertEqual(created.feature_request, retrieved.feature_request)
        self.assertEqual(created.status, retrieved.status)

    def test_get_nonexistent_session(self):
        """Test retrieving non-existent session raises error."""
        with self.assertRaises(FileNotFoundError):
            self.manager.get_session("nonexistent-id")

    def test_update_session(self):
        """Test updating session fields."""
        session = self.manager.create_session("Test feature")

        # Update statistics
        updated = self.manager.update_session(
            session.session_id,
            {
                "statistics": {
                    "total_tasks": 10,
                    "completed_tasks": 5,
                },
            },
        )

        self.assertEqual(updated.statistics.total_tasks, 10)
        self.assertEqual(updated.statistics.completed_tasks, 5)

    def test_update_session_status(self):
        """Test updating session status."""
        session = self.manager.create_session("Test feature")

        updated = self.manager.update_session(
            session.session_id,
            {"status": "planning"},
        )

        self.assertEqual(updated.status, SessionStatus.PLANNING)

    def test_update_session_with_prd_reference(self):
        """Test updating session with PRD reference."""
        session = self.manager.create_session("Test feature")

        updated = self.manager.update_session(
            session.session_id,
            {
                "prd_reference": {
                    "filename": "prd.md",
                    "path": "/tmp/prd.md",
                    "version": "1.0",
                },
            },
        )

        self.assertIsNotNone(updated.prd_reference)
        self.assertEqual(updated.prd_reference.filename, "prd.md")

    def test_transition_state_valid(self):
        """Test valid state transition."""
        session = self.manager.create_session("Test feature")

        # initializing -> planning
        updated = self.manager.transition_state(
            session.session_id,
            SessionStatus.PLANNING,
        )

        self.assertEqual(updated.status, SessionStatus.PLANNING)

    def test_transition_state_invalid(self):
        """Test invalid state transition raises error."""
        session = self.manager.create_session("Test feature")

        # Can't jump from initializing to completed
        with self.assertRaises(ValueError):
            self.manager.transition_state(
                session.session_id,
                SessionStatus.COMPLETED,
            )

    def test_transition_to_completed_sets_timestamp(self):
        """Test transitioning to completed sets completed_at."""
        session = self.manager.create_session("Test feature")

        # Transition through the lifecycle
        self.manager.transition_state(session.session_id, SessionStatus.PLANNING)
        self.manager.transition_state(
            session.session_id,
            SessionStatus.GENERATING_TASKS,
        )
        self.manager.transition_state(session.session_id, SessionStatus.IMPLEMENTING)
        self.manager.transition_state(session.session_id, SessionStatus.VALIDATING)
        self.manager.transition_state(
            session.session_id,
            SessionStatus.GENERATING_REPORT,
        )
        updated = self.manager.transition_state(
            session.session_id,
            SessionStatus.COMPLETED,
        )

        self.assertIsNotNone(updated.completed_at)

    def test_query_sessions_by_status(self):
        """Test querying sessions by status."""
        s1 = self.manager.create_session("Feature 1")
        s2 = self.manager.create_session("Feature 2")

        self.manager.update_session(s1.session_id, {"status": "planning"})
        self.manager.update_session(s2.session_id, {"status": "implementing"})

        results = self.manager.query_sessions(status=SessionStatus.PLANNING)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].session_id, s1.session_id)

    def test_query_sessions_by_branch(self):
        """Test querying sessions by git branch."""
        session = self.manager.create_session("Test feature")

        results = self.manager.query_sessions(branch=session.git_context.branch)

        self.assertGreater(len(results), 0)

    def test_query_sessions_with_limit(self):
        """Test query limit."""
        self.manager.create_session("Feature 1")
        self.manager.create_session("Feature 2")
        self.manager.create_session("Feature 3")

        results = self.manager.query_sessions(limit=2)

        self.assertEqual(len(results), 2)

    def test_query_sessions_sorting(self):
        """Test sessions are sorted by creation time."""
        s1 = self.manager.create_session("Feature 1")
        s2 = self.manager.create_session("Feature 2")

        results = self.manager.query_sessions()

        # Most recent first
        self.assertEqual(results[0].session_id, s2.session_id)
        self.assertEqual(results[1].session_id, s1.session_id)

    def test_list_active_sessions(self):
        """Test listing active sessions."""
        s1 = self.manager.create_session("Feature 1")
        s2 = self.manager.create_session("Feature 2")

        # Mark s2 as completed
        self.manager.transition_state(s2.session_id, SessionStatus.PLANNING)
        self.manager.transition_state(
            s2.session_id,
            SessionStatus.GENERATING_TASKS,
        )
        self.manager.transition_state(s2.session_id, SessionStatus.IMPLEMENTING)
        self.manager.transition_state(s2.session_id, SessionStatus.VALIDATING)
        self.manager.transition_state(s2.session_id, SessionStatus.GENERATING_REPORT)
        self.manager.transition_state(s2.session_id, SessionStatus.COMPLETED)

        active = self.manager.list_active_sessions()

        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].session_id, s1.session_id)

    def test_get_recent_sessions(self):
        """Test getting recent sessions."""
        self.manager.create_session("Feature 1")
        self.manager.create_session("Feature 2")
        self.manager.create_session("Feature 3")

        recent = self.manager.get_recent_sessions(count=2)

        self.assertEqual(len(recent), 2)

    def test_delete_session(self):
        """Test deleting a session."""
        session = self.manager.create_session("Test feature")

        self.manager.delete_session(session.session_id)

        with self.assertRaises(FileNotFoundError):
            self.manager.get_session(session.session_id)

    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session raises error."""
        with self.assertRaises(FileNotFoundError):
            self.manager.delete_session("nonexistent-id")

    def test_session_persistence(self):
        """Test session data persists across manager instances."""
        # Create session with first manager instance
        session1 = self.manager.create_session("Test feature")
        session1_id = session1.session_id

        # Create new manager instance
        manager2 = SessionManager(repo_root=self.temp_dir)

        # Retrieve session with new instance
        session2 = manager2.get_session(session1_id)

        self.assertEqual(session1.session_id, session2.session_id)
        self.assertEqual(session1.feature_request, session2.feature_request)

    def test_pause_and_resume(self):
        """Test pausing and resuming a session."""
        session = self.manager.create_session("Test feature")

        # Pause during planning
        self.manager.transition_state(session.session_id, SessionStatus.PLANNING)
        paused = self.manager.transition_state(session.session_id, SessionStatus.PAUSED)

        self.assertEqual(paused.status, SessionStatus.PAUSED)

        # Resume
        resumed = self.manager.transition_state(
            session.session_id,
            SessionStatus.PLANNING,
        )

        self.assertEqual(resumed.status, SessionStatus.PLANNING)

    def test_failed_state(self):
        """Test transition to failed state."""
        session = self.manager.create_session("Test feature")

        failed = self.manager.transition_state(session.session_id, SessionStatus.FAILED)

        self.assertEqual(failed.status, SessionStatus.FAILED)
        self.assertIsNotNone(failed.completed_at)


class TestStateTransitions(unittest.TestCase):
    """Test state transition rules."""

    def test_all_states_defined(self):
        """Test all states have transition rules."""
        for status in SessionStatus:
            self.assertIn(
                status,
                SessionManager.STATE_TRANSITIONS,
                f"No transitions defined for {status}",
            )

    def test_terminal_states_have_no_transitions(self):
        """Test terminal states cannot transition."""
        terminal_states = [SessionStatus.COMPLETED, SessionStatus.FAILED]

        for state in terminal_states:
            transitions = SessionManager.STATE_TRANSITIONS[state]
            self.assertEqual(
                len(transitions),
                0,
                f"{state} should be terminal but has transitions",
            )

    def test_paused_state_can_resume(self):
        """Test paused state can resume to multiple states."""
        paused_transitions = SessionManager.STATE_TRANSITIONS[SessionStatus.PAUSED]

        self.assertGreater(len(paused_transitions), 0)
        self.assertIn(SessionStatus.PLANNING, paused_transitions)


if __name__ == "__main__":
    unittest.main()
