#!/usr/bin/env python3
"""
Performance and Stress Tests for Resource Limit Enforcement

Comprehensive tests covering:
- Performance test scenarios for resource limit enforcement
- Stress tests for boundary conditions
- Graceful degradation and early termination logic
- Checkpoint creation under various conditions
"""

import json
import tempfile
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from resource_monitor import (
    ResourceMonitor,
    ResourceLimits,
    ResourceUsage,
    LimitStatus,
    LimitCheckResult,
)


class TestTimeLimitPerformance(unittest.TestCase):
    """Performance tests for time limit enforcement."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=100,  # Short for testing
            max_tokens=1000000,
            max_api_calls=10000,
            checkpoint_interval=10,
        )
        self.session_id = "test-time-limit"

    def test_approaching_time_limit(self):
        """Test behavior when session approaches max_duration_seconds."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Simulate 79% of time limit (should be OK)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=79)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)

        # Simulate 81% of time limit (should be APPROACHING)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=81)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("duration", result.approaching_limits)
        self.assertTrue(result.can_continue)

        # Simulate 100% of time limit (should be EXCEEDED)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=100)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("duration", result.exceeded_limits)
        self.assertFalse(result.can_continue)

    def test_time_limit_with_high_progress_continues(self):
        """Test that approaching time limit with high progress continues."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Simulate 85% of time limit (APPROACHING)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=85)

        # With 90% progress, should continue
        should_continue = monitor.should_continue(0.9)
        self.assertTrue(should_continue)

    def test_time_limit_with_low_progress_stops(self):
        """Test that approaching time limit with low progress stops."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Simulate 85% of time limit (APPROACHING)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=85)

        # With 50% progress, should not continue
        should_continue = monitor.should_continue(0.5)
        self.assertFalse(should_continue)

    def test_time_remaining_calculation(self):
        """Test accurate time remaining calculation."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Simulate 30 seconds elapsed
        monitor.usage.start_time = datetime.now() - timedelta(seconds=30)
        remaining = monitor.get_time_remaining()
        self.assertAlmostEqual(remaining, 70, delta=1)

        # Simulate 90 seconds elapsed
        monitor.usage.start_time = datetime.now() - timedelta(seconds=90)
        remaining = monitor.get_time_remaining()
        self.assertAlmostEqual(remaining, 10, delta=1)

        # Simulate exactly at limit
        monitor.usage.start_time = datetime.now() - timedelta(seconds=100)
        remaining = monitor.get_time_remaining()
        self.assertEqual(remaining, 0)

        # Simulate over limit
        monitor.usage.start_time = datetime.now() - timedelta(seconds=110)
        remaining = monitor.get_time_remaining()
        self.assertEqual(remaining, 0)


class TestTokenLimitPerformance(unittest.TestCase):
    """Performance tests for token limit enforcement."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=3600,
            max_tokens=100000,  # 100K for testing
            max_api_calls=10000,
            checkpoint_interval=300,
        )
        self.session_id = "test-token-limit"

    def test_approaching_token_limit(self):
        """Test behavior when session approaches max_tokens."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use 79K tokens (should be OK)
        monitor.record_operation(tokens=79000, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)

        # Use 81K tokens total (should be APPROACHING)
        monitor.record_operation(tokens=2000, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("tokens", result.approaching_limits)
        self.assertTrue(result.can_continue)

    def test_token_limit_exceeded(self):
        """Test token limit exceeded behavior."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use exactly 100K tokens (should be EXCEEDED)
        monitor.record_operation(tokens=100000, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("tokens", result.exceeded_limits)
        self.assertFalse(result.can_continue)

    def test_token_limit_with_high_progress_continues(self):
        """Test that approaching token limit with high progress continues."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use 85K tokens (APPROACHING)
        monitor.record_operation(tokens=85000, api_call=False)

        # With 90% progress, should continue
        should_continue = monitor.should_continue(0.9)
        self.assertTrue(should_continue)

    def test_token_limit_with_low_progress_stops(self):
        """Test that approaching token limit with low progress stops."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use 85K tokens (APPROACHING)
        monitor.record_operation(tokens=85000, api_call=False)

        # With 50% progress, should not continue
        should_continue = monitor.should_continue(0.5)
        self.assertFalse(should_continue)

    def test_tokens_remaining_calculation(self):
        """Test accurate tokens remaining calculation."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use 30K tokens
        monitor.record_operation(tokens=30000, api_call=False)
        remaining = monitor.get_tokens_remaining()
        self.assertEqual(remaining, 70000)

        # Use another 20K tokens
        monitor.record_operation(tokens=20000, api_call=False)
        remaining = monitor.get_tokens_remaining()
        self.assertEqual(remaining, 50000)

        # Use all tokens
        monitor.record_operation(tokens=50000, api_call=False)
        remaining = monitor.get_tokens_remaining()
        self.assertEqual(remaining, 0)


class TestAPICallLimitPerformance(unittest.TestCase):
    """Performance tests for API call limit enforcement."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=3600,
            max_tokens=1000000,
            max_api_calls=1000,  # 1000 for testing
            checkpoint_interval=300,
        )
        self.session_id = "test-api-call-limit"

    def test_approaching_api_call_limit(self):
        """Test behavior when session approaches max_api_calls."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Make 790 API calls (should be OK)
        for _ in range(790):
            monitor.record_operation(tokens=100, api_call=True)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)

        # Make 810 API calls total (should be APPROACHING)
        for _ in range(20):
            monitor.record_operation(tokens=100, api_call=True)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("api_calls", result.approaching_limits)
        self.assertTrue(result.can_continue)

    def test_api_call_limit_exceeded(self):
        """Test API call limit exceeded behavior."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Make exactly 1000 API calls (should be EXCEEDED)
        for _ in range(1000):
            monitor.record_operation(tokens=100, api_call=True)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("api_calls", result.exceeded_limits)
        self.assertFalse(result.can_continue)

    def test_api_call_limit_with_high_progress_continues(self):
        """Test that approaching API call limit with high progress continues."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Make 850 API calls (APPROACHING)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # With 90% progress, should continue
        should_continue = monitor.should_continue(0.9)
        self.assertTrue(should_continue)

    def test_api_call_limit_with_low_progress_stops(self):
        """Test that approaching API call limit with low progress stops."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Make 850 API calls (APPROACHING)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # With 50% progress, should not continue
        should_continue = monitor.should_continue(0.5)
        self.assertFalse(should_continue)

    def test_api_calls_remaining_calculation(self):
        """Test accurate API calls remaining calculation."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Make 300 API calls
        for _ in range(300):
            monitor.record_operation(tokens=100, api_call=True)
        remaining = monitor.get_api_calls_remaining()
        self.assertEqual(remaining, 700)

        # Make 200 more API calls
        for _ in range(200):
            monitor.record_operation(tokens=100, api_call=True)
        remaining = monitor.get_api_calls_remaining()
        self.assertEqual(remaining, 500)


class TestCombinedLimits(unittest.TestCase):
    """Performance tests for combined limit scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
        )
        self.session_id = "test-combined-limits"

    def test_multiple_limits_approached_simultaneously(self):
        """Test when multiple limits are approached simultaneously."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach all three limits (85% each)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=850)  # 85% of time
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)  # 85% of tokens and API calls

        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)
        self.assertIn("duration", result.approaching_limits)
        self.assertIn("tokens", result.approaching_limits)
        self.assertIn("api_calls", result.approaching_limits)
        self.assertEqual(len(result.approaching_limits), 3)

    def test_combined_limits_with_high_progress(self):
        """Test combined limits with high progress continues."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach all limits (85% each)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=850)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # With 90% progress, should continue
        should_continue = monitor.should_continue(0.9)
        self.assertTrue(should_continue)

    def test_combined_limits_with_low_progress(self):
        """Test combined limits with low progress stops."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach all limits (85% each)
        monitor.usage.start_time = datetime.now() - timedelta(seconds=850)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # With 50% progress, should not continue
        should_continue = monitor.should_continue(0.5)
        self.assertFalse(should_continue)

    def test_one_limit_exceeds_while_others_ok(self):
        """Test when one limit exceeds while others are OK."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Exceed time limit but keep tokens and API calls low
        monitor.usage.start_time = datetime.now() - timedelta(seconds=1001)
        monitor.record_operation(tokens=1000, api_call=10)

        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("duration", result.exceeded_limits)
        self.assertNotIn("tokens", result.exceeded_limits)
        self.assertNotIn("api_calls", result.exceeded_limits)

    def test_partial_exceedance(self):
        """Test when some limits exceeded, others approached."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Exceed tokens and API calls, approach time
        monitor.usage.start_time = datetime.now() - timedelta(seconds=850)
        for _ in range(1001):
            monitor.record_operation(tokens=100, api_call=True)

        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)
        self.assertIn("duration", result.approaching_limits)  # Approaching
        self.assertIn("tokens", result.exceeded_limits)  # Exceeded
        self.assertIn("api_calls", result.exceeded_limits)  # Exceeded


class TestGracefulDegradation(unittest.TestCase):
    """Tests for graceful degradation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
            completion_threshold=0.80,  # 80% threshold
        )
        self.session_id = "test-graceful-degradation"

    def test_continue_with_partial_results_when_appropriate(self):
        """Test continue with partial results when >80% progress."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach token limit (85%)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # At 85% progress, should continue to complete
        should_continue = monitor.should_continue(0.85)
        self.assertTrue(should_continue)

        # At 90% progress, should continue
        should_continue = monitor.should_continue(0.90)
        self.assertTrue(should_continue)

        # At exactly 80% progress, should continue
        should_continue = monitor.should_continue(0.80)
        self.assertTrue(should_continue)

    def test_early_termination_when_not_near_completion(self):
        """Test early termination when <80% progress."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach token limit (85%)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # At 79% progress, should not continue
        should_continue = monitor.should_continue(0.79)
        self.assertFalse(should_continue)

        # At 50% progress, should not continue
        should_continue = monitor.should_continue(0.50)
        self.assertFalse(should_continue)

        # At 10% progress, should not continue
        should_continue = monitor.should_continue(0.10)
        self.assertFalse(should_continue)

    def test_custom_completion_threshold(self):
        """Test with custom completion threshold."""
        custom_limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
            completion_threshold=0.90,  # 90% threshold
        )
        monitor = ResourceMonitor(custom_limits, self.session_id)

        # Approach token limit (85%)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        # At 85% progress, should not continue (below 90% threshold)
        should_continue = monitor.should_continue(0.85)
        self.assertFalse(should_continue)

        # At 90% progress, should continue
        should_continue = monitor.should_continue(0.90)
        self.assertTrue(should_continue)

    def test_exceeded_limits_always_stop(self):
        """Test that exceeded limits always stop regardless of progress."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Exceed token limit
        for _ in range(1001):
            monitor.record_operation(tokens=100, api_call=True)

        # Even with 99% progress, should not continue
        should_continue = monitor.should_continue(0.99)
        self.assertFalse(should_continue)

        # Even with 100% progress, should not continue
        should_continue = monitor.should_continue(1.0)
        self.assertFalse(should_continue)


class TestCheckpointStress(unittest.TestCase):
    """Stress tests for checkpoint creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=1,  # 1 second for rapid testing
        )
        self.session_id = "test-checkpoint-stress"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_many_checkpoints_in_short_time(self):
        """Test creating many checkpoints in short time."""
        monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

        # Create 5 checkpoints by waiting between operations
        for i in range(5):
            monitor.record_operation(tokens=100, api_call=True)
            if i < 4:  # Don't sleep after last operation
                time.sleep(1.1)

        self.assertEqual(monitor.usage.checkpoints_created, 5)

        # Verify all checkpoint files exist
        for i in range(1, 6):
            checkpoint_file = (
                self.project_root / ".flow" / "maestro" / "checkpoints" /
                f"resource_checkpoint_{self.session_id}_{i}.json"
            )
            self.assertTrue(checkpoint_file.exists(), f"Checkpoint {i} should exist")

    def test_checkpoint_interval_enforcement(self):
        """Test that checkpoints are only created at intervals."""
        monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

        # First operation should create checkpoint
        monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(monitor.usage.checkpoints_created, 1)

        # Immediate operations should not create checkpoints
        for _ in range(5):
            monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(monitor.usage.checkpoints_created, 1)

        # After interval, next operation should create checkpoint
        time.sleep(1.1)
        monitor.record_operation(tokens=100, api_call=True)
        self.assertEqual(monitor.usage.checkpoints_created, 2)

    def test_checkpoint_data_integrity(self):
        """Test that checkpoint data remains consistent."""
        monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

        # First checkpoint created on first operation
        monitor.record_operation(tokens=1000, api_call=True)

        # Wait for interval to pass, then trigger second checkpoint
        time.sleep(1.1)
        monitor.record_operation(tokens=2000, api_call=True)  # This triggers checkpoint #2

        # Verify we have exactly 2 checkpoints
        self.assertEqual(monitor.usage.checkpoints_created, 2)

        checkpoint_file = (
            self.project_root / ".flow" / "maestro" / "checkpoints" /
            f"resource_checkpoint_{self.session_id}_2.json"
        )

        with open(checkpoint_file) as f:
            data = json.load(f)

        # Verify checkpoint data
        self.assertEqual(data["session_id"], self.session_id)
        self.assertEqual(data["checkpoint_number"], 2)
        # Checkpoint #2 captures state after second operation: 3000 tokens, 2 API calls
        self.assertEqual(data["usage"]["tokens_used"], 3000)
        self.assertEqual(data["usage"]["api_calls_made"], 2)
        self.assertIn("limits", data)


class TestSuddenSpikeStress(unittest.TestCase):
    """Stress tests for sudden resource consumption spikes."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
        )
        self.session_id = "test-sudden-spike"

    def test_sudden_token_spike(self):
        """Test sudden spike in token consumption."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Start with low usage
        monitor.record_operation(tokens=1000, api_call=10)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)

        # Sudden spike to 85%
        monitor.record_operation(tokens=84000, api_call=10)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)

    def test_sudden_api_call_spike(self):
        """Test sudden spike in API call consumption."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Start with low usage
        monitor.record_operation(tokens=100, api_call=10)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)

        # Sudden spike to 850 API calls
        for _ in range(840):
            monitor.record_operation(tokens=100, api_call=True)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)

    def test_rapid_oscillation_between_states(self):
        """Test rapid oscillation between OK, APPROACHING, and EXCEEDED."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Start at OK
        monitor.record_operation(tokens=10000, api_call=100)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)

        # Spike to APPROACHING
        for _ in range(750):
            monitor.record_operation(tokens=100, api_call=True)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)

        # Return to OK (by creating new monitor with fresh limits)
        # This simulates resource cleanup
        fresh_monitor = ResourceMonitor(self.limits, self.session_id + "-fresh")
        fresh_monitor.record_operation(tokens=20000, api_call=200)
        result = fresh_monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)


class TestOscillatingUsageStress(unittest.TestCase):
    """Stress tests for oscillating resource usage patterns."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
        )
        self.session_id = "test-oscillating-usage"

    def test_oscillating_token_usage(self):
        """Test tokens approaching and receding from limit."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach limit (85%)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)

        # Create new monitor simulating resource cleanup/reduction
        # (In real scenario, this would be token budget reallocation)
        fresh_monitor = ResourceMonitor(self.limits, self.session_id + "-fresh")

        # Now at lower usage (20%)
        for _ in range(200):
            fresh_monitor.record_operation(tokens=100, api_call=True)
        result = fresh_monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)

    def test_repeated_approach_and_retreat(self):
        """Test repeatedly approaching and retreating from limits."""
        session_count = 0

        for cycle in range(3):
            session_count += 1
            monitor = ResourceMonitor(self.limits, f"{self.session_id}-cycle{cycle}")

            # Approach limit
            for _ in range(850):
                monitor.record_operation(tokens=100, api_call=True)
            result = monitor.check_limits()
            self.assertEqual(result.status, LimitStatus.APPROACHING)

            # Verify can continue with high progress
            should_continue = monitor.should_continue(0.90)
            self.assertTrue(should_continue)

            # Verify stops with low progress
            should_continue = monitor.should_continue(0.50)
            self.assertFalse(should_continue)


class TestConcurrentOperations(unittest.TestCase):
    """Stress tests for concurrent resource usage."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
        )
        self.session_id = "test-concurrent-ops"

        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_operation_recording(self):
        """Test recording operations from multiple threads."""
        monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)
        lock = threading.Lock()

        def record_operations(thread_id: int, count: int):
            """Record operations from a thread."""
            for _ in range(count):
                with lock:
                    monitor.record_operation(tokens=100, api_call=True)

        # Record from multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_operations, args=(i, 100))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify total operations
        self.assertEqual(monitor.usage.api_calls_made, 500)
        self.assertEqual(monitor.usage.tokens_used, 50000)

    def test_concurrent_limit_checking(self):
        """Test concurrent limit checking operations."""
        monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

        # Pre-populate with operations to reach APPROACHING status (85%)
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        results = []
        lock = threading.Lock()

        def check_limits_concurrently():
            """Check limits from multiple threads."""
            result = monitor.check_limits()
            with lock:
                results.append(result)

        # Check from multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=check_limits_concurrently)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All results should be consistent
        for result in results:
            self.assertEqual(result.status, LimitStatus.APPROACHING)

    def test_concurrent_should_continue(self):
        """Test concurrent should_continue calls."""
        monitor = ResourceMonitor(self.limits, self.session_id, self.project_root)

        # Approach token limit
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        results = []
        lock = threading.Lock()

        def check_continuation(progress: float):
            """Check should_continue from multiple threads."""
            result = monitor.should_continue(progress)
            with lock:
                results.append((progress, result))

        # Check with different progress values
        threads = []
        test_progress = [0.5, 0.7, 0.9, 0.85, 0.6]
        for progress in test_progress:
            thread = threading.Thread(target=check_continuation, args=(progress,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify results match expected behavior
        for progress, result in results:
            if progress >= 0.80:
                self.assertTrue(result, f"Should continue at {progress*100}%")
            else:
                self.assertFalse(result, f"Should not continue at {progress*100}%")


class TestBoundaryConditions(unittest.TestCase):
    """Tests for boundary conditions and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=1000,
            max_tokens=100000,
            max_api_calls=1000,
            checkpoint_interval=100,
        )
        self.session_id = "test-boundary-conditions"

    def test_exactly_at_warning_threshold(self):
        """Test behavior exactly at warning threshold (80%)."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use exactly 80% of tokens
        monitor.record_operation(tokens=80000, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.APPROACHING)

    def test_just_below_warning_threshold(self):
        """Test behavior just below warning threshold (79.9%)."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use 79.9% of tokens
        monitor.record_operation(tokens=79900, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)

    def test_exactly_at_limit(self):
        """Test behavior exactly at limit (100%)."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use exactly 100% of tokens
        monitor.record_operation(tokens=100000, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)

    def test_just_over_limit(self):
        """Test behavior just over limit (100.1%)."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Use 100.1% of tokens
        monitor.record_operation(tokens=100100, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)

    def test_at_completion_threshold(self):
        """Test should_continue exactly at completion threshold."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach token limit (85%)
        monitor.record_operation(tokens=85000, api_call=False)

        # At exactly 80% completion threshold, should continue
        should_continue = monitor.should_continue(0.80)
        self.assertTrue(should_continue)

    def test_just_below_completion_threshold(self):
        """Test should_continue just below completion threshold."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Approach token limit (85%)
        monitor.record_operation(tokens=85000, api_call=False)

        # At 79.99% completion, should not continue
        should_continue = monitor.should_continue(0.7999)
        self.assertFalse(should_continue)

    def test_zero_usage(self):
        """Test behavior with zero usage."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.OK)
        self.assertTrue(result.can_continue)

        summary = monitor.get_usage_summary()
        self.assertEqual(summary["tokens"]["used"], 0)
        self.assertEqual(summary["api_calls"]["used"], 0)

    def test_single_operation_at_limit(self):
        """Test single operation that reaches limit."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Single operation at exactly 100% of token limit
        monitor.record_operation(tokens=100000, api_call=False)
        result = monitor.check_limits()
        self.assertEqual(result.status, LimitStatus.EXCEEDED)

        # Should not continue even with high progress
        should_continue = monitor.should_continue(0.99)
        self.assertFalse(should_continue)


class TestPerformanceUnderLoad(unittest.TestCase):
    """Performance tests under simulated load."""

    def setUp(self):
        """Set up test fixtures."""
        self.limits = ResourceLimits(
            max_duration_seconds=3600,
            max_tokens=1000000,
            max_api_calls=10000,
            checkpoint_interval=300,
        )
        self.session_id = "test-performance-load"

    def test_large_number_of_operations(self):
        """Test handling large number of operations efficiently."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        start_time = time.time()

        # Record 10,000 operations
        for _ in range(10000):
            monitor.record_operation(tokens=100, api_call=True)

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        self.assertLess(elapsed, 5.0)

        # Verify counts
        self.assertEqual(monitor.usage.api_calls_made, 10000)
        self.assertEqual(monitor.usage.tokens_used, 1000000)

    def test_frequent_limit_checks(self):
        """Test performance of frequent limit checks."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Record some operations
        for _ in range(1000):
            monitor.record_operation(tokens=100, api_call=True)

        start_time = time.time()

        # Perform 10,000 limit checks
        for _ in range(10000):
            monitor.check_limits()

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 2 seconds)
        self.assertLess(elapsed, 2.0)

    def test_frequent_should_continue_checks(self):
        """Test performance of frequent should_continue checks."""
        monitor = ResourceMonitor(self.limits, self.session_id)

        # Record some operations to approach limits
        for _ in range(850):
            monitor.record_operation(tokens=100, api_call=True)

        start_time = time.time()

        # Perform 10,000 should_continue checks
        for _ in range(10000):
            monitor.should_continue(0.75)

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 3 seconds)
        self.assertLess(elapsed, 3.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
