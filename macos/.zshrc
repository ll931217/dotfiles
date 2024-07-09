# Download antigen if you haven't already
if [[ ! -f $HOME/.config/antigen.zsh ]]; then
  curl -L git.io/antigen > $HOME/.config/antigen.zsh
fi
source $HOME/.config/antigen.zsh

# Load the oh-my-zsh's library.
antigen use oh-my-zsh

# Bundles from the default repo (robbyrussell's oh-my-zsh).
antigen bundle git
antigen bundle heroku
antigen bundle pip
antigen bundle lein
antigen bundle command-not-found

# Syntax highlighting bundle.
antigen bundle zsh-users/zsh-syntax-highlighting
antigen bundle zsh-users/zsh-autosuggestions
antigen bundle zsh-users/zsh-completions
antigen bundle zsh-users/zsh-history-substring-search
antigen bundle chrissicool/zsh-256color

# Tell Antigen that you're done.
antigen apply

[ -f $HOME/.zshrc.local ] && source $HOME/.zshrc.local
[ -f $HOME/.zshrc.fzf ] && source $HOME/.zshrc.fzf
[ -f $HOME/.bash_aliases ] && source $HOME/.bash_aliases

autoload -Uz compinit && compinit

# Must be added after compinit for completions to work
eval "$(zoxide init zsh)"
