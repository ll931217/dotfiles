# General Aliases
alias cat="bat --color=always"
alias ls="exa -l --git --header --long"
alias rm="trash"
alias nv="nvim"
alias reload="exec zsh"

# CDs
alias ..='cd ../'
alias ...='cd ../../'
alias ....='cd ../../../'
alias cdg='cd ~/Documents/GitHub'

# Python
alias jsonp='python -m json.tool'
alias python='/usr/bin/python3'

# Load all aliases in directory
for file in ~/.aliases/*; do 
  if [ -f "$file" ]; then 
    . "$file" 
  fi 
done
