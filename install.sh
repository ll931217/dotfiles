#!/usr/bin/env bash
#
# Quick start script - legacy wrapper for backward compatibility
# This script forwards to the new modular installation system
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if scripts directory exists
if [[ ! -d "$SCRIPT_DIR/scripts" ]]; then
  echo "Error: scripts directory not found"
  echo "Please make sure you're running this from dotfiles repository root"
  exit 1
fi

# Run new installer, passing through all arguments including --dry-run
exec bash "$SCRIPT_DIR/scripts/install.sh" "$@"
