---
paths:
  - "llm-start"
  - "llm-stop"
  - "*.sh"
  - "**/*.py"
  - "open-webui.env"
---

# Scripts, settings and code

- Never hard-code a model name or a model path. The owner swaps models; everything must work with whatever oMLX offers from `~/models`.
- Every server on this Mac listens on `127.0.0.1` only. The only way in from another device is Tailscale Serve.
- Nothing starts at login, and nothing restarts by itself after the owner stops it. No launchd KeepAlive, no RunAtLoad, no watchdog loops.
- Stopping must free the model's memory.
- Never write the Tailscale address or a port number into a script or settings file. Scripts source `load-local-env.zsh` and use `$TAILSCALE_HOST`, `$OMLX_PORT`, `$WEBUI_PORT` and `$OFFLINE_PORT`.
- Scripts find their own location (`DIR="${0:A:h}"` in zsh) so the folder can be moved. Do not write absolute paths to this folder.
- oMLX must always be started with its API key. Start it only through `llm-start`.
- `open-webui.env` is loaded as shell: quote any value containing `;` or spaces. It holds no secrets.
- Open WebUI's installed files are not modified. The one planned exception is removing its branding, which must be a re-runnable patch script.
- Components must stay swappable: the relay and anything built later should work if the front end or the model server is replaced.
- Keep comments in the style already used: a short header saying what the script does and how to undo it, and a comment wherever the reason is not obvious.
