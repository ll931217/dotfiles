#!/bin/bash

# Modern Status Line for Claude Code
# Features: Clean separators, gradient colors, minimal design, professional aesthetic

# Get JSON input
input=$(cat)

# Extract current directory from JSON
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')

# Modern color palette - subtle gradients and professional tones
# Using 256-color mode for better consistency
C_RESET='\033[0m'
C_DIM='\033[2m'
C_BOLD='\033[1m'

# Gradient color scheme (soft, professional)
C_PRIMARY='\033[38;5;111m'      # Soft sky blue
C_SECONDARY='\033[38;5;151m'    # Soft mint green
C_ACCENT='\033[38;5;222m'       # Warm peach
C_WARN='\033[38;5;223m'         # Soft yellow
C_ERROR='\033[38;5;217m'        # Soft red
C_INFO='\033[38;5;147m'         # Periwinkle
C_SUCCESS='\033[38;5;158m'      # Soft green
C_PURPLE='\033[38;5;177m'       # Soft purple
C_ORANGE='\033[38;5;215m'       # Soft orange
C_GRAY='\033[38;5;245m'         # Subtle gray
C_DARK_GRAY='\033[38;5;242m'    # Darker gray for separators

# Modern separators - clean and minimal
SEP_THIN="${C_DARK_GRAY}│${C_RESET}"
SEP_DOT="${C_DARK_GRAY}·${C_RESET}"
SEP_ARROW="${C_DARK_GRAY}→${C_RESET}"
SEP_BULLET="${C_DARK_GRAY}•${C_RESET}"

# Function to create modern progress bar with gradient effect
# Usage: progress_bar <percentage> <width>
# Example: progress_bar 75 10 -> "▓▓▓▓▓▓▓▓░░"
progress_bar() {
    local percentage=$1
    local width=${2:-10}
    local filled=$((width * percentage / 100))
    local empty=$((width - filled))

    # Handle edge cases
    [ $filled -gt $width ] && filled=$width
    [ $filled -lt 0 ] && filled=0
    [ $empty -lt 0 ] && empty=0

    printf '%.*s' "$filled" "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓"
    printf '%.*s' "$empty" "░░░░░░░░░░░░░░░░░░░░░"
}

# Function to get context window with modern display
get_context_bar() {
    local usage_json=$(echo "$input" | jq '.context_window.current_usage // empty')
    local window_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')

    if [ "$usage_json" = "null" ] || [ -z "$usage_json" ] || [ "$window_size" -eq 0 ]; then
        return
    fi

    # Calculate current usage (input + cache creation + cache read)
    local current=$(echo "$usage_json" | jq '.input_tokens + .cache_creation_input_tokens + .cache_read_input_tokens')
    local percentage=$((current * 100 / window_size))

    # Clamp percentage between 0 and 100
    [ $percentage -gt 100 ] && percentage=100
    [ $percentage -lt 0 ] && percentage=0

    # Determine color based on usage (gradient from green to red)
    local color
    if [ $percentage -lt 33 ]; then
        color="$C_SUCCESS"      # Green
    elif [ $percentage -lt 66 ]; then
        color="$C_INFO"         # Blue
    elif [ $percentage -lt 85 ]; then
        color="$C_ORANGE"       # Orange
    else
        color="$C_ERROR"        # Red
    fi

    # Create compact progress bar
    local bar=$(progress_bar "$percentage" 15)

    # Format: ▓▓▓▓░░ 78%
    printf '%s[%s%s%s]%s%d%%%s' "$color" "$C_BOLD" "$bar" "$color" "$C_RESET" "$percentage" "$C_RESET"
}

# Function to get Claude Code session information with modern design
get_claude_session_info() {
    local session_info=""

    # Extract session data from JSON input
    local session_id=$(echo "$input" | jq -r '.session_id // ""')
    local model_name=$(echo "$input" | jq -r '.model.display_name // ""')
    local transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
    local output_style=$(echo "$input" | jq -r '.output_style.name // ""')

    # Get context window bar
    local context_display=$(get_context_bar)

    if [ -n "$session_id" ] && [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
        # Calculate session duration
        local session_start_time=""
        local current_time=$(date +%s)

        # Try to get session start time from transcript file
        if [ -f "$transcript_path" ]; then
            local first_timestamp=$(grep -m1 '"timestamp"' "$transcript_path" 2>/dev/null | sed -n 's/.*"timestamp":\s*"\([^"]*\)".*/\1/p')
            if [ -n "$first_timestamp" ]; then
                session_start_time=$(date -d "$first_timestamp" +%s 2>/dev/null)
            fi
        fi

        # If we couldn't get start time from transcript, use file creation time
        if [ -z "$session_start_time" ]; then
            session_start_time=$(stat -c %Y "$transcript_path" 2>/dev/null)
        fi

        # Calculate duration
        local duration_seconds=""
        if [ -n "$session_start_time" ] && [ "$session_start_time" -gt 0 ]; then
            duration_seconds=$((current_time - session_start_time))
        fi

        # Format duration
        local duration_display=""
        if [ -n "$duration_seconds" ] && [ "$duration_seconds" -gt 0 ]; then
            local hours=$((duration_seconds / 3600))
            local minutes=$(((duration_seconds % 3600) / 60))
            local seconds=$((duration_seconds % 60))

            if [ "$hours" -gt 0 ]; then
                duration_display="${hours}h${minutes}m"
            elif [ "$minutes" -gt 0 ]; then
                duration_display="${minutes}m${seconds}s"
            else
                duration_display="${seconds}s"
            fi
        fi

        # Extract token usage and cost information from transcript
        local total_input_tokens=0
        local total_output_tokens=0
        local estimated_cost=0

        if [ -f "$transcript_path" ]; then
            local input_tokens=$(grep -o '"input_tokens":[0-9]*' "$transcript_path" 2>/dev/null | sed 's/"input_tokens"://' | awk '{sum+=$1} END {print sum+0}')
            local output_tokens=$(grep -o '"output_tokens":[0-9]*' "$transcript_path" 2>/dev/null | sed 's/"output_tokens"://' | awk '{sum+=$1} END {print sum+0}')

            total_input_tokens=${input_tokens:-0}
            total_output_tokens=${output_tokens:-0}

            # Cost estimation (Claude 3.5 Sonnet pricing)
            # Input: $3 per million tokens, Output: $15 per million tokens
            if [ "$total_input_tokens" -gt 0 ] || [ "$total_output_tokens" -gt 0 ]; then
                local input_cost=$(echo "scale=4; $total_input_tokens * 3 / 1000000" | bc -l 2>/dev/null || echo "0")
                local output_cost=$(echo "scale=4; $total_output_tokens * 15 / 1000000" | bc -l 2>/dev/null || echo "0")
                estimated_cost=$(echo "scale=4; $input_cost + $output_cost" | bc -l 2>/dev/null || echo "0")
            fi
        fi

        # Build session info display with modern aesthetics
        local session_parts=()

        # Model name (soft purple gradient)
        if [ -n "$model_name" ]; then
            local short_model=$(echo "$model_name" | sed 's/Claude //g' | sed 's/Sonnet/SN/' | sed 's/Haiku/HK/' | sed 's/Opus/OP/')
            session_parts+=("${C_PURPLE}${C_BOLD}${short_model}${C_RESET}")
        fi

        # Duration (soft mint)
        if [ -n "$duration_display" ]; then
            session_parts+=("${C_SUCCESS}${duration_display}${C_RESET}")
        fi

        # Token usage (soft blue)
        if [ "$total_input_tokens" -gt 0 ] || [ "$total_output_tokens" -gt 0 ]; then
            local token_display=""
            if [ "$total_input_tokens" -gt 999 ]; then
                local input_k=$((total_input_tokens / 1000))
                token_display="${input_k}k"
            else
                token_display="$total_input_tokens"
            fi

            if [ "$total_output_tokens" -gt 999 ]; then
                local output_k=$((total_output_tokens / 1000))
                token_display="${token_display}${SEP_ARROW}${output_k}k"
            else
                token_display="${token_display}${SEP_ARROW}$total_output_tokens"
            fi

            session_parts+=("${C_INFO}${token_display}${C_RESET}")
        fi

        # Cost (soft peach/warm)
        if [ -n "$estimated_cost" ] && [ "$(echo "$estimated_cost > 0.001" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
            local cost_display=""
            if [ "$(echo "$estimated_cost >= 0.01" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
                cost_display=$(printf "%.2f" "$estimated_cost")
            else
                cost_display=$(printf "%.3f" "$estimated_cost")
            fi
            session_parts+=("${C_ACCENT}\$${cost_display}${C_RESET}")
        fi

        # Output style (if not default, soft periwinkle)
        if [ -n "$output_style" ] && [ "$output_style" != "default" ]; then
            local style_short=$(echo "$output_style" | cut -c1-3 | tr '[:lower:]' '[:upper:]')
            session_parts+=("${C_PRIMARY}${C_DIM}[${style_short}]${C_RESET}")
        fi

        # Combine all session parts with clean separators
        if [ ${#session_parts[@]} -gt 0 ]; then
            local IFS=" "
            session_info="${C_PRIMARY}${C_BOLD}⚡${C_RESET} ${session_parts[*]}"
        fi
    fi

    # Add context bar if available
    if [ -n "$context_display" ]; then
        session_info="${session_info} ${context_display}"
    fi

    echo "$session_info"
}

# Function to get git information with modern display
get_git_info() {
    local dir="$1"
    local git_info=""

    # Check if we're in a git repository (skip optional locks)
    if git -C "$dir" --no-optional-locks rev-parse --git-dir >/dev/null 2>&1; then
        local branch=""
        local status_info=""

        # Get current branch name
        branch=$(git -C "$dir" --no-optional-locks branch --show-current 2>/dev/null)
        if [ -z "$branch" ]; then
            # Fallback for detached HEAD
            branch=$(git -C "$dir" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
        fi

        # Get git status information (skip optional locks)
        local status_output
        status_output=$(git -C "$dir" --no-optional-locks status --porcelain 2>/dev/null)

        # Count different types of changes
        local staged=0
        local modified=0
        local untracked=0
        local deleted=0

        while IFS= read -r line; do
            if [ -n "$line" ]; then
                case "${line:0:2}" in
                "A "* | "M "* | "R "* | "C "* | "D "*) staged=$((staged + 1)) ;;
                " M" | " D") modified=$((modified + 1)) ;;
                " A") staged=$((staged + 1)) ;;
                "??") untracked=$((untracked + 1)) ;;
                *D*) deleted=$((deleted + 1)) ;;
                esac
            fi
        done <<<"$status_output"

        # Get ahead/behind information (skip optional locks)
        local ahead_behind=""
        local upstream=$(git -C "$dir" --no-optional-locks rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
        if [ -n "$upstream" ]; then
            local ahead=$(git -C "$dir" --no-optional-locks rev-list --count HEAD ^"$upstream" 2>/dev/null)
            local behind=$(git -C "$dir" --no-optional-locks rev-list --count "$upstream" ^HEAD 2>/dev/null)

            if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
                ahead_behind="${C_ORANGE}↑${ahead}${C_RESET}${C_GRAY}↓${behind}${C_RESET}"
            elif [ "$ahead" -gt 0 ]; then
                ahead_behind="${C_SUCCESS}↑${ahead}${C_RESET}"
            elif [ "$behind" -gt 0 ]; then
                ahead_behind="${C_ERROR}↓${behind}${C_RESET}"
            fi
        fi

        # Build status indicators with modern icons
        local status_parts=()
        [ $staged -gt 0 ] && status_parts+=("${C_SUCCESS}+${staged}${C_RESET}")
        [ $modified -gt 0 ] && status_parts+=("${C_WARN}~${modified}${C_RESET}")
        [ $deleted -gt 0 ] && status_parts+=("${C_ERROR}-${deleted}${C_RESET}")
        [ $untracked -gt 0 ] && status_parts+=("${C_GRAY}?${untracked}${C_RESET}")

        # Build complete git info with modern styling
        if [ -n "$branch" ]; then
            git_info="${C_PRIMARY}${C_BOLD}${branch}${C_RESET}"
        fi

        # Add ahead/behind info
        if [ -n "$ahead_behind" ]; then
            git_info="${git_info} ${ahead_behind}"
        fi

        # Add status indicators
        if [ ${#status_parts[@]} -gt 0 ]; then
            local IFS=" "
            git_info="${git_info} ${C_GRAY}${status_parts[*]}${C_RESET}"
        fi
    fi

    echo "$git_info"
}

# Function to detect programming language with modern icons
detect_language() {
    local dir="$1"
    local lang_info=""
    local lang_icon=""

    # Check for various language/framework indicators
    if [ -f "$dir/package.json" ]; then
        # Node.js/JavaScript/TypeScript
        if [ -f "$dir/tsconfig.json" ] || grep -q '"typescript"' "$dir/package.json" 2>/dev/null; then
            lang_info="TS"
            lang_icon=""
        else
            lang_info="JS"
            lang_icon=""
        fi
    elif [ -f "$dir/requirements.txt" ] || [ -f "$dir/pyproject.toml" ] || [ -f "$dir/setup.py" ] || [ -f "$dir/Pipfile" ]; then
        lang_info="PY"
        lang_icon=""
    elif [ -f "$dir/go.mod" ]; then
        lang_info="GO"
        lang_icon=""
    elif [ -f "$dir/Cargo.toml" ]; then
        lang_info="RS"
        lang_icon=""
    elif [ -f "$dir/pom.xml" ] || [ -f "$dir/build.gradle" ] || [ -f "$dir/build.gradle.kts" ]; then
        if [ -f "$dir/build.gradle" ] || [ -f "$dir/build.gradle.kts" ]; then
            lang_info="Gradle"
        else
            lang_info="JV"
        fi
        lang_icon=""
    elif [ -f "$dir/composer.json" ]; then
        lang_info="PHP"
        lang_icon=""
    elif [ -f "$dir/Gemfile" ]; then
        lang_info="RB"
        lang_icon=""
    elif [ -f "$dir/mix.exs" ]; then
        lang_info="EX"
        lang_icon=""
    elif [ -f "$dir/dune-project" ] || [ -f "$dir/dune" ]; then
        lang_info="OC"
        lang_icon=""
    elif [ -f "$dir/stack.yaml" ] || [ -f "$dir/cabal.project" ] || [ -f "$dir/*.cabal" ]; then
        lang_info="HS"
        lang_icon=""
    elif [ -f "$dir/CMakeLists.txt" ]; then
        lang_info="C++"
        lang_icon=""
    elif [ -f "$dir/Makefile" ] || [ -f "$dir/makefile" ]; then
        lang_info="Make"
        lang_icon=""
    elif [ -f "$dir/docker-compose.yml" ] || [ -f "$dir/docker-compose.yaml" ] || [ -f "$dir/Dockerfile" ]; then
        lang_info="Docker"
        lang_icon=""
    elif [ -f "$dir/.terraform" ] || [ -f "$dir/main.tf" ]; then
        lang_info="Terraform"
        lang_icon=""
    elif [ -f "$dir/Chart.yaml" ]; then
        lang_info="Helm"
        lang_icon=""
    elif [ -f "$dir/pubspec.yaml" ]; then
        lang_info="Dart"
        lang_icon=""
    elif [ -f "$dir/Project.swift" ] || [ -f "$dir/Package.swift" ]; then
        lang_info="Swift"
        lang_icon=""
    elif [ -f "$dir/build.zig" ]; then
        lang_info="Zig"
        lang_icon=""
    fi

    if [ -n "$lang_info" ]; then
        echo "${lang_icon}${lang_info}"
    fi
}

# Virtual environment info with modern styling
venv_info=""
if [ -n "$VIRTUAL_ENV" ]; then
    venv_info="${C_ACCENT}${C_DIM}($(basename "$VIRTUAL_ENV"))${C_RESET} "
fi

# Get current directory (fallback to pwd if not in JSON)
if [ -z "$current_dir" ]; then
    current_dir=$(pwd)
fi

# Shorten home directory in path
if [ "$HOME" != "" ]; then
    current_dir_short="${current_dir/#$HOME/\~}"
else
    current_dir_short="$current_dir"
fi

# Detect programming language
lang_info=$(detect_language "$current_dir")
lang_display=""
if [ -n "$lang_info" ]; then
    lang_display="${C_PURPLE}${C_BOLD}${lang_info}${C_RESET}${SEP_THIN}"
fi

# Get git information
git_display=$(get_git_info "$current_dir")

# Get Claude Code session information
claude_session_display=$(get_claude_session_info)

# Build the complete status line with modern layout
# Layout: [LANG] │ path │ git │ session
printf "${lang_display}${venv_info}${C_PRIMARY}${C_BOLD}${current_dir_short}${C_RESET}"

# Add git info with separator
if [ -n "$git_display" ]; then
    printf " ${C_GRAY}${SEP_THIN}${C_RESET} ${git_display}"
fi

# Add session info with separator
if [ -n "$claude_session_display" ]; then
    printf " ${C_GRAY}${SEP_THIN}${C_RESET} ${claude_session_display}"
fi

printf "\n"
