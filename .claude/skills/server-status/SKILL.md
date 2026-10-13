---
name: server-status
description: Report whether the private LLM server is running (oMLX and Open WebUI), what the Tailscale address is serving, which devices are connected, and the most recent requests. Use when the owner asks if the server is up, why the chat page is not loading, or before and after any start, stop or settings change.
---

# Server status

Run the helper. It is read-only and prints no secrets.

```bash
./.claude/skills/server-status/status.sh
```

## Reading the result

- **Both "running"** and the Tailscale address serving `proxy http://127.0.0.1:$WEBUI_PORT`: normal operation.
- **Both "not running"**, the offline page "running", and the address serving `proxy http://127.0.0.1:$OFFLINE_PORT`: stopped on purpose with `llm-stop`. Guests see the offline page.
- **Both "not running"** and the address serving `text "Server not runnin..."`: stopped, but the offline page program failed to start and the plain message is showing instead. Look at `offline-page.log`.
- **The address serving a proxy to a port where nothing is running**: the Mac was probably rebooted. Guests see a bare error. Tell the owner; `./llm-start` or `./llm-stop` fixes it.
- **The offline page "running" while the other two are also running**: normal for about a minute during `llm-start`; otherwise the switch back to the chat failed.
- **One running and one not**: something failed. Read the tail of `omlx.log` or `open-webui.log` before suggesting a restart.
- **Listening on anything other than `127.0.0.1`**: a problem. Both must be reachable only from this Mac.
- **Memory**: oMLX holds about 20GB once the model has loaded. It loads on the first request after a start, so a low figure right after `llm-start` is normal.
- **A request that ended with `length`**: the reply hit the length cap. Mention it.

## Then

Report in plain language what is running and what a guest would see right now. Do not start or stop anything unless the owner asks.
