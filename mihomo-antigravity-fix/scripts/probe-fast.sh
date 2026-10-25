#!/usr/bin/env bash
# probe-fast.sh — fast Antigravity (agy) exit-node probe over plain HTTP.
#
# Why: a real `agy` run takes 9-30s and needs a desktop session; this probe
# reproduces Antigravity's per-connection location gate in ~1-4s per request
# and matches real-agy verdicts (calibrated 2026-10-15, see SKILL.md).
#
# Method (reverse-engineered from opencode-antigravity-auth verifyAccountAccess):
#   POST https://daily-cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse
#   body: {"model":"gemini-3-flash","request":{...one "ping" turn, maxOutputTokens:1}}
#   headers: OAuth bearer + Antigravity UA/X-Goog-Api-Client/Client-Metadata
#   No x-goog-user-project (consumer account has no quota project).
# Result: HTTP 200 = this exit IP passes the gate; 400 "location is not
# supported" = rejected; 429/other = noise; network error = node dead.
#
# Non-disruptive: probes run through local listener 127.0.0.1:7891 -> temporary
# group `LLM_SCAN` injected into config.yaml (same markers as scan-llm-agy.sh).
# The user's LLM group selection is untouched. Use `--teardown` to remove.
#
# Usage:
#   probe-fast.sh --node 印度-优化 --count 6     # probe one node, exit 0 if PASS
#   probe-fast.sh --nodes "a,b" --count 6        # probe several nodes
#   probe-fast.sh --teardown                     # remove temp group/listener
#   # sourced by scan-llm-agy.sh --fast: provides pf_* functions
#
# Verdict (count K, default 6): PASS if OK >= ceil(2K/3); early-stop when that
# bar is met or can no longer be met (LOCATION >= K-pass+1); single-shot NETERR
# on the first probe marks the node as dead (skip).
set -u

MIHOMO_DIR="${MIHOMO_DIR:-$HOME/.config/mihomo}"
CONFIG="$MIHOMO_DIR/config.yaml"
API="${MIHOMO_API:-http://127.0.0.1:9090}"
SCAN_PORT="${SCAN_PORT:-7891}"
OUT_DIR="${OUT_DIR:-/tmp/opencode}"
TOKEN_FILE="$OUT_DIR/agy_probe_token.txt"
TOKEN_META="$OUT_DIR/agy_probe_token.meta"
AGY_AUTH="${AGY_AUTH:-$HOME/.gemini/antigravity-cli/antigravity-oauth-token}"

# Public Antigravity OAuth client (from opencode-antigravity-auth / CLIProxyAPI).
PF_CID="1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com"
PF_CSE="${PF_CSE:-}"   # 公开的 Antigravity OAuth client secret 不入库，运行前 export PF_CSE

PF_EP="https://daily-cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse"
PF_BODY='{"model":"gemini-3-flash","request":{"model":"gemini-3-flash","contents":[{"role":"user","parts":[{"text":"ping"}]}],"generationConfig":{"maxOutputTokens":1,"temperature":0}}}'
PF_UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Antigravity/1.18.3 Chrome/138.0.7204.235 Electron/37.3.1 Safari/537.36"

MARK_BEGIN="# ==== TEMP-SCAN (scan-llm-agy.sh) ===="
MARK_END="# ==== /TEMP-SCAN ===="

pf_secret() { sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' "$CONFIG" | head -1; }

pf_reload() {
  curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT "$API/configs?force=true" \
    -H "Authorization: Bearer $(pf_secret)" -H 'Content-Type: application/json' -d '{"path":""}'
}

pf_config_edit() {  # $1=setup|teardown (same blocks as scan-llm-agy.sh)
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
        yaml.safe_load(t)
        p.write_text(t)
else:
    t = re.sub(rf"\n{re.escape(MB)}\nlisteners:\n(?:  .*\n)+{re.escape(ME)}\n", "\n", t)
    t = re.sub(rf"\n  {re.escape(MB)}\n(?:  .*\n)+  {re.escape(ME)}\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    yaml.safe_load(t)
    p.write_text(t)
PYEOF
  python3 -c "import yaml,sys;yaml.safe_load(open('$CONFIG'))" || { echo "ERR: YAML invalid after $1" >&2; return 1; }
}

pf_inject() {  # idempotent; reloads only when it actually changed something
  local before after
  before="$(grep -c "$MARK_BEGIN" "$CONFIG" || true)"
  pf_config_edit setup
  after="$(grep -c "$MARK_BEGIN" "$CONFIG" || true)"
  if [ "$before" != "$after" ]; then
    echo "setup: injected LLM_SCAN + listener $SCAN_PORT (reload -> HTTP $(pf_reload))"
  fi
}

pf_teardown() { pf_config_edit teardown && echo "teardown reload -> HTTP $(pf_reload)"; }

pf_set_node() {  # $1 = node name -> HTTP code
  curl -s --noproxy '*' -o /dev/null -w '%{http_code}' -X PUT \
    -H "Authorization: Bearer $(pf_secret)" -H 'Content-Type: application/json' \
    -d "$(python3 -c 'import json,sys;print(json.dumps({"name":sys.argv[1]}))' "$1")" \
    "$API/proxies/LLM_SCAN"
}

pf_ensure_token() {
  local now prev age rt resp tok
  now=$(date +%s)
  if [ -s "$TOKEN_FILE" ] && [ -f "$TOKEN_META" ]; then
    prev=$(sed -n 's/^saved_at=//p' "$TOKEN_META" | head -1)
    case "$prev" in ''|*[!0-9]*) prev=0 ;; esac
    age=$(( now - prev ))
    [ "$age" -lt 3000 ] && return 0   # <50 min: still valid (1h tokens)
  fi
  rt="$(python3 - "$AGY_AUTH" <<'PY' 2>/dev/null || true
import json,sys
print(json.load(open(sys.argv[1]))["token"]["refresh_token"])
PY
)"
  tok=""
  if [ -n "$rt" ]; then
    for P in 7890 "$SCAN_PORT"; do
      resp="$(curl -sS --noproxy '' -x "http://127.0.0.1:$P" -m 30 -X POST https://oauth2.googleapis.com/token \
        -d "client_id=$PF_CID" -d "client_secret=$PF_CSE" \
        -d "grant_type=refresh_token" -d "refresh_token=$rt" 2>/dev/null || true)"
      tok="$(python3 -c 'import json,sys;print(json.loads(sys.stdin.read() or "{}").get("access_token",""))' <<<"$resp" 2>/dev/null || true)"
      [ -n "$tok" ] && break
    done
  fi
  if [ -z "$tok" ]; then  # fallback: agy's own token if not expired yet
    tok="$(python3 - "$AGY_AUTH" <<'PY' 2>/dev/null || true
import json,sys,datetime
d=json.load(open(sys.argv[1]))["token"]
exp=datetime.datetime.fromisoformat(d["expiry"])
if exp > datetime.datetime.now(exp.tzinfo) + datetime.timedelta(seconds=60):
    print(d["access_token"])
PY
)"
  fi
  [ -n "$tok" ] || { echo "ERR: cannot obtain probe token (agy auth file + refresh both failed)" >&2; return 1; }
  printf '%s' "$tok" > "$TOKEN_FILE"
  printf 'saved_at=%s\n' "$now" > "$TOKEN_META"
}

pf_probe() {  # single request -> OK | LOCATION | NETERR | ERR:<code>:<msg>
  local raw code body msg
  raw=$(curl -sS --noproxy '' -x "http://127.0.0.1:$SCAN_PORT" -m 12 -w $'\n__CODE:%{http_code}' -X POST "$PF_EP" \
        -H "Authorization: Bearer $(cat "$TOKEN_FILE")" \
        -H "Content-Type: application/json" \
        -H "User-Agent: $PF_UA" \
        -H "X-Goog-Api-Client: google-cloud-sdk vscode_cloudshelleditor/0.1" \
        -H 'Client-Metadata: {"ideType":"ANTIGRAVITY","platform":"MACOS","pluginType":"GEMINI"}' \
        -d "$PF_BODY" 2>&1)
  code=$(grep -oE '__CODE:[0-9]+' <<<"$raw" | tail -1 | cut -d: -f2)
  body="${raw%$'\n'__CODE:*}"
  case "$code" in
    200) echo "OK"; return 0 ;;
    ""|000) echo "NETERR"; return 0 ;;
  esac
  if grep -q "location is not supported" <<<"$body"; then echo "LOCATION"; return 0; fi
  msg=$(python3 -c '
import sys,re
t=sys.stdin.read()
m=re.search(r"\"message\"\s*:\s*\"(.*?)\"", t, re.S)
print((m.group(1).replace("\\n"," ").replace("\n"," ")[:100]) if m else t[:100].replace(chr(10)," "))' <<<"$body" 2>/dev/null)
  echo "ERR:${code:-?}:$msg"
}

pf_probe_node() {  # $1=node $2=count ; prints "VERDICT ok/K detail avg_ms" ; exit-style return 0 pass
  local node="$1" K="${2:-6}" pass_at fail_at ok=0 loc=0 other=0 det="" attempts=0 t0 t1 ms=0 r
  pass_at=$(( (2*K + 2) / 3 )); fail_at=$(( K - pass_at + 1 ))
  pf_set_node "$node" >/dev/null
  while [ "$attempts" -lt "$K" ] && [ "$ok" -lt "$pass_at" ] && [ "$loc" -lt "$fail_at" ]; do
    attempts=$((attempts+1))
    t0=$(date +%s%N)
    r=$(pf_probe)
    t1=$(date +%s%N); ms=$(( ms + (t1-t0)/1000000 ))
    case "$r" in
      OK*)       ok=$((ok+1)); det+="P" ;;
      LOCATION*) loc=$((loc+1)); det+="L" ;;
      NETERR*)   other=$((other+1)); det+="N"; [ "$attempts" -eq 1 ] && break ;;
      *)         other=$((other+1)); det+="o" ;;
    esac
    sleep 0.3
  done
  [ "$ms" -gt 0 ] && [ "$attempts" -gt 0 ] && ms=$(( ms / attempts )) || ms=0
  if [ "$ok" -ge "$pass_at" ]; then
    printf 'PASS %d/%d %s %dms\n' "$ok" "$K" "$det" "$ms"
  else
    printf 'fail %d/%d %s %dms\n' "$ok" "$K" "$det" "$ms"
  fi
}

pf_main() {
  local count=6 nodes="" teardown_only=0 rc=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --node) shift; nodes+="${1:-}," ;;
      --nodes) shift; nodes+="${1:-}," ;;
      --count) shift; count="${1:-6}" ;;
      --teardown) teardown_only=1 ;;
      -h|--help) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; return 0 ;;
      *) echo "unknown arg: $1" >&2; return 2 ;;
    esac
    shift
  done
  if [ "$teardown_only" = 1 ]; then pf_teardown; return 0; fi
  [ -n "$nodes" ] || { echo "usage: probe-fast.sh --node NAME [--count K] | --teardown" >&2; return 2; }
  pf_inject || return 1
  pf_ensure_token || return 1
  IFS=',' read -r -a list <<<"${nodes%,}"
  for n in "${list[@]}"; do
    [ -n "$n" ] || continue
    local out; out="$(pf_probe_node "$n" "$count")"
    printf '%-20s %s\n' "$n" "$out"
    [[ "$out" == PASS* ]] || rc=1
  done
  return $rc
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  pf_main "$@"
fi
