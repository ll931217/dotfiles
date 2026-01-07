#!/usr/bin/env python3
"""
Performance Benchmarks for Maestro Orchestrator

Measures performance characteristics of core operations including:
- Session creation and management
- Checkpoint creation and retrieval
- Decision logging
- Error handling
- Subagent coordination
"""

import json
import tempfile
import time
import unittest
from pathlib import Path
from datetime import datetime
from statistics import mean, median, stdev
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, asdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "decision-engine" / "scripts"))

from session_manager import SessionManager, SessionStatus
from checkpoint_manager import CheckpointManager, CheckpointType, CheckpointPhase, StateSnapshot
from decision_logger import DecisionLogger
from error_handler import ErrorHandler, ErrorCategory, ErrorType, Error
from subagent_factory import SubagentFactory
from skill_orchestrator import SkillOrchestrator
from parallel_coordinator import ParallelCoordinator


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    stdev_time: float
    ops_per_second: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkSuite:
    """Suite of benchmark results."""
    timestamp: str
    benchmarks: List[BenchmarkResult]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["benchmarks"] = [b.to_dict() for b in self.benchmarks]
        return data


class PerformanceBenchmark:
    """Performance benchmarking suite for Maestro components."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[BenchmarkResult] = []

    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10
    ) -> BenchmarkResult:
        """
        Run a benchmark function multiple times.

        Args:
            name: Benchmark name
            func: Function to benchmark (should return timing)
            iterations: Number of iterations
            warmup: Number of warmup iterations (not counted)

        Returns:
            BenchmarkResult with statistics
        """
        # Warmup
        for _ in range(warmup):
            func()

        # Actual benchmark
        times: List[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)

        total_time = sum(times)
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=mean(times),
            min_time=min(times),
            max_time=max(times),
            median_time=median(times),
            stdev_time=stdev(times) if len(times) > 1 else 0.0,
            ops_per_second=iterations / total_time
        )
        self.results.append(result)
        return result

    def print_result(self, result: BenchmarkResult):
        """Print benchmark result in readable format."""
        print(f"\n{result.name}:")
        print(f"  Iterations: {result.iterations}")
        print(f"  Total time: {result.total_time:.4f}s")
        print(f"  Avg: {result.avg_time*1000:.2f}ms")
        print(f"  Min: {result.min_time*1000:.2f}ms")
        print(f"  Max: {result.max_time*1000:.2f}ms")
        print(f"  Median: {result.median_time*1000:.2f}ms")
        print(f"  Stdev: {result.stdev_time*1000:.2f}ms")
        print(f"  Ops/sec: {result.ops_per_second:.2f}")

    def save_results(self, output_path: Path):
        """Save benchmark results to JSON file."""
        suite = BenchmarkSuite(
            timestamp=datetime.now().isoformat(),
            benchmarks=self.results,
            summary=self._generate_summary()
        )
        with open(output_path, "w") as f:
            json.dump(suite.to_dict(), f, indent=2)
        print(f"\nResults saved to: {output_path}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_benchmarks": len(self.results),
            "total_iterations": sum(r.iterations for r in self.results),
            "total_time": sum(r.total_time for r in self.results),
        }


class TestSessionManagerPerformance(unittest.TestCase):
    """Performance benchmarks for SessionManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)

        self.benchmark = PerformanceBenchmark(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_benchmark_session_creation(self):
        """Benchmark session creation performance."""
        manager = SessionManager(self.project_root)

        def create_session():
            return manager.create_session(
                feature_request="Benchmark test feature"
            )

        result = self.benchmark.run_benchmark(
            "Session Creation",
            create_session,
            iterations=50,
            warmup=5
        )
        self.benchmark.print_result(result)

        # Performance assertion: should create at least 10 sessions per second
        self.assertGreater(result.ops_per_second, 10.0)

    def test_benchmark_session_retrieval(self):
        """Benchmark session retrieval performance."""
        manager = SessionManager(self.project_root)

        # Create a test session
        session = manager.create_session(feature_request="Test")

        def get_session():
            return manager.get_session(session.session_id)

        result = self.benchmark.run_benchmark(
            "Session Retrieval",
            get_session,
            iterations=100,
            warmup=10
        )
        self.benchmark.print_result(result)

        # Should retrieve at least 100 sessions per second
        self.assertGreater(result.ops_per_second, 100.0)

    def test_benchmark_state_transition(self):
        """Benchmark state transition performance."""
        manager = SessionManager(self.project_root)
        session = manager.create_session(feature_request="Test")

        # First transition to PLANNING (valid from INITIALIZING)
        manager.transition_state(
            session_id=session.session_id,
            new_state=SessionStatus.PLANNING
        )

        def transition_state():
            # Transition to GENERATING_TASKS and back to PLANNING
            # Note: GENERATING_TASKS can't go back to PLANNING, so we use PAUSED
            manager.transition_state(
                session_id=session.session_id,
                new_state=SessionStatus.PAUSED
            )
            # PAUSED can transition to PLANNING
            manager.transition_state(
                session_id=session.session_id,
                new_state=SessionStatus.PLANNING
            )

        result = self.benchmark.run_benchmark(
            "State Transition",
            transition_state,
            iterations=100,
            warmup=10
        )
        self.benchmark.print_result(result)

        # Should handle at least 50 transitions per second
        self.assertGreater(result.ops_per_second, 50.0)


class TestCheckpointManagerPerformance(unittest.TestCase):
    """Performance benchmarks for CheckpointManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "benchmark-session"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )

        # Initialize git repository (required for checkpoints)
        import subprocess
        subprocess.run(["git", "init"], cwd=self.project_root, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_root, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_root, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=self.project_root, capture_output=True)

        self.benchmark = PerformanceBenchmark(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_benchmark_checkpoint_creation(self):
        """Benchmark checkpoint creation performance."""
        manager = CheckpointManager(self.project_root)

        # Create a dummy file to have something to commit for the first checkpoint
        (self.project_root / "test.txt").write_text("test")

        def create_checkpoint():
            # Use commit_first=False to avoid empty commit errors
            return manager.create_checkpoint(
                session_id=self.session_id,
                phase=CheckpointPhase.IMPLEMENT,
                checkpoint_type=CheckpointType.PHASE_COMPLETE,
                description=f"Benchmark checkpoint {time.time()}",
                state_snapshot=StateSnapshot(tasks_completed=1),
                commit_first=False  # Skip commit, just tag current HEAD
            )

        result = self.benchmark.run_benchmark(
            "Checkpoint Creation",
            create_checkpoint,
            iterations=20,  # Reduced to avoid tag conflicts
            warmup=3
        )
        self.benchmark.print_result(result)

        # Should create at least 5 checkpoints per second (git tags are slower)
        self.assertGreater(result.ops_per_second, 5.0)

    def test_benchmark_checkpoint_retrieval(self):
        """Benchmark checkpoint retrieval performance."""
        manager = CheckpointManager(self.project_root)

        # Create a test checkpoint
        checkpoint = manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.PLAN,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="Test checkpoint",
            state_snapshot=StateSnapshot(tasks_completed=1)
        )

        def get_checkpoint():
            return manager.get_checkpoint(self.session_id, checkpoint.checkpoint_id)

        result = self.benchmark.run_benchmark(
            "Checkpoint Retrieval",
            get_checkpoint,
            iterations=100,
            warmup=10
        )
        self.benchmark.print_result(result)

        # Should retrieve at least 100 checkpoints per second
        self.assertGreater(result.ops_per_second, 100.0)


class TestDecisionLoggerPerformance(unittest.TestCase):
    """Performance benchmarks for DecisionLogger."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "benchmark-session"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)

        self.benchmark = PerformanceBenchmark(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_benchmark_decision_logging(self):
        """Benchmark decision logging performance."""
        logger = DecisionLogger(base_path=self.project_root)

        def log_decision():
            return logger.log_decision(
                decision_type="architectural",
                decision={
                    "decision": "Test decision for benchmarking",
                    "rationale": "Performance testing",
                    "context": {"benchmark": True}
                }
            )

        result = self.benchmark.run_benchmark(
            "Decision Logging",
            log_decision,
            iterations=100,
            warmup=10
        )
        self.benchmark.print_result(result)

        # Should log at least 50 decisions per second
        self.assertGreater(result.ops_per_second, 50.0)


class TestErrorHandlerPerformance(unittest.TestCase):
    """Performance benchmarks for ErrorHandler."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "benchmark-session"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )

        self.benchmark = PerformanceBenchmark(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_benchmark_error_detection(self):
        """Benchmark error detection performance."""
        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        test_output = "Error: Connection timeout after 30 seconds"

        def detect_error():
            return handler.detect_error(
                output=test_output,
                source="test",
                exit_code=1
            )

        result = self.benchmark.run_benchmark(
            "Error Detection",
            detect_error,
            iterations=1000,
            warmup=100
        )
        self.benchmark.print_result(result)

        # Should detect at least 1000 errors per second
        self.assertGreater(result.ops_per_second, 1000.0)

    def test_benchmark_recovery_strategy_selection(self):
        """Benchmark recovery strategy selection performance."""
        handler = ErrorHandler(session_id=self.session_id, base_path=self.project_root)

        test_error = Error(
            error_id="test-001",
            timestamp=datetime.now().isoformat(),
            error_type=ErrorType.TIMEOUT,
            category=ErrorCategory.TRANSIENT,
            message="Connection timeout",
            source="test"
        )

        def select_strategy():
            return handler.select_recovery_strategy(test_error)

        result = self.benchmark.run_benchmark(
            "Recovery Strategy Selection",
            select_strategy,
            iterations=1000,
            warmup=100
        )
        self.benchmark.print_result(result)

        # Should select at least 10000 strategies per second
        self.assertGreater(result.ops_per_second, 10000.0)


class TestSubagentFactoryPerformance(unittest.TestCase):
    """Performance benchmarks for SubagentFactory."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create subagent config
        subagent_config = """subagent_types:
  general-purpose:
    model: sonnet
    description: General purpose agent
    capabilities:
      - code_writing
      - debugging
      - analysis
"""
        config_path = self.project_root / ".claude" / "subagent-types.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(subagent_config)

        import os
        os.environ["SUBAGENT_TYPES_PATH"] = str(config_path)

        self.benchmark = PerformanceBenchmark(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_benchmark_subagent_detection(self):
        """Benchmark subagent type detection performance."""
        factory = SubagentFactory()

        def detect_subagent():
            return factory.detect_subagent_type("Create React component with TypeScript")

        result = self.benchmark.run_benchmark(
            "Subagent Type Detection",
            detect_subagent,
            iterations=100,
            warmup=10
        )
        self.benchmark.print_result(result)

        # Should detect at least 100 types per second
        self.assertGreater(result.ops_per_second, 100.0)


class TestStressScenarios(unittest.TestCase):
    """Stress tests for Maestro components."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)
        (self.project_root / ".flow" / "maestro" / "checkpoints").mkdir(parents=True, exist_ok=True)

        # Initialize git repository (required for checkpoints)
        import subprocess
        subprocess.run(["git", "init"], cwd=self.project_root, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_root, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_root, capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=self.project_root, capture_output=True)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_stress_multiple_sessions(self):
        """Stress test: Create and manage 100 sessions concurrently."""
        manager = SessionManager(self.project_root)

        start_time = time.perf_counter()

        # Create 100 sessions
        sessions = []
        for i in range(100):
            session = manager.create_session(
                feature_request=f"Stress test session {i}"
            )
            sessions.append(session)

        creation_time = time.perf_counter() - start_time

        # Verify all sessions
        for session in sessions:
            retrieved = manager.get_session(session.session_id)
            self.assertIsNotNone(retrieved)

        retrieval_time = time.perf_counter() - start_time - creation_time

        print(f"\nStress Test - Multiple Sessions:")
        print(f"  Created 100 sessions in {creation_time:.2f}s ({100/creation_time:.2f} sessions/sec)")
        print(f"  Retrieved 100 sessions in {retrieval_time:.2f}s ({100/retrieval_time:.2f} sessions/sec)")

        # Performance assertions
        self.assertLess(creation_time, 10.0, "Should create 100 sessions in under 10 seconds")
        self.assertLess(retrieval_time, 5.0, "Should retrieve 100 sessions in under 5 seconds")

    def test_stress_many_decisions(self):
        """Stress test: Log 100 decisions."""
        logger = DecisionLogger(base_path=self.project_root)

        start_time = time.perf_counter()

        # Log 100 decisions
        for i in range(100):
            logger.log_decision(
                decision_type="architectural",
                decision={
                    "decision": f"Decision {i}",
                    "rationale": f"Rationale {i}",
                    "context": {"index": i}
                }
            )

        logging_time = time.perf_counter() - start_time

        print(f"\nStress Test - Many Decisions:")
        print(f"  Logged 100 decisions in {logging_time:.2f}s ({100/logging_time:.2f} decisions/sec)")

        # Performance assertion
        self.assertLess(logging_time, 5.0, "Should log 100 decisions in under 5 seconds")


if __name__ == "__main__":
    # Run all benchmarks
    unittest.main(verbosity=2)
