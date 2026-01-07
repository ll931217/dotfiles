#!/usr/bin/env python3
"""
Test suite for Skill Orchestrator.

Tests skill detection, invocation, and context enrichment.
"""

import pytest
from datetime import datetime
from skill_orchestrator import (
    SkillOrchestrator,
    SkillMapping,
    SkillInvocation,
    SkillContext,
    EnrichedContext,
    SkillInvocationStatus,
)


class TestSkillOrchestrator:
    """Test suite for SkillOrchestrator class."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create a test orchestrator with temp directory."""
        orchestrator = SkillOrchestrator(repo_root=str(tmp_path))
        return orchestrator

    @pytest.fixture
    def sample_task_metadata(self):
        """Sample task metadata."""
        return {
            "description": "Create a login UI component with email and password fields",
            "category": "frontend",
            "priority": "high",
        }

    @pytest.fixture
    def sample_task_context(self):
        """Sample task context."""
        return {
            "prd_context": "User authentication flow with email/password",
            "code_context": "Existing auth service in src/auth.ts",
            "existing_patterns": "Use shadcn/ui components",
        }

    class TestSkillDetection:
        """Test skill detection logic."""

        def test_detect_from_metadata_explicit_skills(self, orchestrator):
            """Test detection when applicable_skills is in metadata."""
            task_metadata = {
                "description": "Build a UI component",
                "applicable_skills": ["frontend-design", "webapp-testing"],
            }

            skills = orchestrator.detect_applicable_skills(
                task_description=task_metadata["description"],
                task_metadata=task_metadata,
            )

            assert skills == ["frontend-design", "webapp-testing"]

        def test_detect_from_task_category(self, orchestrator):
            """Test detection based on task category."""
            skills = orchestrator.detect_applicable_skills(
                task_description="Build a component",
                task_category="frontend",
            )

            assert "frontend-design" in skills

        def test_detect_from_trigger_patterns(self, orchestrator):
            """Test detection from trigger patterns."""
            # Frontend trigger
            skills = orchestrator.detect_applicable_skills(
                task_description="Create a UI component for login",
            )
            assert "frontend-design" in skills

            # Testing trigger
            skills = orchestrator.detect_applicable_skills(
                task_description="Generate Playwright tests for checkout",
            )
            assert "webapp-testing" in skills

            # Documentation trigger
            skills = orchestrator.detect_applicable_skills(
                task_description="Generate API documentation for user service",
            )
            assert "document-skills" in skills

        def test_detect_multiple_skills(self, orchestrator):
            """Test detecting multiple applicable skills."""
            skills = orchestrator.detect_applicable_skills(
                task_description="Create UI component and generate tests",
            )

            # Should detect both frontend and testing skills
            assert "frontend-design" in skills
            assert "webapp-testing" in skills

        def test_detect_no_matching_skills(self, orchestrator):
            """Test when no skills match."""
            skills = orchestrator.detect_applicable_skills(
                task_description="Configure database connection string",
            )

            # Should not have UI-specific skills
            assert "frontend-design" not in skills
            assert "webapp-testing" not in skills

        def test_detect_case_insensitive(self, orchestrator):
            """Test pattern matching is case insensitive."""
            variations = [
                "CREATE A UI component",
                "create a UI component",
                "Create A Ui Component",
            ]

            for description in variations:
                skills = orchestrator.detect_applicable_skills(
                    task_description=description,
                )
                assert "frontend-design" in skills

        def test_detect_invalid_metadata_skills(self, orchestrator):
            """Test handling of invalid skill names in metadata."""
            task_metadata = {
                "description": "Build a component",
                "applicable_skills": ["frontend-design", "nonexistent-skill"],
            }

            skills = orchestrator.detect_applicable_skills(
                task_description=task_metadata["description"],
                task_metadata=task_metadata,
            )

            # Should only include valid skills
            assert skills == ["frontend-design"]

    class TestSkillInvocation:
        """Test skill invocation methods."""

        def test_invoke_skill_with_string_context(self, orchestrator):
            """Test invoking skill with string context."""
            invocation = orchestrator.invoke_skill(
                skill_name="frontend-design",
                context="Create a login form",
            )

            assert invocation.skill_name == "frontend-design"
            assert invocation.status == SkillInvocationStatus.PENDING
            assert "Create a login form" in invocation.args
            assert invocation.args.startswith("Create distinctive, production-grade")

        def test_invoke_skill_with_dict_context(self, orchestrator):
            """Test invoking skill with dict context."""
            context = {
                "task_description": "Build dashboard",
                "prd_context": "Analytics dashboard",
            }

            invocation = orchestrator.invoke_skill(
                skill_name="frontend-design",
                context=context,
            )

            assert invocation.skill_name == "frontend-design"
            assert "Build dashboard" in invocation.args
            assert "Analytics dashboard" in invocation.args

        def test_invoke_skill_with_skill_context(self, orchestrator):
            """Test invoking skill with SkillContext object."""
            context = SkillContext(
                task_description="Build dashboard",
                prd_context="Analytics dashboard",
                existing_patterns="Dark theme",
            )

            invocation = orchestrator.invoke_skill(
                skill_name="frontend-design",
                context=context,
            )

            assert invocation.skill_name == "frontend-design"
            assert "Build dashboard" in invocation.args
            assert "Analytics dashboard" in invocation.args
            assert "Dark theme" in invocation.args

        def test_invoke_skill_invalid_skill_name(self, orchestrator):
            """Test invoking with invalid skill name."""
            with pytest.raises(ValueError, match="Unknown skill"):
                orchestrator.invoke_skill(
                    skill_name="nonexistent-skill",
                    context="Test",
                )

        def test_invoke_skill_invalid_context_type(self, orchestrator):
            """Test invoking with invalid context type."""
            with pytest.raises(ValueError, match="Invalid context type"):
                orchestrator.invoke_skill(
                    skill_name="frontend-design",
                    context=123,  # Invalid type
                )

        def test_invocation_recorded_in_history(self, orchestrator):
            """Test that invocations are recorded in history."""
            orchestrator.invoke_skill(
                skill_name="frontend-design",
                context="Test task",
            )

            history = orchestrator.get_invocation_history()
            assert len(history) == 1
            assert history[0].skill_name == "frontend-design"

    class TestPromptFormatting:
        """Test prompt formatting from templates."""

        def test_format_prompt_basic(self, orchestrator):
            """Test basic prompt formatting."""
            context = SkillContext(
                task_description="Create login form",
            )

            prompt = orchestrator.format_skill_prompt(
                skill_name="frontend-design",
                context=context,
            )

            assert "Create login form" in prompt
            assert "production-grade frontend UI" in prompt

        def test_format_prompt_with_all_fields(self, orchestrator):
            """Test prompt formatting with all context fields."""
            context = SkillContext(
                task_description="Build dashboard",
                prd_context="Analytics PRD",
                existing_patterns="Grid layout",
            )

            prompt = orchestrator.format_skill_prompt(
                skill_name="frontend-design",
                context=context,
            )

            assert "Build dashboard" in prompt
            assert "Analytics PRD" in prompt
            assert "Grid layout" in prompt

        def test_format_prompt_missing_fields(self, orchestrator):
            """Test prompt formatting with missing optional fields."""
            context = SkillContext(
                task_description="Test task",
                # prd_context and other optional fields are None
            )

            prompt = orchestrator.format_skill_prompt(
                skill_name="frontend-design",
                context=context,
            )

            # Should not crash with missing fields
            assert "Test task" in prompt

        def test_format_prompt_different_skills(self, orchestrator):
            """Test formatting prompts for different skills."""
            context = SkillContext(task_description="Test task")

            frontend_prompt = orchestrator.format_skill_prompt(
                skill_name="frontend-design",
                context=context,
            )

            testing_prompt = orchestrator.format_skill_prompt(
                skill_name="webapp-testing",
                context=context,
            )

            # Prompts should be different
            assert frontend_prompt != testing_prompt
            assert "UI" in frontend_prompt
            assert "Playwright" in testing_prompt

    class TestContextEnrichment:
        """Test context enrichment with skill outputs."""

        def test_apply_skills_single_skill(self, orchestrator, sample_task_metadata, sample_task_context):
            """Test applying a single skill."""
            enriched = orchestrator.apply_skills_before_subagent(
                task_metadata=sample_task_metadata,
                task_context=sample_task_context,
            )

            assert isinstance(enriched, EnrichedContext)
            assert enriched.original_context == sample_task_context
            assert len(enriched.skill_invocations) > 0
            assert "frontend-design" in enriched.skill_guidance

        def test_apply_skills_multiple_skills(self, orchestrator):
            """Test applying multiple skills."""
            task_metadata = {
                "description": "Create UI and generate tests",
                "applicable_skills": ["frontend-design", "webapp-testing"],
            }
            task_context = {"prd_context": "Test PRD"}

            enriched = orchestrator.apply_skills_before_subagent(
                task_metadata=task_metadata,
                task_context=task_context,
            )

            assert len(enriched.skill_invocations) == 2
            assert "frontend-design" in enriched.skill_guidance
            assert "webapp-testing" in enriched.skill_guidance

        def test_apply_skills_no_applicable_skills(self, orchestrator):
            """Test when no skills are applicable."""
            task_metadata = {
                "description": "Configure database",
            }
            task_context = {}

            enriched = orchestrator.apply_skills_before_subagent(
                task_metadata=task_metadata,
                task_context=task_context,
            )

            # Should still return enriched context, just with no skills
            assert isinstance(enriched, EnrichedContext)
            assert len(enriched.skill_invocations) == 0

        def test_enriched_context_to_dict(self, orchestrator, sample_task_metadata, sample_task_context):
            """Test converting enriched context to dictionary."""
            enriched = orchestrator.apply_skills_before_subagent(
                task_metadata=sample_task_metadata,
                task_context=sample_task_context,
            )

            data = enriched.to_dict()

            assert "original_context" in data
            assert "skill_invocations" in data
            assert "skill_guidance" in data
            assert "combined_guidance" in data
            assert "invocation_timestamp" in data

        def test_combined_guidance_format(self, orchestrator, sample_task_metadata, sample_task_context):
            """Test combined guidance string format."""
            enriched = orchestrator.apply_skills_before_subagent(
                task_metadata=sample_task_metadata,
                task_context=sample_task_context,
            )

            # Should contain skill names
            assert "frontend-design" in enriched.combined_guidance

            # Should be formatted with sections
            assert "## Skill:" in enriched.combined_guidance

    class TestInvocationHistory:
        """Test invocation history management."""

        def test_get_all_history(self, orchestrator):
            """Test retrieving all invocation history."""
            orchestrator.invoke_skill("frontend-design", "Task 1")
            orchestrator.invoke_skill("webapp-testing", "Task 2")

            history = orchestrator.get_invocation_history()

            assert len(history) == 2

        def test_filter_history_by_skill(self, orchestrator):
            """Test filtering history by skill name."""
            orchestrator.invoke_skill("frontend-design", "Task 1")
            orchestrator.invoke_skill("frontend-design", "Task 2")
            orchestrator.invoke_skill("webapp-testing", "Task 3")

            frontend_history = orchestrator.get_invocation_history(skill_name="frontend-design")

            assert len(frontend_history) == 2
            assert all(inv.skill_name == "frontend-design" for inv in frontend_history)

        def test_filter_history_by_status(self, orchestrator):
            """Test filtering history by status."""
            invocation = orchestrator.invoke_skill("frontend-design", "Task")
            invocation.status = SkillInvocationStatus.SUCCESS

            success_history = orchestrator.get_invocation_history(status=SkillInvocationStatus.SUCCESS)

            assert len(success_history) == 1

        def test_limit_history_results(self, orchestrator):
            """Test limiting history results."""
            for i in range(10):
                orchestrator.invoke_skill("frontend-design", f"Task {i}")

            limited = orchestrator.get_invocation_history(limit=5)

            assert len(limited) == 5

        def test_clear_history(self, orchestrator):
            """Test clearing invocation history."""
            orchestrator.invoke_skill("frontend-design", "Task")

            orchestrator.clear_invocation_history()
            history = orchestrator.get_invocation_history()

            assert len(history) == 0

    class TestSkillInfo:
        """Test skill information retrieval."""

        def test_get_available_skills(self, orchestrator):
            """Test getting list of available skills."""
            skills = orchestrator.get_available_skills()

            assert isinstance(skills, list)
            assert "frontend-design" in skills
            assert "webapp-testing" in skills
            assert "document-skills" in skills

        def test_get_skill_info_existing(self, orchestrator):
            """Test getting info for existing skill."""
            info = orchestrator.get_skill_info("frontend-design")

            assert info is not None
            assert info.skill_name == "frontend-design"
            assert isinstance(info.triggers, list)
            assert info.prompt_template is not None

        def test_get_skill_info_nonexistent(self, orchestrator):
            """Test getting info for nonexistent skill."""
            info = orchestrator.get_skill_info("nonexistent-skill")

            assert info is None


class TestDataClasses:
    """Test data class serialization and methods."""

    def test_skill_invocation_to_dict(self):
        """Test SkillInvocation serialization."""
        invocation = SkillInvocation(
            skill_name="frontend-design",
            args="Test args",
            status=SkillInvocationStatus.SUCCESS,
            result="Test result",
        )

        data = invocation.to_dict()

        assert data["skill_name"] == "frontend-design"
        assert data["args"] == "Test args"
        assert data["status"] == "success"  # Enum value
        assert data["result"] == "Test result"

    def test_skill_context_to_dict(self):
        """Test SkillContext serialization."""
        context = SkillContext(
            task_description="Test task",
            prd_context="Test PRD",
        )

        data = context.to_dict()

        assert data["task_description"] == "Test task"
        assert data["prd_context"] == "Test PRD"
        # None values should be filtered out
        assert "code_context" not in data

    def test_enriched_context_to_dict(self):
        """Test EnrichedContext serialization."""
        enriched = EnrichedContext(
            original_context={"key": "value"},
            skill_invocations=[],
            skill_guidance={},
            combined_guidance="Test guidance",
        )

        data = enriched.to_dict()

        assert data["original_context"] == {"key": "value"}
        assert data["skill_invocations"] == []
        assert data["combined_guidance"] == "Test guidance"
        assert "invocation_timestamp" in data


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_frontend_task_workflow(self):
        """Test complete frontend task workflow."""
        orchestrator = SkillOrchestrator()

        task_metadata = {
            "description": "Create a responsive navigation bar with dropdown menu",
            "category": "frontend",
        }

        task_context = {
            "prd_context": "E-commerce site navigation",
            "existing_patterns": "Use Tailwind CSS",
        }

        enriched = orchestrator.apply_skills_before_subagent(
            task_metadata=task_metadata,
            task_context=task_context,
        )

        # Should detect frontend-design skill
        assert "frontend-design" in enriched.skill_guidance

        # Should have formatted prompt
        invocation = enriched.skill_invocations[0]
        assert "navigation bar" in invocation.args
        assert "Tailwind CSS" in invocation.args

    def test_testing_task_workflow(self):
        """Test complete testing task workflow."""
        orchestrator = SkillOrchestrator()

        task_metadata = {
            "description": "Generate E2E tests for checkout flow using Playwright",
            "category": "testing",
        }

        task_context = {
            "app_url": "https://staging.example.com",
            "test_scenarios": "Add to cart, checkout, payment",
        }

        enriched = orchestrator.apply_skills_before_subagent(
            task_metadata=task_metadata,
            task_context=task_context,
        )

        # Should detect webapp-testing skill
        assert "webapp-testing" in enriched.skill_guidance

        # Should have formatted prompt with test details
        invocation = enriched.skill_invocations[0]
        assert "checkout flow" in invocation.args
        assert "Playwright" in invocation.args

    def test_documentation_task_workflow(self):
        """Test complete documentation task workflow."""
        orchestrator = SkillOrchestrator()

        task_metadata = {
            "description": "Generate API documentation for user endpoints",
            "category": "documentation",
        }

        task_context = {
            "doc_type": "OpenAPI/Swagger",
            "api_spec": "User CRUD operations",
            "prd_context": "User management API",
        }

        enriched = orchestrator.apply_skills_before_subagent(
            task_metadata=task_metadata,
            task_context=task_context,
        )

        # Should detect document-skills
        assert "document-skills" in enriched.skill_guidance

        # Should include document type and API spec
        invocation = enriched.skill_invocations[0]
        assert "OpenAPI/Swagger" in invocation.args
        assert "User CRUD" in invocation.args

    def test_mcp_builder_workflow(self):
        """Test MCP server builder workflow."""
        orchestrator = SkillOrchestrator()

        task_metadata = {
            "description": "Create an MCP server for GitHub API integration",
        }

        task_context = {
            "external_api": "GitHub REST API v3",
            "auth_method": "Personal Access Token",
        }

        enriched = orchestrator.apply_skills_before_subagent(
            task_metadata=task_metadata,
            task_context=task_context,
        )

        # Should detect mcp-builder skill
        assert "mcp-builder" in enriched.skill_guidance

        invocation = enriched.skill_invocations[0]
        assert "GitHub API" in invocation.args
        assert "Personal Access Token" in invocation.args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
