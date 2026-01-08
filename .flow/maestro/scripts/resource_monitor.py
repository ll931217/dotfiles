#!/usr/bin/env python3
"""
Resource Monitor for Maestro Orchestrator

Monitors and enforces resource limits during autonomous workflow execution.
Tracks token usage, API calls, time elapsed, and provides graceful degradation
when limits are approached.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class LimitStatus(Enum):
    """Status of resource limit checking."""
    OK = "ok"
    APPROACHING = "approaching"
    EXCEEDED = "exceeded"


@dataclass
class ResourceLimits:
    """Configuration for resource limits."""
    max_duration_seconds: int = 3600  # 1 hour default
    max_tokens: int = 1000000  # 1M tokens default
    max_api_calls: int = 1000  # API call budget
    checkpoint_interval: int = 300  # 5 minutes default

    # Warning thresholds (percentage of limit)
    duration_warning_threshold: float = 0.80  # 80%
    token_warning_threshold: float = 0.80  # 80%
    api_call_warning_threshold: float = 0.80  # 80%

    # Completion threshold for continuing despite approaching limits
    completion_threshold: float = 0.80  # 80% complete


@dataclass
class ResourceUsage:
    """Current resource usage statistics."""
    duration_seconds: float
    tokens_used: int
    api_calls_made: int
    checkpoints_created: int

    # Timestamps
    start_time: datetime
    last_operation_time: datetime
    last_checkpoint_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "duration_seconds": self.duration_seconds,
            "tokens_used": self.tokens_used,
            "api_calls_made": self.api_calls_made,
            "checkpoints_created": self.checkpoints_created,
            "start_time": self.start_time.isoformat(),
            "last_operation_time": self.last_operation_time.isoformat(),
            "last_checkpoint_time": self.last_checkpoint_time.isoformat() if self.last_checkpoint_time else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceUsage":
        """Create from dictionary."""
        return cls(
            duration_seconds=data["duration_seconds"],
            tokens_used=data["tokens_used"],
            api_calls_made=data["api_calls_made"],
            checkpoints_created=data["checkpoints_created"],
            start_time=datetime.fromisoformat(data["start_time"]),
            last_operation_time=datetime.fromisoformat(data["last_operation_time"]),
            last_checkpoint_time=datetime.fromisoformat(data["last_checkpoint_time"]) if data.get("last_checkpoint_time") else None,
        )


@dataclass
class LimitCheckResult:
    """Result of a limit check."""
    status: LimitStatus
    approaching_limits: list[str] = field(default_factory=list)
    exceeded_limits: list[str] = field(default_factory=list)
    can_continue: bool = True
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "approaching_limits": self.approaching_limits,
            "exceeded_limits": self.exceeded_limits,
            "can_continue": self.can_continue,
            "reason": self.reason,
        }


class ResourceMonitor:
    """
    Monitor and enforce resource limits during workflow execution.

    Tracks token usage, API calls, time elapsed, and provides graceful
    degradation when limits are approached.
    """

    def __init__(self, limits: ResourceLimits, session_id: str, project_root: Optional[Path] = None):
        """
        Initialize ResourceMonitor.

        Args:
            limits: ResourceLimits configuration
            session_id: Unique session identifier
            project_root: Optional project root path for saving state
        """
        self.limits = limits
        self.session_id = session_id
        self.project_root = Path(project_root) if project_root else None

        # Initialize usage tracking
        start_time = datetime.now()
        self.usage = ResourceUsage(
            duration_seconds=0.0,
            tokens_used=0,
            api_calls_made=0,
            checkpoints_created=0,
            start_time=start_time,
            last_operation_time=start_time,
        )

        # Setup logging
        self.logger = logging.getLogger(f"ResourceMonitor[{session_id}]")
        self.logger.info(f"ResourceMonitor initialized with limits: {self._limits_summary()}")

    def _limits_summary(self) -> str:
        """Get summary of configured limits."""
        return (
            f"max_duration={self.limits.max_duration_seconds}s, "
            f"max_tokens={self.limits.max_tokens}, "
            f"max_api_calls={self.limits.max_api_calls}"
        )

    def check_limits(self) -> LimitCheckResult:
        """
        Check current resource usage against limits.

        Returns:
            LimitCheckResult with status and details
        """
        now = datetime.now()
        self.usage.duration_seconds = (now - self.usage.start_time).total_seconds()

        approaching_limits = []
        exceeded_limits = []

        # Check duration
        duration_ratio = self.usage.duration_seconds / self.limits.max_duration_seconds
        if duration_ratio >= 1.0:
            exceeded_limits.append("duration")
        elif duration_ratio >= self.limits.duration_warning_threshold:
            approaching_limits.append("duration")

        # Check tokens
        token_ratio = self.usage.tokens_used / self.limits.max_tokens
        if token_ratio >= 1.0:
            exceeded_limits.append("tokens")
        elif token_ratio >= self.limits.token_warning_threshold:
            approaching_limits.append("tokens")

        # Check API calls
        api_ratio = self.usage.api_calls_made / self.limits.max_api_calls
        if api_ratio >= 1.0:
            exceeded_limits.append("api_calls")
        elif api_ratio >= self.limits.api_call_warning_threshold:
            approaching_limits.append("api_calls")

        # Determine status
        if exceeded_limits:
            status = LimitStatus.EXCEEDED
            can_continue = False
            reason = f"Exceeded limits: {', '.join(exceeded_limits)}"
        elif approaching_limits:
            status = LimitStatus.APPROACHING
            can_continue = True  # Will be re-evaluated in should_continue
            reason = f"Approaching limits: {', '.join(approaching_limits)}"
        else:
            status = LimitStatus.OK
            can_continue = True
            reason = "All limits within acceptable range"

        result = LimitCheckResult(
            status=status,
            approaching_limits=approaching_limits,
            exceeded_limits=exceeded_limits,
            can_continue=can_continue,
            reason=reason,
        )

        # Log status
        if status != LimitStatus.OK:
            self.logger.warning(f"Limit check: {reason}")

        return result

    def record_operation(self, tokens: int, api_call: bool = True):
        """
        Record resource usage for an operation.

        Args:
            tokens: Number of tokens used in the operation
            api_call: Whether this was an API call (default: True)
        """
        self.usage.tokens_used += tokens
        if api_call:
            self.usage.api_calls_made += 1

        self.usage.last_operation_time = datetime.now()

        # Check if we need a checkpoint
        if self._should_create_checkpoint():
            self._create_checkpoint()

    def should_continue(self, progress_estimate: float) -> bool:
        """
        Determine if execution should continue based on progress and limits.

        Implements graceful degradation logic:
        - If limits are OK, always continue
        - If approaching limits and progress > 80%, continue to completion
        - If approaching limits and progress < 80%, stop gracefully

        Args:
            progress_estimate: Estimated completion (0.0 to 1.0)

        Returns:
            True if execution should continue, False otherwise
        """
        limit_check = self.check_limits()

        if limit_check.status == LimitStatus.EXCEEDED:
            self.logger.warning(f"Cannot continue: {limit_check.reason}")
            return False

        if limit_check.status == LimitStatus.OK:
            return True

        # Approaching limits - evaluate based on progress
        if progress_estimate >= self.limits.completion_threshold:
            self.logger.info(
                f"Approaching limits but progress is {progress_estimate*100:.1f}%, "
                f"continuing to completion"
            )
            return True
        else:
            self.logger.warning(
                f"Approaching limits and progress is only {progress_estimate*100:.1f}%, "
                f"stopping gracefully to save partial results"
            )
            return False

    def get_usage_report(self) -> ResourceUsage:
        """
        Get current resource usage report.

        Returns:
            ResourceUsage with current statistics
        """
        # Update duration
        now = datetime.now()
        self.usage.duration_seconds = (now - self.usage.start_time).total_seconds()

        return self.usage

    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Get a summary of resource usage with percentages.

        Returns:
            Dictionary with usage statistics and percentages
        """
        usage = self.get_usage_report()

        duration_pct = (usage.duration_seconds / self.limits.max_duration_seconds) * 100
        tokens_pct = (usage.tokens_used / self.limits.max_tokens) * 100
        api_calls_pct = (usage.api_calls_made / self.limits.max_api_calls) * 100

        return {
            "duration": {
                "used": usage.duration_seconds,
                "limit": self.limits.max_duration_seconds,
                "percentage": duration_pct,
                "remaining": max(0, self.limits.max_duration_seconds - usage.duration_seconds),
            },
            "tokens": {
                "used": usage.tokens_used,
                "limit": self.limits.max_tokens,
                "percentage": tokens_pct,
                "remaining": max(0, self.limits.max_tokens - usage.tokens_used),
            },
            "api_calls": {
                "used": usage.api_calls_made,
                "limit": self.limits.max_api_calls,
                "percentage": api_calls_pct,
                "remaining": max(0, self.limits.max_api_calls - usage.api_calls_made),
            },
            "checkpoints": usage.checkpoints_created,
            "session_id": self.session_id,
        }

    def _should_create_checkpoint(self) -> bool:
        """Check if a checkpoint should be created based on time interval."""
        if self.usage.last_checkpoint_time is None:
            return True

        elapsed_since_checkpoint = (
            datetime.now() - self.usage.last_checkpoint_time
        ).total_seconds()

        return elapsed_since_checkpoint >= self.limits.checkpoint_interval

    def _create_checkpoint(self):
        """Create a checkpoint of current resource usage state."""
        self.usage.checkpoints_created += 1
        self.usage.last_checkpoint_time = datetime.now()

        self.logger.info(
            f"Checkpoint #{self.usage.checkpoints_created} created: "
            f"{self._get_checkpoint_summary()}"
        )

        # Save checkpoint to file if project_root is set
        if self.project_root:
            self._save_checkpoint_to_file()

    def _get_checkpoint_summary(self) -> str:
        """Get a summary of current resource usage."""
        usage = self.get_usage_report()
        return (
            f"duration={usage.duration_seconds:.1f}s, "
            f"tokens={usage.tokens_used}, "
            f"api_calls={usage.api_calls_made}"
        )

    def _save_checkpoint_to_file(self):
        """Save checkpoint state to file."""
        if not self.project_root:
            return

        checkpoints_dir = self.project_root / ".flow" / "maestro" / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_file = (
            checkpoints_dir / f"resource_checkpoint_{self.session_id}_{self.usage.checkpoints_created}.json"
        )

        checkpoint_data = {
            "session_id": self.session_id,
            "checkpoint_number": self.usage.checkpoints_created,
            "timestamp": datetime.now().isoformat(),
            "usage": self.usage.to_dict(),
            "limits": {
                "max_duration_seconds": self.limits.max_duration_seconds,
                "max_tokens": self.limits.max_tokens,
                "max_api_calls": self.limits.max_api_calls,
                "checkpoint_interval": self.limits.checkpoint_interval,
            },
        }

        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            self.logger.debug(f"Checkpoint saved to {checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")

    def get_time_remaining(self) -> float:
        """
        Get estimated time remaining before duration limit.

        Returns:
            Seconds remaining (0 if limit exceeded)
        """
        current_duration = (datetime.now() - self.usage.start_time).total_seconds()
        return max(0, self.limits.max_duration_seconds - current_duration)

    def get_tokens_remaining(self) -> int:
        """
        Get estimated tokens remaining before token limit.

        Returns:
            Tokens remaining (0 if limit exceeded)
        """
        return max(0, self.limits.max_tokens - self.usage.tokens_used)

    def get_api_calls_remaining(self) -> int:
        """
        Get estimated API calls remaining before API call limit.

        Returns:
            API calls remaining (0 if limit exceeded)
        """
        return max(0, self.limits.max_api_calls - self.usage.api_calls_made)

    def get_estimated_completion_possible(self, estimated_tokens_remaining: int, estimated_time_remaining: int) -> bool:
        """
        Check if completion is possible with estimated remaining resources.

        Args:
            estimated_tokens_remaining: Estimated tokens needed to complete
            estimated_time_remaining: Estimated time (seconds) needed to complete

        Returns:
            True if completion seems possible with remaining resources
        """
        tokens_ok = self.get_tokens_remaining() >= estimated_tokens_remaining
        time_ok = self.get_time_remaining() >= estimated_time_remaining

        return tokens_ok and time_ok

    def log_status(self):
        """Log current resource usage status."""
        summary = self.get_usage_summary()
        self.logger.info(
            f"Resource Usage: "
            f"duration: {summary['duration']['percentage']:.1f}%, "
            f"tokens: {summary['tokens']['percentage']:.1f}%, "
            f"api_calls: {summary['api_calls']['percentage']:.1f}%"
        )
