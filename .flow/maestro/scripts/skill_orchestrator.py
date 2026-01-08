#!/usr/bin/env python3
"""
Maestro Skill Orchestrator

Handles skill invocation before subagent execution. Provides domain-specific
guidance by invoking appropriate skills and passing their output to subagents.
"""

import re
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


class SkillInvocationStatus(str, Enum):
    """Status of skill invocation."""
    PENDING = "pending"
    INVOKING = "invoking"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SkillMapping:
    """Mapping configuration for a skill."""
    skill_name: str
    triggers: List[str]
    prompt_template: str
    description: Optional[str] = None


@dataclass
class SkillInvocation:
    """Record of a skill invocation."""
    skill_name: str
    args: str
    result: Optional[str] = None
    status: SkillInvocationStatus = SkillInvocationStatus.PENDING
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class SkillContext:
    """Context passed to skill invocation."""
    task_description: str
    task_category: Optional[str] = None
    prd_context: Optional[str] = None
    code_context: Optional[str] = None
    existing_patterns: Optional[str] = None
    dependencies: Optional[List[str]] = None
    external_api: Optional[str] = None
    auth_method: Optional[str] = None
    doc_type: Optional[str] = None
    app_url: Optional[str] = None
    test_scenarios: Optional[str] = None
    skill_purpose: Optional[str] = None
    workflow_context: Optional[str] = None
    api_spec: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class EnrichedContext:
    """Task context enriched with skill outputs."""
    original_context: Dict[str, Any]
    skill_invocations: List[SkillInvocation]
    skill_guidance: Dict[str, str]  # skill_name -> guidance
    combined_guidance: str
    invocation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_context": self.original_context,
            "skill_invocations": [inv.to_dict() for inv in self.skill_invocations],
            "skill_guidance": self.skill_guidance,
            "combined_guidance": self.combined_guidance,
            "invocation_timestamp": self.invocation_timestamp,
        }


class SkillOrchestrator:
    """
    Orchestrates skill invocation before subagent execution.

    The skill orchestrator:
    1. Detects applicable skills from task metadata or trigger patterns
    2. Invokes skills using appropriate prompt templates
    3. Passes skill output to subagents as context
    4. Handles skill failures gracefully
    """

    # Default skill mappings from subagent-types.yaml
    DEFAULT_SKILL_MAPPINGS: Dict[str, SkillMapping] = {
        "flow:plan": SkillMapping(
            skill_name="flow:plan",
            triggers=[
                r"generate.*prd",
                r"create.*prd",
                r"plan.*feature",
                r"requirements.*doc",
                r"product.*requirements",
            ],
            prompt_template="""Generate a Product Requirements Document (PRD) for: {task_description}

Autonomous Mode: {autonomous_mode}
Session ID: {session_id}
Enable Human Interaction: {enable_human_interaction}

Requirements:
- Generate comprehensive PRD with functional requirements
- Include technical considerations and constraints
- Define acceptance criteria
- If enable_human_interaction is True, ask clarifying questions exactly once
- If autonomous_mode is True, proceed with sensible defaults for ambiguous decisions

Output:
- PRD should be saved to .flow/prd-{session_id}.md
- Return the path to the generated PRD file
""",
            description="PRD generation skill for planning phase with one-time human interaction"
        ),
        "flow:generate-tasks": SkillMapping(
            skill_name="flow:generate-tasks",
            triggers=[
                r"generate.*tasks",
                r"create.*tasks",
                r"breakdown.*work",
                r"task.*generation",
                r"implementation.*tasks",
            ],
            prompt_template="""Generate implementation tasks for PRD at: {prd_path}

Autonomous Mode: {autonomous_mode}
Session ID: {session_id}
Enable Human Interaction: {enable_human_interaction}

Requirements:
- Read and analyze the PRD file
- Generate epics and sub-tasks with clear dependencies
- Order tasks to maximize parallel execution
- Use beads (bd) for task tracking
- Return list of tasks with dependencies

Context:
- PRD Path: {prd_path}
- This is autonomous mode - proceed without human input
""",
            description="Task generation skill for breaking down PRD into actionable tasks"
        ),
        "frontend-design": SkillMapping(
            skill_name="frontend-design",
            triggers=[
                r"create.*ui",
                r"build.*interface",
                r"design.*component",
                r"front.?end.*design",
                r"styling|style.*guide",
                r"layout|visual",
            ],
            prompt_template="""Create distinctive, production-grade frontend UI for: {task_description}

Requirements:
- Avoid generic AI aesthetics
- Use creative, polished design patterns
- Ensure accessibility compliance
- Responsive design for all screen sizes

Context:
- PRD: {prd_context}
- Existing patterns: {existing_patterns}
""",
            description="Frontend UI design skill for component creation and styling"
        ),
        "mcp-builder": SkillMapping(
            skill_name="mcp-builder",
            triggers=[
                r"create.*mcp.*server",
                r"build.*integration",
                r"mcp.*tool",
                r"model.?context.?protocol",
                r"external.*api.*integration",
                r"third.?party.*service",
            ],
            prompt_template="""Build an MCP server for: {task_description}

Requirements:
- Use FastMCP (Python) or MCP SDK (TypeScript)
- Follow MCP server best practices
- Include proper error handling
- Add resource definitions for all operations

Integration details:
- External API: {external_api}
- Authentication: {auth_method}
""",
            description="MCP server construction skill for integrations"
        ),
        "skill-creator": SkillMapping(
            skill_name="skill-creator",
            triggers=[
                r"create.*skill",
                r"new.*agent.*skill",
                r"define.*agent",
                r"agent.*capability",
                r"custom.*skill.*workflow",
            ],
            prompt_template="""Create a new agent skill for: {task_description}

Requirements:
- Follow skill-creator best practices
- Include clear usage examples
- Add skill metadata and documentation
- Define input/output schema

Skill purpose: {skill_purpose}
Target workflow: {workflow_context}
""",
            description="Custom agent skill creation skill"
        ),
        "webapp-testing": SkillMapping(
            skill_name="webapp-testing",
            triggers=[
                r"test.*web.*app",
                r"e2e.*test",
                r"playwright",
                r"chrome.*devtool",
                r"browser.*test",
                r"ui.*test|component.*test",
                r"verify.*frontend",
            ],
            prompt_template="""Test web application: {task_description}

Requirements:
- Use Playwright for browser automation
- Test on multiple browsers (Chrome, Firefox, Safari)
- Include accessibility testing
- Generate test reports

Test environment:
- URL: {app_url}
- Test user flows: {test_scenarios}
""",
            description="Web application testing skill using Playwright"
        ),
        "document-skills": SkillMapping(
            skill_name="document-skills",
            triggers=[
                r"create.*pdf|docx|xlsx|pptx",
                r"generate.*document",
                r"export.*report",
                r"document.*template",
                r"api.*documentation",
                r"user.*guide",
                r"technical.*spec",
            ],
            prompt_template="""Generate document: {task_description}

Requirements:
- Document type: {doc_type}
- Include tables/figures as appropriate
- Follow documentation best practices
- Export to specified format

Content sources:
- PRD: {prd_context}
- Code: {code_context}
- API endpoints: {api_spec}
""",
            description="Document generation skill for reports and documentation"
        ),
    }

    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize skill orchestrator.

        Args:
            repo_root: Repository root path. If None, auto-detected.
        """
        if repo_root:
            self.repo_root = Path(repo_root).absolute()
        else:
            self.repo_root = Path(__file__).parent.parent.parent.parent.absolute()

        self.skill_mappings = self._load_skill_mappings()
        self.invocation_history: List[SkillInvocation] = []

    def _load_skill_mappings(self) -> Dict[str, SkillMapping]:
        """
        Load skill mappings from subagent-types.yaml.

        Returns:
            Dictionary of skill_name -> SkillMapping
        """
        config_path = self.repo_root / ".claude" / "subagent-types.yaml"

        if not config_path.exists():
            return self.DEFAULT_SKILL_MAPPINGS.copy()

        try:
            import yaml

            with open(config_path) as f:
                config = yaml.safe_load(f)

            skill_mappings = {}
            for skill_name, skill_config in config.get("skill_mappings", {}).items():
                skill_mappings[skill_name] = SkillMapping(
                    skill_name=skill_name,
                    triggers=skill_config.get("triggers", []),
                    prompt_template=skill_config.get("prompt_template", ""),
                    description=skill_config.get("description"),
                )

            return skill_mappings if skill_mappings else self.DEFAULT_SKILL_MAPPINGS.copy()

        except (ImportError, FileNotFoundError, yaml.YAMLError) as e:
            # Fallback to defaults if yaml is not available or file is corrupted
            return self.DEFAULT_SKILL_MAPPINGS.copy()

    def detect_applicable_skills(
        self,
        task_description: str,
        task_category: Optional[str] = None,
        task_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Detect applicable skills for a task.

        Detection strategy:
        1. Check task_metadata.applicable_skills if present
        2. Check task_category for associated skill
        3. Match task_description against skill trigger patterns

        Args:
            task_description: The task description text
            task_category: Optional task category
            task_metadata: Optional task metadata from beads

        Returns:
            List of applicable skill names
        """
        applicable_skills = []

        # Strategy 1: Check task metadata
        if task_metadata and "applicable_skills" in task_metadata:
            metadata_skills = task_metadata["applicable_skills"]
            if isinstance(metadata_skills, list) and metadata_skills:
                # Validate that skills exist in mappings
                valid_skills = [s for s in metadata_skills if s in self.skill_mappings]
                applicable_skills.extend(valid_skills)
                return applicable_skills  # Return early if explicitly specified

        # Strategy 2: Check task category for associated skill
        if task_category:
            category_skill = self._get_skill_for_category(task_category)
            if category_skill and category_skill not in applicable_skills:
                applicable_skills.append(category_skill)

        # Strategy 3: Match against trigger patterns
        description_lower = task_description.lower()

        for skill_name, skill_mapping in self.skill_mappings.items():
            if skill_name in applicable_skills:
                continue  # Already added

            for trigger_pattern in skill_mapping.triggers:
                try:
                    if re.search(trigger_pattern, description_lower, re.IGNORECASE):
                        applicable_skills.append(skill_name)
                        break  # No need to check other triggers for this skill
                except re.error:
                    # Invalid regex pattern, skip
                    continue

        return applicable_skills

    def _get_skill_for_category(self, category: str) -> Optional[str]:
        """
        Get the skill associated with a task category.

        Args:
            category: Task category name

        Returns:
            Skill name or None
        """
        # Category to skill mapping from subagent-types.yaml
        category_skill_map = {
            "frontend": "frontend-design",
            "testing": "webapp-testing",
            "documentation": "document-skills",
        }

        return category_skill_map.get(category)

    def format_skill_prompt(
        self,
        skill_name: str,
        context: SkillContext,
    ) -> str:
        """
        Format skill prompt from template and context.

        Args:
            skill_name: Name of the skill
            context: Skill context with template variables

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If skill_name not found in mappings
        """
        if skill_name not in self.skill_mappings:
            raise ValueError(f"Unknown skill: {skill_name}")

        skill_mapping = self.skill_mappings[skill_name]
        template = skill_mapping.prompt_template

        # Build template variables from context
        context_dict = context.to_dict()

        # Fill template using str.format() for {variable} substitution
        try:
            # Use format_map with a dict that returns empty string for missing keys
            class DefaultDict(dict):
                def __missing__(self, key):
                    return ""

            formatted_prompt = template.format_map(DefaultDict(context_dict))
        except (KeyError, ValueError) as e:
            # Fallback: replace missing variables with empty strings manually
            import re

            # Find all {variable} patterns in template
            variables = set(re.findall(r'\{(\w+)\}', template))

            # Build replacement dict with empty defaults
            defaults = {var: context_dict.get(var, "") for var in variables}

            # Try formatting again
            try:
                formatted_prompt = template.format(**defaults)
            except (KeyError, ValueError):
                # Last resort: manual replacement
                formatted_prompt = template
                for var, value in defaults.items():
                    formatted_prompt = formatted_prompt.replace(f"{{{var}}}", str(value))

        return formatted_prompt

    def invoke_skill(
        self,
        skill_name: str,
        context: Union[SkillContext, str, Dict[str, Any]],
    ) -> SkillInvocation:
        """
        Invoke a skill with the given context.

        Note: This method prepares the skill invocation but does not
        actually execute the Skill tool (that's done by Claude Code).
        It returns a SkillInvocation object with the prepared arguments.

        Args:
            skill_name: Name of the skill to invoke
            context: Skill context (SkillContext object, dict, or string)

        Returns:
            SkillInvocation object with prepared invocation

        Raises:
            ValueError: If skill_name not found
        """
        if skill_name not in self.skill_mappings:
            raise ValueError(
                f"Unknown skill: {skill_name}. "
                f"Available skills: {list(self.skill_mappings.keys())}"
            )

        # Normalize context
        if isinstance(context, str):
            context = SkillContext(task_description=context)
        elif isinstance(context, dict):
            context = SkillContext(**context)
        elif not isinstance(context, SkillContext):
            raise ValueError(f"Invalid context type: {type(context)}")

        # Format skill prompt
        skill_args = self.format_skill_prompt(skill_name, context)

        # Create invocation record
        invocation = SkillInvocation(
            skill_name=skill_name,
            args=skill_args,
            status=SkillInvocationStatus.PENDING,
        )

        # Add to history
        self.invocation_history.append(invocation)

        return invocation

    def apply_skills_before_subagent(
        self,
        task_metadata: Dict[str, Any],
        task_context: Dict[str, Any],
    ) -> EnrichedContext:
        """
        Apply applicable skills before subagent execution.

        This is the main orchestration method that:
        1. Detects applicable skills from task metadata
        2. Invokes each skill and captures output
        3. Enriches task context with skill guidance

        Args:
            task_metadata: Task metadata from beads (description, category, etc.)
            task_context: Current task context to pass to subagent

        Returns:
            Enriched context with skill guidance

        Note:
            This method only prepares skill invocations. The actual skill
            execution happens when Claude Code processes the returned
            EnrichedContext and invokes the Skill tool.
        """
        task_description = task_metadata.get("description", "")
        task_category = task_metadata.get("category")

        # Detect applicable skills
        applicable_skills = self.detect_applicable_skills(
            task_description=task_description,
            task_category=task_category,
            task_metadata=task_metadata,
        )

        # Build skill context
        skill_context = SkillContext(
            task_description=task_description,
            task_category=task_category,
            prd_context=task_context.get("prd_context"),
            code_context=task_context.get("code_context"),
            existing_patterns=task_context.get("existing_patterns"),
            dependencies=task_context.get("dependencies"),
            external_api=task_context.get("external_api"),
            auth_method=task_context.get("auth_method"),
            doc_type=task_context.get("doc_type"),
            app_url=task_context.get("app_url"),
            test_scenarios=task_context.get("test_scenarios"),
            skill_purpose=task_context.get("skill_purpose"),
            workflow_context=task_context.get("workflow_context"),
            api_spec=task_context.get("api_spec"),
        )

        # Prepare skill invocations
        skill_invocations = []
        skill_guidance = {}

        for skill_name in applicable_skills:
            try:
                invocation = self.invoke_skill(skill_name, skill_context)
                invocation.status = SkillInvocationStatus.INVOKING
                skill_invocations.append(invocation)

                # Add placeholder for skill guidance
                # (Will be filled when skill actually executes)
                skill_guidance[skill_name] = f"Skill '{skill_name}' invoked with args: {invocation.args[:100]}..."

            except ValueError as e:
                # Skill invocation failed, record error
                failed_invocation = SkillInvocation(
                    skill_name=skill_name,
                    args="",
                    status=SkillInvocationStatus.FAILED,
                    error_message=str(e),
                )
                skill_invocations.append(failed_invocation)

        # Build combined guidance
        combined_guidance = self._build_combined_guidance(skill_invocations, skill_guidance)

        # Create enriched context
        enriched = EnrichedContext(
            original_context=task_context,
            skill_invocations=skill_invocations,
            skill_guidance=skill_guidance,
            combined_guidance=combined_guidance,
        )

        return enriched

    def _build_combined_guidance(
        self,
        skill_invocations: List[SkillInvocation],
        skill_guidance: Dict[str, str],
    ) -> str:
        """
        Build combined skill guidance string.

        Args:
            skill_invocations: List of skill invocations
            skill_guidance: Dictionary of skill_name -> guidance

        Returns:
            Combined guidance string
        """
        if not skill_invocations:
            return ""

        sections = []

        for invocation in skill_invocations:
            if invocation.status == SkillInvocationStatus.FAILED:
                sections.append(
                    f"## Skill: {invocation.skill_name} (FAILED)\n"
                    f"Error: {invocation.error_message}\n"
                )
            else:
                guidance = skill_guidance.get(invocation.skill_name, "")
                sections.append(
                    f"## Skill: {invocation.skill_name}\n"
                    f"{guidance}\n"
                )

        return "\n".join(sections)

    def get_invocation_history(
        self,
        skill_name: Optional[str] = None,
        status: Optional[SkillInvocationStatus] = None,
        limit: Optional[int] = None,
    ) -> List[SkillInvocation]:
        """
        Query skill invocation history.

        Args:
            skill_name: Filter by skill name
            status: Filter by invocation status
            limit: Maximum number of results

        Returns:
            List of matching skill invocations
        """
        results = self.invocation_history

        if skill_name:
            results = [inv for inv in results if inv.skill_name == skill_name]

        if status:
            results = [inv for inv in results if inv.status == status]

        # Sort by timestamp descending
        results = sorted(results, key=lambda inv: inv.timestamp, reverse=True)

        if limit:
            results = results[:limit]

        return results

    def clear_invocation_history(self) -> None:
        """Clear invocation history."""
        self.invocation_history.clear()

    def get_available_skills(self) -> List[str]:
        """
        Get list of available skills.

        Returns:
            List of skill names
        """
        return list(self.skill_mappings.keys())

    def get_skill_info(self, skill_name: str) -> Optional[SkillMapping]:
        """
        Get information about a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            SkillMapping object or None if not found
        """
        return self.skill_mappings.get(skill_name)


def main():
    """CLI entry point for skill orchestration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Maestro Skill Orchestrator"
    )
    parser.add_argument(
        "action",
        choices=["detect", "list", "info", "history"],
        help="Action to perform",
    )
    parser.add_argument("--description", help="Task description")
    parser.add_argument("--category", help="Task category")
    parser.add_argument("--skill", help="Skill name")
    parser.add_argument("--format", choices=["json", "pretty"], default="json",
                        help="Output format")

    args = parser.parse_args()

    orchestrator = SkillOrchestrator()

    if args.action == "detect":
        if not args.description:
            parser.error("--description required for detect action")

        skills = orchestrator.detect_applicable_skills(
            task_description=args.description,
            task_category=args.category,
        )

        output = {
            "task_description": args.description,
            "task_category": args.category,
            "applicable_skills": skills,
        }

    elif args.action == "list":
        skills = orchestrator.get_available_skills()
        output = {
            "available_skills": [
                {
                    "name": skill_name,
                    "description": orchestrator.skill_mappings[skill_name].description,
                    "triggers": orchestrator.skill_mappings[skill_name].triggers,
                }
                for skill_name in skills
            ]
        }

    elif args.action == "info":
        if not args.skill:
            parser.error("--skill required for info action")

        skill_info = orchestrator.get_skill_info(args.skill)
        if not skill_info:
            output = {"error": f"Skill not found: {args.skill}"}
        else:
            output = {
                "name": skill_info.skill_name,
                "description": skill_info.description,
                "triggers": skill_info.triggers,
                "prompt_template": skill_info.prompt_template[:200] + "...",
            }

    elif args.action == "history":
        history = orchestrator.get_invocation_history()
        output = {
            "invocation_count": len(history),
            "invocations": [inv.to_dict() for inv in history[:10]],
        }

    # Print output
    if args.format == "pretty":
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output))


if __name__ == "__main__":
    main()
