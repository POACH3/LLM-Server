#!/bin/zsh
# Starts Open WebUI in the foreground on this Mac only. The address and port
# numbers come from local.env.
# Stop it with Ctrl+C. Settings come from open-webui.env; the oMLX API key
# is read from omlx-api-key. Note: Open WebUI also saves that key in its own
# database (open-webui-data/webui.db) on first start.
set -e
DIR="${0:A:h}"
cd "$DIR"
source "$DIR/load-local-env.zsh"
set -a
source ./open-webui.env
set +a
# Data folder (accounts, settings, uploads) sits next to this script.
export DATA_DIR="$DIR/open-webui-data"
# Folder Open WebUI serves its page extras from (icons, and the loader.js it
# loads on every page). Kept next to this script, so the status badge can be
# added without touching Open WebUI's installed files. Open WebUI empties and
# refills this folder at every start; llm-start then copies the badge in.
export STATIC_DIR="$DIR/open-webui-static"
mkdir -p "$STATIC_DIR"
export OPENAI_API_KEY="$(cat ./omlx-api-key)"
# Where requests for the model go: the relay, which passes them on to
# the model server. (Open WebUI saves this address in its database on first
# start; after that it is changed in Admin Panel, Settings, Connections.)
# And which page addresses may call the API: the Tailscale address (guests
# and the owner's other devices) and this Mac.
export OPENAI_API_BASE_URL="http://127.0.0.1:$RELAY_PORT/v1"
export CORS_ALLOW_ORIGIN="https://$TAILSCALE_HOST;http://localhost:$WEBUI_PORT"
exec "$HOME/.local/bin/open-webui" serve --host 127.0.0.1 --port "$WEBUI_PORT"
