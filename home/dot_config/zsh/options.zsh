### Start vi-mode configuration

# Enable vi mode
bindkey -v

# Use system clipboard for yank/paste
function zle-clipboard-copy {
  echo -n "$CUTBUFFER" | xclip -selection clipboard
}
zle -N zle-clipboard-copy

# Bind 'y' in visual mode to also copy to system clipboard
bindkey -M vicmd 'y' zle-clipboard-copy

# Change cursor shape for different vi modes
function zle-keymap-select {
  if [[ ${KEYMAP} == vicmd ]] ||
     [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'  # Block cursor
  elif [[ ${KEYMAP} == main ]] ||
       [[ ${KEYMAP} == viins ]] ||
       [[ ${KEYMAP} = '' ]] ||
       [[ $1 = 'beam' ]]; then
    echo -ne '\e[5 q'  # Beam cursor
  fi
}
zle -N zle-keymap-select

# Use beam shape cursor on startup
echo -ne '\e[5 q'

# Use beam shape cursor for each new prompt
preexec() { echo -ne '\e[5 q' ;}

# Reduce key delay (makes switching between modes faster)
export KEYTIMEOUT=1

### End vi-mode configuration
