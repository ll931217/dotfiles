#!/usr/bin/env bash
#
# Install script for baoge-hooks plugin
# Delegates to the plugin's install.sh script
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/../plugins/baoge-hooks"

# Source install-lib for logging functions
if [[ -f "$SCRIPT_DIR/install-lib.sh" ]]; then
    source "$SCRIPT_DIR/install-lib.sh"
else
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

# Main installation
main() {
    log "Installing Baoge Hooks plugin..."

    # Check if plugin directory exists
    if [[ ! -d "$PLUGIN_DIR" ]]; then
        error "Plugin directory not found: $PLUGIN_DIR"
        return 1
    fi

    # Check if plugin install.sh exists
    if [[ ! -f "$PLUGIN_DIR/install.sh" ]]; then
        error "Plugin install script not found: $PLUGIN_DIR/install.sh"
        return 1
    fi

    # Propagate --dry-run flag if set
    local install_args=()
    if [[ $DRY_RUN == true ]]; then
        install_args+=(--dry-run)
    fi

    # Propagate --verbose flag if set
    if [[ $VERBOSE == true ]]; then
        install_args+=(--verbose)
    fi

    # Run the plugin install script
    bash "$PLUGIN_DIR/install.sh" "${install_args[@]}"

    success "Baoge Hooks plugin installed successfully!"
}

# Run main function
main "$@"
