#!/bin/sh
# Wait for a TCP host:port to accept connections. Pure /bin/sh, no dependencies.
#   wait-for-it.sh host:port [-t seconds] [-- command args...]
set -eu

usage() {
  echo "usage: $0 host:port [-t timeout_seconds] [-- command args...]" >&2
  exit 2
}

[ $# -ge 1 ] || usage
HOSTPORT="$1"; shift
HOST="${HOSTPORT%%:*}"
PORT="${HOSTPORT##*:}"
TIMEOUT=30

while [ $# -gt 0 ]; do
  case "$1" in
    -t) TIMEOUT="$2"; shift 2 ;;
    --) shift; break ;;
    *) usage ;;
  esac
done

[ -n "$HOST" ] && [ -n "$PORT" ] && [ "$HOST" != "$PORT" ] || usage

probe() {
  if command -v nc >/dev/null 2>&1; then
    nc -z "$HOST" "$PORT" >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c "import socket,sys; s=socket.socket(); s.settimeout(1)
try: s.connect(('$HOST', int('$PORT'))); sys.exit(0)
except OSError: sys.exit(1)"
  else
    (exec 3<>"/dev/tcp/$HOST/$PORT") >/dev/null 2>&1
  fi
}

start=$(date +%s)
until probe; do
  now=$(date +%s)
  if [ $((now - start)) -ge "$TIMEOUT" ]; then
    echo "wait-for-it: timeout after ${TIMEOUT}s waiting for $HOST:$PORT" >&2
    exit 1
  fi
  sleep 1
done
echo "wait-for-it: $HOST:$PORT is available after $(( $(date +%s) - start ))s" >&2

if [ $# -gt 0 ]; then
  exec "$@"
fi
