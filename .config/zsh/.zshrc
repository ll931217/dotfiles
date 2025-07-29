## ░▀▀█░█▀▀░█░█░█▀▄░█▀▀
## ░▄▀░░▀▀█░█▀█░█▀▄░█░░
## ░▀▀▀░▀▀▀░▀░▀░▀░▀░▀▀▀
##
## rxyhn's Z-Shell configuration
## https://github.com/rxyhn

# The git prompt's git commands are read-only and should not interfere with
# other processes. This environment variable is equivalent to running with `git
# --no-optional-locks`, but falls back gracefully for older versions of git.
# See git(1) for and git-status(1) for a description of that flag.
#
# We wrap in a local function instead of exporting the variable directly in
# order to avoid interfering with manually-run git commands by the user.

autoload -Uz compinit
compinit

function cheat(){ curl cheat.sh/"$@";  }

mkmv() {
  if [ -z "$1" ]; then
    echo "Usage: $0 <directory_name>"
    exit 1
  fi

  mkdir -p "$1" && cd "$1"
}


pwcp() {
  if [ -z "$1" ]; then
    echo "Usage: $0 <entry name>"
    exit 1
  fi
  rbw get "$(rbw list | rg -i $1 | fzf)" | wl-copy -n
}

function __git_prompt_git() {
  GIT_OPTIONAL_LOCKS=0 command git "$@"
}

# Outputs the name of the current branch
# Usage example: git pull origin $(git_current_branch)
# Using '--quiet' with 'symbolic-ref' will not cause a fatal error (128) if
# it's not a symbolic ref, but in a Git repo.
function git_current_branch() {
  local ref
  ref=$(__git_prompt_git symbolic-ref --quiet HEAD 2> /dev/null)
  local ret=$?
  if [[ $ret != 0 ]]; then
    [[ $ret == 128 ]] && return  # no git repo.
    ref=$(__git_prompt_git rev-parse --short HEAD 2> /dev/null) || return
  fi
  echo ${ref#refs/heads/}
}

function convert2gif() {
  if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: convert2gif <input> <output>"
    echo ""
    echo "Example: ffmpeg -i video.mp4 -f yuv4mpegpipe - | gifski -o anim.gif -"
    return 1
  fi
  ffmpeg -i $1 -f yuv4mpegpipe - | gifski -o $2 -
}

function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
	yazi "$@" --cwd-file="$tmp"
	if cwd="$(/usr/bin/cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
		builtin cd -- "$cwd"
	fi
	rm -f -- "$tmp"
}

function convert2gif() {
  if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: convert2gif <input> <output>"
    echo ""
    echo "Example: convert2gif video.mp4 ~/Videos/anim.gif"
    return 1
  fi

  ffmpeg -i $1 -f yuv4mpegpipe - | gifski -o $2 -
}

function watchservice() {
  if [ -z "$1" ]; then
    echo "Usage: watchservice <servicename>"
    echo ""
    echo "Example: watchservice nginx"
    return 1
  fi

  sudo journalctl -f -b -n 500 -o cat -u $1
}

checkport() {
  if [ -z "$1" ]; then
    echo "Usage: $0 <port>"
    exit 1
  fi

  lsof -i -P | grep LISTEN | grep :$1
}

# function checkport() {
#   if [ -z "$1" ]; then
#     echo "Usage: checkport <port>"
#     echo ""
#     echo "Example: checkport 3000"
#     return 1
#   fi
#
#   sudo lsof -nP -iTCP -sTCP:LISTEN | rg $1
# }

function killport() {
  if [ -z "$1" ]; then
    echo "Usage: killport <port>"
    return 1
  fi
  
  pid=$(sudo lsof -nP -iTCP -sTCP:LISTEN | grep $1 | awk '{print $2}')
  
  if [ -z "$pid" ]; then
    echo "No process found using port $1"
    return 1
  fi
  
  sudo kill -9 $pid
}

function mcd() {
  if [ -z "$1" ]; then
    echo "Usage: mcd <folder_name>"
    return 1
  fi

  mkdir $1 && cd $1
}

function timezsh() {
  shell=${1-$SHELL}
  for i in $(seq 1 10); do /usr/bin/time $shell -i -c exit; done
}

while read file
do 
  source "$ZDOTDIR/$file.zsh"
done <<-EOF
theme
env
aliases
utility
options
plugins
keybinds
prompt
plumbr
sunnyvale
leap
EOF

# vim:ft=zsh:nowrap
