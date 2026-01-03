#!/usr/bin/env bash
#
# Install script for baoge-hooks plugin
# Copies scripts to ~/.scripts/opencode/ and registers the plugin in Claude Code settings
#

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_NAME="baoge-hooks"
SCRIPTS_SOURCE="$SCRIPT_DIR/scripts"
SCRIPTS_TARGET="$HOME/.scripts/opencode"
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
SKIP_HOOKS=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --verbose) VERBOSE=true ;;
        --skip-hooks) SKIP_HOOKS=true ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Preview changes without executing"
            echo "  --verbose     Show detailed output"
            echo "  --skip-hooks  Skip hook registration in settings.json"
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
# INSTALLATION FUNCTIONS
# ============================================================================

# Create target directory and copy scripts
install_scripts() {
    log "Installing hook scripts to $SCRIPTS_TARGET..."

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would create directory: $SCRIPTS_TARGET"
        log "[DRY RUN] Would copy scripts from $SCRIPTS_SOURCE"
        for script in "$SCRIPTS_SOURCE"/*.sh; do
            if [[ -f "$script" ]]; then
                local script_name
                script_name=$(basename "$script")
                log "[DRY RUN] Would copy: $script_name"
                log "[DRY RUN] Would set executable permissions"
            fi
        done
        return 0
    fi

    # Create target directory
    mkdir -p "$SCRIPTS_TARGET"

    # Check for existing scripts
    local existing_scripts=()
    for script in "$SCRIPTS_SOURCE"/*.sh; do
        if [[ -f "$script" ]]; then
            local script_name
            script_name=$(basename "$script")
            if [[ -f "$SCRIPTS_TARGET/$script_name" ]]; then
                existing_scripts+=("$script_name")
            fi
        fi
    done

    # Warn about existing scripts
    if [[ ${#existing_scripts[@]} -gt 0 ]]; then
        warn "Existing scripts found in $SCRIPTS_TARGET:"
        for script in "${existing_scripts[@]}"; do
            warn "  - $script"
        done
        echo ""
        warn "These will be overwritten."
        echo ""
    fi

    # Copy all scripts
    local copied=0
    for script in "$SCRIPTS_SOURCE"/*.sh; do
        if [[ -f "$script" ]]; then
            local script_name
            script_name=$(basename "$script")
            cp "$script" "$SCRIPTS_TARGET/$script_name"
            chmod +x "$SCRIPTS_TARGET/$script_name"
            ((copied++))

            if [[ $VERBOSE == true ]]; then
                log "Copied: $script_name"
            fi
        fi
    done

    success "Installed $copied script(s) to $SCRIPTS_TARGET"
}

# Register hooks in Claude Code settings
register_hooks() {
    if [[ $SKIP_HOOKS == true ]]; then
        log "Skipping hook registration (--skip-hooks flag)"
        return 0
    fi

    log "Registering hooks in Claude Code settings..."

    if [[ ! -f "$SETTINGS_FILE" ]]; then
        error "Settings file not found: $SETTINGS_FILE"
        error "Please ensure Claude Code is installed and configured."
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would register hooks in $SETTINGS_FILE"
        log "[DRY RUN] Would backup settings file first"
        return 0
    fi

    # Backup settings file
    local backup_file
    backup_file="${SETTINGS_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    cp "$SETTINGS_FILE" "$backup_file"
    log "Backed up settings to: $backup_file"

    # Read plugin.json to get hooks
    local plugin_json
    plugin_json="$SCRIPT_DIR/plugin.json"

    if [[ ! -f "$plugin_json" ]]; then
        error "plugin.json not found: $plugin_json"
        return 1
    fi

    # Check if jq is available
    if ! command -v jq &>/dev/null; then
        error "jq is required but not installed."
        error "Please install jq: pacman -S jq"
        return 1
    fi

    # Merge hooks into settings.json
    local temp_file
    temp_file=$(mktemp)

    # Extract hooks from plugin.json and merge with existing settings
    jq -s '
        .[0] as $settings |
        .[1].hooks as $plugin_hooks |
        ($settings.hooks // {}) as $existing_hooks |
        $settings |
        .hooks = ($existing_hooks + $plugin_hooks |
            to_entries |
            group_by(.key) |
            map({
                key: .[0].key,
                value: (map(.value) | add | unique_by(.matcher // ""))
            }) |
            from_entries)
    ' "$SETTINGS_FILE" "$plugin_json" > "$temp_file"

    # Verify the merge was successful
    if ! jq empty "$temp_file" 2>/dev/null; then
        error "Failed to merge hooks - invalid JSON generated"
        rm -f "$temp_file"
        return 1
    fi

    # Replace original settings file
    mv "$temp_file" "$SETTINGS_FILE"

    success "Registered hooks in $SETTINGS_FILE"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."

    local errors=0

    # Check scripts directory
    if [[ ! -d "$SCRIPTS_TARGET" ]]; then
        error "Scripts directory not found: $SCRIPTS_TARGET"
        ((errors++))
    else
        # Check for each script
        local expected_scripts=(
            "enhanced-notify.sh"
            "danger-alert.sh"
            "context-monitor.sh"
            "tool-tracker.sh"
            "session-start-notify.sh"
            "session-end-notify.sh"
            "stop-notify.sh"
        )

        for script in "${expected_scripts[@]}"; do
            if [[ ! -f "$SCRIPTS_TARGET/$script" ]]; then
                error "Missing script: $script"
                ((errors++))
            elif [[ ! -x "$SCRIPTS_TARGET/$script" ]]; then
                error "Script not executable: $script"
                ((errors++))
            fi
        done
    fi

    if [[ $errors -eq 0 ]]; then
        success "All scripts verified"
    else
        error "Verification failed with $errors error(s)"
        return 1
    fi
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

main() {
    echo ""
    echo "=== Baoge Hooks Plugin Installation ==="
    echo ""

    log "Plugin: $PLUGIN_NAME"
    log "Source: $SCRIPT_DIR"
    log "Target: $SCRIPTS_TARGET"
    echo ""

    if [[ $DRY_RUN == true ]]; then
        warn "DRY RUN MODE - No changes will be made"
        echo ""
    fi

    # Step 1: Install scripts
    install_scripts
    echo ""

    # Step 2: Register hooks
    if [[ $SKIP_HOOKS == false ]]; then
        register_hooks
        echo ""
    fi

    # Step 3: Verify installation
    if [[ $DRY_RUN == false ]]; then
        verify_installation
        echo ""
    fi

    # Summary
    echo ""
    echo "=== Installation Summary ==="
    echo ""
    success "Baoge Hooks Plugin installed successfully!"
    echo ""
    echo "Scripts installed to: $SCRIPTS_TARGET"
    echo "Hooks registered in: $SETTINGS_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Restart Claude Code"
    echo "  2. Hooks will be automatically activated"
    echo ""
    echo "To uninstall, run: $SCRIPT_DIR/uninstall.sh"
    echo ""
}

# Run main installation
main "$@"
