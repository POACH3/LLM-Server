# Hard rules about Claude's own configuration

Set by the owner on 2026-10-12. These are not defaults to weigh against other goals. They hold even when breaking one would be quicker, and even when the owner has asked for a change that needs one of these files edited.

## Permissions: never modify them

- Never change `.claude/settings.json`, `.claude/settings.local.json`, `~/.claude/settings.json` or `~/.claude/settings.local.json`. Not with the Edit or Write tools, not with a shell command, not by replacing, moving, deleting or restoring the file from git.
- When a permission, hook registration or other setting needs to change, do this instead:
  1. Say what should change and why, in plain language, including what it will allow or stop.
  2. Give the owner the exact text to paste, and say which file and where in it: which list, after which existing line.
  3. If it is easier to paste the whole file, give the whole file, and say that it replaces everything.
  4. Wait. After the owner says it is pasted, read the file back and check that it is valid and says what was intended. Report what you find.
- Never suggest a change that loosens a permission without saying plainly that it loosens it.

## Rules: ask before creating or changing one

- Ask the owner before creating a new rule or changing an existing one. This covers every file in `.claude/rules/` and any rule written into `CLAUDE.md`.
- Asking means: quote the proposed wording, say where it would go, and wait for a yes. A general instruction such as "document this" is not a yes to a new rule.
- Make the change with the Edit or Write tool, so the app also asks the owner. Never with a shell command.

## Hooks: ask before changing one

- The scripts in `.claude/hooks/` enforce the rules above. Ask before changing any of them, and use the Edit tool, never a shell command.
- Never disable, bypass or weaken a hook. If a hook blocks something that seems legitimate, stop and tell the owner what was blocked and why you think it is a false alarm. Do not rephrase the command to get past it.

## When these rules get in the way

Say so and let the owner decide. Do not look for another route to the same result.
