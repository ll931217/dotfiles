#!/usr/bin/env bash
# Detect git worktree context for /prd:summary command
# Outputs: WORKTREE_MODE, CURRENT_BRANCH, BRANCH_WORKTREES (associative array)

detect_worktree_context() {
  # Check if we're in a worktree using git's built-in detection
  # In a worktree, .git is a file containing "gitdir: <path>"
  # In main repo, .git is a directory
  local is_worktree="false"
  local git_dir

  git_dir=$(git rev-parse --git-dir 2>/dev/null)

  # Check if .git is a file (worktree) or directory (main repo)
  if [[ -f "$git_dir/commondir" ]]; then
    # This is a worktree - commondir file only exists in worktrees
    is_worktree="true"
  fi

  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

  if [ "$is_worktree" = "false" ]; then
    WORKTREE_MODE="multi"

    # Build associative array of worktrees for this branch
    declare -gA BRANCH_WORKTREES
    local wt_key path branch_key branch wt_branch wt_name

    while read -r wt_key path branch_key branch; do
      # Validate porcelain format: "worktree /path branch refs/heads/name"
      [ "$wt_key" != "worktree" ] && continue
      [ "$branch_key" != "branch" ] && continue

      # Extract branch name from worktree
      wt_branch=$(basename "$branch" | sed 's/refs\/heads\///')
      if [ "$wt_branch" = "$CURRENT_BRANCH" ]; then
        # Main directory also counts as a "worktree"
        if [ "$path" = "$(git rev-parse --show-toplevel)" ]; then
          BRANCH_WORKTREES["[main]"]="$path"
        else
          # Get worktree name from path
          wt_name=$(basename "$path" | sed 's/.*\.git\/worktrees\///')
          BRANCH_WORKTREES["$wt_name"]="$path"
        fi
      fi
    done < <(git worktree list --porcelain 2>/dev/null | grep -E "^(worktree|branch)" | paste - -)

    # If no worktrees found for current branch, show only main directory
    if [ ${#BRANCH_WORKTREES[@]} -eq 0 ]; then
      BRANCH_WORKTREES["[main]"]=$(git rev-parse --show-toplevel)
    fi
  else
    # In a worktree - single worktree mode
    WORKTREE_MODE="single"
  fi

  export WORKTREE_MODE CURRENT_BRANCH
}

# If script is executed directly (not sourced), run detection and display results
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  detect_worktree_context
  echo "WORKTREE_MODE=$WORKTREE_MODE"
  echo "CURRENT_BRANCH=$CURRENT_BRANCH"
  if [ "$WORKTREE_MODE" = "multi" ]; then
    echo "BRANCH_WORKTREES:"
    for key in "${!BRANCH_WORKTREES[@]}"; do
      echo "  [$key]=${BRANCH_WORKTREES[$key]}"
    done
  fi
fi
