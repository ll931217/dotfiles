##
## Aliases
##

alias sudo="sudo -E "

alias pgclia='PGPASSWORD="$(gopass show -o vici_pw)" pgcli -h 172.21.10.106 -U postgres -p 5432'

# Tmux
alias tmux="tmux -2"
alias tn="tmux -2 new -s"
alias ta="tmux -2 a -t"
alias tk="tmux -2 kill-session -t"
alias tka="tmux kill-server"
alias tl="tmux -2 list-sessions"
alias mux="tmuxinator"
alias start="tmuxinator start ."

alias zj="zellij"
alias zja="zellij a"
alias zjn="zellij -s"
alias zjk="zellij k"
alias zjka="zellij ka"
alias zjw="zellij web"
alias zjl="$HOME/.scripts/zellij-list-sessions.sh"
alias zjrc="pushd $HOME/.config/zellij/ ; $EDITOR config.kdl ; popd"

alias logout="pkill -KILL -u $USER"
alias genpw="openssl rand -base64 16"

alias k="kubectl"
alias tf="terraform"
alias tfw="terraform workspace"
alias tfg="terragrunt"

alias wclass="xprop | grep WM_CLASS | awk '{ print $4 }'"

alias mcp-inspector="vpx @modelcontextprotocol/inspector"

alias shadcn="vpx shadcn@latest"

alias cc='~/.local/bin/claude'
alias ccc='~/.local/bin/claude -c'
alias cx='codex --yolo'
# alias oc="opencode"

# History
# alias h='history -10000'
# alias hf='history -10000 | fzf'
# alias hl='history -10000 | less'
# alias hs='history -10000 | grep'
# alias hsi='history -10000 | grep -i'

# agent-deck
alias ad='agent-deck'
alias ada='agent-deck add'

# worktrunk
alias wsc='wt switch --create'
alias wrm='wt remove'
alias wtm='wt merge'

# Append
alias akn='curl https://raw.githubusercontent.com/forrestchang/andrej-karpthy-skills/main/CLAUDE.md > CLAUDE.md'
alias aka='curl https://raw.githubusercontent.com/forrestchang/andrej-karpthy-skills/main/CLAUDE.md >> CLAUDE.md'
alias aks='mkdir -p .claude/skills && curl -o .claude/skills/karpathy-guidelines.md https://raw.githubusercontent.com/forrestchang/andrej-karpthy-skills/main/.claude/skills/karpathy-guidelines.md'

alias mount_market_info='sshfs -o uid=$(id -u),gid=$(id -g) liang@172.21.10.109:/mnt/Market_Info ~/Remote/Market_Info/'

# Atuin - enhanced shell history
alias ats='atuin search'
alias atl='atuin history list'
alias atsync='atuin sync'
alias atdoc='atuin doctor'
alias atssh='atuin search ssh'
alias atsshl='atuin history list | grep -e "^ssh" | fzf'
alias atdk='atuin search docker'
alias atdkb='atuin search "docker build"'
alias atdkr='atuin search "docker run"'
alias atdkl='atuin history list | grep -i docker'
alias atgit='atuin search git'
alias atgitc='atuin search "git commit"'
alias atgitb='atuin search "git branch"'
alias atstat='atuin history list | cut -d" " -f2- | sort | uniq -c | sort -nr | head -20'
alias atfail='atuin search --filter "exit=1"'

alias atsr='atuin scripts run'

alias ld="lazydocker"
alias lg="lazygit"
alias lz="lazyssh"
alias pp="purple"

alias zshrc='cd ~ ; $EDITOR $HOME/.zshrc $HOME/.config/zsh/.zshrc $HOME/.config/zsh/aliases.zsh $HOME/.config/zsh/env.zsh $HOME/.config/zsh/functions.zsh ; cd - ; exec zsh'
alias nvrc='cd ~/.config/nvim ; $EDITOR init.lua ; cd -'
alias i3rc='cd ~/.config/i3/ ; $EDITOR ~/.config/i3/config ; cd -'

# Pretty print PATH
alias print_path="sed 's/:/\\n/g' <<< \"$PATH\""
alias format_csv="column -t -s,"
alias dos2unix="sed -i 's/\\r$//'"

alias ssh='TERM=xterm-256color ssh'

alias ubd="curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash"
alias upnpm="curl -fsSL https://get.pnpm.io/install.sh | sh -"
alias uzen="bash <(curl https://updates.zen-browser.app/appimage.sh)"
alias say="espeak"

alias glow="glow -p -w 0 -l"
alias jsonp="python -m json.tool"
alias run="pnpm run"
alias rl="exec zsh"
alias c="clear"
alias q="exit"
alias cleanram="sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'"
alias trim_all="sudo fstrim -va"
alias mtar='tar -zcvf' # mtar <archive_compress>
alias utar='tar -zxvf' # utar <archive_decompress> <file_list>
alias zip='zip -r'     # z <archive_compress> <file_list>
alias uz='unzip'       # uz <archive_decompress> -d <dir>
alias sr='source ~/.config/zsh/env.zsh'
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias n="nvim"
alias psg="ps aux | grep -v grep | grep -i -e VSZ -e"
alias mkdir="mkdir -p"
alias fm='yazi'
alias ls="eza -lgmM --icons=always --group-directories-first --time-style='+%Y-%m-%d %H:%M:%S'"
alias la="ls -a"
alias lt="ls --tree -L"
alias bat="batcat --color always"
alias cat="batcat --color=never --pager=never --plain"
# alias cat="mcat"
alias grep='grep --color=auto'
alias mv='mv -v'
alias cp='cp -vr'
alias rm='trash'

alias pull-all='for dir in */; do [ -d "$dir/.git" ] && echo "==> $dir" && git -C "$dir" pull; done'
alias notes="$EDITOR $HOME/vault/nodes.md"

alias -s csv="column -t -s','"
