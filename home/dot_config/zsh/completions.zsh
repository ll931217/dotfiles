# Native completion policy used with Znap and fzf-tab.
zmodload -i zsh/complist

unsetopt menu_complete
setopt auto_menu
setopt complete_in_word
setopt always_to_end

# Let fzf-tab own the selection UI while retaining smart native matching.
zstyle ':completion:*' menu no
zstyle ':completion:*' matcher-list \
  'm:{[:lower:][:upper:]}={[:upper:][:lower:]}' \
  'r:|=*' \
  'l:|=* r:|=*'
