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

antigen bundle zsh-users/zsh-completions
antigen bundle zsh-users/zsh-autosuggestions
antigen bundle zsh-users/zsh-syntax-highlighting
antigen bundle zsh-users/zsh-history-substring-search

antigen bundle Aloxaf/fzf-tab
antigen bundle junegunn/fzf-bin
antigen bundle hlissner/zsh-autopair
antigen bundle chrissicool/zsh-256color
antigen bundle MichaelAquilina/zsh-you-should-use
antigen bundle zdharma-continuum/history-search-multi-word

# Tell Antigen that you're done.
antigen apply

[ -f $HOME/.zshrc.local ] && source $HOME/.zshrc.local
[ -f $HOME/.zshrc.fzf ] && source $HOME/.zshrc.fzf
[ -f $HOME/.bash_aliases ] && source $HOME/.bash_aliases

autoload -Uz compinit && compinit

# Must be added after compinit for completions to work
eval "$(zoxide init zsh)"
