##
## Aliases
##

# Tmux
alias tmux="tmux -2"
alias tn="tmux -2 new -s"
alias ta="tmux -2 a -t"
alias tk="tmux -2 kill-session -t"
alias tka="tmux kill-server"
alias tl="tmux -2 list-sessions"

alias zj="zellij"

alias tf="terraform"
alias tfw="terraform workspace"
alias tfg="terragrunt"

alias wclass="xprop | grep WM_CLASS | awk '{ print $4 }'"

alias k="kubectl"

alias oc="opencode"
alias ccusage="npx ccusage@latest"
alias ma="mcpm-aider"
# alias ff="fastfetch"
alias ff="fzf --preview 'bat --style=numbers --color=always {}'"

# History
alias h='history -10000'
alias hf='history -10000 | fzf'
alias hl='history -10000 | less'
alias hs='history -10000 | grep'
alias hsi='history -10000 | grep -i'

# Atuin - enhanced shell history
alias ats='atuin search'
alias atl='atuin history list'
alias atsync='atuin sync'
alias atdoc='atuin doctor'
alias atssh='atuin search ssh'
alias atsshl='atuin history list | grep ssh'
alias atdk='atuin search docker'
alias atdkb='atuin search "docker build"'
alias atdkr='atuin search "docker run"'
alias atdkl='atuin history list | grep -i docker'
alias atgit='atuin search git'
alias atgitc='atuin search "git commit"'
alias atgitb='atuin search "git branch"'
alias atstat='atuin history list | cut -d" " -f2- | sort | uniq -c | sort -nr | head -20'
alias atfail='atuin search --filter "exit=1"'

# GitHub Copilot
alias ghcu="gh extension upgrade gh-copilot"
alias ghce="gh copilot explain"
alias ghcs="gh copilot suggest"

alias ubd="curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash"
alias uwt="curl --proto '=https' --tlsv1.2 -LsSf https://github.com/max-sixty/worktrunk/releases/download/v0.8.2/worktrunk-installer.sh | sh"

alias zshrc='pushd ~ ; $EDITOR ~/.config/zsh/.zshrc ~/.config/zsh/aliases.zsh ~/.config/zsh/env.zsh ~/.config/zsh/keys.zsh ; popd ; exec zsh'
alias nvrc='cd ~/.config/nvim ; $EDITOR init.lua ; cd -'
alias hyprrc='cd ~/.config/hypr/ ; $EDITOR ~/.config/hypr/hyprland.conf ; cd -'
alias i3rc='cd ~/.config/i3/ ; $EDITOR ~/.config/i3/config ; cd -'

# Pretty print PATH
alias print_path="sed 's/:/\\n/g' <<< \"$PATH\""

alias pm="pulsemixer"
alias yv="youtube-viewer"
alias hn="hackernews_tui"

alias ssh='TERM=xterm-256color ssh'

alias upnpm="curl -fsSL https://get.pnpm.io/install.sh | sh -"
alias uzen="bash <(curl https://updates.zen-browser.app/appimage.sh)"
alias say="espeak"

alias jsonp="python -m json.tool"
alias lg="lazygit"
alias run="pnpm run"
alias rl="exec zsh"
alias c="clear"
alias q="exit"
alias cleanram="sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'"
alias trim_all="sudo fstrim -va"
alias mkgrub='sudo grub-mkconfig -o /boot/grub/grub.cfg'
alias mtar='tar -zcvf' # mtar <archive_compress>
alias utar='tar -zxvf' # utar <archive_decompress> <file_list>
# alias z='zip -r' # z <archive_compress> <file_list>
alias uz='unzip' # uz <archive_decompress> -d <dir>
alias sr='source ~/.config/zsh/env.zsh'
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias n="nvim"
alias nvd="neovide"
alias psg="ps aux | grep -v grep | grep -i -e VSZ -e" 
alias mkdir="mkdir -p"
alias fm='yazi'
alias pacin="pacman -Slq | fzf -m --preview 'cat <(pacman -Si {1}) <(pacman -Fl {1} | awk \"{print \$2}\")' | xargs -ro sudo pacman -S"
alias yayin="yay -Slq | fzf -m --preview 'cat <(yay -Si {1}) <(yay -Fl {1} | awk \"{print \$2}\")' | xargs -ro yay -S"
alias pacrem="pacman -Qq | fzf --multi --preview 'pacman -Qi {1}' | xargs -ro sudo pacman -Rns"
alias pac="pacman -Q | fzf"
alias cleanpac='sudo pacman -Rns $(pacman -Qtdq); yay -c'
alias installed="grep -i installed /var/log/pacman.log | fzf"
alias ls="eza --color=always --icons=always --group-directories-first"
alias l="ls -l"
alias la="ls -a"
alias lla="ls -la"
alias lt="ls --tree"
alias bat="bat --color=always"
alias cat="bat --plain --color=auto --pager=never"
alias grep='grep --color=auto'
alias mv='mv -v'
alias cp='cp -vr'
# alias rm='rm -vr'
alias rm='trash'

# vim:ft=zsh
