#!/usr/bin/env python3
"""
Example: Using the Subagent Factory

This example demonstrates how to use the SubagentFactory for intelligent
task-to-subagent mapping in the Maestro orchestration system.
"""

import logging
from pathlib import Path
from subagent_factory import SubagentFactory

# Configure logging to see detection details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_basic_detection():
    """Example 1: Basic subagent type detection."""
    print("\n" + "="*70)
    print("Example 1: Basic Subagent Detection")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Different task types
    tasks = [
        "Create React component for user profile",
        "Implement REST API endpoint for authentication",
        "Add JWT authentication with OAuth2",
        "Write unit tests for payment processing",
        "Optimize database query performance",
        "Create API documentation with OpenAPI specs"
    ]

    for task in tasks:
        subagent_type = factory.detect_subagent_type(task)
        print(f"Task: {task}")
        print(f"→ Subagent: {subagent_type}\n")


def example_detailed_detection():
    """Example 2: Detailed detection with metadata."""
    print("\n" + "="*70)
    print("Example 2: Detailed Detection with Metadata")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Task with file context
    task_description = "Create responsive UI component for user dashboard"
    task_metadata = {
        "files": [
            "src/components/Dashboard.tsx",
            "src/components/UserProfile.tsx",
            "src/services/api.ts"
        ],
        "dependencies": ["react", "typescript", "tailwindcss"]
    }

    result = factory.detect_subagent_detailed(task_description, task_metadata)

    print(f"Task: {task_description}")
    print(f"Files: {', '.join(Path(f).name for f in task_metadata['files'])}")
    print(f"\nDetection Result:")
    print(f"  Subagent Type: {result.subagent_type}")
    print(f"  Category: {result.category}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Skill: {result.skill}")
    print(f"  Matched Patterns: {', '.join(result.matched_patterns)}")
    print(f"  Fallback Agents: {', '.join(result.fallback_agents) or 'None'}")


def example_agent_config():
    """Example 3: Creating agent configuration."""
    print("\n" + "="*70)
    print("Example 3: Creating Agent Configuration")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Frontend task
    task_description = "Create responsive UI component for data visualization"
    task_context = {
        "description": task_description,
        "prd": """
        Build a data visualization dashboard that displays:
        - User analytics charts
        - Real-time metrics
        - Export functionality
        """,
        "code_patterns": "Component-based architecture with React",
        "confidence": 0.85,
        "matched_patterns": ["component", "ui|interface"]
    }

    # Detect subagent
    subagent_type = factory.detect_subagent_type(task_description)

    # Create agent configuration
    agent_config = factory.create_agent_config(subagent_type, task_context)

    print(f"Task: {task_description}\n")
    print("Agent Configuration:")
    print(f"  Subagent Type: {agent_config.subagent_type}")
    print(f"  System Prompt: {agent_config.system_prompt[:100]}...")
    print(f"\n  Skill Config:")
    if agent_config.skill_config:
        print(f"    Name: {agent_config.skill_config['name']}")
        print(f"    Prompt: {agent_config.skill_config['prompt'][:100]}...")
    else:
        print("    None")
    print(f"\n  Fallback Chain: {', '.join(agent_config.fallback_chain)}")
    print(f"\n  Detection Metadata:")
    print(f"    Category: {agent_config.detection_metadata.get('category')}")
    print(f"    Confidence: {agent_config.detection_metadata.get('confidence'):.2f}")


def example_fallback_handling():
    """Example 4: Fallback agent handling."""
    print("\n" + "="*70)
    print("Example 4: Fallback Agent Handling")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Get fallback chain for a subagent
    subagent_type = "frontend-developer"
    fallback_agents = factory.get_fallback_agents(subagent_type)

    print(f"Primary Subagent: {subagent_type}")
    print(f"Fallback Chain: {', '.join(fallback_agents)}\n")

    # Simulate primary agent failure
    available_agents = [
        "react-pro",
        "javascript-pro",
        "typescript-pro",
        "backend-architect"
    ]
    attempted_agents = [subagent_type]

    print(f"Available Agents: {', '.join(available_agents)}")
    print(f"Attempted Agents: {', '.join(attempted_agents)}\n")

    # Select first fallback
    fallback = factory.fallback_handler.select_fallback(
        failed_agent=subagent_type,
        category="frontend",
        attempted_agents=attempted_agents,
        available_agents=available_agents
    )

    if fallback:
        print(f"Selected Fallback: {fallback}")
        attempted_agents.append(fallback)

        # Simulate fallback also failing, select next
        next_fallback = factory.fallback_handler.select_fallback(
            failed_agent=fallback,
            category="frontend",
            attempted_agents=attempted_agents,
            available_agents=available_agents
        )

        if next_fallback:
            print(f"Next Fallback: {next_fallback}")
        else:
            print("No more fallback agents available")
    else:
        print("No fallback agents available")


def example_skill_detection():
    """Example 5: Skill trigger detection."""
    print("\n" + "="*70)
    print("Example 5: Skill Detection")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Tasks that trigger skills
    skill_tasks = [
        ("Create responsive UI component", "frontend-design"),
        ("Test web application with Playwright", "webapp-testing"),
        ("Generate PDF report from data", "document-skills"),
        ("Build MCP server for GitHub API", "mcp-builder"),
        ("Create new agent skill for testing", "skill-creator"),
        ("Write some documentation", None)  # No skill
    ]

    for task, expected_skill in skill_tasks:
        detected_skill = factory.detect_skill(task)
        status = "✓" if detected_skill == expected_skill else "✗"

        print(f"{status} Task: {task}")
        print(f"  Expected Skill: {expected_skill or 'None'}")
        print(f"  Detected Skill: {detected_skill or 'None'}")
        print()


def example_priority_ordering():
    """Example 6: Priority-based category selection."""
    print("\n" + "="*70)
    print("Example 6: Priority-Based Category Selection")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Task that could match multiple categories
    # Security has higher priority than frontend
    task = "Implement secure authentication UI for React app"

    result = factory.detect_subagent_detailed(task)

    print(f"Task: {task}\n")
    print("Why Security Category?")
    print("  - Contains 'authentication' and 'secure' keywords")
    print("  - Security category has higher priority than frontend")
    print("  - Even though 'React app' suggests frontend")
    print(f"\nSelected Category: {result.category}")
    print(f"Selected Subagent: {result.subagent_type}")
    print(f"Confidence: {result.confidence:.2f}")


def example_integration_workflow():
    """Example 7: Complete integration workflow."""
    print("\n" + "="*70)
    print("Example 7: Complete Integration Workflow")
    print("="*70 + "\n")

    factory = SubagentFactory()

    # Simulate task from PRD
    prd_task = {
        "id": "task-123",
        "description": "Implement user authentication with JWT tokens",
        "files": ["auth_service.py", "user_model.py", "config.py"],
        "dependencies": ["fastapi", "jwt", "sqlalchemy"],
        "prd_section": "User Authentication System"
    }

    print(f"Task: {prd_task['description']}")
    print(f"Files: {', '.join(Path(f).name for f in prd_task['files'])}\n")

    # Step 1: Detect subagent
    print("Step 1: Detect Subagent")
    result = factory.detect_subagent_detailed(
        prd_task['description'],
        prd_task
    )
    print(f"  → Subagent: {result.subagent_type}")
    print(f"  → Category: {result.category}")
    print(f"  → Confidence: {result.confidence:.2f}\n")

    # Step 2: Check for skills
    print("Step 2: Check for Skills")
    skill = factory.detect_skill(prd_task['description'])
    print(f"  → Skill Triggered: {skill or 'None'}\n")

    # Step 3: Create agent configuration
    print("Step 3: Create Agent Configuration")
    agent_config = factory.create_agent_config(
        result.subagent_type,
        {
            "description": prd_task['description'],
            "prd": "Implement secure user authentication",
            "files": prd_task['files']
        }
    )
    print(f"  → System Prompt: Created")
    print(f"  → Skill Config: {'Included' if agent_config.skill_config else 'None'}")
    print(f"  → Fallback Chain: {len(agent_config.fallback_chain)} agents\n")

    # Step 4: Prepare for execution
    print("Step 4: Ready for Execution")
    print("  Configuration can now be passed to Task tool:")
    print(f"    subagent_type: {agent_config.subagent_type}")
    print(f"    system_prompt: {len(agent_config.system_prompt)} chars")
    print(f"    context: {len(agent_config.context)} items")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Subagent Factory Usage Examples")
    print("="*70)

    example_basic_detection()
    example_detailed_detection()
    example_agent_config()
    example_fallback_handling()
    example_skill_detection()
    example_priority_ordering()
    example_integration_workflow()

    print("\n" + "="*70)
    print("Examples Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
