#!/usr/bin/env bash
# scan-llm-agy.sh — scan mihomo LLM candidate nodes for Antigravity (agy) compatibility.
#
# Two probe engines:
#   * default : real `agy --print "PONG"` runs (ground truth, 9-30s per attempt)
#   * --fast  : HTTP probe via probe-fast.sh (1-5s per attempt); calibrated
#               2026-10-15 to match real-agy verdicts (see SKILL.md)
#
# Why: Antigravity rejects bad exit IPs, and feiniao/subscription node pools
# rotate daily. The LLM group's `filter` whitelist in config.yaml must be
# refreshed from real evidence (PASS = >=2/3 probe wins per node).
#
# How it stays non-disruptive: the scan routes probes through a dedicated local
# listener 127.0.0.1:7891 -> temporary group `LLM_SCAN`, so the user's LLM group
# selection and normal traffic are untouched. Temp group/listener are removed
# when the scan finishes (unless --keep).
#
# Usage:
#   bash scan-llm-agy.sh                       # full scan, real agy (slow, ~1h)
#   bash scan-llm-agy.sh --fast                # full scan, HTTP probe (~10 min)
#   bash scan-llm-agy.sh --fast --limit 5      # smoke test: first 5 candidates
#   bash scan-llm-agy.sh --fast --nodes a,b,c  # scan only these nodes
#   bash scan-llm-agy.sh --fast --verify 3     # agy spot-check first 3 PASS nodes
#   bash scan-llm-agy.sh --probe-count 8       # fast mode: probes per node (default 6)
#   bash scan-llm-agy.sh --keep                # keep temp group/listener after scan
# Output: /tmp/opencode/agy_scan_<ts>.tsv + .log ; final PASS list + filter regex.
set -u

MIHOMO_DIR="${MIHOMO_DIR:-$HOME/.config/mihomo}"
CONFIG="$MIHOMO_DIR/config.yaml"
API="${MIHOMO_API:-http://127.0.0.1:9090}"
SCAN_PORT=7891
OUT_DIR="${OUT_DIR:-/tmp/opencode}"
AGY="${AGY:-$HOME/.local/bin/agy}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT=0; KEEP=0; FAST=0; PROBE_COUNT=6; NODES_ARG=""; VERIFY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --limit) shift; LIMIT="${1:-0}" ;;
    --keep) KEEP=1 ;;
    --fast) FAST=1 ;;
    --probe-count) shift; PROBE_COUNT="${1:-6}" ;;
    --nodes) shift; NODES_ARG="${1:-}" ;;
    --verify) shift; VERIFY="${1:-0}" ;;
    -h|--help) sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

SECRET="$(sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' "$CONFIG" | head -1)"
[ -n "$SECRET" ] || { echo "ERR: cannot read secret from $CONFIG" >&2; exit 1; }
if [ "$FAST" = 0 ]; then
  [ -x "$AGY" ] || { echo "ERR: agy not found ($AGY)" >&2; exit 1; }
fi
mkdir -p "$OUT_DIR"

export DISPLAY="${DISPLAY:-:1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

api() { curl -s --noproxy '*' -H "Authorization: Bearer $SECRET" "$@"; }
reload() { curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT "$API/configs?force=true" \
  -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' -d '{"path":""}'; }

# fast probe engine (pf_* functions + token management)
if [ "$FAST" = 1 ]; then
  [ -f "$SCRIPT_DIR/probe-fast.sh" ] || { echo "ERR: $SCRIPT_DIR/probe-fast.sh missing" >&2; exit 1; }
  # shellcheck source=probe-fast.sh
  source "$SCRIPT_DIR/probe-fast.sh"
fi

MARK_BEGIN="# ==== TEMP-SCAN (scan-llm-agy.sh) ===="
MARK_END="# ==== /TEMP-SCAN ===="

config_edit() {  # $1=setup|teardown
  python3 - "$CONFIG" "$1" <<'PYEOF'
import pathlib, re, sys, yaml
p = pathlib.Path(sys.argv[1]); mode = sys.argv[2]
t = p.read_text()
MB, ME = "# ==== TEMP-SCAN (scan-llm-agy.sh) ====", "# ==== /TEMP-SCAN ===="
if mode == "setup":
    if MB not in t:
        lb = f"\n{MB}\nlisteners:\n  - name: scan-in\n    type: mixed\n    listen: 127.0.0.1\n    port: 7891\n    proxy: LLM_SCAN\n{ME}\n"
        anchor = "tcp-concurrent: true\n"
        assert anchor in t, "anchor tcp-concurrent not found"
        t = t.replace(anchor, anchor + lb, 1)
        gb = f"\n  {MB}\n  # LLM_SCAN: temporary group for agy compatibility scans\n  - name: LLM_SCAN\n    type: select\n    use:\n      - feiniao\n      - subscription\n  {ME}\n"
        anchor2 = "\n  - name: AUTO\n"
        assert anchor2 in t, "anchor AUTO group not found"
        t = t.replace(anchor2, gb + anchor2, 1)
        yaml.safe_load(t)  # never write an invalid config
        p.write_text(t)
else:
    t = re.sub(rf"\n{re.escape(MB)}\nlisteners:\n(?:  .*\n)+{re.escape(ME)}\n", "\n", t)
    t = re.sub(rf"\n  {re.escape(MB)}\n(?:  .*\n)+  {re.escape(ME)}\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    yaml.safe_load(t)  # never write an invalid config
    p.write_text(t)
PYEOF
  python3 -c "import yaml,sys;yaml.safe_load(open('$CONFIG'))" || { echo "ERR: YAML invalid after $1" >&2; exit 1; }
}

set_node() {
  curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT \
    -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' \
    -d "{\"name\":\"$1\"}" "$API/proxies/LLM_SCAN"
}

probe_once() {  # real agy through the scan listener -> P|L|X|A|O
  local out
  out="$(env http_proxy="http://127.0.0.1:$SCAN_PORT" https_proxy="http://127.0.0.1:$SCAN_PORT" \
        all_proxy="http://127.0.0.1:$SCAN_PORT" no_proxy='127.0.0.1,localhost,::1' NO_PROXY='127.0.0.1,localhost,::1' \
        timeout 60 "$AGY" --print "reply with exactly PONG" --log-file "$OUT_DIR/agy_probe.log" 2>&1 | tr -d '\r')"
  if grep -q "PONG" <<<"$out"; then printf 'P'
  elif grep -q "location is not supported" <<<"$out"; then printf 'L'
  elif grep -q "proxyconnect" <<<"$out"; then printf 'X'
  elif grep -qE "not logged into|UNAUTHENTICATED" <<<"$out"; then printf 'A'
  else printf 'O'; fi
}

teardown() {
  if [ "$KEEP" = 1 ]; then
    echo "(--keep) temp group LLM_SCAN + port $SCAN_PORT left in place"
  else
    config_edit teardown
    echo "teardown reload -> HTTP $(reload)"
  fi
}
trap teardown EXIT

echo "setup: inject temp group + listener ..."
config_edit setup
echo "setup reload -> HTTP $(reload)"
sleep 1

if [ -n "$NODES_ARG" ]; then
  candidates="$(tr ',' '\n' <<<"$NODES_ARG")"
else
  candidates="$(api "$API/providers/proxies" | python3 -c '
import sys,json
d=json.load(sys.stdin)["providers"]
bad=("剩余流量","套餐到期","过滤掉","电报群","防失联","每次使用前","有超过","官网")
seen=[]
for prov in ("feiniao","subscription"):
    for n in d.get(prov,{}).get("proxies",[]):
        name=n.get("name","")
        if any(b in name for b in bad): continue
        if name in seen: continue
        seen.append(name)
print("\n".join(seen))')"
fi
if [ "$LIMIT" -gt 0 ]; then candidates="$(head -n "$LIMIT" <<<"$candidates")"; fi
total=$(grep -c . <<<"$candidates")

if [ "$FAST" = 1 ]; then
  pf_ensure_token || { echo "ERR: cannot obtain probe token (agy auth + refresh failed)" >&2; exit 1; }
else
  # self-test the listener on a real node before scanning
  first_node="$(head -n 1 <<<"$candidates")"
  set_node "$first_node" >/dev/null
  sleep 0.5
  curl -s --noproxy '' -x "http://127.0.0.1:$SCAN_PORT" -o /dev/null -w "listener $SCAN_PORT self-test ($first_node) -> HTTP %{http_code}\n" -m 10 https://www.gstatic.com/generate_204
fi
i=0

TS=$(date +%Y%m%d_%H%M%S)
TSV="$OUT_DIR/agy_scan_$TS.tsv"; LOG="$OUT_DIR/agy_scan_$TS.log"
printf 'node\tattempts\tpong\tlocation\tother\tdetail\n' > "$TSV"
if [ "$FAST" = 1 ]; then
  pass_at=$(( (2*PROBE_COUNT + 2) / 3 )); fail_at=$(( PROBE_COUNT - pass_at + 1 ))
  printf 'scan start %s | mode=fast | total=%d candidates | probes<=%d | pass>=%d OK\n' \
    "$(date '+%F %T')" "$total" "$PROBE_COUNT" "$pass_at" >> "$LOG"
else
  printf 'scan start %s | mode=agy | total=%d candidates\n' "$(date '+%F %T')" "$total" >> "$LOG"
fi

auth_streak=0
while IFS= read -r node; do
  [ -n "$node" ] || continue
  i=$((i+1))
  t0=$(date +%s)
  code=$(set_node "$node")
  if [ "$code" != "204" ]; then
    printf '%s\t0\t0\t0\t0\tsetfail-%s\n' "$node" "$code" >> "$TSV"
    printf '[%d/%d] %-16s SETFAIL(%s)\n' "$i" "$total" "$node" "$code" | tee -a "$LOG"
    continue
  fi
  sleep 0.3

  if [ "$FAST" = 1 ]; then
    attempts=0; ok=0; loc=0; other=0; detail=""
    while [ "$attempts" -lt "$PROBE_COUNT" ] && [ "$ok" -lt "$pass_at" ] && [ "$loc" -lt "$fail_at" ]; do
      attempts=$((attempts+1))
      r="$(pf_probe)"
      case "$r" in
        OK*)       ok=$((ok+1)); detail+="P" ;;
        LOCATION*) loc=$((loc+1)); detail+="L" ;;
        NETERR*)   other=$((other+1)); detail+="N"
                   if [ "$attempts" -eq 1 ]; then break; fi ;;   # node unreachable: no point retrying
        *)         other=$((other+1)); detail+="o" ;;
      esac
      sleep 0.3
    done
    dt=$(( $(date +%s) - t0 ))
    if [ "$ok" -ge "$pass_at" ]; then verdict="PASS"; else verdict="fail"; fi
    printf '%s\t%d\t%d\t%d\t%d\t%s\n' "$node" "$attempts" "$ok" "$loc" "$other" "$detail" >> "$TSV"
    printf '[%d/%d] %-16s %-4s %-5s %s\n' "$i" "$total" "$node" "$verdict" "$detail" "(${dt}s)" | tee -a "$LOG"
    continue
  fi

  attempts=0; pong=0; loc=0; other=0; detail=""
  while [ "$attempts" -lt 3 ] && [ "$pong" -lt 2 ]; do
    attempts=$((attempts+1))
    r="$(probe_once)"
    case "$r" in
      P) pong=$((pong+1)); detail+="P" ;;
      L) loc=$((loc+1)); detail+="L" ;;
      X) other=$((other+1)); detail+="X" ;;
      A) other=$((other+1)); detail+="A" ;;
      *) other=$((other+1)); detail+="O" ;;
    esac
  done
  dt=$(( $(date +%s) - t0 ))
  if [ "$pong" -ge 2 ]; then verdict="PASS"; else verdict="fail"; fi
  printf '%s\t%d\t%d\t%d\t%d\t%s\n' "$node" "$attempts" "$pong" "$loc" "$other" "$detail" >> "$TSV"
  printf '[%d/%d] %-16s %-4s %-5s %s\n' "$i" "$total" "$node" "$verdict" "$detail" "(${dt}s)" | tee -a "$LOG"

  if [ "$verdict" = "fail" ] && [ "$detail" = "AAA" ]; then auth_streak=$((auth_streak+1)); else auth_streak=0; fi
  if [ "$auth_streak" -ge 3 ]; then
    printf 'ABORT: 3 consecutive auth failures (AAA) at %s\n' "$(date '+%F %T')" | tee -a "$LOG"
    break
  fi
done <<<"$candidates"

if [ "$FAST" = 1 ]; then PT="$pass_at"; else PT=2; fi
pass_rows="$(awk -F'\t' -v pt="$PT" 'NR>1 && +$3>=pt {print $1}' "$TSV")"
pcnt=$(awk -F'\t' -v pt="$PT" 'NR>1 && +$3>=pt' "$TSV" | wc -l)
printf '\n===== DONE %s =====\nPASS (%d/%d):\n%s\nTSV: %s\n' \
  "$(date '+%F %T')" "$pcnt" "$i" "$pass_rows" "$TSV" | tee -a "$LOG"

# optional: anchor fast-mode results with real agy spot checks
if [ "$FAST" = 1 ] && [ "$VERIFY" -gt 0 ] && [ -x "$AGY" ]; then
  printf 'agy spot-verify (first %d PASS nodes):\n' "$VERIFY" | tee -a "$LOG"
  n=0
  while IFS= read -r node; do
    [ -n "$node" ] || continue
    n=$((n+1)); [ "$n" -gt "$VERIFY" ] && break
    set_node "$node" >/dev/null; sleep 0.5
    r="$(probe_once)"
    case "$r" in P) v="PONG ✓";; L) v="LOCATION";; *) v="OTHER($r)";; esac
    printf '  %-16s %s\n' "$node" "$v" | tee -a "$LOG"
  done <<<"$pass_rows"
fi

regex="^($(echo "$pass_rows" | paste -sd'|'))\$"
printf '\nLLM filter regex (paste into config.yaml after review):\n%s\n' "$regex" | tee -a "$LOG"
echo "(temp group/listener will be removed by teardown)"
