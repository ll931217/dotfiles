#!/usr/bin/env python3
"""
Maestro PRD Requirement Validator - Validates PRD requirements are met

Analyzes PRD requirements and validates implementation:
- Parses PRD frontmatter for requirements
- Tracks requirement implementation status
- Validates completion of all requirements
- Provides detailed requirement coverage report
"""

import json
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
sys.path.insert(0, str(maestro_root / "scripts"))
sys.path.insert(0, str(maestro_root / "decision-engine" / "scripts"))

from session_manager import SessionManager
from decision_logger import DecisionLogger


class RequirementStatus(Enum):
    """Status of a PRD requirement."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VALIDATED = "validated"
    BLOCKED = "blocked"


@dataclass
class Requirement:
    """A PRD requirement with metadata."""

    id: str
    title: str
    description: str
    category: str
    priority: str
    status: RequirementStatus = RequirementStatus.PENDING
    validation_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status.value,
            "validation_criteria": self.validation_criteria,
            "dependencies": self.dependencies,
            "evidence": self.evidence,
            "notes": self.notes,
        }


@dataclass
class ValidationResult:
    """Result of PRD requirement validation."""

    prd_path: str
    total_requirements: int = 0
    implemented_requirements: int = 0
    validated_requirements: int = 0
    blocked_requirements: int = 0
    requirements: List[Requirement] = field(default_factory=list)
    coverage_percentage: float = field(init=False)
    missing_requirements: List[str] = field(default_factory=list)
    critical_gaps: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calculate coverage percentage after initialization."""
        self.coverage_percentage = (
            self.validated_requirements / self.total_requirements * 100
            if self.total_requirements > 0
            else 0.0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prd_path": self.prd_path,
            "total_requirements": self.total_requirements,
            "implemented_requirements": self.implemented_requirements,
            "validated_requirements": self.validated_requirements,
            "blocked_requirements": self.blocked_requirements,
            "requirements": [r.to_dict() for r in self.requirements],
            "coverage_percentage": self.coverage_percentage,
            "missing_requirements": self.missing_requirements,
            "critical_gaps": self.critical_gaps,
        }

    @property
    def all_requirements_met(self) -> bool:
        """Check if all requirements are validated."""
        return self.validated_requirements == self.total_requirements and self.total_requirements > 0

    @property
    def all_requirements_implemented(self) -> bool:
        """Check if all requirements are implemented."""
        return (
            self.implemented_requirements + self.validated_requirements
        ) == self.total_requirements and self.total_requirements > 0


class PRDRequirementValidator:
    """
    Validates PRD requirements are implemented and tested.

    Parses PRD frontmatter, tracks requirement status, and validates completion.
    """

    def __init__(self, project_root: Path, session_id: str):
        """
        Initialize PRD Requirement Validator.

        Args:
            project_root: Root directory of the project
            session_id: Current session ID
        """
        self.project_root = Path(project_root).resolve()
        self.session_id = session_id

        # Initialize components
        self.session_manager = SessionManager(self.project_root)
        self.decision_logger = DecisionLogger(session_id, self.project_root)

        # Setup logging
        self.logger = logging.getLogger(f"maestro.prdvalidator.{session_id[:8]}")

    def parse_prd_requirements(self, prd_path: Path) -> List[Requirement]:
        """
        Parse requirements from PRD frontmatter.

        Args:
            prd_path: Path to PRD markdown file

        Returns:
            List of Requirement objects
        """
        self.logger.info(f"Parsing PRD requirements from {prd_path}")

        try:
            content = prd_path.read_text()

            # Extract frontmatter
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not frontmatter_match:
                self.logger.warning(f"No frontmatter found in {prd_path}")
                return []

            frontmatter_text = frontmatter_match.group(1)
            frontmatter = yaml.safe_load(frontmatter_text)

            requirements = []

            # Parse requirements from frontmatter
            raw_requirements = frontmatter.get("requirements", [])
            if not raw_requirements:
                self.logger.warning(f"No requirements found in PRD frontmatter")
                return []

            for idx, req in enumerate(raw_requirements):
                requirement = Requirement(
                    id=req.get("id", f"REQ-{idx + 1}"),
                    title=req.get("title", f"Requirement {idx + 1}"),
                    description=req.get("description", ""),
                    category=req.get("category", "general"),
                    priority=req.get("priority", "P2"),
                    validation_criteria=req.get("validation_criteria", []),
                    dependencies=req.get("dependencies", []),
                )
                requirements.append(requirement)

            self.logger.info(f"Parsed {len(requirements)} requirements from PRD")
            return requirements

        except Exception as e:
            self.logger.error(f"Failed to parse PRD requirements: {e}")
            return []

    def validate_requirements(
        self,
        prd_path: Path,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate PRD requirements are met.

        Args:
            prd_path: Path to PRD markdown file
            context: Optional validation context (e.g., task completion status)

        Returns:
            ValidationResult with detailed status
        """
        self.logger.info(f"Validating PRD requirements from {prd_path}")

        context = context or {}

        # Parse requirements from PRD
        requirements = self.parse_prd_requirements(prd_path)

        if not requirements:
            return ValidationResult(
                prd_path=str(prd_path),
                coverage_percentage=0.0,
            )

        # Update requirement status based on context
        requirements = self._update_requirement_status(requirements, context)

        # Calculate statistics
        total = len(requirements)
        implemented = sum(1 for r in requirements if r.status == RequirementStatus.IMPLEMENTED)
        validated = sum(1 for r in requirements if r.status == RequirementStatus.VALIDATED)
        blocked = sum(1 for r in requirements if r.status == RequirementStatus.BLOCKED)

        # Identify gaps
        missing = [r.id for r in requirements if r.status == RequirementStatus.PENDING]
        critical_gaps = [
            r.id for r in requirements
            if r.priority in ["P0", "P1"] and r.status not in [RequirementStatus.IMPLEMENTED, RequirementStatus.VALIDATED]
        ]

        result = ValidationResult(
            prd_path=str(prd_path),
            total_requirements=total,
            implemented_requirements=implemented + validated,
            validated_requirements=validated,
            blocked_requirements=blocked,
            requirements=requirements,
            missing_requirements=missing,
            critical_gaps=critical_gaps,
        )

        # Log validation result
        self.decision_logger.log_decision(
            decision_type="prd_validation",
            decision={
                "decision": f"PRD requirement validation: {result.coverage_percentage:.1f}% coverage ({validated}/{total} validated)",
                "rationale": f"Analyzed {total} requirements, {validated} fully validated, {implemented + validated} implemented",
                "prd_path": str(prd_path),
                "coverage_percentage": result.coverage_percentage,
                "total_requirements": total,
                "validated_requirements": validated,
                "critical_gaps": len(result.critical_gaps),
            },
        )

        return result

    def _update_requirement_status(
        self,
        requirements: List[Requirement],
        context: Dict[str, Any],
    ) -> List[Requirement]:
        """
        Update requirement status based on context.

        Args:
            requirements: List of requirements
            context: Validation context with task completion data

        Returns:
            Updated list of requirements
        """
        # Get task completion status from context
        completed_tasks = context.get("completed_tasks", [])
        in_progress_tasks = context.get("in_progress_tasks", [])

        for req in requirements:
            # Check if requirement is validated (all validation criteria met)
            if self._is_requirement_validated(req, completed_tasks):
                req.status = RequirementStatus.VALIDATED
            # Check if requirement is implemented (tasks complete but not validated)
            elif self._is_requirement_implemented(req, completed_tasks):
                req.status = RequirementStatus.IMPLEMENTED
            # Check if requirement is in progress
            elif self._is_requirement_in_progress(req, in_progress_tasks):
                req.status = RequirementStatus.IN_PROGRESS
            # Check if requirement is blocked (dependencies not met)
            elif self._is_requirement_blocked(req, requirements):
                req.status = RequirementStatus.BLOCKED
            else:
                req.status = RequirementStatus.PENDING

        return requirements

    def _is_requirement_validated(self, requirement: Requirement, completed_tasks: List[str]) -> bool:
        """Check if requirement is validated."""
        # Requirement is validated if all validation criteria have corresponding completed tasks
        if not requirement.validation_criteria:
            return False

        # Check if validation criteria match completed tasks
        for criterion in requirement.validation_criteria:
            criterion_lower = criterion.lower()
            if not any(criterion_lower in task.lower() for task in completed_tasks):
                return False

        return True

    def _is_requirement_implemented(self, requirement: Requirement, completed_tasks: List[str]) -> bool:
        """Check if requirement is implemented."""
        # Check if any completed task matches the requirement
        req_text = f"{requirement.id} {requirement.title} {requirement.description}".lower()

        for task in completed_tasks:
            if any(word in task.lower() for word in req_text.split()[:5]):
                return True

        return False

    def _is_requirement_in_progress(self, requirement: Requirement, in_progress_tasks: List[str]) -> bool:
        """Check if requirement is in progress."""
        req_text = f"{requirement.id} {requirement.title}".lower()

        for task in in_progress_tasks:
            if any(word in task.lower() for word in req_text.split()[:3]):
                return True

        return False

    def _is_requirement_blocked(self, requirement: Requirement, all_requirements: List[Requirement]) -> bool:
        """Check if requirement is blocked by unmet dependencies."""
        if not requirement.dependencies:
            return False

        req_map = {r.id: r for r in all_requirements}

        for dep_id in requirement.dependencies:
            dep = req_map.get(dep_id)
            if not dep:
                continue

            if dep.status not in [RequirementStatus.IMPLEMENTED, RequirementStatus.VALIDATED]:
                return True

        return False

    def generate_requirement_report(self, result: ValidationResult) -> str:
        """
        Generate human-readable requirement validation report.

        Args:
            result: ValidationResult to report on

        Returns:
            Formatted report string
        """
        lines = [
            "# PRD Requirement Validation Report",
            "",
            f"**PRD**: {result.prd_path}",
            f"**Coverage**: {result.coverage_percentage:.1f}%",
            f"**Status**: {'✅ All requirements met' if result.all_requirements_met else '⚠️ Requirements pending'}",
            "",
            "## Summary",
            "",
            f"- Total Requirements: {result.total_requirements}",
            f"- Implemented: {result.implemented_requirements}",
            f"- Validated: {result.validated_requirements}",
            f"- Blocked: {result.blocked_requirements}",
            "",
        ]

        if result.critical_gaps:
            lines.extend([
                "## 🚨 Critical Gaps",
                "",
            ])
            for gap_id in result.critical_gaps:
                req = next((r for r in result.requirements if r.id == gap_id), None)
                if req:
                    lines.append(f"- **{req.id}**: {req.title}")

            lines.append("")

        if result.missing_requirements:
            lines.extend([
                "## Missing Requirements",
                "",
            ])
            for req_id in result.missing_requirements:
                req = next((r for r in result.requirements if r.id == req_id), None)
                if req:
                    lines.append(f"- **{req.id}**: {req.title}")

            lines.append("")

        lines.extend([
            "## Requirement Details",
            "",
        ])

        for req in result.requirements:
            status_emoji = {
                RequirementStatus.VALIDATED: "✅",
                RequirementStatus.IMPLEMENTED: "🟡",
                RequirementStatus.IN_PROGRESS: "🔄",
                RequirementStatus.BLOCKED: "🚫",
                RequirementStatus.PENDING: "⚪",
            }.get(req.status, "❓")

            lines.extend([
                f"### {status_emoji} {req.id}: {req.title}",
                "",
                f"**Priority**: {req.priority} | **Status**: {req.status.value}",
                "",
                f"{req.description}",
                "",
            ])

            if req.validation_criteria:
                lines.extend([
                    "**Validation Criteria**:",
                    "",
                ])
                for criterion in req.validation_criteria:
                    lines.append(f"- {criterion}")
                lines.append("")

            if req.evidence:
                lines.extend([
                    "**Evidence**:",
                    "",
                ])
                for evidence in req.evidence:
                    lines.append(f"- {evidence}")
                lines.append("")

        return "\n".join(lines)


def main():
    """Example usage of PRDRequirementValidator."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    if len(sys.argv) < 3:
        print("Usage: python prd_requirement_validator.py <session-id> <prd-path>")
        sys.exit(1)

    project_root = Path.cwd()
    session_id = sys.argv[1]
    prd_path = Path(sys.argv[2])

    # Create validator
    validator = PRDRequirementValidator(project_root, session_id)

    # Validate requirements
    result = validator.validate_requirements(prd_path)

    # Generate report
    report = validator.generate_requirement_report(result)
    print(report)

    print(f"\nAll requirements met: {result.all_requirements_met}")
    print(f"All requirements implemented: {result.all_requirements_implemented}")


if __name__ == "__main__":
    main()
