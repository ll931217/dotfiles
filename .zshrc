# Source local config if exists
[ -f $HOME/.zshrc.local ] && source $HOME/.zshrc.local

# Download antigen if you haven't already
source $HOME/.config/antigen.zsh

# Source alias file if exists
[ -f $HOME/.bash_aliases ] && source $HOME/.bash_aliases

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
antigen bundle chrissicool/zsh-256color

# ZSH Theme
# Load the theme.
antigen theme romkatv/powerlevel10k

# Tell Antigen that you're done.
antigen apply
