# Sourced by the scripts in this folder, after DIR is set. Loads the address
# and port numbers from local.env, which is kept out of git.
if [ ! -f "$DIR/local.env" ]; then
  echo "Missing $DIR/local.env. Copy local.env.example to local.env and fill in the values." >&2
  exit 1
fi
source "$DIR/local.env"
for _v in TAILSCALE_HOST OMLX_PORT WEBUI_PORT OFFLINE_PORT RELAY_PORT; do
  if [ -z "${(P)_v}" ]; then
    echo "$_v is not set in $DIR/local.env." >&2
    exit 1
  fi
done
_ports=("$OMLX_PORT" "$WEBUI_PORT" "$OFFLINE_PORT" "$RELAY_PORT")
_different=(${(u)_ports})
case "${(j::)_ports}" in
  *[!0-9]*) echo "The four port values in $DIR/local.env must be numbers." >&2; exit 1 ;;
esac
if [ ${#_different} -ne ${#_ports} ] || [ ${_ports[(I)0]} -ne 0 ]; then
  echo "The four port values in $DIR/local.env must be four different port numbers." >&2
  exit 1
fi
unset _v _ports _different
