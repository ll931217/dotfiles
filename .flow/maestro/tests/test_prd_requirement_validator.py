#!/usr/bin/env python3
"""
Tests for PRD Requirement Validator
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from prd_requirement_validator import (
    PRDRequirementValidator,
    Requirement,
    RequirementStatus,
    ValidationResult,
)


class TestRequirement(unittest.TestCase):
    """Test cases for Requirement."""

    def test_requirement_creation(self):
        """Test creating Requirement."""
        req = Requirement(
            id="REQ-1",
            title="Test Requirement",
            description="A test requirement",
            category="testing",
            priority="P1",
        )

        self.assertEqual(req.id, "REQ-1")
        self.assertEqual(req.title, "Test Requirement")
        self.assertEqual(req.status, RequirementStatus.PENDING)

    def test_to_dict(self):
        """Test converting Requirement to dict."""
        req = Requirement(
            id="REQ-1",
            title="Test Requirement",
            description="A test requirement",
            category="testing",
            priority="P1",
            validation_criteria=["Test passes"],
        )

        data = req.to_dict()

        self.assertEqual(data["id"], "REQ-1")
        self.assertEqual(data["title"], "Test Requirement")
        self.assertEqual(data["status"], "pending")
        self.assertEqual(len(data["validation_criteria"]), 1)


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult."""

    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=10,
            implemented_requirements=8,
            validated_requirements=5,
        )

        self.assertEqual(result.total_requirements, 10)
        self.assertEqual(result.implemented_requirements, 8)
        self.assertEqual(result.validated_requirements, 5)

    def test_all_requirements_met(self):
        """Test all_requirements_met property."""
        # All validated
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=10,
            validated_requirements=10,
        )
        self.assertTrue(result.all_requirements_met)

        # Not all validated
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=10,
            validated_requirements=5,
        )
        self.assertFalse(result.all_requirements_met)

    def test_all_requirements_implemented(self):
        """Test all_requirements_implemented property."""
        # All implemented or validated
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=10,
            implemented_requirements=7,
            validated_requirements=3,
        )
        self.assertTrue(result.all_requirements_implemented)

        # Not all implemented
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=10,
            implemented_requirements=5,
            validated_requirements=2,
        )
        self.assertFalse(result.all_requirements_implemented)

    def test_coverage_percentage(self):
        """Test coverage percentage calculation."""
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=10,
            validated_requirements=5,
        )
        self.assertEqual(result.coverage_percentage, 50.0)


class TestPRDRequirementValidator(unittest.TestCase):
    """Test cases for PRDRequirementValidator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.session_id = "test-session-123"

        # Create directory structure
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id).mkdir(
            parents=True, exist_ok=True
        )
        (self.project_root / ".flow" / "maestro" / "decisions").mkdir(parents=True, exist_ok=True)

        # Create session metadata
        from session_manager import SessionStatus
        import json

        session_metadata = {
            "session_id": self.session_id,
            "feature_request": "Test feature",
            "status": SessionStatus.VALIDATING.value,
            "current_phase": "validate",
            "start_time": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "git_context": {
                "branch": "main",
                "commit": "abc123",
                "repo_root": str(self.project_root),
            },
        }
        (self.project_root / ".flow" / "maestro" / "sessions" / self.session_id / "metadata.json").write_text(
            json.dumps(session_metadata)
        )

        # Mock git commands
        from unittest.mock import patch
        self.git_patcher = patch("subprocess.run")
        self.mock_run = self.git_patcher.start()
        self.mock_run.return_value = MagicMock(stdout="main\n", returncode=0)

        # Create validator
        self.validator = PRDRequirementValidator(self.project_root, self.session_id)

    def tearDown(self):
        """Clean up test fixtures."""
        self.git_patcher.stop()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test PRDRequirementValidator initialization."""
        self.assertEqual(self.validator.session_id, self.session_id)
        self.assertEqual(self.validator.project_root, self.project_root)

    def test_parse_prd_requirements(self):
        """Test parsing requirements from PRD."""
        # Create a PRD file with requirements
        prd_content = """---
title: Test PRD
status: approved
requirements:
  - id: REQ-1
    title: First requirement
    description: Implement first feature
    category: core
    priority: P0
    validation_criteria:
      - Unit tests pass
      - Integration tests pass
  - id: REQ-2
    title: Second requirement
    description: Implement second feature
    category: ui
    priority: P1
    dependencies:
      - REQ-1
---

# Test PRD

This is a test PRD.
"""

        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text(prd_content)

        requirements = self.validator.parse_prd_requirements(prd_path)

        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[0].id, "REQ-1")
        self.assertEqual(requirements[0].title, "First requirement")
        self.assertEqual(requirements[0].priority, "P0")
        self.assertEqual(len(requirements[0].validation_criteria), 2)
        self.assertEqual(requirements[1].id, "REQ-2")
        self.assertEqual(len(requirements[1].dependencies), 1)

    def test_parse_prd_no_frontmatter(self):
        """Test parsing PRD without frontmatter."""
        prd_content = """# Test PRD

This PRD has no frontmatter.
"""

        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text(prd_content)

        requirements = self.validator.parse_prd_requirements(prd_path)

        self.assertEqual(len(requirements), 0)

    def test_parse_prd_no_requirements(self):
        """Test parsing PRD without requirements."""
        prd_content = """---
title: Test PRD
status: draft
---

# Test PRD
"""

        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text(prd_content)

        requirements = self.validator.parse_prd_requirements(prd_path)

        self.assertEqual(len(requirements), 0)

    def test_validate_requirements_all_pending(self):
        """Test validation when all requirements are pending."""
        # Create PRD with requirements
        prd_content = """---
title: Test PRD
requirements:
  - id: REQ-1
    title: First requirement
    description: Implement first feature
    category: core
    priority: P0
  - id: REQ-2
    title: Second requirement
    description: Implement second feature
    category: ui
    priority: P1
---

# Test PRD
"""

        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text(prd_content)

        result = self.validator.validate_requirements(prd_path)

        self.assertEqual(result.total_requirements, 2)
        self.assertEqual(result.validated_requirements, 0)
        self.assertEqual(result.coverage_percentage, 0.0)
        self.assertFalse(result.all_requirements_met)

    def test_validate_requirements_with_completed_tasks(self):
        """Test validation with completed tasks."""
        prd_content = """---
title: Test PRD
requirements:
  - id: REQ-1
    title: First requirement
    description: Implement first feature
    category: core
    priority: P0
    validation_criteria:
      - Unit tests pass
  - id: REQ-2
    title: Second requirement
    description: Implement second feature
    category: ui
    priority: P1
---

# Test PRD
"""

        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text(prd_content)

        # Provide context with completed tasks
        context = {
            "completed_tasks": [
                "REQ-1: Implement first feature with unit tests",
                "Unit tests pass for REQ-1",
            ],
            "in_progress_tasks": [],
        }

        result = self.validator.validate_requirements(prd_path, context)

        self.assertEqual(result.total_requirements, 2)
        self.assertGreater(result.validated_requirements, 0)
        self.assertGreater(result.coverage_percentage, 0.0)

    def test_validate_requirements_critical_gaps(self):
        """Test validation identifies critical gaps."""
        prd_content = """---
title: Test PRD
requirements:
  - id: REQ-1
    title: Critical requirement
    description: Must implement
    category: core
    priority: P0
  - id: REQ-2
    title: Nice to have
    description: Optional feature
    category: ui
    priority: P3
---

# Test PRD
"""

        prd_path = self.project_root / "test-prd.md"
        prd_path.write_text(prd_content)

        result = self.validator.validate_requirements(prd_path)

        # P0 requirement should be in critical gaps
        self.assertIn("REQ-1", result.critical_gaps)
        self.assertNotIn("REQ-2", result.critical_gaps)

    def test_is_requirement_blocked(self):
        """Test requirement blocking logic."""
        req1 = Requirement(id="REQ-1", title="First", description="", category="core", priority="P0")
        req1.status = RequirementStatus.IMPLEMENTED

        req2 = Requirement(
            id="REQ-2",
            title="Second",
            description="",
            category="core",
            priority="P1",
            dependencies=["REQ-1"],
        )

        all_requirements = [req1, req2]

        # REQ-2 should not be blocked (REQ-1 is implemented)
        is_blocked = self.validator._is_requirement_blocked(req2, all_requirements)
        self.assertFalse(is_blocked)

        # Change REQ-1 to pending
        req1.status = RequirementStatus.PENDING

        # Now REQ-2 should be blocked
        is_blocked = self.validator._is_requirement_blocked(req2, all_requirements)
        self.assertTrue(is_blocked)

    def test_generate_requirement_report(self):
        """Test generating requirement report."""
        result = ValidationResult(
            prd_path="/path/to/prd.md",
            total_requirements=2,
            implemented_requirements=1,
            validated_requirements=1,
            requirements=[
                Requirement(
                    id="REQ-1",
                    title="Validated requirement",
                    description="Fully implemented",
                    category="core",
                    priority="P0",
                    status=RequirementStatus.VALIDATED,
                ),
                Requirement(
                    id="REQ-2",
                    title="Pending requirement",
                    description="Not started",
                    category="ui",
                    priority="P1",
                    status=RequirementStatus.PENDING,
                ),
            ],
            critical_gaps=["REQ-2"],
        )

        report = self.validator.generate_requirement_report(result)

        self.assertIn("PRD Requirement Validation Report", report)
        self.assertIn("50.0%", report)  # Coverage is auto-calculated as 50% (1/2)
        self.assertIn("REQ-1", report)
        self.assertIn("REQ-2", report)
        self.assertIn("Critical Gaps", report)


class TestRequirementStatus(unittest.TestCase):
    """Test cases for RequirementStatus enum."""

    def test_status_values(self):
        """Test RequirementStatus enum values."""
        self.assertEqual(RequirementStatus.PENDING.value, "pending")
        self.assertEqual(RequirementStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(RequirementStatus.IMPLEMENTED.value, "implemented")
        self.assertEqual(RequirementStatus.VALIDATED.value, "validated")
        self.assertEqual(RequirementStatus.BLOCKED.value, "blocked")


if __name__ == "__main__":
    unittest.main()
