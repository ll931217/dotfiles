function cheat() { curl cheat.sh/"$@"; }

# usage: clip "$KOMODO_API_SECRET"
function clip() {
  if [ -t 0 ]; then
    printf '%s' "$1" | xclip -selection clipboard;
  else
    xclip -selection clipboard
  fi
}

function procproj() {
  local pid="$1"

  while [[ "$pid" -gt 1 && -r "/proc/$pid/status" ]]; do
    local name cwd ppid

    name=$(cat "/proc/$pid/comm" 2>/dev/null)
    cwd=$(readlink -f "/proc/$pid/cwd" 2>/dev/null)
    ppid=$(awk '/^PPid:/ {print $2}' "/proc/$pid/status")

    printf "%-8s %-25s %s\n" "$pid" "$name" "$cwd"

    pid="$ppid"
  done
}

function y() {
  local tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
  yazi "$@" --cwd-file="$tmp"
  if cwd="$(/usr/bin/cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
    cd -- "$cwd"
  fi
  rm -f -- "$tmp"
}

function checkport() {
  if [[ -z "$1" ]]; then
    echo "Usage: checkport <port> [<port2> <port3> ...]"
    return 1
  fi

  for port in "$@"; do
    echo "Checking port: $port"
    # Try using lsof first
    if command -v lsof >/dev/null; then
      lsof -iTCP:"$port" -sTCP:LISTEN -n -P || echo "  No process is listening on port $port (via lsof)."
    # If lsof isn't available, fall back to netstat or ss
    elif command -v ss >/dev/null; then
      ss -ltnp | grep ":$port" || echo "  No process is listening on port $port (via ss)."
    elif command -v netstat >/dev/null; then
      netstat -tulnp | grep ":$port" || echo "  No process is listening on port $port (via netstat)."
    else
      echo "Neither lsof, ss, nor netstat is available. Cannot check ports."
      return 2
    fi
    echo ""
  done
}

function killport() {
  if [[ -z "$1" ]]; then
    echo "Usage: killport <port> [<port2> <port3> ...]"
    return 1
  fi

  for port in "$@"; do
    echo "Killing process on port: $port"

    if command -v lsof >/dev/null; then
      # Get PID(s) using lsof (-t outputs only PIDs)
      local pids=$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null)
      if [[ -n "$pids" ]]; then
        echo "  Found PID(s): $pids"
        echo "$pids" | xargs kill -9
        echo "  Killed process(es) on port $port"
      else
        echo "  No process is listening on port $port"
      fi
    elif command -v fuser >/dev/null; then
      # Fallback to fuser
      if fuser -k "$port/tcp" 2>/dev/null; then
        echo "  Killed process on port $port (via fuser)"
      else
        echo "  No process is listening on port $port"
      fi
    elif command -v ss >/dev/null; then
      # Extract PID from ss output
      local pid=$(ss -ltnp | grep ":$port " | grep -oP 'pid=\K\d+' | head -1)
      if [[ -n "$pid" ]]; then
        echo "  Found PID: $pid"
        kill -9 "$pid"
        echo "  Killed process on port $port"
      else
        echo "  No process is listening on port $port"
      fi
    else
      echo "Neither lsof, fuser, nor ss is available. Cannot kill port."
      return 2
    fi
    echo ""
  done
}

# unalias z
function z() {
  if [[ -z "$*" ]]; then
    cd "$(_z -l 2>&1 | fzf +s --tac | sed 's/^[0-9,.]* *//')"
  else
    _last_z_args="$@"
    _z "$@"
  fi
}

function zz() {
  cd "$(_z -l 2>&1 | sed 's/^[0-9,.]* *//' | fzf -q "$_last_z_args")"
}

function describe_apt() {
  sudo cat /var/log/apt/history.log | grep -A5 -B5 "$@"
}

# Function to update worktrunk
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

# Show top processes by open file descriptors (like htop for FDs)
function fdtop() {
  local count=${1:-20}
  echo "Top $count processes by open file descriptors:"
  echo "==============================================="
  printf "%-8s %-6s %-12s %-20s %-50s %s\n" "PID" "FDs" "OWNER" "CWD" "COMMAND"
  echo "-------------------------------------------------------------------------------------------------------"

  for pid in /proc/[0-9]*; do
    pid_num=$(basename $pid)
    fd_count=$(ls $pid/fd 2>/dev/null | wc -l)

    # Skip if we can't read fd directory
    [ "$fd_count" -eq 0 ] 2>/dev/null && continue

    # Get process info using ps
    proc_info=$(ps -p $pid_num -o user=,comm=,args= 2>/dev/null)
    [ -z "$proc_info" ] && continue

    owner=$(echo "$proc_info" | awk '{print $1}')
    proc_name=$(echo "$proc_info" | awk '{print $2}')
    proc_args=$(echo "$proc_info" | awk '{$1=$2=""; print substr($0,3)}' | cut -c1-80)

    # Get current working directory
    cwd=$(readlink -f $pid/cwd 2>/dev/null || echo "N/A")
    cwd_short=$(echo "$cwd" | rev | cut -d'/' -f1-3 | rev)
    [ ${#cwd} -gt 30 ] && cwd_short=".../$cwd_short"

    printf "%-8s %-6s %-12s %-20s %-50s %s\n" "$pid_num" "$fd_count" "$owner" "$cwd_short" "$proc_args"
  done | sort -t' ' -k2 -rn | head -$count
}

# Generate a random string with configurable character classes.
# Usage: randstr [length]
# Env vars (all optional):
#   RANDSTR_LENGTH       (default: 21)
#   RANDSTR_SYMBOLS      (1/0, default: 1)
#   RANDSTR_NUMBERS      (1/0, default: 1)
#   RANDSTR_MIN_SYMBOLS  (default: 2)
#   RANDSTR_MIN_NUMBERS  (default: 2)
randstr() {
  local length="${1:-${RANDSTR_LENGTH:-21}}"
  local use_symbols="${RANDSTR_SYMBOLS:-1}"
  local use_numbers="${RANDSTR_NUMBERS:-1}"
  local min_symbols="${RANDSTR_MIN_SYMBOLS:-2}"
  local min_numbers="${RANDSTR_MIN_NUMBERS:-3}"

  local letters='A-Za-z'
  local numbers='0-9'
  local symbols='!@#$%^&*'

  local pool="$letters"
  local need_symbols=0 need_numbers=0

  [[ "$use_symbols" == "1" ]] && {
    pool+="$symbols"
    need_symbols=$min_symbols
  }
  [[ "$use_numbers" == "1" ]] && {
    pool+="$numbers"
    need_numbols=$min_numbers
  }

  local min_total=$((need_symbols + need_numbers))
  if ((min_total > length)); then
    print -u2 "randstr: minimums ($min_total) exceed length ($length)"
    return 1
  fi

  local result=""
  ((need_symbols > 0)) && result+="$(LC_ALL=C tr -dc "$symbols" </dev/urandom | head -c "$need_symbols")"
  ((need_numbers > 0)) && result+="$(LC_ALL=C tr -dc "$numbers" </dev/urandom | head -c "$need_numbers")"

  local remaining=$((length - min_total))
  ((remaining > 0)) && result+="$(LC_ALL=C tr -dc "$pool" </dev/urandom | head -c "$remaining")"

  # Shuffle so guaranteed chars aren't clustered at the start
  print -r -- "$result" | fold -w1 | shuf | tr -d '\n'
  print
}

function unset_anthropic_env() {
  unset ANTHROPIC_API_KEY
  unset ANTHROPIC_BASE_URL
  unset ANTHROPIC_MODEL
  unset ANTHROPIC_DEFAULT_OPUS_MODEL
  unset ANTHROPIC_DEFAULT_SONNET_MODEL
  unset ANTHROPIC_DEFAULT_HAIKU_MODEL
  # export ANTHROPIC_MODEL='opusplan'
}

function set_claude_env() {
  unset_anthropic_env
  export ANTHROPIC_BASE_URL=http://higw.vici.corp
  export ANTHROPIC_MODEL='opusplan'
  export ANTHROPIC_DEFAULT_OPUS_MODEL='vertex-claude-opus-4-6'
  export ANTHROPIC_DEFAULT_SONNET_MODEL='vertex-claude-sonnet-4-5'
  export ANTHROPIC_DEFAULT_HAIKU_MODEL='vertex-claude-sonnet-4-5'
}

function set_claude_test_env() {
  unset_anthropic_env
  export ANTHROPIC_BASE_URL=http://higw-a.vici.corp
  # export ANTHROPIC_MODEL='claude-max-opus-4-6'
  export ANTHROPIC_DEFAULT_OPUS_MODEL='claude-max-opus-4-6'
  export ANTHROPIC_DEFAULT_SONNET_MODEL='claude-max-sonnet-4-6'
  export ANTHROPIC_DEFAULT_HAIKU_MODEL='claude-max-haiku-4-5'
}

function update_cc_model_overrides() {
  # Validate JSON format before backup
  if ! jq empty "$HOME/.claude/settings.json" 2>/dev/null; then
    echo "Warning: $HOME/.claude/settings.json is not valid JSON. Restoring from latest backup..."
    local latest_backup=$(ls -t "$HOME/.claude/settings.json.bak_"* 2>/dev/null | head -1)
    if [[ -z "$latest_backup" ]]; then
      echo "Error: No backup found to restore from. Aborting."
      return 1
    fi
    cp "$latest_backup" "$HOME/.claude/settings.json"
    echo "Restored from $latest_backup"
  else
    cp "$HOME/.claude/settings.json" "$HOME/.claude/settings.json.bak_$(date '+%Y%m%d_%H%M%S')"
  fi
  if jq ".modelOverrides[\"claude-opus-4-6\"] = \"$ANTHROPIC_DEFAULT_OPUS_MODEL\" | .modelOverrides[\"claude-sonnet-4-6\"] = \"$ANTHROPIC_DEFAULT_SONNET_MODEL\" | .modelOverrides[\"claude-haiku-4-5\"] = \"$ANTHROPIC_DEFAULT_HAIKU_MODEL\"" "$HOME/.claude/settings.json" >/tmp/tmp_cc_settings.json 2>/dev/null; then
    mv /tmp/tmp_cc_settings.json "$HOME/.claude/settings.json"
  else
    rm -f /tmp/tmp_cc_settings.json
  fi
}

# set_claude_env
# set_claude_test_env
unset_anthropic_env
# update_cc_model_overrides

##
## ClickHouse
##

function set_ch_rom() {
  export CLICKHOUSE_HOST="172.21.10.105"
  export CLICKHOUSE_PORT="8123"
  export CLICKHOUSE_USER="root"
  export CLICKHOUSE_PASSWORD="CH@1qaz@WSX"
  export CLICKHOUSE_SECURE=false
  export CLICKHOUSE_VERIFY=false
  export CLICKHOUSE_CONNECT_TIMEOUT=30
  export CLICKHOUSE_SEND_RECEIVE_TIMEOUT=30
}

# Convert a string to ASCII/byte decimal values.
# Usage: str2ascii <string> [<string2> ...]
#   -h, --hex   output hex instead of decimal
#   -c, --char  show "char=code" pairs
# Examples:
#   str2ascii Hi           # 72 105
#   str2ascii -h Hi        # 48 69
#   str2ascii -c Hi        # H=72 i=105
function str2ascii() {
  local fmt="%d" pairs=0
  while (($#)); do
    case "$1" in
      -h|--hex)  fmt="%x"; shift ;;
      -c|--char) pairs=1; shift ;;
      *)         break ;;
    esac
  done

  if [[ -z "$1" ]]; then
    echo "Usage: str2ascii [-h|--hex] [-c|--char] <string> [<string2> ...]" >&2
    return 1
  fi

  for s in "$@"; do
    local i=0 out=""
    for ((i=0; i<${#s}; i++)); do
      local ch="${s:$i:1}"
      local code="$(printf "$fmt" "'$ch")"
      if ((pairs)); then
        out+="${ch}=${code} "
      else
        out+="${code} "
      fi
    done
    echo "${out% }"
  done
}

function copy_slide() {
  if [[ -z "$1" ]]; then
    echo "Usage: copy_slide <file> [<file2> <file3> ...]"
    return 1
  fi

  for file in "$@"; do
    echo "Checking file: $file"
    if [[ -f $file ]]; then
      scp $file liangshih.lin@172.21.10.106:/opt/docs/slides/liang
    else
      echo "$file does not exist"
      return 2
    fi
    echo ""
  done
}

function hj() {
  # `hj example.org'
  http --pretty=all --print=b "$@" | jless
}

function v() {
  # `v file.ts' -- reuse ONE nvim instead of one instance per project.
  # Each nvim instance runs its own LSP servers, keyed on (instance, root_dir),
  # and nothing is shared across instances. Nine project instances therefore
  # meant nine sets of tsserver. This reuses a single server on a fixed socket.
  # Uses nvim's built-in --server/--remote; no nvr dependency.
  local sock="${XDG_RUNTIME_DIR:-/tmp}/nvim-shared.sock"
  # Probe rather than trust the socket file: a crashed nvim leaves the inode
  # behind, and connecting to a dead socket just errors out.
  if [[ -S $sock ]] && nvim --server "$sock" --remote-expr 1 >/dev/null 2>&1; then
    nvim --server "$sock" --remote "${@:-.}"
    # ponytail: --remote returns immediately and does not move focus. In tmux,
    # jump manually, or wire `tmux switch-client` here if it becomes annoying.
  else
    rm -f "$sock"
    nvim --listen "$sock" "$@"
  fi
}
