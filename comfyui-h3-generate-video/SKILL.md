---
name: comfyui-h3-generate-video
description: |
  Use ONLY for local/remote ComfyUI MiniMax H3 video generation. Template-driven: submits a bundled API-format workflow (workflows/minimax-h3-ref2v.json, overridable with --workflow), discovers nodes by class_type, validates the graph before submitting, and accepts text prompts plus reference images (≤9), videos (≤3), and audios (≤3). Supports 9:16 or 16:9 (required), 3-15s, 480p/768p, 4-16 steps, Motion Context chains for consecutive child shots, UNET auto fallback (int8→fp8), and any ComfyUI base URL. Trigger on ComfyUI H3 video, local MiniMax H3, H3 ref2va, 480p/768p H3, 本地海螺视频, H3 分镜连续生成.
compatibility: Requires a reachable ComfyUI endpoint with MiniMax H3 nodes and ref2va models. Default endpoint https://vbzor1z91j009jw4-8188.sc02-webservice.gpuhome.cc:8443; override with --comfy-url (e.g. http://192.168.31.200:8188).
trigger-words: [ComfyUI H3生成视频, 本地 MiniMax H3, minimax-h3-ref2va, 480p H3, 768p H3, 本地海螺视频, H3 连续分镜, Motion Context]
---

# ComfyUI MiniMax H3 Video Generator (template-driven)

Use this skill when the user asks to generate a video with the **local** MiniMax
H3 ComfyUI interface. This skill is for actual rendering through a ComfyUI HTTP
endpoint — not cloud MiniMax API calls and not prompt-only consultation.

The entry point is `scripts/generate_video.py` in this skill directory. Copy the
whole skill directory to another machine, run Python through `uv` (or any
Python ≥ 3.11), and point `--comfy-url` at a compatible ComfyUI endpoint. The
script has zero third-party dependencies and no project-specific imports.

## How it works

1. Loads the bundled workflow template `workflows/minimax-h3-ref2v.json`
   (API format, 42 nodes, byte-identical to the verified export). `--workflow`
   accepts any structurally compatible template.
2. Resolves models against the server (`GET /object_info`): `--unet auto`
   prefers `minimax_h3_ref2va_pruned_int8_scaled.safetensors`, falls back to
   `minimax_h3_ref2va_pruned_fp8_scaled.safetensors`; missing CLIP/VAE/LoRA
   files are listed per file. If neither UNET exists, the script fails **before
   any `POST /prompt`**.
3. Uploads references, rewrites the template copy (node lookup by class_type —
   never hardcoded IDs), validates the graph (dangling links, slot
   continuity, output node), then submits and polls.

All reference media — images, videos, and audios — upload through
`POST /upload/image`. Core ComfyUI registers no `/upload/video` endpoint and
that endpoint performs no extension validation; this is the canonical path for
every media type.

## CLI

```bash
# Required: --prompt, --out, --aspect-ratio
uv run scripts/generate_video.py \
  --prompt "classic Chinese 2D ink-and-color animation, ..." \
  --out result.mp4 --aspect-ratio 9:16

# With references (order = slot order: Nth file -> API slot N-1)
uv run scripts/generate_video.py \
  --prompt "..." --out r.mp4 --aspect-ratio 16:9 \
  --ref-images first_frame.png character.png scene.png \
  --ref-videos motion_ref.mp4 --ref-audios ambience.mp3 \
  --duration 8 --resolution 768p --steps 8 --seed 12345

# Consecutive child shots (Motion Context chain), see contract below
uv run scripts/generate_video.py --prompt "..." --out r.mp4 --aspect-ratio 9:16 \
  --latent-path h3_context/proj_s01_v1 --save-index 2 --load-index 1

# Any endpoint
uv run scripts/generate_video.py ... --comfy-url http://192.168.31.200:8188
```

| Flag | Values | Notes |
| --- | --- | --- |
| `--aspect-ratio` | `9:16` / `16:9` | **required, no default** |
| `--duration` | 3-15 (default 5) | seconds; frame count computed server-side as 17n+5 @ 24fps |
| `--resolution` | `480p` / `768p` (default 768p) | maps to megapixels 0.4 / 0.9 |
| `--steps` | 4-16 (default 8) | BasicScheduler.steps |
| `--unet` | `auto` / `fp8` / `int8` (default auto) | auto = int8→fp8 fallback |
| `--ref-images/--ref-videos/--ref-audios` | lists, ≤9/≤3/≤3 | see contract below |
| `--save-index` | 0-256 (default 0) | Motion Context save clip_index |
| `--load-index` | 0-256, optional | omit = standalone; 0 = newest in chain; child S uses S-1 |
| `--latent-path` | string (default `h3_context/clip`) | stable per parent-shot chain |
| `--comfy-url` | any http(s) URL | default: env `COMFYUI_URL` or the bundled endpoint |
| `--workflow` | path | override the bundled template |
| `--poll-timeout` | seconds (default 3600) | |

## Reference-slot contract

The visible reference-loader names are one-based (`ref_img_1`–`ref_img_9`,
`ref_video_1`–`ref_video_3`, `ref_audio_1`–`ref_audio_3`); exported API fields
are zero-based (`ref_image_0`–`ref_image_8`, `ref_video_0`–`ref_video_2`,
`ref_audio_0`–`ref_audio_2`). In prompts, `@图片1` / `<Picture 1>` maps to API
slot `ref_image_0` — prompt numbering stays 1-based.

- Fill supplied references **consecutively from slot 0**; the Nth file passed
  on the command line lands in API slot N-1. Zero references is valid.
- Every unused slot: the loader node (and, for videos, its paired
  `GetVideoComponents`) is deleted and the main node's input key removed.
  The script refuses to submit graphs with dangling reference inputs.
- Upload order convention: first-frame image, character identity references,
  scene/environment references.
- Reference videos must be ≥ 5 frames; H3 expects 24fps, 2-15s clips.

## Motion Context chain contract (child shots)

For a parent shot split into consecutive child shots, use one stable
`--latent-path` for the whole chain and pass explicit indices. Sub-shots are
numbered `P_S` (pure digits, S starting at 1) in the caller's storyboard; the
mapping is mechanical:

| Sub-shot `P_S` | `--save-index` | `--load-index` |
| --- | --- | --- |
| `P_1` (chain head) | 1 | omit |
| `P_2` | 2 | 1 |
| `P_3` | 3 | 2 |
| `P_S` | S | S-1 |

- `--save-index 0` writes a new auto-numbered file every run; use 0 only for
  standalone shots that are not part of any chain. For chain members use
  explicit slots: save N overwrites its own reject instead of stacking files.
- `--load-index 0` loads the **newest** latent in the chain folder
  (not retry-safe); `--load-index N>0` loads exactly slot N. Chain-head
  `P_1` omits `--load-index` entirely.
- Omitting `--load-index` renders a standalone shot: the LoadLatent,
  MotionContext, and Trim nodes are **excluded from the submitted graph**
  (API format has no bypass — the frontend's Ctrl+B semantics are replicated:
  consumer links are re-routed through the removed nodes' matching-type
  inputs), nothing is loaded, and the shot still saves its own latent
  (always-on Save node). The Save slot file lands at
  `<latent-path>/clip_0000N.safetensors`; the load path is the
  `<latent-path>` directory.
- `clip_index` is an integer 0-256. Never use child-shot IDs, English labels,
  or gaps as index values.

## Submission and retrieval

1. `POST /prompt` with the validated graph; a 400 response surfaces the
   server's structured `node_errors` verbatim in the error message.
2. Poll `GET /history/{prompt_id}` until `status.status_str` is success or an
   explicit failure.
3. Find the first video in `outputs.videos` / `outputs.video` / `outputs.gifs`
   / `outputs.images` whose filename ends in `.mp4`, `.mov`, `.webm`, `.mkv`.
4. Download via `GET /view?filename=&subfolder=&type=` (URL-encoded). A failed
   download retries **only the GET** — the non-idempotent `/prompt` is never
   re-sent.

The script prints `prompt_id`, resolution, aspect, duration, steps, unet, and
seed; success requires the downloaded file to be non-empty.

## Prompt shaping for video generation (mandatory h3-prompt-writing route)

**This requirement applies only when generating video with this skill.** It
does not apply to image generation, audio generation, or other non-video
operations. For a video render with references (Ref2VA — any of
`--ref-images`, `--ref-videos`, `--ref-audios`), the prompt MUST be rewritten
with the **`h3-prompt-writing` skill**
(`ai-drama/backend/workspace/skills/h3-prompt-writing/`): read
`references/ref-en.txt` and produce the six-section Ref2VA format —
`subject_definitions`, `summary`, `retention_analysis`, `detailed_description`,
`overall_soundscape`, `non_diegetic_music`, in that order. For text-only or
keyframe modes, follow `references/base-en.txt`
(`integrated_multimodal_description` / `overall_soundscape` /
`non_diegetic_music`).

**Label ↔ slot mapping (verified against the H3 node source
`comfy_extras/nodes_minimax_h3.py` and `comfy/text_encoders/minimax.py`):**
prompt tags are **1-based per type and match CLI argument order** — the Nth
file of `--ref-images` is `<Picture N>`, the Nth file of `--ref-videos` is
`<Video N>`, the Nth file of `--ref-audios` is `<Audio N>`. The node builds
the presentation as `<Picture i>: <vision>` … `<Audio j>:` … `<Video k>:
<blocks>` in fixed order (images, then videos with each soundtrack's
`<Audio j>` emitted right before its `<Video k>`, then standalone audio), so
the tags in the prompt must match the order the files are passed on the CLI.
`<Video N>` and `<Audio N>` are numbered independently; a video's own
soundtrack is NOT automatically an `<Audio N>` unless the caller also passes
that audio file to `--ref-audios` and references it.

Begin text-only prompts with the Liaozhai/H3 visual lock when the project is a
Chinese 2D animation:

`classic Chinese 2D ink-and-color animation, Shanghai Animation Film Studio-inspired visual language, The Legend of Sealed Book-inspired theatrical fantasy, classic Chinese cel-animation coloring, crisp cel-shaded flat colors, hard-edged shadow shapes, limited two-tone shading, gongbi contour linework, flat mineral-pigment color planes, restrained xuan-paper texture, layered painted staging, theatrical folklore gestures, limited animation, readable silhouettes, no 3D render`

For Ref2VA rewrites, put the style lock inside the style-establishing
sentences before `[Shot 1]` (per the six-section format). Keep prompts free of
storyboard labels, arrows, panel borders, timing annotations, watermarks, and
subtitles unless the user explicitly requests them.

## Failure handling

- Missing H3 node or model file: the script stops before submitting and lists
  the missing paths. Fix the ComfyUI install; do not patch the graph ad hoc.
- `POST /prompt` 400: read the surfaced `node_errors` (missing inputs, dangling
  links, custom-node not installed) and correct the inputs/template.
- Identity drift: revise reference order and prompt markers, then rerender the
  affected shot; do not silently accept a mismatched clip.
- Download failure after successful execution: rerun with the same arguments —
  the script will re-poll history and retry only the download GET.

## Deliverable

Return the local output path and verification facts. For a multi-shot project,
render independent clips first, review them, then assemble with ffmpeg in
approved shot order. Do not add subtitles or BGM unless requested.
