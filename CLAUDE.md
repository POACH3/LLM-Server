# Private LLM Server

A private AI chat service on the owner's Mac Studio (M1 Max, 64GB) for the owner and a few trusted users. A model runs locally under oMLX, Open WebUI provides the chat page and logins, and Tailscale makes the page reachable from approved devices. No prompt or reply may leave the Mac.

## Read first

- [SPEC.md](SPEC.md): how the owner wants this built. Goals, constraints, architecture, features, plans. Start with its Handoff section.
- [OVERVIEW.md](OVERVIEW.md): what was actually done. Sections 1 to 5 are the short summary; section 10 is the as-built reference; section 12 lists cautions learned the hard way.
- [LOGS.local.md](LOGS.local.md) (not in git): the dated log of high-level changes and decisions. Its last rows say what happened most recently.

## How it fits together

```
browser -> Tailscale (https://$TAILSCALE_HOST) -> Open WebUI 127.0.0.1:$WEBUI_PORT -> relay 127.0.0.1:$RELAY_PORT -> oMLX 127.0.0.1:$OMLX_PORT -> model in ~/models
```

The real address and port numbers are in `local.env` (not in git), which every script reads, and are listed for you in `CLAUDE.local.md` (not in git). Tracked files use the placeholders `$TAILSCALE_HOST`, `$OMLX_PORT`, `$WEBUI_PORT`, `$OFFLINE_PORT` and `$RELAY_PORT`. Never write the real values into a tracked file.

The relay (`relay.py`, the first slices of SPEC.md's gatekeeper) does two jobs. It records one row per chat request in `usage.csv`: who, when, which model, how many tokens, how long, never the text (F12, M2a). And it is where the owner reserves the server: while reserved, new chat requests from anyone but an admin are refused with a clear message (F4, M2b; switched with `./llm-reserve`). A badge in the chat page (`chat-page/loader.js`) shows everyone free, in use or reserved; it reads the relay's state through the address `/llm-status`. For an admin the badge is also the switch: a click goes to `/llm-reserve`, and the relay checks the sender's sign-in with Open WebUI before changing anything.

## Commands

| Task | Command |
| --- | --- |
| Start both servers | `./llm-start` |
| Stop both and free the model's memory | `./llm-stop` |
| Reserve for the owner, release, or show the state | `./llm-reserve on`, `off`, `status` |
| See what is running | `./.claude/skills/server-status/status.sh` |

Starting and stopping affects the owner's guests. Ask before running either.

## What is in this folder

| Path | What it is | In git |
| --- | --- | --- |
| `llm-start`, `llm-stop`, `start-open-webui.sh` | Start and stop scripts (zsh) | Yes |
| `relay.py` | The relay between Open WebUI and oMLX: usage records and the owner's reservation (started and stopped with the rest) | Yes |
| `chat-page/loader.js` | The status badge shown in the chat page; `llm-start` copies it into `open-webui-static/` after Open WebUI is up | Yes |
| `open-webui-static/` | Open WebUI's page extras, which it empties and refills at every start | No |
| `llm-reserve` | Reserve the server for the owner, release it, or show its state (zsh) | Yes |
| `usage.csv` | The usage records the relay writes | No |
| `open-webui.env` | Open WebUI settings, commented, no secrets | Yes |
| `offline/index.html`, `offline-page.py` | The page shown at the Tailscale address while stopped, and the small program that hands it out (started by `llm-stop`, ended by `llm-start`) | Yes |
| `offline-message.txt` | Plain text shown instead if the offline page program fails to start | Yes |
| `local.env.example`, `load-local-env.zsh` | Layout of the local values file, and the loader the scripts share | Yes |
| `local.env`, `CLAUDE.local.md` | This Mac's real address and ports | No |
| `LOGS.local.md` | The dated log of high-level changes and decisions | No |
| `SPEC.md`, `OVERVIEW.md` | The two project documents | Yes |
| `README.md` | Short introduction for someone opening the repository | Yes |
| `omlx-api-key`, `.webui_secret_key` | Secrets | No |
| `open-webui-data/` | Accounts, settings database, saved chats, uploads | No |
| `*.log` | Server logs | No |

Outside this folder: models in `~/models`, oMLX's own settings and cache in `~/.omlx`, Open WebUI installed as a pinned uv tool under `~/.local/share/uv/tools/open-webui`.

## Rules that matter most

The full rules are in `.claude/rules/`. The ones most likely to be broken by accident:

1. **One step at a time.** Do a step, report, and wait for the owner's go-ahead.
2. **Never print a secret or handle a password.** The owner does every sign-in and system approval.
3. **Never record what anyone typed or what the model replied.**
4. **Never hard-code a model name.**
5. **Nothing auto-starts or auto-restarts.** Everything listens on `127.0.0.1` only.
6. **Log only high-level changes and decisions**, in `LOGS.local.md` (use the `record-change` skill). Routine operation and document edits do not need a row.

## Things that will trip you up

- Many Open WebUI settings are saved in its database on first start and then ignore `open-webui.env`. See the `change-setting` skill.
- oMLX does not remember its API key. A plain `omlx serve` runs with no key; always use `./llm-start`.
- `open-webui.env` is loaded as shell. Quote values containing `;` or spaces.
- Admins are exempt from Open WebUI's "nothing saved" rule. Guests' chats are not stored; the owner's are.
- Stop can fail for a guest whose phone has slept, leaving a reply generating in the background. Replies are capped at 20,000 tokens for that reason.
- Tailscale's Mac app cannot serve files, only a port or plain text. That is why the offline page has its own small program on `$OFFLINE_PORT`, which does not come back after a reboot.

## Claude Code setup in this repository

- `.claude/settings.json`: denies reading the secret files and the data folder with the Read tool; denies committing, pushing and editing any settings file; asks before start, stop, history changes, and edits to rules or hooks; registers two hooks.
- `git-hooks/pre-commit`: a git hook, not a Claude one. Git runs it before every commit, whoever makes it, and cancels a commit that includes a secret file, the database, a log, `local.env`, the key's value, or the real Tailscale address. Switched on with `git config core.hooksPath git-hooks`.
- `.claude/hooks/check-shell-syntax.sh`: after a script is edited, checks that it still parses.
- `.claude/hooks/protect-claude-config.sh`: blocks shell commands that would change the settings files, the hooks or the rules.
- `.claude/skills/`: `server-status`, `record-change`, `change-setting`.
- `.claude/rules/`: secrets, working with the owner, documentation, scripts and code, Claude's own configuration.
- `.claude/output-styles/one-step.md`: an optional reply style matching how the owner likes to work. Not switched on by default.
