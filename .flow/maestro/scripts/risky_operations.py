#!/usr/bin/env python3
"""
Maestro Risky Operations Detector

Detects and classifies risky operations that require pre-operation checkpoints
for safe rollback during Maestro orchestration sessions.
"""

import logging
import re
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger("maestro.risky_operations")


class RiskLevel(str, Enum):
    """Risk level classification for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OperationRisk:
    """Risk assessment for an operation."""
    is_risky: bool
    operation_type: Optional[str]
    risk_level: RiskLevel
    description: str
    requires_checkpoint: bool
    suggested_mitigation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_risky": self.is_risky,
            "operation_type": self.operation_type,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "requires_checkpoint": self.requires_checkpoint,
            "suggested_mitigation": self.suggested_mitigation,
        }


class RiskyOperationDetector:
    """
    Detects and classifies risky operations requiring pre-operation checkpoints.

    Uses pattern matching to identify potentially dangerous operations like:
    - Git operations that modify history (push, amend, rebase)
    - File deletion operations
    - Bulk modifications
    - Database migrations
    - External API calls with side effects
    """

    # Operation patterns for risky operations
    OPERATION_PATTERNS = {
        'git_push': {
            'pattern': r'git\s+(push|force\s+push|commit\s+--amend|rebase)',
            'risk_level': RiskLevel.HIGH,
            'description': 'Git operation that modifies remote history',
            'mitigation': 'Create checkpoint before pushing, verify branch is correct',
        },
        'file_deletion': {
            'pattern': r'(rm\s+-rf|del\s+/.*|unlink|shred|\brm\b.*-\w*r[e]c)',
            'risk_level': RiskLevel.CRITICAL,
            'description': 'File or directory deletion operation',
            'mitigation': 'Verify paths are correct, create checkpoint, use --dry-run first',
        },
        'bulk_modification': {
            'pattern': r'(mass\s+delete|bulk\s+(delete|update|remove)|replace\s+all|find.*-exec\s+rm)',
            'risk_level': RiskLevel.HIGH,
            'description': 'Bulk modification affecting multiple files',
            'mitigation': 'Review affected files, create checkpoint, test on subset first',
        },
        'database_migration': {
            'pattern': r'(migration|migrate\b|rollback\s+(db|database)|drop\s+table|truncate|alembic|flyway|liquibase)',
            'risk_level': RiskLevel.CRITICAL,
            'description': 'Database schema modification',
            'mitigation': 'Backup database, create checkpoint, test migration on staging',
        },
        'deployment': {
            'pattern': r'(deploy|release|publish|upload\s+to\s+production)',
            'risk_level': RiskLevel.CRITICAL,
            'description': 'Deployment to production environment',
            'mitigation': 'Create checkpoint, run pre-deployment checks, have rollback plan',
        },
        'dependency_update': {
            'pattern': r'(npm\s+install|pip\s+install|bundle\s+install|cargo\s+update).*(--upgrade|-U)',
            'risk_level': RiskLevel.MEDIUM,
            'description': 'Dependency version updates',
            'mitigation': 'Create checkpoint, review changelogs, test thoroughly',
        },
        'configuration_change': {
            'pattern': r'(config|settings|env)\s*(set|update|modify|change)',
            'risk_level': RiskLevel.MEDIUM,
            'description': 'Configuration modification',
            'mitigation': 'Create checkpoint, validate config, backup current settings',
        },
        'credential_rotation': {
            'pattern': r'(rotate|regenerate|reset)\s+(key|token|password|credential|secret)',
            'risk_level': RiskLevel.HIGH,
            'description': 'Credential or secret rotation',
            'mitigation': 'Create checkpoint, have recovery codes ready, test access',
        },
    }

    # Patterns that indicate safe operations (low risk)
    SAFE_OPERATION_PATTERNS = [
        r'git\s+(status|log|diff|show|branch)',
        r'ls\b|dir\b',
        r'cat\b|less\b|more\b',
        r'echo\b|print\b',
        r'test\s+--?dry-?run',
        r'--dry-run\b',
        r'--check\b',
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risky operation detector.

        Args:
            config: Optional configuration with custom patterns or thresholds
        """
        self.config = config or {}

        # Compile regex patterns for performance
        self.compiled_patterns = {
            op_type: re.compile(pattern_data['pattern'], re.IGNORECASE)
            for op_type, pattern_data in self.OPERATION_PATTERNS.items()
        }

        self.compiled_safe_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.SAFE_OPERATION_PATTERNS
        ]

        # Custom patterns from config
        if 'custom_patterns' in self.config:
            for op_type, pattern_data in self.config['custom_patterns'].items():
                self.compiled_patterns[op_type] = re.compile(
                    pattern_data['pattern'],
                    re.IGNORECASE
                )

    def is_risky_operation(self, operation: str) -> bool:
        """
        Determine if an operation is risky.

        Args:
            operation: Operation command or description string

        Returns:
            True if operation is considered risky
        """
        risk = self.classify_operation(operation)
        return risk.is_risky

    def classify_operation(self, operation: str) -> OperationRisk:
        """
        Classify an operation and assess its risk level.

        Args:
            operation: Operation command or description string

        Returns:
            OperationRisk object with detailed assessment
        """
        if not operation or not operation.strip():
            return OperationRisk(
                is_risky=False,
                operation_type=None,
                risk_level=RiskLevel.LOW,
                description="Empty operation",
                requires_checkpoint=False,
            )

        operation_stripped = operation.strip()

        # Check if it matches safe patterns first
        for safe_pattern in self.compiled_safe_patterns:
            if safe_pattern.search(operation_stripped):
                return OperationRisk(
                    is_risky=False,
                    operation_type=None,
                    risk_level=RiskLevel.LOW,
                    description=f"Safe operation: {operation_stripped}",
                    requires_checkpoint=False,
                )

        # Check against risky operation patterns
        for op_type, compiled_pattern in self.compiled_patterns.items():
            if compiled_pattern.search(operation_stripped):
                pattern_data = self.OPERATION_PATTERNS.get(op_type, {})
                if isinstance(pattern_data, dict):
                    risk_level = pattern_data.get('risk_level', RiskLevel.MEDIUM)
                    description = pattern_data.get('description', 'Risky operation detected')
                    mitigation = pattern_data.get('mitigation')
                else:
                    risk_level = RiskLevel.MEDIUM
                    description = 'Risky operation detected'
                    mitigation = None

                return OperationRisk(
                    is_risky=True,
                    operation_type=op_type,
                    risk_level=risk_level,
                    description=description,
                    requires_checkpoint=True,
                    suggested_mitigation=mitigation,
                )

        # Default: unknown operation, treat as medium risk
        return OperationRisk(
            is_risky=False,
            operation_type=None,
            risk_level=RiskLevel.LOW,
            description=f"Unknown operation: {operation_stripped}",
            requires_checkpoint=False,
        )

    def get_operation_description(self, operation: str) -> str:
        """
        Get a human-readable description of the operation risk.

        Args:
            operation: Operation command or description string

        Returns:
            Human-readable description
        """
        risk = self.classify_operation(operation)

        if risk.is_risky:
            return (
                f"[{risk.risk_level.value.upper()}] {risk.description}\n"
                f"Operation Type: {risk.operation_type}\n"
                f"Requires Checkpoint: Yes\n"
                f"Suggested Mitigation: {risk.suggested_mitigation or 'None provided'}"
            )
        else:
            return f"[SAFE] {risk.description}"

    def should_create_checkpoint(self, operation: str) -> bool:
        """
        Determine if a checkpoint should be created before an operation.

        Args:
            operation: Operation command or description string

        Returns:
            True if checkpoint should be created
        """
        risk = self.classify_operation(operation)
        return risk.requires_checkpoint

    def get_risky_operations_from_list(
        self,
        operations: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze a list of operations and return risky ones.

        Args:
            operations: List of operation strings

        Returns:
            List of dictionaries with operation details and risk assessment
        """
        risky_ops = []

        for i, operation in enumerate(operations):
            risk = self.classify_operation(operation)
            if risk.is_risky:
                risky_ops.append({
                    'index': i,
                    'operation': operation,
                    'risk': risk.to_dict(),
                })

        return risky_ops

    def estimate_recovery_complexity(self, operation: str) -> str:
        """
        Estimate the complexity of recovering from a failed operation.

        Args:
            operation: Operation command or description string

        Returns:
            Recovery complexity level: 'simple', 'moderate', 'complex', 'very_complex'
        """
        risk = self.classify_operation(operation)

        if not risk.is_risky:
            return 'simple'

        if risk.risk_level == RiskLevel.CRITICAL:
            if risk.operation_type in ['database_migration', 'deployment']:
                return 'very_complex'
            return 'complex'

        if risk.risk_level == RiskLevel.HIGH:
            if 'bulk' in operation.lower():
                return 'complex'
            return 'moderate'

        return 'moderate'


def main():
    """CLI for testing risky operation detection."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Maestro Risky Operations Detector"
    )
    parser.add_argument(
        "operation",
        help="Operation command or description to analyze",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()

    detector = RiskyOperationDetector()
    risk = detector.classify_operation(args.operation)

    if args.format == "json":
        print(json.dumps(risk.to_dict(), indent=2))
    else:
        print(detector.get_operation_description(args.operation))


if __name__ == "__main__":
    main()
