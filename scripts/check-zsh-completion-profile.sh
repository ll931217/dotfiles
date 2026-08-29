#!/usr/bin/env bash

set -euo pipefail

shell_state=$(TERM=xterm-256color env -u ZDOTDIR zsh -lic '
  print -r -- "autosuggest_strategy=${(j:,:)ZSH_AUTOSUGGEST_STRATEGY}"
  typeset -a matchers
  zstyle -a ":completion:*" matcher-list matchers
  print -r -- "matcher_list=${(j:|:)matchers}"
  typeset menu_style
  zstyle -s ":completion:*:*:*:*:*" menu menu_style
  print -r -- "menu_style=$menu_style"
  print -r -- "completion_options=$options[completeinword],$options[alwaystoend]"
  print -r -- "tab_binding=$(bindkey "^I")"
  print -r -- "fzf_tab_widget=${widgets[fzf-tab-complete]-}"
' 2>/dev/null)

state_value() {
  sed -n "s/.*$1=//p" <<<"$shell_state"
}

autosuggest_strategy=$(state_value autosuggest_strategy)
if [[ ",$autosuggest_strategy," != *,history,completion, ]]; then
  printf 'expected autosuggestion strategies to end with history,completion; got %s\n' \
    "$autosuggest_strategy" >&2
  exit 1
fi

matcher_list=$(state_value matcher_list)
expected_matchers='m:{[:lower:][:upper:]}={[:upper:][:lower:]}|r:|=*|l:|=* r:|=*'
if [[ "$matcher_list" != "$expected_matchers" ]]; then
  printf 'unexpected completion matcher list: %s\n' "${matcher_list:-<unset>}" >&2
  exit 1
fi

menu_style=$(state_value menu_style)
if [[ "$menu_style" != no ]]; then
  printf 'expected fzf-tab-compatible completion menu policy; got %s\n' \
    "${menu_style:-<unset>}" >&2
  exit 1
fi

completion_options=$(state_value completion_options)
if [[ "$completion_options" != on,on ]]; then
  printf 'expected complete_in_word and always_to_end; got %s\n' \
    "$completion_options" >&2
  exit 1
fi

tab_binding=$(state_value tab_binding)
fzf_tab_widget=$(state_value fzf_tab_widget)
if [[ "$tab_binding" != *' fzf-tab-complete' || -z "$fzf_tab_widget" ]]; then
  printf 'expected Tab to use the fzf-tab completion widget; got %s (%s)\n' \
    "${tab_binding:-<unset>}" "${fzf_tab_widget:-<unset>}" >&2
  exit 1
fi

fixture_dir=$(mktemp -d /tmp/zsh-completion-profile.XXXXXX)
cleanup_fixture() {
  find "$fixture_dir" -depth -delete
}
trap cleanup_fixture EXIT
touch "$fixture_dir/SmartCompletionCandidate"

run_completion_probe() {
  local completion_input=$1
  local probe_output

  if ! probe_output=$(
    ZSH_COMPLETION_FIXTURE_DIR="$fixture_dir" \
      ZSH_COMPLETION_POLICY="$HOME/.config/zsh/completions.zsh" \
      ZSH_COMPLETION_NEWLINE=$'\n' \
      ZSH_COMPLETION_INPUT="cat $completion_input"$'\t' \
      timeout 5s zsh -fc '
        zmodload zsh/zpty
        zpty completion /usr/bin/zsh -f
        zpty -r completion line "*"
        zpty -w completion \
          "PS1=\$(printf \"\\120\\122\\117\\102\\105\\076\\040\"); autoload -Uz compinit; compinit -C; source ${(q)ZSH_COMPLETION_POLICY}; cd ${(q)ZSH_COMPLETION_FIXTURE_DIR}${ZSH_COMPLETION_NEWLINE}"
        zpty -r completion line "*PROBE>*"
        zpty -w completion "$ZSH_COMPLETION_INPUT"
        zpty -r completion line "*SmartCompletionCandidate*"
        print -r -- "$line"
        zpty -d completion
      '
  ); then
    printf 'completion probe %s timed out or failed\n' "$completion_input" >&2
    return 1
  fi

  printf '%s' "$probe_output"
}

for completion_input in smart CompletionCandidate; do
  completion_probe=$(run_completion_probe "$completion_input")
  if [[ "$completion_probe" != *SmartCompletionCandidate* ]]; then
    printf 'completion probe %s did not produce SmartCompletionCandidate\n' \
      "$completion_input" >&2
    exit 1
  fi
done

printf 'personal Zsh completion profile is configured correctly\n'
