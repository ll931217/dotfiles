#!/usr/bin/env python3
"""
Example usage of the Skill Orchestrator.

Demonstrates how to use the skill orchestrator in typical workflows.
"""

from skill_orchestrator import (
    SkillOrchestrator,
    SkillContext,
    SkillInvocationStatus,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def example_basic_detection():
    """Example: Basic skill detection from task description."""
    print_section("Example 1: Basic Skill Detection")

    orchestrator = SkillOrchestrator()

    task_description = "Create UI component for responsive navigation bar"

    skills = orchestrator.detect_applicable_skills(
        task_description=task_description,
    )

    print(f"Task: {task_description}")
    print(f"Detected skills: {skills}")


def example_detection_with_category():
    """Example: Skill detection with task category."""
    print_section("Example 2: Detection with Task Category")

    orchestrator = SkillOrchestrator()

    skills = orchestrator.detect_applicable_skills(
        task_description="Build login component",
        task_category="frontend",
    )

    print("Task: Build login component")
    print(f"Category: frontend")
    print(f"Detected skills: {skills}")


def example_detection_from_metadata():
    """Example: Skill detection from task metadata."""
    print_section("Example 3: Detection from Task Metadata")

    orchestrator = SkillOrchestrator()

    task_metadata = {
        "description": "Implement user authentication",
        "category": "backend",
        "applicable_skills": ["frontend-design", "webapp-testing"],
    }

    skills = orchestrator.detect_applicable_skills(
        task_description=task_metadata["description"],
        task_category=task_metadata.get("category"),
        task_metadata=task_metadata,
    )

    print("Task metadata:")
    for key, value in task_metadata.items():
        print(f"  {key}: {value}")
    print(f"Detected skills: {skills}")


def example_skill_invocation():
    """Example: Invoking a skill with context."""
    print_section("Example 4: Skill Invocation")

    orchestrator = SkillOrchestrator()

    # Create skill context
    context = SkillContext(
        task_description="Create a dashboard with data visualization",
        prd_context="Analytics dashboard for sales data",
        existing_patterns="Use chart library and dark theme",
    )

    # Invoke the skill
    invocation = orchestrator.invoke_skill(
        skill_name="frontend-design",
        context=context,
    )

    print(f"Skill: {invocation.skill_name}")
    print(f"Status: {invocation.status.value}")
    print(f"\nGenerated prompt:")
    print("-" * 60)
    print(invocation.args[:300] + "...")


def example_full_orchestration():
    """Example: Full skill orchestration workflow."""
    print_section("Example 5: Full Orchestration Workflow")

    orchestrator = SkillOrchestrator()

    # Prepare task metadata and context
    task_metadata = {
        "description": "Design component for shopping cart with add/remove items",
        "category": "frontend",
        "priority": "high",
    }

    task_context = {
        "prd_context": "E-commerce shopping cart",
        "code_context": "Existing cart state management in useCart.ts",
        "existing_patterns": "Use shadcn/ui for components",
    }

    # Apply skills before subagent
    enriched = orchestrator.apply_skills_before_subagent(
        task_metadata=task_metadata,
        task_context=task_context,
    )

    print("Original context:")
    for key, value in task_context.items():
        print(f"  {key}: {value}")

    print(f"\nSkills applied: {len(enriched.skill_invocations)}")
    for invocation in enriched.skill_invocations:
        print(f"  - {invocation.skill_name}: {invocation.status.value}")

    print(f"\nSkill guidance summary:")
    for skill_name, guidance in enriched.skill_guidance.items():
        print(f"  [{skill_name}]")
        print(f"  {guidance[:100]}...")


def example_testing_workflow():
    """Example: Testing task with skill orchestration."""
    print_section("Example 6: Testing Task Workflow")

    orchestrator = SkillOrchestrator()

    task_metadata = {
        "description": "Generate E2E tests for checkout flow",
        "category": "testing",
    }

    task_context = {
        "app_url": "https://staging.example.com",
        "test_scenarios": "Add to cart, proceed to checkout, complete payment",
        "prd_context": "E-commerce checkout process",
    }

    enriched = orchestrator.apply_skills_before_subagent(
        task_metadata=task_metadata,
        task_context=task_context,
    )

    print(f"Task: {task_metadata['description']}")
    print(f"Skills invoked: {[inv.skill_name for inv in enriched.skill_invocations]}")

    if enriched.skill_invocations:
        invocation = enriched.skill_invocations[0]
        print(f"\nSkill prompt preview:")
        print(invocation.args[:200] + "...")


def example_documentation_workflow():
    """Example: Documentation task with skill orchestration."""
    print_section("Example 7: Documentation Task Workflow")

    orchestrator = SkillOrchestrator()

    task_metadata = {
        "description": "Generate API documentation for user management endpoints",
        "category": "documentation",
    }

    task_context = {
        "doc_type": "OpenAPI/Swagger",
        "api_spec": "User CRUD operations (GET, POST, PUT, DELETE)",
        "prd_context": "User management service",
        "code_context": "src/api/users.ts",
    }

    enriched = orchestrator.apply_skills_before_subagent(
        task_metadata=task_metadata,
        task_context=task_context,
    )

    print(f"Task: {task_metadata['description']}")
    print(f"Document type: {task_context['doc_type']}")

    if enriched.skill_invocations:
        invocation = enriched.skill_invocations[0]
        print(f"\nSkill: {invocation.skill_name}")
        print(f"Prompt includes document type: {task_context['doc_type'] in invocation.args}")


def example_mcp_builder_workflow():
    """Example: MCP server builder workflow."""
    print_section("Example 8: MCP Server Builder Workflow")

    orchestrator = SkillOrchestrator()

    task_metadata = {
        "description": "Create an MCP server for Slack integration",
    }

    task_context = {
        "external_api": "Slack Web API",
        "auth_method": "OAuth 2.0 bot token",
        "prd_context": "Enable Claude to send messages to Slack channels",
    }

    enriched = orchestrator.apply_skills_before_subagent(
        task_metadata=task_metadata,
        task_context=task_context,
    )

    print(f"Task: {task_metadata['description']}")
    print(f"External API: {task_context['external_api']}")

    if enriched.skill_invocations:
        invocation = enriched.skill_invocations[0]
        print(f"\nSkill: {invocation.skill_name}")
        print(f"Framework guidance in prompt: {'FastMCP' in invocation.args or 'MCP SDK' in invocation.args}")


def example_invocation_history():
    """Example: Querying invocation history."""
    print_section("Example 9: Invocation History")

    orchestrator = SkillOrchestrator()

    # Perform multiple invocations
    tasks = [
        ("Create UI component", "frontend-design"),
        ("Generate tests", "webapp-testing"),
        ("Create UI component 2", "frontend-design"),
    ]

    for task_desc, skill_name in tasks:
        orchestrator.invoke_skill(skill_name, task_desc)

    # Query all history
    all_history = orchestrator.get_invocation_history()
    print(f"Total invocations: {len(all_history)}")

    # Filter by skill
    frontend_history = orchestrator.get_invocation_history(skill_name="frontend-design")
    print(f"Frontend skill invocations: {len(frontend_history)}")

    # Filter with limit
    recent = orchestrator.get_invocation_history(limit=2)
    print(f"Recent invocations: {len(recent)}")


def example_available_skills():
    """Example: Listing available skills."""
    print_section("Example 10: Available Skills")

    orchestrator = SkillOrchestrator()

    skills = orchestrator.get_available_skills()

    print(f"Total available skills: {len(skills)}")
    print("\nSkills:")
    for skill_name in skills:
        skill_info = orchestrator.get_skill_info(skill_name)
        description = skill_info.description if skill_info else "No description"
        trigger_count = len(skill_info.triggers) if skill_info else 0
        print(f"  - {skill_name}")
        print(f"    Description: {description}")
        print(f"    Triggers: {trigger_count}")


def example_combined_guidance():
    """Example: Combined guidance from multiple skills."""
    print_section("Example 11: Combined Skill Guidance")

    orchestrator = SkillOrchestrator()

    task_metadata = {
        "description": "Create UI and tests for user profile",
        "applicable_skills": ["frontend-design", "webapp-testing"],
    }

    task_context = {
        "prd_context": "User profile management",
        "app_url": "https://dev.example.com",
    }

    enriched = orchestrator.apply_skills_before_subagent(
        task_metadata=task_metadata,
        task_context=task_context,
    )

    print("Combined skill guidance:")
    print("-" * 60)
    print(enriched.combined_guidance)


def main():
    """Run all examples."""
    examples = [
        example_basic_detection,
        example_detection_with_category,
        example_detection_from_metadata,
        example_skill_invocation,
        example_full_orchestration,
        example_testing_workflow,
        example_documentation_workflow,
        example_mcp_builder_workflow,
        example_invocation_history,
        example_available_skills,
        example_combined_guidance,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")

    print("\n" + "="*60)
    print(" All examples completed ")
    print("="*60)


if __name__ == "__main__":
    main()
