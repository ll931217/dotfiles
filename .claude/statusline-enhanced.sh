#!/bin/bash

# Get JSON input
input=$(cat)

# Extract current directory from JSON
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')

# Function to get Claude Code session information
get_claude_session_info() {
    local session_info=""

    # Extract session data from JSON input
    local session_id=$(echo "$input" | jq -r '.session_id // ""')
    local model_name=$(echo "$input" | jq -r '.model.display_name // ""')
    local transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
    local output_style=$(echo "$input" | jq -r '.output_style.name // ""')

    if [ -n "$session_id" ] && [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
        # Calculate session duration
        local session_start_time=""
        local current_time=$(date +%s)

        # Try to get session start time from transcript file
        if [ -f "$transcript_path" ]; then
            # Look for timestamp in transcript (assuming first line has timestamp)
            local first_timestamp=$(grep -m1 '"timestamp"' "$transcript_path" 2>/dev/null | sed -n 's/.*"timestamp":\s*"\([^"]*\)".*/\1/p')
            if [ -n "$first_timestamp" ]; then
                # Convert ISO timestamp to epoch seconds
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
            # Count input and output tokens from transcript
            # Look for usage patterns in the transcript JSON
            local input_tokens=$(grep -o '"input_tokens":[0-9]*' "$transcript_path" 2>/dev/null | sed 's/"input_tokens"://' | awk '{sum+=$1} END {print sum+0}')
            local output_tokens=$(grep -o '"output_tokens":[0-9]*' "$transcript_path" 2>/dev/null | sed 's/"output_tokens"://' | awk '{sum+=$1} END {print sum+0}')

            total_input_tokens=${input_tokens:-0}
            total_output_tokens=${output_tokens:-0}

            # Rough cost estimation (Claude 3.5 Sonnet pricing as of 2024)
            # Input: $3 per million tokens, Output: $15 per million tokens
            if [ "$total_input_tokens" -gt 0 ] || [ "$total_output_tokens" -gt 0 ]; then
                local input_cost=$(echo "scale=4; $total_input_tokens * 3 / 1000000" | bc -l 2>/dev/null || echo "0")
                local output_cost=$(echo "scale=4; $total_output_tokens * 15 / 1000000" | bc -l 2>/dev/null || echo "0")
                estimated_cost=$(echo "scale=4; $input_cost + $output_cost" | bc -l 2>/dev/null || echo "0")
            fi
        fi

        # Build session info display
        local session_parts=()

        # Model name (bright cyan)
        if [ -n "$model_name" ]; then
            local short_model=$(echo "$model_name" | sed 's/Claude /C/' | sed 's/Sonnet/S/' | sed 's/Haiku/H/' | sed 's/Opus/O/')
            session_parts+=("\033[01;96m$short_model\033[00m")
        fi

        # Duration (bright green if active)
        if [ -n "$duration_display" ]; then
            session_parts+=("\033[01;92m⏱$duration_display\033[00m")
        fi

        # Token usage (bright yellow)
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
                token_display="${token_display}→${output_k}k"
            else
                token_display="${token_display}→$total_output_tokens"
            fi

            session_parts+=("\033[01;93m🔢$token_display\033[00m")
        fi

        # Cost (bright red if significant)
        if [ -n "$estimated_cost" ] && [ "$(echo "$estimated_cost > 0.001" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
            local cost_display=""
            if [ "$(echo "$estimated_cost >= 0.01" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
                cost_display=$(printf "%.2f" "$estimated_cost")
            else
                cost_display=$(printf "%.3f" "$estimated_cost")
            fi
            session_parts+=("\033[01;91m\$$cost_display\033[00m")
        fi

        # Output style (if not default, in bright blue)
        if [ -n "$output_style" ] && [ "$output_style" != "default" ]; then
            local style_short=$(echo "$output_style" | cut -c1-3 | tr '[:lower:]' '[:upper:]')
            session_parts+=("\033[01;94m[$style_short]\033[00m")
        fi

        # Combine all session parts
        if [ ${#session_parts[@]} -gt 0 ]; then
            local IFS="|"
            session_info="\033[01;37m⚡\033[00m${session_parts[*]}"
        fi
    fi

    echo "$session_info"
}

# Function to get git information
get_git_info() {
    local dir="$1"
    local git_info=""

    # Check if we're in a git repository
    if git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
        local branch=""
        local status_info=""
        local changes=""

        # Get current branch name
        branch=$(git -C "$dir" branch --show-current 2>/dev/null)
        if [ -z "$branch" ]; then
            # Fallback for detached HEAD
            branch=$(git -C "$dir" rev-parse --short HEAD 2>/dev/null)
        fi

        # Get git status information
        local status_output
        status_output=$(git -C "$dir" status --porcelain 2>/dev/null)

        # Count different types of changes
        local staged=0
        local modified=0
        local untracked=0
        local deleted=0

        while IFS= read -r line; do
            if [ -n "$line" ]; then
                case "${line:0:2}" in
                    "A "*|"M "*|"R "*|"C "*|"D "*) staged=$((staged + 1)) ;;
                    " M"|" D") modified=$((modified + 1)) ;;
                    " A") staged=$((staged + 1)) ;;
                    "??") untracked=$((untracked + 1)) ;;
                    *D*) deleted=$((deleted + 1)) ;;
                esac
            fi
        done <<< "$status_output"

        # Get ahead/behind information
        local ahead_behind=""
        local upstream=$(git -C "$dir" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
        if [ -n "$upstream" ]; then
            local ahead=$(git -C "$dir" rev-list --count HEAD ^"$upstream" 2>/dev/null)
            local behind=$(git -C "$dir" rev-list --count "$upstream" ^HEAD 2>/dev/null)

            if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
                ahead_behind="↑$ahead↓$behind"
            elif [ "$ahead" -gt 0 ]; then
                ahead_behind="↑$ahead"
            elif [ "$behind" -gt 0 ]; then
                ahead_behind="↓$behind"
            fi
        fi

        # Build status indicators
        local status_parts=()
        [ $staged -gt 0 ] && status_parts+=("\033[01;32m+$staged\033[00m")
        [ $modified -gt 0 ] && status_parts+=("\033[01;33m~$modified\033[00m")
        [ $deleted -gt 0 ] && status_parts+=("\033[01;31m-$deleted\033[00m")
        [ $untracked -gt 0 ] && status_parts+=("\033[01;37m?$untracked\033[00m")

        # Combine status parts
        if [ ${#status_parts[@]} -gt 0 ]; then
            local IFS="|"
            status_info="${status_parts[*]}"
        fi

        # Build complete git info
        git_info="\033[01;36m($branch"
        [ -n "$ahead_behind" ] && git_info="$git_info \033[01;35m$ahead_behind\033[01;36m"
        [ -n "$status_info" ] && git_info="$git_info $status_info\033[01;36m"
        git_info="$git_info)\033[00m"
    fi

    echo "$git_info"
}

# Function to detect programming language/technology
detect_language() {
    local dir="$1"
    local lang_info=""
    
    # Check for various language/framework indicators
    if [ -f "$dir/package.json" ]; then
        # Node.js/JavaScript/TypeScript
        if [ -f "$dir/tsconfig.json" ] || grep -q '"typescript"' "$dir/package.json" 2>/dev/null; then
            lang_info="TypeScript"
        else
            lang_info="Node.js"
        fi
    elif [ -f "$dir/requirements.txt" ] || [ -f "$dir/pyproject.toml" ] || [ -f "$dir/setup.py" ] || [ -f "$dir/Pipfile" ]; then
        # Python
        lang_info="Python"
    elif [ -f "$dir/go.mod" ]; then
        # Go
        lang_info="Go"
    elif [ -f "$dir/Cargo.toml" ]; then
        # Rust
        lang_info="Rust"
    elif [ -f "$dir/pom.xml" ] || [ -f "$dir/build.gradle" ] || [ -f "$dir/build.gradle.kts" ]; then
        # Java
        if [ -f "$dir/build.gradle" ] || [ -f "$dir/build.gradle.kts" ]; then
            lang_info="Gradle"
        else
            lang_info="Java"
        fi
    elif [ -f "$dir/composer.json" ]; then
        # PHP
        lang_info="PHP"
    elif [ -f "$dir/Gemfile" ]; then
        # Ruby
        lang_info="Ruby"
    elif [ -f "$dir/mix.exs" ]; then
        # Elixir
        lang_info="Elixir"
    elif [ -f "$dir/dune-project" ] || [ -f "$dir/dune" ]; then
        # OCaml
        lang_info="OCaml"
    elif [ -f "$dir/stack.yaml" ] || [ -f "$dir/cabal.project" ] || [ -f "$dir/*.cabal" ]; then
        # Haskell
        lang_info="Haskell"
    elif [ -f "$dir/CMakeLists.txt" ]; then
        # C/C++ with CMake
        lang_info="C/C++"
    elif [ -f "$dir/Makefile" ] || [ -f "$dir/makefile" ]; then
        # Generic Makefile
        lang_info="Make"
    elif [ -f "$dir/docker-compose.yml" ] || [ -f "$dir/docker-compose.yaml" ]; then
        # Docker Compose
        lang_info="Docker"
    elif [ -f "$dir/Dockerfile" ]; then
        # Docker
        lang_info="Docker"
    elif [ -f "$dir/.terraform" ] || [ -f "$dir/main.tf" ]; then
        # Terraform
        lang_info="Terraform"
    elif [ -f "$dir/Chart.yaml" ]; then
        # Helm
        lang_info="Helm"
    elif [ -f "$dir/pubspec.yaml" ]; then
        # Dart/Flutter
        lang_info="Dart"
    elif [ -f "$dir/Project.swift" ] || [ -f "$dir/Package.swift" ]; then
        # Swift
        lang_info="Swift"
    elif [ -f "$dir/build.zig" ]; then
        # Zig
        lang_info="Zig"
    fi
    
    echo "$lang_info"
}

# Virtual environment info
venv_info=""
if [ -n "$VIRTUAL_ENV" ]; then
    venv_info="\033[01;33m($(basename "$VIRTUAL_ENV"))\033[00m "
fi

# Get current directory (fallback to pwd if not in JSON)
if [ -z "$current_dir" ]; then
    current_dir=$(pwd)
fi

# Detect programming language
lang_info=$(detect_language "$current_dir")
lang_display=""
if [ -n "$lang_info" ]; then
    # Display language in bright magenta color
    lang_display=" \033[01;35m[$lang_info]\033[00m"
fi

# Get git information
git_display=$(get_git_info "$current_dir")

# Get Claude Code session information
claude_session_display=$(get_claude_session_info)

# Build the complete status line
printf "${venv_info}${debian_chroot:+(${debian_chroot})}\033[01;34m${current_dir}\033[00m${lang_display}"
[ -n "$git_display" ] && printf " $git_display"
[ -n "$claude_session_display" ] && printf " $claude_session_display"