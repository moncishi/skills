"""Fake-transport QA suite for the generalized comfyui-h3-generate-video skill.

Injects urllib-level http_get/http_post in generate_video; no real ComfyUI needed.
Run: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import copy
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import generate_video as g  # noqa: E402

TEMPLATE_PATH = SKILL_DIR / "workflows" / "minimax-h3-ref2v.json"
TEMPLATE = json.loads(TEMPLATE_PATH.read_text())


def ok_object_info() -> dict:
    return {
        "MiniMaxH3ReferenceToVideo": {"input": {"required": {}}},
        "ResolutionSelector": {"input": {"required": {"aspect_ratio": [[
            "9:16 (Portrait Widescreen)", "16:9 (Landscape Wide)"]]}}},
        "UNETLoader": {"input": {"required": {"unet_name": [[
            "minimax_h3_ref2va_pruned_int8_scaled.safetensors",
            "minimax_h3_ref2va_pruned_fp8_scaled.safetensors"]]}}},
        "CLIPLoader": {"input": {"required": {"clip_name": [["qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"]]}}},
        "VAELoader": {"input": {"required": {"vae_name": [[
            "minimax_h3_video_vae_fp16.safetensors",
            "minimax_h3_audio_vae_fp32.safetensors"]]}}},
        "LoraLoaderModelOnly": {"input": {"required": {"lora_name": [[
            "minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors"]]}}},
        "MiniMaxH3MotionContextLoadLatent": {
            "input": {"required": {"latent_path": ["STRING", {}], "clip_index": ["INT", {}]}},
            "output": ["LATENT"]},
        "MiniMaxH3MotionContext": {
            "input": {"required": {
                "context_length": [["22", "5", "39", "56"]],
                "audio_context_length": ["INT", {}],
                "conditioning": ["CONDITIONING", {}], "vae": ["VAE", {}],
                "latent": ["LATENT", {}], "context_latent": ["LATENT", {}],
                "audio_vae": ["VAE", {}]}},
            "output": ["CONDITIONING", "INT"]},
        "MiniMaxH3MotionContextTrim": {
            "input": {"required": {"trim_frames": ["INT", {}], "fps": ["INT", {}],
                                   "match_tail": ["BOOLEAN", {}],
                                   "images": ["IMAGE", {}], "audio": ["AUDIO", {}]}},
            "output": ["IMAGE", "AUDIO"]},
    }


class FakeTransport:
    """Records calls; returns scripted responses."""

    def __init__(self, object_info: dict | None = None):
        self.object_info = object_info if object_info is not None else ok_object_info()
        self.calls: list[tuple[str, bytes | None]] = []
        self.prompt_calls = 0
        self.upload_responses: list[tuple[int, str]] = []  # list of (status, json)
        self.upload_fail = False
        self.prompt_status = 200
        self.prompt_body: bytes = b"{}"
        self.prompt_400_body = json.dumps({
            "error": {"type": "invalid_prompt", "message": "Prompt has no outputs"},
            "node_errors": {"191": {"errors": [{"message": "dangling link", "details": ""}]}}}).encode()
        self.history_responses: list[dict] = []
        self.view_bodies: list[bytes] = [b"FAKEMP4DATA"]
        self._uploads = 0
        self._history = 0
        self._views = 0

    # --- urllib-level replacements -------------------------------------
    def get(self, url: str, timeout: int = 300) -> bytes:
        self.calls.append(("GET", url, None))
        if "/system_stats" in url:
            return json.dumps({"system": {"comfyui_version": "0.3.60-test"}}).encode()
        if "/object_info" in url:
            return json.dumps(self.object_info).encode()
        if "/history/" in url:
            self._history += 1
            if self._history <= len(self.history_responses):
                return json.dumps(self.history_responses[self._history - 1]).encode()
            return json.dumps({}).encode()
        if "/view" in url:
            self._views += 1
            body = self.view_bodies[min(self._views - 1, len(self.view_bodies) - 1)]
            if not body:
                raise urllib.error.URLError("empty view response")
            return body
        raise AssertionError(f"unexpected GET {url}")

    def post(self, url: str, data: bytes, content_type: str, timeout: int = 300):
        self.calls.append(("POST", url, data))
        if "/upload/image" in url:
            self._uploads += 1
            if self.upload_fail:
                return 500, b"server exploded"
            status, name = (self.upload_responses.pop(0) if self.upload_responses else (200, f"up{self._uploads}.png"))
            return status, json.dumps({"name": name, "subfolder": "h3-ref/test"}).encode()
        if "/prompt" in url:
            self.prompt_calls += 1
            if self.prompt_status != 200:
                return self.prompt_status, self.prompt_400_body
            return 200, self.prompt_body if self.prompt_body != b"{}" else json.dumps({"prompt_id": "pid-123"}).encode()
        raise AssertionError(f"unexpected POST {url}")

    def install(self):
        self._orig = (g.http_get, g.http_post)
        g.http_get, g.http_post = self.get, self.post

    def uninstall(self):
        g.http_get, g.http_post = self._orig

    def post_count(self, path: str) -> int:
        return sum(1 for c in self.calls if c[0] == "POST" and path in c[1])


def history_success() -> dict:
    return {"pid-123": {"status": {"status_str": "success", "completed": True},
                        "outputs": {"255": {"videos": [{"filename": "out.mp4", "subfolder": "video/MiniMax_H3",
                                                        "type": "output"}]}}}}


def history_failed() -> dict:
    return {"pid-123": {"status": {"status_str": "error", "completed": True,
                                   "messages": [{"type": "execution_error"}]}}}


def run_main(argv: list[str], transport: FakeTransport) -> int:
    transport.install()
    try:
        return g.main(argv)
    finally:
        transport.uninstall()


def base_argv(out: str = "/tmp/opencode/t_out.mp4", **overrides) -> list[str]:
    argv = ["--prompt", "test prompt", "--out", out, "--aspect-ratio", "9:16",
            "--poll-timeout", "1"]
    for key, value in overrides.items():
        flag = "--" + key.replace("_", "-")
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        elif isinstance(value, list):
            argv.extend([flag] + [str(v) for v in value])
        else:
            argv.extend([flag, str(value)])
    return argv


class TestTransformCore(unittest.TestCase):
    def test_clone_does_not_mutate_template(self):
        wf = g.clone_workflow(TEMPLATE)
        wf["191"]["inputs"]["length"] = 999
        self.assertEqual(TEMPLATE["191"]["inputs"]["length"], ["215", 1])
        wf["258"]["inputs"]["value"] = "changed"
        self.assertIn("snow-covered", TEMPLATE["258"]["inputs"]["value"])

    def test_find_node_class_and_title(self):
        wf = g.clone_workflow(TEMPLATE)
        self.assertEqual(g.find_node(wf, "PrimitiveFloat", "Duration in Seconds"), "216")
        self.assertEqual(g.find_node(wf, "SaveVideo"), "255")
        with self.assertRaises(g.GenerationError):
            g.find_node(wf, "NonexistentNodeType")

    def test_ref_slots_from_191_not_titles(self):
        wf = g.clone_workflow(TEMPLATE)
        loader_id, key = g.find_ref_slot(wf, "image", 0)
        self.assertEqual((loader_id, key), ("268", "ref_images.ref_image_0"))
        loader_id, key = g.find_ref_slot(wf, "video", 0)
        self.assertEqual((loader_id, key), ("242", "ref_videos.ref_video_0"))
        loader_id, key = g.find_ref_slot(wf, "audio", 2)
        self.assertEqual((loader_id, key), ("267", "ref_audios.ref_audio_2"))

    def test_delete_node_clears_references(self):
        wf = g.clone_workflow(TEMPLATE)
        g.delete_node(wf, "268")
        self.assertNotIn("268", wf)
        main_inputs = wf["191"]["inputs"]
        value = main_inputs.get("ref_images.ref_image_0")
        self.assertTrue(value is None or str(value[0]) != "268")

    def test_validate_graph_catches_dangling_slot(self):
        wf = g.clone_workflow(TEMPLATE)
        # Simulate an inconsistent manual edit: loader node removed but the
        # main node's input key left behind (delete_node would clean it).
        del wf["268"]
        with self.assertRaises(g.GenerationError) as ctx:
            g.validate_graph(wf)
        self.assertIn("ref_images.ref_image_0", str(ctx.exception))

    def test_validate_graph_ok_on_clean_template(self):
        wf = g.clone_workflow(TEMPLATE)
        g.validate_graph(wf)  # no exception

    def test_load_workflow_missing_class_type(self):
        bad = g.clone_workflow(TEMPLATE)
        bad.pop("255")
        path = Path("/tmp/opencode/t_bad_missing_savevideo.json")
        path.write_text(json.dumps(bad))
        with self.assertRaises(g.GenerationError) as ctx:
            g.load_workflow(path)
        self.assertIn("SaveVideo", str(ctx.exception))

    def test_load_workflow_invalid_json(self):
        path = Path("/tmp/opencode/t_not_json.txt")
        path.write_text("not json")
        with self.assertRaises(g.GenerationError):
            g.load_workflow(path)


class TestParams(unittest.TestCase):
    def test_preflight_accepts_installed_convrot_ref2va_unet(self):
        info = ok_object_info()
        info["UNETLoader"]["input"]["required"]["unet_name"][0] = [
            "minimax_h3_ref2va_pruned_int8_convrot.safetensors"]
        self.assertEqual(
            g.preflight_models(g.clone_workflow(TEMPLATE), "auto", info),
            "minimax_h3_ref2va_pruned_int8_convrot.safetensors")

    def test_apply_params_full_write(self):
        wf = g.clone_workflow(TEMPLATE)
        g.apply_params(wf, prompt="hello world", duration=8, resolution="768p",
                       aspect_ratio="9:16", steps=12, seed=424242,
                       unet_name=g.UNET_INT8, object_info=ok_object_info())
        self.assertEqual(wf["258"]["inputs"]["value"], "hello world")
        self.assertEqual(wf["216"]["inputs"]["value"], 8)
        self.assertEqual(wf["217"]["inputs"]["megapixels"], 0.9)
        self.assertEqual(wf["217"]["inputs"]["aspect_ratio"], "9:16 (Portrait Widescreen)")
        self.assertEqual(wf["245:209"]["inputs"]["steps"], 12)
        self.assertEqual(wf["245:206"]["inputs"]["noise_seed"], 424242)
        self.assertEqual(wf["244:198"]["inputs"]["unet_name"], g.UNET_INT8)

    def test_aspect_16_9_dynamic_match(self):
        wf = g.clone_workflow(TEMPLATE)
        g.apply_params(wf, prompt="x", duration=5, resolution="480p",
                       aspect_ratio="16:9", steps=8, seed=1,
                       unet_name=g.UNET_FP8, object_info=ok_object_info())
        self.assertEqual(wf["217"]["inputs"]["aspect_ratio"], "16:9 (Landscape Wide)")

    def test_aspect_16_9_missing_choice(self):
        info = ok_object_info()
        info["ResolutionSelector"]["input"]["required"]["aspect_ratio"][0] = [
            "9:16 (Portrait Widescreen)", "4:3 (Classic)"]
        with self.assertRaises(g.GenerationError) as ctx:
            g.resolve_aspect_ratio("16:9", info)
        self.assertIn("16:9", str(ctx.exception))

    def test_aspect_rich_combo_format(self):
        # Real shape from custom-node ResolutionSelector: ['COMBO', {'options': [...]}]
        info = ok_object_info()
        info["ResolutionSelector"]["input"]["required"]["aspect_ratio"] = [
            "COMBO", {"options": ["1:1 (Square)", "9:16 (Portrait Widescreen)",
                                  "16:9 (Widescreen)"], "default": "1:1 (Square)"}]
        self.assertEqual(g.resolve_aspect_ratio("16:9", info), "16:9 (Widescreen)")
        self.assertEqual(g.resolve_aspect_ratio("9:16", info), "9:16 (Portrait Widescreen)")

    def test_frame_shape(self):
        for duration in (3, 4, 5, 8, 12, 15):
            frames = g.frame_count(duration)
            self.assertEqual(frames % 17, 5, f"{duration}s -> {frames}")

    def test_duration_bounds(self):
        args = g.parse_args(base_argv(duration=2))
        with self.assertRaises(g.GenerationError):
            g.validate_args(args)
        args = g.parse_args(base_argv(duration=16))
        with self.assertRaises(g.GenerationError):
            g.validate_args(args)
        args = g.parse_args(base_argv(duration=3))
        g.validate_args(args)  # lower bound legal

    def test_load_index_bounds(self):
        args = g.parse_args(base_argv(load_index=0))
        g.validate_args(args)  # 0 = newest, legal
        args = g.parse_args(base_argv(load_index=257))
        with self.assertRaises(g.GenerationError):
            g.validate_args(args)


class TestReferences(unittest.TestCase):
    def test_two_images_one_video(self):
        wf = g.clone_workflow(TEMPLATE)
        g.wire_references(wf, images=["a.png", "b.png"], videos=["v.mp4"], audios=[])
        main = wf["191"]["inputs"]
        self.assertEqual(main["ref_images.ref_image_0"], ["268", 0])
        self.assertEqual(main["ref_images.ref_image_1"], ["274", 0])
        self.assertEqual(wf["268"]["inputs"]["image"], "a.png")
        self.assertEqual(wf["274"]["inputs"]["image"], "b.png")
        self.assertEqual(main["ref_videos.ref_video_0"], ["242", 0])
        self.assertEqual(wf["252"]["inputs"]["file"], "v.mp4")
        self.assertIn("242", wf)  # GetVideoComponents kept for filled slot
        # unused slots cleaned
        self.assertNotIn("ref_images.ref_image_2", main)
        self.assertNotIn("269", wf)
        self.assertNotIn("ref_videos.ref_video_1", main)
        self.assertNotIn("263", wf)
        self.assertNotIn("264", wf)
        # audio fully removed
        self.assertNotIn("253", wf)
        self.assertNotIn("266", wf)
        self.assertNotIn("267", wf)
        self.assertFalse(any(k.startswith("ref_audios.") for k in main))
        g.validate_graph(wf)  # cleaned graph must validate

    def test_zero_references_removes_all_loaders(self):
        wf = g.clone_workflow(TEMPLATE)
        g.wire_references(wf, images=[], videos=[], audios=[])
        main = wf["191"]["inputs"]
        for group in g.REF_GROUPS:
            self.assertFalse(any(k.startswith(group["prefix"]) for k in main))
        self.assertNotIn("268", wf)
        self.assertNotIn("252", wf)
        self.assertNotIn("242", wf)
        self.assertNotIn("253", wf)
        g.validate_graph(wf)

    def test_over_limit_rejected(self):
        wf = g.clone_workflow(TEMPLATE)
        with self.assertRaises(g.GenerationError):
            g.wire_references(wf, images=[f"{i}.png" for i in range(10)], videos=[], audios=[])
        with self.assertRaises(g.GenerationError):
            g.wire_references(wf, images=[], videos=["1.mp4", "2.mp4", "3.mp4", "4.mp4"], audios=[])

    def test_over_limit_args_before_submit(self):
        transport = FakeTransport()
        code = run_main(base_argv(ref_images=[f"/tmp/opencode/img{i}.png" for i in range(10)]), transport)
        self.assertEqual(code, 1)
        self.assertEqual(transport.prompt_calls, 0)

class TestMotionContext(unittest.TestCase):
    def test_standalone_excludes_load_path(self):
        wf = g.clone_workflow(TEMPLATE)
        g.apply_motion_context(wf, latent_path="h3_context/clip", save_index=0,
                               load_index=None, object_info=ok_object_info())
        # load path nodes removed from the graph entirely (mode:4 is a no-op key
        # in API format -- the execution engine ignores it)
        self.assertNotIn("202", wf)
        self.assertNotIn("237", wf)
        self.assertNotIn("213", wf)
        # consumer links re-routed through the bypassed nodes (pass-through)
        self.assertEqual(wf["245:207"]["inputs"]["conditioning"], ["191", 0])
        self.assertEqual(wf["245:214"]["inputs"]["images"], ["245:211", 0])
        self.assertEqual(wf["245:214"]["inputs"]["audio"], ["245:212", 0])
        # save node always kept with caller's config (prefix=<latent-path>/clip,
        # clip_index) — load path (when chaining) is the bare latent_path directory
        self.assertEqual(wf["218"]["inputs"]["clip_index"], 0)
        self.assertEqual(wf["218"]["inputs"]["filename_prefix"], "h3_context/clip/clip")
        g.validate_graph(wf)

    def test_chain_child1(self):
        wf = g.clone_workflow(TEMPLATE)
        g.apply_motion_context(wf, latent_path="h3_context/p1_s01_v1", save_index=1,
                               load_index=0, object_info=ok_object_info())
        self.assertIn("202", wf)
        self.assertIn("237", wf)
        self.assertEqual(wf["202"]["inputs"]["latent_path"], "h3_context/p1_s01_v1")
        self.assertEqual(wf["202"]["inputs"]["clip_index"], 0)
        self.assertEqual(wf["218"]["inputs"]["clip_index"], 1)
        g.validate_graph(wf)

    def test_chain_child2(self):
        wf = g.clone_workflow(TEMPLATE)
        g.apply_motion_context(wf, latent_path="h3_context/p1_s01_v1", save_index=2,
                               load_index=1, object_info=ok_object_info())
        self.assertEqual(wf["202"]["inputs"]["clip_index"], 1)
        self.assertEqual(wf["218"]["inputs"]["clip_index"], 2)
        g.validate_graph(wf)

    def test_load_index_negative_rejected(self):
        wf = g.clone_workflow(TEMPLATE)
        with self.assertRaises(g.GenerationError):
            g.apply_motion_context(wf, latent_path="x", save_index=0, load_index=-3,
                                   object_info=ok_object_info())
        with self.assertRaises(g.GenerationError):
            g.apply_motion_context(wf, latent_path="x", save_index=0, load_index=257,
                                   object_info=ok_object_info())


class TestPreflight(unittest.TestCase):
    def test_auto_picks_int8(self):
        wf = g.clone_workflow(TEMPLATE)
        name = g.preflight_models(wf, "auto", ok_object_info())
        self.assertEqual(name, g.UNET_INT8)

    def test_auto_falls_back_to_fp8(self):
        info = ok_object_info()
        opts = info["UNETLoader"]["input"]["required"]["unet_name"][0]
        opts.remove("minimax_h3_ref2va_pruned_int8_scaled.safetensors")
        name = g.preflight_models(g.clone_workflow(TEMPLATE), "auto", info)
        self.assertEqual(name, g.UNET_FP8)

    def test_both_missing_zero_prompt(self):
        info = ok_object_info()
        info["UNETLoader"]["input"]["required"]["unet_name"][0] = ["other_model.safetensors"]
        transport = FakeTransport(object_info=info)
        code = run_main(base_argv(), transport)
        self.assertEqual(code, 1)
        self.assertEqual(transport.prompt_calls, 0)
        self.assertIn("均不存在", self._stderr.getvalue())

    def test_explicit_int8_missing(self):
        info = ok_object_info()
        info["UNETLoader"]["input"]["required"]["unet_name"][0] = [
            "minimax_h3_ref2va_pruned_fp8_scaled.safetensors"]
        with self.assertRaises(g.GenerationError) as ctx:
            g.preflight_models(g.clone_workflow(TEMPLATE), "int8", info)
        self.assertIn("UNet 缺失", str(ctx.exception))

    def test_vae_missing_listed_per_file(self):
        info = ok_object_info()
        info["VAELoader"]["input"]["required"]["vae_name"][0] = ["minimax_h3_video_vae_fp16.safetensors"]
        with self.assertRaises(g.GenerationError) as ctx:
            g.preflight_models(g.clone_workflow(TEMPLATE), "auto", info)
        self.assertIn("minimax_h3_audio_vae_fp32.safetensors", str(ctx.exception))

    def setUp(self):
        self._orig_stderr = sys.stderr
        sys.stderr = io.StringIO()
        self._stderr = sys.stderr

    def tearDown(self):
        sys.stderr = self._orig_stderr


class TestSubmitChain(unittest.TestCase):
    def setUp(self):
        self._orig_stderr = sys.stderr
        sys.stderr = io.StringIO()
        self._stderr = sys.stderr

    def tearDown(self):
        sys.stderr = self._orig_stderr

    def test_full_success_path(self):
        transport = FakeTransport()
        transport.history_responses = [history_success()]
        out = "/tmp/opencode/t_success.mp4"
        code = run_main(base_argv(out=out), transport)
        self.assertEqual(code, 0)
        self.assertEqual(Path(out).read_bytes(), b"FAKEMP4DATA")
        self.assertEqual(transport.prompt_calls, 1)

    def test_history_error_state(self):
        transport = FakeTransport()
        transport.history_responses = [history_failed()]
        code = run_main(base_argv(), transport)
        self.assertEqual(code, 1)
        self.assertIn("工作流失败", self._stderr.getvalue())

    def test_prompt_400_node_errors_surfaced(self):
        transport = FakeTransport()
        transport.prompt_status = 400
        code = run_main(base_argv(), transport)
        self.assertEqual(code, 1)
        err = self._stderr.getvalue()
        self.assertIn("node_errors", err)
        self.assertIn("dangling link", err)

    def test_view_empty_retries_get_only(self):
        transport = FakeTransport()
        transport.history_responses = [history_success()]
        transport.view_bodies = [b""]  # first /view empty
        code = run_main(base_argv(), transport)
        self.assertEqual(code, 1)
        self.assertEqual(transport.prompt_calls, 1)  # never re-POSTed
        self.assertEqual(transport.post_count("/prompt"), 1)

    def test_upload_failure_reported(self):
        img = Path("/tmp/opencode/a.png")
        img.write_bytes(b"PNGDATA")
        transport = FakeTransport()
        transport.upload_fail = True
        code = run_main(base_argv(ref_images=[str(img)]), transport)
        self.assertEqual(code, 1)
        err = self._stderr.getvalue()
        self.assertIn("/upload/image", err)
        self.assertEqual(transport.prompt_calls, 0)

    def test_node_errors_content(self):
        transport = FakeTransport()
        transport.prompt_status = 400
        transport.prompt_400_body = json.dumps({"node_errors": {"191": {"errors": [
            {"message": "required input missing", "details": "ref_images.ref_image_0"}]}}}).encode()
        run_main(base_argv(), transport)
        self.assertIn("ref_images.ref_image_0", self._stderr.getvalue())

    def test_missing_aspect_ratio_argparse(self):
        argv = ["--prompt", "x", "--out", "/tmp/opencode/x.mp4"]
        with self.assertRaises(SystemExit):
            g.parse_args(argv)

    def test_missing_ref_file_rejected_before_upload(self):
        transport = FakeTransport()
        code = run_main(base_argv(ref_images=["/tmp/opencode/definitely-missing.png"]), transport)
        self.assertEqual(code, 1)
        self.assertIn("参考素材不存在", self._stderr.getvalue())
        self.assertEqual(transport.prompt_calls, 0)


class TestStaticChecks(unittest.TestCase):
    def test_template_is_valid_json_and_byte_identical(self):
        import hashlib
        src = Path("/home/monci/codex-based-drama/production/南塘清音/monci-minimax-h3-ref2v.json")
        bundled = SKILL_DIR / "workflows" / "minimax-h3-ref2v.json"
        if src.exists():
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(sha(src), sha(bundled), "bundled template must stay byte-identical to source")

    def test_compileall(self):
        import py_compile
        py_compile.compile(str(SKILL_DIR / "scripts" / "generate_video.py"), doraise=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
