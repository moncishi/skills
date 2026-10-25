#!/usr/bin/env bash
# probe-and-fix.sh — find a mihomo exit node that Google Antigravity (agy) accepts,
# and select it in the target proxy-group.
#
# Root cause this solves: Antigravity's agent path rejects datacenter/hosting exit IPs
# (`FAILED_PRECONDITION (400): User location is not supported for the API use.`).
#
# For a much faster HTTP-based probe (1-4s/attempt, no desktop needed) see
# probe-fast.sh and `scan-llm-agy.sh --fast`.
#
# Usage: see --help
set -u

MIHOMO_DIR="${MIHOMO_DIR:-$HOME/.config/mihomo}"
CONFIG="$MIHOMO_DIR/config.yaml"
API="${MIHOMO_API:-http://127.0.0.1:9090}"
GROUP="${GROUP:-LLM}"
AGY="${AGY:-$HOME/.local/bin/agy}"
TIMEOUT="${TIMEOUT:-90}"

# Default candidate pool: prefer the "feiniao" (Hysteria2) provider nodes, which are the
# ones that historically pass Antigravity's checks. Extend as you discover working nodes.
DEFAULT_NODES="${DEFAULT_NODES:-新加坡01aws hy2台湾01 新加坡02aws 新加坡03aws 新加坡04aws 新加坡05aws 日本01aws 日本02aws 美国02aws}"

FULL=0; LIST=0; DRY=0; REFRESH=0; VERIFY=0; NODES=""

while [ $# -gt 0 ]; do
  case "$1" in
    --full) FULL=1 ;;
    --list) LIST=1 ;;
    --dry-run) DRY=1 ;;
    --refresh) REFRESH=1 ;;
    --verify) VERIFY=1 ;;
    --nodes) shift; NODES="${1:-}" ;;
    --group) shift; GROUP="${1:-LLM}" ;;
    --timeout) shift; TIMEOUT="${1:-90}" ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

SECRET="$(sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' "$CONFIG" 2>/dev/null | head -1)"
[ -n "$SECRET" ] || { echo "ERR: cannot read secret from $CONFIG" >&2; exit 1; }
AGY_BIN="$(command -v agy || echo "$AGY")"
[ -x "$AGY_BIN" ] || { echo "ERR: agy not found ($AGY_BIN)" >&2; exit 1; }

api() { curl -s --noproxy '*' -H "Authorization: Bearer $SECRET" "$API$1"; }
set_node() { curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT \
  -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' \
  -d "{\"name\":\"$1\"}" "$API/proxies/$GROUP"; }

group_now() { api "/proxies/$GROUP" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("now",""))' 2>/dev/null; }
group_nodes() {
  api "/proxies/$GROUP" | python3 -c '
import sys,json
d=json.load(sys.stdin)
bad=("剩余流量","套餐到期","过滤掉","电报群","防失联","每次使用前","有超过","官网")
for n in d.get("all",[]):
    if any(b in n for b in bad): continue
    print(n)
' 2>/dev/null
}

# ---- env for agy: needs desktop session so it can unlock gnome-keyring ----
setup_agy_env() {
  export HOME="${HOME:-/home/monci}"
  export DISPLAY="${DISPLAY:-:1}"
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=${XDG_RUNTIME_DIR}/bus}"
  # force agy through mihomo
  export http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890 all_proxy=http://127.0.0.1:7890
  export no_proxy="127.0.0.1,localhost,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
  export NO_PROXY="$no_proxy"
}

probe() {
  local node="$1" code out
  code="$(set_node "$node")"
  [ "$code" = "204" ] || { echo "SETFAIL"; return; }
  sleep 1
  out="$(cd "$HOME" && timeout "$TIMEOUT" "$AGY_BIN" --print "reply with exactly PONG" 2>&1 | tr -d '\r')"
  if   grep -q "PONG"                    <<<"$out"; then echo "PONG"
  elif grep -q "location is not supported" <<<"$out"; then echo "LOCATION"
  elif grep -qE "SUBSCRIPTION_REQUIRED|PERMISSION_DENIED" <<<"$out"; then echo "PERMISSION"
  elif grep -qE "UNAUTHENTICATED|not logged into Antigravity" <<<"$out"; then echo "NOAUTH"
  elif grep -q "proxyconnect" <<<"$out"; then echo "PROXYFAIL"
  else echo "OTHER/TIMEOUT"
  fi
}

setup_agy_env

if [ "$REFRESH" = 1 ]; then
  for p in $(api /providers/proxies | python3 -c 'import sys,json;print(" ".join(json.load(sys.stdin)["providers"].keys()))' 2>/dev/null); do
    printf 'refresh %s -> HTTP %s\n' "$p" "$(curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT -H "Authorization: Bearer $SECRET" "$API/providers/proxies/$p")"
  done
fi

if [ "$LIST" = 1 ]; then
  echo "LLM/[$GROUP] now = $(group_now)"; group_nodes; exit 0
fi

if [ "$VERIFY" = 1 ]; then
  echo "[$GROUP=$(group_now)] verify -> $(probe "$(group_now)")"; exit 0
fi

if [ "$FULL" = 1 ]; then NODES="$(group_nodes | tr '\n' ' ')"; fi
[ -n "$NODES" ] || NODES="$DEFAULT_NODES"

echo "group=$GROUP  now=$(group_now)  timeout=${TIMEOUT}s"
echo "candidates: $NODES"
echo "------------------------------------------------------------------"
WINNER=""
for n in $NODES; do
  r="$(probe "$n")"
  printf '%-28s %s\n' "$n" "$r"
  if [ "$r" = "PONG" ] && [ -z "$WINNER" ]; then WINNER="$n"; fi
done
echo "------------------------------------------------------------------"
if [ -z "$WINNER" ]; then
  echo "❌ no Antigravity-compatible node found in the candidate set."
  echo "   -> try: $0 --full   /   $0 --refresh   /   add a residential-IP provider"
  exit 1
fi
if [ "$DRY" = 1 ]; then
  echo "✅ first working node: $WINNER (dry-run, not switching)"
else
  set_node "$WINNER" >/dev/null
  echo "✅ switched $GROUP -> $WINNER"
fi
