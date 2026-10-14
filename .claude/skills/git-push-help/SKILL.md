---
name: git-push-help
description: Help the owner when git push or pull to GitHub fails to sign in ("Missing or invalid credentials", "failed to get: -25308", "Authentication failed", "No anonymous write access"), usually because the session is over SSH and the Mac's keychain is locked. Use when the owner pastes such an error or asks how to push from a remote session.
---

# Pushing to GitHub from a remote session

Claude never pushes (it is denied in the settings) and never types or asks for a password. This skill only tells the owner what to run.

## Why it fails

- Git gets the GitHub sign-in from the Mac's login keychain (`osxkeychain`). Error `-25308` means the keychain is locked and cannot ask for the password, which is what happens in an SSH session (the editor connected to the Mac remotely).
- The fallback, VS Code's sign-in helper (`vscode-git-….sock`, `ECONNREFUSED`), fails when the terminal outlived a reconnect of the editor window.

## Check

Whether this session is remote, without printing any address:

```bash
[ -n "$SSH_CONNECTION" ] && echo "remote (SSH) session" || echo "local session"
```

## What to tell the owner

In the same terminal they push from, the owner runs this and types the Mac password when asked:

```
security unlock-keychain ~/Library/Keychains/login.keychain-db
```

Then `git push` again. This worked on 2026-10-14.

- The keychain stays unlocked until it locks itself again (sleep, its idle timeout, or logging out), so the next push may need it again.
- Alternatives: open a new VS Code terminal and push (VS Code offers a GitHub sign-in), or push from Terminal at the Mac itself.
- If it still fails after unlocking, ask for the new error before suggesting anything else. Do not suggest storing a token in a file or in the remote URL.
