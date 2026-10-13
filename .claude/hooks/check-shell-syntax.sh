#!/bin/zsh
# PostToolUse hook for Edit and Write. After a shell script in this project is
# changed, checks that it still parses. Exit 2 reports the error to Claude.

f="$(jq -r '.tool_response.filePath // .tool_input.file_path // empty')"
[ -n "$f" ] && [ -f "$f" ] || exit 0

case "${f:t}" in
  llm-start|llm-stop|*.sh|*.zsh) ;;
  *) exit 0 ;;
esac

# Use the interpreter named on the script's first line; default to zsh.
shell=zsh
head -n 1 "$f" | grep -q 'bash' && shell=bash
head -n 1 "$f" | grep -Eq '/sh( |$)' && shell=sh

if ! out="$($shell -n "$f" 2>&1)"; then
  print -r -- "Syntax error in ${f:t} ($shell -n):" >&2
  print -r -- "$out" >&2
  exit 2
fi
exit 0
