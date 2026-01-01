## ░▀▀█░█▀▀░█░█░█▀▄░█▀▀
## ░▄▀░░▀▀█░█▀█░█▀▄░█░░
## ░▀▀▀░▀▀▀░▀░▀░▀░▀░▀▀▀
##
## liang's Z-Shell configuration
## https://github.com/ll931217

# The git prompt's git commands are read-only and should not interfere with
# other processes. This environment variable is equivalent to running with `git
# --no-optional-locks`, but falls back gracefully for older versions of git.
# See git(1) for git-status(1) for a description of that flag.
#
# We wrap in a local function instead of exporting the variable directly in
# order to avoid interfering with manually-run git commands by the user.

export ZDOTDIR="$HOME/.config/zsh"

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
setopt hist_save_no_dups          # Don't save duplicates

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

# Oh-My-Zsh plugins from Zinit migration
znap source ohmyzsh/ohmyzsh plugins/colored-man-pages/colored-man-pages.plugin.zsh
znap source ohmyzsh/ohmyzsh plugins/command-not-found/command-not-found.plugin.zsh

# External binaries (exa and bat are now available system-wide)
# These are managed via system package manager instead of Zinit

# --------------------------------------------
# External tools (moved before completion for better startup)
# --------------------------------------------
eval "$(zoxide init zsh)"
eval "$(direnv hook zsh)"
eval "$(starship init zsh)"
eval "$(goose term init zsh)"
eval "$(atuin init zsh)"

# --------------------------------------------
# Source private config files
# --------------------------------------------
if [ -d "$ZDOTDIR/private" ]; then
  for file in "$ZDOTDIR/private"/*.zsh; do
    [ -f "$file" ] && source "$file"
  done
fi

# --------------------------------------------
# Your extra config files (conditional loading)
# --------------------------------------------

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

# Lazy load heavy configurations only when needed
# _lazy_load_heavy_configs() {
#   files=("functions" "aliases" "keys" "env", "fzf")
#   for file in "${files[@]}"; do
#     [ -f "$HOME/.config/zsh/$file.zsh" ] && source "$HOME/.config/zsh/$file.zsh"
#   done
# }

# Defer heavy configurations - trigger after first command
# autoload -Uz add-zsh-hook
# add-zsh-hook precmd _lazy_load_heavy_configs

while read file
do
  [ -f "$ZDOTDIR/$file.zsh" ] && source "$ZDOTDIR/$file.zsh"
done <<-EOF
  env
  keys
  fzf
  theme
  aliases
  functions
  utility
  options
  plugins
  keybinds
  prompt
EOF

# Enable grc
[[ -s "/etc/grc.zsh" ]] && source /etc/grc.zsh

# Auto activate python venv
[ -f /usr/share/zsh/plugins/zsh-auto-venv/auto-venv.zsh ] && source /usr/share/zsh/plugins/zsh-auto-venv/auto-venv.zsh

# Command not found with suggestions on how to install
[ -f /usr/share/doc/pkgfile/command-not-found.zsh ] && source /usr/share/doc/pkgfile/command-not-found.zsh

# vim:ft=zsh:nowrap
