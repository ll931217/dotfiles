#!/usr/bin/env bash
# Auto-Generated Documentation System
#
# Uses specialized agents to auto-generate documentation for the dotfiles project.
#
# Usage:
#   ./scripts/generate-docs.sh [--type <type>] [--output <dir>] [--verbose]
#
# Options:
#   --type <type>    Documentation type: api, config, workflow, or all
#   --output <dir>   Output directory for generated docs (default: ./docs)
#   --verbose        Show detailed generation output
#   --help           Show this help message

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
DOC_TYPE="all"
OUTPUT_DIR="./docs"
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)
      DOC_TYPE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# //g' | sed 's/^#//g'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Logging functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[DONE]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[SKIP]${NC} $1"
}

log_doc() {
  echo -e "${CYAN}[DOC]${NC} $1"
}

# Get repository root
get_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/GitHub/dotfiles"
}

# Create output directory if needed
setup_output_dir() {
  if [[ ! -d "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
    log_info "Created output directory: $OUTPUT_DIR"
  fi
}

# Generate API documentation
generate_api_docs() {
  log_doc "Generating API documentation..."

  # Uses api-documenter agent for tool APIs
  local repo_root=$(get_repo_root)
  local output_file="$OUTPUT_DIR/api.md"

  {
    echo "# API Documentation"
    echo ""
    echo "Auto-generated API documentation for dotfiles scripts and tools."
    echo ""
    echo "## Script APIs"
    echo ""

    # Find all executable scripts
    find "$repo_root/scripts" -type f -executable | while read -r script; do
      local script_name=$(basename "$script")
      local script_path="${script#$repo_root/}"

      echo "### $script_name"
      echo ""
      echo "**Path:** \`$script_path\`"
      echo ""

      # Extract usage information if available
      if grep -q "^# Usage:" "$script"; then
        echo "**Usage:**"
        echo ""
        sed -n '/^# Usage:/,/^$/p' "$script" | sed 's/^# //g' | sed 's/^#//g'
        echo ""
      fi

      # Extract description
      if head -1 "$script" | grep -q "^#!/"; then
        local description=$(sed -n '2p' "$script" | sed 's/^# //g')
        echo "**Description:** $description"
        echo ""
      fi

      echo "---"
      echo ""
    done
  } > "$output_file"

  log_success "API documentation generated: $output_file"
}

# Generate configuration documentation
generate_config_docs() {
  log_doc "Generating configuration documentation..."

  # Uses architect-review agent for config structure
  local repo_root=$(get_repo_root)
  local output_file="$OUTPUT_DIR/configurations.md"

  {
    echo "# Configuration Documentation"
    echo ""
    echo "Auto-generated documentation for all configuration files."
    echo ""
    echo "## Configuration Categories"
    echo ""

    # Read categories from CATEGORIES.yaml if available
    local categories_file="$repo_root/.config/CATEGORIES.yaml"
    if [[ -f "$categories_file" ]]; then
      echo "This project uses a structured configuration system with specialized agents for different config categories."
      echo ""
      echo "### Available Categories"
      echo ""
      echo "| Category | Description | Primary Agent |"
      echo "|----------|-------------|---------------|"

      # Extract category information (simple parsing)
      grep -E "^[a-z_]+:$" "$categories_file" | sed 's/:$//' | while read -r category; do
        local desc=$(sed -n "/^$category:/,/^description:/p" "$categories_file" | grep "description:" | sed 's/.*: //g' | head -1)
        local agent=$(sed -n "/^$category:/,/^primary_agent:/p" "$categories_file" | grep "primary_agent:" | sed 's/.*: //g' | head -1)
        printf "| %-20s | %-40s | %-15s |\n" "$category" "$desc" "$agent"
      done
      echo ""
    fi

    echo "## Configuration Files"
    echo ""

    # Document all config files
    find "$repo_root/.config" -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.toml" -o -name "*.conf" -o -name "*.lua" -o -name ".*rc" \) | sort | while read -r config; do
      local config_name=$(basename "$config")
      local config_path="${config#$repo_root/}"
      local config_type="${config##*.}"

      echo "### $config_name"
      echo ""
      echo "**Path:** \`$config_path\`"
      echo "**Type:** $config_type"
      echo ""

      # Extract inline comments/descriptions
      if [[ "$config_type" == "yaml" || "$config_type" == "yml" ]]; then
        local desc=$(grep "^#.*:" "$config" 2>/dev/null | head -5)
        if [[ -n "$desc" ]]; then
          echo "**Description:**"
          echo ""
          echo "$desc" | sed 's/^# //g'
          echo ""
        fi
      fi

      echo "---"
      echo ""
    done
  } > "$output_file"

  log_success "Configuration documentation generated: $output_file"
}

# Generate workflow documentation
generate_workflow_docs() {
  log_doc "Generating workflow documentation..."

  # Uses prompt-engineer agent for workflow documentation
  local repo_root=$(get_repo_root)
  local output_file="$OUTPUT_DIR/workflows.md"

  {
    echo "# Workflow Documentation"
    echo ""
    echo "Auto-generated documentation for development workflows and processes."
    echo ""
    echo "## Flow Commands"
    echo ""

    # Document flow commands
    local flow_dir="$repo_root/.claude/commands/flow"
    if [[ -d "$flow_dir" ]]; then
      echo "Available flow commands for PRD-driven development:"
      echo ""

      for flow_file in "$flow_dir"/*.md; do
        if [[ -f "$flow_file" ]]; then
          local flow_name=$(basename "$flow_file" .md)
          local description=$(grep "^description:" "$flow_file" | head -1 | sed 's/description: //g')

          echo "### /flow:$flow_name"
          echo ""
          if [[ -n "$description" ]]; then
            echo "$description"
            echo ""
          fi

          # Extract key steps from the flow command
          echo "**Key Steps:**"
          echo ""
          grep -E "^#{1,3}\s+" "$flow_file" | head -10 | sed 's/^//g' | sed 's/^/  /g'
          echo ""

          echo "---"
          echo ""
        fi
      done
    fi

    echo "## Agent Skills"
    echo ""

    # Document available skills
    local skills_dir="$repo_root/.claude/skills"
    if [[ -d "$skills_dir" ]]; then
      echo "Available agent skills for specialized tasks:"
      echo ""

      for skill_file in "$skills_dir"/*.md; do
        if [[ -f "$skill_file" ]]; then
          local skill_name=$(basename "$skill_file" .md)
          local description=$(grep "^description:" "$skill_file" | head -1 | sed 's/description: //g')

          printf "**%s** - %s\n\n" "$skill_name" "$description"
        fi
      done
    fi

    echo "## Development Workflow"
    echo ""
    echo "1. Create PRD: \`/flow:plan\`"
    echo "2. Generate tasks: \`/flow:generate-tasks\`"
    echo "3. Implement tasks: \`/flow:implement\`"
    echo "4. Finalize: \`/flow:cleanup\`"
    echo "5. View summary: \`/flow:summary\`"
    echo ""

  } > "$output_file"

  log_success "Workflow documentation generated: $output_file"
}

# Generate README documentation
generate_readme_docs() {
  log_doc "Generating README documentation..."

  local repo_root=$(get_repo_root)
  local output_file="$OUTPUT_DIR/README.md"

  {
    echo "# Dotfiles Documentation"
    echo ""
    echo "Auto-generated documentation for the dotfiles project."
    echo ""
    echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "---"
    echo ""
    echo "## Documentation Index"
    echo ""
    echo "- [API Documentation](api.md) - Script and tool APIs"
    echo "- [Configurations](configurations.md) - Configuration file reference"
    echo "- [Workflows](workflows.md) - Development workflows and processes"
    echo ""
    echo "---"
    echo ""
    echo "## Quick Links"
    echo ""
    echo "### Scripts"
    echo ""
    find "$repo_root/scripts" -type f -executable | sort | while read -r script; do
      local script_name=$(basename "$script")
      local script_path="${script#$repo_root/}"
      echo "- [$script_name]($script_path)"
    done
    echo ""
    echo "### Configurations"
    echo ""
    find "$repo_root/.config" -maxdepth 1 -type d | sort | while read -r config; do
      local config_name=$(basename "$config")
      if [[ "$config_name" != "." && "$config_name" != ".config" ]]; then
        echo "- [$config_name]($config_path)"
      fi
    done
    echo ""

  } > "$output_file"

  log_success "README documentation generated: $output_file"
}

# Main function
main() {
  local repo_root=$(get_repo_root)

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Auto-Generated Documentation System"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Repository: $repo_root"
  echo "Output: $OUTPUT_DIR"
  echo "Type: $DOC_TYPE"
  echo ""

  # Setup output directory
  setup_output_dir

  # Generate documentation based on type
  case "$DOC_TYPE" in
    api)
      generate_api_docs
      ;;
    config)
      generate_config_docs
      ;;
    workflow)
      generate_workflow_docs
      ;;
    all)
      generate_api_docs
      generate_config_docs
      generate_workflow_docs
      generate_readme_docs
      ;;
    *)
      log_warning "Unknown documentation type: $DOC_TYPE"
      echo "Valid types: api, config, workflow, all"
      exit 1
      ;;
  esac

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log_success "Documentation generation complete!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Generated files in $OUTPUT_DIR:"
  ls -la "$OUTPUT_DIR"/*.md 2>/dev/null | awk '{print "  " $NF}'
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
