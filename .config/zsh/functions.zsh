function __git_prompt_git() {
  GIT_OPTIONAL_LOCKS=0 command git "$@"
}

# Outputs the name of the current branch
# Usage example: git pull origin $(git_current_branch)
# Using '--quiet' with 'symbolic-ref' will not cause a fatal error (128) if
# it's not a symbolic ref, but in a Git repo.
function git_current_branch() {
  local ref
  ref=$(__git_prompt_git symbolic-ref --quiet HEAD 2> /dev/null)
  local ret=$?
  if [[ $ret != 0 ]]; then
    [[ $ret == 128 ]] && return  # no git repo.
    ref=$(__git_prompt_git rev-parse --short HEAD 2> /dev/null) || return
  fi
  echo ${ref#refs/heads/}
}

function convert2gif() {
  if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: convert2gif <input> <output>"
    echo ""
    echo "Example: ffmpeg -i video.mp4 -f yuv4mpegpipe - | gifski -o anim.gif -"
    return 1
  fi
  ffmpeg -i $1 -f yuv4mpegpipe - | gifski -o $2 -
}

function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(/usr/bin/cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}

function convert2gif() {
  if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: convert2gif <input> <output>"
    echo ""
    echo "Example: convert2gif video.mp4 ~/Videos/anim.gif"
    return 1
  fi

  ffmpeg -i $1 -f yuv4mpegpipe - | gifski -o $2 -
}

function watchservice() {
  if [ -z "$1" ]; then
    echo "Usage: watchservice <servicename>"
    echo ""
    echo "Example: watchservice nginx"
    return 1
  fi

  sudo journalctl -f -b -n 500 -o cat -u $1
}

function checkport() {
  if [ -z "$1" ]; then
    echo "Usage: checkport <port>"
    echo ""
    echo "Example: checkport 3000"
    return 1
  fi

  # sudo ss -tulpns | rg $1
  sudo lsof -nP -iTCP -sTCP:LISTEN | rg $1
}

function killport() {
  if [ -z "$1" ]; then
    echo "Usage: killport <port>"
    return 1
  fi
  
  pid=$(sudo lsof -nP -iTCP -sTCP:LISTEN | grep $1 | awk '{print $2}')
  
  if [ -z "$pid" ]; then
    echo "No process found using port $1"
    return 1
  fi
  
  sudo kill -9 $pid
}

function mcd() {
  if [ -z "$1" ]; then
    echo "Usage: mcd <folder_name>"
    return 1
  fi

  mkdir $1 && cd $1
}

function timezsh() {
  shell=${1-$SHELL}
  for i in $(seq 1 10); do /usr/bin/time $shell -i -c exit; done
}

function spf() {
    os=$(uname -s)

    # Linux
    if [[ "$os" == "Linux" ]]; then
        export SPF_LAST_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/superfile/lastdir"
    fi

    # macOS
    if [[ "$os" == "Darwin" ]]; then
        export SPF_LAST_DIR="$HOME/Library/Application Support/superfile/lastdir"
    fi

    command spf "$@"

    [ ! -f "$SPF_LAST_DIR" ] || {
        . "$SPF_LAST_DIR"
        rm -f -- "$SPF_LAST_DIR" > /dev/null
    }
}

function reset_nvim() {
  rm -rf ~/.local/share/nvim
  rm -rf ~/.local/state/nvim
  rm -rf ~/.cache/nvim
}

function cheat(){ curl cheat.sh/"$@";  }

function mkmv() {
  if [ -z "$1" ]; then
    echo "Usage: $0 <directory_name>"
    exit 1
  fi

  mkdir -p "$1" && cd "$1"
}


function pwcp() {
  if [ -z "$1" ]; then
    echo "Usage: $0 <entry name>"
    exit 1
  fi
  rbw get "$(rbw list | rg -i $1 | fzf)" | wl-copy -n
}

function uwt() {
  local latest_version
  local install_url

  # Fetch latest release tag from GitHub API
  latest_version=$(curl -s https://api.github.com/repos/max-sixty/worktrunk/releases/latest | jq -r '.tag_name')

  if [ -z "$latest_version" ] || [ "$latest_version" = "null" ]; then
    echo "Error: Failed to fetch latest worktrunk version"
    return 1
  fi

  echo "Installing worktrunk $latest_version..."

  install_url="https://github.com/max-sixty/worktrunk/releases/download/${latest_version}/worktrunk-installer.sh"

  curl --proto '=https' --tlsv1.2 -LsSf "$install_url" | sh
}

function oc() {
  local base_name=$(basename "$PWD")
  local path_hash=$(echo "$PWD" | md5sum | cut -c1-4)
  local session_name="${base_name}-${path_hash}"
  
  # Find available port
  local port=14096
  while [ $port -lt 15096 ]; do
    if ! lsof -i :$port >/dev/null 2>&1; then
      break
    fi
    port=$((port + 1))
  done
  
  export OPENCODE_PORT=$port
  
  if [ -n "$TMUX" ]; then
    opencode --port $port "$@"
  else
    local oc_cmd="OPENCODE_PORT=$port opencode --port $port $*; exec $SHELL"
    if tmux has-session -t "$session_name" 2>/dev/null; then
      tmux new-window -t "$session_name" -c "$PWD" "$oc_cmd"
      tmux attach-session -t "$session_name"
    else
      tmux new-session -s "$session_name" -c "$PWD" "$oc_cmd"
    fi
  fi
}

function reset_anthropic_env() {
  unset ANTHROPIC_DEFAULT_HAIKU_MODEL
  unset ANTHROPIC_DEFAULT_OPUS_MODEL
  unset ANTHROPIC_DEFAULT_SONNET_MODEL
  unset ANTHROPIC_MODEL
  unset ANTHROPIC_BASE_URL
}

function use_zai() {
  reset_anthropic_env

  export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-5"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-4.7"
  export ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.7-flashx"
  export ANTHROPIC_MODEL="opusplan"
  export CLAUDE_CODE_ENABLE_TELEMETRY="0"
  export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
  export ANTHROPIC_AUTH_TOKEN="$GLM_API_KEY"
  export API_TIMEOUT_MS=3000000
}

function use_llama_cpp() {
  reset_anthropic_env

  export ANTHROPIC_DEFAULT_HAIKU_MODEL="qwen2.5-coder"
  export ANTHROPIC_DEFAULT_SONNET_MODEL="qwen2.5-coder"
  export ANTHROPIC_DEFAULT_OPUS_MODEL="qwen3-deepseek-r1"
  export ANTHROPIC_MODEL="qwen2.5-coder"
  # export ANTHROPIC_MODEL="glm-opus"
  export ANTHROPIC_BASE_URL="http://localhost:20000"
  export CLAUDE_CODE_ENABLE_TELEMETRY="0"
  export API_TIMEOUT_MS=3000000
}

use_zai
