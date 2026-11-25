#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_file="${GPT_IMAGE_CONFIG:-${script_dir}/config.local.json}"
cli_bin="${GPT_IMAGE_2_SKILL_BIN:-/home/monci/.local/bin/gpt-image-2-skill}"
auth_file="/home/monci/.codex/auth.json"
auth_key="OPENAI_API_KEY"
prompt=""
out_file=""
size="1024x1024"
quality="high"
format="png"

usage() {
  cat <<'EOF'
Usage:
  generate-image.sh --prompt TEXT --out FILE [--size SIZE] [--quality QUALITY] [--format FORMAT]

Options:
  --prompt TEXT       Image prompt (required)
  --out FILE          Output image file (required)
  --size SIZE         e.g. 1024x1024, 2K, or 4K
  --quality QUALITY   low, medium, high, or auto
  --format FORMAT     png, jpeg, or webp
  --config FILE       Override the release CLI config file
  -h, --help          Show this help

Environment:
  GPT_IMAGE_2_SKILL_BIN  Override the release binary path
EOF
}

while (($#)); do
  case "$1" in
    --prompt) prompt="${2:?--prompt requires a value}"; shift 2 ;;
    --out) out_file="${2:?--out requires a value}"; shift 2 ;;
    --size) size="${2:?--size requires a value}"; shift 2 ;;
    --quality) quality="${2:?--quality requires a value}"; shift 2 ;;
    --format) format="${2:?--format requires a value}"; shift 2 ;;
    --config) config_file="${2:?--config requires a value}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$prompt" || -z "$out_file" ]]; then
  printf '%s\n' 'Error: --prompt and --out are required.' >&2
  usage >&2
  exit 2
fi

command -v jq >/dev/null || { printf '%s\n' 'Error: jq is required.' >&2; exit 1; }
[[ -x "$cli_bin" ]] || { printf 'Error: release CLI not executable: %s\n' "$cli_bin" >&2; exit 1; }
[[ -r "$config_file" ]] || { printf 'Error: config not readable: %s\n' "$config_file" >&2; exit 1; }
[[ -r "$auth_file" ]] || { printf 'Error: auth file not readable: %s\n' "$auth_file" >&2; exit 1; }

api_key="$(jq -er --arg key "$auth_key" '.[$key] // empty' "$auth_file")"
[[ -n "$api_key" ]] || { printf 'Error: auth key %s is missing.\n' "$auth_key" >&2; exit 1; }
export OPENAI_API_KEY="$api_key"

cli_args=(
  --json
  --config "$config_file"
  --provider codex-current
  images generate
  --model gpt-image-2
  --prompt "$prompt"
  --out "$out_file"
  --size "$size"
  --quality "$quality"
  --format "$format"
)

"$cli_bin" "${cli_args[@]}"
