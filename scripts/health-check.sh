#!/usr/bin/env bash
# Comprehensive Health Check System
#
# Uses multiple specialized agents to perform comprehensive health checks
# across the dotfiles project.
#
# Usage:
#   ./scripts/health-check.sh [--category <cat>] [--fix] [--verbose]
#
# Options:
#   --category <cat>  Run specific category only (config, performance, security, best_practices)
#   --fix            Attempt to fix issues found
#   --verbose        Show detailed check output
#   --help           Show this help message

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Options
CATEGORY="all"
FIX=false
VERBOSE=false

# Health check results
declare -a CHECK_RESULTS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --category)
      CATEGORY="$2"
      shift 2
      ;;
    --fix)
      FIX=true
      shift
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
  echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[FAIL]${NC} $1"
}

log_health() {
  echo -e "${MAGENTA}[CHECK]${NC} $1"
}

# Get repository root
get_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/GitHub/dotfiles"
}

# ============================================================================
# Configuration Health Checks
# Agent: architect-review
# ============================================================================
check_configuration() {
  log_health "Running configuration health checks..."

  local found_issues=0
  local repo_root=$(get_repo_root)

  # Check 1: Config file syntax validation
  log_info "Validating configuration file syntax..."

  local configs=(
    ".config/alacritty/alacritty.yml:yaml"
    ".config/kitty/kitty.conf:kitty"
    ".config/starship.toml:toml"
    ".config/nvim/init.lua:lua"
  )

  for config_pair in "${configs[@]}"; do
    local config_path="${config_pair%%:*}"
    local config_type="${config_pair##*:}"
    local full_path="$repo_root/$config_path"

    if [[ -f "$full_path" ]]; then
      case "$config_type" in
        yaml)
          if command -v yamllint &>/dev/null; then
            if yamllint "$full_path" &>/dev/null; then
              if [[ "$VERBOSE" == "true" ]]; then
                log_success "$config_path syntax is valid"
              fi
            else
              log_error "$config_path has syntax errors"
              ((found_issues++))
            fi
          fi
          ;;
        toml)
          # Basic TOML validation (check for unmatched brackets/quotes)
          if grep -q '^\[' "$full_path"; then
            local open_brackets=$(grep -o '\[' "$full_path" | wc -l)
            local close_brackets=$(grep -o '\]' "$full_path" | wc -l)
            if [[ $open_brackets -ne $close_brackets ]]; then
              log_error "$config_path has unmatched brackets"
              ((found_issues++))
            fi
          fi
          ;;
        lua)
          # Basic Lua syntax check (check for matching 'end' keywords)
          local functions=$(grep -c 'function ' "$full_path" 2>/dev/null || echo 0)
          local ends=$(grep -c '^end$' "$full_path" 2>/dev/null || echo 0)
          if [[ $functions -ne $ends ]] && [[ "$VERBOSE" == "true" ]]; then
            log_warning "$config_path may have unbalanced function/end blocks"
          fi
          ;;
      esac
    fi
  done

  # Check 2: Broken symlink detection
  log_info "Checking for broken symlinks..."

  local broken_symlinks=$(find "$repo_root/.config" -type l ! -exec test -e {} \; 2>/dev/null | wc -l)

  if [[ $broken_symlinks -gt 0 ]]; then
    log_error "Found $broken_symlinks broken symlinks in .config"
    if [[ "$VERBOSE" == "true" ]]; then
      find "$repo_root/.config" -type l ! -exec test -e {} \; -print 2>/dev/null | while read -r link; do
        echo "  └─ $link -> $(readlink "$link")"
      done
    fi
    ((found_issues++))
  else
    log_success "No broken symlinks found"
  fi

  # Check 3: Deprecated config detection
  log_info "Checking for deprecated configurations..."

  local deprecated_patterns=(
    ".vimrc:Use nvim instead"
    ".bashrc:Use zsh instead"
    "TERMINAL=alacritty:Use kitty or ghostty"
  )

  for pattern in "${deprecated_patterns[@]}"; do
    local search="${pattern%%:*}"
    local reason="${pattern##*:}"

    if grep -r "$search" "$repo_root/.config" &>/dev/null; then
      log_warning "Deprecated pattern found: $search ($reason)"
      ((found_issues++))
    fi
  done

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    CHECK_RESULTS+=("configuration:PASS")
    log_success "Configuration health checks passed"
  else
    CHECK_RESULTS+=("configuration:FAIL:$found_issues issues found")
    log_error "Configuration health checks failed: $found_issues issues"
  fi
}

# ============================================================================
# Performance Health Checks
# Agent: performance-engineer
# ============================================================================
check_performance() {
  log_health "Running performance health checks..."

  local found_issues=0
  local repo_root=$(get_repo_root)

  # Check 1: Shell startup time
  log_info "Checking shell startup time..."

  if [[ -n "$ZSH_VERSION" ]]; then
    local startup_time=$(command time zsh -i -c exit 2>&1 | grep real | awk '{print $2}')
    if [[ "$VERBOSE" == "true" ]]; then
      log_info "Zsh startup time: $startup_time"
    fi

    # Parse startup time (rough check)
    local startup_seconds=$(echo "$startup_time" | sed 's/0m//;s/s//')
    if [[ $(echo "$startup_seconds > 1.0" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
      log_warning "Shell startup time is slow: $startup_time"
      ((found_issues++))
    fi
  fi

  # Check 2: Memory usage patterns
  log_info "Checking memory usage..."

  if command -v free &>/dev/null; then
    local available_mem=$(free -h | awk '/^Mem:/ {print $7}')
    local mem_percent=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')

    if [[ "$VERBOSE" == "true" ]]; then
      log_info "Memory usage: ${mem_percent}% (available: $available_mem)"
    fi

    if [[ $mem_percent -gt 90 ]]; then
      log_warning "High memory usage: ${mem_percent}%"
      ((found_issues++))
    fi
  fi

  # Check 3: Slow config detection (large files)
  log_info "Checking for large configuration files..."

  find "$repo_root/.config" -type f -size +100k 2>/dev/null | while read -r large_file; do
    local file_size=$(du -h "$large_file" | cut -f1)
    log_warning "Large config file: $large_file ($file_size)"
    ((found_issues++))
  done

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    CHECK_RESULTS+=("performance:PASS")
    log_success "Performance health checks passed"
  else
    CHECK_RESULTS+=("performance:WARN:$found_issues performance issues")
    log_warning "Performance health checks: $found_issues issues"
  fi
}

# ============================================================================
# Security Health Checks
# Agent: security-auditor
# ============================================================================
check_security() {
  log_health "Running security health checks..."

  local found_issues=0
  local repo_root=$(get_repo_root)

  # Check 1: Exposed secrets detection
  log_info "Checking for exposed secrets..."

  local secret_patterns=(
    "password.*=.*[^[:space:]]"
    "api_key.*=.*[^[:space:]]"
    "token.*=.*[^[:space:]]"
    "secret.*=.*[^[:space:]]"
    "AKIA[0-9A-Z]{16}"  # AWS access key pattern
  )

  for pattern in "${secret_patterns[@]}"; do
    if grep -r -i "$pattern" "$repo_root/.config" 2>/dev/null | grep -v "example\|sample\|template" | head -1 &>/dev/null; then
      log_warning "Potential secret found matching pattern: $pattern"
      ((found_issues++))
    fi
  done

  # Check 2: Insecure permissions
  log_info "Checking file permissions..."

  # Check for world-writable files
  local world_writable=$(find "$repo_root/.config" -type f -perm -o+w 2>/dev/null | wc -l)

  if [[ $world_writable -gt 0 ]]; then
    log_error "Found $world_writable world-writable files"
    ((found_issues++))
  fi

  # Check for files with executable bit that shouldn't have it
  local unexpected_exec=$(find "$repo_root/.config" -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.toml" -o -name "*.conf" \) -executable 2>/dev/null | wc -l)

  if [[ $unexpected_exec -gt 0 ]]; then
    log_warning "Found $unexpected_exec config files with executable bit"
    ((found_issues++))
  fi

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    CHECK_RESULTS+=("security:PASS")
    log_success "Security health checks passed"
  else
    CHECK_RESULTS+=("security:FAIL:$found_issues security issues")
    log_error "Security health checks failed: $found_issues issues"
  fi
}

# ============================================================================
# Best Practices Health Checks
# Agent: code-reviewer
# ============================================================================
check_best_practices() {
  log_health "Running best practices health checks..."

  local found_issues=0
  local repo_root=$(get_repo_root)

  # Check 1: Code style consistency
  log_info "Checking code style consistency..."

  # Check for trailing whitespace
  local trailing_whitespace=$(grep -r "[[:space:]]$" "$repo_root/scripts" 2>/dev/null | wc -l)

  if [[ $trailing_whitespace -gt 0 ]]; then
    log_warning "Found $trailing_whitespace lines with trailing whitespace in scripts"
    ((found_issues++))
  fi

  # Check 2: Documentation completeness
  log_info "Checking documentation completeness..."

  # Check if scripts have usage information
  local scripts_without_usage=0
  for script in "$repo_root/scripts"/*.sh; do
    if [[ -f "$script" ]]; then
      if ! grep -q "^# Usage:" "$script" 2>/dev/null; then
        ((scripts_without_usage++))
      fi
    fi
  done

  if [[ $scripts_without_usage -gt 0 ]]; then
    log_warning "$scripts_without_usage scripts missing usage documentation"
    ((found_issues++))
  fi

  # Check 3: Test coverage (basic check)
  log_info "Checking test coverage..."

  local test_count=$(find "$repo_root" -name "*test*.sh" -o -name "*_test.lua" 2>/dev/null | wc -l)

  if [[ "$VERBOSE" == "true" ]]; then
    log_info "Found $test_count test files"
  fi

  if [[ $test_count -eq 0 ]]; then
    log_warning "No test files found"
    ((found_issues++))
  fi

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    CHECK_RESULTS+=("best_practices:PASS")
    log_success "Best practices health checks passed"
  else
    CHECK_RESULTS+=("best_practices:WARN:$found_issues practice issues")
    log_warning "Best practices health checks: $found_issues issues"
  fi
}

# ============================================================================
# Fix Issues
# ============================================================================
fix_issues() {
  if [[ "$FIX" != "true" ]]; then
    return
  fi

  log_info "Attempting to fix issues..."

  # Fix trailing whitespace
  log_info "Fixing trailing whitespace..."
  local repo_root=$(get_repo_root)
  find "$repo_root/scripts" -type f -name "*.sh" -exec sed -i 's/[[:space:]]*$//' {} \;

  # Fix world-writable files
  log_info "Fixing world-writable files..."
  find "$repo_root/.config" -type f -perm -o+w -exec chmod o-w {} \;

  log_success "Applied fixes"
}

# ============================================================================
# Results Summary
# ============================================================================
print_summary() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Health Check Summary"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  local total=0
  local passed=0
  local failed=0
  local warned=0

  for result in "${CHECK_RESULTS[@]}"; do
    ((total++))

    local category="${result%%:*}"
    local status="${result#*:}"
    local status_code="${status%%:*}"

    case "$status_code" in
      PASS)
        ((passed++))
        echo -e "${GREEN}✓${NC} $category"
        ;;
      FAIL)
        ((failed++))
        local details="${status##*:}"
        echo -e "${RED}✗${NC} $category: $details"
        ;;
      WARN)
        ((warned++))
        local details="${status##*:}"
        echo -e "${YELLOW}⚠${NC} $category: $details"
        ;;
    esac
  done

  echo ""
  echo "Total: $total | Passed: $passed | Failed: $failed | Warnings: $warned"

  # Overall result
  if [[ $failed -eq 0 ]]; then
    echo ""
    log_success "All critical health checks passed!"
    return 0
  else
    echo ""
    log_error "Some health checks failed. Please review and fix."
    return 1
  fi
}

# ============================================================================
# Main
# ============================================================================
main() {
  local repo_root=$(get_repo_root)

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Comprehensive Health Check System"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Repository: $repo_root"
  echo "Category: $CATEGORY"
  echo ""

  # Run health checks based on category
  case "$CATEGORY" in
    configuration|config)
      check_configuration
      ;;
    performance|perf)
      check_performance
      ;;
    security)
      check_security
      ;;
    best_practices|practices)
      check_best_practices
      ;;
    all)
      check_configuration
      check_performance
      check_security
      check_best_practices
      ;;
    *)
      log_error "Unknown category: $CATEGORY"
      echo "Valid categories: config, performance, security, best_practices, all"
      exit 1
      ;;
  esac

  # Print summary
  print_summary
  local exit_code=$?

  # Attempt fixes if requested
  fix_issues

  exit $exit_code
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
