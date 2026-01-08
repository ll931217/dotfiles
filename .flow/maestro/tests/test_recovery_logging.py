"""
Comprehensive tests for Recovery Audit Logging System.

Tests cover:
- Recovery attempt logging with full details
- Audit trail generation and persistence
- Export to JSON and CSV formats
- Recovery statistics calculation
- Session management
- Report generation
- Integration with AutoRecoveryManager
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import json
import time
import os

# Import the module under test
import sys
maestro_root = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(maestro_root))

from auto_recovery import (
    AutoRecoveryManager,
    RecoveryStrategyType,
    RecoveryAttempt,
    RecoveryAuditLogger,
    RecoveryAuditEntry,
    Error,
)


class TestRecoveryAuditEntry(unittest.TestCase):
    """Test RecoveryAuditEntry dataclass."""

    def test_audit_entry_creation(self):
        """Test creating a recovery audit entry."""
        entry = RecoveryAuditEntry(
            entry_id="entry_test123",
            timestamp="2024-01-01T00:00:00Z",
            session_id="session_abc123",
            error_type="SyntaxError",
            strategy="fix",
            attempt_number=1,
            success=True,
            changes_made=["Fixed syntax error"],
            files_modified=["/path/to/file.py"],
            rollback_performed=False,
            next_action="continue",
            duration_seconds=1.5,
            error_message="Invalid syntax",
            recovery_message="Recovery successful",
        )

        self.assertEqual(entry.entry_id, "entry_test123")
        self.assertEqual(entry.session_id, "session_abc123")
        self.assertTrue(entry.success)
        self.assertEqual(len(entry.changes_made), 1)

    def test_audit_entry_to_dict(self):
        """Test converting audit entry to dictionary."""
        entry = RecoveryAuditEntry(
            entry_id="entry_test",
            timestamp="2024-01-01T00:00:00Z",
            session_id="session_test",
            error_type="TestError",
            strategy="retry",
            attempt_number=1,
            success=False,
            changes_made=[],
            files_modified=[],
            rollback_performed=False,
            next_action="retry",
            duration_seconds=0.5,
            error_message="Test error",
            recovery_message="Failed",
        )

        entry_dict = entry.to_dict()

        self.assertIsInstance(entry_dict, dict)
        self.assertEqual(entry_dict["entry_id"], "entry_test")
        self.assertEqual(entry_dict["strategy"], "retry")
        self.assertFalse(entry_dict["success"])

    def test_audit_entry_to_json(self):
        """Test converting audit entry to JSON string."""
        entry = RecoveryAuditEntry(
            entry_id="entry_test",
            timestamp="2024-01-01T00:00:00Z",
            session_id="session_test",
            error_type="TestError",
            strategy="fix",
            attempt_number=1,
            success=True,
            changes_made=["Applied fix"],
            files_modified=["file.py"],
            rollback_performed=False,
            next_action="complete",
            duration_seconds=1.0,
            error_message="Error",
            recovery_message="Success",
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        self.assertEqual(parsed["entry_id"], "entry_test")
        self.assertTrue(parsed["success"])


class TestRecoveryAuditLogger(unittest.TestCase):
    """Test RecoveryAuditLogger functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_dir = Path(self.temp_dir) / "audit"
        self.logger = RecoveryAuditLogger(audit_dir=self.audit_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_logger_initialization(self):
        """Test logger initialization creates audit directory."""
        self.assertTrue(self.audit_dir.exists())
        self.assertEqual(self.logger.audit_dir, self.audit_dir)

    def test_start_session_default_id(self):
        """Test starting a session with auto-generated ID."""
        session_id = self.logger.start_session()

        self.assertIsNotNone(session_id)
        self.assertTrue(session_id.startswith("session_"))
        self.assertIn(session_id, self.logger._session_start_times)

    def test_start_session_custom_id(self):
        """Test starting a session with custom ID."""
        custom_id = "my_custom_session"
        session_id = self.logger.start_session(custom_id)

        self.assertEqual(session_id, custom_id)
        self.assertIn(custom_id, self.logger._session_start_times)

    def test_log_recovery_attempt(self):
        """Test logging a recovery attempt."""
        session_id = self.logger.start_session()

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=["Fixed syntax"],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.5,
            message="Recovery successful",
        )

        entry_id = self.logger.log_recovery_attempt(
            attempt=attempt,
            session_id=session_id,
            files_modified=["test.py"],
            rollback_performed=False,
            next_action="complete",
        )

        self.assertIsNotNone(entry_id)
        self.assertTrue(entry_id.startswith("entry_"))

        # Verify entry was stored
        entries = self.logger.get_recovery_history(session_id)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].entry_id, entry_id)

    def test_log_multiple_attempts(self):
        """Test logging multiple recovery attempts."""
        session_id = self.logger.start_session()
        error = Error(error_type="TestError", message="Test", source="test")

        for i in range(3):
            attempt = RecoveryAttempt(
                attempt_number=i + 1,
                strategy="retry",
                success=i == 2,  # Last attempt succeeds
                error_before=error,
                error_after=None,
                changes_made=[f"Attempt {i+1}"],
                timestamp="2024-01-01T00:00:00Z",
                duration_seconds=1.0,
                message="Attempt",
            )

            self.logger.log_recovery_attempt(attempt, session_id)

        entries = self.logger.get_recovery_history(session_id)
        self.assertEqual(len(entries), 3)

    def test_get_recovery_history_empty_session(self):
        """Test getting history for non-existent session."""
        history = self.logger.get_recovery_history("nonexistent_session")
        self.assertEqual(len(history), 0)

    def test_get_all_session_ids(self):
        """Test getting all session IDs."""
        session1 = self.logger.start_session()
        session2 = self.logger.start_session()

        all_sessions = self.logger.get_all_session_ids()

        self.assertIn(session1, all_sessions)
        self.assertIn(session2, all_sessions)

    def test_export_audit_trail_json(self):
        """Test exporting audit trail to JSON."""
        session_id = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=["Fixed"],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.0,
            message="Success",
        )

        self.logger.log_recovery_attempt(attempt, session_id)

        export_path = self.logger.export_audit_trail(session_id, format="json")

        self.assertTrue(Path(export_path).exists())

        # Verify JSON structure
        with open(export_path) as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(data["total_entries"], 1)
        self.assertIn("entries", data)

    def test_export_audit_trail_csv(self):
        """Test exporting audit trail to CSV."""
        session_id = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=["Fixed"],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.0,
            message="Success",
        )

        self.logger.log_recovery_attempt(attempt, session_id)

        export_path = self.logger.export_audit_trail(session_id, format="csv")

        self.assertTrue(Path(export_path).exists())
        self.assertTrue(export_path.endswith(".csv"))

    def test_export_audit_trail_empty_session(self):
        """Test exporting audit trail for empty session."""
        session_id = self.logger.start_session()

        with self.assertRaises(ValueError):
            self.logger.export_audit_trail(session_id)

    def test_export_audit_trail_invalid_format(self):
        """Test exporting with invalid format."""
        session_id = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=[],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.0,
            message="Success",
        )

        self.logger.log_recovery_attempt(attempt, session_id)

        with self.assertRaises(ValueError):
            self.logger.export_audit_trail(session_id, format="invalid")

    def test_get_recovery_statistics_empty(self):
        """Test statistics for empty session."""
        stats = self.logger.get_recovery_statistics("nonexistent_session")

        self.assertEqual(stats["total_attempts"], 0)
        self.assertEqual(stats["successful_attempts"], 0)
        self.assertEqual(stats["success_rate"], 0.0)

    def test_get_recovery_statistics_with_data(self):
        """Test statistics calculation with actual data."""
        session_id = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")

        # Add multiple attempts
        for i in range(5):
            attempt = RecoveryAttempt(
                attempt_number=i + 1,
                strategy="fix" if i < 3 else "retry",
                success=i >= 3,  # Last 2 succeed
                error_before=error,
                error_after=None,
                changes_made=[f"Change {i}"],
                timestamp="2024-01-01T00:00:00Z",
                duration_seconds=1.0 + i * 0.5,
                message=f"Attempt {i+1}",
            )

            files_modified = [f"file{i}.py"] if i < 2 else []

            self.logger.log_recovery_attempt(
                attempt,
                session_id,
                files_modified=files_modified,
                rollback_performed=(i == 4),
                next_action="complete" if i >= 3 else "retry",
            )

        stats = self.logger.get_recovery_statistics(session_id)

        self.assertEqual(stats["total_attempts"], 5)
        self.assertEqual(stats["successful_attempts"], 2)
        self.assertEqual(stats["failed_attempts"], 3)
        self.assertEqual(stats["success_rate"], 40.0)
        self.assertEqual(stats["strategies_used"]["fix"], 3)
        self.assertEqual(stats["strategies_used"]["retry"], 2)
        self.assertEqual(stats["rollback_count"], 1)
        self.assertEqual(stats["files_modified_count"], 2)

    def test_generate_recovery_report(self):
        """Test generating comprehensive recovery report."""
        session_id = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=["Fixed"],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.5,
            message="Success",
        )

        self.logger.log_recovery_attempt(attempt, session_id)

        report_path = self.logger.generate_recovery_report(session_id)

        self.assertTrue(Path(report_path).exists())

        # Verify report structure
        with open(report_path) as f:
            report = json.load(f)

        self.assertIn("report_metadata", report)
        self.assertIn("summary", report)
        self.assertIn("statistics", report)
        self.assertIn("detailed_entries", report)

    def test_clear_session(self):
        """Test clearing a specific session."""
        session_id = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=[],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.0,
            message="Success",
        )

        self.logger.log_recovery_attempt(attempt, session_id)
        self.assertEqual(len(self.logger.get_recovery_history(session_id)), 1)

        self.logger.clear_session(session_id)

        self.assertEqual(len(self.logger.get_recovery_history(session_id)), 0)
        self.assertNotIn(session_id, self.logger._session_start_times)

    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        session1 = self.logger.start_session()
        session2 = self.logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=[],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.0,
            message="Success",
        )

        self.logger.log_recovery_attempt(attempt, session1)
        self.logger.log_recovery_attempt(attempt, session2)

        self.assertGreater(len(self.logger.get_all_session_ids()), 0)

        self.logger.clear_all_sessions()

        self.assertEqual(len(self.logger.get_all_session_ids()), 0)

    def test_persistent_audit_file(self):
        """Test that audit entries are written to file immediately."""
        # Create a fresh logger with a unique directory to avoid conflicts
        import uuid
        import shutil
        unique_dir = Path(self.temp_dir) / f"audit_persistent_{uuid.uuid4().hex[:8]}"
        fresh_logger = RecoveryAuditLogger(audit_dir=unique_dir)

        session_id = fresh_logger.start_session()

        error = Error(error_type="TestError", message="Test", source="test")
        attempt = RecoveryAttempt(
            attempt_number=1,
            strategy="fix",
            success=True,
            error_before=error,
            error_after=None,
            changes_made=[],
            timestamp="2024-01-01T00:00:00Z",
            duration_seconds=1.0,
            message="Success",
        )

        fresh_logger.log_recovery_attempt(attempt, session_id)

        # Check that file was created
        audit_file = unique_dir / f"{session_id}_audit.jsonl"
        self.assertTrue(audit_file.exists())

        # Verify file content - read entire file and parse JSON objects
        with open(audit_file) as f:
            content = f.read()

        # Count complete JSON objects (they start with { and end with })
        json_objects = content.strip().split('\n')
        # Filter out empty strings and count actual objects
        json_objects = [obj for obj in json_objects if obj.strip().startswith('{')]

        # Note: JSON with indentation spans multiple lines, so we count objects differently
        # We'll verify that we can parse at least one complete entry
        entries_found = 0
        for line in content.split('\n'):
            if '"entry_id"' in line:
                entries_found += 1

        self.assertGreaterEqual(entries_found, 1)

        # Parse and verify at least one complete JSON object
        # Read the file and extract JSON objects
        with open(audit_file) as f:
            file_content = f.read()

        # Find complete JSON objects by parsing
        import re
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, file_content, re.DOTALL)

        self.assertGreater(len(matches), 0)
        entry_data = json.loads(matches[0])
        self.assertEqual(entry_data["session_id"], session_id)


class TestAutoRecoveryManagerIntegration(unittest.TestCase):
    """Test integration of audit logging with AutoRecoveryManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_dir = Path(self.temp_dir) / "audit"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_manager_with_audit_logging_enabled(self):
        """Test that audit logging works when enabled."""
        manager = AutoRecoveryManager(
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        self.assertIsNotNone(manager.audit_logger)
        self.assertTrue(manager.enable_audit_logging)

    def test_manager_with_audit_logging_disabled(self):
        """Test that audit logging can be disabled."""
        manager = AutoRecoveryManager(enable_audit_logging=False)

        self.assertIsNone(manager.audit_logger)
        self.assertFalse(manager.enable_audit_logging)

    def test_recovery_attempt_is_logged(self):
        """Test that recovery attempts are logged to audit trail."""
        manager = AutoRecoveryManager(
            max_attempts=2,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        # Configure a successful fix
        manager.fix_generator = lambda e: "Fix applied"

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = manager.attempt_recovery(error, {})

        self.assertTrue(result.success)

        # Verify audit logging occurred
        self.assertIsNotNone(manager.current_session_id)
        audit_trail = manager.get_audit_trail()
        self.assertGreater(len(audit_trail), 0)

    def test_multiple_recovery_attempts_logged(self):
        """Test that multiple recovery attempts are all logged."""
        manager = AutoRecoveryManager(
            max_attempts=3,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        # Configure to fail first 2 attempts, succeed on 3rd
        attempt_count = [0]

        def failing_fix(error):
            attempt_count[0] += 1
            return None if attempt_count[0] < 3 else "Fix applied"

        manager.fix_generator = failing_fix

        error = Error(
            error_type="SyntaxError",
            message="Invalid syntax",
            source="linter",
        )

        result = manager.attempt_recovery(error, {})

        self.assertTrue(result.success)

        # Verify multiple attempts were logged
        audit_trail = manager.get_audit_trail()
        self.assertGreaterEqual(len(audit_trail), 3)

    def test_get_recovery_statistics_from_manager(self):
        """Test getting statistics through manager."""
        manager = AutoRecoveryManager(
            max_attempts=2,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        manager.fix_generator = lambda e: "Fix applied"

        error = Error(error_type="TestError", message="Test", source="test")
        manager.attempt_recovery(error, {})

        stats = manager.get_recovery_statistics()

        self.assertIn("total_attempts", stats)
        self.assertIn("success_rate", stats)
        self.assertGreater(stats["total_attempts"], 0)

    def test_export_audit_trail_from_manager(self):
        """Test exporting audit trail through manager."""
        manager = AutoRecoveryManager(
            max_attempts=2,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        manager.fix_generator = lambda e: "Fix applied"

        error = Error(error_type="TestError", message="Test", source="test")
        manager.attempt_recovery(error, {})

        export_path = manager.export_audit_trail(format="json")

        self.assertIsNotNone(export_path)
        self.assertTrue(Path(export_path).exists())

    def test_generate_recovery_report_from_manager(self):
        """Test generating recovery report through manager."""
        manager = AutoRecoveryManager(
            max_attempts=2,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        manager.fix_generator = lambda e: "Fix applied"

        error = Error(error_type="TestError", message="Test", source="test")
        manager.attempt_recovery(error, {})

        report_path = manager.generate_recovery_report()

        self.assertIsNotNone(report_path)
        self.assertTrue(Path(report_path).exists())

        # Verify report structure
        with open(report_path) as f:
            report = json.load(f)

        self.assertIn("report_metadata", report)
        self.assertIn("summary", report)

    def test_start_new_session(self):
        """Test starting a new audit session."""
        manager = AutoRecoveryManager(
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        session1 = manager.start_new_session()
        self.assertIsNotNone(session1)

        session2 = manager.start_new_session()
        self.assertIsNotNone(session2)

        self.assertNotEqual(session1, session2)

    def test_clear_audit_history(self):
        """Test clearing audit history through manager."""
        manager = AutoRecoveryManager(
            max_attempts=2,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        manager.fix_generator = lambda e: "Fix applied"

        error = Error(error_type="TestError", message="Test", source="test")
        manager.attempt_recovery(error, {})

        self.assertGreater(len(manager.get_audit_trail()), 0)

        manager.clear_audit_history()

        # After clearing, session ID should be None
        self.assertIsNone(manager.current_session_id)

    def test_audit_logging_disabled_no_errors(self):
        """Test that disabling audit logging doesn't cause errors."""
        manager = AutoRecoveryManager(
            enable_audit_logging=False,
        )

        manager.fix_generator = lambda e: "Fix applied"

        error = Error(error_type="TestError", message="Test", source="test")
        result = manager.attempt_recovery(error, {})

        self.assertTrue(result.success)

        # These should return None or empty without errors
        self.assertIsNone(manager.export_audit_trail())
        self.assertEqual(manager.get_recovery_statistics(), {})
        self.assertIsNone(manager.generate_recovery_report())

    def test_failed_recovery_is_logged(self):
        """Test that failed recovery attempts are logged."""
        manager = AutoRecoveryManager(
            max_attempts=2,
            audit_dir=self.audit_dir,
            enable_audit_logging=True,
        )

        # Configure all strategies to fail
        manager.fix_generator = lambda e: None
        manager.retry_handler = None
        manager.alternative_selector = None
        manager.rollback_handler = None

        error = Error(
            error_type="UnfixableError",
            message="Cannot be fixed",
            source="test",
        )

        result = manager.attempt_recovery(error, {})

        self.assertFalse(result.success)
        self.assertTrue(result.escalated_to_human)

        # Verify failed attempts were logged
        audit_trail = manager.get_audit_trail()
        self.assertGreater(len(audit_trail), 0)

        # Check that entries show failures
        failed_attempts = [e for e in audit_trail if not e["success"]]
        self.assertGreater(len(failed_attempts), 0)


class TestRecoveryStatisticsCalculation(unittest.TestCase):
    """Test recovery statistics calculation in detail."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_dir = Path(self.temp_dir) / "audit"
        self.logger = RecoveryAuditLogger(audit_dir=self.audit_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_success_rate_calculation(self):
        """Test accurate success rate calculation."""
        session_id = self.logger.start_session()
        error = Error(error_type="TestError", message="Test", source="test")

        # 3 success, 2 failures
        for i in range(5):
            attempt = RecoveryAttempt(
                attempt_number=i + 1,
                strategy="fix",
                success=i < 3,
                error_before=error,
                error_after=None,
                changes_made=[],
                timestamp="2024-01-01T00:00:00Z",
                duration_seconds=1.0,
                message="",
            )

            self.logger.log_recovery_attempt(attempt, session_id)

        stats = self.logger.get_recovery_statistics(session_id)
        self.assertEqual(stats["success_rate"], 60.0)

    def test_duration_statistics(self):
        """Test duration statistics calculation."""
        session_id = self.logger.start_session()
        error = Error(error_type="TestError", message="Test", source="test")

        durations = [1.0, 2.5, 3.0, 1.5]

        for i, duration in enumerate(durations):
            attempt = RecoveryAttempt(
                attempt_number=i + 1,
                strategy="fix",
                success=True,
                error_before=error,
                error_after=None,
                changes_made=[],
                timestamp="2024-01-01T00:00:00Z",
                duration_seconds=duration,
                message="",
            )

            self.logger.log_recovery_attempt(attempt, session_id)

        stats = self.logger.get_recovery_statistics(session_id)

        expected_total = sum(durations)
        expected_avg = expected_total / len(durations)

        self.assertEqual(stats["total_duration_seconds"], round(expected_total, 3))
        self.assertEqual(stats["average_duration_seconds"], round(expected_avg, 3))

    def test_error_type_distribution(self):
        """Test error type distribution tracking."""
        session_id = self.logger.start_session()

        # Different error types
        error_types = ["SyntaxError", "ImportError", "TypeError", "SyntaxError", "SyntaxError"]

        for error_type in error_types:
            error = Error(error_type=error_type, message="Test", source="test")
            attempt = RecoveryAttempt(
                attempt_number=1,
                strategy="fix",
                success=True,
                error_before=error,
                error_after=None,
                changes_made=[],
                timestamp="2024-01-01T00:00:00Z",
                duration_seconds=1.0,
                message="",
            )

            self.logger.log_recovery_attempt(attempt, session_id)

        stats = self.logger.get_recovery_statistics(session_id)

        self.assertEqual(stats["error_type_distribution"]["SyntaxError"], 3)
        self.assertEqual(stats["error_type_distribution"]["ImportError"], 1)
        self.assertEqual(stats["error_type_distribution"]["TypeError"], 1)

    def test_files_modified_tracking(self):
        """Test tracking of modified files across attempts."""
        session_id = self.logger.start_session()
        error = Error(error_type="TestError", message="Test", source="test")

        files_sets = [
            ["file1.py", "file2.py"],
            ["file2.py", "file3.py"],
            ["file1.py", "file4.py"],
        ]

        for files in files_sets:
            attempt = RecoveryAttempt(
                attempt_number=1,
                strategy="fix",
                success=True,
                error_before=error,
                error_after=None,
                changes_made=[],
                timestamp="2024-01-01T00:00:00Z",
                duration_seconds=1.0,
                message="",
            )

            self.logger.log_recovery_attempt(attempt, session_id, files_modified=files)

        stats = self.logger.get_recovery_statistics(session_id)

        # Should have unique files
        expected_files = {"file1.py", "file2.py", "file3.py", "file4.py"}
        self.assertEqual(stats["files_modified_count"], 4)
        self.assertEqual(set(stats["files_modified"]), expected_files)


if __name__ == "__main__":
    unittest.main()
