#!/usr/bin/env python3
"""
Test for autonomous task generation phase implementation.

Validates that:
1. Task generation phase invokes /flow:generate-tasks skill
2. Human interaction is disabled (autonomous mode)
3. Session state transitions correctly (GENERATING_TASKS -> IMPLEMENTING)
4. Decision is logged with proper context
5. Task ordering engine is used for parallel execution optimization
6. Tasks are returned with proper structure
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

# Add maestro scripts to path
maestro_root = Path(__file__).parent.parent
scripts_dir = maestro_root / "scripts"
decision_engine_dir = maestro_root / "decision-engine" / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(decision_engine_dir))

from orchestrator import MaestroOrchestrator


def test_phase_task_generation_invokes_flow_generate_tasks_skill():
    """Test that task generation phase invokes /flow:generate-tasks skill with correct parameters."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)
    orchestrator.session_id = "test-session-1234"

    # Mock the skill orchestrator
    mock_skill_invocation = Mock()
    mock_skill_invocation.skill_name = "flow:generate-tasks"
    orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)

    # Mock the decision logger
    orchestrator.decision_logger.log_decision = Mock(side_effect=["decision-001", "decision-002"])

    # Mock session manager
    orchestrator.session_manager.transition_state = Mock()

    # Mock task ordering engine
    mock_ordering_engine = Mock()
    mock_ordering_engine.compute_ordering.return_value = {
        "total_groups": 3,
        "parallel_groups": [["task1", "task2"], ["task3"], ["task4", "task5", "task6"]],
        "total_tasks": 6,
    }
    mock_ordering_engine.graph = {"edges": []}

    with patch.object(orchestrator, 'skill_orchestrator'):
        orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)

    # Patch TaskOrderingEngine
    with patch('orchestrator.TaskOrderingEngine') as MockTaskOrderingEngine:
        MockTaskOrderingEngine.return_value = mock_ordering_engine
        mock_ordering_engine.load_from_beads = Mock()

        # Execute
        prd_path = Path("/tmp/test_project/.flow/prd-test-session.md")
        tasks = orchestrator._phase_task_generation(prd_path)

    # Verify skill invocation
    assert orchestrator.skill_orchestrator.invoke_skill.called, \
        "Skill orchestrator invoke_skill should be called"
    call_args = orchestrator.skill_orchestrator.invoke_skill.call_args

    # Check skill_name
    assert call_args[1]["skill_name"] == "flow:generate-tasks", \
        f"Expected skill_name 'flow:generate-tasks', got '{call_args[1]['skill_name']}'"

    # Check context contains required fields
    context = call_args[1]["context"]
    assert "prd_path" in context, "Context missing 'prd_path'"
    assert "autonomous_mode" in context, "Context missing 'autonomous_mode'"
    assert "session_id" in context, "Context missing 'session_id'"
    assert "enable_human_interaction" in context, "Context missing 'enable_human_interaction'"

    # Verify human interaction is DISABLED (autonomous mode)
    assert context["enable_human_interaction"] is False, \
        "Human interaction should be disabled during task generation"

    # Verify autonomous mode is set
    assert context["autonomous_mode"] is True, \
        "Autonomous mode should be True"

    # Verify PRD path is passed
    assert context["prd_path"] == str(prd_path), \
        f"PRD path should be {prd_path}, got {context['prd_path']}"

    print("✓ All assertions passed for skill invocation!")
    print(f"  - /flow:generate-tasks skill invoked correctly")
    print(f"  - Human interaction disabled: {context['enable_human_interaction']}")
    print(f"  - Autonomous mode: {context['autonomous_mode']}")
    print(f"  - PRD path: {context['prd_path']}")


def test_task_generation_session_state_transitions():
    """Test that session state transitions correctly during task generation."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)
    orchestrator.session_id = "test-session-5678"

    # Mock dependencies
    mock_skill_invocation = Mock()
    mock_skill_invocation.skill_name = "flow:generate-tasks"
    orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)
    orchestrator.decision_logger.log_decision = Mock(side_effect=["decision-001", "decision-002"])

    # Track state transitions
    transition_states = []
    def track_transition(*args, **kwargs):
        transition_states.append(kwargs.get("new_state"))

    orchestrator.session_manager.transition_state = Mock(side_effect=track_transition)

    # Mock task ordering engine
    mock_ordering_engine = Mock()
    mock_ordering_engine.compute_ordering.return_value = {
        "total_groups": 2,
        "parallel_groups": [["task1"], ["task2"]],
        "total_tasks": 2,
    }
    mock_ordering_engine.graph = {"edges": []}

    with patch('orchestrator.TaskOrderingEngine') as MockTaskOrderingEngine:
        MockTaskOrderingEngine.return_value = mock_ordering_engine
        mock_ordering_engine.load_from_beads = Mock()

        # Execute
        prd_path = Path("/tmp/test_project/.flow/prd-test.md")
        tasks = orchestrator._phase_task_generation(prd_path)

    # Verify state transitions
    assert len(transition_states) == 2, \
        f"Expected 2 state transitions, got {len(transition_states)}"

    # First transition: GENERATING_TASKS
    assert transition_states[0].value == "generating_tasks", \
        f"First transition should be to GENERATING_TASKS, got {transition_states[0].value}"

    # Second transition: IMPLEMENTING
    assert transition_states[1].value == "implementing", \
        f"Second transition should be to IMPLEMENTING, got {transition_states[1].value}"

    print("✓ Session state transitions verified!")
    print(f"  - Transition 1: {transition_states[0].value}")
    print(f"  - Transition 2: {transition_states[1].value}")


def test_task_generation_decision_logging():
    """Test that decisions are logged with proper context."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)
    orchestrator.session_id = "test-session-decision"

    # Mock dependencies
    mock_skill_invocation = Mock()
    mock_skill_invocation.skill_name = "flow:generate-tasks"
    orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)

    # Track decision logging calls
    decision_calls = []
    def track_decision(*args, **kwargs):
        decision_calls.append(kwargs)
        return f"decision-{len(decision_calls):03d}"

    orchestrator.decision_logger.log_decision = Mock(side_effect=track_decision)
    orchestrator.session_manager.transition_state = Mock()

    # Mock task ordering engine
    mock_ordering_engine = Mock()
    mock_ordering_engine.compute_ordering.return_value = {
        "total_groups": 2,
        "parallel_groups": [["task1", "task2"], ["task3"]],
        "total_tasks": 3,
    }
    mock_ordering_engine.graph = {"edges": [{"dep": "task1", "task": "task2"}]}

    with patch('orchestrator.TaskOrderingEngine') as MockTaskOrderingEngine:
        MockTaskOrderingEngine.return_value = mock_ordering_engine
        mock_ordering_engine.load_from_beads = Mock()

        # Execute
        prd_path = Path("/tmp/test_project/.flow/prd-test.md")
        tasks = orchestrator._phase_task_generation(prd_path)

    # Verify decision logging
    assert len(decision_calls) == 2, \
        f"Expected 2 decisions to be logged, got {len(decision_calls)}"

    # First decision: task_generation
    task_gen_decision = decision_calls[0]
    assert task_gen_decision["decision_type"] == "task_generation", \
        f"First decision type should be 'task_generation', got {task_gen_decision['decision_type']}"

    assert "autonomous" in task_gen_decision["decision"]["rationale"].lower(), \
        "Task generation decision rationale should mention autonomous mode"

    assert task_gen_decision["decision"]["context"]["autonomous_mode"] is True, \
        "Task generation decision context should have autonomous_mode=True"

    assert task_gen_decision["decision"]["context"]["human_interaction"] is False, \
        "Task generation decision context should have human_interaction=False"

    # Second decision: task_ordering
    task_ordering_decision = decision_calls[1]
    assert task_ordering_decision["decision_type"] == "task_ordering", \
        f"Second decision type should be 'task_ordering', got {task_ordering_decision['decision_type']}"

    assert "parallel" in task_ordering_decision["decision"]["rationale"].lower(), \
        "Task ordering decision rationale should mention parallel execution"

    assert "total_groups" in task_ordering_decision["decision"]["context"], \
        "Task ordering decision context should include total_groups"

    assert task_ordering_decision["decision"]["context"]["total_groups"] == 2, \
        "Task ordering decision context should have total_groups=2"

    print("✓ Decision logging verified!")
    print(f"  - Decision 1: {task_gen_decision['decision_type']}")
    print(f"  - Decision 2: {task_ordering_decision['decision_type']}")
    print(f"  - Total groups: {task_ordering_decision['decision']['context']['total_groups']}")


def test_task_generation_returns_ordered_tasks():
    """Test that task generation returns properly ordered task list."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)
    orchestrator.session_id = "test-session-ordered"

    # Mock dependencies
    mock_skill_invocation = Mock()
    mock_skill_invocation.skill_name = "flow:generate-tasks"
    orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)
    orchestrator.decision_logger.log_decision = Mock(side_effect=["decision-001", "decision-002"])
    orchestrator.session_manager.transition_state = Mock()

    # Mock task ordering engine with parallel groups
    mock_ordering_engine = Mock()
    mock_ordering_engine.compute_ordering.return_value = {
        "total_groups": 3,
        "parallel_groups": [
            ["task-1", "task-2"],  # Group 0: can run in parallel
            ["task-3"],            # Group 1: single task
            ["task-4", "task-5", "task-6"],  # Group 2: can run in parallel
        ],
        "total_tasks": 6,
    }
    mock_ordering_engine.graph = {"edges": []}

    with patch('orchestrator.TaskOrderingEngine') as MockTaskOrderingEngine:
        MockTaskOrderingEngine.return_value = mock_ordering_engine
        mock_ordering_engine.load_from_beads = Mock()

        # Execute
        prd_path = Path("/tmp/test_project/.flow/prd-test.md")
        tasks = orchestrator._phase_task_generation(prd_path)

    # Verify task structure
    assert isinstance(tasks, list), \
        f"Tasks should be a list, got {type(tasks)}"

    assert len(tasks) == 6, \
        f"Expected 6 tasks, got {len(tasks)}"

    # Verify task structure
    for task in tasks:
        assert "id" in task, "Task should have 'id' field"
        assert "group" in task, "Task should have 'group' field"
        assert "can_run_in_parallel" in task, "Task should have 'can_run_in_parallel' field"

    # Verify parallel groups
    group_0_tasks = [t for t in tasks if t["group"] == 0]
    group_1_tasks = [t for t in tasks if t["group"] == 1]
    group_2_tasks = [t for t in tasks if t["group"] == 2]

    assert len(group_0_tasks) == 2, \
        f"Group 0 should have 2 tasks, got {len(group_0_tasks)}"
    assert all(t["can_run_in_parallel"] for t in group_0_tasks), \
        "All tasks in group 0 should have can_run_in_parallel=True"

    assert len(group_1_tasks) == 1, \
        f"Group 1 should have 1 task, got {len(group_1_tasks)}"

    assert len(group_2_tasks) == 3, \
        f"Group 2 should have 3 tasks, got {len(group_2_tasks)}"
    assert all(t["can_run_in_parallel"] for t in group_2_tasks), \
        "All tasks in group 2 should have can_run_in_parallel=True"

    print("✓ Task ordering verified!")
    print(f"  - Total tasks: {len(tasks)}")
    print(f"  - Group 0: {len(group_0_tasks)} tasks (parallel)")
    print(f"  - Group 1: {len(group_1_tasks)} task")
    print(f"  - Group 2: {len(group_2_tasks)} tasks (parallel)")


def test_flow_generate_tasks_skill_mapping_exists():
    """Test that flow:generate-tasks skill is registered in skill orchestrator."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)

    # Check if skill is registered
    available_skills = orchestrator.skill_orchestrator.get_available_skills()

    assert "flow:generate-tasks" in available_skills, \
        f"flow:generate-tasks skill should be registered. Available skills: {available_skills}"

    # Get skill info
    skill_info = orchestrator.skill_orchestrator.get_skill_info("flow:generate-tasks")

    assert skill_info is not None, \
        "Skill info should not be None"

    assert skill_info.skill_name == "flow:generate-tasks", \
        f"Skill name should be 'flow:generate-tasks', got {skill_info.skill_name}"

    assert skill_info.description is not None, \
        "Skill should have a description"

    print("✓ Skill mapping verified!")
    print(f"  - Skill name: {skill_info.skill_name}")
    print(f"  - Description: {skill_info.description}")


def test_autonomous_mode_no_human_interaction():
    """Test that task generation runs in autonomous mode without human interaction."""

    # Setup
    project_root = Path("/tmp/test_project")
    orchestrator = MaestroOrchestrator(project_root)
    orchestrator.session_id = "test-session-autonomous"

    # Mock dependencies
    mock_skill_invocation = Mock()
    mock_skill_invocation.skill_name = "flow:generate-tasks"
    orchestrator.skill_orchestrator.invoke_skill = Mock(return_value=mock_skill_invocation)
    orchestrator.decision_logger.log_decision = Mock(side_effect=["decision-001", "decision-002"])
    orchestrator.session_manager.transition_state = Mock()

    # Mock task ordering engine
    mock_ordering_engine = Mock()
    mock_ordering_engine.compute_ordering.return_value = {
        "total_groups": 1,
        "parallel_groups": [["task1"]],
        "total_tasks": 1,
    }
    mock_ordering_engine.graph = {"edges": []}

    with patch('orchestrator.TaskOrderingEngine') as MockTaskOrderingEngine:
        MockTaskOrderingEngine.return_value = mock_ordering_engine
        mock_ordering_engine.load_from_beads = Mock()

        # Execute
        prd_path = Path("/tmp/test_project/.flow/prd-test.md")
        tasks = orchestrator._phase_task_generation(prd_path)

    # Verify skill invocation context
    call_args = orchestrator.skill_orchestrator.invoke_skill.call_args
    context = call_args[1]["context"]

    # Verify autonomous mode
    assert context["autonomous_mode"] is True, \
        "autonomous_mode should be True in task generation"

    # Verify no human interaction
    assert context["enable_human_interaction"] is False, \
        "enable_human_interaction should be False in task generation"

    # Verify decision context
    decision_calls = orchestrator.decision_logger.log_decision.call_args_list
    task_gen_context = decision_calls[0][1]["decision"]["context"]

    assert task_gen_context["autonomous_mode"] is True, \
        "Decision context should have autonomous_mode=True"

    assert task_gen_context["human_interaction"] is False, \
        "Decision context should have human_interaction=False"

    print("✓ Autonomous mode verified!")
    print(f"  - autonomous_mode: {context['autonomous_mode']}")
    print(f"  - enable_human_interaction: {context['enable_human_interaction']}")
    print(f"  - No human input required")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing Task Generation Phase Implementation")
    print("=" * 70)
    print()

    tests = [
        test_phase_task_generation_invokes_flow_generate_tasks_skill,
        test_task_generation_session_state_transitions,
        test_task_generation_decision_logging,
        test_task_generation_returns_ordered_tasks,
        test_flow_generate_tasks_skill_mapping_exists,
        test_autonomous_mode_no_human_interaction,
    ]

    for test in tests:
        print(f"Running: {test.__name__}")
        print("-" * 70)
        try:
            test()
            print()
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            print()
            return 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()
            return 1

    print("=" * 70)
    print("All tests passed! ✓")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
