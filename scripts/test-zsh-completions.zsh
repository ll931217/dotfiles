#!/usr/bin/env zsh
# Drives a real interactive zsh in a pty and presses Tab. Fails if a tool's
# completion produces nothing — which is what happened silently for years while
# antigen's `compdef () {}` stub swallowed every compdef call.
# Usage: zsh scripts/test-zsh-completions.zsh [tool ...]

zmodload zsh/zpty
local -a tools=( $@ )
(( $#tools )) || tools=( t3 tv sesh gwq ast-grep gopass )
local -i fails=0
local -i ran=0

for tool in $tools; do
  if ! (( $+commands[$tool] )) && [[ ! -x "$HOME/.vite-plus/bin/$tool" ]]; then
    print "SKIP $tool (not installed)"; continue
  fi
  (( ran++ ))
  zpty -b Z zsh -i
  zpty -w Z ''
  sleep 1                        # let precmd run antigen's deferred compinit
  zpty -n -w Z "$tool "$'\t'
  sleep 2
  local out='' chunk
  while zpty -r -t Z chunk 2>/dev/null; do out+=$chunk; done
  zpty -d Z
  # Assert a real completion, not zsh's filename fallback: these tools all
  # describe their subcommands, so `_describe` prints "name  -- description".
  # Plain file completion never emits " -- ", so this catches the exact failure
  # mode where the completion is missing and zsh quietly lists files instead.
  if [[ $out == *" -- "* ]]; then
    print "PASS $tool (described subcommands present)"
  else
    print "FAIL $tool — Tab gave no described subcommands (filename fallback?)"
    (( fails++ ))
  fi
done

print ---
if (( fails )); then print "$fails failed"; exit 1; fi
if (( ran == 0 )); then print "no tools tested — nothing was verified"; exit 1; fi
print "all $ran completions working"
