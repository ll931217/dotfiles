# ZDOTDIR=$HOME/.config/zsh
ANTIGEN_LOG=/tmp/antigen.log
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

antigen bundle thewtex/tmux-mem-cpu-load

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
[ -f $HOME/.config/zsh/functions.zsh ] && source $HOME/.config/zsh/functions.zsh
[ -f $HOME/.config/zsh/aliases.zsh ] && source $HOME/.config/zsh/aliases.zsh
[ -f $HOME/.config/zsh/env.zsh ] && source $HOME/.config/zsh/env.zsh
[ -f /opt/miniconda3/etc/profile.d/conda.sh ] && source /opt/miniconda3/etc/profile.d/conda.sh

autoload -Uz compinit && compinit

# Must be added after compinit for completions to work
eval "$(zoxide init zsh)"
eval "$(direnv hook zsh)"
eval "$(atuin init zsh)"

# bun completions
[ -s "/home/ll931217/.bun/_bun" ] && source "/home/ll931217/.bun/_bun"

# pnpm
export PNPM_HOME="/home/ll931217/.local/share/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C /usr/bin/terraform terraform

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/home/ll931217/google-cloud-sdk/path.zsh.inc' ]; then . '/home/ll931217/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/home/ll931217/google-cloud-sdk/completion.zsh.inc' ]; then . '/home/ll931217/google-cloud-sdk/completion.zsh.inc'; fi

export PATH=$PATH:/home/ll931217/.millennium/ext/bin

# Added by LM Studio CLI (lms)
export PATH="$PATH:/home/ll931217/.lmstudio/bin"
source /usr/share/doc/pkgfile/command-not-found.zsh

# opencode
export PATH=/home/ll931217/.opencode/bin:$PATH

[[ "$TERM_PROGRAM" == "kiro" ]] && . "$(kiro --locate-shell-integration-path zsh)"
