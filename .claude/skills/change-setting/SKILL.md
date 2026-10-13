---
name: change-setting
description: Change a setting of Open WebUI or oMLX on this server safely. Use when the owner asks to change behavior such as login length, sign-up, reply length, permissions, features, or sampling, or when a setting does not seem to take effect.
---

# Changing a setting

Most surprises on this project came from settings that live somewhere other than where they were edited. Find out where the setting lives before changing anything.

## Open WebUI

There are two kinds of setting.

1. **Read from the environment at every start.** Edit `open-webui.env`, then restart Open WebUI. Known examples: `OFFLINE_MODE`, `BYPASS_MODEL_ACCESS_CONTROL`, `CORS_ALLOW_ORIGIN`, `ENABLE_ADMIN_CHAT_ACCESS`, `ENABLE_ADMIN_EXPORT`, `ENABLE_FORWARD_USER_INFO_HEADERS`.
2. **Saved in the database on first start, then the environment is ignored.** Known examples: login length (`auth.jwt_expiry`), sign-up (`ui.enable_signup`), default role, default permissions, banners, default model settings. Changing `open-webui.env` alone does nothing for these.

To tell which kind a setting is, look it up in the installed source:

```bash
S=~/.local/share/uv/tools/open-webui/lib/python3.11/site-packages/open_webui
grep -n "THE_SETTING_NAME" $S/env.py $S/config.py
```

A name defined in `env.py` is the first kind. A name in `config.py` that also appears in the mapping of dotted keys near the end of that file (for example `'ui.enable_signup': ENABLE_SIGNUP`) is the second kind.

For the second kind, either the owner changes it in the Admin Panel, or, with the owner's go-ahead:

1. Stop the server (`./llm-stop`).
2. Update the row in the `config` table of `open-webui-data/webui.db`. Values are JSON: text needs double quotes inside the SQL string, for example `'"7d"'`; booleans are `true` or `false`.
3. Also update `open-webui.env`, so a future fresh install matches.
4. Start the server (`./llm-start`) and read the row back to confirm.

`open-webui.env` is loaded as shell. Put any value containing `;`, spaces or other shell characters in double quotes.

## oMLX

Settings are in `~/.omlx/settings.json`. oMLX rewrites that file when it starts, so edit it only while oMLX is stopped. The API key is the exception: it is not stored there and is passed by `llm-start` at every start.

## Every time

1. Say what will change, what it affects for guests, and how long the server will be down. Wait for the owner's go-ahead.
2. Check nobody is mid-request before stopping: look at the last lines of `omlx.log`.
3. Change one setting at a time.
4. Verify the effect, not just the stored value, where that is possible without logging in as someone.
5. Record it with the `record-change` skill.
