#!/usr/bin/env bash
# Codex ChatGPT OAuth image generation wrapper.
# Keeps proxy, auth file, and model defaults in one place so the skill stays short.
set -euo pipefail

SKILL_DIR="${CODEX_IMAGE_SKILL_DIR:-$HOME/.codex/skills/gpt-image-2-skill}"
AUTH_FILE="${CODEX_AUTH_FILE:-$HOME/.codex/auth.json}"
MODEL="${CODEX_IMAGE_MODEL:-gpt-6-luna}"
PROXY="${CODEX_IMAGE_PROXY:-http://127.0.0.1:7890}"
WRAPPER="$SKILL_DIR/scripts/gpt_image_2_skill.cjs"

usage() {
    cat <<'EOF'
Usage:
  codex-image.sh generate --prompt "..." --out /path/out.png [--size WxH] [--quality low|medium|high]
  codex-image.sh edit --prompt "..." --ref-image /path/in.png --out /path/out.png [--ref-image ...]
  codex-image.sh doctor

Environment:
  CODEX_IMAGE_MODEL      Codex model, default gpt-6-luna (gpt-5.4 fails on Plus)
  CODEX_IMAGE_PROXY      Proxy for chatgpt.com, default http://127.0.0.1:7890
  CODEX_IMAGE_SKILL_DIR  gpt-image-2-skill directory
  CODEX_AUTH_FILE        Codex auth.json path
  CODEX_IMAGE_EVENTS=1   Print JSONL progress events to stderr
EOF
}

fail() {
    printf '{"error":{"code":"%s","message":"%s"}}\n' "$1" "$2"
    exit 1
}

enable_proxy() {
    export HTTPS_PROXY="$PROXY" HTTP_PROXY="$PROXY" https_proxy="$PROXY" http_proxy="$PROXY"
    export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}" no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"
}

check_runtime() {
    [[ -f "$WRAPPER" ]] || fail "runtime_missing" "gpt-image-2-skill not found at $WRAPPER"
    [[ -f "$AUTH_FILE" ]] || fail "auth_missing" "Codex auth file not found at $AUTH_FILE"
    command -v node >/dev/null 2>&1 || fail "node_missing" "node is required"
}

case "${1:-}" in
    generate|edit)
        subcommand="$1"
        shift
        check_runtime
        enable_proxy
        args=(--json --provider codex)
        [[ "${CODEX_IMAGE_EVENTS:-}" == "1" ]] && args+=(--json-events)
        args+=(images "$subcommand" -m "$MODEL" "$@")
        cd "$SKILL_DIR"
        exec node "$WRAPPER" "${args[@]}"
        ;;
    doctor)
        check_runtime
        enable_proxy
        cd "$SKILL_DIR"
        exec node "$WRAPPER" --json --provider codex doctor
        ;;
    help|-h|--help|"")
        usage
        ;;
    *)
        usage >&2
        fail "invalid_command" "unknown subcommand: $1"
        ;;
esac
