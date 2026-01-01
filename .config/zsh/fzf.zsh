export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --glob "!.git/*"'
# export FZF_COMPLETION_TRIGGER='~~' # Change default trigger
export FZF_COMPLETION_OPTS='--border --info=inline'

_fzf_compgen_path() {
    fd --hidden --follow --exclude ".git" . "$1"
}

_fzf_compgen_dir() {
    fd --type d --hidden --follow --exclude ".git" . "$1"
}

_fzf_comprun() {
    local command=$1
    shift

    case "$command" in
        cd)           fzf "$@" --preview 'tree -C {} | head -200' ;;
        export|unset) fzf "$@" --preview "eval 'echo \$'{}" ;;
        ssh)          fzf "$@" --preview 'dig {}' ;;
        *)            fzf "$@" ;;
    esac
}

# fh - repeat history
fh() {
  eval $( ([ -n "$ZSH_NAME" ] && fc -l 1 || history) | fzf +s --tac | sed -E 's/ *[0-9]*\*? *//' | sed -E 's/\\/\\\\/g')
}

# fkill - kill processes - list only the ones you can kill. Modified the earlier script.
fkill() {
    local pid 
    if [ "$UID" != "0" ]; then
        pid=$(ps -f -u $UID | sed 1d | fzf -m | awk '{print $2}')
    else
        pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
    fi  

    if [ "x$pid" != "x" ]
    then
        echo $pid | xargs kill -${1:-9}
    fi  
}

# Install (one or multiple) selected application(s)
# using "brew search" as source input
# mnemonic [B]rew [I]nstall [P]ackage
bip() {
  local inst=$(brew search "$@" | fzf -m)

  if [[ $inst ]]; then
    for prog in $(echo $inst);
    do; brew install $prog; done;
  fi
}

# Update (one or multiple) selected application(s)
# mnemonic [B]rew [U]pdate [P]ackage
bup() {
  local upd=$(brew leaves | fzf -m)

  if [[ $upd ]]; then
    for prog in $(echo $upd);
    do; brew upgrade $prog; done;
  fi
}

# Delete (one or multiple) selected application(s)
# mnemonic [B]rew [C]lean [P]ackage (e.g. uninstall)
bcp() {
  local uninst=$(brew leaves | fzf -m)

  if [[ $uninst ]]; then
    for prog in $(echo $uninst);
    do; brew uninstall $prog; done;
  fi
}

# run npm script (requires jq)
fns() {
  local script
  script=$(\cat package.json | jq -r '.scripts | keys[] ' | sort | fzf) && npm run $(echo "$script")
}

# unalias z 2> /dev/null
# z() {
#   [ $# -gt 0 ] && _z "$*" && return
#   cd "$(_z -l 2>&1 | fzf --height 40% --nth 2.. --reverse --inline-info +s --tac --query "${*##-* }" | sed 's/^[0-9,.]* *//')"
# }

eval "$(fzf --zsh)"

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
