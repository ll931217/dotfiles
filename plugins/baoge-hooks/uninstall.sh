#!/usr/bin/env bash
#
# Uninstall script for baoge-hooks plugin
# Removes scripts and unregisters the plugin from Claude Code settings
#

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="baoge-hooks"
SCRIPTS_TARGET="$HOME/.claude/scripts/baoge-hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"

# Color codes (import from install-lib if available)
if [[ -f "$SCRIPT_DIR/../../scripts/install-lib.sh" ]]; then
    source "$SCRIPT_DIR/../../scripts/install-lib.sh"
else
    # Fallback colors
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    log() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
    success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
    warn() { echo -e "${YELLOW}[WARNING]${NC} $*" >&2; }
    error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
fi

# Parse arguments
DRY_RUN=false
VERBOSE=false
FORCE=false
SKIP_HOOKS=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --verbose) VERBOSE=true ;;
        --force) FORCE=true ;;
        --skip-hooks) SKIP_HOOKS=true ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Preview changes without executing"
            echo "  --verbose     Show detailed output"
            echo "  --force       Skip confirmation prompts"
            echo "  --skip-hooks  Skip hook removal from settings.json"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# ============================================================================
# UNINSTALLATION FUNCTIONS
# ============================================================================

# Remove hooks from Claude Code settings
remove_hooks() {
    if [[ $SKIP_HOOKS == true ]]; then
        log "Skipping hook removal (--skip-hooks flag)"
        return 0
    fi

    log "Removing hooks from Claude Code settings..."

    if [[ ! -f "$SETTINGS_FILE" ]]; then
        warn "Settings file not found: $SETTINGS_FILE"
        warn "Skipping hook removal"
        return 0
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would remove hooks from $SETTINGS_FILE"
        log "[DRY RUN] Would backup settings file first"
        return 0
    fi

    # Backup settings file
    local backup_file
    backup_file="${SETTINGS_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    cp "$SETTINGS_FILE" "$backup_file"
    log "Backed up settings to: $backup_file"

    # Check if jq is available
    if ! command -v jq &>/dev/null; then
        warn "jq is not installed. Hooks will not be removed from settings.json"
        warn "To remove hooks manually, edit $SETTINGS_FILE"
        return 0
    fi

    # Read plugin.json to get hooks to remove
    local plugin_json
    plugin_json="$SCRIPT_DIR/plugin.json"

    if [[ ! -f "$plugin_json" ]]; then
        warn "plugin.json not found: $plugin_json"
        warn "Skipping hook removal"
        return 0
    fi

    # Extract hook commands from plugin.json
    local hook_commands
    hook_commands=$(jq -r '
        .hooks |
        to_entries[] |
        .value[] |
        .hooks[] |
        select(.command != null) |
        .command
    ' "$plugin_json" 2>/dev/null || echo "")

    if [[ -z "$hook_commands" ]]; then
        warn "No hooks found in plugin.json"
        return 0
    fi

    # Remove hooks that match our plugin's commands
    local temp_file
    temp_file=$(mktemp)

    # Build jq filter to remove our hooks
    local jq_filter
    jq_filter='del(
        .hooks[][].hooks[] |
        select(
            .command == "bash ~/.claude/scripts/enhanced-notify.sh" or
            .command == "bash ~/.claude/scripts/danger-alert.sh" or
            .command == "bash ~/.claude/scripts/context-monitor.sh" or
            .command == "bash ~/.claude/scripts/tool-tracker.sh" or
            .command == "bash ~/.claude/scripts/session-start-notify.sh" or
            .command == "bash ~/.claude/scripts/session-end-notify.sh" or
            .command == "bash ~/.claude/scripts/stop-notify.sh" or
            .command == "bd prime"
        )
    )'

    jq "$jq_filter" "$SETTINGS_FILE" > "$temp_file" 2>/dev/null || true

    # Clean up empty hook arrays
    local clean_file
    clean_file=$(mktemp)
    jq 'del(.hooks[][] | select(. == []))' "$temp_file" > "$clean_file" 2>/dev/null || true

    # Verify the result is valid JSON
    if jq empty "$clean_file" 2>/dev/null; then
        mv "$clean_file" "$SETTINGS_FILE"
        rm -f "$temp_file"
        success "Removed hooks from $SETTINGS_FILE"
    else
        warn "Failed to remove hooks - settings file may be corrupted"
        warn "Backup saved at: $backup_file"
        rm -f "$temp_file" "$clean_file"
        return 1
    fi
}

# Remove scripts directory
remove_scripts() {
    log "Removing scripts directory: $SCRIPTS_TARGET"

    if [[ ! -d "$SCRIPTS_TARGET" ]]; then
        warn "Scripts directory not found: $SCRIPTS_TARGET"
        return 0
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would remove directory: $SCRIPTS_TARGET"
        log "[DRY RUN] Would delete all files in directory"
        return 0
    fi

    # List scripts that will be removed
    if [[ $VERBOSE == true ]]; then
        log "Scripts to be removed:"
        ls -la "$SCRIPTS_TARGET" 2>/dev/null || true
        echo ""
    fi

    # Remove directory and all contents
    rm -rf "$SCRIPTS_TARGET"
    success "Removed scripts directory"
}

# Verify cleanup
verify_cleanup() {
    log "Verifying cleanup..."

    local remaining=0

    # Check if scripts directory still exists
    if [[ -d "$SCRIPTS_TARGET" ]]; then
        warn "Scripts directory still exists: $SCRIPTS_TARGET"
        ((remaining++))
    fi

    # Check if hooks are still in settings
    if [[ -f "$SETTINGS_FILE" ]] && command -v jq &>/dev/null; then
        local hooks_remaining
        hooks_remaining=$(jq -r '
            .hooks[][].hooks[] |
            select(.command != null) |
            .command
        ' "$SETTINGS_FILE" 2>/dev/null | grep -c "opencode" || echo "0")

        if [[ $hooks_remaining -gt 0 ]]; then
            warn "Some hooks may still be registered in settings.json"
            ((remaining++))
        fi
    fi

    if [[ $remaining -eq 0 ]]; then
        success "Cleanup verified"
    else
        warn "Cleanup may be incomplete - $remaining issue(s) found"
    fi
}

# ============================================================================
# MAIN UNINSTALLATION FLOW
# ============================================================================

main() {
    echo ""
    echo "=== Baoge Hooks Plugin Uninstallation ==="
    echo ""

    log "Plugin: $PLUGIN_NAME"
    log "Scripts directory: $SCRIPTS_TARGET"
    log "Settings file: $SETTINGS_FILE"
    echo ""

    if [[ $DRY_RUN == true ]]; then
        warn "DRY RUN MODE - No changes will be made"
        echo ""
    fi

    # Confirmation prompt (unless --force)
    if [[ $FORCE == false && $DRY_RUN == false ]]; then
        echo "This will:"
        echo "  - Remove all scripts from: $SCRIPTS_TARGET"
        echo "  - Remove hooks from: $SETTINGS_FILE"
        echo ""
        if ! confirm "Continue with uninstallation?"; then
            log "Uninstall cancelled"
            exit 0
        fi
        echo ""
    fi

    # Step 1: Remove hooks from settings
    if [[ $SKIP_HOOKS == false ]]; then
        remove_hooks
        echo ""
    fi

    # Step 2: Remove scripts directory
    remove_scripts
    echo ""

    # Step 3: Verify cleanup
    if [[ $DRY_RUN == false ]]; then
        verify_cleanup
        echo ""
    fi

    # Summary
    echo ""
    echo "=== Uninstallation Summary ==="
    echo ""
    success "Baoge Hooks Plugin uninstalled successfully!"
    echo ""
    echo "Scripts removed from: $SCRIPTS_TARGET"
    echo "Hooks removed from: $SETTINGS_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Restart Claude Code"
    echo "  2. Hooks will no longer be active"
    echo ""
    echo "To reinstall, run: $SCRIPT_DIR/install.sh"
    echo ""
}

# Run main uninstallation
main "$@"
