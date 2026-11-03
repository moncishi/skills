#!/usr/bin/env bash
# scan-llm-agy.sh — scan mihomo AGY candidate nodes for Antigravity (agy) compatibility.
#
# Two probe engines:
#   * default : real `agy --print "PONG"` runs (ground truth, 9-30s per attempt)
#   * --fast  : HTTP probe via probe-fast.sh (1-5s per attempt); calibrated
#               2026-10-15 to match real-agy verdicts (see SKILL.md)
#
# Why: Antigravity rejects bad exit IPs, and feiniao/subscription node pools
# rotate daily. The AGY group's `filter` whitelist in config.yaml must be
# refreshed from real evidence (PASS = >=2/3 probe wins per node).
#
# How it stays non-disruptive: each worker uses its own temporary selector and
# local listener (7891-7898), so concurrent probes never race to change routes.
# The user's AGY group selection and normal traffic are untouched. Temp groups
# and listeners are removed when the scan finishes (unless --keep).
#
# Usage:
#   bash scan-llm-agy.sh                       # full scan, real agy (slow, ~1h)
#   bash scan-llm-agy.sh --fast                # full scan, HTTP probe (default 4-way parallel)
#   bash scan-llm-agy.sh --fast --jobs 4       # probe four isolated routes concurrently
#   bash scan-llm-agy.sh --fast --jobs 1       # serial fast scan
#   bash scan-llm-agy.sh --jobs 2             # opt in to concurrent real agy probes
#   bash scan-llm-agy.sh --fast --limit 5      # smoke test: first 5 candidates
#   bash scan-llm-agy.sh --fast --nodes a,b,c  # scan only these nodes
#   bash scan-llm-agy.sh --fast --verify 3     # agy spot-check first 3 PASS nodes
#   bash scan-llm-agy.sh --probe-count 8       # fast mode: probes per node (default 6)
#   bash scan-llm-agy.sh --keep                # keep temporary groups/listeners after scan
# Output: /tmp/opencode/agy_scan_<ts>.tsv + .log ; final PASS list + filter regex.
set -u

MIHOMO_DIR="${MIHOMO_DIR:-$HOME/.config/mihomo}"
CONFIG="$MIHOMO_DIR/config.yaml"
API="${MIHOMO_API:-http://127.0.0.1:9090}"
SCAN_PORT=7891
OUT_DIR="${OUT_DIR:-/tmp/opencode}"
LOCK_FILE="${SCAN_LOCK_FILE:-/tmp/opencode/agy_scan.lock}"
AGY="${AGY:-$HOME/.local/bin/agy}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIMIT=0; KEEP=0; FAST=0; PROBE_COUNT=6; NODES_ARG=""; VERIFY=0; JOBS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --limit) shift; LIMIT="${1:-0}" ;;
    --keep) KEEP=1 ;;
    --fast) FAST=1 ;;
    --probe-count) shift; PROBE_COUNT="${1:-6}" ;;
    --nodes) shift; NODES_ARG="${1:-}" ;;
    --verify) shift; VERIFY="${1:-0}" ;;
    --jobs) shift; JOBS="${1:-}" ;;
    -h|--help) sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$JOBS" ]; then
  if [ "$FAST" = 1 ]; then JOBS=4; else JOBS=1; fi
fi
case "$JOBS" in ''|*[!0-9]*) echo "ERR: --jobs must be an integer from 1 to 8" >&2; exit 2 ;; esac
[ "$JOBS" -ge 1 ] && [ "$JOBS" -le 8 ] || { echo "ERR: --jobs must be between 1 and 8" >&2; exit 2; }

SECRET="$(sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' "$CONFIG" | head -1)"
[ -n "$SECRET" ] || { echo "ERR: cannot read secret from $CONFIG" >&2; exit 1; }
if [ "$FAST" = 0 ]; then
  [ -x "$AGY" ] || { echo "ERR: agy not found ($AGY)" >&2; exit 1; }
fi
mkdir -p "$OUT_DIR"
mkdir -p "$(dirname "$LOCK_FILE")"
exec 9>"$LOCK_FILE"
flock -n 9 || { echo "ERR: another agy scan/probe is using the temporary mihomo groups" >&2; exit 1; }

export DISPLAY="${DISPLAY:-:1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

api() { curl -s --noproxy '*' -H "Authorization: Bearer $SECRET" "$@"; }
reload() { curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT "$API/configs?force=true" \
  -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' -d '{"path":""}'; }

# Share the config-edit and fast-probe helpers with the standalone probe command.
[ -f "$SCRIPT_DIR/probe-fast.sh" ] || { echo "ERR: $SCRIPT_DIR/probe-fast.sh missing" >&2; exit 1; }
# shellcheck source=probe-fast.sh
source "$SCRIPT_DIR/probe-fast.sh"

set_node() { pf_set_node "$1" "${2:-LLM_SCAN}"; }

probe_once() {  # $1=port $2=worker; real agy through isolated scan listener -> P|L|X|A|O
  local port="${1:-$SCAN_PORT}" worker="${2:-1}"
  local out
  out="$(env http_proxy="http://127.0.0.1:$port" https_proxy="http://127.0.0.1:$port" \
        all_proxy="http://127.0.0.1:$port" no_proxy='127.0.0.1,localhost,::1' NO_PROXY='127.0.0.1,localhost,::1' \
        timeout 60 "$AGY" --print "reply with exactly PONG" --log-file "$OUT_DIR/agy_probe_${TS}_w${worker}.log" 2>&1 | tr -d '\r')"
  if grep -q "PONG" <<<"$out"; then printf 'P'
  elif grep -q "location is not supported" <<<"$out"; then printf 'L'
  elif grep -q "proxyconnect" <<<"$out"; then printf 'X'
  elif grep -qE "not logged into|UNAUTHENTICATED" <<<"$out"; then printf 'A'
  else printf 'O'; fi
}

TS=$(date +%Y%m%d_%H%M%S)
TSV="$OUT_DIR/agy_scan_$TS.tsv"; LOG="$OUT_DIR/agy_scan_$TS.log"
WORK_DIR="$(mktemp -d "$OUT_DIR/agy_scan_${TS}.work.XXXXXX")"
umask 077
worker_cleanup() {
  if [ -n "${WORK_DIR:-}" ] && [ -d "$WORK_DIR" ]; then rm -rf -- "$WORK_DIR"; fi
}
cp -a "$CONFIG" "$WORK_DIR/config.before.yaml" || { echo "ERR: cannot snapshot mihomo config; refusing to scan" >&2; worker_cleanup; exit 1; }
CONFIG_HASH_BEFORE="$(sha256sum "$CONFIG" | awk '{print $1}')"
PRIOR_SCAN_NODE="$(api "$API/proxies/LLM_SCAN" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("now", ""))' 2>/dev/null || true)"

teardown() {
  if [ "$KEEP" = 1 ]; then
    echo "(--keep) isolated temp groups/listeners left in place"
  else
    local current_hash reload_status restore_tmp
    current_hash="$(sha256sum "$CONFIG" | awk '{print $1}')"
    if [ "$current_hash" != "$CONFIG_HASH_BEFORE" ]; then
      restore_tmp="$CONFIG.restore.$$"
      if cp -a "$WORK_DIR/config.before.yaml" "$restore_tmp" && mv -f -- "$restore_tmp" "$CONFIG"; then
        reload_status="$(pf_reload)"
        echo "teardown restored original config -> HTTP $reload_status"
        if [ -n "$PRIOR_SCAN_NODE" ]; then
          echo "teardown restored previous LLM_SCAN selection -> HTTP $(pf_set_node "$PRIOR_SCAN_NODE" LLM_SCAN)"
        fi
      else
        echo "ERR: could not restore config; secure backup retained at $WORK_DIR/config.before.yaml" >&2
        WORK_DIR=""
      fi
    fi
  fi
  worker_cleanup
}
trap teardown EXIT

echo "setup: inject $JOBS isolated temp groups/listeners ..."
setup_status="$(pf_config_edit setup "$JOBS")" || { echo "ERR: cannot configure scan listeners" >&2; exit 1; }
if [ "$setup_status" = changed ]; then
  setup_http="$(pf_reload)"
  echo "setup reload -> HTTP $setup_http"
  [ "$setup_http" = 204 ] || { echo "ERR: mihomo did not accept temporary scan config" >&2; exit 1; }
fi
sleep 1

if [ -n "$NODES_ARG" ]; then
  candidates="$(tr ',' '\n' <<<"$NODES_ARG")"
else
  candidates="$(api "$API/providers/proxies" | python3 -c '
import sys,json
d=json.load(sys.stdin)["providers"]
bad=("剩余流量","套餐到期","过滤掉","电报群","防失联","每次使用前","有超过","官网")
seen=[]
for prov in ("bjnet2","feiniao","subscription"):
    for n in d.get(prov,{}).get("proxies",[]):
        name=n.get("name","")
        if any(b in name for b in bad): continue
        if name in seen: continue
        seen.append(name)
print("\n".join(seen))')"
fi
if [ "$LIMIT" -gt 0 ]; then candidates="$(head -n "$LIMIT" <<<"$candidates")"; fi
total=$(grep -c . <<<"$candidates")
[ "$total" -gt 0 ] || { echo "ERR: no candidate nodes to scan" >&2; exit 1; }

if [ "$FAST" = 1 ]; then
  pf_ensure_token || { echo "ERR: cannot obtain probe token (agy auth + refresh failed)" >&2; exit 1; }
else
  # self-test the listener on a real node before scanning
  first_node="$(head -n 1 <<<"$candidates")"
  set_node "$first_node" LLM_SCAN >/dev/null
  sleep 0.5
  curl -s --noproxy '' -x "http://127.0.0.1:$SCAN_PORT" -o /dev/null -w "listener $SCAN_PORT self-test ($first_node) -> HTTP %{http_code}\n" -m 10 https://www.gstatic.com/generate_204
fi
printf 'node\tattempts\tpong\tlocation\tother\tdetail\n' > "$TSV"
if [ "$FAST" = 1 ]; then
  pass_at=$(( (2*PROBE_COUNT + 2) / 3 )); fail_at=$(( PROBE_COUNT - pass_at + 1 ))
  printf 'scan start %s | mode=fast | jobs=%d | total=%d candidates | probes<=%d | pass>=%d OK\n' \
    "$(date '+%F %T')" "$JOBS" "$total" "$PROBE_COUNT" "$pass_at" >> "$LOG"
else
  printf 'scan start %s | mode=agy | jobs=%d | total=%d candidates\n' "$(date '+%F %T')" "$JOBS" "$total" >> "$LOG"
fi

for ((w=1; w<=JOBS; w++)); do : > "$WORK_DIR/queue_$w.tsv"; : > "$WORK_DIR/result_$w.tsv"; done
candidate_index=0
while IFS= read -r node; do
  [ -n "$node" ] || continue
  candidate_index=$((candidate_index+1))
  worker=$(( (candidate_index - 1) % JOBS + 1 ))
  printf '%d\t%s\n' "$candidate_index" "$node" >> "$WORK_DIR/queue_$worker.tsv"
done <<<"$candidates"

scan_worker() {
  local worker="$1" group port index node code t0 dt attempts ok pong loc other detail r verdict
  local auth_streak=0
  group="LLM_SCAN"; [ "$worker" -gt 1 ] && group="LLM_SCAN_$worker"
  port=$((7890 + worker))
  while IFS=$'\t' read -r index node; do
    [ -n "${node:-}" ] || continue
    [ -e "$WORK_DIR/abort-auth" ] && break
    t0=$(date +%s)
    code=$(set_node "$node" "$group")
    if [ "$code" != "204" ]; then
      printf '%s\t%s\t0\t0\t0\t0\tsetfail-%s\n' "$index" "$node" "$code" >> "$WORK_DIR/result_$worker.tsv"
      printf '[%s/%s] %-16s SETFAIL(%s)\n' "$index" "$total" "$node" "$code" | tee -a "$LOG"
      continue
    fi
    sleep 0.3

    if [ "$FAST" = 1 ]; then
      attempts=0; ok=0; loc=0; other=0; detail=""
      while [ "$attempts" -lt "$PROBE_COUNT" ] && [ "$ok" -lt "$pass_at" ] && [ "$loc" -lt "$fail_at" ]; do
        attempts=$((attempts+1))
        r="$(pf_probe "$port")"
        case "$r" in
          OK*)       ok=$((ok+1)); detail+="P" ;;
          LOCATION*) loc=$((loc+1)); detail+="L" ;;
          NETERR*)   other=$((other+1)); detail+="N"
                     if [ "$attempts" -eq 1 ]; then break; fi ;;
          *)         other=$((other+1)); detail+="o" ;;
        esac
        sleep 0.3
      done
      dt=$(( $(date +%s) - t0 ))
      if [ "$ok" -ge "$pass_at" ]; then verdict="PASS"; else verdict="fail"; fi
      printf '%s\t%s\t%d\t%d\t%d\t%d\t%s\n' "$index" "$node" "$attempts" "$ok" "$loc" "$other" "$detail" >> "$WORK_DIR/result_$worker.tsv"
      printf '[%s/%s] %-16s %-4s %-5s (%ss)\n' "$index" "$total" "$node" "$verdict" "$detail" "$dt" | tee -a "$LOG"
      continue
    fi

    attempts=0; pong=0; loc=0; other=0; detail=""
    while [ "$attempts" -lt 3 ] && [ "$pong" -lt 2 ]; do
      attempts=$((attempts+1))
      r="$(probe_once "$port" "$worker")"
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
    printf '%s\t%s\t%d\t%d\t%d\t%d\t%s\n' "$index" "$node" "$attempts" "$pong" "$loc" "$other" "$detail" >> "$WORK_DIR/result_$worker.tsv"
    printf '[%s/%s] %-16s %-4s %-5s (%ss)\n' "$index" "$total" "$node" "$verdict" "$detail" "$dt" | tee -a "$LOG"

    if [ "$verdict" = "fail" ] && [ "$detail" = "AAA" ]; then auth_streak=$((auth_streak+1)); else auth_streak=0; fi
    if [ "$auth_streak" -ge 3 ]; then
      : > "$WORK_DIR/abort-auth"
      printf 'worker %s ABORT: 3 consecutive auth failures (AAA) at %s\n' "$worker" "$(date '+%F %T')" | tee -a "$LOG"
      break
    fi
  done < "$WORK_DIR/queue_$worker.tsv"
}

pids=()
for ((w=1; w<=JOBS; w++)); do scan_worker "$w" & pids+=("$!"); done
worker_failed=0
for pid in "${pids[@]}"; do wait "$pid" || worker_failed=1; done
if [ "$worker_failed" -ne 0 ]; then echo "ERR: one or more scan workers failed" >&2; fi
sort -n -k1,1 "$WORK_DIR"/result_*.tsv | awk -F'\t' 'BEGIN{OFS="\t"} NF>=7 {print $2,$3,$4,$5,$6,$7}' >> "$TSV"
i=$(awk 'END{print NR-1}' "$TSV")

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
printf '\nAGY filter regex (paste into config.yaml after review):\n%s\n' "$regex" | tee -a "$LOG"
echo "(temp group/listener will be removed by teardown)"
[ "$worker_failed" -eq 0 ] || exit 1
