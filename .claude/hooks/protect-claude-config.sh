#!/bin/zsh
# PreToolUse hook for Bash. Stops Claude from changing its own permissions,
# hooks or rules through a shell command, which would get around the
# permission rules that cover the Edit and Write tools.
#   - Settings files (permissions): never. The owner pastes changes in.
#   - Hooks and rules: only through the Edit tool, where the owner is asked.
# Reading these files (cat, jq, grep, git diff and so on) is still allowed.
# Input: the tool call as JSON on stdin. Exit 2 blocks the command.

cmd="$(jq -r '.tool_input.command // empty')"
[ -n "$cmd" ] || exit 0

# Which protected area, if any, does the command mention?
area=""
if print -r -- "$cmd" | grep -Eq '\.claude/settings(\.local)?\.json|\.claude/settings\b|settings\.local\.json'; then
  area="settings"
elif print -r -- "$cmd" | grep -Eq '\.claude/hooks'; then
  area="hooks"
elif print -r -- "$cmd" | grep -Eq '\.claude/rules'; then
  area="rules"
fi
[ -n "$area" ] || exit 0

# Ignore harmless redirections of messages before looking for writes.
probe="$(print -r -- "$cmd" | sed -E 's/[0-9]*>[[:space:]]*\/dev\/null//g; s/[0-9]*>&[0-9]+//g')"

# Anything that can write, move, delete or run code against the file.
writers='>|(^|[^[:alnum:]_])(tee|mv|cp|rm|dd|ln|install|truncate|chmod|chown|touch|mkdir|rsync|patch|ed|vi|vim|nano|open|osascript)([^[:alnum:]_]|$)'
writers="$writers"'|sed[^|;&]*[[:space:]]-[a-zA-Z]*i|perl|python|ruby|node|awk[^|;&]*-i|swift'
writers="$writers"'|git[^|;&]*[[:space:]](checkout|restore|apply|stash|reset|clean|rm|mv)([[:space:]]|$)'

if print -r -- "$probe" | grep -Eq "$writers"; then
  case "$area" in
    settings) msg="Claude may not change its own permissions. Give the owner the exact text and ask them to paste it into the settings file." ;;
    hooks)    msg="hooks may only be changed with the Edit tool, after asking the owner. Not through a shell command." ;;
    rules)    msg="rules may only be created or changed with the Edit tool, after asking the owner. Not through a shell command." ;;
  esac
  print -r -- "Blocked by .claude/hooks/protect-claude-config.sh: $msg" >&2
  exit 2
fi
exit 0
