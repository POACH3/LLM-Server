# Sourced by the scripts in this folder, after DIR is set. Loads the address
# and port numbers from local.env, which is kept out of git.
if [ ! -f "$DIR/local.env" ]; then
  echo "Missing $DIR/local.env. Copy local.env.example to local.env and fill in the values." >&2
  exit 1
fi
source "$DIR/local.env"
for _v in TAILSCALE_HOST OMLX_PORT WEBUI_PORT OFFLINE_PORT; do
  if [ -z "${(P)_v}" ]; then
    echo "$_v is not set in $DIR/local.env." >&2
    exit 1
  fi
done
case "$OMLX_PORT$WEBUI_PORT$OFFLINE_PORT" in
  *[!0-9]*) echo "OMLX_PORT, WEBUI_PORT and OFFLINE_PORT in $DIR/local.env must be numbers." >&2; exit 1 ;;
esac
if [ "$OMLX_PORT" -lt 1 ] || [ "$WEBUI_PORT" -lt 1 ] || [ "$OFFLINE_PORT" -lt 1 ] \
   || [ "$OMLX_PORT" = "$WEBUI_PORT" ] || [ "$OMLX_PORT" = "$OFFLINE_PORT" ] \
   || [ "$WEBUI_PORT" = "$OFFLINE_PORT" ]; then
  echo "OMLX_PORT, WEBUI_PORT and OFFLINE_PORT in $DIR/local.env must be three different port numbers." >&2
  exit 1
fi
unset _v
