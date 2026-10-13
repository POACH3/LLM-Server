# Private LLM Server

A private AI chat service that runs entirely on one Mac. The owner and a few trusted people open a web page and chat with a model running on that Mac. No prompt or reply is sent to any company.

This repository holds the start and stop scripts, the settings, and the project's documentation. It does not contain the model, any secrets, or anyone's conversations.

## How it works

```
browser on an approved device
        |
        |  Tailscale private network (encrypted end to end)
        v
   Open WebUI        the chat page and logins      this Mac only
        |
        v
      oMLX           runs the model                this Mac only
        |
        v
   model files       ~/models
```

| Part | What it does |
| --- | --- |
| [oMLX](https://github.com/jundot/omlx) | Runs the model on Apple Silicon and produces the answers |
| [Open WebUI](https://github.com/open-webui/open-webui) | The chat web page, accounts and logins |
| [Tailscale](https://tailscale.com) | A private network, so only approved devices can reach the page |

Both programs listen only on the Mac itself. The only way in from another device is through Tailscale.

## Status

The baseline works: the server runs, the owner and guests have chatted from their own devices, and guests' conversations are not saved. Still to come: usage logging per user, a way for the owner to reserve the server, a queue, and a status display. See [SPEC.md](SPEC.md) for the plan.

## Requirements

- A Mac with Apple Silicon and enough memory for the model
- macOS 15 or newer
- [Homebrew](https://brew.sh), [uv](https://docs.astral.sh/uv/), oMLX, Open WebUI and the Tailscale app
- A model in MLX format in `~/models`

The step-by-step record of how this Mac was set up is in [OVERVIEW.md](OVERVIEW.md), section 7.

## Setup on a new machine

1. Install the tools listed above and download a model into `~/models`.
2. Copy the example file and fill in your own values:

   ```bash
   cp local.env.example local.env
   ```

   It holds the Tailscale address guests use and the three port numbers. `local.env` is not in git.
3. Create the key Open WebUI uses to talk to oMLX, in a file named `omlx-api-key` in this folder, readable only by you. It is not in git.
4. Turn on the commit check, which stops a secret or your real address from being committed by accident:

   ```bash
   git config core.hooksPath git-hooks
   ```
5. Start the server, then open the chat page and create the first account, which becomes the admin.

## Day to day

| Task | Command |
| --- | --- |
| Start | `./llm-start` |
| Stop and free the model's memory | `./llm-stop` |

- Nothing starts by itself. After a reboot, run `./llm-start`.
- While stopped, the address shows the page in `offline/index.html`. A small program hands it out; `llm-stop` starts it and `llm-start` ends it. After a reboot, run `./llm-stop` to bring the page back.
- Stopping and starting does not sign anyone out.

To add a guest: share the Mac with them in Tailscale's admin console, have them sign up on the chat page, then approve their account in Open WebUI's Admin Panel.

## What is in this repository

| Path | What it is |
| --- | --- |
| `llm-start`, `llm-stop` | Start and stop both programs |
| `start-open-webui.sh` | Loads the settings and launches Open WebUI |
| `load-local-env.zsh` | Loads the address and ports from `local.env` for the scripts |
| `local.env.example` | The layout of `local.env`, with placeholder values |
| `git-hooks/pre-commit` | The check git runs before every commit to keep secrets out |
| `open-webui.env` | Open WebUI settings, with a comment on each. No secrets |
| `offline/index.html`, `offline-page.py` | The page shown while the server is stopped, and the small program that hands it out |
| `offline-message.txt` | Plain text shown instead if that program fails to start |
| [SPEC.md](SPEC.md) | How the project is meant to be built: goals, constraints, architecture, features, plans |
| [OVERVIEW.md](OVERVIEW.md) | What was actually done: decisions, setup, measurements and findings |
| [CLAUDE.md](CLAUDE.md), `.claude/` | Instructions and tooling for working on this project with Claude Code |

## What is deliberately not here

These stay on the Mac and are ignored by git:

| Item | Why |
| --- | --- |
| `local.env` | The real Tailscale address and port numbers |
| `LOGS.local.md` | The dated log of changes and decisions |
| `omlx-api-key`, `.webui_secret_key` | Secrets |
| `open-webui-data/` | Accounts, settings, saved chats and uploaded files |
| `*.log` | Server logs |
| Model files | Large, and downloaded separately |

A check runs before every commit to enforce this. `git-hooks/pre-commit` cancels a commit that includes any of the items above, the value of a secret pasted into another file, or the real Tailscale address. It is switched on by the `git config` step in the setup section, and you can confirm it with `git config core.hooksPath`, which should print `git-hooks`.

## Privacy

- Prompts and replies never leave the Mac. Open WebUI runs in offline mode, with update checks and outside services switched off.
- Guests' conversations are not saved. The admin's own are, unless a chat is set to temporary.
- Logs hold timings and token counts, never the text of a conversation.
- To produce an answer, the Mac has to see the prompt and reply while the request runs. Whoever operates the Mac is trusted not to record them.

More detail is in [OVERVIEW.md](OVERVIEW.md), section 5.
