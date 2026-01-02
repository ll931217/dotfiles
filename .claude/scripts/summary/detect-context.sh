#!/usr/bin/env bash
# Detect git worktree context for /prd:summary command
# Outputs: WORKTREE_MODE, CURRENT_BRANCH, BRANCH_WORKTREES (associative array)

detect_worktree_context() {
  local git_dir git_common_dir is_worktree
  git_dir=$(git rev-parse --git-dir 2>/dev/null)
  git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)
  is_worktree=$([ "$git_dir" != "$git_common_dir" ] && echo "true" || echo "false")

  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

  if [ "$is_worktree" = "false" ]; then
    WORKTREE_MODE="multi"

    # Build associative array of worktrees for this branch
    declare -gA BRANCH_WORKTREES
    local path branch wt_branch wt_name

    while read -r path branch; do
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
