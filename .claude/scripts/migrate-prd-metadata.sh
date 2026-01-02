#!/bin/bash

# Migrate existing PRDs to include YAML frontmatter with git context
# This script adds metadata frontmatter to all existing PRD files that don't have it
# Also adds changelog section for tracking PRD versions
# Usage: .claude/scripts/migrate-prd-metadata.sh

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Check if in a git repository
if [ -z "$REPO_ROOT" ]; then
  echo -e "${RED}Error: Not in a git repository${NC}"
  exit 1
fi

# Flow directory path (can be absolute or relative to repo root)
FLOW_DIR="$REPO_ROOT/.flow"

# Check if flow directory exists
if [ ! -d "$FLOW_DIR" ]; then
  echo -e "${YELLOW}Warning: /.flow directory not found at $FLOW_DIR${NC}"
  echo "Creating /.flow directory..."
  mkdir -p "$FLOW_DIR"
fi

echo "Migrating PRDs in: $FLOW_DIR"
echo "Repository root: $REPO_ROOT"
echo ""

# Counters
MIGRATED=0
SKIPPED=0
ERRORS=0

# Find all PRD files (not history files)
find "$FLOW_DIR" -name "prd-*-v*.md" ! -name "*-history.md" -type f 2>/dev/null | sort | while read -r prd_file; do
  echo "Processing: $(basename "$prd_file")"

  # Check if already has frontmatter (YAML starts with ---)
  if head -1 "$prd_file" | grep -q "^---$"; then
    echo -e "  ${GREEN}✓${NC} Already has frontmatter, skipping"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Extract version and feature name from filename
  filename=$(basename "$prd_file")

  # Parse filename: prd-feature-name-vN.md
  if [[ ! $filename =~ ^prd-(.+)-v([0-9]+)\.md$ ]]; then
    echo -e "  ${YELLOW}⚠${NC}  Filename doesn't match expected pattern, skipping"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  feature="${BASH_REMATCH[1]}"
  version="v${BASH_REMATCH[2]}"

  # Normalize feature name (replace hyphens with spaces for display, but keep original)
  feature_display=$(echo "$feature" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')

  # Get file metadata
  if stat --version &>/dev/null; then
    # GNU stat (Linux)
    created_timestamp=$(stat -c '%W' "$prd_file" 2>/dev/null || stat -c '%Y' "$prd_file")
    modified_timestamp=$(stat -c '%Y' "$prd_file")
  else
    # BSD stat (macOS)
    created_timestamp=$(stat -f '%B' "$prd_file" 2>/dev/null || stat -f '%m' "$prd_file")
    modified_timestamp=$(stat -f '%m' "$prd_file")
  fi

  # Convert to ISO 8601 format
  created_date=$(date -u -d @"$created_timestamp" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -r "$created_timestamp" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")
  modified_date=$(date -u -d @"$modified_timestamp" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -r "$modified_timestamp" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Try to extract commit SHA and author from git history
  commit_sha=$(git log --diff-filter=A --follow --format="%H" -- "$prd_file" 2>/dev/null | head -1)
  if [ -z "$commit_sha" ]; then
    commit_sha=$(git log -1 --format="%H" 2>/dev/null || echo "unknown")
  fi

  author=$(git log --diff-filter=A --follow --format="%an <%ae>" -- "$prd_file" 2>/dev/null | head -1)
  if [ -z "$author" ]; then
    author=$(git log -1 --format="%an <%ae>" 2>/dev/null || echo "Unknown")
  fi

  # Determine branch type from current branch
  current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
  case "$current_branch" in
    main|master) branch_type="main" ;;
    develop|dev) branch_type="develop" ;;
    feature/*) branch_type="feature" ;;
    bugfix/*|fix/*) branch_type="bugfix" ;;
    hotfix/*) branch_type="hotfix" ;;
    *) branch_type="other" ;;
  esac

  # Check if in worktree
  git_dir=$(git rev-parse --git-dir 2>/dev/null)
  git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)
  if [ "$git_dir" != "$git_common_dir" ]; then
    is_worktree="true"
    worktree_name=$(echo "$current_branch" | sed 's|/|-|g')
    worktree_path="$git_dir"
  else
    is_worktree="false"
    worktree_name="main"
    worktree_path=""
  fi

  # Read original content
  original_content=$(cat "$prd_file")

  # Create temp file with new frontmatter
  temp_file=$(mktemp)

  cat > "$temp_file" <<EOF
---
prd:
  version: $version
  feature_name: $feature
  status: approved
git:
  branch: $current_branch
  branch_type: $branch_type
  created_at_commit: $commit_sha
  updated_at_commit: $commit_sha
worktree:
  is_worktree: $is_worktree
  name: $worktree_name
  path: $worktree_path
  repo_root: $REPO_ROOT
metadata:
  created_at: $created_date
  updated_at: $modified_date
  created_by: $author
  filename: $filename
beads:
  related_issues: []
  related_epics: []
---

$original_content

## Changelog

| Version | Date             | Summary of Changes |
| ------- | ---------------- | ------------------- |
| $version | $(date -u +"%Y-%m-%d %H:%M") | Initial migration |
EOF

  # Replace original file with migrated version
  mv "$temp_file" "$prd_file"

  echo -e "  ${GREEN}✓${NC} Migrated (branch: $current_branch, version: $version)"
  MIGRATED=$((MIGRATED + 1))
done

echo ""
echo "Migration complete!"
echo "- Migrated: $MIGRATED files"
echo "- Skipped: $SKIPPED files (already have frontmatter or invalid filename)"
echo ""
echo "Note: Migrated PRDs now include:"
echo "  - YAML frontmatter with git context (branch, worktree, etc.)"
echo "  - Changelog section at bottom for tracking version history"
echo "  - Single-file approach: version tracked in frontmatter (not filename)"
echo ""
echo "Migrated PRDs have branch info set to the current branch."
echo "If a PRD was created in a different branch, you may need to update the frontmatter manually."
