#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"

DRY_RUN=false
APPLY=true
FORCE=false

log() {
    printf '[chezmoi] %s\n' "$*" >&2
}

fail() {
    printf '[chezmoi] ERROR: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: bootstrap/install.sh [OPTIONS]

Bootstrap chezmoi from this repository and apply the managed home state.

Options:
  --dry-run    Render and show changes without modifying the home directory
  --no-apply   Initialize chezmoi and show the diff, but do not apply it
  --force      Apply without interactive conflict prompts
  -h, --help   Show this help
EOF
}

install_chezmoi() {
    if command -v chezmoi >/dev/null 2>&1; then
        return 0
    fi

    log "chezmoi is not installed; installing a user-local binary"
    local bin_dir="$HOME/.local/bin"
    mkdir -p -- "$bin_dir"

    if command -v brew >/dev/null 2>&1; then
        brew install chezmoi
        return 0
    fi

    if command -v curl >/dev/null 2>&1; then
        curl --fail --location --silent --show-error \
            https://get.chezmoi.io | sh -s -- -b "$bin_dir"
        export PATH="$bin_dir:$PATH"
        return 0
    fi

    fail "chezmoi is missing and neither brew nor curl is available"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            APPLY=false
            shift
            ;;
        --no-apply)
            APPLY=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "unknown option: $1"
            ;;
    esac
done

install_chezmoi
command -v chezmoi >/dev/null 2>&1 || fail "chezmoi installation did not provide an executable"

CHEZMOI=(chezmoi --source "$REPO_ROOT" --no-pager)
"${CHEZMOI[@]}" init --guess-repo-url=false

log "Reviewing managed changes"
if [[ "$DRY_RUN" == true ]]; then
    "${CHEZMOI[@]}" diff --dry-run
    exit 0
fi

"${CHEZMOI[@]}" diff

if [[ "$APPLY" != true ]]; then
    log "Initialization complete; apply skipped by request"
    exit 0
fi

if [[ "$FORCE" == true ]]; then
    "${CHEZMOI[@]}" apply --force
else
    if [[ ! -t 0 ]]; then
        fail "refusing noninteractive apply without --force"
    fi
    read -r -p "Apply these chezmoi changes? [y/N] " answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        log "Apply cancelled"
        exit 0
    fi
    "${CHEZMOI[@]}" apply
fi

log "Apply complete"
