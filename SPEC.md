# Private LLM Server: Design Spec

- **As of:** 2026-10-14 (first written 2026-09-30)
- **Status:** M0 (baseline) is complete: the server runs and guests have used it. M1 (measure) has begun with two investigations. The relay is done (closed by the owner 2026-10-14): it records usage (M2a), summarized by `llm-usage`, and lets the owner reserve the server from the Mac or by clicking the badge in the chat page (M2b). The badge shows everyone free, in use or reserved.
- **What this file is:** how the owner wants this project built: goals, constraints, architecture, features and plans.
- **Companion file:** [OVERVIEW.md](OVERVIEW.md) holds everything about what was actually done: decisions, what is installed and how it is configured, measurements, findings, and notes from each tool's documentation.
- **Audience:** a Claude agent (or human) implementing or extending this project.

## Handoff (read this first)

**Project.** A private LLM server on the owner's Mac Studio (M1 Max, 64GB), on a budget, for the owner plus 1-3 friends or family. MVP = M0 (oMLX + Open WebUI + Tailscale + one everyday model; done) then M1 (measure, pick the server, decide on a hardware upgrade).

**Read next.** Sections 1-3 here for goals and constraints, then OVERVIEW.md sections 1-5 for what exists today, then the section for the task at hand.

**How the owner wants to work.** "Slow down. Take each thing one at a time. Be explicit." One step per message, then wait for the owner's go-ahead. Explain in plain language; the owner asks for simpler wording when an explanation is too technical. In a Claude Code session on the Mac the assistant runs commands itself; anything needing a password, an account, a system approval or a browser sign-in is done by the owner. Never print or ask for passwords or the API key. Decisions that are the owner's go through a short multiple-choice question.

**Where we are (updated 2026-10-14).** M0 is done, and so are M2a and M2b. Nothing is half-finished on the Mac. Whether the server is running changes often; check with the `server-status` skill rather than trusting this file.

**Guard hook: confirmed live 2026-10-12.** `.claude/hooks/protect-claude-config.sh` blocks shell commands that would change Claude's settings, hooks or rules. It was checked at the start of a new session with this harmless command, which only prints text, and the command was blocked as intended:

```
echo "probe only, changes nothing: cp .claude/settings.json"
```

No check is needed at the start of each session. Run the probe again only after the hook or its registration in `.claude/settings.json` has changed, in a session started after the change, because hooks load when a session starts. If it is not blocked then, tell the owner and give them corrected text to paste into `.claude/settings.json`; never edit that file yourself. Record the result in the OVERVIEW.md log.

**State of the repository.** This folder (`~/Documents/Code/llm-server`) is a git repository. The owner made four commits on 2026-10-12 and pushed them to GitHub (`origin`). The GitHub repository is **public**, by the owner's choice (2026-10-14): treat every tracked file and commit as published. `git commit` and `git push` are denied to Claude in `.claude/settings.json`: the owner makes commits. If the owner asks for help preparing one, show the exact list of files and stop. A secret-blocking check, `git-hooks/pre-commit`, runs before every commit, whoever makes it, and cancels one that includes a secret file, private data, a secret's value, or the real Tailscale address; it is switched on by `git config core.hooksPath git-hooks`, which `git config core.hooksPath` should confirm (it does as of 2026-10-14). Whether it was on for those four commits was not confirmed. Secrets, the database, logs, `local.env` and `CLAUDE.local.md` are in this folder but ignored by git.

**Rules added late in that session, easy to miss.** Claude never modifies its own permissions (the settings files): give the owner the exact text to paste, then read it back. Claude asks before creating or changing any rule or hook. The real Tailscale address and port numbers live only in `local.env` and `CLAUDE.local.md`; every tracked file uses `$TAILSCALE_HOST`, `$OMLX_PORT`, `$WEBUI_PORT`, `$OFFLINE_PORT` and `$RELAY_PORT`. Full text in `.claude/rules/`.

**Done recently (2026-10-12 to 2026-10-14).**
- **Relay (F12, M2a; F4, M2b).** `relay.py` records usage to `usage.csv`; `llm-usage` summarizes it per person and per model (messages, time, tokens, length-cap hits, refusals) for the last 24 hours, 7 days and all time, plus the longest requests. The owner reserves with `./llm-reserve` or the badge in the chat page. The owner closed the relay as done on 2026-10-14 with these untested: a guest's temporary chat, Stop and a long reply through the relay, and the owner's own test of the badge switch in a browser.- **Permanent guest notice:** skipped by the owner on 2026-10-14.

**What the owner wants next.**
1. **Remove "Open WebUI" branding.** Owner's choice 2026-10-14: no replacement name; the tab reads "Private LLM" with the OI icon kept; every other logo and icon removed. Built and applied the same day without touching installed files (`chat-page/branding.js`, `custom.css`, `blank.png`, copied in by `llm-start`). **Unfinished:** the owner still saw "Open WebUI" in several places, possibly the browser's saved copy; set aside by the owner. Next: the owner checks in a private window and names each place and its wording.
2. **M1 measurements**, listed below.

**Also open, not yet scheduled.**
- Long-document timings (section 8). The measurement a hardware decision depends on. First run done 2026-10-14 for Qwen3.6-35B-A3B: 109K tokens took 8.6 minutes before the first word, follow-ups about 2 s, peak memory 25GB (OVERVIEW.md section 8). Waiting on the owner: is that wait acceptable (Q4)? Recommended next: the same test with the FP16 oQ4 build, said to read prompts faster on M1 chips.
- Thinking: the main cause of slow replies. Limit it or make it a per-chat choice.
- Runaway replies: publishers' sampling values set per model 2026-10-14 (top-k 20 for both; presence penalty 1.5 for Qwen), which made one test question's runaway rarer but not gone (OVERVIEW.md section 9). The owner set aside the rest on 2026-10-14: a deliberate Stop test; trying oMLX's per-model thinking budget (best measured with the performance run); later, cancel or time limit in the gatekeeper.
- oMLX disk cache: done 2026-10-14. Examined (derived working state, no text); the owner chose a 50GB limit and a 7-day expiry run by `llm-stop` (OVERVIEW.md section 9).
- Warm-up request in `llm-start`: built 2026-10-14 (loads Open WebUI's default model before the address points back at the chat page). Confirmed at a real start the same day.
- Research R10 for saved conversations private from the admin, then the owner decides how strong that guarantee must be.
- `README.md`'s "Setup on a new machine" section is an untested sketch.

**Decisions not to re-open** unless something new is learned: the hidden prompt from Open WebUI's built-in tools stays as it is; the owner chats from the admin account; guests sign up and the owner approves; logins last 7 days; replies are capped at 20,000 tokens; uploads are on. The full list is in OVERVIEW.md section 6.

**Housekeeping that is the owner's to do.** Empty the Trash (it holds the first Open WebUI data folder, with a test chat and a copy of the oMLX key). Delete the saved test chats in the admin account. Delete the now-empty old folder `~/Documents/LLM Server`.

**Keeping the two files in step.** A change to what the owner wants (a requirement, feature, architecture choice or plan) goes in this file. Everything else goes in OVERVIEW.md: decisions, results and the as-built sections when the setup changes. High-level changes and decisions also get a short dated row in `LOGS.local.md`, which is not in git; routine operation and document edits do not.

## 0. How to use this document

Each statement falls into one of four confidence levels. Treat them differently.

| Label | Meaning | What to do |
| --- | --- | --- |
| **DECIDED** | The owner explicitly chose this. | Follow it. Do not re-litigate. Raise a conflict instead of silently deviating. |
| **DEFAULT** | A sensible starting choice not yet confirmed. | Use it, but say so when it matters and accept changes. |
| **ESTIMATE** | A number or claim from general knowledge, not measured on this machine. | Never present as fact. Replace with measurements from the test plan (section 8). |
| **UNVERIFIED** | A tool capability or model detail that may be wrong or outdated. | Check current documentation or run a test before building on it. |

Model names, sizes, tool features and speeds change quickly. Search current docs before relying on them. What has already been looked up or measured is in OVERVIEW.md (tool notes, measurements, log).

## 1. Goal and priorities

**DECIDED.** A private, always available LLM server on a Mac Studio the owner already has. The owner and 1-3 friends or family use it through a web page. No data leaves the machine.

Priorities, in order:

1. Answer quality, including on hard tasks.
2. Handling very large inputs: hundreds of pages or whole codebases (100K+ tokens).
3. Snappy responses. Longer waits are acceptable on complex tasks.
4. Serving several people at once. A nicety; expected to be rare.

The expected workload is a mix of everyday chat and drafting, coding and agentic tasks, and long-document analysis.

**Note on priorities and model choice.** Quality is priority 1 and speed is priority 3, but the spec's everyday models are chosen for speed (about 3B active parameters). Whether a slower, denser model is worth it is a question for M1 (see section 5 and section 8).

## 2. Hard constraints

| Constraint | Status | Implication |
| --- | --- | --- |
| **Privacy**: fully local. No cloud APIs. No information sent to public or private companies. The owner accepts a third party in the network path (for example a Tailscale relay) only if that party can never see the content of requests or responses. **Refined 2026-10-09:** the owner is not concerned about third parties seeing connection metadata (who connects, when, from where), as long as they cannot see prompts or LLM responses. | DECIDED | Never propose hybrid or cloud fallback. Disable telemetry in any tool you add (UNVERIFIED how, per tool). Downloading model weights is fine; uploading prompts or documents anywhere is not. Reject any access method where a third party can read traffic, such as Cloudflare Tunnel. Because metadata is acceptable, there is no need for Headscale on privacy grounds (section 10). |
| **Users**: owner plus 1-3 friends or family, who only open a web page. | DECIDED | Keep guest UX trivial. Guests reach the server over a Tailscale private network, so each guest device needs the free Tailscale app installed and signed in once; after that the LLM is a normal web page. The owner accepted this trade-off. Devices that cannot install the app (for example a managed work or school computer) are not covered for now; see section 10. One reviewer reports the app does not connect on networks that block tailscale.com (UNVERIFIED). |
| **Availability** (revised 2026-10-09): the LLM is available throughout the day. The owner also uses the Mac for general tasks alongside it, and at times runs intensive work (for example machine learning training), during which the owner stops the LLM service manually. If the Mac shuts down, the LLM does not need to start by itself. **Overnight:** the owner has no preference; default is no sleep, revisit after M1. | DECIDED (overnight: no preference) | No system sleep while the LLM is meant to be available (the display may sleep). Start and stop the services manually; do not rely on auto-start at boot, and do not configure anything that restarts a service the owner stopped. Stopping must free the model's memory. Do not assume the LLM has exclusive use of the machine. |
| **Chat history**: none saved in the first iteration. | DECIDED | Do not add persistence. Private accounts and history may come later (section 10). |
| **Owner priority**: the owner has uninterrupted priority during resource-heavy work. | DECIDED | Guests must never evict the owner's loaded document. |
| **Budget**: start with the existing machine as a proof of concept. Upgrade near term only if the benefit is clear. A machine change is expected long term. | DECIDED | Do not recommend purchases without measurements showing the bottleneck. |
| **Modularity**: the owner considers it important that components can be swapped without rebuilding the rest of the system. | DECIDED | Favor designs where one component can be replaced with minimal changes to the others. Weigh swappability when choosing between tools. The owner also expects to swap and test different models (2026-10-09), so never hard-code a model name or path. |

## 3. Hardware

Apple Mac Studio, M1 Max, 10-core CPU, 24-core GPU, 16-core Neural Engine, 64GB unified memory, 1TB SSD.

- **Memory bandwidth** is about 400 GB/s (ESTIMATE from Apple's published figure for this chip). It sets generation speed.
- **GPU memory**: macOS lets the GPU use roughly 45-48GB by default (ESTIMATE). It can be raised, for example `sudo sysctl iogpu.wired_limit_mb=57344` for about 56GB, leaving about 8GB for macOS. UNVERIFIED whether the setting persists across reboots; check, and if it does not, apply it at boot.
- **Strength**: fast generation on ~30B MoE models (ESTIMATE 30-60 tokens/sec), low power for a server that is always available.
- **Weakness**: prompt processing (prefill) is compute-bound and slow on this chip. Measured 2026-10-14 with Qwen3.6-35B-A3B: a 109K-token first prompt took 8.6 minutes (single reading). Concurrent users share the same bandwidth and slow each other down.
- **Upgrade logic**: if the long-document wait is the problem, the upgrade case is prefill compute, not memory capacity. An M2 Ultra is roughly 2-3x faster at prefill (ESTIMATE), and newer M5-generation chips more. Decide from measurements.
- **Cheaper levers to try before buying hardware** (none cost money): cache reuse or slot save/restore so the slow first prompt happens once per document; 8-bit KV cache quantization; a lighter-attention model; chunked retrieval instead of one giant context; raising the GPU memory limit.
- **Software upgrade path after the MVP** is milestones M2-M6 (section 7). Hardware upgrade is a separate, measurement-driven decision.

## 4. Architecture

```
Friends/family (browser)     Owner (browser)
          \                     /
           v                   v
   Tailscale private network (only invited or shared devices connect)
          |chat                     |status
 ---------v-------------------------v------------ Mac Studio M1 Max (awake while available)
 |  Open WebUI                 Status page [custom]                    |
 |  (no saved history)         (queue position, messaging, memory view)|
 |        |                      ^ queue,users        ^ memory stats   |
 |        v                      |                   |                |
 |  Gatekeeper proxy [custom] --------------------> Model server      |
 |  (queue, owner-priority, user count)              (oMLX, llama.cpp |
 |                                                    or mlx_lm.server;|
 |                                                    one model +     |
 |                                                    its KV cache)   |
 |                                                        |loads on swap
 |                                                        v           |
 |                                                   Model files (SSD)|
 ----------------------------------------------------------------------
```

Every chat request passes through the gatekeeper before it reaches the model server. That is what makes queueing and owner priority possible. Do not let Open WebUI talk to the model server directly.

**M0 note:** for the first baseline there is no gatekeeper yet (it arrives in M2), so Open WebUI talks to the model server directly for now. Keep the model server on localhost only so the access layer can change later without touching it.

| Component | Choice | Status |
| --- | --- | --- |
| Model server | oMLX for now. llama.cpp `llama-server` and `mlx_lm.server` are comparison candidates; all three are OpenAI-compatible, so the rest of the system can swap between them. | DEFAULT. Chosen after M1 testing (section 8). |
| Front end | Open WebUI. | DEFAULT. May be replaced if the saved-conversation requirement (F9) needs a front end that stores or encrypts chats per user. |
| Gatekeeper | A proxy between the front end and the model server (LiteLLM or a small custom proxy): per-user usage logging first (F12), then one request at a time, queue, user count, owner priority. It should also be able to cancel or time-limit a request itself. It cannot own the "offline" page, which sits in front of the chat page (section 10). | First slice built 2026-10-12: the usage relay (M2a) is in the path and records usage. Queue, owner priority and cancelling are still to come. |
| Status page | A small custom page, or elements inside the chat interface, for queue position, user count, owner-priority banner, messaging and the memory view. | Planned (M3, M4). Where it lives depends on research R2. |
| Network / access | Tailscale private network with the Tailscale app on each device. Nothing public, no router ports opened. Guests get access by device sharing (each guest uses their own Tailscale account and sees only the Mac). Funnel and a VPS relay are deferred. | DECIDED. |
| Guest-reachable surface | Only the front end is reachable by guests. The model server listens on this Mac only. Do not depend on Tailscale-specific features such as identity headers, so a later switch of access method stays cheap. | DEFAULT. |
| Model swapping | One model loaded at a time, swapped on demand through the queue. | DEFAULT. Two resident models to be considered after M1. |
| Availability | System sleep disabled while the LLM is meant to be available. Services are started and stopped by hand, never start by themselves, and are never restarted after the owner stops them. Stopping must free the model's memory. | DECIDED. |

Ports and paths (DECIDED 2026-10-09, owner approved): oMLX on port $OMLX_PORT, this Mac only, models in `~/models`; Open WebUI on port $WEBUI_PORT; configs and logs in `~/Documents/Code/llm-server`. Nothing runs as a launch service; the start and stop commands are used instead.

The as-built components, versions, addresses, files and settings are in OVERVIEW.md (sections 2, 3 and 10). What was learned about each tool is in OVERVIEW.md section 11.

## 5. Models and memory budget

Sizes are ESTIMATES for 4-bit unless stated. Names below were verified to exist on 2026-10-09 (R7, partly done); sizes and speeds are still unmeasured here.

| Role | Candidate | Approx. size | Notes |
| --- | --- | --- | --- |
| Everyday (baseline for M0) | Qwen3.6-35B-A3B, 4-bit MLX | ~18-24GB depending on build | 35B total, 3B active, hybrid attention with 262K native context, Apache 2.0, released about April 2026 **(checked)**. Owner indicated this as the intended model on 2026-10-09; the specific MLX build is not yet chosen (see below). |
| Everyday (light) | gpt-oss-20b | ~12GB | Very fast; friendliest to concurrent users. Released Aug 2025, so older. |
| Quality (coding, agents) | Laguna XS 2.1 (33B MoE, 3B active), Q8 | ~33GB | Exists **(checked)**: Poolside's coding-agent model, 256K context, successor to Laguna XS.2. Coding-focused, so it may not be the best general-quality model. |
| Quality (stretch) | Qwen3-Next-80B-A3B, 4-bit | ~45GB | Created Sept 2025. Listings disagree on whether it is still offered. Probably superseded by the Qwen3.6 generation. Low priority. |
| Quality contender to test in M1 | Qwen3.8-27B (dense), 4-bit MLX | ~15GB (ESTIMATE) | Released Aug 14, 2026, Apache 2.0 **(checked)**. Vendor-reported scores beat Qwen3.6-27B by about 5.7 points on average across four shared benchmarks (coding and agentic gains of roughly 6-8 points, GPQA only about 1.4). No direct benchmark against Qwen3.6-35B-A3B found. Dense means all parameters are read per token, so expect slower generation and slower prefill than the 35B-A3B (see below). |

**Not suitable for this machine:** Qwen3.8-Flash-Next (about 180B parameters stored, 6B active, Q4 about 82GB, needs about 96GB of memory; Alibaba-only benchmarks, labeled experimental) **(checked)**.

How model formats work, which builds exist and how to download them is in OVERVIEW.md section 11.

### Quality versus speed (to settle in M1)

A dense 27B model reads all 27B parameters per token; the A3B model reads about 3B. oMLX's own release notes list Qwen3.6-27B at about 35 tokens/sec versus about 90 for Qwen3.6-35B-A3B on an M3 Ultra, on a development build. The M1 Max has about half the memory bandwidth of an M3 Ultra, so expect lower numbers on both. ESTIMATE only. Prefill, the long-document wait, scales with compute per token and should be slower still for the dense model (ESTIMATE). Test the 35B-A3B against the 27B on real documents and real hard questions before choosing.

### Swapping versus two resident models

**DEFAULT:** start with one model loaded at a time on a single port, swapping on demand. Loading a 20-45GB model should take tens of seconds (ESTIMATE).

Two resident models need a raised GPU limit of about 56GB. Pairings (ESTIMATES): 20GB + 33GB leaves almost nothing for a 100K-token cache; 12GB + 33GB leaves about 10GB; a 4-bit quality model (~18GB) + 20GB leaves about 18GB at some quality cost. Test after measuring real swap times.

Swapping discards the loaded in-memory KV cache. A guest's model request could therefore destroy the owner's processed document. Model swaps must go through the queue and be blocked during owner-priority mode.

### Long documents and the KV cache

- **KV cache** is the stored intermediate work a model builds while reading a prompt, so it need not redo it for each new word. It makes follow-up questions fast and takes memory. **LRU (least recently used)** is the rule of dropping whatever was used longest ago when space runs out; it does not know the owner's document is more important than a guest's chat, which is why the gatekeeper and owner-priority mode exist.
- A KV cache belongs to one specific model. When a model is unloaded or swapped, its in-memory cache goes with it. A cache saved to disk survives, but only helps once the **same** model is loaded again and the same prefix is requested. oMLX's disk cache is designed to survive restarts and model switches (UNVERIFIED in detail; test it in M1).
- The first prompt processes the whole document and is slow. Follow-ups reuse the cached prefix, so they cost roughly a short prompt plus a small slowdown from longer context.
- KV cache size depends on architecture (rough figures for 100K tokens at 16-bit, UNVERIFIED): dense 32B-class ~25GB; ~30B MoE with standard attention ~10GB; linear or hybrid attention (Qwen3-Next style) a few GB. 8-bit KV quantization roughly halves these at some quality cost. Qwen3.6-35B-A3B uses hybrid attention, which should help (UNVERIFIED).
- The cache is lost when another request evicts it, when the model is swapped or unloaded (unless saved to disk), when the start of the conversation changes (system prompt, injected memory or retrieval), on idle timeouts, or under memory pressure.
- Quality can degrade at very long context even when it fits. Test retrieval accuracy on real documents. Chunked retrieval may beat one giant context for some questions.

## 6. Features

Each feature lists what to build and how to know it works. Status in brackets.

### F1. Active user count [DECIDED]
Show how many people are using the service on the status page.
- "Active" means a user with an in-flight or queued request, or seen within N minutes. N is 5 minutes (DEFAULT, 2026-10-09; the owner did not object).
- Acceptance: the count updates live and never includes the same session twice.

### F2. Queue with position [DECIDED]
One heavy request at a time; others wait in line and see their position.
- FIFO, except owner-priority (F4).
- Position updates live on the status page and in chat.
- Decided 2026-10-09: one request at a time overall.
- Acceptance: a second user sending a prompt during a long job sees "you're Nth in line", and is served in order when the job ends.

### F3. User-to-user messaging [DECIDED]
A waiting user can message the user currently holding the server, for example to ask how long they plan to use it.
- Needs a nickname or name per session even with no saved chat history. Users are identified by a lightweight login (DECIDED 2026-10-09); Open WebUI accounts may already provide it (UNVERIFIED how the identity reaches the gatekeeper).
- Messages are ephemeral, consistent with the no-history decision.

### F4. Owner-priority mode [DECIDED]
A flag the owner flips for heavy work.
- While on: new guest requests are queued (or held), and model swaps are blocked. First version (owner request 2026-10-12): new guest requests are refused with a clear message in their chat, for example "The owner is using the server right now. Please try again later."; holding them in a queue comes with the queue (M2b).
- The owner turns it on and off from the chat interface (a switch visible only to the admin), and all users can see that the server is occupied or reserved (F10).
- Guests see a clear banner that an owner session is active.
- Decided 2026-10-09: an in-flight guest request finishes; new guest requests are held.
- Acceptance: with the flag on, no guest request reaches the model server and the owner's cached document is never evicted.

### F5. Model selection with swap-time estimate [DECIDED]
Users pick a model and see an estimated swap time before confirming.
- A swap is a queued request, never allowed during owner-priority mode.
- The estimate should come from measured swap times (section 8), not guesses. Decided 2026-10-09: show a range based on measured swap history.

### F6. Live memory view [DECIDED]
A UI showing memory pressure in real time, so users can see when they will begin to run into issues and why.
- Break down: model weights, each active context's KV cache, and headroom.
- Soft warnings only. **No hard block** for now (a hard block is a bookmarked idea).
- UNVERIFIED how precisely per-process GPU memory can be read on macOS. The view may need to be approximate; say so in the UI if it is.
- oMLX's admin dashboard and its memory-guard feature may supply part of this (UNVERIFIED); check before building from scratch.

### F7. Document slot save/restore [BOOKMARKED, wanted]
Save a processed document's state to disk and restore it in seconds after eviction, so a multi-minute prefill is not repeated. Also allows keeping several processed documents for later.
- **oMLX** persists KV cache blocks to SSD and restores matching prefixes after requests and restarts **(checked, project's own description)**. This may satisfy F7 without custom work. UNVERIFIED at 100K+ tokens on this hardware.
- **llama.cpp** has a slot save/restore API (needs `--slot-save-path`); a client or proxy must call it. UNVERIFIED at 100K+ tokens on this hardware.
- **`mlx_lm.server`**: no disk persistence found in the mainline; a proposal was closed. UNVERIFIED whether any equivalent exists elsewhere.
- This may decide the model server choice.

### F8. No saved history [DECIDED]
Nothing is stored in the first iteration. Verify the mechanism in Open WebUI.

### F9. User-controlled, transparent and private conversations [DECIDED as a requirement 2026-10-10; design and milestone open]
Stated by the owner on 2026-10-10:
- **Transparent.** Each user can see what conversation data of theirs is saved, and when it is destroyed.
- **User control, explicit.** Each user has full control over their own conversations, with a visible indicator of whether they are in saved or unsaved mode.
- **Private from everyone, including the admin.** No user can see another user's conversations, and neither can the admin.
- **Preferred mechanism:** per-user encryption. The owner is open to other options.

Design notes (reasoning, 2026-10-10; UNVERIFIED until researched as R10):
- Open WebUI stores chats unencrypted in its SQLite database (its docs say SQLCipher is unsupported since v0.9.0). `ENABLE_ADMIN_CHAT_ACCESS=false` and `ENABLE_ADMIN_EXPORT=false` remove the admin screens, but whoever controls the Mac can still open the database file. So stock Open WebUI with saved chats meets "admin cannot see" by configuration and trust only, not technically.
- Ways to make saved chats technically unreadable to the admin: (a) save nothing on the server (enforced temporary chat); (b) keep saved chats in each user's own browser instead of on the server (a different front end, or a mode of one; loses sync between a user's devices); (c) encrypt saved chats in the browser with a key derived from the user's password, so the server holds only ciphertext (custom work or a front end that supports it; a forgotten password loses the chats).
- **Limit that no storage design removes:** to generate an answer, the Mac must see the prompt and the answer unencrypted while the request runs. The machine's operator could log that if they chose to. "Admin cannot see" can be made technically true for stored conversations, and is a matter of configuration and conduct for live requests (no content logging; verify oMLX and Open WebUI logs).
- Server-side leftovers also count toward transparency: oMLX's SSD cache (`~/.omlx/cache`), uploaded files, logs. Each needs a stated lifetime or must be off.

### F10. Indicators in the chat interface [WANTED 2026-10-10; design open]
The owner wants these visible to users, ideally inside the chat interface itself:
- **Privacy:** whether the current chat is saved (F9).
- **Memory pressure:** the machine's memory state, including context window size (F6).
- **In use:** whether another person is currently using the model (F1, F2).
- **Swap time:** how long a model swap will take (F5).

Whether Open WebUI's custom stylesheet and script, its plugins, or a separate status page carries them is research task R2. Deferred until after the system is running and measured.

### F11. Friendly "offline" page [BUILT 2026-10-12]
**Built:** while the LLM is stopped, the Tailscale address shows a styled page with the owner's wording, "Server not running. sorry :/", which turns into the chat by itself once the server is back. Still wanted from the original idea below: a distinct message when the owner has reserved the machine.

When the LLM is stopped, guests should see a clear page saying the server is offline, and ideally when it is expected back, instead of a bare error. Consider a distinct message for "the owner is using the machine for heavy work". Must not restart anything the owner stopped. Options are in section 10.

### F12. Usage logging per user [DECIDED 2026-10-12]
The owner wants to know which models each user uses, how many tokens they consume, and how long they occupy the server.
- **Record per request:** time, user, model, prompt tokens, reply tokens, seconds occupied, and how the reply ended (finished, stopped, or hit the length cap).
- **Never record** prompt or reply text.
- **Summaries on demand:** per user per day, per model, longest requests.
- **Transparency (F9):** guests are told that usage (who, when, how much) is recorded, in the same notice that tells them chats are not saved.
- **How (DECIDED): a relay** between the front end and the model server. Each request passes through it; it records the fields above and forwards the request unchanged. The front end attaches the user's name and account id to each request it forwards (Open WebUI has a setting for this), and the relay reads them. This relay is the first slice of the M2 gatekeeper and sits in the same place, so the queue, owner priority and request cancelling are built onto it later.
- **Options considered and not chosen:** (a) an Open WebUI plugin that records the same fields: nothing new to run, but tied to Open WebUI and unverified for temporary chats; (b) matching up the existing oMLX and Open WebUI logs by time: no changes, but it identifies devices rather than accounts and fails when requests overlap. Option (b) remains available for a rough look at past days.
- **Requirements on the relay:** independent of the front end (works if Open WebUI is replaced); model-agnostic (no model names in code); listens on this Mac only; started and stopped by the same start and stop commands; if the relay is down the chat page shows a clear error rather than silently bypassing it; streaming replies must pass through without added delay.
- **Acceptance:** after a guest and the owner each send messages, the log shows one row per request with the right user, model, token counts and duration, and contains no message text.

## 7. Build order and plans

- [x] **Stage 0 Interview.** Done 2026-10-09 and 2026-10-10. The owner's answers are in OVERVIEW.md section 6.
- [x] **M0 Baseline.** Done 2026-10-12. oMLX, Open WebUI and Tailscale installed; one everyday model; admin account first; guests chatted from their own devices. The step-by-step record is in OVERVIEW.md section 7.
- [ ] **M1 Measure.** Time long-document prompts, generation speed, memory use, model swaps and cache behavior (section 8). Use the results to choose the model server and to decide whether an upgrade is needed. Decide whether two resident models are viable.
- [ ] **M2 Gatekeeper.** Proxy in front of the model server, built in slices:
  - [x] **M2a Relay, usage records (F12).** Built 2026-10-12 as a custom relay writing `usage.csv`; `llm-usage` summaries added and the relay closed as done 2026-10-14. Guest notice skipped; a test with a guest's chat not done.
  - [x] **M2b Reserve and status (owner priority 2026-10-12).** Part done 2026-10-12: reserving from the Mac (`llm-reserve`), refusal message, and the relay reporting free, in use or reserved. The badge in the chat page is also done. The owner's switch on the badge is done too. In full: The owner can block other users from the model; an in-flight guest reply finishes; the relay reports free, in use or reserved; a badge in the chat page shows it to everyone, with the owner's switch on it.
  - [ ] **M2c** Single-request limit and queue, user count.
  - [ ] **M2d** Request cancel or time limit.
- [ ] **M3 Status page.** Queue position, user count, owner-priority banner, messaging.
- [ ] **M4 Memory view.** Live breakdown with soft warnings.
- [ ] **M5 Model selection.** Swap requests through the queue, with measured swap-time estimates.
- [ ] **M6 Slot save/restore.** If the chosen server supports it (oMLX may already provide it).
- [ ] **Saved conversations (F9).** After the MVP. Research R10 first, then the owner chooses how strong the "admin cannot read" guarantee must be.

### Smaller planned items

- [x] Friendly "offline" page (F11), styled, 2026-10-12.
- [ ] ~~A permanent "nothing is saved" notice for guests~~ Skipped by the owner 2026-10-14.
- [ ] Thinking: limit it or make it a per-chat choice (section 8).
- [x] Warm-up request in the start command so the first person does not wait for the model to load. Built 2026-10-14.
- [ ] Runaway replies: ~~set top-k to the model's recommended value~~ (done 2026-10-14, per model); deliberate Stop test; thinking budget; cancel or time limit in the gatekeeper.
- [x] Decide a size cap or expiry for the oMLX disk cache. 50GB and 7 days, 2026-10-14 (DECIDED).

### Research tasks

Findings so far are in OVERVIEW.md (section 11). Run each when the step that needs it arrives.

| # | Task | Needed for | Status |
| --- | --- | --- | --- |
| R1 | Can Open WebUI disable saved chat history for everyone? Does it phone home, and how is that switched off? | M0 | Done. |
| R2 | Can Open WebUI's plugins, custom stylesheet or custom script host the queue, messaging, memory view and the F10 indicators, or is a separate status page needed? Can oMLX's admin dashboard supply any of it? | M3 design | Open. |
| R3 | What queue, parallel-limit and per-user features does LiteLLM provide, versus a small custom proxy? How does the gatekeeper learn which Open WebUI user sent a request? | M2 | Open. |
| R4 | Slot save/restore: llama.cpp's API and its limits at 100K+ tokens, and the equivalents in oMLX and `mlx_lm.server`. | M1 server choice | Partly done; limits at 100K+ tokens on this hardware untested. |
| R5 | llama-swap: can it keep several models resident, and does it expose swap events and timings? | M5 | Open. |
| R6 | macOS specifics: how to read per-process GPU and unified memory, and whether `iogpu.wired_limit_mb` persists across reboots. | Any GPU-limit change; M4 | Open. |
| R7 | Verify candidate models exist, with sizes and quantizations. | Each new model | Done for the M0 model; repeat for each contender. |
| R8 | Tailscale: sharing on the free plan, the user limit, direct versus relayed connections. | M0 | Done, except relayed-connection speed for guests away from home, not yet measured under load. |
| R9 | Telemetry, update checks or phone-home behavior in oMLX (and any component added), and how to disable them. | Privacy | Done for oMLX 2026-10-14: nothing goes out on its own. Its admin dashboard checks GitHub for updates when opened, and uploads benchmark results to omlx.ai when a benchmark is run there, so do not benchmark from the dashboard. Menu-bar app not installed, not checked. |
| R10 | For F9: what Open WebUI's temporary chat stores and shows; front ends that keep chats in the browser or encrypt them per user while working with an OpenAI-compatible server; what oMLX's disk cache holds and how to cap, expire or disable it; what each component logs. | Saved conversations (F9) | Open. |

## 8. Proof-of-concept test plan

Goal: answer one question before any upgrade. Is the long-document wait on the M1 Max acceptable? All speed figures in this document are ESTIMATES until these tests are run.

- [ ] Time to first token on 10K, 50K and 100K-token prompts, for each candidate model. Partly done 2026-10-14 for Qwen3.6-35B-A3B (11K: 20 s, 87.5K: 6 min, 109K: 8.6 min; follow-ups 0.5 to 2.1 s); results in OVERVIEW.md section 8. Still to do: about 50K, and the other models.
- [ ] Generation speed in tokens per second for the everyday and quality models, at short and long context.
- [ ] Follow-up test: load a large document, ask a question, then two follow-ups; compare time to first token each time.
- [ ] KV cache memory at 100K tokens for each model, at 16-bit and 8-bit, and whether the machine starts swapping.
- [ ] Retrieval accuracy at long context: ask about facts known to be on specific pages of a real document.
- [ ] Model swap time for each model pair, and whether the cache is lost on swap. On oMLX, also test whether the disk cache makes the next question fast after swapping away and back.
- [ ] Slot save/restore: save a processed 100K-token document, restore it, time both steps (llama.cpp first; compare oMLX's SSD cache).
- [ ] Cache reuse in oMLX, `mlx_lm.server` and llama.cpp's `llama-server`, to choose the server.
- [ ] Quantization comparison for Qwen3.6-35B-A3B: plain MLX 4-bit versus the oQ4 FP16 variant, for prompt-processing speed and answer quality.
- [ ] Quality versus speed: Qwen3.6-35B-A3B versus Qwen3.8-27B (dense) on real documents and real hard questions, measuring first-prompt wait, generation speed and answer quality.
- [ ] Open WebUI prompt construction: does it change the start of the conversation and break the cache?
- [ ] **Speed reminders from the 2026-10-11 iPhone test (owner asked to come back to these):**
  - [ ] Thinking: measure reply time and answer quality with thinking on, limited and off; find how to switch it per chat (Open WebUI model parameters or an oMLX per-model setting) and choose the default.
  - [x] Hidden prompt: identified as Open WebUI's built-in tools (2026-10-12). Owner decided not to remove them. Follow-ups in the same chat already reuse the cache.
  - [x] First-use load: warm-up added to `llm-start` 2026-10-14; at a real start it loaded Qwen in about 5 s before the chat page was reachable.
- [ ] Concurrent requests from two users, and what the queue does to the owner's cached document.
- [ ] Staying available: sleep stays disabled while the LLM is meant to be up; nothing starts by itself after a reboot or power loss (the owner runs `llm-start`); whether a raised GPU memory limit persists across reboots.

**Decision rule:** if the first-prompt wait on real documents is tolerable and follow-ups are fast, stay on the M1 Max. If the wait or the memory pressure is the problem, the upgrade case is prefill compute.

Record results in OVERVIEW.md (measurements and log) so later work uses measured numbers.

## 9. Open questions

- Which model server wins after testing: oMLX or llama.cpp (`mlx_lm.server` as a baseline)?
- Is a dense model (Qwen3.8-27B) worth its speed cost against Qwen3.6-35B-A3B? Is the oQ4 FP16 build faster at reading prompts on this chip?
- What first-prompt wait on a 100K-token document is acceptable? (Owner: not sure; decide after seeing real times.)
- Should thinking be on by default, limited, or a per-chat choice?
- How strong must the guarantee be that the admin cannot read saved chats: technically impossible, or switched off on trust? (Owner: decide after research R10.)
- Does the oMLX disk cache count as "saved data" for the transparency requirement, and what lifetime should it have? (Lifetime answered 2026-10-14: at most 7 days, 50GB. It is treated as derived saved data, listed in OVERVIEW.md section 5.)
- Where do the F10 indicators live: inside Open WebUI or on a separate status page?
- How does the gatekeeper identify the user behind each request? (Answered 2026-10-12: Open WebUI's user-info headers, tested and switched on. Still open: whether to use the signed form.)
- Custom relay or LiteLLM? Answered 2026-10-12: custom (`relay.py`).
- Should the machine stay available overnight? (Owner: no preference; revisit after M1.)
- Is a hardware upgrade justified? (Only from M1 measurements.)

## 10. Bookmarked and deferred ideas

Each has a trigger for revisiting. Research notes behind these (Funnel, VPS relay, Headscale, SSD-streaming engines) are in OVERVIEW.md section 11.

| Idea | Status | Revisit when |
| --- | --- | --- |
| "Reserved" message on the offline page (F11) | Styled offline page built 2026-10-12 | With reserve and status (M2b): a distinct message when the owner has reserved the machine. Note: the offline page sits in front of the chat page, so the gatekeeper, which sits behind it, cannot own it. |
| Remove "Open WebUI" branding | Applied 2026-10-14, not yet confirmed in a browser; set aside by the owner | Done through the page-extras folder instead of patching installed files, so upgrades cannot break it. Allowed by its license at 50 users or fewer. Revisit when the owner reports where the name still shows. Not covered: the name a phone uses for a home-screen shortcut (served by Open WebUI itself). |
| Private accounts and chat history (F9) | Moved up: wanted next after the MVP | After M1. Needs a storage decision, including whether the owner as admin can read guests' chats. |
| Two resident models | Open | After swap times are measured. Needs a raised GPU limit and a pair that leaves room for a 100K-token cache. |
| Guest lane on a second port | Deferred | Traffic grows, or guests keep evicting the owner's cache. A small model with capped context, so guests never evict the owner's document. |
| Hard memory block | Deferred | Soft warnings prove insufficient. |
| Quick offline and relaunch | Built in basic form (start and stop commands) | Still wanted: graceful shutdown that tells queued users, and the friendly offline page. |
| Shared machine (partitioning) | Direction chosen: the LLM runs in the background alongside the owner's general use | Decide the memory reservation from M1 measurements (owner needs roughly 8-12GB for light use). |
| Scheduled availability | Open | Run the server on a schedule to reduce exposure and save energy. Needs a schedule, a clear message for guests when it is off, and a rethink of the "sleep disabled" default. |
| Tailscale Funnel | Deferred (the owner may revisit) | A device that cannot install the Tailscale app, or a guest unwilling to install it. Needs an access gate in front of the chat page first. |
| VPS relay with TLS passthrough | Deferred (the owner may revisit) | Only if Funnel's limits break the use case. |
| Headscale | Dropped | Only if the owner's stance on connection metadata changes. |
| Dense Qwen3.8-27B as a quality contender | Open | M1 quality-versus-speed measurements. |
| Uncensored model variant | Deferred: not required | The owner asks to test one. |
| SSD-streaming engines (Flash-MoE, Colibri) | Open | The owner wants a slow path for very hard problems. |
| Slot save/restore in `mlx_lm.server` | Not available in the mainline | Resolved by the M1 server choice. |
| Hardware upgrade or replacement | Open | After M1 measurements. |

## 11. Notes for the implementing agent

- **Working style.** The owner likes to be interviewed about goals before solutions and prefers concise answers. Offer choices with tradeoffs, and say which you recommend and why. **For implementation steps (added 2026-10-09):** go one step at a time, be explicit about what to run and what to send back, and do not move on until the owner confirms. If outputs from a step are missing, say so before continuing.
- **Do not invent numbers.** Label estimates, and prefer measuring. Never present speed, memory or swap-time figures as facts until tested. Benchmarks found online are mostly vendor-reported or from aggregators that disagree with each other; treat them as leads.
- **Verify tools before building on them.** Model and tool ecosystems change quickly. Search current documentation for oMLX, LiteLLM, Open WebUI, llama.cpp, `mlx_lm`, llama-swap and Tailscale rather than relying on memory.
- **Check model format before download.** The model must be in the format the chosen server reads (MLX for oMLX and `mlx_lm.server`, GGUF for llama.cpp) and small enough to fit with its KV cache. Open the repository's file list first. Download only conversions of the exact base model.
- **Privacy first.** If a design choice would send prompts, documents or usage data outside the machine, it is out of scope. Connection metadata may be seen by third parties; content may not. Ask the owner before adding any dependency that phones home, and check oMLX's auto-update and telemetry (R9).
- **Interview before building.** Stage 0 is done, but the habit stands: when a new milestone raises questions that are the owner's to decide, ask them in small batches before building, and say which milestone each unresolved item blocks.
- **Do not assume exclusive use of the machine.** The owner may also use it for day-to-day tasks, and may want to take the LLM offline quickly or run it on a schedule. The details are undecided (sections 9 and 10). Build services that stop and restart cleanly, and do not hard-code memory budgets that leave nothing for macOS.
- **Protect the owner's cache.** When in doubt, design so that guests cannot cause a loss of the owner's processed document.
- **Ask before spending money.** Hardware purchases need measured justification and the owner's confirmation.
- **Keep this file current.** When a question in section 9 is answered or a test in section 8 is run, update this spec if the plan or a requirement changed, and log it in OVERVIEW.md.
