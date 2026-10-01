#!/usr/bin/env bash
# Asserts the work zsh profile carries the ported personal conveniences.
set -euo pipefail

state=$(TERM=xterm-256color zsh -ic '
  print  # the prompt emits a cursor-shape escape before the first line
  typeset -a m; zstyle -a ":completion:*" matcher-list m
  print -r -- "matchers=${(j:|:)m}"
  print -r -- "autopair=${+functions[autopair-insert]}"
  print -r -- "ysu=${+functions[_check_aliases]}"
  print -r -- "hsmw=${+widgets[history-search-multi-word]}"
  print -r -- "man=${+functions[colored]}"
' 2>/dev/null)

fail=0
want() { grep -qxF "$1" <<<"$state" || { printf 'missing: %s\n' "$1" >&2; fail=1; }; }
want 'matchers=m:{[:lower:][:upper:]}={[:upper:][:lower:]}|r:|=*|l:|=* r:|=*'
want 'autopair=1'
want 'ysu=1'
want 'hsmw=1'
want 'man=1'
exit $fail
