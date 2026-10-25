#!/usr/bin/env node
// OpenAI-compatible image API backed by Codex ChatGPT OAuth.
// Lets Infinite Canvas use the Codex image quota as a normal image channel.
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import os from "node:os";
import path from "node:path";

const HOST = process.env.CODEX_IMAGE_API_HOST || "127.0.0.1";
const PORT = Number(process.env.CODEX_IMAGE_API_PORT || 17372);
const CLI = process.env.CODEX_IMAGE_CLI || path.join(os.homedir(), ".codex/skills/gpt-image-2-skill/scripts/gpt_image_2_skill.cjs");
const MODEL = process.env.CODEX_IMAGE_MODEL || "gpt-6-luna";
const PROXY = process.env.CODEX_IMAGE_PROXY || "http://127.0.0.1:7890";
const AUTH_FILE = process.env.CODEX_AUTH_FILE || path.join(os.homedir(), ".codex/auth.json");
const KEY_FILE = process.env.CODEX_IMAGE_KEY_FILE || path.join(os.homedir(), ".codex/codex-image-api.key");
let API_KEY = process.env.CODEX_IMAGE_API_KEY || "";
let authMode = API_KEY ? "env" : "none";
const REMOTE_AUTH = !/^(?:127\.0\.0\.1|localhost|::1)$/i.test(HOST);
const ALLOWED_ORIGINS = (process.env.CODEX_IMAGE_ALLOWED_ORIGINS || "http://localhost:3000,http://127.0.0.1:3000,https://canvas.best,https://www.canvas.best")
    .split(",").map((item) => item.trim()).filter(Boolean);
const LOOPBACK_ORIGIN = /^http:\/\/(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/i;
const PRIVATE_ORIGIN = /^https?:\/\/(?:localhost|127\.0\.0\.1|\[::1\]|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?::\d+)?$/i;
const MODELS = [{ id: "gpt-image-2", object: "model", created: 0, owned_by: "codex" }];
const QUALITY_MAP = { low: "low", medium: "medium", high: "high", xhigh: "high", max: "high", auto: "auto" };

function isLoopback(address) {
    const value = String(address || "");
    return value === "127.0.0.1" || value === "::1" || value === "::ffff:127.0.0.1";
}

function authorized(req) {
    if (!API_KEY) return true;
    // A generated key only protects remote clients; loopback keeps working for the local canvas.
    if (authMode === "file" && isLoopback(req.socket.remoteAddress)) return true;
    return req.headers.authorization === `Bearer ${API_KEY}`;
}

async function ensureApiKey() {
    if (API_KEY || !REMOTE_AUTH) return;
    try {
        API_KEY = (await readFile(KEY_FILE, "utf8")).trim();
    } catch {
        // Generate below.
    }
    if (!API_KEY) {
        API_KEY = crypto.randomBytes(24).toString("base64url");
        await writeFile(KEY_FILE, `${API_KEY}\n`, { mode: 0o600 });
        console.log(`Generated API key for remote clients: ${API_KEY}`);
        console.log(`Saved to ${KEY_FILE}`);
    }
    authMode = "file";
}

function originAllowed(origin) {
    return !origin || ALLOWED_ORIGINS.includes(origin) || LOOPBACK_ORIGIN.test(origin) || PRIVATE_ORIGIN.test(origin);
}

function corsHeaders(origin) {
    const allowed = originAllowed(origin);
    return {
        ...(allowed && origin ? { "access-control-allow-origin": origin, vary: "origin" } : {}),
        "access-control-allow-methods": "GET, POST, OPTIONS",
        "access-control-allow-headers": "authorization, content-type",
        "access-control-allow-private-network": "true",
        "access-control-max-age": "86400",
    };
}

function send(res, status, payload, origin) {
    res.writeHead(status, { ...corsHeaders(origin), "content-type": "application/json; charset=utf-8" });
    res.end(JSON.stringify(payload));
}

function sendError(res, status, message, code, origin) {
    send(res, status, { error: { message, code, type: "codex_image_api_error" } }, origin);
}

function readBody(req) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        req.on("data", (chunk) => chunks.push(chunk));
        req.on("end", () => resolve(Buffer.concat(chunks)));
        req.on("error", reject);
    });
}

function normalizeSize(value) {
    const size = String(value || "").trim();
    if (!/^\d{2,5}x\d{2,5}$/i.test(size)) return "";
    const [width, height] = size.toLowerCase().split("x").map(Number);
    if (width > 3840 || height > 3840 || width % 16 || height % 16) return "";
    return `${width}x${height}`;
}

function normalizeQuality(value) {
    return QUALITY_MAP[String(value || "").trim().toLowerCase()] || "";
}

function parseCliOutput(stdout) {
    const trimmed = stdout.trim();
    if (!trimmed) return {};
    try {
        return JSON.parse(trimmed);
    } catch {
        // Progress lines can prefix the final pretty-printed JSON object; scan for the last balanced object.
        for (let end = trimmed.lastIndexOf("}"); end >= 0; end = trimmed.lastIndexOf("}", end - 1)) {
            for (let start = trimmed.lastIndexOf("{", end); start >= 0; start = trimmed.lastIndexOf("{", start - 1)) {
                try {
                    return JSON.parse(trimmed.slice(start, end + 1));
                } catch {
                    // Keep narrowing the slice.
                }
            }
        }
        return {};
    }
}

function runCli(args) {
    return new Promise((resolve, reject) => {
        const child = spawn(process.execPath, [CLI, "--json", "--provider", "codex", ...args], {
            cwd: path.dirname(CLI),
            env: { ...process.env, HTTPS_PROXY: PROXY, HTTP_PROXY: PROXY, https_proxy: PROXY, http_proxy: PROXY },
            stdio: ["ignore", "pipe", "pipe"],
        });
        let stdout = "";
        let stderr = "";
        child.stdout.on("data", (chunk) => (stdout += chunk));
        child.stderr.on("data", (chunk) => (stderr += chunk));
        child.on("error", reject);
        child.on("close", (code) => {
            const payload = parseCliOutput(stdout);
            if (code === 0) return resolve(payload);
            const error = payload.error || {};
            const detail = typeof error.detail === "string" ? error.detail : error.detail ? JSON.stringify(error.detail) : "";
            const message = [error.message, detail].filter(Boolean).join(" | ") || stderr.trim().split(/\r?\n/).slice(-3).join(" ") || `codex image command failed with exit code ${code}`;
            const failure = new Error(message);
            failure.code = error.code || "";
            failure.stderr = stderr.trim().slice(-2000);
            reject(failure);
        });
    });
}

async function parseRequest(req) {
    const body = await readBody(req);
    const contentType = String(req.headers["content-type"] || "").toLowerCase();
    if (contentType.startsWith("multipart/form-data")) {
        const request = new Request(`http://${HOST}:${PORT}${req.url}`, { method: "POST", headers: { "content-type": req.headers["content-type"] }, body });
        const form = await request.formData();
        const files = [];
        for (const value of form.values()) {
            if (value && typeof value === "object" && typeof value.arrayBuffer === "function") files.push(value);
        }
        return {
            prompt: String(form.get("prompt") || ""),
            n: Number(form.get("n") || 1),
            size: String(form.get("size") || ""),
            quality: String(form.get("quality") || ""),
            background: String(form.get("background") || ""),
            files,
        };
    }
    const json = body.length ? JSON.parse(body.toString("utf8")) : {};
    return { prompt: String(json.prompt || ""), n: Number(json.n || 1), size: String(json.size || ""), quality: String(json.quality || ""), background: String(json.background || ""), files: [] };
}

async function generateOne({ prompt, size, quality, background, files }, index, tempDir) {
    const out = path.join(tempDir, `image-${index}.png`);
    const args = [];
    const transparent = background.trim().toLowerCase() === "transparent";
    const op = files.length ? ["images", "edit"] : transparent ? ["transparent", "generate"] : ["images", "generate"];
    args.push(...op, "-m", MODEL, "--prompt", prompt, "--out", out);
    if (transparent && !files.length) args.push("--method", "auto");
    if (normalizeSize(size)) args.push("--size", normalizeSize(size));
    if (normalizeQuality(quality)) args.push("--quality", normalizeQuality(quality));
    if (files.length) {
        const refs = [];
        for (const [fileIndex, file] of files.entries()) {
            const ref = path.join(tempDir, `ref-${index}-${fileIndex}-${file.name || "image.png"}`);
            await writeFile(ref, Buffer.from(await file.arrayBuffer()));
            refs.push(ref);
        }
        refs.forEach((ref) => args.push("--ref-image", ref));
    }
    await runCli(args);
    return (await readFile(out)).toString("base64");
}

async function handleImages(req, res, edit, origin) {
    if (!originAllowed(origin)) return sendError(res, 403, "origin not allowed", "origin_not_allowed", origin);
    let input;
    try {
        input = await parseRequest(req);
    } catch (error) {
        return sendError(res, 400, `invalid request body: ${error.message}`, "invalid_request", origin);
    }
    if (!input.prompt.trim()) return sendError(res, 400, "prompt is required", "invalid_request", origin);
    if (edit && !input.files.length) return sendError(res, 400, "image is required", "invalid_request", origin);
    const count = Math.max(1, Math.floor(Math.abs(input.n) || 1));
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "codex-image-api-"));
    const startedAt = Date.now();
    const images = [];
    try {
        for (let index = 0; index < count; index += 1) {
            try {
                images.push({ b64_json: await generateOne(input, index, tempDir) });
            } catch (error) {
                console.error(`${new Date().toLocaleTimeString()} image ${index + 1}/${count} failed [${error.code || "error"}]: ${error.message}${error.stderr ? `\n${error.stderr}` : ""}`);
                if (!images.length && index === count - 1) throw error;
            }
        }
        console.log(`${new Date().toLocaleTimeString()} ${edit ? "edit" : "generate"} ${images.length}/${count} image(s) -> ${((Date.now() - startedAt) / 1000).toFixed(1)}s`);
        send(res, 200, { created: Math.floor(Date.now() / 1000), model: "gpt-image-2", data: images }, origin);
    } catch (error) {
        sendError(res, 502, error.message, "image_generation_failed", origin);
    } finally {
        await rm(tempDir, { recursive: true, force: true });
    }
}

const server = createServer(async (req, res) => {
    const origin = req.headers.origin;
    if (req.method === "OPTIONS") {
        res.writeHead(originAllowed(origin) ? 204 : 403, corsHeaders(origin));
        return res.end();
    }
    const url = new URL(req.url || "/", `http://${HOST}:${PORT}`);
    if (req.method === "GET" && url.pathname === "/health") return send(res, 200, { ok: true, provider: "codex", model: MODEL, auth: authMode === "none" ? "disabled" : authMode === "file" ? "remote-key" : "required" }, origin);
    if (req.method === "GET" && (url.pathname === "/v1/models" || url.pathname.startsWith("/v1/models/"))) {
        if (!authorized(req)) return sendError(res, 401, "invalid api key", "invalid_api_key", origin);
        if (url.pathname === "/v1/models") return send(res, 200, { object: "list", data: MODELS }, origin);
        const id = decodeURIComponent(url.pathname.slice("/v1/models/".length));
        const model = MODELS.find((item) => item.id === id);
        return model ? send(res, 200, model, origin) : sendError(res, 404, `model not found: ${id}`, "model_not_found", origin);
    }
    if (req.method === "POST" && (url.pathname === "/v1/images/generations" || url.pathname === "/v1/images/edits")) {
        if (!authorized(req)) return sendError(res, 401, "invalid api key", "invalid_api_key", origin);
        return handleImages(req, res, url.pathname.endsWith("/edits"), origin);
    }
    sendError(res, 404, "not found", "not_found", origin);
});
server.requestTimeout = 0;
server.headersTimeout = 0;
server.timeout = 0;
await ensureApiKey();
server.listen(PORT, HOST, () => {
    console.log(`Codex Image API: http://${HOST}:${PORT}`);
    console.log(`Infinite Canvas base URL: http://${HOST === "0.0.0.0" ? "<this-machine-ip>" : HOST}:${PORT}`);
    console.log(`Model: gpt-image-2 | Codex model: ${MODEL} | Auth: ${AUTH_FILE}`);
    console.log(`Auth mode: ${authMode === "none" ? "disabled (loopback only)" : authMode === "file" ? `remote clients require key from ${KEY_FILE}` : "required (CODEX_IMAGE_API_KEY)"}`);
    console.log(`Allowed origins: ${ALLOWED_ORIGINS.join(", ")} (plus loopback and private LAN origins)`);
});
