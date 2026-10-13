# Private LLM Server: Overview

- **As of:** 2026-10-12
- **Status:** The first milestone (M0) is complete. The server runs on the Mac Studio, you and two guests have chatted with it from your own devices, and guests' conversations are not saved. The server is currently stopped; start it with `./llm-start` from the project folder. Next to build is the usage-logging relay. The project folder is a local git repository with no commits yet; a secret-blocking check runs before every commit (section 10).
- **Picking up in a new chat:** the handoff at the top of [SPEC.md](SPEC.md) says what to check first and what comes next. The last rows of the log in `LOGS.local.md` (not in git) say what happened most recently.
- **What this file is:** the record of what was actually done: decisions, what is installed and how it is set up, measurements, findings, and notes from each tool's documentation. The dated log is kept separately in `LOGS.local.md`.
- **Companion file:** [SPEC.md](SPEC.md) holds how you want the project built: goals, constraints, architecture, features and plans.
- **Placeholders:** this file never shows the real Tailscale address or port numbers. `$TAILSCALE_HOST`, `$OMLX_PORT`, `$WEBUI_PORT`, `$OFFLINE_PORT` and `$RELAY_PORT` stand for the values kept in `local.env`, which is not in git; `(tailnet name)`, `(machine name)` and `(Tailscale IP)` stand for the parts of the address. Earlier log rows were edited on 2026-10-12 to use them.
- **Section numbers:** in notes moved here from the spec, "section N" refers to SPEC.md unless it says otherwise.

## 1. What this is

A private AI chat service running on your Mac Studio (M1 Max, 64GB). You and a few friends or family open a web page and chat with a model that runs entirely on the Mac. No prompt or answer is sent to any company.

## 2. How it fits together

```
Your devices and guests' devices (browser)
        |
        |  Tailscale private network (encrypted end to end)
        v
https://$TAILSCALE_HOST        <- the address everyone uses
        |
        v
Open WebUI  (chat page, logins)        127.0.0.1:$WEBUI_PORT, this Mac only
        |
        v
Relay  (usage records, reserving)      127.0.0.1:$RELAY_PORT, this Mac only
        |
        v
oMLX  (runs the model)                 127.0.0.1:$OMLX_PORT, this Mac only
        |
        v
Model files in ~/models
```

| Part | What it does | Version |
| --- | --- | --- |
| oMLX | Runs the AI model and produces the answers | 0.7.0 |
| Open WebUI | The chat web page, accounts and logins | 0.11.4 (pinned) |
| Tailscale | Private network that lets approved devices reach the Mac | 1.104.1 |
| Model | Qwen3.6-35B-A3B, 4-bit MLX build from `mlx-community` | 20.4GB |
| Second model | Laguna XS 2.1 (coding), 6-bit MLX build from `mlx-community` | 25GB |

The two programs on the Mac listen only on the Mac itself. The only way in from another device is through Tailscale.

## 3. Using it day to day

| Task | How |
| --- | --- |
| Start | `~/Documents/Code/llm-server/llm-start` (starts oMLX, then Open WebUI; safe to run twice) |
| Stop and free the model's memory (about 20GB) | `~/Documents/Code/llm-server/llm-stop` |
| Chat from any of your Tailscale devices | `https://$TAILSCALE_HOST` |
| Chat at the Mac if Tailscale or the internet is down | `http://localhost:$WEBUI_PORT` |
| Turn the Tailscale address off / on | `tailscale serve --https=443 off` / `tailscale serve --bg $WEBUI_PORT` |
| Look at logs | `~/Documents/Code/llm-server/omlx.log`, `~/Documents/Code/llm-server/open-webui.log` |

- Nothing starts by itself at login or after a reboot, except the Tailscale app. After a reboot, run `llm-start`.
- Stopping and starting does not sign anyone out.
- The two addresses lead to the same page. Browsers remember sign-ins separately for each, and there is no redirect between them.
- While the server is stopped, the Tailscale address shows a styled page saying "Server not running. sorry :/". The page checks every 30 seconds and turns into the chat by itself once the server is back. To change it, edit `~/Documents/Code/llm-server/offline/index.html`; the change shows straight away.
- After a reboot the address shows a bare error, because nothing starts by itself. Run `llm-stop` to bring the offline page back, or `llm-start` to bring the chat back.

### Adding a guest

1. In Tailscale's admin console (`https://login.tailscale.com/admin/machines`), open the menu for the machine `(machine name)`, choose **Share**, and send the invite link.
2. The guest installs Tailscale, signs in with their own account, and accepts the link.
3. The guest opens `https://$TAILSCALE_HOST`, chooses **Sign up**, and creates an account. The email is only a login name and can be made up. The password needs 8+ characters with an uppercase letter, a lowercase letter, a digit and a symbol.
4. You approve them: **Admin Panel → Users**, change their role from **pending** to **user**.

To remove a guest, revoke the share in Tailscale and delete or deactivate the account in Admin Panel → Users. If a guest forgets their password, you reset it there too.

## 4. Who has access now

- **You:** the admin account, on the Mac Studio, an iPhone and a second Mac.
- **Guests:** two people, each on their own Tailscale account and device, plus one ordinary test account you created.
- Tailscale's free plan allows up to 6 users. A shared guest sees only this Mac, and the Mac cannot start connections to their devices.

## 5. Privacy: what is and is not saved

| Data | Saved? | Where | Notes |
| --- | --- | --- | --- |
| Guests' conversations | No | n/a | Verified after real use: 0 chats in the database for ordinary users |
| Your (admin) conversations | Yes, by default | Open WebUI's database, unencrypted | Admins are exempt from the "nothing saved" rule. You can switch a chat to temporary |
| Uploaded files | Yes, until deleted | `~/Documents/Code/llm-server/open-webui-data/uploads` | Uploads are on at your request |
| Processed prompts (cache) | Yes, in a derived form | `~/.omlx/cache` | Lets the model skip re-reading long documents. What exactly it holds is still to be examined |
| Prompt or answer text in logs | No | n/a | Checked several times; logs hold timings and token counts only |

- **Nothing leaves the Mac.** Open WebUI runs in offline mode with update checks, tracking and outside services switched off. Spot checks found no connections to anything outside the Mac. A sustained watch has not been done.
- **Admin viewing is switched off.** The admin screens for viewing and exporting other users' chats are disabled. This matters little today, since guests' chats are not stored at all.
- **A limit worth knowing:** to produce an answer, the Mac must see the prompt and the answer unencrypted while the request runs. Whoever operates the Mac could log that if they chose to. No storage design removes this.
- **Third parties:** Tailscale and your sign-in provider can see connection details (who connects and when), which you accepted. They cannot see prompts or answers.

## 6. Decisions

### Summary

| Topic | Decision |
| --- | --- |
| Priorities | Answer quality first, large inputs second, speed third, several users at once fourth |
| Privacy | Fully local. Connection details may be visible to third parties; content may not |
| Access | Tailscale private network; share the Mac with each guest |
| Availability | No system sleep; started and stopped by hand; no auto-start; you stop it for heavy work such as ML training |
| Model server | oMLX for now; llama.cpp to be compared in M1 |
| Model | Standard (not uncensored) Qwen3.6-35B-A3B 4-bit; you expect to swap and test others |
| Guests' conversations | Not saved in this first version |
| Saved conversations later | Wanted after the MVP: each user in explicit control, with a visible saved/unsaved indicator, and private from everyone including the admin. How strong the "admin cannot read" guarantee must be is to be decided after research |
| Your own account | You chat from the admin account, with extra permissions guests do not get |
| Uploads | On. An uploaded document's full text goes into the conversation |
| Accounts | Guests sign up themselves; you approve each one |
| Login length | 7 days |
| Reply length | Capped at 20,000 tokens, roughly 5 to 11 minutes at worst |
| Hidden prompt from Open WebUI's built-in tools | Leave as is; 5 to 6 seconds per conversation is acceptable |
| Usage logging | Record per request who, which model, how many tokens and how long, never the text; done by the relay between Open WebUI and oMLX, written to `usage.csv` |
| Reserving the server | The owner reserves it with `llm-reserve on`: a guest's reply in progress finishes, new guest requests are refused with a clear message, the owner's go through; it clears on restart |
| Budget | No hardware purchase without measurements that justify it |

### Interview answers in detail (Stage 0, 2026-09-30 to 2026-10-10)

Moved from the spec. Each row is a question put to you, why it mattered, and your answer.

| # | Question | Why it matters | Blocks | Recommendation (DEFAULT, confirm) |
| --- | --- | --- | --- | --- |
| Q1 | How should guests reach the server? **ANSWERED 2026-09-30, reconfirmed 2026-10-09: Tailscale app on each device (private network). Funnel and a VPS relay are deferred; the owner may revisit either later.** | Guests need only a browser after a one-time app install, and no third party may read the content. | None (answered) | Tailscale private network; see section 4. |
| Q2 | Tailscale or self-hosted Headscale? **ANSWERED 2026-09-30: Tailscale for the MVP. CLOSED 2026-10-09: Headscale is not needed, because the owner is not concerned about metadata.** | Headscale's main benefit was keeping connection metadata private. | None (closed) | Revisit only if the metadata stance changes. |
| Q3 | How will the machine be shared with your day-to-day use? Options raised so far: run in the background with reduced capability for you, quick offline and relaunch, or a schedule. **PARTLY ANSWERED 2026-10-09:** the LLM runs in the background while the owner uses the Mac normally, available throughout the day with no sleep; the owner stops it manually for intensive work such as ML training; no auto-start after shutdown is needed. **Overnight: the owner has no preference (2026-10-09), so sleep stays disabled and this is revisited after M1.** **Memory reservation answered 2026-10-09: the owner needs roughly 8-12GB for their own work while the LLM runs (light use); when a heavy task comes, the owner stops the LLM.** Treat that plus macOS itself as roughly 12-16GB (ESTIMATE), leaving about 48GB for model and cache, which is close to the default GPU limit, so no limit change is needed for M0. | Affects the sleep setting, how services are launched and the memory budget. | M0 (initial settings, now answered); memory reservation can wait for M1 | Manual start and stop, sleep disabled while available, default GPU limit for M0. Decide overnight availability and the memory reservation from M1 measurements. |
| Q4 | What first-prompt wait on a 100K-token document is acceptable: under 2 minutes, under 10 minutes, or no limit? **ANSWERED 2026-10-09: not sure yet; measure real times in M1 and decide then.** | Turns the section 8 decision rule into a number. | M1 evaluation | Get a rough figure now; refine after seeing real times. |
| Q5 | Confirm the model for the first baseline. **PARTLY ANSWERED 2026-10-09: owner indicated Qwen3.6-35B-A3B. Still open: which exact 4-bit MLX build, and whether an uncensored variant is a requirement.** | Needs to exist and fit before download. | M0 (Step 3) | Plain `mlx-community` 4-bit or the oQ4 build for the baseline; add the FP16 oQ4 variant and Qwen3.8-27B as M1 contenders. Open the exact repo's file list before download. |
| Q6 | Approve the proposed ports, install paths, service names and repository layout. **ANSWERED 2026-10-09: approved as proposed (oMLX port $OMLX_PORT, this Mac only, models in `~/models`; Open WebUI port $WEBUI_PORT; configs and logs in `~/Documents/Code/llm-server`).** | Not decided in this spec; the agent proposes them. | None (answered) | Agent proposes a short list; owner approves or edits. oMLX's default model folder is `~/.omlx/models`. |
| Q7 | How are users identified for the queue and messaging: nickname per session, or a lightweight login? Do you expect to add private accounts and history later? **ANSWERED 2026-10-09: lightweight login.** Open WebUI already requires approved accounts, so reuse them if the gatekeeper can read the user's identity (UNVERIFIED how; check at M2). Chat history stays off. | If accounts are coming, the gatekeeper's user identity should be designed for them now. | M2 | Nickname per session for now, with an identity field that can later map to accounts. |
| Q8 | What counts as a "heavy" request, and what counts as an "active" user? **ANSWERED 2026-10-09: one request at a time overall. Active = request in flight or queued, or seen in the last 5 minutes (the owner did not object to 5).** | Defines queue behavior and the user count. | M2 | Start with one request at a time overall. Active = request in flight or queued, or seen in the last N minutes; propose N. |
| Q9 | When owner-priority mode turns on, does an in-flight guest request finish? Are new guest requests held in the queue or rejected? **ANSWERED 2026-10-09: an in-flight guest request finishes; new guest requests are held, with a visible banner.** | Defines how much a guest can be interrupted. | M2 | Let the in-flight request finish and hold new ones with a visible banner. |
| Q10 | How accurate must the model-swap time estimate be, and should it learn from past swaps? **ANSWERED 2026-10-09: show a range based on measured swap history.** | Shapes the swap UI. | M5 | Show a range from measured history. |
| Q11 | Do any parked ideas need to move up? See table C. **ANSWERED 2026-10-09: private accounts and history moves up; all others stay parked.** | Last check before building. | None | Ask once at the end of the interview. |
| Q12 | Share the Mac with each guest's own Tailscale account, or invite guests into your Tailscale network? **ANSWERED 2026-10-09: share the Mac with each guest.** | Sharing limits a guest to this one machine. Inviting counts toward the free plan's user limit (3 per recent sources, 6 per the earlier spec; unresolved) and needs access rules to keep guests off your other devices. | M0 | Share the Mac with each guest. The 3-user finding makes inviting three guests plus the owner infeasible on the free plan. |
| Q13 | Is an uncensored model a requirement? (New 2026-10-09.) **ANSWERED 2026-10-09: not a requirement for now; use the standard models in this spec. The owner wants the freedom to swap in and test different models later.** | Decides whether to evaluate the AEON uncensored Qwen3.6-27B family; affects quality, speed and guest safety. | M1 | Not a requirement unless the owner says so; stay with the standard base model. |

### Parked ideas as confirmed with you (2026-10-09)

The current list of deferred ideas, with what would bring each one back, is in SPEC.md section 10. This is the record of what you said when asked.

| Idea | Current status | Trigger to bring forward |
| --- | --- | --- |
| Guest lane on a second port | Deferred | Traffic grows, or guests keep evicting the owner's cache |
| Hard memory block | Deferred | Soft warnings prove insufficient |
| Private accounts and chat history | **Moved up 2026-10-09:** the owner wants it next after the first iteration; scope and milestone not yet decided | After the MVP (M0-M1). The "no saved history" constraint still holds for the first iteration. Questions to settle then: where chats are stored, and whether the owner as admin can read guests' chats. |
| SSD-streaming engines (Flash-MoE, Colibri) | Open | The owner wants a slow path for very hard problems |
| Two resident models | Open | After swap times are measured (M1) |
| Hardware upgrade or replacement | Open | After M1 measurements |
| Quick offline and relaunch, scheduled availability, shared machine | Open | Covered by Q3 |
| Tailscale Funnel or a VPS relay for browser-only devices | Deferred; the owner may revisit either | A device that cannot install the Tailscale app, or a guest unwilling to install it |
| Headscale | Dropped (metadata not a concern) | Only if the owner's metadata stance changes |
| Dense Qwen3.8-27B as a quality contender | Open | M1 measurements of quality versus speed |
| Uncensored Qwen3.6-27B (AEON) variant | Deferred 2026-10-09: not required for now; the owner may test other models later | The owner asks to test it |

## 7. What was done

### Summary

| Step | What | When |
| --- | --- | --- |
| 1 | Checked macOS and set the Mac not to sleep | Oct 9 |
| 2 | Installed oMLX; removed a leftover service that auto-started it | Oct 9 |
| 3 | Installed the download tools, downloaded the model, verified its checksums, confirmed it loads and answers | Oct 9 |
| 4 | Set an API key on oMLX; installed and configured Open WebUI; created the admin account; wrote the start and stop commands | Oct 10 |
| 5 | Installed Tailscale on the Mac and your iPhone; turned on HTTPS; served the chat page at the Tailscale address; shared the Mac with two guests | Oct 11 |
| 6 | Guests signed up, were approved and chatted from their own devices | Oct 11 to 12 |
| After | Login length set to 7 days; guest sign-up with approval turned on; reply length capped at 20,000 tokens | Oct 11 to 12 |

### M0 steps in detail

Moved from the spec. The "What" column is the step as planned; the last column is what actually happened.

| Step | What | Status (2026-10-09) |
| --- | --- | --- |
| 1 | Keep the Mac awake (revised 2026-10-09): confirm macOS 15 or newer (`sw_vers`); in System Settings, Energy: prevent automatic sleeping when the display is off; verify with `pmset -g` (`sleep` 0). Wake for network access and start after power failure are optional, because the LLM does not need to auto-start. Auto-login and FileVault are no longer an issue. Consider that automatic macOS update restarts will take the LLM down until it is started again. | **Done 2026-10-09:** macOS 27.0.1 (meets the macOS 15 requirement); `pmset -g` shows `sleep 0`, `displaysleep 90`, `womp 1`, `autorestart 0`. |
| 2 | Install the model server: check Homebrew; `brew tap jundot/omlx https://github.com/jundot/omlx` then `brew install jundot/omlx/omlx`; `omlx --help` and `omlx serve --help`; start once in the foreground with `omlx serve --model-dir ~/models`; test with `curl http://localhost:$OMLX_PORT/v1/models`. No model yet. | **Done 2026-10-09.** Homebrew 7.0.7, oMLX 0.7.0, `brew analytics` disabled. A pre-existing Homebrew background service (`sh.brew.omlx`, RunAtLoad and KeepAlive true, plain `omlx serve`, running since Oct 1) held port $OMLX_PORT; stopped with `brew services stop omlx` (status none). Foreground start with `--model-dir ~/models` worked: listens on 127.0.0.1:$OMLX_PORT, 0 models, `/v1/models` returned an empty list, Ctrl+C shut down cleanly, port freed. Findings in section 11. |
| 3 | Choose and download one model. First do R7 properly: open the exact repo's file list, confirm it is an MLX conversion of the base model, and confirm size and format. Candidate: a 4-bit MLX build of Qwen3.6-35B-A3B (section 5). Test response. | **Done 2026-10-09.** `mlx-community/Qwen3.6-35B-A3B-4bit` in `~/models`, verified by checksum; loads in oMLX 0.7.0 and answers. Results in section 11. |
| 4 | Install Open WebUI without Docker (for example `uvx --python 3.11 open-webui@latest serve --port $WEBUI_PORT`), create the admin account first, close sign-ups, set new users to "pending", connect to the model server on localhost with its API key, wrap in a launchd service. | **Done 2026-10-10** (no launchd service; plain start and stop commands instead). Open WebUI 0.11.4, settings in `~/Documents/Code/llm-server/open-webui.env`, admin plus one ordinary test account, `~/Documents/Code/llm-server/llm-start` and `llm-stop`. Details in section 11. |
| 5 | Install Tailscale on the Mac and the owner's devices; use `tailscale serve` for HTTPS inside the tailnet; share the Mac with guests (Q12). Avoid Funnel for now. | **Mostly done 2026-10-11.** Tailscale 1.104.1 on the Mac (machine name `(machine name)`) and the owner's iPhone; HTTPS enabled; `tailscale serve --bg $WEBUI_PORT` serves `https://$TAILSCALE_HOST/` to the tailnet. The owner's iPhone test passed and the Mac is shared with two guests (2026-10-11). **Done.** |
| 6 | Guest test from a device that is not the owner's: open the Tailscale URL, log in as a guest, chat, confirm the guest cannot see admin settings or the owner's chats. | **Done 2026-10-11/12 as far as the Mac can show:** two guests on their own Tailscale accounts and devices reached the HTTPS address, signed up, were approved and chatted; their chats left nothing in the database. Still to hear from the owner: the guests' own impressions, and confirmation that a guest sees no admin settings. |

## 8. Measurements so far

Single readings from normal use, not a benchmark.

| Reading | Result |
| --- | --- |
| Generation speed, one request at a time | 60 to 70 tokens per second |
| Generation speed when requests overlap | 23 to 31 tokens per second |
| Model load, first request after starting | 6 to 8 seconds |
| Memory with the model loaded | About 20GB |
| Wait before the first word on each message through the chat page | 5 to 6.5 seconds |
| Typical reply through the chat page | 17 to 42 seconds, mostly thinking |
| Network delay, your iPhone at home | 5 milliseconds, direct connection |

### Two-model speed test (2026-10-12)

Measured straight at oMLX, not through the chat page or the relay. Short prompt (about 30 tokens), 300-token replies, nobody else using the server. Five rounds; each round switched to a model (one swap) and then ran it three more times. Averages, with lowest and highest.

| | Qwen3.6-35B-A3B 4-bit | Laguna XS 2.1 6-bit |
| --- | --- | --- |
| Tokens per second, model loaded (15 runs each) | 69.9 (69.7 to 70.0) | 52.1 (51.8 to 52.4) |
| Seconds to first token, model loaded (15 runs each) | 0.21 (0.20 to 0.21) | 0.25 (0.24 to 0.26) |
| Seconds to first token when the other model must be swapped out first (5 swaps each) | 12.9 (9.1 to 15.1) | 8.2 (8.1 to 8.3) |
| Memory once loaded (oMLX's log) | 19.3GB | 25.7GB |

- The two models do not stay in memory together: each switch unloads one (about 4 s, from oMLX's log) and loads the other.
- Swapping to Qwen took about 15 s three times and 9 to 10 s twice; the cause of the difference was not investigated.
- Not covered: long prompts, where time to first token is dominated by reading the prompt; the chat page, which adds its own hidden prompt of 3,300 to 4,500 tokens and so a few seconds to the first message of each chat; several people at once; and answer quality.
- Laguna's earlier single reading of about 39 tokens per second was a first run straight after loading; these figures replace it.

## 9. Known issues and findings

1. **Slow replies.** Three causes were found: the model thinks at length before answering (17 to 42 seconds), which is the main one; Open WebUI's hidden prompt costs 5 to 6.5 seconds on the first message of each chat, which you decided to leave as is (see below); and the first message after starting waits about 6 seconds for the model to load. Thinking and the first-use load are still to be looked at in M1.
2. **Runaway reply.** One reply ran for 17.7 minutes until it hit the length limit, slowing everyone. The cap is now 20,000 tokens. Investigated on 2026-10-12, see "The runaway reply" below.
3. **No queue yet.** Requests from several people run at once and slow each other down.
4. **Offline page.** Built 2026-10-12, first as plain text and then as a styled page handed out by a small program. After a reboot the address shows a bare error until you run `llm-start` or `llm-stop`. Not yet seen in a real browser: the look on a phone through Tailscale, and the automatic switch to the chat.
5. **"Nothing is saved" notice for guests.** The temporary-chat label disappears after the first message. A permanent banner is the planned fix.
6. **The oMLX cache.** It grows with use and its automatic limit is about 220GB. What it holds and how to cap or expire it is still to be examined.
7. **Housekeeping for you.** Empty the Trash, which holds the first Open WebUI data folder with a test chat and a copy of the oMLX key. Two saved test chats remain in your admin account.
8. **API key in two places.** Open WebUI keeps a plain-text copy of the oMLX key in its database. Changing the key means updating both.

### The runaway reply: what the logs show (2026-10-12)

- **What happened.** A guest on a phone had a normal three-message chat, left the phone idle for six minutes, then came back and sent a message. That reply never finished: it ran for 17.7 minutes to the length limit. The guest pressed Stop twice and it did not work, then re-sent the question, which was answered normally in about a minute while the first reply was still running in the background.
- **Why Stop did not work (confirmed in Open WebUI's code).** A temporary chat is tied to the browser's live connection to the server. When a phone sleeps or the browser goes to the background, that connection drops. The page still shows the old chat, but the server no longer recognizes it, so Stop is rejected and the reply keeps generating. Every guest uses temporary chats, so any guest can run into this. It has not been reproduced on purpose yet.
- **Why the reply never ended (not known).** Reply text is not logged, so the content cannot be examined. Two suspects: the model got stuck in its thinking; or a sampling setting, where oMLX leaves "top-k" switched off while the model's own configuration file specifies 20, which makes endless text more likely.
- **Also seen.** Very long replies generate at about half speed (about 33 tokens per second) and make oMLX's memory use swing between about 22GB and 38GB.
- **What protects you now.** The 20,000-token cap limits a runaway to roughly 5 to 11 minutes.
- **Possible next steps.** Set top-k to the model's recommended 20; run a deliberate Stop test with the ordinary test account; and when the gatekeeper is built (M2), have it cancel or time-limit requests itself so nothing depends on Open WebUI's Stop button.

### The hidden prompt: understood, left as is (2026-10-12)

- **What it is.** Open WebUI attaches descriptions of its "built-in tools" to every message: helper functions the model may call, such as looking up the current time, asking a structured question, or searching files in the chat. That is about 3,300 extra tokens for an ordinary user and about 4,500 for the admin, who is allowed more tools. This comes from reading Open WebUI's code and has not been confirmed by measurement.
- **What it costs.** About 5 to 6.5 seconds before the first word, on the first message of each new chat. Follow-up messages in the same chat reuse the cache and do not pay it again.
- **Why the cache does not absorb it.** For this model, oMLX saves its cache in steps of 4,096 tokens, and the tool descriptions are shorter than one step.
- **Your decision.** Leave it. A few seconds per conversation is not worth changing anything for.
- **If you change your mind.** Switch the built-in tools off as a global default in Open WebUI (the model capability `builtin_tools`). It takes about 15 seconds of downtime. The model would then lose the ability to look up the date and time or use those helpers by itself. Details are in the log (section 13), in the 2026-10-12 row on the hidden prompt.
- **A side finding for long documents.** Because the cache works in 4,096-token steps, up to that many tokens at the end of a long document may be re-read on each follow-up question. To be measured in M1.

### Checked and found to be fine (2026-10-12)

- **oMLX's 32,768-token context setting** is only a fallback for models whose size is unknown. For this model the limit is its own 262,144 tokens. Not yet tried with a real long document.
- **oMLX's `claude_code: cloud` setting** only affects how oMLX's helper launches a separate coding tool. It sends nothing from your chats anywhere.
- **oMLX's web search feature** exists but runs only if a program calls it explicitly. The chat page does not, and the log shows no calls.
- **oMLX's usage file and its own logs** hold counts and timings only, no prompt or answer text.

## 10. As-built reference

Update this section whenever the setup changes.

### Components

| Component | Version | Installed by | Listens on | Notes |
| --- | --- | --- | --- | --- |
| oMLX | 0.7.0 | Homebrew (`jundot/omlx`) | 127.0.0.1:$OMLX_PORT | API key required; admin dashboard at `/admin` (same key) |
| Open WebUI | 0.11.4 | `uv tool install --python 3.11 "open-webui==0.11.4"` | 127.0.0.1:$WEBUI_PORT | Pinned; upgrade deliberately with `uv tool install` and a new version number |
| Tailscale | 1.104.1 | Standalone `.pkg` from tailscale.com | Tailnet address (Tailscale IP), HTTPS 443 via Serve | Machine name `(machine name)`; auto-updates in-app |
| Model | `mlx-community/Qwen3.6-35B-A3B-4bit` | `hf download` | n/a | 20.4GB in `~/models/Qwen3.6-35B-A3B-4bit`, checksums verified |
| Model (added 2026-10-12) | `mlx-community/Laguna-XS-2.1-6bit` | `hf download`, model data and settings files only (the repository's Python files were skipped) | n/a | Poolside's coding model, 33B parameters, 6-bit. 25GB in `~/models/Laguna-XS-2.1-6bit`, six data files match the published checksums. Single readings from one short test: loads in about 7 s, 25.9GB in memory, about 39 tokens per second. oMLX now reports it as its default model. Not tested: a real coding task, long prompts, and switching between the two models |
| Tools | `uv` 0.12.24 (Homebrew), `hf` 2.2.0 (`uv tool`) | | | |

### Files

| Path | What it is |
| --- | --- |
| `~/Documents/Code/llm-server/llm-start`, `llm-stop` | Day-to-day commands |
| `~/Documents/Code/llm-server/local.env` | This Mac's real Tailscale address and the three port numbers. Not in git. Read by every script |
| `~/Documents/Code/llm-server/local.env.example`, `load-local-env.zsh` | The layout of `local.env` with placeholder values, and the loader the scripts share |
| `~/Documents/Code/llm-server/CLAUDE.local.md` | The real values behind the placeholders, for Claude Code sessions. Not in git |
| `~/Documents/Code/llm-server/git-hooks/pre-commit` | The check git runs before every commit; cancels it if a secret, private data or the real address is included |
| `~/Documents/Code/llm-server/offline/index.html` | The page shown at the Tailscale address while the server is stopped. One self-contained file; loads nothing from anywhere else |
| `~/Documents/Code/llm-server/offline-page.py` | The small program that hands out that page on 127.0.0.1:$OFFLINE_PORT. Started by `llm-stop`, ended by `llm-start`. Uses the Mac's own `/usr/bin/python3`, records no requests, about 20MB of memory |
| `~/Documents/Code/llm-server/offline-message.txt` | Plain text shown instead if the page program fails to start (first line only) |
| `~/Documents/Code/LLM-Server/chat-page/loader.js` | The status badge: a small pill showing "server free", "server occupied" or "server reserved by owner". It sits at the bottom left of the chat area, just to the right of the left pane, and on a phone just above the chat box at its left end. For an admin it also shows "reserve" or "release" and is clickable. It asks the address `/llm-status` every 2 seconds and hides itself if there is no answer (as at the Mac's own `localhost` address) |
| `~/Documents/Code/LLM-Server/open-webui-static/` | Open WebUI's page-extras folder (`STATIC_DIR`), kept in the project so its installed files are not touched. Open WebUI empties and refills it at every start; `llm-start` then copies the badge in as `loader.js`. Not in git |
| `~/Documents/Code/llm-server/llm-reserve` | `llm-reserve on`, `off` or `status`: reserves the server for the owner, releases it, or shows free, in use or reserved |
| `~/Documents/Code/llm-server/relay.py` | The relay on 127.0.0.1:$RELAY_PORT. Passes every request from Open WebUI on to oMLX, records one row per chat request, and while the server is reserved refuses chat requests from anyone whose role is not admin (they are recorded as "refused: reserved"). Started and stopped by `llm-start` and `llm-stop`. Uses the Mac's own `/usr/bin/python3`. For streamed replies it adds a standard flag asking oMLX to report token counts |
| `~/Documents/Code/llm-server/usage.csv` | The usage records: time, user name, user id, model, prompt tokens, reply tokens, seconds, how it ended. No text. Not in git; readable only by this Mac account. Opens in a text editor or spreadsheet |
| `~/Documents/Code/llm-server/start-open-webui.sh` | Loads the settings and key, runs Open WebUI in the foreground (used by `llm-start`) |
| `~/Documents/Code/llm-server/SPEC.md`, `OVERVIEW.md`, `CLAUDE.md` | The project documents, and the summary Claude Code reads at the start of a session |
| `~/Documents/Code/llm-server/.claude/` | Claude Code settings, hooks, skills, rules and an output style for this project |
| `~/Documents/Code/llm-server/.gitignore`, `.git/` | The local git repository and its ignore rules |
| `~/Documents/Code/llm-server/open-webui.env` | Open WebUI settings, commented; no secrets; loaded as shell, so quote values containing `;` |
| `~/Documents/Code/llm-server/omlx-api-key` | The oMLX API key (mode 600). Never print it |
| `~/Documents/Code/llm-server/.webui_secret_key` | Open WebUI's login-signing key (mode 600). Deleting it signs everyone out |
| `~/Documents/Code/llm-server/open-webui-data/` | Open WebUI's database (`webui.db`: accounts, settings, the admin's saved chats, a copy of the oMLX key) and `uploads/` (uploaded files) |
| `~/Documents/Code/llm-server/*.log` | Logs; appended, not rotated |
| `~/models/` | Model folders; oMLX offers every model it finds here |
| `~/.omlx/settings.json` | oMLX's saved options (not the API key) |
| `~/.omlx/cache/` | oMLX's SSD cache of processed prompts; grows with use, automatic cap about 220GB |

### Repository and safeguards

The project folder is a local git repository: no remote, nothing pushed, and no commits yet. You make the commits; Claude cannot.

**Three layers keep secrets and private data out of the repository.**

| Layer | What it does | Applies to |
| --- | --- | --- |
| `.gitignore` | Git does not offer the secret files, `local.env`, `CLAUDE.local.md`, the Open WebUI data folder, logs or database files for committing | Everyone |
| `git-hooks/pre-commit` | **A secret-blocking check that git runs before every commit.** It cancels the commit if any of those files has been staged anyway, if the value of either secret has been pasted into another file, or if this Mac's real Tailscale address or tailnet name appears anywhere in the changes | Everyone, including commits you make in Terminal |
| Placeholders | Tracked files say `$TAILSCALE_HOST`, `$OMLX_PORT` and `$WEBUI_PORT`; the real values live only in `local.env` and `CLAUDE.local.md` | Everyone |

About the pre-commit check:
- It is switched on by a git setting local to this copy: `git config core.hooksPath git-hooks`. Check it with `git config core.hooksPath`, which should print `git-hooks`. A fresh copy of the repository needs that command run once.
- When it cancels a commit, it prints which file or value caused it. Unstage or fix that item and commit again.
- It can be skipped with `git commit --no-verify`. It guards against accidents, not against a deliberate override.
- It was tested by running it directly against seven staged situations (two that should pass, five that should be cancelled). It has not yet been exercised by a real commit.

**What limits Claude Code in this project** (all in `.claude/`, and applying only to Claude, never to you):

| Piece | What it does |
| --- | --- |
| Permissions, deny | Claude cannot read the two secret files or the data folder with its file tool, cannot commit or push, and cannot edit any settings file |
| Permissions, ask | You are prompted before Claude starts or stops the server, undoes or rewrites git history, or edits a rule or a hook |
| Hook: `protect-claude-config.sh` | Blocks a shell command that would change the settings files, the hooks or the rules. Registered on 2026-10-12 and confirmed live the same day in a new chat (one probe command was blocked as intended) |
| Hook: `check-shell-syntax.sh` | After Claude edits a script, checks that it still parses |
| Rules (five files) | Written instructions: secrets and private data; working with you; the two documents; scripts and code; Claude's own configuration |
| Skills (three) | Saved procedures: server status, recording a change, changing a setting |

When a permission needs changing, Claude gives you the text and you paste it into `.claude/settings.json`; Claude then reads it back.

### Current settings that matter

- **Saved data:** ordinary users' chats are temporary and leave nothing in the database (verified). The admin's chats are saved in plain text. Uploaded files are stored in `open-webui-data/uploads` until deleted. Processed prompts are cached by oMLX on disk.
- **Admin limits:** admin viewing of other users' chats, admin export, workspace content access and analytics are switched off in the interface. The owner of the Mac can still read the database file directly.
- **Accounts:** sign-up open; new accounts start as pending and are unusable until the admin approves them; password rules on; logins last 7 days.
- **Outbound traffic:** offline mode on (no version check, no Hugging Face downloads), community sharing, web search, image generation and direct connections off. No non-local connections were seen from either server in spot checks; no sustained watch has been done.
- **Extra model requests:** automatic titles, tags, follow-ups, autocomplete and query generation off; code interpreter and execution off; memories, notes, channels, ratings, arena and chat sharing off.
- **Documents:** an uploaded document's full text is placed in the conversation (no search index).
- **Reply length:** oMLX's default limit is 20,000 tokens per reply (`sampling.max_tokens` in `~/.omlx/settings.json`; edit only while oMLX is stopped).
- **Usage records:** Open WebUI sends each model request to the relay (its saved connection address was changed to the relay's port on 2026-10-12), with the user's name and id attached (`ENABLE_FORWARD_USER_INFO_HEADERS=true`). Tested with one message from the admin account: the row's token counts matched oMLX's own log. Not tested: a guest's temporary chat, Stop, and long replies through the relay.
- **Owner's switch:** for an admin the badge shows "reserve" or "release" and is clickable. The click goes to `/llm-reserve`, which Tailscale Serve passes to the relay, carrying the page's sign-in token. The relay hands that token to Open WebUI on this Mac (`/api/v1/auths/`) and acts only if the answer is an admin; it does not keep or log the token. Tested against the real Open WebUI from the Mac: no token and a made-up token are both refused. The safety of the switch rests on Open WebUI's sign-in.
- **Status badge:** Tailscale Serve passes three addresses: `/` to the chat page, `/llm-status` to the relay's read-only state, and `/llm-reserve` to the owner's switch. The state (free, in use, reserved, and how many requests are in progress) is readable by any device that can reach the Tailscale address, signed in or not. Tested from the Mac: reserving cannot be reached through the Tailscale address. Open WebUI's API documentation page loses its styling with the folder moved; it is not used here.
- **Default model:** new chats start on the Qwen model for everyone (`ui.default_models` in Open WebUI's saved settings, set 2026-10-12). Without it Open WebUI picks the first model alphabetically. A person's own chosen default overrides it. If the default model is ever removed, change this setting in Admin Panel, Settings, Models.
- **Models:** every model oMLX offers is available to every approved user (`BYPASS_MODEL_ACCESS_CONTROL=true`).

## 11. Tool notes: what was found in documentation and source code

Publisher pages and source code, not independent tests, unless a row says it was tested here. Dates show when each was looked up. The log in `LOGS.local.md` has the detail behind each finding.

### Model servers: oMLX, `mlx_lm.server`, llama.cpp

Comparison (checked 2026-10-09):

All three expose an OpenAI-compatible API, so Open WebUI and the gatekeeper can swap between them. Speed claims below are from the projects' own pages or community posts, not measured on this machine.

| | oMLX | `mlx_lm.server` | llama.cpp `llama-server` |
| --- | --- | --- | --- |
| Model format | MLX (safetensors) | MLX (safetensors) | GGUF |
| Reuse a processed long document | Built in: a two-tier KV cache (RAM plus SSD) restores previously seen prefixes across requests and server restarts | In-memory LRU prompt cache only, lost on restart. A proposed disk-persistence change was closed; UNVERIFIED whether any equivalent was merged elsewhere | Slot save/restore API (`POST /slots/{id}?action=save` and `restore`), requires starting with `--slot-save-path`. Manual: a client or proxy must call it. A third-party proxy (hearth) automates it, tested on small contexts only |
| Several models, swapping | Built in | One model | Needs a helper such as llama-swap (UNVERIFIED) |
| Admin UI and monitoring | Web dashboard at `/admin`, menu-bar app | None found | None found |
| Maturity | Newest and fast-changing (project created Feb 2026; some releases track unmerged upstream work) | Upstream and simple | Most mature, runs on any hardware |
| Platform | Apple Silicon only, macOS 15+ | Apple Silicon | Any |
| Privacy concern to check | Menu-bar app has in-app auto-update; check for telemetry or phone-home (R9) | Check | Check |

Conclusion so far (DEFAULT, to be tested): oMLX looks strongest for priorities 1-2 because its disk cache is the feature F7 describes, llama.cpp is the safest comparator and keeps hardware options open, and `mlx_lm.server` is mainly a baseline since oMLX is built on the same MLX library. None of this is proven for the M1 Max.

### Component notes from the design phase

Moved from the spec's architecture table. These record what was known or assumed about each component before and during the build; where the build later settled a point, the log has the outcome.

| Component | Choice | Status |
| --- | --- | --- |
| Model server | Three candidates, all OpenAI-compatible: **oMLX** (`jundot/omlx`, MLX-based), **llama.cpp `llama-server`**, and **`mlx_lm.server`**. Summary of what was found is in the next subsection. | DEFAULT: start M0 with oMLX (already being installed), install llama.cpp for the M1 comparison, and choose after testing (section 8). |
| Front end | Open WebUI, with temporary chats so nothing is saved. | DEFAULT. UNVERIFIED that an admin can disable history for everyone. |
| Gatekeeper | LiteLLM or a small custom proxy. | DEFAULT. UNVERIFIED which queue and parallel-limit features LiteLLM provides. |
| Status page | Small custom web page. First check whether Open WebUI's plugin system can host it. oMLX also ships its own admin dashboard at `/admin` (monitoring, model management, benchmarking); check whether it can supply the memory view or other pieces. | DEFAULT. UNVERIFIED. |
| Network / access | **Tailscale private network** (free Personal plan) with the Tailscale app on each device. Nothing is public and no router ports are opened. Covered devices: iPhone/iPad, Mac and Linux. Guests: **device sharing** (each guest uses their own Tailscale account and sees only the Mac) is the DEFAULT; inviting guests as users is the alternative. **Free-plan user limit (settled 2026-10-10):** tailscale.com/pricing says up to 6 users and unlimited user devices, non-commercial use; the "3 users" figure came from third-party articles. Sharing remains the choice because a shared guest sees only this Mac. Headscale is no longer needed (section 2). Funnel and a VPS relay are deferred, and the owner may revisit either (section 10). | DECIDED (Tailscale app). Guest sharing method: DEFAULT, see Stage 0 Q12. |
| Guest-reachable surface | Only Open WebUI is reachable by guests. The model server listens on localhost only. Do not depend on Tailscale-specific features such as identity headers, because Funnel does not pass them, and that keeps a future switch to Funnel or a VPS relay cheap. Apply the login hardening below from the start. | DEFAULT (added 2026-10-09; confirm with the owner). |
| Open WebUI baseline security | Open WebUI's documentation says it is built for private, trusted networks, which this setup matches. Baseline: register the admin account first (sign-up then closes automatically), keep the default "pending" role for new users, enable password validation, shorten login lifetime (the docs suggest 8-24 hours; **the owner chose 7 days on 2026-10-11**, default was 4 weeks), pin to a tagged release and update promptly. | DEFAULT (confirm with the owner). |
| Model server credentials | If using oMLX, start it with an API key (`--api-key`, or the `OMLX_API_KEY` environment variable, or the admin UI). Its main key also opens the admin dashboard and lets the holder change settings; sub-keys can only call the API. Give only Open WebUI a key, and never give guests any. | DEFAULT, UNVERIFIED in detail. |
| Model swapping | oMLX has built-in multi-model management (several models held with least-recently-used eviction, pinning and per-model timeouts) **(checked 2026-10-09, from the project's own descriptions)**. llama-swap remains a candidate for llama.cpp. | UNVERIFIED: confirm features before adopting. |
| Availability model (revised 2026-10-09) | System sleep disabled while the LLM is meant to be available (the display may sleep). Services are started and stopped manually: oMLX offers `omlx start`, `omlx stop` and `omlx restart` (managed background service) and a menu-bar app. They need not start after a reboot. Must stop cleanly and release memory on demand, because the owner will stop the LLM for intensive work. Avoid configurations that auto-restart a stopped service (for example launchd KeepAlive). Tailscale itself can start at login. | DEFAULT, owner-directed. Whether to start Open WebUI at login is decided at M0 Step 4. The sleep default may change if a schedule is adopted (section 10). |

### oMLX: findings from running it

Version 0.7.0, installed with Homebrew. From its help text, its installed source, its logs and use on this Mac.

- **API key.** `--api-key` is not saved to `~/.omlx/settings.json`; it must be passed at every start, and a plain `omlx serve` runs with no key. The same key opens the admin dashboard at `/admin`. Sub-keys that can only call the API exist but are not used yet. Rejected keys are logged as a short fingerprint only. oMLX renames its process to `omlx-server`, so the key is not visible in the process list.
- **Saved options.** Other options given to `omlx serve` are saved to `~/.omlx/settings.json` and persist. Edit that file only while oMLX is stopped; it rewrites it on start.
- **Model discovery.** It offers every model folder under `~/models`. It is also said to scan `~/.cache/huggingface/hub`; an unrelated image model there was not listed.
- **Context limit.** `sampling.max_context_window` (32768) is only a fallback for models whose size is unknown. The effective limit is a per-model override if set, otherwise the model's native length (262,144 here), clamped only if `max_context_window_policy` is set. Longer prompts are rejected with HTTP 400.
- **Reply limit.** `sampling.max_tokens` is the default reply cap (now 20000). A request that asks for more explicitly can exceed it.
- **Sampling.** Global defaults are temperature 1.0, top-p 0.95, top-k 0 (off), repetition penalty 1.0. It reads only token ids (end-of-sequence, suppressed tokens) from the model's `generation_config.json`, not that file's sampling values (`top_k: 20` for this model).
- **Cache.** A two-tier cache of processed prompts: memory, plus SSD at `~/.omlx/cache` with an automatic size cap (about 220GB here). For this hybrid-attention model it stores snapshots at 4,096-token block boundaries, so reuse works in 4,096-token steps: a follow-up in the same chat restores its cached prefix, but a shared prefix shorter than one block is not reused across chats.
- **Memory.** A memory enforcer sets a ceiling at start that varies with free memory (29.5 to 42GB seen). With the model loaded the process holds about 20GB. During very long replies its memory swung between about 22GB and 38GB. It suggests `sudo sysctl iogpu.wired_limit_mb=60293`; not applied. `memory_pressure`'s free percentage is not a reliable sign of whether the model is loaded; use the process footprint.
- **Loading.** The model loads on the first request after start (6 to 8 s with files warm) and stays loaded; `idle_timeout_seconds` is null.
- **Concurrency.** `max_concurrent_requests` is 8; overlapping requests run together and each slows down (23 to 31 tokens/sec seen against 60 to 66 alone).
- **Thinking.** The model's thinking is returned in a separate `reasoning_content` field when a reply completes. If a low token limit cuts the reply off mid-thought, the thinking text arrives as the content and there is no answer.
- **Other features present but unused.** A web search endpoint (DuckDuckGo by default) that runs only if a client calls it; a `claude_code` setting that only affects how oMLX's helper launches a separate coding tool; a built-in model downloader, quantizer and uploader in the admin dashboard; `omlx start`, `stop`, `restart` for a managed background server (not used; the project's own start and stop commands are used instead).
- **What it records.** `~/.omlx/usage.sqlite3`: hourly totals per model (requests, tokens, timings), no text. `~/.omlx/logs/`: daily logs kept 7 days, no prompt text found. `~/.omlx/stats.json`: all-time counters.
- **Homebrew service.** `brew services` had once been set to run oMLX at login with auto-restart; it was stopped and must stay off.
- **Not yet checked.** Whether it checks for updates, and the behavior of its menu-bar app (not installed here).

### Open WebUI: findings from running it

Version 0.11.4, installed with `uv tool install --python 3.11 "open-webui==0.11.4"`. From its documentation, its installed source and use on this Mac.

- **Settings are sticky.** Many settings are written to its database on first start and then ignore the environment. Later changes go through the Admin Panel, or by stopping it and editing the `config` table in `webui.db` (done for login length and sign-up). Environment-only settings, read at every start, include `BYPASS_MODEL_ACCESS_CONTROL`, `CORS_ALLOW_ORIGIN`, `OFFLINE_MODE`, `ENABLE_ADMIN_CHAT_ACCESS` and `ENABLE_ADMIN_EXPORT`.
- **The settings file is loaded as shell.** Values containing `;` or spaces must be in double quotes.
- **Temporary chat.** With "Enforced Temporary" in the default permissions, ordinary users' chats create no chat record (verified: 0 rows after real use). Admins are exempt. The "temporary" label disappears after the first message. There is a per-user "Temporary Chat by Default" setting (untested). A temporary chat's id is tied to the browser's live socket session; if that session drops (a phone sleeping), Stop returns 404 and the reply keeps generating.
- **Admin access.** `ENABLE_ADMIN_CHAT_ACCESS=false` and `ENABLE_ADMIN_EXPORT=false` remove the admin's screens for viewing and exporting others' chats. `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS=false` also removes the admin's exemption from access control. Chats are stored unencrypted in SQLite (database encryption is unsupported since v0.9.0), so whoever controls the Mac can read saved chats from the file.
- **Model access.** A model that comes from a connection and has no entry in Open WebUI's own model table is refused ("Model not found") for anyone not exempt from access control. `BYPASS_MODEL_ACCESS_CONTROL=true` makes every model from the connection available to every approved user.
- **Accounts.** The first account becomes the admin and sign-up then closes by itself. New accounts take the default role (pending). The email is only a login name and is not verified. With password validation on, the default rule is 8+ characters with upper, lower, digit and symbol. Login length is `auth.jwt_expiry` (default 4 weeks; now 7 days). The login-signing key is generated into `.webui_secret_key` in the working directory, and logins survive restarts as long as that file is kept.
- **Outbound calls found in the source.** A version check to GitHub (`ENABLE_VERSION_UPDATE_CHECK`); a Hugging Face download of the default embedding model on first use; a default connection to `api.openai.com` unless the base URL is set; OpenTelemetry export, off by default. `OFFLINE_MODE=true` blocks the first two. No analytics code was found in the three main source files read; the rest was not audited.
- **Uploads.** Stored in `DATA_DIR/uploads`. With `BYPASS_EMBEDDING_AND_RETRIEVAL=true` a document's whole text goes into the conversation and no embedding model is needed.
- **User identity for the model server.** `ENABLE_FORWARD_USER_INFO_HEADERS=true` makes it attach the user's name, id, email and role, plus chat and message ids, as headers on each request it forwards; a signed-token form is available. Off by default; switched on here in `open-webui.env` on 2026-10-12. **Tested here the same day** with a stand-in for the model server and one message from the admin account: the chat request carried `X-OpenWebUI-User-Name`, `-User-Id` (36 characters), `-User-Email`, `-User-Role`, `-Chat-Id` and `-Auth-Type`, and the requests for the model list carried the same without the chat id. No message id header was seen. Not tested: an ordinary user's temporary chat.
- **Usage dashboard.** Its admin analytics report per user and per model from saved chat messages, so temporary chats are not counted. Switched off here.
- **Built-in tools.** By default it attaches descriptions of its built-in tools to every request (about 3,300 tokens for a user, 4,500 for the admin). A global default model capability, `builtin_tools`, switches them off. Left on, by your decision.
- **Stored credentials.** It keeps the model server's API key in plain text in `webui.db`.
- **Listening address.** `open-webui serve` defaults to all network interfaces; it is started with `--host 127.0.0.1`.
- **Customization.** Every page loads `/static/custom.css` and `/static/loader.js`, both shipped empty; `STATIC_DIR` can point to a folder of your own. Banners, a response watermark and pending-user text are built-in settings. Functions (filters, pipes, actions) and tools are server-side Python plugins (not yet evaluated here). Its license forbids altering Open WebUI branding unless there are 50 or fewer users in any rolling 30 days, which this deployment satisfies.
- **Its own security guidance.** The documentation says it is built for private, trusted networks, and suggests registering the admin first, keeping new users pending, enabling password validation, shortening login lifetime and updating promptly.

### Tailscale: findings

Version 1.104.1, Standalone app. From Tailscale's pages (read 2026-10-09 to 2026-10-11) and use on this Mac.

- **Free Personal plan.** Up to 6 users and unlimited user devices, for non-commercial use (tailscale.com/pricing). An earlier figure of 3 users came from third-party articles.
- **Device sharing.** Available on all plans. The guest needs their own Tailscale account, accepts an invite link (single-use by email, or a copied link; unused links expire in 30 days), and then sees only the shared machine. The shared machine cannot start connections to the guest's devices. The owner can revoke at any time. A shared machine is reachable only by its full name. Tagged machines cannot be shared. Whether shared users count toward the 6-user limit is not stated.
- **Serve cannot serve files on macOS.** The macOS app refuses a file or folder target because of sandbox restrictions; a `text:` target works and is used for the offline message. Text is always sent labelled as plain text, even when it is a whole web page (tested 2026-10-12), so a styled page cannot be delivered this way.
- **Serve.** `tailscale serve --bg $WEBUI_PORT` proxies the tailnet HTTPS address to a local port and is remembered across restarts. Tested: it works for shared guests. The first request after enabling took about 10 s while the certificate was issued.
- **HTTPS certificates.** Enabled per tailnet in the admin console. Doing so publishes the machine name and tailnet DNS name in public certificate logs.
- **Names.** Three separate names: the tailnet display name (a label), the tailnet DNS name (random by default, here `(tailnet name).ts.net`), and the machine name (here `(machine name)`, renamed from the Mac's own name).
- **Encryption.** Traffic is end-to-end encrypted even when relayed; relays cannot read it.
- **Direct versus relayed.** Idle peers show as relayed. The owner's iPhone went direct on the home network (5 ms). Guests away from home may stay relayed; not measured under load.
- **macOS variants.** Tailscale recommends the Standalone app (a `.pkg` from its own site). It runs only after the user logs in to the Mac and updates itself in-app. Its documentation lists Funnel as unsupported in the Standalone and App Store variants.
- **Sign-in.** Through an outside identity provider (Google, Microsoft, GitHub, Apple or a passkey); Tailscale has no passwords of its own.
- **A second VPN.** Another VPN app is installed and connected on this Mac alongside Tailscale and has not caused problems so far.
- **Funnel, VPS relay, Headscale.** Research notes are in the deferred-ideas table below.

### Models and Hugging Face

- The official Qwen repositories are **not** directly usable here. `Qwen/Qwen3.6-35B-A3B` is 71.9 GB across 26 safetensors shards (inferred full precision), with no MLX or GGUF files. `Qwen/Qwen3.6-27B` is 55.6 GB across 15 shards. Both exceed or nearly exhaust 64GB **(checked)**.
- oMLX and `mlx_lm.server` need an **MLX-converted, quantized** build (about 18-24GB for the 35B-A3B at 4-bit). llama.cpp needs **GGUF**. Download only a build that says it is a conversion of the exact base model.
- MLX 4-bit builds of Qwen3.6-35B-A3B seen on Hugging Face **(checked, third-party uploads; file lists not yet opened)**: `mlx-community/Qwen3.6-35B-A3B-4bit` (plain), `mlx-community/Qwen3.6-35B-A3B-4bit-DWQ`, `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit` (mixed precision, size within about 5% of plain 4-bit), `deepsweet/Qwen3.6-35B-A3B-MLX-oQ4` (quantized with oMLX's own oQ tool), `WinterCharm/Qwen3.6-35B-A3B-wMix58` (about 24 GiB). oQ output is standard mlx-lm safetensors and loads in stock MLX apps, so it does not lock the project to oMLX; some builds with extra speculative-decoding parts are oMLX-only, so prefer a plain build.
- The deepsweet page describes an **FP16 variant** as an M1/M2 tweak that gives a noticeable prompt-processing boost, because older chips lack native BF16 support. This targets the M1 Max's weak point. UNVERIFIED on this machine; test it in M1. "VL" in a name means the vision part is kept; no "VL" means text-only.
- **Avoid fine-tunes** unless the owner asks: several results were derivatives (an "abliterated" build, a coding fine-tune, an agent fine-tune), not the base model.
- **Open question: uncensored variants.** The owner asked about `mlx-community`'s "UNCENSORED Qwen 3.6 27B" collection: one third-party model, Qwen3.6-27B-AEON-Ultimate-Uncensored, in MLX at fp16, 8, 6, 5, 4, 3 and 2 bits. Format is fine, but it is a third party's modification of the dense 27B, with unknown method, unknown maker and no benchmarks found. It would also be slower than the 35B-A3B. The spec has no uncensored requirement. Owner answer 2026-10-09: not a requirement for now; stay with the standard models, though the owner expects to swap in and test other models later. If guests include family, note that such a model has no usual refusals.
- Downloading is done from Hugging Face. oMLX's admin dashboard has a built-in model downloader **(from the project's description; UNVERIFIED)**.
- If a community build is not trusted, `mlx_lm.convert` can convert the original, but that needs the full download and an unknown amount of memory. Not recommended unless needed.

### Research task status with findings (as of 2026-10-12)

Moved from the spec, which now keeps a short version of this table.

| # | Task | Blocks | Status |
| --- | --- | --- | --- |
| R1 | Can Open WebUI disable saved chat history for everyone at the admin level? Does it have telemetry or phone-home behavior, and how is it switched off? | M0 | **Done 2026-10-09 (docs and 0.11.4 source read; not yet tested on this Mac).** Findings in the 2026-10-09 log row for R1 (section 13). **Update 2026-10-10, tested here:** enforced temporary chat binds ordinary users (0 chats saved after real use) and does not bind the admin account, whose chats are saved. |
| R2 | Can Open WebUI's plugin or extension system host the queue, messaging and memory view, or is a separate status page needed? Also check whether oMLX's admin dashboard can supply any of it. | M3 design | Open |
| R3 | What queue, parallel-limit and per-user features does LiteLLM provide today, versus a small custom proxy? | M2 | Open |
| R4 | Slot save/restore: how llama.cpp's server does it, what limits apply at 100K+ tokens, and whether `mlx_lm.server` or oMLX has an equivalent. | M1 server choice | **Partly done 2026-10-09:** llama.cpp has the slot API (needs `--slot-save-path`); oMLX persists KV blocks to SSD; `mlx_lm.server` mainline has in-memory cache only. Limits at 100K+ tokens on this hardware still untested. |
| R5 | llama-swap: can it keep several models resident, and does it expose swap events and timings? | M5 | Open |
| R6 | macOS specifics: how to read per-process GPU and unified memory, and whether `iogpu.wired_limit_mb` persists across reboots. | M0 and M4 | Open |
| R7 | Verify that the candidate models in section 5 exist, and confirm their sizes and quantizations. | M0 | **Partly done 2026-10-09:** names exist; official repos are too large; MLX 4-bit builds exist (section 5). Exact file lists and sizes of the chosen build still to open before download. **Update 2026-10-09: done for the M0 model.** Its file list was read, it was downloaded and its checksums match the published values. Repeat for each new contender. |
| R8 | Verify the Tailscale assumptions that matter now: that device sharing works on the free Personal plan and how a guest accepts it, the free plan's user limit, and that connections between devices and the Mac are direct rather than through a slow shared relay (`tailscale ping`). | M0 | **Partly done 2026-10-09:** Tailscale's docs say traffic is end-to-end encrypted even through relays, and that Funnel relays cannot decrypt traffic (TLS ends on the owner's device). User-limit conflict (3 vs 6) and free-plan sharing rules still open. **Updated 2026-10-10:** resolved from tailscale.com/pricing and the sharing doc, see the 2026-10-10 log row for Step 5a (section 13). Still to test on real devices: Serve over HTTPS for a shared-device guest, and direct versus relayed connections. **Update 2026-10-12, tested here:** Serve over HTTPS works for shared guests; the owner's iPhone connects directly on the home network (5 ms). Not yet measured: relayed-connection speed under load for guests away from home. |
| R10 | **New 2026-10-10.** For F9: confirm what Open WebUI's temporary chat stores and shows (indicator, per-user default, what a user can delete); whether enforced temporary binds admins; front ends that keep chats in the browser or encrypt them per user while still working with an OpenAI-compatible server and a login the gatekeeper can use; what oMLX's SSD cache holds (tokens or text recoverable?) and how to cap, expire or disable it; what each component logs. | Saved mode (F9); cache part before guests use M0 | Open |
| R9 | **New.** Check oMLX for telemetry, update checks or phone-home behavior (its menu-bar app has in-app auto-update), and how to disable them. Same check for any other component added. | M0 | **Partly done 2026-10-12 (read in oMLX's source, settings and logs):** its usage file and logs hold counts and timings, no text; its web search endpoint runs only if a client calls it, and the log shows no calls; its `claude_code` setting sends nothing; no telemetry was seen in its log. Not yet checked: whether oMLX checks for updates, and its menu-bar app (not installed here). |

### Deferred ideas: research notes

Moved from the spec, which now keeps a short version of this table.

| Idea | Status | Revisit when |
| --- | --- | --- |
| Slot save/restore in `mlx_lm.server` | Answered 2026-10-09 (partly) | Not found in the mainline; a proposal to persist the prompt cache to disk was closed, and UNVERIFIED whether any equivalent was merged elsewhere. oMLX provides an SSD-persisted KV cache instead; llama.cpp has slot save/restore. Resolve by M1 server choice. |
| Two resident models | Open | After swap times are measured. Needs a raised GPU limit and a pair that leaves room for a 100K-token cache. oMLX can hold several models with LRU eviction. |
| Guest lane on a second port | Deferred | Traffic grows. A small model (for example gpt-oss-20b) with capped context, so guests never evict the owner's document. |
| Hard memory block | Deferred | Soft warnings prove insufficient. |
| Private accounts and chat history | **Moved up 2026-10-09:** wanted next after the first iteration; scope and milestone not yet decided | After the MVP. Needs a per-user login (already chosen for the queue, Q7) and a storage decision, including whether the owner as admin can read guests' chats. |
| Self-hosted network coordination (Headscale) | **Dropped 2026-10-09** | Not needed: the owner is not concerned about connection metadata. Revisit only if that changes. Notes if it ever returns: it is an open-source self-hosted replacement for Tailscale's coordination server; clients are still Tailscale's own apps (macOS and iOS apps are closed source); sharing between users is supported; iOS support is listed as supported in the current README but older copies said not yet; the server must be reachable by every client (likely a VPS); guests must point their app at the owner's server. |
| Tailscale Funnel | Deferred (the owner may revisit) | A public URL for devices that cannot install the app, such as a managed work or school computer. **Checked 2026-10-09 against Tailscale's documentation:** a Funnel relay uses a TCP proxy, cannot decrypt traffic, and the visitor's device ends the TLS connection with the owner's device; Funnel only works over TLS and needs valid HTTPS certificates for the tailnet. It needs a recent Tailscale version (1.38.3 or later), MagicDNS, HTTPS enabled and a Funnel permission in the policy file; it allows only certain ports; on macOS it needs the open-source variant of the Tailscale app; it does not pass Tailscale identity headers. **Not checked (spec claims, UNVERIFIED):** beta status, non-configurable bandwidth limits with no published numbers, only `ts.net` names, ports 443, 8443 and 10000. It makes the Open WebUI login public, and Open WebUI's documentation says it should sit behind a VPN, zero-trust proxy or authenticated reverse proxy, so add an access gate (for example a local reverse proxy with a long random password) before enabling it. Verify before use: the real bandwidth limit with a large-document upload test, and how the open-source macOS variant updates. A managed work computer may also be inspected by its employer. |
| VPS relay (AWS Lightsail), TLS passthrough | Deferred (the owner may revisit) | Fallback if Funnel's beta status, bandwidth limits or ports become a problem. Since metadata is no longer a concern, owning the relay is not a privacy benefit; its remaining advantage is freedom from Funnel's limits. A small VPS forwards encrypted traffic by domain name (SNI) through a tunnel to the Mac, so the Mac still ends TLS and the VPS sees only encrypted data. Needs a domain, a forwarder (for example haproxy or Caddy's layer-4 module; Pangolin ends TLS on the VPS, so it is not end-to-end), certificates managed on the Mac, ongoing VPS upkeep (OS updates, domain renewal, monitoring, remote login hardening), and the same access gate in front of Open WebUI. AWS sign-in services such as Cognito are not needed, because Open WebUI handles accounts. Prices and details are UNVERIFIED. |
| Funnel versus VPS relay: security comparison (reasoning, 2026-10-09, not tested) | Recorded | Both put the Open WebUI login on the public internet, so both need the same gate, closed sign-ups, strong passwords and prompt updates. Funnel: Tailscale runs and patches the relay and hides the Mac's home IP address behind it, so there is less for the owner to maintain. VPS relay: the owner must patch a public server, and (inference) a compromised VPS could be a foothold into the tunnel to the home Mac, so the tunnel must be restricted to the one needed port. For a hobby setup, a vendor-maintained relay is generally the lower-risk choice; the VPS wins only if Funnel's limits break the use case. The private Tailscale network avoids the exposure entirely, which is why it is the MVP choice. |
| SSD-streaming engines: [Flash-MoE](https://insiderllm.com/guides/flash-moe-run-397b-model-laptop/), [Colibri](https://www.everydev.ai/tools/colibri/llms.txt) | Open | Run huge MoE models from SSD at a few tokens per second. Flash-MoE is built for one model (Qwen3.5-397B-A17B, about 4.4 tokens/sec on a 48GB M3 Max); Colibri supports several model families. Single-user and slow, so possibly a path for hard problems while nobody else is using the server. Not suitable for long documents. Expect slower results on the M1 Max. Details come from search results that were not opened in full: verify. |
| Hardware upgrade or replacement | Open | Decide from proof-of-concept measurements. |
| Shared machine (partitioning) | **Direction chosen 2026-10-09:** the LLM runs in the background alongside the owner's general use; the memory reservation is still open | The LLM runs in the background while the owner uses the Mac as normal, with reduced capability. Needs a memory budget that reserves room for macOS and the owner's apps on top of the model and KV cache. This interacts with the GPU memory limit (section 3), model choice (section 5) and whether two models can stay resident. Decide how much memory and CPU to reserve, and what happens when the owner's apps create memory pressure. |
| Quick offline and relaunch | **Wanted 2026-10-09:** the owner stops the LLM manually for intensive work such as ML training and starts it again afterward; a friendly message for guests while it is down is open | Take the server offline at a moment's notice so the owner can use the machine's full capability, then relaunch the LLM when done. Needs graceful shutdown (tell queued users, drain or cancel requests) and a one-step restart. Stopping discards the loaded KV cache, so slot save/restore (F7) would soften the cost. Consider how it relates to owner-priority mode (F4) and the queue. |
| **Friendly "offline" page (owner reminder 2026-10-11)** | **Built in basic form 2026-10-12** (plain text; the notes here were written before it was built) | **Outcome:** option (a) was built with plain text instead of a page, because Tailscale's macOS app cannot serve files; `llm-stop` shows the message and `llm-start` switches back. Option (b)'s idea that the gatekeeper could own the page was wrong: the gatekeeper sits behind the chat page and the offline page must sit in front. Still wanted: a styled page and a distinct "reserved" message. **Original notes:** When the LLM is stopped, the Tailscale address shows a bare error page because Tailscale Serve is still forwarding to a port nothing is listening on. Wanted: a simple page telling guests the server is offline (and, ideally, when it is expected back). Options to evaluate: (a) `llm-stop` switches Tailscale Serve to a small static page and `llm-start` switches it back; (b) a tiny always-on local web server in front of Open WebUI that shows the page whenever Open WebUI is down (this is also where the M2 gatekeeper will sit, so the gatekeeper could own it). Must not auto-restart anything the owner stopped. Also consider a distinct message for "owner is using the machine for heavy work". |
| Scheduled availability | Open (the owner wants it available "throughout the day"; overnight is undecided) | Run the server on a schedule to reduce exposure to attacks and save energy when use is unlikely. Needs a schedule definition, a clear message for guests when the server is off, a decision on what guests see when the Mac is unreachable, and a rethink of the "sleep disabled" default. |

## 12. Cautions and lessons

- A secret-blocking check runs before every git commit (`git-hooks/pre-commit`). If a commit is cancelled, read its message; do not reach for `--no-verify`. In a fresh copy of the repository it is off until `git config core.hooksPath git-hooks` is run.
- Hooks and permissions in `.claude/` limit Claude only. They never check what you do in Terminal; the git hook is what covers your commits.

- oMLX does NOT save `--api-key` to its settings; a plain `omlx serve` runs with no key. Always start with `llm-start`.
- `omlx serve --model-dir ...` does save its other options to `~/.omlx/settings.json`. A Homebrew service for oMLX once ran at login with auto-restart; it was stopped with `brew services stop omlx` and must stay off.
- The oMLX memory ceiling varies by start (29.5 to 36.0GB seen). oMLX suggests `sudo sysctl iogpu.wired_limit_mb=60293`; do NOT apply it without R6.
- Many Open WebUI settings are saved in its database on first start and then ignore `open-webui.env`. Change those in Admin Panel, or stop Open WebUI and edit the `config` table (done once, for the login lifetime). Keep the env file in step for a future fresh install.
- `open-webui.env` is loaded as shell: put any value containing `;` or spaces in double quotes. An unquoted semicolon once stopped Open WebUI from starting.
- `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS=false` also removes the admin's exemption from model permissions; `BYPASS_MODEL_ACCESS_CONTROL=true` is what makes oMLX's models usable by everyone. Without it every chat fails with "Model not found".
- Open WebUI stores the oMLX key in plain text in `webui.db`. Changing the key means updating the key file and Open WebUI's connection setting.
- Open WebUI closes sign-up by itself after the first account on a fresh install; it was turned back on (2026-10-11) so guests sign up and the owner approves. Passwords need 8+ characters with upper, lower, digit and symbol; tell people before they type one, and suggest saving the password straight away. A rejected first attempt caused a lockout during setup.
- Download models with `HF_HUB_DISABLE_XET=1 HF_HUB_DISABLE_TELEMETRY=1 hf download <repo> --local-dir ~/models/<name>`; the default transfer mode held everything in memory.
- The model thinks before answering and needs a generous token limit; a low limit returns thinking text and no answer.
- All speed and size figures are single readings until M1. Official Qwen repos are full precision and unusable here; only MLX-converted 4-bit builds fit.

## 13. Decision and results log

The dated log of every decision, step and finding is kept in `LOGS.local.md` in the project folder. That file is not in git: it stays on this Mac only. It holds high-level changes and decisions only; new rows are added there, at the end.

## 14. Sources

Vendor and project pages, not independent tests.

- Tailscale Funnel: https://tailscale.com/kb/1223/funnel
- Tailscale security and encryption: https://tailscale.com/security
- Tailscale relay (DERP) servers: https://tailscale.com/docs/reference/derp-servers
- oMLX project and releases: https://github.com/jundot/omlx and https://github.com/jundot/omlx/releases/tag/v0.5.0.dev4
- `mlx_lm.server` disk-cache proposal (closed): https://github.com/ml-explore/mlx-lm/pull/1405
- llama.cpp slot save/restore discussion: https://github.com/ggml-org/llama.cpp/discussions/18244 and https://lemonade-server.ai/docs/api/llamacpp/
- hearth (third-party llama.cpp cache proxy): https://pypi.org/project/hearth-llm/
- Qwen3.6-35B-A3B official repository: https://huggingface.co/Qwen/Qwen3.6-35B-A3B/tree/main
- Qwen3.6-27B official repository: https://huggingface.co/Qwen/Qwen3.6-27B/tree/main
- MLX builds: https://huggingface.co/deepsweet/Qwen3.6-35B-A3B-MLX-oQ4, https://huggingface.co/mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit, https://huggingface.co/mlx-community/Qwen3.6-35B-A3B-4bit-DWQ, https://huggingface.co/WinterCharm/Qwen3.6-35B-A3B-wMix58
- Uncensored collection: https://huggingface.co/collections/mlx-community/uncensored-qwen-36-27b
- Qwen3.8-27B: https://huggingface.co/Qwen/Qwen3.8-27B and comparison https://www.datalearner.com/en/ai-models/compare/qwen3-8-27b/vs/qwen3-6-27b
- Qwen3.8-Flash-Next versus 27B: https://www.yottalabs.ai/post/qwen-3-8-flash-next-vs-qwen-3-8-27b-2026
- Laguna XS 2.1: https://www.respan.ai/models/laguna-xs-2.1
- Mac model roundup: https://insiderllm.com/guides/best-local-llms-mac-2026/
