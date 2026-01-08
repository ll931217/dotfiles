#!/usr/bin/env python3
"""
Test for autonomous planning phase implementation.

Validates that:
1. Planning phase invokes /flow:plan skill
2. Human interaction is enabled exactly once
3. Session state transitions correctly
4. Decision is logged with proper context
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
scripts_dir = maestro_root / "scripts"
decision_engine_dir = maestro_root / "decision-engine" / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(decision_engine_dir))

from orchestrator import MaestroOrchestrator


def test_phase_planning_invokes_flow_plan_skill():
    """Test that planning phase invokes /flow:plan skill with correct parameters."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)
    orchestrator.session_id = "test-session-1234"

    # Mock the skill orchestrator
    mock_skill_invocation = Mock()
    mock_skill_invocation.skill_name = "flow:plan"
    orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)

    # Mock the decision logger
    orchestrator.decision_logger.log_decision = Mock(return_value="decision-001")

    # Mock session manager
    orchestrator.session_manager.transition_state = Mock()

    # Execute
    feature_request = "Implement user authentication with OAuth"
    prd_path = orchestrator._phase_planning(feature_request)

    # Verify skill invocation
    orchestrator.skill_orchestrator.invoke_skill.assert_called_once()
    call_args = orchestrator.skill_orchestrator.invoke_skill.call_args

    # Check skill_name
    assert call_args[1]["skill_name"] == "flow:plan", \
        f"Expected skill_name 'flow:plan', got '{call_args[1]['skill_name']}'"

    # Check context contains required fields
    context = call_args[1]["context"]
    assert "feature_request" in context, "Context missing 'feature_request'"
    assert "autonomous_mode" in context, "Context missing 'autonomous_mode'"
    assert "session_id" in context, "Context missing 'session_id'"
    assert "enable_human_interaction" in context, "Context missing 'enable_human_interaction'"

    # Verify human interaction is enabled
    assert context["enable_human_interaction"] is True, \
        "Human interaction should be enabled during planning"

    # Verify autonomous mode is set
    assert context["autonomous_mode"] is True, \
        "Autonomous mode should be True"

    # Verify session state transition
    orchestrator.session_manager.transition_state.assert_called_once()
    transition_call = orchestrator.session_manager.transition_state.call_args
    assert transition_call[1]["new_state"].value == "planning", \
        "Session state should transition to PLANNING"

    # Verify decision logging
    orchestrator.decision_logger.log_decision.assert_called_once()
    decision_call = orchestrator.decision_logger.log_decision.call_args
    assert decision_call[1]["decision_type"] == "planning", \
        "Decision type should be 'planning'"
    assert "one-time human input" in decision_call[1]["decision"]["rationale"], \
        "Decision rationale should mention one-time human input"

    # Verify PRD path is returned
    assert prd_path is not None, "PRD path should be returned"
    assert str(prd_path).endswith(".md"), "PRD path should end with .md"

    print("✓ All assertions passed!")
    print(f"  - /flow:plan skill invoked correctly")
    print(f"  - Human interaction enabled: {context['enable_human_interaction']}")
    print(f"  - Autonomous mode: {context['autonomous_mode']}")
    print(f"  - Session state transitioned to PLANNING")
    print(f"  - Decision logged with ID: decision-001")
    print(f"  - PRD path: {prd_path}")


def test_flow_plan_skill_mapping_exists():
    """Test that flow:plan skill is registered in skill orchestrator."""

    from skill_orchestrator import SkillOrchestrator

    # Create skill orchestrator
    skill_orchestrator = SkillOrchestrator()

    # Check if flow:plan is in available skills
    available_skills = skill_orchestrator.get_available_skills()
    assert "flow:plan" in available_skills, \
        f"flow:plan skill not found in available skills: {available_skills}"

    # Get skill info
    skill_info = skill_orchestrator.get_skill_info("flow:plan")
    assert skill_info is not None, "flow:plan skill info should not be None"

    # Verify skill has correct properties
    assert skill_info.skill_name == "flow:plan", "Skill name should be 'flow:plan'"
    assert skill_info.description is not None, "Skill should have a description"
    assert "PRD" in skill_info.description or "planning" in skill_info.description.lower(), \
        "Skill description should mention PRD or planning"

    print("✓ flow:plan skill mapping verified!")
    print(f"  - Skill name: {skill_info.skill_name}")
    print(f"  - Description: {skill_info.description}")


if __name__ == "__main__":
    print("Testing autonomous planning phase implementation...\n")

    try:
        test_flow_plan_skill_mapping_exists()
        print()
        test_phase_planning_invokes_flow_plan_skill()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
