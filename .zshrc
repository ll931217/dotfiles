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
# git clone https://github.com/bhilburn/powerlevel9k.git
POWERLEVEL9K_MODE='nerdfont-complete'

source ~/Documents/GitHub/powerlevel9k/powerlevel9k.zsh-theme

POWERLEVEL9K_PROMPT_ON_NEWLINE=true
POWERLEVEL9K_MULTILINE_LAST_PROMPT_PREFIX="%(?:%{$fg_bold[green]%}➜ :%{$fg_bold[red]%}➜ )"
POWERLEVEL9K_MULTILINE_FIRST_PROMPT_PREFIX=""
POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(ssh dir vcs)
POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(status node_version time)

#POWERLEVEL9K_USER_ICON="\uF415" # 
POWERLEVEL9K_ROOT_ICON="\uF09C"
#POWERLEVEL9K_SUDO_ICON=$'\uF09C' # 
POWERLEVEL9K_TIME_FORMAT="%D{%H:%M}"
#POWERLEVEL9K_VCS_GIT_ICON='\uF408 '
#POWERLEVEL9K_VCS_GIT_GITHUB_ICON='\uF408 '
#
# Load the theme.
# antigen theme refined

# Tell Antigen that you're done.
antigen apply
