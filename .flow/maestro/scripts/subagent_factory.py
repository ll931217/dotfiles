#!/usr/bin/env python3
"""
Subagent Factory for Maestro Orchestrator

Intelligent task-to-subagent mapping system that:
- Parses task descriptions to extract category keywords
- Matches to subagent types using subagent-types.yaml taxonomy
- Selects primary subagent based on task category
- Handles fallbacks when primary agent unavailable
- Creates agent configurations for Task tool execution
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import yaml


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SubagentConfig:
    """Configuration for a subagent type."""
    subagent: str
    patterns: List[str] = field(default_factory=list)
    skill: Optional[str] = None
    fallback_agents: List[str] = field(default_factory=list)
    category: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subagent": self.subagent,
            "patterns": self.patterns,
            "skill": self.skill,
            "fallback_agents": self.fallback_agents,
            "category": self.category
        }


@dataclass
class SkillMapping:
    """Configuration for a skill mapping."""
    skill_name: str
    triggers: List[str] = field(default_factory=list)
    prompt_template: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "triggers": self.triggers,
            "prompt_template": self.prompt_template
        }


@dataclass
class DetectionResult:
    """Result of subagent type detection."""
    subagent_type: str
    category: str
    confidence: float
    skill: Optional[str] = None
    matched_patterns: List[str] = field(default_factory=list)
    fallback_agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subagent_type": self.subagent_type,
            "category": self.category,
            "confidence": self.confidence,
            "skill": self.skill,
            "matched_patterns": self.matched_patterns,
            "fallback_agents": self.fallback_agents
        }


@dataclass
class AgentConfig:
    """Complete configuration for subagent execution."""
    subagent_type: str
    system_prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    skill_config: Optional[Dict[str, Any]] = None
    fallback_chain: List[str] = field(default_factory=list)
    detection_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subagent_type": self.subagent_type,
            "system_prompt": self.system_prompt,
            "context": self.context,
            "skill_config": self.skill_config,
            "fallback_chain": self.fallback_chain,
            "detection_metadata": self.detection_metadata
        }


class TaskCategoryParser:
    """Parses task descriptions to extract category keywords and metadata."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize parser with detection configuration."""
        self.confidence_threshold = config.get(
            "detection_config",
            {}
        ).get("confidence_threshold", 0.6)
        self.priority_order = config.get(
            "detection_config",
            {}
        ).get("priority_order", [])

    def extract_keywords(self, task_description: str) -> List[str]:
        """
        Extract relevant keywords from task description.

        Args:
            task_description: Raw task description text

        Returns:
            List of normalized keywords
        """
        # Convert to lowercase
        text = task_description.lower()

        # Extract file extensions
        file_extensions = re.findall(r'\.\w{2,4}\b', text)

        # Extract technical terms (words with underscores, hyphens, or camelCase)
        technical_terms = re.findall(
            r'\b[a-z0-9_]+\b|\b[a-z]+-[a-z]+\b|[A-Z][a-z]+(?:[A-Z][a-z]+)*',
            text
        )

        # Extract common technical phrases
        phrases = re.findall(
            r'\b(?:api|database|backend|frontend|test|testing|tests|spec|mock|assert|deploy|'
            r'document|debug|refactor|performance|security|'
            r'architecture|microservice|controller|unit|integration|e2e)\b',
            text
        )

        # Combine and deduplicate
        keywords = list(set(
            file_extensions + technical_terms + phrases
        ))

        logger.debug(f"Extracted keywords: {keywords}")
        return keywords

    def categorize_task(
        self,
        task_description: str,
        task_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Categorize task based on description and metadata.

        Args:
            task_description: Raw task description
            task_metadata: Additional task context (files, dependencies, etc.)

        Returns:
            Dictionary with category analysis
        """
        keywords = self.extract_keywords(task_description)

        # Analyze file extensions from metadata
        file_context = task_metadata.get("files", [])
        extensions = set()
        for file_path in file_context:
            if "." in Path(file_path).name:
                ext = Path(file_path).suffix.lower()
                extensions.add(ext)

        # Analyze dependencies
        dependencies = task_metadata.get("dependencies", [])

        return {
            "keywords": keywords,
            "extensions": list(extensions),
            "dependencies": dependencies,
            "has_tests": any(
                any(kw in keyword for kw in ["test", "spec", "mock", "assert"])
                for keyword in keywords
            ),
            "has_ui": any(
                any(kw in keyword for kw in ["ui", "interface", "component", "react"])
                for keyword in keywords
            ),
            "has_backend": any(
                any(kw in keyword for kw in ["api", "service", "backend", "controller"])
                for keyword in keywords
            )
        }


class SubagentSelector:
    """Selects appropriate subagent based on task category analysis."""

    def __init__(self, categories: Dict[str, Dict[str, Any]], config: Dict[str, Any]):
        """Initialize selector with category mappings."""
        self.categories = categories
        self.config = config
        self.priority_order = config.get(
            "detection_config",
            {}
        ).get("priority_order", [])
        self.confidence_threshold = config.get(
            "detection_config",
            {}
        ).get("confidence_threshold", 0.6)

    def match_patterns(
        self,
        task_description: str,
        category_analysis: Dict[str, Any],
        patterns: List[str]
    ) -> Tuple[float, List[str]]:
        """
        Match task description and category analysis against patterns.

        Args:
            task_description: Raw task description
            category_analysis: Parsed category information
            patterns: List of regex patterns to match

        Returns:
            Tuple of (confidence_score, matched_patterns)
        """
        matches = []
        text = task_description.lower()
        keywords = category_analysis.get("keywords", [])
        extensions = category_analysis.get("extensions", [])

        for pattern in patterns:
            try:
                # Check if pattern matches description
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(pattern)
                    continue

                # Check if pattern matches any keyword
                for keyword in keywords:
                    if re.search(pattern, keyword, re.IGNORECASE):
                        matches.append(pattern)
                        break

                # Check if pattern matches any file extension
                for ext in extensions:
                    if re.search(pattern, ext, re.IGNORECASE):
                        matches.append(pattern)
                        break

            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                continue

        # Calculate confidence based on match ratio
        if patterns:
            confidence = len(matches) / len(patterns)
        else:
            confidence = 0.0

        return min(confidence, 1.0), matches

    def select_category(
        self,
        task_description: str,
        category_analysis: Dict[str, Any]
    ) -> Tuple[str, float, List[str]]:
        """
        Select best matching category for the task.

        Args:
            task_description: Raw task description
            category_analysis: Parsed category information

        Returns:
            Tuple of (category_name, confidence, matched_patterns)
        """
        best_category = "default"
        best_confidence = 0.0
        best_matches = []

        # Check categories in priority order
        for category_name in self.priority_order:
            if category_name not in self.categories:
                continue

            category_config = self.categories[category_name]
            patterns = category_config.get("patterns", [])

            confidence, matches = self.match_patterns(
                task_description,
                category_analysis,
                patterns
            )

            # Update best match if this category scores higher
            if confidence > best_confidence:
                best_confidence = confidence
                best_category = category_name
                best_matches = matches

            logger.debug(
                f"Category '{category_name}': confidence={confidence:.2f}, "
                f"matches={len(matches)}"
            )

        return best_category, best_confidence, best_matches

    def select_subagent(
        self,
        task_description: str,
        task_metadata: Dict[str, Any]
    ) -> DetectionResult:
        """
        Select primary subagent for the task.

        Args:
            task_description: Raw task description
            task_metadata: Additional task context

        Returns:
            DetectionResult with selected subagent and metadata
        """
        # Analyze task category
        category_analysis = {
            "keywords": re.findall(r'\b[a-z0-9_-]+\b', task_description.lower()),
            "extensions": [],
            "dependencies": task_metadata.get("dependencies", [])
        }

        # Extract file extensions from files in metadata
        for file_path in task_metadata.get("files", []):
            if "." in Path(file_path).name:
                ext = Path(file_path).suffix.lower()
                category_analysis["extensions"].append(ext)

        # Select category
        category_name, confidence, matched_patterns = self.select_category(
            task_description,
            category_analysis
        )

        # Get category configuration
        category_config = self.categories.get(category_name, {})
        subagent = category_config.get("subagent", "general-purpose")
        skill = category_config.get("skill")
        fallback_agents = category_config.get("fallback_agents", [])

        result = DetectionResult(
            subagent_type=subagent,
            category=category_name,
            confidence=confidence,
            skill=skill,
            matched_patterns=matched_patterns,
            fallback_agents=fallback_agents
        )

        logger.info(
            f"Selected subagent '{subagent}' for category '{category_name}' "
            f"(confidence: {confidence:.2f})"
        )

        return result


class FallbackAgentHandler:
    """Manages fallback agent selection and validation."""

    def __init__(self, categories: Dict[str, Dict[str, Any]], config: Dict[str, Any]):
        """Initialize handler with category mappings."""
        self.categories = categories
        self.max_fallback_attempts = config.get(
            "detection_config",
            {}
        ).get("max_fallback_attempts", 3)

    def get_fallback_agents(
        self,
        subagent_type: str,
        category: str
    ) -> List[str]:
        """
        Get fallback agents for a subagent type.

        Args:
            subagent_type: Primary subagent that failed
            category: Task category

        Returns:
            List of fallback agent types in priority order
        """
        category_config = self.categories.get(category, {})
        fallback_agents = category_config.get("fallback_agents", [])

        logger.debug(
            f"Fallback agents for '{subagent_type}' (category '{category}'): "
            f"{fallback_agents}"
        )

        return fallback_agents

    def select_fallback(
        self,
        failed_agent: str,
        category: str,
        attempted_agents: List[str],
        available_agents: List[str]
    ) -> Optional[str]:
        """
        Select next fallback agent from available options.

        Args:
            failed_agent: Agent that failed
            category: Task category
            attempted_agents: Agents already attempted
            available_agents: All available agent types

        Returns:
            Next fallback agent or None if exhausted
        """
        fallback_agents = self.get_fallback_agents(failed_agent, category)

        for fallback in fallback_agents:
            if fallback not in attempted_agents and fallback in available_agents:
                logger.info(
                    f"Selected fallback agent '{fallback}' after '{failed_agent}' failed"
                )
                return fallback

        logger.warning(
            f"No more fallback agents available for '{failed_agent}' "
            f"in category '{category}'"
        )

        return None


class SubagentFactory:
    """
    Main factory for task-based subagent selection and instantiation.

    Usage:
        factory = SubagentFactory()
        result = factory.detect_subagent_type("Implement REST API for user management")
        config = factory.create_agent_config("backend-architect", {"prd": "..."})
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize subagent factory.

        Args:
            config_path: Path to subagent-types.yaml configuration
        """
        self.config_path = config_path or self._find_config_path()
        self.config = self._load_config()
        self.categories = self.config.get("task_categories", {})
        self.skill_mappings = self._load_skill_mappings()

        # Initialize components
        detection_config = self.config.get("detection_config", {})
        self.parser = TaskCategoryParser(self.config)
        self.selector = SubagentSelector(self.categories, self.config)
        self.fallback_handler = FallbackAgentHandler(self.categories, self.config)

        logger.info(f"SubagentFactory initialized with {len(self.categories)} categories")

    def _find_config_path(self) -> Path:
        """Find subagent-types.yaml configuration file."""
        # For testing: allow path to be set via environment variable
        import os
        env_path = os.environ.get("SUBAGENT_TYPES_PATH")
        if env_path:
            return Path(env_path)

        # Try relative to script first
        script_dir = Path(__file__).parent
        config_path = script_dir / ".claude" / "subagent-types.yaml"

        if config_path.exists():
            return config_path

        # Try repository root
        repo_root = Path(__file__).parent.parent.parent.parent
        config_path = repo_root / ".claude" / "subagent-types.yaml"

        if config_path.exists():
            return config_path

        # Try absolute path from script directory
        repo_root_abs = Path(__file__).resolve().parent.parent.parent.parent
        config_path = repo_root_abs / ".claude" / "subagent-types.yaml"

        if config_path.exists():
            return config_path

        raise FileNotFoundError(
            f"Cannot find subagent-types.yaml configuration file"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load subagent configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            raise

    def _load_skill_mappings(self) -> Dict[str, SkillMapping]:
        """Load skill mappings from configuration."""
        mappings = {}

        for skill_name, skill_config in self.config.get("skill_mappings", {}).items():
            mappings[skill_name] = SkillMapping(
                skill_name=skill_name,
                triggers=skill_config.get("triggers", []),
                prompt_template=skill_config.get("prompt_template", "")
            )

        logger.debug(f"Loaded {len(mappings)} skill mappings")
        return mappings

    def detect_subagent_type(self, task_description: str) -> str:
        """
        Detect subagent type from task description.

        Args:
            task_description: Raw task description text

        Returns:
            Detected subagent type name
        """
        result = self.selector.select_subagent(
            task_description,
            {}
        )

        return result.subagent_type

    def detect_skill(self, task_description: str) -> Optional[str]:
        """
        Detect if task requires a specific skill invocation.

        Args:
            task_description: Raw task description text

        Returns:
            Skill name if triggered, None otherwise
        """
        text = task_description.lower()

        for skill_name, skill_mapping in self.skill_mappings.items():
            for trigger in skill_mapping.triggers:
                if re.search(trigger, text, re.IGNORECASE):
                    logger.debug(f"Skill '{skill_name}' triggered by pattern '{trigger}'")
                    return skill_name

        return None

    def select_subagent(self, task_metadata: Dict[str, Any]) -> str:
        """
        Select subagent based on task metadata.

        Args:
            task_metadata: Task metadata including description, files, etc.

        Returns:
            Selected subagent type name
        """
        task_description = task_metadata.get(
            "description",
            task_metadata.get("content", "")
        )

        result = self.selector.select_subagent(
            task_description,
            task_metadata
        )

        return result.subagent_type

    def detect_subagent_detailed(
        self,
        task_description: str,
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> DetectionResult:
        """
        Detailed subagent detection with full metadata.

        Args:
            task_description: Raw task description text
            task_metadata: Additional task context

        Returns:
            DetectionResult with full detection metadata
        """
        task_metadata = task_metadata or {}

        result = self.selector.select_subagent(
            task_description,
            task_metadata
        )

        # Check for skill triggers
        skill = self.detect_skill(task_description)
        if skill:
            result.skill = skill

        return result

    def get_fallback_agents(self, subagent_type: str) -> List[str]:
        """
        Get fallback agents for a subagent type.

        Args:
            subagent_type: Subagent type name

        Returns:
            List of fallback agent types
        """
        # Find category for this subagent
        category = None
        for cat_name, cat_config in self.categories.items():
            if cat_config.get("subagent") == subagent_type:
                category = cat_name
                break

        if not category:
            logger.warning(f"No category found for subagent '{subagent_type}'")
            return []

        return self.fallback_handler.get_fallback_agents(subagent_type, category)

    def create_agent_config(
        self,
        subagent_type: str,
        task_context: Dict[str, Any]
    ) -> AgentConfig:
        """
        Create complete agent configuration for Task tool execution.

        Args:
            subagent_type: Selected subagent type
            task_context: Task execution context

        Returns:
            AgentConfig ready for Task tool invocation
        """
        # Find category configuration
        category = None
        category_config = {}
        for cat_name, cat_config in self.categories.items():
            if cat_config.get("subagent") == subagent_type:
                category = cat_name
                category_config = cat_config
                break

        # Build system prompt
        system_prompt = self._build_system_prompt(
            subagent_type,
            category,
            task_context
        )

        # Get fallback chain
        fallback_agents = category_config.get("fallback_agents", [])

        # Check for skill configuration
        skill_name = category_config.get("skill")
        skill_config = None
        if skill_name and skill_name in self.skill_mappings:
            skill_mapping = self.skill_mappings[skill_name]
            skill_config = {
                "name": skill_name,
                "prompt": self._format_skill_prompt(
                    skill_mapping,
                    task_context
                )
            }

        # Build detection metadata
        detection_metadata = {
            "category": category,
            "confidence": task_context.get("confidence", 1.0),
            "matched_patterns": task_context.get("matched_patterns", []),
            "timestamp": task_context.get("timestamp")
        }

        config = AgentConfig(
            subagent_type=subagent_type,
            system_prompt=system_prompt,
            context=task_context,
            skill_config=skill_config,
            fallback_chain=fallback_agents,
            detection_metadata=detection_metadata
        )

        logger.debug(f"Created agent config for '{subagent_type}'")
        return config

    def _build_system_prompt(
        self,
        subagent_type: str,
        category: Optional[str],
        task_context: Dict[str, Any]
    ) -> str:
        """Build system prompt for subagent."""
        base_prompt = f"You are a {subagent_type} specialized agent.\n"

        if category:
            base_prompt += f"Task Category: {category}\n"

        # Add PRD context if available
        if task_context.get("prd"):
            base_prompt += "\nPRD Context:\n"
            base_prompt += task_context["prd"][:500]  # Truncate for context efficiency
            base_prompt += "...\n"

        # Add relevant code context
        if task_context.get("code_patterns"):
            base_prompt += "\nCode Patterns:\n"
            base_prompt += str(task_context["code_patterns"])[:300]
            base_prompt += "\n"

        return base_prompt

    def _format_skill_prompt(
        self,
        skill_mapping: SkillMapping,
        task_context: Dict[str, Any]
    ) -> str:
        """Format skill invocation prompt."""
        template = skill_mapping.prompt_template

        # Extract template variables
        task_description = task_context.get("description", "")
        prd_context = task_context.get("prd", "")
        existing_patterns = task_context.get("code_patterns", "")
        external_api = task_context.get("external_api", "")
        auth_method = task_context.get("auth_method", "")
        skill_purpose = task_context.get("skill_purpose", "")
        workflow_context = task_context.get("workflow_context", "")
        doc_type = task_context.get("doc_type", "")
        code_context = task_context.get("code_context", "")
        api_spec = task_context.get("api_spec", "")
        app_url = task_context.get("app_url", "")
        test_scenarios = task_context.get("test_scenarios", "")

        # Format template
        prompt = template.format(
            task_description=task_description,
            prd_context=prd_context,
            existing_patterns=existing_patterns,
            external_api=external_api,
            auth_method=auth_method,
            skill_purpose=skill_purpose,
            workflow_context=workflow_context,
            doc_type=doc_type,
            code_context=code_context,
            api_spec=api_spec,
            app_url=app_url,
            test_scenarios=test_scenarios
        )

        return prompt


# CLI interface for testing
def main():
    """CLI interface for testing subagent detection."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python subagent_factory.py '<task description>'")
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])

    factory = SubagentFactory()

    print("\n=== Subagent Detection ===\n")
    print(f"Task: {task_description}\n")

    # Detect subagent type
    subagent_type = factory.detect_subagent_type(task_description)
    print(f"Subagent Type: {subagent_type}")

    # Detailed detection
    result = factory.detect_subagent_detailed(task_description)
    print(f"Category: {result.category}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Skill: {result.skill}")
    print(f"Matched Patterns: {result.matched_patterns}")
    print(f"Fallback Agents: {result.fallback_agents}")

    # Create agent config
    task_context = {
        "description": task_description,
        "confidence": result.confidence,
        "matched_patterns": result.matched_patterns
    }

    agent_config = factory.create_agent_config(subagent_type, task_context)
    print(f"\nAgent Config:")
    print(f"  System Prompt: {agent_config.system_prompt[:100]}...")
    print(f"  Skill Config: {agent_config.skill_config}")
    print(f"  Fallback Chain: {agent_config.fallback_chain}")


if __name__ == "__main__":
    main()
