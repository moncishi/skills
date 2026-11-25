---
name: codex-imagegen
description: Use Codex's own ChatGPT quota to generate or edit images when the user explicitly asks for "Codex 内置生图", "用 Codex 生图", "用 Codex 密钥/额度生图", "imagegen", or wants image generation without an OPENAI_API_KEY. Routes image_generation through Codex ChatGPT OAuth via the local gpt-image-2-skill CLI. Not for ordinary canvas image requests; those should use the infinite-canvas MCP canvas_generate_image tool.
license: MIT
compatibility: opencode
metadata:
  audience: monci
  provider: codex-chatgpt-oauth
---

# Codex Image Generation

用 Codex 的 ChatGPT 账号额度生图，不读 `OPENAI_API_KEY`，也不走 OpenAI API 账单。

## 什么时候用

只在用户明确要求以下能力时使用：

- “用 Codex 生图 / 用 Codex 内置生图 / imagegen”
- “用 Codex 的密钥、账号或额度生图”
- 明确不想配置 `OPENAI_API_KEY` 的图片生成或编辑

普通画布生图、批量出图、需要可控尺寸或透明背景时，优先用 `infinite-canvas` MCP 的 `canvas_generate_image`，不要把这条 Codex 通道当默认。

## 前置条件

- `~/.codex/auth.json` 存在且 ChatGPT OAuth 未过期
- `~/.codex/skills/gpt-image-2-skill` 已安装
- 本机代理 `http://127.0.0.1:7890` 可用（默认值，可用环境变量覆盖）
- Codex 默认模型用 `gpt-6-luna`；Plus 账号不支持技能里写死的 `gpt-5.4`

## 生成

```bash
~/.config/opencode/skills/codex-imagegen/scripts/codex-image.sh generate \
  --prompt "a minimalist blue paintbrush icon on pure white, no text" \
  --out /tmp/opencode/icon.png \
  --size 1024x1024 \
  --quality high
```

## 参考图编辑

```bash
~/.config/opencode/skills/codex-imagegen/scripts/codex-image.sh edit \
  --prompt "把背景改成纯白，保留人物姿势和构图" \
  --ref-image /path/to/source.png \
  --out /tmp/opencode/edited.png
```

可重复传 `--ref-image`，最多 16 张。

## 自检

```bash
~/.config/opencode/skills/codex-imagegen/scripts/codex-image.sh doctor
```

输出里应看到 `"provider": "codex"`、`"reachable": true`。如果 `reachable` 为 `false`，先检查代理，不要改提示词。

## 参数与限制

- 默认模型 `gpt-6-luna`，可用 `CODEX_IMAGE_MODEL` 覆盖；不要用 `gpt-5.4`。
- 默认代理 `http://127.0.0.1:7890`，可用 `CODEX_IMAGE_PROXY` 覆盖。
- 请求的 `--size` 不会被严格遵守：请求 1024x1024 时实际可能是 1254x1254。需要精确尺寸时改用画布生图或 OpenAI 兼容 API。
- `--quality` 可用。
- Codex provider 不支持 `--background`、`--n`、`--mask`、`--input-fidelity`；透明背景请在提示词里明确要求并检查生成结果的 alpha。
- 输出消耗 Codex Plus 额度。
- 不要把 `~/.codex/auth.json` 或任何 token 打印到对话、日志或画布内容里。

## 结果处理

1. 脚本把最终 JSON 输出到 stdout，其中 `path` 是实际文件路径。
2. 检查文件存在且能打开；需要时读取图片确认内容。
3. 项目资产移动到目标目录，不要只留在 `/tmp`。
4. 需要放进画布时，再按画布 MCP 的附件/图片节点流程导入。
5. 失败时先看 `error.code` 和 `detail`：`http_error` 多为代理或模型问题，`auth_failed` 多为 OAuth 过期。

## 可选环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `CODEX_IMAGE_MODEL` | `gpt-6-luna` | Codex 后端模型 |
| `CODEX_IMAGE_PROXY` | `http://127.0.0.1:7890` | 本地代理 |
| `CODEX_IMAGE_SKILL_DIR` | `~/.codex/skills/gpt-image-2-skill` | gpt-image-2-skill 目录 |
| `CODEX_AUTH_FILE` | `~/.codex/auth.json` | Codex OAuth 文件 |
| `CODEX_IMAGE_EVENTS` | 空 | 设为 `1` 时在 stderr 输出进度事件 |

## 给 Infinite Canvas 当 OpenAI 兼容图片 API

脚本 `scripts/codex-image-api.mjs` 把同一条 Codex 通道包装成本地 OpenAI 兼容接口，端口 `17372`。

```bash
# 服务已由 systemd user service 托管
systemctl --user status codex-image-api
systemctl --user restart codex-image-api
journalctl --user -u codex-image-api -f

# 自检
curl http://127.0.0.1:17372/health
```

接口：

- `POST /v1/images/generations`
- `POST /v1/images/edits`（multipart，字段 `image` / `image[]`）
- `GET /v1/models`
- `GET /v1/models/{id}`
- `GET /health`

局域网访问：

- systemd 服务里已设置 `CODEX_IMAGE_API_HOST=0.0.0.0`，监听所有网卡。
- 本机画布继续用 `http://127.0.0.1:17372`，不需要 key。
- 其他设备用 `http://<本机局域网 IP>:17372`，必须带 key。
- key 自动生成在 `~/.codex/codex-image-api.key`，用 `cat` 查看；重启服务不会变化。
- CORS 允许 localhost、127.0.0.1、私有网段（10/8、192.168/16、172.16/12）的任意端口，以及 `canvas.best`。
- 如果从 HTTPS 页面访问 HTTP 的局域网 IP，浏览器可能按混合内容拦截；手机/其他设备建议直接打开局域网 HTTP 版画布。
- 只想本机使用时，把 `CODEX_IMAGE_API_HOST` 改回 `127.0.0.1` 并重启。

在无限画布里新增渠道：

1. 协议选 OpenAI
2. Base URL 填 `http://127.0.0.1:17372`
3. API Key 留空
4. 添加模型 `gpt-image-2`，能力选「图片」
5. 到生图模型里选这个渠道的 `gpt-image-2`

说明：

- 默认监听 `0.0.0.0`（由 systemd 服务设置）；本机请求不需要 key，远程请求需要 `~/.codex/codex-image-api.key`。
- 请求里的 `size` 会被传递，但 Codex 不严格采纳；输出以实际尺寸为准。
- `background: transparent` 会走 gpt-image-2-skill 的 `transparent generate`，返回真实带 alpha 的 PNG。
- 参考图编辑走 `images edit`，最多 16 张参考图。
- 每张图串行生成，`n > 1` 会依次请求，耗时叠加。
- 需要保护本地接口时设置 `CODEX_IMAGE_API_KEY`，渠道里填同一个值即可。
- 日志只记录数量和耗时，不记录提示词内容。

