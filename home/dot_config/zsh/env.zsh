export EDITOR=nvim
export TERMINAL=alacritty
export ENVIRONMENT=development
# Limit vitest concurrency
export VITEST_MAX_THREADS=4

export GTK_USE_PORTAL=0
export XDG_CURRENT_DESKTOP=i3 # helps with defaults
export FILEMANAGER=thunar     # or your preferred file manager

export OPENSESSIONS_SKIP_BINARY_DOWNLOAD=1
export GOOSE_DISABLE_KEYRING=1
export T3CODE_TELEMETRY_ENABLED=false

export RTK_TELEMETRY_DISABLED=1
export MEMKIT_DESTRUCTIVE_MODE=1

export PATH=$HOME/.cua/bin:$PATH
export PATH=$HOME/.local/bin:$PATH
export PATH=$HOME/.local/bin/arbor/:$PATH
export PATH=$HOME/.cargo/bin:$PATH
export PATH=$HOME/.scripts:$PATH

# Disable auth for mcp-inspector
export DANGEROUSLY_OMIT_AUTH=true

export LD_LIBRARY_PATH=$HOME/.local/lib:/usr/local/libexec:/usr/local/lib:$LD_LIBRARY_PATH

# Beads
export BEADS_DOLT_SERVER_MODE=1
export BEADS_DOLT_SERVER_HOST=0.0.0.0
export BEADS_DOLT_SERVER_PORT=3306
# export BEADS_DOLT_SERVER_USER=root
# export BEADS_DOLT_PASSWORD=

# Portless HTTPS by default
export PORTLESS_HTTPS=1

# Go environment setup
export GOROOT=$HOME/go
export GOPATH=$HOME/gowork
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH

# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/.local/bin/programs/curl/lib/
export PAGER=less # more, less


export KOMODO_API_URL="https://komodo.data.vici.corp"
unset KOMODO_API_KEY KOMODO_API_SECRET KOMODO_CLI_KEY KOMODO_CLI_SECRET
if (( $+commands[gopass] )); then
  _komodo_api_key=$(gopass show -o infra/komodo_api_key 2>/dev/null) || _komodo_api_key=
  _komodo_api_secret=$(gopass show -o infra/komodo_api_secret 2>/dev/null) || _komodo_api_secret=

  if [[ -n "$_komodo_api_key" && -n "$_komodo_api_secret" ]]; then
    export KOMODO_API_KEY="$_komodo_api_key"
    export KOMODO_API_SECRET="$_komodo_api_secret"
    export KOMODO_CLI_KEY="$KOMODO_API_KEY"
    export KOMODO_CLI_SECRET="$KOMODO_API_SECRET"
  fi

  unset _komodo_api_key _komodo_api_secret
fi

# Trailing /api: the frontend proxy strips one /api before forwarding to the
# backend, which mounts the External API v2 router at /api/v2 — so the public
# path is /api/api/v2 and the script appends /api/v2 to this base.
export HDX_API_URL=https://hyperdx.data.vici.corp/api

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Used as API Header: `Authorization: Bearer $NETBOX_API_TOKEN`

export BD_JIRA_SCRIPT=$HOME/.scripts/bd/jira2jsonl.py
export JIRA_BD_SCRIPT=$HOME/.scripts/bd/jsonl2jira.py

unset CLAUDE_CODE_USE_BEDROCK
unset AWS_PROFILE
# export DISABLE_TELEMETRY=1
# export DISABLE_ERROR_REPORTING=1
export CLAUDE_CODE_ENABLE_TASKS=1
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Changes the task creation directory since /tmp/claude is shared
# export TMPDIR=$HOME/.tmp
export CLAUDE_CODE_TMPDIR=$HOME/tmp



export OPENAI_BASE_URL=http://aigw-service.vici.corp/v1

# Lumen Diff viewer
export LUMEN_AI_PROVIDER="openai"
export LUMEN_AI_MODEL="gpt-5.4-mini"

# liangshihlin-viciholdings
export GITLAB_HOST=gitlab.data.vici.corp
# SDK MCP Server Deploy token
# name: gitlab+deploy-token-13

# Harbor tokens
# vici-sdk-mcp-server gitlab-ci robot token
export HARBOR_ROBOT_USER='robot$datateam+liang'

export REPO_OS_OVERRIDE=linux
export REGISTRY_URL=http://localhost:44444/r

# Amp theme for eza (compat with eza < 0.20.0 which doesn't read theme.yml)
# Palette: accent #E7894C  fg #F2ECDD  muted #B8AFA0  red #D9634F
#          blue #6A9FCC  green #7C9B96  cyan #8FC4C4  yellow #E3A25A
export EZA_COLORS="di=38;2;231;137;76;1:ex=38;2;124;155;150;1:ln=38;2;106;159;204:bd=38;2;217;99;79;1:cd=38;2;217;99;79;1:so=38;2;184;175;160:pi=38;2;184;175;160:or=38;2;217;99;79;1:ur=38;2;242;236;221;1:uw=38;2;227;162;90;1:ux=38;2;124;155;150;1:ue=38;2;124;155;150;1:gr=38;2;242;236;221:gw=38;2;227;162;90:gx=38;2;124;155;150:tr=38;2;184;175;160:tw=38;2;184;175;160:tx=38;2;184;175;160:su=38;2;231;137;76:sf=38;2;184;175;160:xa=38;2;184;175;160:sn=38;2;242;236;221:sb=38;2;184;175;160:df=38;2;184;175;160:ds=38;2;143;196;196:uu=38;2;231;137;76;1:un=38;2;184;175;160:gu=38;2;242;236;221:gn=38;2;184;175;160:lc=38;2;184;175;160:ga=38;2;124;155;150:gm=38;2;227;162;90:gd=38;2;217;99;79:gv=38;2;106;159;204:gt=38;2;231;137;76:da=38;2;227;162;90:in=38;2;184;175;160:bl=38;2;184;175;160:hd=38;2;231;137;76;1;4"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

if command -v wt >/dev/null 2>&1; then eval "$(command wt config shell init zsh)"; fi

# source "$HOME/programs/kitty/lib/kitty/shell-integration/zsh/kitty.zsh"
# source "$HOME/programs/kitty/lib/kitty/shell-integration/zsh/completions/_kitty"

# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

[ -f $HOME/.proxy ] && source $HOME/.proxy

# Executor CLI (remote server at 172.21.10.105:4788)
# CLI's HTTP client doesn't grok CIDR NO_PROXY; add the literal host so it bypasses the proxy
export NO_PROXY="$NO_PROXY,172.21.10.105"

# Vite+ bin (https://viteplus.dev)
[[ -r "$HOME/.vite-plus/env" ]] && source "$HOME/.vite-plus/env"

# Secrets
# Rendered by chezmoi from gopass (dotfiles-secrets/*); mode 0600 and
# never committed. Regenerate with `chezmoi apply ~/.config/zsh/private`.
[[ -r "${ZDOTDIR:-$HOME/.config/zsh}/private/keys.zsh" ]] && \
  source "${ZDOTDIR:-$HOME/.config/zsh}/private/keys.zsh"
# export BEADS_DOLT_SERVER_SOCKET=/tmp/mysql.socket
