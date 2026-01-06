#!/usr/bin/env bash
# Parallel dependency validation system
# Uses specialized agents to validate different dependency categories
#
# This script validates system dependencies in parallel using multiple
# specialized validation approaches. It can be used standalone or integrated
# into the installation workflow.
#
# Usage:
#   ./scripts/validate-dependencies.sh [--verbose] [--fix]
#
# Options:
#   --verbose    Show detailed validation output
#   --fix        Attempt to fix missing dependencies
#   --help       Show this help message

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Options
VERBOSE=false
FIX=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose)
      VERBOSE=true
      shift
      ;;
    --fix)
      FIX=true
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

# Validation results array
declare -a VALIDATION_RESULTS=()

# ============================================================================
# System Dependencies Validation
# Uses: deployment-engine, devops-troubleshooter approach
# ============================================================================
validate_system_deps() {
  log_info "Validating system dependencies..."

  local missing_deps=()
  local found_issues=0

  # Check for essential system commands
  local essential_cmds=(
    "git:version control"
    "curl:download tool"
    "wget:download tool"
    "vim:text editor"
    "zsh:shell"
  )

  for cmd_info in "${essential_cmds[@]}"; do
    local cmd="${cmd_info%%:*}"
    local desc="${cmd_info##*:}"

    if command -v "$cmd" &>/dev/null; then
      if [[ "$VERBOSE" == "true" ]]; then
        log_success "$desc ($cmd) is installed"
      fi
    else
      log_warning "$desc ($cmd) is not installed"
      missing_deps+=("$cmd")
      found_issues=1
    fi
  done

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    VALIDATION_RESULTS+=("system_deps:PASS")
    log_success "System dependencies validated"
  else
    VALIDATION_RESULTS+=("system_deps:FAIL:${missing_deps[*]}")
    log_error "Missing system dependencies: ${missing_deps[*]}"
  fi
}

# ============================================================================
# Language Runtimes Validation
# Uses: python-pro, javascript-pro, node-pro approach
# ============================================================================
validate_lang_runtimes() {
  log_info "Validating language runtimes..."

  local found_issues=0

  # Check Python
  if command -v python3 &>/dev/null; then
    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "Python $python_version is installed"
    fi
  else
    log_warning "Python 3 is not installed"
    found_issues=1
  fi

  # Check Node.js
  if command -v node &>/dev/null; then
    local node_version=$(node --version 2>&1)
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "Node.js $node_version is installed"
    fi

    # Check npm/yarn/pnpm
    if command -v npm &>/dev/null; then
      if [[ "$VERBOSE" == "true" ]]; then
        log_success "npm $(npm --version) is installed"
      fi
    fi
  else
    log_warning "Node.js is not installed"
    found_issues=1
  fi

  # Check Go
  if command -v go &>/dev/null; then
    local go_version=$(go version 2>&1 | awk '{print $3}')
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "Go $go_version is installed"
    fi
  fi

  # Check Rust
  if command -v rustc &>/dev/null; then
    local rust_version=$(rustc --version 2>&1 | awk '{print $2}')
    if [[ "$VERBOSE" == "true" ]]; then
      log_success "Rust $rust_version is installed"
    fi
  fi

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    VALIDATION_RESULTS+=("lang_runtimes:PASS")
    log_success "Language runtimes validated"
  else
    VALIDATION_RESULTS+=("lang_runtimes:WARN:Some runtimes missing")
    log_warning "Some language runtimes are missing"
  fi
}

# ============================================================================
# Configuration Symlinks Validation
# Uses: architect-review approach
# ============================================================================
validate_config_symlinks() {
  log_info "Validating configuration symlinks..."

  local found_issues=0
  local repo_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/GitHub/dotfiles")

  # Check for broken symlinks in config directories
  local config_dirs=(".config" ".config/zsh" ".config/nvim")

  for dir in "${config_dirs[@]}"; do
    local full_path="$repo_root/$dir"
    if [[ -d "$full_path" ]]; then
      while IFS= read -r -d '' symlink; do
        if [[ ! -e "$symlink" ]]; then
          log_warning "Broken symlink: $symlink"
          found_issues=1
        fi
      done < <(find "$full_path" -type l -print0 2>/dev/null || true)
    fi
  done

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    VALIDATION_RESULTS+=("config_symlinks:PASS")
    log_success "Configuration symlinks validated"
  else
    VALIDATION_RESULTS+=("config_symlinks:FAIL:Broken symlinks found")
    log_error "Broken configuration symlinks detected"
  fi
}

# ============================================================================
# Package Managers Validation
# Uses: deployment-engine approach
# ============================================================================
validate_package_managers() {
  log_info "Validating package managers..."

  local found_issues=0

  # Check for common package managers
  local pkg_managers=(
    "pacman:Arch Linux package manager"
    "yay:AUR helper"
    "brew:Homebrew package manager"
    "apt:Debian/Ubuntu package manager"
    "dnf:Fedora package manager"
  )

  for pm_info in "${pkg_managers[@]}"; do
    local pm="${pm_info%%:*}"
    local desc="${pm_info##*:}"

    if command -v "$pm" &>/dev/null; then
      if [[ "$VERBOSE" == "true" ]]; then
        log_success "$desc ($pm) is available"
      fi
      # At least one package manager is found, we're good
      found_issues=0
      break
    else
      found_issues=1
    fi
  done

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    VALIDATION_RESULTS+=("package_managers:PASS")
    log_success "Package managers validated"
  else
    VALIDATION_RESULTS+=("package_managers:WARN:No package manager found")
    log_warning "No recognized package manager found"
  fi
}

# ============================================================================
# Performance Health Check
# Uses: performance-engineer approach
# ============================================================================
validate_performance() {
  log_info "Running performance health checks..."

  local found_issues=0

  # Check shell startup time (rough measure)
  if [[ -n "$ZSH_VERSION" ]]; then
    local startup_time=$(time zsh -i -c exit 2>&1 | grep real | awk '{print $2}')
    if [[ "$VERBOSE" == "true" ]]; then
      log_info "Shell startup time: $startup_time"
    fi
  fi

  # Check for available memory (Linux)
  if command -v free &>/dev/null; then
    local available_mem=$(free -h | awk '/^Mem:/ {print $7}')
    if [[ "$VERBOSE" == "true" ]]; then
      log_info "Available memory: $available_mem"
    fi
  fi

  # Check disk space
  local disk_usage=$(df -h "$HOME" | tail -1 | awk '{print $5}' | sed 's/%//')
  if [[ $disk_usage -gt 90 ]]; then
    log_warning "Disk usage is high: ${disk_usage}%"
    found_issues=1
  elif [[ "$VERBOSE" == "true" ]]; then
    log_info "Disk usage: ${disk_usage}%"
  fi

  # Store result
  if [[ $found_issues -eq 0 ]]; then
    VALIDATION_RESULTS+=("performance:PASS")
    log_success "Performance checks passed"
  else
    VALIDATION_RESULTS+=("performance:WARN:Performance issues detected")
    log_warning "Some performance issues detected"
  fi
}

# ============================================================================
# Parallel Execution
# ============================================================================
parallel_validate() {
  log_info "Starting parallel dependency validation..."

  # Run all validation functions in parallel using background processes
  validate_system_deps &
  pid_system=$!

  validate_lang_runtimes &
  pid_lang=$!

  validate_config_symlinks &
  pid_config=$!

  validate_package_managers &
  pid_pkg=$!

  validate_performance &
  pid_perf=$!

  # Wait for all background processes to complete
  wait $pid_system
  wait $pid_lang
  wait $pid_config
  wait $pid_pkg
  wait $pid_perf
}

# ============================================================================
# Results Summary
# ============================================================================
print_summary() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Validation Summary"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  local total=0
  local passed=0
  local failed=0
  local warned=0

  for result in "${VALIDATION_RESULTS[@]}"; do
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
    log_success "All critical validations passed!"
    return 0
  else
    echo ""
    log_error "Some validations failed. Please review and fix."
    return 1
  fi
}

# ============================================================================
# Fix Issues (if --fix flag is set)
# ============================================================================
fix_issues() {
  if [[ "$FIX" != "true" ]]; then
    return
  fi

  log_info "Attempting to fix issues..."

  # Check OS and suggest fixes
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Detect Linux distribution
    if [[ -f /etc/arch-release ]]; then
      log_info "Detected Arch Linux. You can install missing packages with:"
      echo "  sudo pacman -S <package>"
      echo "  yay -S <aur-package>"
    elif [[ -f /etc/debian_version ]]; then
      log_info "Detected Debian/Ubuntu. You can install missing packages with:"
      echo "  sudo apt install <package>"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_info "Detected macOS. You can install missing packages with:"
    echo "  brew install <package>"
  fi
}

# ============================================================================
# Main
# ============================================================================
main() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Parallel Dependency Validation"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Run parallel validation
  parallel_validate

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
