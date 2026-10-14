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
   relay             records usage; owner's reserve this Mac only
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

The baseline works: the server runs, the owner and guests have chatted from their own devices, and guests' conversations are not saved. Usage is recorded per user (who, when, which model, how many tokens, how long; never the text). The owner can reserve the server with `./llm-reserve on`, and a badge in the chat page shows everyone whether it is free, in use or reserved. The owner can also reserve and release by clicking that badge. Still to come: a queue. See [SPEC.md](SPEC.md) for the plan.

## Performance on M1 Max 64GB

Every figure here was measured on one machine: a **Mac Studio, M1 Max (10-core CPU, 24-core GPU), 64GB**, running oMLX 0.7.0. One person at a time, nobody else using the server. Through the chat page, the first message of each chat is a few seconds slower than these figures, because Open WebUI adds its own instructions to it. Answer quality and several users at once have not been measured. More detail is in [OVERVIEW.md](OVERVIEW.md), section 8.

### Qwen3.6-35B-A3B, 4-bit (`mlx-community/Qwen3.6-35B-A3B-4bit`)

The everyday model: 35B parameters, about 3B used per word.

**Short prompts** (2026-10-12; about 30 tokens in, 300 out; averages of 15 runs, straight at the model server):

| | |
| --- | --- |
| Writing speed | 69.9 tokens per second |
| Wait for the first word, model loaded | 0.21 s |
| Wait for the first word when the other model must be swapped out first | 12.9 s (9.1 to 15.1, 5 swaps) |
| Memory once loaded | 19.3GB |

**Long documents** (2026-10-14; single readings, through the relay; the text was Python source code; [`tests/long-document-test`](tests/long-document-test) repeats it):

| Prompt size (tokens) | First question: wait for the first word | Follow-up: wait for the first word | Writing speed | Peak memory |
| --- | --- | --- | --- | --- |
| 11,000 | 20 s | 0.5 s | 59 tokens/s | 23GB |
| 87,500 | 6 min | 1.7 s | 34 tokens/s | 25GB |
| 109,400 | 8.6 min | 2.1 s | 30 tokens/s | 25GB |

The first question about a long document is slow because the model has to read all of it, and reading slows as the text grows (about 540 tokens per second at 11,000 tokens, about 210 at 109,000). Follow-up questions in the same chat start within about 2 seconds, because oMLX keeps what it has already read. Memory is not the limit: a 100,000-token conversation used at most 25GB.

### Laguna XS 2.1, 6-bit (`mlx-community/Laguna-XS-2.1-6bit`)

Poolside's coding model: 33B parameters, about 3B used per word.

**Short prompts** (2026-10-12; same method as above):

| | |
| --- | --- |
| Writing speed | 52.1 tokens per second |
| Wait for the first word, model loaded | 0.25 s |
| Wait for the first word when the other model must be swapped out first | 8.2 s (8.1 to 8.3, 5 swaps) |
| Memory once loaded | 25.7GB |

**Long documents:** not yet measured.

### Switching models

The two models do not stay in memory together. Choosing the other one in the chat unloads the current one (about 4 s) and loads the other, which is the swap time shown above.

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
| Reserve the server for the owner, release it, or see its state | `./llm-reserve on`, `off`, `status` |

- Nothing starts by itself. After a reboot, run `./llm-start`.
- While stopped, the address shows the page in `offline/index.html`. A small program hands it out; `llm-stop` starts it and `llm-start` ends it. After a reboot, run `./llm-stop` to bring the page back.
- Stopping and starting does not sign anyone out.

To add a guest: share the Mac with them in Tailscale's admin console, have them sign up on the chat page, then approve their account in Open WebUI's Admin Panel.

## What is in this repository

| Path | What it is |
| --- | --- |
| `llm-start`, `llm-stop` | Start and stop both programs |
| `start-open-webui.sh` | Loads the settings and launches Open WebUI |
| `relay.py` | Sits between Open WebUI and oMLX. Records usage per request in `usage.csv`, and refuses guests' requests while the owner has reserved the server |
| `chat-page/loader.js` | The status badge added to the chat page (free, in use, reserved) |
| `chat-page/branding.js`, `custom.css`, `blank.png` | Remove Open WebUI's name and logos from the page, without changing its installed files |
| `llm-reserve` | The owner's command to reserve the server, release it, or see its state |
| `llm-usage` | Summarizes the usage records: per person and per model, for the last day, week and all time |
| `tests/long-document-test`, `tests/build-long-prompt.py` | Times models on long prompts of exact sizes, prose or code (first question and a follow-up), through the relay |
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
| `usage.csv` | Usage records |
| Model files | Large, and downloaded separately |

A check runs before every commit to enforce this. `git-hooks/pre-commit` cancels a commit that includes any of the items above, the value of a secret pasted into another file, or the real Tailscale address. It is switched on by the `git config` step in the setup section, and you can confirm it with `git config core.hooksPath`, which should print `git-hooks`.

## Privacy

- Prompts and replies never leave the Mac. Open WebUI runs in offline mode, with update checks and outside services switched off.
- Guests' conversations are not saved. The admin's own are, unless a chat is set to temporary.
- Logs and usage records hold who, when, timings and token counts, never the text of a conversation.
- To produce an answer, the Mac has to see the prompt and reply while the request runs. Whoever operates the Mac is trusted not to record them.

More detail is in [OVERVIEW.md](OVERVIEW.md), section 5.
