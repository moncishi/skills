#!/usr/bin/env bash
# probe-and-fix.sh — find a mihomo exit node that Google Antigravity (agy) accepts,
# and select it in the target proxy-group.
#
# Root cause this solves: Antigravity's agent path rejects datacenter/hosting exit IPs
# (`FAILED_PRECONDITION (400): User location is not supported for the API use.`).
#
# Multiplier policy (AGY): prefer 3x nodes first, then 5x nodes, and avoid 1x nodes.
# Hong Kong nodes are skipped by default because Antigravity rejects HK exit IPs.
#
# For a much faster HTTP-based probe (1-4s/attempt, no desktop needed) see
# probe-fast.sh and `scan-llm-agy.sh --fast`.
#
# Usage:
#   probe-and-fix.sh                 # probe AGY candidates (3x first, then 5x; skip HK & 1x)
#   probe-and-fix.sh --full          # probe all non-1x nodes in target group (still 3x -> 5x)
#   probe-and-fix.sh --include-hk    # include Hong Kong nodes in auto-candidates
#   probe-and-fix.sh --include-1x    # allow 1x nodes as last resort in auto-candidates
#   probe-and-fix.sh --nodes "a,b"   # probe only these comma/space-separated nodes (exact order)
#   probe-and-fix.sh --list          # list current selection and prioritized candidates
#   probe-and-fix.sh --dry-run       # probe without switching
#   probe-and-fix.sh --refresh       # force-refresh proxy providers before probing
#   probe-and-fix.sh --verify        # verify currently selected node only
set -u

MIHOMO_DIR="${MIHOMO_DIR:-$HOME/.config/mihomo}"
CONFIG="$MIHOMO_DIR/config.yaml"
API="${MIHOMO_API:-http://127.0.0.1:9090}"
GROUP="${GROUP:-AGY}"
AGY="${AGY:-$HOME/.local/bin/agy}"
TIMEOUT="${TIMEOUT:-90}"
DEFAULT_NODES="${DEFAULT_NODES:-}"

FULL=0; LIST=0; DRY=0; REFRESH=0; VERIFY=0; INCLUDE_HK=0; INCLUDE_1X=0; NODES=""

while [ $# -gt 0 ]; do
  case "$1" in
    --full) FULL=1 ;;
    --list) LIST=1 ;;
    --dry-run) DRY=1 ;;
    --refresh) REFRESH=1 ;;
    --verify) VERIFY=1 ;;
    --include-hk) INCLUDE_HK=1 ;;
    --include-1x) INCLUDE_1X=1 ;;
    --nodes) shift; NODES="${1:-}" ;;
    --group) shift; GROUP="${1:-AGY}" ;;
    --timeout) shift; TIMEOUT="${1:-90}" ;;
    -h|--help) sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

SECRET="$(sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' "$CONFIG" 2>/dev/null | head -1)"
[ -n "$SECRET" ] || { echo "ERR: cannot read secret from $CONFIG" >&2; exit 1; }
AGY_BIN="$(command -v agy || echo "$AGY")"
[ -x "$AGY_BIN" ] || { echo "ERR: agy not found ($AGY_BIN)" >&2; exit 1; }

api() { curl -s --noproxy '*' -H "Authorization: Bearer $SECRET" "$API$1"; }
set_node() {
  local payload
  payload="$(python3 -c 'import json,sys;print(json.dumps({"name":sys.argv[1]}))' "$1")"
  curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT \
    -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' \
    -d "$payload" "$API/proxies/$GROUP"
}

group_now() { api "/proxies/$GROUP" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("now",""))' 2>/dev/null; }
group_nodes() {
  api "/proxies/$GROUP" | python3 -c '
import re, sys, json
include_hk = sys.argv[1] == "1"
include_1x = sys.argv[2] == "1"
d = json.load(sys.stdin)
bad = ("剩余流量","套餐到期","过滤掉","电报群","防失联","每次使用前","有超过","官网","永久流量")
is_1x = re.compile(r"(^|[^0-9.])1[倍xX]")
is_3x = re.compile(r"(^|[^0-9.])3[倍xX]")
is_5x = re.compile(r"(^|[^0-9.])5[倍xX]")

def rank(name):
    if is_3x.search(name): return 0
    if is_5x.search(name): return 1
    if not is_1x.search(name): return 2
    return 3

items = []
for idx, n in enumerate(d.get("all", [])):
    if any(b in n for b in bad): continue
    if not include_hk and "香港" in n: continue
    if not include_1x and is_1x.search(n): continue
    items.append((rank(n), idx, n))
items.sort(key=lambda x: (x[0], x[1]))
for _, _, n in items:
    print(n)
' "$INCLUDE_HK" "$INCLUDE_1X" 2>/dev/null
}

# ---- env for agy: needs desktop session so it can unlock gnome-keyring ----
setup_agy_env() {
  export HOME="${HOME:-/home/gryphon}"
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
  for p in $(api /providers/proxies | python3 -c 'import sys,json;print(" ".join(k for k in json.load(sys.stdin)["providers"].keys() if k!="default"))' 2>/dev/null); do
    printf 'refresh %s -> HTTP %s\n' "$p" "$(curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT -H "Authorization: Bearer $SECRET" "$API/providers/proxies/$p")"
  done
fi

if [ "$LIST" = 1 ]; then
  echo "AGY/[$GROUP] now = $(group_now)"; group_nodes; exit 0
fi

if [ "$VERIFY" = 1 ]; then
  echo "[$GROUP=$(group_now)] verify -> $(probe "$(group_now)")"; exit 0
fi

CANDIDATE_LIST=()
if [ -n "$NODES" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && CANDIDATE_LIST+=("$line")
  done < <(python3 -c 'import re,sys;print("\n".join(x for x in re.split(r"[,\s]+", sys.argv[1].strip()) if x))' "$NODES")
elif [ "$FULL" = 1 ] || [ -z "$DEFAULT_NODES" ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && CANDIDATE_LIST+=("$line")
  done < <(group_nodes)
else
  while IFS= read -r line; do
    [ -n "$line" ] && CANDIDATE_LIST+=("$line")
  done < <(python3 -c 'import re,sys;print("\n".join(x for x in re.split(r"[,\s]+", sys.argv[1].strip()) if x))' "$DEFAULT_NODES")
fi

[ "${#CANDIDATE_LIST[@]}" -gt 0 ] || { echo "ERR: no candidate nodes in group $GROUP" >&2; exit 1; }

echo "group=$GROUP  now=$(group_now)  timeout=${TIMEOUT}s"
echo "candidates (${#CANDIDATE_LIST[@]}, priority 3x -> 5x): ${CANDIDATE_LIST[*]}"
echo "------------------------------------------------------------------"
WINNER=""
for n in "${CANDIDATE_LIST[@]}"; do
  r="$(probe "$n")"
  printf '%-28s %s\n' "$n" "$r"
  if [ "$r" = "PONG" ] && [ -z "$WINNER" ]; then WINNER="$n"; fi
done
echo "------------------------------------------------------------------"
if [ -z "$WINNER" ]; then
  echo "❌ no Antigravity-compatible node found in the candidate set."
  echo "   -> try: $0 --refresh   /   add a residential-IP provider"
  exit 1
fi
if [ "$DRY" = 1 ]; then
  echo "✅ first working node: $WINNER (dry-run, not switching)"
else
  set_node "$WINNER" >/dev/null
  echo "✅ switched $GROUP -> $WINNER"
fi
