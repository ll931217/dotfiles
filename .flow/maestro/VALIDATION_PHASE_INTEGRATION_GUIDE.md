# Validation Phase Integration Guide

## Quick Integration Steps

To integrate the validation phase implementation into the Maestro Orchestrator, follow these steps:

### Step 1: Add Import and Initialization

In `orchestrator.py`, add the validation implementation import:

```python
# Near the top of the file, after existing imports
from orchestrator_validation_implementation import ValidationPhaseImplementation
```

In the `__init__` method, after logging setup:

```python
# After self._setup_logging()
# Initialize validation phase implementation
self.validation_impl = ValidationPhaseImplementation(
    logger=self.logger,
    project_root=self.project_root,
    session_id=self.session_id,
)
```

### Step 2: Replace Stub Methods

Replace the existing stub methods in the orchestrator with calls to the validation implementation:

```python
def _detect_test_framework(self) -> Optional[str]:
    """Detect which test framework is being used."""
    return self.validation_impl.detect_test_framework()

def _execute_tests(self, framework: Optional[str]) -> Dict[str, Any]:
    """Execute tests using the detected framework."""
    return self.validation_impl.execute_tests(framework)

def _run_pytest(self) -> Dict[str, Any]:
    """Run pytest and parse results."""
    return self.validation_impl._run_pytest()

def _run_unittest(self) -> Dict[str, Any]:
    """Run unittest and parse results."""
    return self.validation_impl._run_unittest()

def _run_jest(self) -> Dict[str, Any]:
    """Run Jest and parse results."""
    return self.validation_impl._run_jest()

def _run_go_tests(self) -> Dict[str, Any]:
    """Run Go tests and parse results."""
    return self.validation_impl._run_go_tests()

def _validate_prd_requirements(self, prd_path: Path) -> Dict[str, Any]:
    """Validate implementation against PRD requirements."""
    return self.validation_impl.validate_prd_requirements(prd_path)

def _execute_quality_gates(self, gate_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """Execute quality gate checks."""
    return self.validation_impl.execute_quality_gates(gate_names)

def _check_linting(self) -> Dict[str, Any]:
    """Check code linting."""
    return self.validation_impl._check_linting()

def _check_typecheck(self) -> Dict[str, Any]:
    """Check type checking."""
    return self.validation_impl._check_typecheck()

def _check_security(self) -> Dict[str, Any]:
    """Check security issues."""
    return self.validation_impl._check_security()

def _generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
    """Generate human-readable validation report."""
    return self.validation_impl.generate_validation_report(validation_results)

def _is_validation_successful(self, validation_results: Dict[str, Any]) -> bool:
    """Check if validation was successful."""
    return self.validation_impl.is_validation_successful(validation_results)
```

### Step 3: Update _phase_validation Method

Replace the existing `_phase_validation` method with the full implementation:

```python
def _phase_validation(self, prd_path: Path) -> Dict[str, Any]:
    """Phase 4: Validate implementation quality with autonomous test execution."""
    self.logger.info("Phase 4: Validation")

    # Update session state to VALIDATING
    self.session_manager.transition_state(
        session_id=self.session_id,
        new_state=SessionStatus.VALIDATING,
    )

    validation_results = {
        "autonomous_mode": True,
        "human_interaction": False,
        "tests": {},
        "prd": {},
        "quality_gates": {},
    }

    # Step 1: Execute test suite with framework detection
    if self.config["validation"]["run_tests"]:
        self.logger.info("  → Running test suite...")

        test_framework = self._detect_test_framework()
        self.logger.info(f"  • Detected test framework: {test_framework or 'none'}")

        test_result = self._execute_tests(test_framework)

        validation_results["tests"] = {
            "framework": test_framework,
            "status": "passed" if test_result.get("success") else "failed",
            "passed": test_result.get("passed", 0),
            "failed": test_result.get("failed", 0),
            "total": test_result.get("total", 0),
            "coverage": test_result.get("coverage", 0.0),
            "failures": test_result.get("failures", [])[:5],
        }

        status_str = "✓" if test_result.get("success") else "✗"
        self.logger.info(
            f"  {status_str} Tests: {test_result.get('passed', 0)}/{test_result.get('total', 0)} passed"
        )

        # Log test execution decision
        self.decision_logger.log_decision(
            decision_type="test_execution",
            decision={
                "decision": f"Test execution using {test_framework or 'no framework'}",
                "rationale": f"Autonomous test execution detected framework '{test_framework}' and ran test suite. "
                           f"Result: {test_result.get('passed', 0)} passed, {test_result.get('failed', 0)} failed",
                "phase": "validation",
                "context": {
                    "framework": test_framework,
                    "total_tests": test_result.get("total", 0),
                    "passed": test_result.get("passed", 0),
                    "failed": test_result.get("failed", 0),
                    "coverage": test_result.get("coverage", 0.0),
                },
                "impact": {
                    "validation_status": "passed" if test_result.get("success") else "failed",
                    "autonomous_execution": "No human input required",
                },
            },
        )

    # Step 2: Validate PRD requirements
    if self.config["validation"]["validate_prd"]:
        self.logger.info("  → Validating PRD requirements...")

        prd_result = self._validate_prd_requirements(prd_path)

        validation_results["prd"] = {
            "status": "passed" if prd_result.get("all_requirements_met") else "failed",
            "total_requirements": prd_result.get("total_requirements", 0),
            "validated_requirements": prd_result.get("validated_requirements", 0),
            "coverage_percentage": prd_result.get("coverage_percentage", 0.0),
            "critical_gaps": prd_result.get("critical_gaps", []),
        }

        coverage = prd_result.get("coverage_percentage", 0.0)
        status_str = "✓" if prd_result.get("all_requirements_met") else "✗"
        self.logger.info(
            f"  {status_str} PRD validation: {coverage:.1f}% coverage "
            f"({prd_result.get('validated_requirements', 0)}/{prd_result.get('total_requirements', 0)} requirements met)"
        )

        # Log PRD validation decision
        self.decision_logger.log_decision(
            decision_type="prd_validation",
            decision={
                "decision": f"PRD requirement validation: {coverage:.1f}% coverage",
                "rationale": f"Validated {prd_result.get('validated_requirements', 0)} of "
                           f"{prd_result.get('total_requirements', 0)} requirements. "
                           f"Critical gaps: {len(prd_result.get('critical_gaps', []))}",
                "phase": "validation",
                "context": {
                    "prd_path": str(prd_path),
                    "total_requirements": prd_result.get("total_requirements", 0),
                    "validated_requirements": prd_result.get("validated_requirements", 0),
                    "coverage_percentage": coverage,
                    "critical_gaps": prd_result.get("critical_gaps", []),
                },
                "impact": {
                    "prd_compliance": "passed" if prd_result.get("all_requirements_met") else "failed",
                    "implementation_gaps": len(prd_result.get("critical_gaps", [])),
                },
            },
        )

    # Step 3: Run quality gates
    quality_gates = self.config["validation"]["quality_gates"]
    if quality_gates:
        self.logger.info("  → Running quality gates...")

        gate_results = self._execute_quality_gates(quality_gates)

        validation_results["quality_gates"] = gate_results

        # Count gate results
        passed_gates = sum(1 for g in gate_results.values() if g.get("status") == "passed")
        total_gates = len(gate_results)

        status_str = "✓" if passed_gates == total_gates else "✗"
        self.logger.info(f"  {status_str} Quality gates: {passed_gates}/{total_gates} passed")

        for gate_name, gate_result in gate_results.items():
            gate_status = gate_result.get("status", "unknown")
            self.logger.info(f"    • {gate_name}: {gate_status}")

        # Log quality gate decision
        self.decision_logger.log_decision(
            decision_type="quality_gates",
            decision={
                "decision": f"Quality gate execution: {passed_gates}/{total_gates} passed",
                "rationale": f"Executed {total_gates} quality gates ({', '.join(quality_gates)}). "
                           f"Result: {passed_gates} passed, {total_gates - passed_gates} failed",
                "phase": "validation",
                "context": {
                    "gates_configured": quality_gates,
                    "gates_executed": list(gate_results.keys()),
                    "gates_passed": passed_gates,
                    "gates_failed": total_gates - passed_gates,
                    "detailed_results": gate_results,
                },
                "impact": {
                    "code_quality": "acceptable" if passed_gates == total_gates else "needs_improvement",
                    "autonomous_validation": "All quality gates executed without human input",
                },
            },
        )

    # Step 4: Create validation checkpoint
    self.logger.info("  → Creating validation checkpoint...")
    try:
        validation_checkpoint = self.checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            phase=CheckpointPhase.VALIDATE,
            checkpoint_type=CheckpointType.PHASE_COMPLETE,
            description="Validation phase complete",
            state_snapshot=StateSnapshot(
                tasks_completed=validation_results.get("tests", {}).get("passed", 0),
            ),
        )
        validation_results["checkpoint"] = validation_checkpoint.checkpoint_id
        self.logger.info(f"  ✓ Checkpoint: {validation_checkpoint.commit_sha[:8]}")
    except Exception as e:
        self.logger.warning(f"  ⚠ Could not create checkpoint: {e}")

    # Step 5: Generate validation report
    validation_results["report"] = self._generate_validation_report(validation_results)

    # Step 6: Handle validation failures with autonomous recovery
    if not self._is_validation_successful(validation_results):
        self.logger.warning("  ⚠ Validation failed, attempting autonomous recovery...")
        recovery_result = self._attempt_validation_recovery(validation_results)

        validation_results["recovery"] = recovery_result

        if recovery_result.get("success"):
            self.logger.info("  ✓ Recovery successful, validation may retry")
        else:
            self.logger.error("  ✗ Recovery failed, will proceed to review phase")

    return validation_results
```

### Step 4: Add Recovery Method

Add the autonomous recovery method:

```python
def _attempt_validation_recovery(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt autonomous recovery from validation failures."""
    recovery_result = {
        "success": False,
        "message": "Recovery not attempted",
        "actions_taken": [],
    }

    try:
        # Analyze failures
        failures = []

        tests = validation_results.get("tests", {})
        if tests.get("status") == "failed":
            failures.append(f"Test failures: {tests.get('failed', 0)} tests failed")

        prd = validation_results.get("prd", {})
        if prd.get("critical_gaps"):
            failures.append(f"PRD gaps: {len(prd.get('critical_gaps', []))} critical requirements missing")

        quality_gates = validation_results.get("quality_gates", {})
        failed_gates = [name for name, result in quality_gates.items() if result.get("status") == "failed"]
        if failed_gates:
            failures.append(f"Quality gates: {', '.join(failed_gates)} failed")

        if not failures:
            return recovery_result

        self.logger.info("  → Analyzing validation failures:")
        for failure in failures:
            self.logger.info(f"    • {failure}")

        # Determine recovery strategy (autonomous, no human input)
        recovery_strategy = "retry_with_fixes"  # Autonomous retry strategy

        self.logger.info(f"  → Recovery strategy: {recovery_strategy}")

        # Log recovery decision
        self.decision_logger.log_decision(
            decision_type="validation_recovery",
            decision={
                "decision": f"Attempt autonomous recovery: {recovery_strategy}",
                "rationale": f"Validation failed with {len(failures)} issues. "
                           f"Autonomous recovery will attempt fixes without human input. "
                           f"If recovery fails, workflow will proceed to review phase for refinement.",
                "phase": "validation",
                "context": {
                    "failures": failures,
                    "strategy": recovery_strategy,
                    "human_interaction": False,
                },
                "impact": {
                    "autonomous_recovery": True,
                    "fallback": "review_phase_refinement",
                },
            },
        )

        recovery_result.update({
            "success": False,  # Recovery doesn't fix issues in this phase
            "message": "Validation failures logged for review phase refinement",
            "actions_taken": [
                "analyzed_validation_failures",
                "determined_recovery_strategy",
                "logged_issues_for_refinement",
            ],
            "failures": failures,
            "strategy": recovery_strategy,
        })

    except Exception as e:
        self.logger.error(f"  ✗ Recovery attempt failed: {e}")
        recovery_result["message"] = f"Recovery error: {str(e)}"

    return recovery_result
```

### Step 5: Run Tests

Verify the implementation works correctly:

```bash
# Run the validation phase tests
python .flow/maestro/tests/test_validation_phase_standalone.py

# Expected output:
# Ran 19 tests in 0.055s
# OK
```

## Configuration

The validation phase is controlled by the orchestrator config:

```yaml
validation:
  run_tests: true
  validate_prd: true
  quality_gates:
    - lint
    - typecheck
    - security
  fail_on_gate_violation: true
```

## Usage Example

```python
# In the orchestrator workflow
result = self._execute_workflow_phases(feature_request)

# The validation phase will automatically:
# 1. Detect and execute tests
# 2. Validate PRD requirements
# 3. Run quality gates
# 4. Generate validation report
# 5. Attempt recovery on failures
```

## Key Benefits

1. **Autonomous Operation**: No human interaction required
2. **Multi-Language Support**: Python, JavaScript/TypeScript, Go
3. **Flexible Quality Gates**: Configurable and extensible
4. **Comprehensive Reporting**: Detailed validation reports
5. **Error Resilience**: Graceful handling of missing tools
6. **Integration Ready**: Works with existing Maestro components

## Troubleshooting

### Issue: Tests not detected

**Solution**: Ensure test configuration files exist (pytest.ini, pyproject.toml, etc.)

### Issue: Quality gates skipped

**Solution**: Install required tools (ruff, mypy, bandit, etc.) or configure different gates

### Issue: PRD validation fails

**Solution**: Ensure PRD has proper YAML frontmatter with requirements section

## Next Steps

1. Integrate the implementation into the orchestrator
2. Test with real projects
3. Customize quality gates for specific needs
4. Add additional test frameworks if needed
5. Configure coverage thresholds
