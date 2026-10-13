#!/bin/zsh
# Prints the state of the private LLM server without revealing any secret.
# Read-only: starts and stops nothing.
DIR="${0:A:h:h:h:h}"
TS=/usr/local/bin/tailscale
source "$DIR/load-local-env.zsh"

port_state() {  # name, port
  local pid
  pid="$(lsof -nP -tiTCP:"$2" -sTCP:LISTEN 2>/dev/null | head -n 1)"
  if [ -n "$pid" ]; then
    local addr mem
    addr="$(lsof -nP -a -p "$pid" -iTCP -sTCP:LISTEN 2>/dev/null | awk 'NR>1{print $9}' | head -n 1)"
    mem="$(ps -o rss= -p "$pid" | awk '{printf "%.1f GB", $1/1048576}')"
    echo "$1: running (pid $pid, listening on $addr, memory $mem)"
  else
    echo "$1: not running"
  fi
}

echo "Project folder: $DIR"
port_state "oMLX (model server)" "$OMLX_PORT"
port_state "Open WebUI (chat page)" "$WEBUI_PORT"
port_state "Offline page (shown while stopped)" "$OFFLINE_PORT"

if [ -x "$TS" ]; then
  echo "Tailscale address is serving:"
  "$TS" serve status 2>&1 | sed 's/^/  /'
  echo "Devices:"
  "$TS" status 2>/dev/null | awk '{printf "  %-24s %-6s %s\n", $2, $4, ($5=="-"?"idle":$5" "$6" "$7)}'
else
  echo "Tailscale: command not found at $TS"
fi

if [ -f "$DIR/omlx.log" ]; then
  echo "Last five requests (time, tokens, speed, prompt size, how it ended):"
  grep "Chat completion" "$DIR/omlx.log" | tail -n 5 \
    | sed -E 's/^([0-9-]+ [0-9:]+).*model=([^,]+), ([0-9]+ tokens in [0-9.]+s \([0-9.]+ tok\/s\)), prompt: ([0-9]+), finish_reason=([a-z_]+).*/  \1  \2  \3  prompt \4  \5/'
fi
