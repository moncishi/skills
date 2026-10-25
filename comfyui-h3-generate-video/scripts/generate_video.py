#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Generate one local MiniMax H3 video through the ComfyUI HTTP API.

Template-driven: loads a bundled API-format workflow JSON, locates nodes by
class_type (+ _meta.title where needed), transforms a deep copy, validates the
graph, then submits. Supports image/video/audio references (9/3/3), Motion
Context chains (save-index/load-index), UNET auto fallback (int8->fp8),
9:16/16:9, 3-15s, 480p/768p, and any ComfyUI base URL.

Examples:
  uv run generate_video.py --prompt "..." --out result.mp4 --aspect-ratio 9:16
  uv run generate_video.py --prompt "..." --out r.mp4 --aspect-ratio 16:9 \
      --ref-images a.png b.png --ref-videos clip.mp4 --duration 8
  uv run generate_video.py --prompt "..." --out r.mp4 --aspect-ratio 9:16 \
      --latent-path h3_context/proj_s01_v1 --save-index 2 --load-index 1
"""

from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Final

DEFAULT_COMFY_URL: Final[str] = "https://vbzor1z91j009jw4-8188.sc02-webservice.gpuhome.cc:8443"
DEFAULT_LATENT_PATH: Final[str] = "h3_context/clip"
UNET_INT8: Final[str] = "minimax_h3_ref2va_pruned_int8_scaled.safetensors"
UNET_FP8: Final[str] = "minimax_h3_ref2va_pruned_fp8_scaled.safetensors"
UNET_INT8_CONVROT: Final[str] = "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
UNET_NVFP4: Final[str] = "minimax_h3_ref2va_pruned_nvfp4.safetensors"
ASPECT_9_16: Final[str] = "9:16 (Portrait Widescreen)"

FPS: Final[int] = 24
FRAME_STEP: Final[int] = 17
FRAME_OFFSET: Final[int] = 5
MIN_DURATION: Final[int] = 3
MAX_DURATION: Final[int] = 15
MIN_STEPS: Final[int] = 4
MAX_STEPS: Final[int] = 16
MAX_CLIP_INDEX: Final[int] = 256
SUPPORTED_RESOLUTIONS: Final[frozenset[str]] = frozenset({"480p", "768p"})
MEGAPIXELS: Final[dict[str, float]] = {"480p": 0.4, "768p": 0.9}
VIDEO_SUFFIXES: Final[frozenset[str]] = frozenset({".mp4", ".mov", ".webm", ".mkv"})

REQUIRED_CLASS_TYPES: Final[frozenset[str]] = frozenset({
    "MiniMaxH3ReferenceToVideo",
    "ResolutionSelector",
    "PrimitiveFloat",
    "PrimitiveStringMultiline",
    "BasicScheduler",
    "RandomNoise",
    "UNETLoader",
    "CLIPLoader",
    "VAELoader",
    "LoraLoaderModelOnly",
    "MiniMaxH3MotionContextLoadLatent",
    "MiniMaxH3MotionContext",
    "MiniMaxH3MotionContextSaveLatent",
    "MiniMaxH3MotionContextTrim",
    "SaveVideo",
    "LoadImage",
    "LoadVideo",
    "LoadAudio",
    "GetVideoComponents",
})

PROMPT_TITLE: Final[str] = "Input Text (Prompt)"
DURATION_TITLE: Final[str] = "Duration in Seconds"
RESOLUTION_TITLE: Final[str] = "aspect_select"

REF_GROUPS: Final[tuple[dict[str, Any], ...]] = (
    {"prefix": "ref_images", "field": "ref_image", "loader_field": "image", "limit": 9, "kind": "image"},
    {"prefix": "ref_videos", "field": "ref_video", "loader_field": "file", "limit": 3, "kind": "video"},
    {"prefix": "ref_audios", "field": "ref_audio", "loader_field": "audio", "limit": 3, "kind": "audio"},
)


class GenerationError(RuntimeError):
    """Raised when ComfyUI cannot accept or complete the requested render."""


# ---------------------------------------------------------------- HTTP layer
# Thin wrappers so tests can monkeypatch http_get/http_post (injectable transport).

def http_get(url: str, timeout: int = 300) -> bytes:
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def http_post(url: str, data: bytes, content_type: str, timeout: int = 300) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=data, headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def http_post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    status, body = http_post(url, json.dumps(payload).encode(), "application/json")
    try:
        decoded = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        decoded = None
    if status != 200 or not isinstance(decoded, dict):
        detail = body.decode("utf-8", errors="replace")[:2000]
        raise GenerationError(f"ComfyUI HTTP {status}: {detail}")
    return decoded


# ---------------------------------------------------------------- CLI

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--duration", type=int, default=5, help="3-15 seconds")
    parser.add_argument("--resolution", choices=sorted(SUPPORTED_RESOLUTIONS), default="768p")
    parser.add_argument("--aspect-ratio", required=True, choices=("9:16", "16:9"))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--steps", type=int, default=8, help="4-16 sampler steps")
    parser.add_argument("--poll-timeout", type=int, default=3600)
    parser.add_argument("--comfy-url", default=os.environ.get("COMFYUI_URL", DEFAULT_COMFY_URL))
    parser.add_argument("--workflow", type=Path,
                        default=Path(__file__).resolve().parent.parent / "workflows" / "minimax-h3-ref2v.json")
    parser.add_argument("--ref-images", nargs="*", type=Path, default=[])
    parser.add_argument("--ref-videos", nargs="*", type=Path, default=[])
    parser.add_argument("--ref-audios", nargs="*", type=Path, default=[])
    parser.add_argument("--unet", choices=("auto", "fp8", "int8", "nvfp4"), default="auto")
    parser.add_argument("--save-index", type=int, default=0,
                        help=f"Motion Context save clip_index (0-{MAX_CLIP_INDEX})")
    parser.add_argument("--load-index", type=int,
                        help=(f"Motion Context load clip_index (0-{MAX_CLIP_INDEX}); "
                              "omit for standalone shot; 0 = newest in chain; "
                              "child S uses S-1"))
    parser.add_argument("--latent-path", default=DEFAULT_LATENT_PATH,
                        help="stable Motion Context filename_prefix / latent_path for one parent-shot chain")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if not MIN_DURATION <= args.duration <= MAX_DURATION:
        raise GenerationError(f"duration 必须在 {MIN_DURATION}-{MAX_DURATION} 秒之间，得到 {args.duration}")
    if not MIN_STEPS <= args.steps <= MAX_STEPS:
        raise GenerationError(f"steps 必须在 {MIN_STEPS}-{MAX_STEPS} 之间，得到 {args.steps}")
    if not 0 <= args.save_index <= MAX_CLIP_INDEX:
        raise GenerationError(f"save-index 必须在 0-{MAX_CLIP_INDEX} 之间，得到 {args.save_index}")
    if args.load_index is not None and not 0 <= args.load_index <= MAX_CLIP_INDEX:
        raise GenerationError(
            f"load-index 必须在 0-{MAX_CLIP_INDEX} 之间，得到 {args.load_index}")
    if args.load_index is not None and not str(args.latent_path).strip():
        raise GenerationError("load-index 需要非空 --latent-path（同一父分镜链必须复用同一路径）")
    if args.comfy_url and not args.comfy_url.startswith(("http://", "https://")):
        raise GenerationError(f"--comfy-url 必须是 http(s) URL，得到 {args.comfy_url}")
    limits = {"image": len(args.ref_images), "video": len(args.ref_videos), "audio": len(args.ref_audios)}
    for kind, count in limits.items():
        limit = next(group["limit"] for group in REF_GROUPS if group["kind"] == kind)
        if count > limit:
            raise GenerationError(f"参考{kind}最多 {limit} 个，得到 {count}")


def frame_count(duration: int) -> int:
    base = max(FRAME_OFFSET, round(duration * FPS))
    return base + ((FRAME_OFFSET - base % FRAME_STEP) + FRAME_STEP) % FRAME_STEP


# ------------------------------------------------------- workflow transform core

def load_workflow(path: Path) -> dict[str, dict[str, Any]]:
    try:
        workflow = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationError(f"模板加载失败 {path}: {exc}") from exc
    if not isinstance(workflow, dict) or not workflow:
        raise GenerationError(f"模板不是非空 JSON 对象: {path}")
    present = {node.get("class_type") for node in workflow.values() if isinstance(node, dict)}
    missing = sorted(REQUIRED_CLASS_TYPES - present)
    if missing:
        raise GenerationError(f"模板缺少必选 class_type: {', '.join(missing)}")
    return workflow


def clone_workflow(workflow: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return copy.deepcopy(workflow)


def find_node(workflow: dict[str, dict[str, Any]], class_type: str,
              title: str | None = None) -> str:
    """Locate a node id by class_type (+ optional exact _meta.title). Raises on 0 or >1 matches."""
    matches = [
        node_id for node_id, node in workflow.items()
        if node.get("class_type") == class_type
        and (title is None or node.get("_meta", {}).get("title") == title)
    ]
    if not matches:
        suffix = f" (title={title!r})" if title else ""
        raise GenerationError(f"图中找不到节点 class_type={class_type}{suffix}")
    if len(matches) > 1:
        suffix = f" (title={title!r})" if title else ""
        raise GenerationError(f"节点 class_type={class_type}{suffix} 有多个匹配: {matches}")
    return matches[0]


def main_node_id(workflow: dict[str, dict[str, Any]]) -> str:
    return find_node(workflow, "MiniMaxH3ReferenceToVideo")


def find_ref_slot(workflow: dict[str, dict[str, Any]], kind: str,
                  index: int) -> tuple[str, str]:
    """Return (loader_node_id, input_key) for API slot `index` of `kind`.

    Slots are discovered from the main node's inputs (ref_images.ref_image_N etc.)
    — never from loader titles, which are inconsistent across exports.
    """
    group = next((g for g in REF_GROUPS if g["kind"] == kind), None)
    if group is None:
        raise GenerationError(f"未知参考素材类型: {kind}")
    main = workflow[main_node_id(workflow)]
    key = f"{group['prefix']}.{group['field']}_{index}"
    value = main["inputs"].get(key)
    if not (isinstance(value, list) and len(value) == 2 and str(value[0]) in workflow):
        raise GenerationError(f"模板缺少参考槽位 {key}")
    return str(value[0]), key


def find_video_components(workflow: dict[str, dict[str, Any]], loader_id: str) -> str | None:
    """Find the GetVideoComponents node fed by this LoadVideo, if any."""
    for node_id, node in workflow.items():
        if node.get("class_type") == "GetVideoComponents" and node.get("inputs", {}).get("video") == [loader_id, 0]:
            return node_id
    return None


def find_loader_for_components(workflow: dict[str, dict[str, Any]], components_id: str) -> str:
    """Find the LoadVideo feeding a GetVideoComponents node (inverse of the above)."""
    components = workflow.get(components_id)
    feed = components.get("inputs", {}).get("video") if components else None
    if isinstance(feed, list) and len(feed) == 2:
        loader_id = str(feed[0])
        loader = workflow.get(loader_id)
        if loader is not None and loader.get("class_type") == "LoadVideo":
            return loader_id
    raise GenerationError(f"GetVideoComponents {components_id} 的上游 LoadVideo 缺失或类型不符")


def delete_node(workflow: dict[str, dict[str, Any]], node_id: str) -> None:
    """Remove a node and every reference to it across the graph."""
    workflow.pop(node_id, None)
    for node in workflow.values():
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        for key, value in list(inputs.items()):
            if isinstance(value, list) and len(value) == 2 and str(value[0]) == node_id:
                del inputs[key]


def validate_graph(workflow: dict[str, dict[str, Any]]) -> None:
    """Pre-submit client-side graph validation. Raises GenerationError listing all problems."""
    problems: list[str] = []
    allowed_top = {"class_type", "inputs", "_meta"}
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            problems.append(f"节点 {node_id} 不是对象")
            continue
        if not isinstance(node.get("class_type"), str) or not node["class_type"]:
            problems.append(f"节点 {node_id} 缺少 class_type")
        if not isinstance(node.get("inputs"), dict):
            problems.append(f"节点 {node_id} 缺少 inputs")
        extra = set(node) - allowed_top
        if extra:
            problems.append(f"节点 {node_id} 含非法顶层键: {sorted(extra)}")
        for key, value in node.get("inputs", {}).items():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], (str, int)) \
                    and not isinstance(value[0], bool):
                if str(value[0]) not in workflow:
                    problems.append(f"节点 {node_id}.{key} 悬空连线 → {value[0]}")
    if not any(node.get("class_type") == "SaveVideo" for node in workflow.values()):
        problems.append("图中没有 SaveVideo 输出节点")

    # Reference slots must be filled consecutively from 0 with no dangling targets.
    main_id = next((nid for nid, node in workflow.items()
                    if node.get("class_type") == "MiniMaxH3ReferenceToVideo"), None)
    if main_id is not None:
        main_inputs = workflow[main_id]["inputs"]
        for group in REF_GROUPS:
            pattern = re.compile(rf"^{re.escape(group['prefix'])}\.{re.escape(group['field'])}_(\d+)$")
            filled: dict[int, str] = {}
            for key, value in main_inputs.items():
                match = pattern.match(key)
                if not match:
                    continue
                if isinstance(value, list) and len(value) == 2 and str(value[0]) in workflow:
                    filled[int(match.group(1))] = key
                else:
                    problems.append(f"{key} 孤儿引用 → {value}")
            expected = list(range(len(filled)))
            if sorted(filled) != expected:
                problems.append(f"{group['prefix']} 槽位不连续: 已填 {sorted(filled)}，应从 0 连续填充")
    if problems:
        raise GenerationError("图校验失败:\n- " + "\n- ".join(problems))


# ---------------------------------------------------------------- parameter writes

def apply_params(workflow: dict[str, dict[str, Any]], *, prompt: str, duration: int,
                 resolution: str, aspect_ratio: str, steps: int, seed: int,
                 unet_name: str, object_info: dict[str, Any]) -> None:
    find_node(workflow, "PrimitiveStringMultiline", PROMPT_TITLE)
    workflow[find_node(workflow, "PrimitiveStringMultiline", PROMPT_TITLE)]["inputs"]["value"] = prompt

    duration_id = find_node(workflow, "PrimitiveFloat", DURATION_TITLE)
    workflow[duration_id]["inputs"]["value"] = duration
    frames = frame_count(duration)
    if frames % FRAME_STEP != FRAME_OFFSET:
        raise GenerationError(f"帧数 {frames} 不符合 {FRAME_STEP}n+{FRAME_OFFSET} 形状")
    print(f"frames: {frames} ({duration}s @ {FPS}fps, {FRAME_STEP}n+{FRAME_OFFSET})")

    resolution_id = find_node(workflow, "ResolutionSelector", RESOLUTION_TITLE)
    inputs = workflow[resolution_id]["inputs"]
    inputs["megapixels"] = MEGAPIXELS[resolution]
    inputs["aspect_ratio"] = resolve_aspect_ratio(aspect_ratio, object_info)

    workflow[find_node(workflow, "BasicScheduler")]["inputs"]["steps"] = steps
    workflow[find_node(workflow, "RandomNoise")]["inputs"]["noise_seed"] = seed
    workflow[find_node(workflow, "UNETLoader")]["inputs"]["unet_name"] = unet_name


def combo_choices(entry: Any) -> list[str] | None:
    """Extract combo choices from object_info input specs.

    Two real-world shapes: core nodes return [[choice, ...]]; some custom
    nodes (e.g. ResolutionSelector) return ['COMBO', {'options': [...], ...}].
    """
    if isinstance(entry, list) and entry:
        if isinstance(entry[0], list):
            return [str(item) for item in entry[0]]
        if entry[0] == "COMBO" and len(entry) == 2 and isinstance(entry[1], dict):
            options = entry[1].get("options")
            if isinstance(options, list):
                return [str(item) for item in options]
    return None


def resolve_aspect_ratio(aspect_ratio: str, object_info: dict[str, Any]) -> str:
    selector = object_info.get("ResolutionSelector", {})
    choices: list[str] | None = None
    for section in ("required", "optional"):
        entry = selector.get("input", {}).get(section, {}).get("aspect_ratio")
        choices = combo_choices(entry)
        if choices is not None:
            break
    if aspect_ratio == "9:16":
        if choices is not None and ASPECT_9_16 not in choices:
            raise GenerationError(f"9:16 选项 {ASPECT_9_16!r} 不在服务端枚举中，可用: {choices}")
        return ASPECT_9_16
    # 16:9 — exact enum name varies by install; prefix-match against server choices.
    if choices is None:
        raise GenerationError("object_info 缺少 ResolutionSelector.aspect_ratio 枚举，无法解析 16:9")
    for choice in choices:
        if choice.startswith("16:9"):
            return choice
    raise GenerationError(f"服务端枚举中找不到 16:9 选项，可用: {choices}")


# ---------------------------------------------------------------- references

def wire_references(workflow: dict[str, dict[str, Any]], *, images: list[str],
                    videos: list[str], audios: list[str]) -> None:
    """Fill supplied references into consecutive slots from 0; delete unused slot nodes.

    Video slots link to a GetVideoComponents node whose upstream LoadVideo holds
    the file field; image/audio slots link directly to their loaders.
    """
    provided = {"image": images, "video": videos, "audio": audios}
    main = workflow[main_node_id(workflow)]
    for group in REF_GROUPS:
        pattern = re.compile(rf"^{re.escape(group['prefix'])}\.{re.escape(group['field'])}_(\d+)$")
        slots: dict[int, tuple[str, str]] = {}
        for key, value in main["inputs"].items():
            match = pattern.match(key)
            if match and isinstance(value, list) and len(value) == 2:
                slots[int(match.group(1))] = (str(value[0]), key)
        files = provided[group["kind"]]
        if len(files) > group["limit"]:
            raise GenerationError(
                f"参考{group['kind']}最多 {group['limit']} 个，得到 {len(files)}")
        for index in sorted(slots):
            slot_node_id, key = slots[index]
            if index < len(files):
                if group["kind"] == "video":
                    loader_id = find_loader_for_components(workflow, slot_node_id)
                else:
                    loader_id = slot_node_id
                loader = workflow.get(loader_id)
                if loader is None:
                    raise GenerationError(f"槽位 {key} 指向的 loader {loader_id} 不存在")
                loader["inputs"][group["loader_field"]] = files[index]
            else:
                if group["kind"] == "video":
                    components_id = slot_node_id
                    loader_id = find_loader_for_components(workflow, components_id)
                    delete_node(workflow, components_id)
                    delete_node(workflow, loader_id)
                else:
                    delete_node(workflow, slot_node_id)
                main["inputs"].pop(key, None)


# ---------------------------------------------------------------- motion context chain

def input_declared_type(node_info: dict[str, Any], key: str) -> str | None:
    for section in ("required", "optional"):
        entry = node_info.get("input", {}).get(section, {}).get(key)
        if isinstance(entry, list) and entry and isinstance(entry[0], str) and entry[0] != "COMBO":
            return entry[0]
    return None


def bypass_nodes(workflow: dict[str, dict[str, Any]], node_ids: list[str],
                 object_info: dict[str, Any]) -> None:
    """Replicate the ComfyUI frontend's Ctrl+B (bypass) semantics for API-format graphs.

    The execution engine has no mode handling — a UI "bypassed" node is
    excluded from the graph and each consumer link is re-routed through the
    bypassed node's matching-type input link (pass-through); links without a
    pass-through source are dropped. Without this, "mode": 4 is an ignored key
    and the node still executes.
    """
    node_ids = list(dict.fromkeys(node_ids))
    snapshot: dict[str, tuple[str, dict[str, Any], dict[str, Any]]] = {}
    for nid in node_ids:
        node = workflow.get(nid)
        if node is None:
            continue
        snapshot[nid] = (node["class_type"], copy.deepcopy(node.get("inputs", {})),
                         object_info.get(node["class_type"], {}))

    def out_type(nid: str, slot: int) -> str | None:
        outputs = snapshot[nid][2].get("output", [])
        return outputs[slot] if slot < len(outputs) else None

    def resolve(upstream_id: str, upstream_slot: int) -> list | None:
        if upstream_id not in snapshot:
            return [upstream_id, upstream_slot]
        cls, inputs, node_info = snapshot[upstream_id]
        wanted = out_type(upstream_id, upstream_slot)
        for key, value in inputs.items():
            if isinstance(value, list) and len(value) == 2 \
                    and input_declared_type(node_info, key) == wanted:
                return resolve(str(value[0]), value[1])
        return None

    for nid in node_ids:
        if nid not in snapshot:
            continue
        cls, inputs, node_info = snapshot[nid]
        for consumer_id, consumer in workflow.items():
            if consumer_id == nid or not isinstance(consumer, dict):
                continue
            consumer_inputs = consumer.get("inputs", {})
            for key, value in list(consumer_inputs.items()):
                if not (isinstance(value, list) and len(value) == 2 and str(value[0]) == nid):
                    continue
                wanted = out_type(nid, value[1])
                replacement = None
                for src_key, src_value in inputs.items():
                    if isinstance(src_value, list) and len(src_value) == 2 \
                            and input_declared_type(node_info, src_key) == wanted:
                        replacement = resolve(str(src_value[0]), src_value[1])
                        break
                if replacement is None:
                    del consumer_inputs[key]
                else:
                    consumer_inputs[key] = replacement
    for nid in node_ids:
        workflow.pop(nid, None)


def apply_motion_context(workflow: dict[str, dict[str, Any]], *, latent_path: str,
                         save_index: int, load_index: int | None,
                         object_info: dict[str, Any]) -> None:
    """Save is always on (218); omitting load-index excludes the load path.

    load_index semantics (per ComfyUI-H3-Motion-Context _resolve_latent_path):
    omitted = standalone shot / chain head (202/237/213 bypassed out of the
    graph, nothing loaded); 0 = load NEWEST latent in the chain folder;
    N>0 = load exactly slot N. Chain convention: child S saves to slot S and
    loads slot S-1; the chain head omits --load-index entirely.
    """
    if load_index is not None and not 0 <= load_index <= MAX_CLIP_INDEX:
        raise GenerationError(f"load-index 必须在 0-{MAX_CLIP_INDEX} 之间，得到 {load_index}")
    if not 0 <= save_index <= MAX_CLIP_INDEX:
        raise GenerationError(f"save-index 必须在 0-{MAX_CLIP_INDEX} 之间，得到 {save_index}")

    save_id = find_node(workflow, "MiniMaxH3MotionContextSaveLatent")
    # Save writes <prefix>_<NNNNN>.safetensors under the prefix's directory
    # (folder_paths.get_save_image_path). Keeping "clip" as the basename makes
    # slot N land at <latent-path>/clip_0000N.safetensors.
    workflow[save_id]["inputs"]["filename_prefix"] = f"{latent_path.rstrip('/')}/clip"
    workflow[save_id]["inputs"]["clip_index"] = save_index

    if load_index is None:
        bypass_nodes(workflow, [
            find_node(workflow, "MiniMaxH3MotionContextLoadLatent"),
            find_node(workflow, "MiniMaxH3MotionContext"),
            find_node(workflow, "MiniMaxH3MotionContextTrim"),
        ], object_info)
    else:
        load_id = find_node(workflow, "MiniMaxH3MotionContextLoadLatent")
        # Load resolves slot N as <latent_path>/*_0000N.safetensors, so the
        # load path must be the DIRECTORY the save prefix lives in.
        workflow[load_id]["inputs"]["latent_path"] = latent_path
        workflow[load_id]["inputs"]["clip_index"] = load_index
    # MiniMaxH3MotionContextTrim (213) is never touched.


# ---------------------------------------------------------------- model preflight

def object_info_choices(object_info: dict[str, Any], class_type: str,
                        field: str) -> list[str]:
    node = object_info.get(class_type)
    if not isinstance(node, dict):
        raise GenerationError(f"object_info 缺少 {class_type}（自定义节点未安装？）")
    for section in ("required", "optional"):
        entry = node.get("input", {}).get(section, {}).get(field)
        choices = combo_choices(entry)
        if choices is not None:
            return choices
    raise GenerationError(f"object_info 中 {class_type}.{field} 无可选项列表")


def preflight_models(workflow: dict[str, dict[str, Any]], unet_choice: str,
                     object_info: dict[str, Any]) -> str:
    """Validate every model file the template references; resolve --unet auto.

    Raises before any POST /prompt when files are missing.
    """
    unet_options = object_info_choices(object_info, "UNETLoader", "unet_name")
    if unet_choice == "auto":
        for candidate in (UNET_INT8, UNET_FP8, UNET_INT8_CONVROT):
            if candidate in unet_options:
                unet_name = candidate
                break
        else:
            raise GenerationError(
                f"兼容的 H3 Ref2VA UNet 均不存在于服务端。缺失: {UNET_INT8}, {UNET_FP8}, "
                f"{UNET_INT8_CONVROT}；可用示例: {unet_options[:5]}")
    else:
        if unet_choice == "nvfp4":
            candidates = (UNET_NVFP4,)
        elif unet_choice == "int8":
            candidates = (UNET_INT8, UNET_INT8_CONVROT)
        else:
            candidates = (UNET_FP8,)
        unet_name = next((candidate for candidate in candidates if candidate in unet_options), candidates[0])
        if unet_name not in unet_options:
            raise GenerationError(f"UNet 缺失: {', '.join(candidates)}；可用示例: {unet_options[:5]}")

    missing: list[str] = []
    checks: list[tuple[str, str, str]] = [
        ("CLIPLoader", "clip_name", "clip_name"),
        ("VAELoader", "vae_name", "vae_name"),
        ("LoraLoaderModelOnly", "lora_name", "lora_name"),
    ]
    option_cache: dict[str, list[str]] = {}
    for class_type, field, option_field in checks:
        if class_type not in option_cache:
            option_cache[class_type] = object_info_choices(object_info, class_type, option_field)
        options = option_cache[class_type]
        for node in workflow.values():
            if node.get("class_type") == class_type:
                value = node.get("inputs", {}).get(field)
                if isinstance(value, str) and value not in options:
                    missing.append(f"{class_type}.{field}={value}")
    if missing:
        raise GenerationError("模型文件缺失（服务端 object_info 中不存在）:\n- " + "\n- ".join(missing))
    return unet_name


# ---------------------------------------------------------------- upload / submit / poll / download

def upload_media(base_url: str, path: Path, subfolder: str) -> str:
    """Upload image/video/audio via POST /upload/image (core ComfyUI has no /upload/video;
    that endpoint performs no extension validation). Returns 'subfolder/name'."""
    if not path.is_file():
        raise GenerationError(f"参考素材不存在: {path}")
    boundary = f"----h3-{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + path.read_bytes() + (
        f"\r\n--{boundary}\r\n"
        'Content-Disposition: form-data; name="type"\r\n\r\n'
        "input\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="subfolder"\r\n\r\n'
        f"{subfolder}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    status, raw = http_post(f"{base_url}/upload/image", body,
                            f"multipart/form-data; boundary={boundary}")
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = None
    if status != 200 or not isinstance(payload, dict):
        detail = raw.decode("utf-8", errors="replace")[:1000]
        raise GenerationError(f"上传 {path.name} 失败（POST /upload/image, HTTP {status}）: {detail}")
    name = payload.get("name")
    if not isinstance(name, str) or not name:
        raise GenerationError(f"上传 {path.name} 后未返回文件名: {payload}")
    returned_subfolder = str(payload.get("subfolder") or subfolder).strip("/")
    return f"{returned_subfolder}/{name}" if returned_subfolder else name


def check_comfyui(base_url: str) -> dict[str, Any]:
    try:
        stats = json.loads(http_get(f"{base_url}/system_stats"))
        object_info = json.loads(http_get(f"{base_url}/object_info"))
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        raise GenerationError(f"ComfyUI 端点不可达 {base_url}: {exc}（可用 --comfy-url 指定其他地址重试）") from exc
    if not isinstance(object_info, dict):
        raise GenerationError("object_info 返回非对象 JSON")
    if "MiniMaxH3ReferenceToVideo" not in object_info:
        raise GenerationError("ComfyUI 未注册 MiniMaxH3ReferenceToVideo 节点")
    version = stats.get("system", {}).get("comfyui_version", "unknown") if isinstance(stats, dict) else "unknown"
    print(f"ComfyUI ready: {version}")
    return object_info


def submit(base_url: str, workflow: dict[str, dict[str, Any]]) -> str:
    payload = {"prompt": workflow, "client_id": f"h3-{uuid.uuid4().hex}"}
    try:
        response = http_post_json(f"{base_url}/prompt", payload)
    except GenerationError as exc:
        raise GenerationError(f"{exc}\n（服务端校验失败时 node_errors 已包含在上方响应原文中）") from exc
    prompt_id = response.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise GenerationError(f"ComfyUI 未返回 prompt_id: {response}")
    return prompt_id


def poll(base_url: str, prompt_id: str, timeout: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"{base_url}/history/{urllib.parse.quote(prompt_id, safe='')}"
    while time.monotonic() < deadline:
        time.sleep(10)
        try:
            history = json.loads(http_get(url))
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            print(f"history 轮询异常，继续: {exc}", flush=True)
            continue
        entry = history.get(prompt_id) if isinstance(history, dict) else None
        if not isinstance(entry, dict):
            continue
        status = entry.get("status", {})
        status_str = str(status.get("status_str", "")) if isinstance(status, dict) else ""
        if status_str in {"error", "failed"}:
            raise GenerationError(f"ComfyUI 工作流失败: {json.dumps(status, ensure_ascii=False)[:2000]}")
        if status_str not in {"success", "completed"}:
            print(f"running: {status_str or 'unknown'}", flush=True)
            continue
        return entry
    raise GenerationError(f"等待 ComfyUI 任务超时: {prompt_id}")


def output_media(entry: dict[str, Any]) -> dict[str, str]:
    outputs = entry.get("outputs")
    if not isinstance(outputs, dict):
        raise GenerationError("ComfyUI 已完成，但没有 outputs")
    for output in outputs.values():
        if not isinstance(output, dict):
            continue
        for key in ("videos", "video", "gifs", "images"):
            values = output.get(key)
            if not isinstance(values, list):
                continue
            for media in values:
                if not isinstance(media, dict):
                    continue
                filename = media.get("filename")
                if isinstance(filename, str) and Path(filename).suffix.lower() in VIDEO_SUFFIXES:
                    return {
                        "filename": filename,
                        "subfolder": str(media.get("subfolder") or ""),
                        "type": str(media.get("type") or "output"),
                    }
    raise GenerationError("ComfyUI 已完成，但 history 中没有视频媒体")


def download(base_url: str, media: dict[str, str], output: Path) -> None:
    query = urllib.parse.urlencode(media)
    try:
        data = http_get(f"{base_url}/view?{query}")
    except urllib.error.URLError as exc:
        raise GenerationError(f"下载成片失败: {exc}") from exc
    if not data:
        raise GenerationError("ComfyUI 成片下载为空")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validate_args(args)
        base_url = args.comfy_url.rstrip("/")

        object_info = check_comfyui(base_url)

        template = load_workflow(args.workflow)
        unet_name = preflight_models(template, args.unet, object_info)

        subfolder = f"h3-ref/{uuid.uuid4().hex}"
        uploaded_images = [upload_media(base_url, p, subfolder) for p in args.ref_images]
        uploaded_videos = [upload_media(base_url, p, subfolder) for p in args.ref_videos]
        uploaded_audios = [upload_media(base_url, p, subfolder) for p in args.ref_audios]

        workflow = clone_workflow(template)

        seed = args.seed if args.seed is not None else uuid.uuid4().int % (2 ** 53)

        apply_params(workflow, prompt=args.prompt, duration=args.duration,
                     resolution=args.resolution, aspect_ratio=args.aspect_ratio,
                     steps=args.steps, seed=seed, unet_name=unet_name,
                     object_info=object_info)
        wire_references(workflow, images=uploaded_images, videos=uploaded_videos,
                        audios=uploaded_audios)
        apply_motion_context(workflow, latent_path=args.latent_path,
                             save_index=args.save_index, load_index=args.load_index,
                             object_info=object_info)
        validate_graph(workflow)

        print(f"submitted: resolution={args.resolution}, aspect={args.aspect_ratio}, "
              f"duration={args.duration}s, steps={args.steps}, unet={unet_name}, seed={seed}")
        prompt_id = submit(base_url, workflow)
        print(f"prompt_id: {prompt_id}")
        entry = poll(base_url, prompt_id, args.poll_timeout)
        download(base_url, output_media(entry), args.out)
        print(f"saved: {args.out}")
        return 0
    except (GenerationError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
