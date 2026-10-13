# Secrets and private data

- Never print, quote, log or commit the contents of `omlx-api-key` or `.webui_secret_key`. When a command needs the key, read it inside the command (`"$(cat ./omlx-api-key)"`) and mask it in any output you show.
- Never ask the owner for a password and never type one. Account creation, sign-in, system approvals and anything needing the Mac password are done by the owner.
- Never log in to Open WebUI as the owner or a guest, and never forge a login token, even though the signing key is on disk.
- `open-webui-data/webui.db` holds accounts, password hashes and the owner's saved chats. Read it only for counts, roles and saved settings. Do not read emails, password hashes or chat text.
- Never record the text of anyone's prompt or reply, in logs, documents or commits. Usage records hold who, when, which model, how many tokens and how long. Nothing else.
- Nothing may send prompts, replies or documents off this Mac. Ask the owner before adding any dependency or setting that contacts an outside service.
- The real Tailscale address, tailnet name, machine name, Tailscale IP and port numbers live only in `local.env` and `CLAUDE.local.md`, which git ignores. In every tracked file, commit message and document use the placeholders (`$TAILSCALE_HOST`, `$OMLX_PORT`, `$WEBUI_PORT`, `$OFFLINE_PORT`, `$RELAY_PORT`, `(tailnet name)`, `(machine name)`, `(Tailscale IP)`). When pasting command output into a document, replace the real values first.
- The repository is local and private. `OVERVIEW.md` still describes how the server is secured and where its weak spots are; review it before the repository is ever made public.
- A check in git-hooks/pre-commit cancels any commit containing a secret, private data, or the real Tailscale address; never skip it with --no-verify.
