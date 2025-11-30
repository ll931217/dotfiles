# --------------------------------------------
# Znap: the fast-as-hell plugin manager
# --------------------------------------------
if [[ ! -f ~/.znap/znap.zsh ]]; then
  git clone https://github.com/marlonrichert/zsh-snap.git ~/.znap
fi
source ~/.znap/znap.zsh

# --------------------------------------------
# Proper ZSH history configuration
# --------------------------------------------
HISTFILE="$HOME/.zsh_history"
HISTSIZE=50000
SAVEHIST=50000

setopt appendhistory              # Append, don't overwrite
setopt sharehistory               # Share history between sessions
setopt inc_append_history         # Write commands immediately
setopt hist_ignore_dups           # Ignore duplicates
setopt hist_ignore_all_dups
setopt hist_reduce_blanks         # Clean up whitespace
setopt hist_verify                # Don't run expanded history immediately
setopt extended_history           # Save timestamps
setopt hist_save_no_dups          # Don’t save duplicates

# --------------------------------------------
# Plugins (Znap auto-clones, caches & compiles)
# --------------------------------------------

# Change plugin home directory
zstyle ':znap:*' repos-dir ~/.config/zsh/plugins

# Git aliases from Oh-My-Zsh without Oh-My-Zsh
znap source ohmyzsh/ohmyzsh plugins/git/git.plugin.zsh

# Common Zsh plugins
znap source zsh-users/zsh-completions
znap source zsh-users/zsh-autosuggestions
znap source zsh-users/zsh-syntax-highlighting
znap source zsh-users/zsh-history-substring-search
znap source zdharma-continuum/history-search-multi-word

# Extra utilities
znap source thewtex/tmux-mem-cpu-load
znap source Aloxaf/fzf-tab
znap source hlissner/zsh-autopair
znap source chrissicool/zsh-256color
znap source MichaelAquilina/zsh-you-should-use

# --------------------------------------------
# External tools (moved before completion for better startup)
# --------------------------------------------
eval "$(zoxide init zsh)"
eval "$(direnv hook zsh)"
eval "$(starship init zsh)"
eval "$(goose term init zsh)"
eval "$(atuin init zsh)"

# --------------------------------------------
# Your extra config files (conditional loading)
# --------------------------------------------

# Load essential configs immediately
[ -f $HOME/.zshrc.local ] && source $HOME/.zshrc.local
[ -f $HOME/.zshrc.fzf ] && source $HOME/.zshrc.fzf

# Fast startup configs
[ -f /opt/miniconda3/etc/profile.d/conda.sh ] && source /opt/miniconda3/etc/profile.d/conda.sh

# --------------------------------------------
# Completion System
# --------------------------------------------
# Skip security checks for faster startup (run compinit -C)
autoload -Uz compinit && compinit -C

# --------------------------------------------
# External tools - remaining
# --------------------------------------------
# Bun completions
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"

autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C /usr/bin/terraform terraform
export PATH=$PATH:/home/ll931217/go/bin
