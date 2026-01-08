#!/usr/bin/env python3
"""
Tests for Resource Monitor

Comprehensive unit tests for resource_monitor.py module.
"""

import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from resource_monitor import (
    ResourceMonitor,
    ResourceLimits,
    ResourceUsage,
    LimitStatus,
    LimitCheckResult,
)


class TestResourceLimits(unittest.TestCase):
    """Test ResourceLimits dataclass."""

    def test_default_limits(self):
        """Test default limit values."""
        limits = ResourceLimits()
        self.assertEqual(limits.max_duration_seconds, 3600)
        self.assertEqual(limits.max_tokens, 1000000)
        self.assertEqual(limits.max_api_calls, 1000)
        self.assertEqual(limits.checkpoint_interval, 300)

    def test_custom_limits(self):
        """Test custom limit values."""
        limits = ResourceLimits(
            max_duration_seconds=1800,
            max_tokens=500000,
            max_api_calls=500,
            checkpoint_interval=600,
        )
        self.assertEqual(limits.max_duration_seconds, 1800)
        self.assertEqual(limits.max_tokens, 500000)
        self.assertEqual(limits.max_api_calls, 500)
        self.assertEqual(limits.checkpoint_interval, 600)

    def test_warning_thresholds(self):
        """Test warning threshold defaults."""
        limits = ResourceLimits()
        self.assertEqual(limits.duration_warning_threshold, 0.80)
        self.assertEqual(limits.token_warning_threshold, 0.80)
        self.assertEqual(limits.api_call_warning_threshold, 0.80)
        self.assertEqual(limits.completion_threshold, 0.80)


class TestResourceUsage(unittest.TestCase):
    """Test ResourceUsage dataclass."""

    def test_usage_initialization(self):
        """Test ResourceUsage initialization."""
        start_time = datetime.now()
        usage = ResourceUsage(
            duration_seconds=100.0,
            tokens_used=1000,
            api_calls_made=10,
            checkpoints_created=2,
            start_time=start_time,
            last_operation_time=start_time,
        )
        self.assertEqual(usage.duration_seconds, 100.0)
        self.assertEqual(usage.tokens_used, 1000)
        self.assertEqual(usage.api_calls_made, 10)
        self.assertEqual(usage.checkpoints_created, 2)

    def test_usage_to_dict(self):
        """Test ResourceUsage serialization to dict."""
        start_time = datetime.now()
        usage = ResourceUsage(
            duration_seconds=100.0,
            tokens_used=1000,
            api_calls_made=10,
            checkpoints_created=2,
            start_time=start_time,
            last_operation_time=start_time,
            last_checkpoint_time=start_time,
        )
        data = usage.to_dict()
        self.assertEqual(data["duration_seconds"], 100.0)
        self.assertEqual(data["tokens_used"], 1000)
        self.assertEqual(data["api_calls_made"], 10)
        self.assertEqual(data["checkpoints_created"], 2)
        self.assertIn("start_time", data)
        self.assertIn("last_operation_time", data)
        self.assertIn("last_checkpoint_time", data)

    def test_usage_from_dict(self):
        """Test ResourceUsage deserialization from dict."""
        start_time = datetime.now()
        data = {
            "duration_seconds": 100.0,
            "tokens_used": 1000,
            "api_calls_made": 10,
            "checkpoints_created": 2,
            "start_time": start_time.isoformat(),
            "last_operation_time": start_time.isoformat(),
            "last_checkpoint_time": start_time.isoformat(),
        }
        usage = ResourceUsage.from_dict(data)
        self.assertEqual(usage.duration_seconds, 100.0)
        self.assertEqual(usage.tokens_used, 1000)
        self.assertEqual(usage.api_calls_made, 10)
        self.assertEqual(usage.checkpoints_created, 2)

    def test_usage_from_dict_none_checkpoint(self):
        """Test ResourceUsage deserialization with None checkpoint."""
        start_time = datetime.now()
        data = {
            "duration_seconds": 100.0,
            "tokens_used": 1000,
            "api_calls_made": 10,
            "checkpoints_created": 0,
            "start_time": start_time.isoformat(),
            "last_operation_time": start_time.isoformat(),
            "last_checkpoint_time": None,
        }
        usage = ResourceUsage.from_dict(data)
        self.assertIsNone(usage.last_checkpoint_time)


class TestLimitCheckResult(unittest.TestCase):
    """Test LimitCheckResult dataclass."""

    def test_ok_result(self):
        """Test OK limit check result."""
        result = LimitCheckResult(status=LimitStatus.OK, can_continue=True)
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)
        self.assertEqual(len(result.approaching_limits), 0)
        self.assertEqual(len(result.exceeded_limits), 0)

    def test_approaching_result(self):
        """Test APPROACHING limit check result."""
        result = LimitCheckResult(
            status=LimitStatus.APPROACHING,
            approaching_limits=["tokens", "api_calls"],
            can_continue=True,
            reason="Approaching limits: tokens, api_calls",
        )
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertTrue(result.can_continue)
        self.assertEqual(len(result.approaching_limits), 2)
        self.assertIn("tokens", result.approaching_limits)
        self.assertIn("api_calls", result.approaching_limits)

    def test_exceeded_result(self):
        """Test EXCEEDED limit check result."""
        result = LimitCheckResult(
            status=LimitStatus.EXCEEDED,
            exceeded_limits=["duration"],
            can_continue=False,
            reason="Exceeded limits: duration",
        )
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertFalse(result.can_continue)
        self.assertEqual(len(result.exceeded_limits), 1)
        self.assertIn("duration", result.exceeded_limits)

    def test_to_dict(self):
        """Test LimitCheckResult serialization."""
        result = LimitCheckResult(
            status=LimitStatus.APPROACHING,
            approaching_limits=["tokens"],
            exceeded_limits=[],
            can_continue=True,
            reason="Approaching limits: tokens",
        )
        data = result.to_dict()
        self.assertEqual(data["status"], "approaching")
        self.assertEqual(data["can_continue"], True)
        self.assertEqual(len(data["approaching_limits"]), 1)
        self.assertEqual(len(data["exceeded_limits"]), 0)


class TestResourceMonitorInitialization(unittest.TestCase):
    """Test ResourceMonitor initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,  # 10 minutes
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,  # 1 minute
        )
        self.session_id = "test-session-123"

    def test_basic_initialization(self):
        """Test basic ResourceMonitor initialization."""
        monitor = ResourceMonitor(self.limits, self.session_id)
        self.assertEqual(monitor.limits, self.limits)
        self.assertEqual(monitor.session_id, self.session_id)
        self.assertIsNone(monitor.project_root)

    def test_initialization_with_project_root(self):
        """Test initialization with project root."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            monitor = ResourceMonitor(self.limits, self.session_id, project_root)
            self.assertEqual(monitor.project_root, project_root)

    def test_initial_usage_state(self):
        """Test initial usage state is correct."""
        monitor = ResourceMonitor(self.limits, self.session_id)
        usage = monitor.get_usage_report()
        self.assertEqual(usage.tokens_used, 0)
        self.assertEqual(usage.api_calls_made, 0)
        self.assertEqual(usage.checkpoints_created, 0)
        self.assertIsNotNone(usage.start_time)
        self.assertIsNotNone(usage.last_operation_time)


class TestResourceMonitorLimitChecking(unittest.TestCase):
    """Test ResourceMonitor limit checking functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id)

    def test_check_limits_initial_state(self):
        """Test limit checking in initial state."""
        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)
        self.assertEqual(len(result.approaching_limits), 0)
        self.assertEqual(len(result.exceeded_limits), 0)

    def test_check_limits_ok_status(self):
        """Test limit checking with OK status."""
        # Use 50% of each resource
        self.monitor.record_operation(tokens=5000, api_call=50)
        # Simulate some time passing (less than warning threshold)
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=300)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)

    def test_check_limits_approaching_duration(self):
        """Test limit checking with approaching duration limit."""
        # Set time to 85% of limit
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=510)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("duration", result.approaching_limits)
        self.assertTrue(result.can_continue)

    def test_check_limits_approaching_tokens(self):
        """Test limit checking with approaching token limit."""
        # Use 85% of token limit
        self.monitor.record_operation(tokens=8500, api_call=10)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("tokens", result.approaching_limits)
        self.assertTrue(result.can_continue)

    def test_check_limits_approaching_api_calls(self):
        """Test limit checking with approaching API call limit."""
        # Make 85 API calls
        for _ in range(85):
            self.monitor.record_operation(tokens=100, api_call=True)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("api_calls", result.approaching_limits)
        self.assertTrue(result.can_continue)

    def test_check_limits_exceeded_duration(self):
        """Test limit checking with exceeded duration limit."""
        # Set time to 100% of limit
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=600)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("duration", result.exceeded_limits)
        self.assertFalse(result.can_continue)

    def test_check_limits_exceeded_tokens(self):
        """Test limit checking with exceeded token limit."""
        # Use 100% of token limit
        self.monitor.record_operation(tokens=10000, api_call=10)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("tokens", result.exceeded_limits)
        self.assertFalse(result.can_continue)

    def test_check_limits_exceeded_api_calls(self):
        """Test limit checking with exceeded API call limit."""
        # Make 100 API calls
        for _ in range(100):
            self.monitor.record_operation(tokens=100, api_call=True)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("api_calls", result.exceeded_limits)
        self.assertFalse(result.can_continue)

    def test_check_limits_multiple_approaching(self):
        """Test limit checking with multiple approaching limits."""
        # Use 85% of tokens and make 85 API calls
        for _ in range(85):
            self.monitor.record_operation(tokens=100, api_call=True)

        result = self.monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("tokens", result.approaching_limits)
        self.assertIn("api_calls", result.approaching_limits)
        self.assertEqual(len(result.approaching_limits), 2)


class TestResourceMonitorOperationRecording(unittest.TestCase):
    """Test ResourceMonitor operation recording."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id)

    def test_record_operation_increments_tokens(self):
        """Test that recording operation increments token count."""
        self.monitor.record_operation(tokens=100, api_call=False)
        self.assertEqual(self.monitor.usage.tokens_used, 100)
        self.assertEqual(self.monitor.usage.api_calls_made, 0)

    def test_record_operation_increments_api_calls(self):
        """Test that recording operation increments API call count."""
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(self.monitor.usage.tokens_used, 100)
        self.assertEqual(self.monitor.usage.api_calls_made, 1)

    def test_record_operation_multiple_calls(self):
        """Test recording multiple operations."""
        operations = [
            (100, True),
            (200, True),
            (150, False),
            (300, True),
        ]
        for tokens, api_call in operations:
            self.monitor.record_operation(tokens=tokens, api_call=api_call)

        self.assertEqual(self.monitor.usage.tokens_used, 750)
        self.assertEqual(self.monitor.usage.api_calls_made, 3)  # Only 3 operations had api_call=True

    def test_record_operation_updates_last_operation_time(self):
        """Test that recording operation updates last operation time."""
        initial_time = self.monitor.usage.last_operation_time
        time.sleep(0.01)  # Small delay
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertGreater(self.monitor.usage.last_operation_time, initial_time)


class TestResourceMonitorShouldContinue(unittest.TestCase):
    """Test ResourceMonitor should_continue logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id)

    def test_should_continue_with_ok_status(self):
        """Test should_continue returns True when status is OK."""
        self.assertTrue(self.monitor.should_continue(0.5))
        self.assertTrue(self.monitor.should_continue(0.1))

    def test_should_continue_with_exceeded_status(self):
        """Test should_continue returns False when limits exceeded."""
        # Exceed token limit
        self.monitor.record_operation(tokens=10000, api_call=10)
        result = self.monitor.should_continue(0.9)
        self.assertFalse(result)

    def test_should_continue_with_high_progress(self):
        """Test should_continue returns True when approaching limits but progress is high."""
        # Approach token limit (85%)
        self.monitor.record_operation(tokens=8500, api_call=10)

        # With high progress (90%), should continue
        self.assertTrue(self.monitor.should_continue(0.9))

    def test_should_continue_with_low_progress(self):
        """Test should_continue returns False when approaching limits and progress is low."""
        # Approach token limit (85%)
        self.monitor.record_operation(tokens=8500, api_call=10)

        # With low progress (50%), should not continue
        self.assertFalse(self.monitor.should_continue(0.5))

    def test_should_continue_at_completion_threshold(self):
        """Test should_continue at exactly the completion threshold."""
        # Approach token limit (85%)
        self.monitor.record_operation(tokens=8500, api_call=10)

        # At exactly 80% completion, should continue
        self.assertTrue(self.monitor.should_continue(0.8))

    def test_should_continue_just_below_threshold(self):
        """Test should_continue just below completion threshold."""
        # Approach token limit (85%)
        self.monitor.record_operation(tokens=8500, api_call=10)

        # At 79% completion, should not continue
        self.assertFalse(self.monitor.should_continue(0.79))


class TestResourceMonitorUsageReport(unittest.TestCase):
    """Test ResourceMonitor usage reporting."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id)

    def test_get_usage_report(self):
        """Test getting usage report."""
        # Record 5 separate API calls
        for _ in range(5):
            self.monitor.record_operation(tokens=200, api_call=True)
        usage = self.monitor.get_usage_report()
        self.assertEqual(usage.tokens_used, 1000)
        self.assertEqual(usage.api_calls_made, 5)
        self.assertGreater(usage.duration_seconds, 0)

    def test_get_usage_summary(self):
        """Test getting usage summary."""
        # Record 50 separate API calls
        for _ in range(50):
            self.monitor.record_operation(tokens=100, api_call=True)
        summary = self.monitor.get_usage_summary()

        self.assertIn("duration", summary)
        self.assertIn("tokens", summary)
        self.assertIn("api_calls", summary)
        self.assertIn("checkpoints", summary)
        self.assertIn("session_id", summary)

        # Check structure of each resource
        self.assertIn("used", summary["tokens"])
        self.assertIn("limit", summary["tokens"])
        self.assertIn("percentage", summary["tokens"])
        self.assertIn("remaining", summary["tokens"])

        # Check values
        self.assertEqual(summary["tokens"]["used"], 5000)
        self.assertEqual(summary["tokens"]["limit"], 10000)
        self.assertEqual(summary["tokens"]["percentage"], 50.0)
        self.assertEqual(summary["api_calls"]["used"], 50)

    def test_get_usage_summary_percentages(self):
        """Test usage summary calculates correct percentages."""
        # Use exactly 50% of each resource
        for _ in range(50):
            self.monitor.record_operation(tokens=100, api_call=True)
        summary = self.monitor.get_usage_summary()

        self.assertEqual(summary["tokens"]["percentage"], 50.0)
        self.assertEqual(summary["api_calls"]["percentage"], 50.0)


class TestResourceMonitorRemainingResources(unittest.TestCase):
    """Test ResourceMonitor remaining resource calculations."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id)

    def test_get_time_remaining(self):
        """Test getting time remaining."""
        # Simulate 100 seconds elapsed
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=100)
        remaining = self.monitor.get_time_remaining()
        # Allow small floating point tolerance
        self.assertAlmostEqual(remaining, 500, delta=0.1)  # 600 - 100

    def test_get_time_remaining_zero_when_exceeded(self):
        """Test time remaining is zero when limit exceeded."""
        # Simulate 700 seconds elapsed
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=700)
        remaining = self.monitor.get_time_remaining()
        self.assertEqual(remaining, 0)

    def test_get_tokens_remaining(self):
        """Test getting tokens remaining."""
        self.monitor.record_operation(tokens=3000, api_call=10)
        remaining = self.monitor.get_tokens_remaining()
        self.assertEqual(remaining, 7000)  # 10000 - 3000

    def test_get_tokens_remaining_zero_when_exceeded(self):
        """Test tokens remaining is zero when limit exceeded."""
        self.monitor.record_operation(tokens=10000, api_call=10)
        remaining = self.monitor.get_tokens_remaining()
        self.assertEqual(remaining, 0)

    def test_get_api_calls_remaining(self):
        """Test getting API calls remaining."""
        # Make 30 separate API calls
        for _ in range(30):
            self.monitor.record_operation(tokens=100, api_call=True)
        remaining = self.monitor.get_api_calls_remaining()
        self.assertEqual(remaining, 70)  # 100 - 30

    def test_get_api_calls_remaining_zero_when_exceeded(self):
        """Test API calls remaining is zero when limit exceeded."""
        for _ in range(100):
            self.monitor.record_operation(tokens=100, api_call=True)
        remaining = self.monitor.get_api_calls_remaining()
        self.assertEqual(remaining, 0)


class TestResourceMonitorCheckpointing(unittest.TestCase):
    """Test ResourceMonitor checkpointing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=1,  # 1 second for testing
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_checkpoint_created_on_first_operation(self):
        """Test that first checkpoint is created on first operation."""
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(self.monitor.usage.checkpoints_created, 1)
        self.assertIsNotNone(self.monitor.usage.last_checkpoint_time)

    def test_checkpoint_created_after_interval(self):
        """Test that checkpoint is created after interval elapses."""
        # First checkpoint
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(self.monitor.usage.checkpoints_created, 1)

        # Wait for interval to pass
        time.sleep(1.1)

        # Second checkpoint
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(self.monitor.usage.checkpoints_created, 2)

    def test_checkpoint_not_created_before_interval(self):
        """Test that checkpoint is not created before interval elapses."""
        # First checkpoint
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(self.monitor.usage.checkpoints_created, 1)

        # Immediate operation (before interval)
        self.monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(self.monitor.usage.checkpoints_created, 1)

    def test_checkpoint_saved_to_file(self):
        """Test that checkpoint is saved to file."""
        self.monitor.record_operation(tokens=100, api_call=True)

        checkpoint_file = (
            self.project_root / ".flow" / "maestro" / "checkpoints" / f"resource_checkpoint_{self.session_id}_1.json"
        )
        self.assertTrue(checkpoint_file.exists())

        # Verify file contents
        with open(checkpoint_file) as f:
            data = json.load(f)
            self.assertEqual(data["session_id"], self.session_id)
            self.assertEqual(data["checkpoint_number"], 1)
            self.assertIn("usage", data)
            self.assertIn("limits", data)

    def test_checkpoint_without_project_root(self):
        """Test checkpointing without project root (no file save)."""
        monitor = ResourceMonitor(self.limits, self.session_id, project_root=None)
        monitor.record_operation(tokens=100, api_call=True)

        # Should still create checkpoint in memory
        self.assertEqual(monitor.usage.checkpoints_created, 1)
        self.assertIsNotNone(monitor.usage.last_checkpoint_time)


class TestResourceMonitorCompletionEstimation(unittest.TestCase):
    """Test ResourceMonitor completion estimation."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-123"
        self.monitor = ResourceMonitor(self.limits, self.session_id)

    def test_estimated_completion_possible_with_sufficient_resources(self):
        """Test completion possible with sufficient remaining resources."""
        self.monitor.record_operation(tokens=3000, api_call=30)
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=100)

        # Need 2000 more tokens and 200 more seconds
        possible = self.monitor.get_estimated_completion_possible(
            estimated_tokens_remaining=2000,
            estimated_time_remaining=200,
        )
        self.assertTrue(possible)

    def test_estimated_completion_possible_with_insufficient_tokens(self):
        """Test completion not possible with insufficient tokens."""
        self.monitor.record_operation(tokens=9000, api_call=30)

        # Need 2000 more tokens but only have 1000 remaining
        possible = self.monitor.get_estimated_completion_possible(
            estimated_tokens_remaining=2000,
            estimated_time_remaining=100,
        )
        self.assertFalse(possible)

    def test_estimated_completion_possible_with_insufficient_time(self):
        """Test completion not possible with insufficient time."""
        self.monitor.usage.start_time = datetime.now() - timedelta(seconds=500)

        # Need 200 more seconds but only have 100 remaining
        possible = self.monitor.get_estimated_completion_possible(
            estimated_tokens_remaining=1000,
            estimated_time_remaining=200,
        )
        self.assertFalse(possible)


class TestResourceMonitorIntegration(unittest.TestCase):
    """Integration tests for ResourceMonitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        self.limits = ResourceLimits(
            max_duration_seconds=600,
            max_tokens=10000,
            max_api_calls=100,
            checkpoint_interval=60,
        )
        self.session_id = "test-session-integration"
        self.monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_workflow_simulation(self):
        """Test a complete workflow simulation with resource monitoring."""
        # Simulate a workflow with multiple operations
        operations = [
            (1000, 10),  # Phase 1: 1000 tokens, 10 API calls
            (2000, 20),  # Phase 2: 2000 tokens, 20 API calls
            (1500, 15),  # Phase 3: 1500 tokens, 15 API calls
        ]

        progress_estimates = [0.3, 0.6, 0.9]

        for i, (tokens, api_calls) in enumerate(operations):
            # Check if we should continue
            should_continue = self.monitor.should_continue(progress_estimates[i])
            self.assertTrue(should_continue, f"Should continue at phase {i+1}")

            # Record operations for this phase
            # Each operation is one API call
            tokens_per_call = tokens // api_calls
            for _ in range(api_calls):
                self.monitor.record_operation(tokens=tokens_per_call, api_call=True)

        # Final check
        final_check = self.monitor.check_limits()
        self.assertEqual(final_check.status, LimitStatus.OK)

        # Get summary
        summary = self.monitor.get_usage_summary()
        self.assertLess(summary["tokens"]["percentage"], 80)
        self.assertLess(summary["api_calls"]["percentage"], 80)

    def test_workflow_stopping_on_low_progress(self):
        """Test workflow stopping when approaching limits with low progress."""
        # Use 85% of tokens with 85 separate API calls
        for _ in range(85):
            self.monitor.record_operation(tokens=100, api_call=True)

        # With only 50% progress, should not continue
        should_continue = self.monitor.should_continue(0.5)
        self.assertFalse(should_continue)

        # Verify we can still get a partial results report
        summary = self.monitor.get_usage_summary()
        self.assertEqual(summary["tokens"]["used"], 8500)
        self.assertGreater(summary["tokens"]["remaining"], 0)

    def test_workflow_continuing_with_high_progress(self):
        """Test workflow continuing when approaching limits with high progress."""
        # Use 85% of tokens with 85 separate API calls
        for _ in range(85):
            self.monitor.record_operation(tokens=100, api_call=True)

        # With 90% progress, should continue
        should_continue = self.monitor.should_continue(0.9)
        self.assertTrue(should_continue)


if __name__ == "__main__":
    unittest.main()
