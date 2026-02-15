#!/bin/bash
# vibereps tab completion for bash and zsh

if [ -n "$ZSH_VERSION" ]; then
  # Native zsh completion
  _vibereps() {
    local -a commands
    commands=(
      '--pause:Pause until end of day or specified timestamp'
      '--resume:Resume tracking'
      '--toggle:Toggle pause on/off'
      '--status:Check pause status'
      '--list-exercises:List available exercises'
      '--help:Show help'
    )
    _describe 'command' commands
  }
  compdef _vibereps vibereps
else
  # Bash completion
  _vibereps_completions() {
    local cur
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=( $(compgen -W "--pause --resume --toggle --status --list-exercises --help" -- "$cur") )
    return 0
  }
  complete -F _vibereps_completions vibereps
fi
