# Agent Skills

本仓库收录可供 Codex 和其他兼容 agent 使用的 skills。每个技能独立放在同名目录中，入口文件为 `SKILL.md`。

## 目录结构

所有技能的真实文件只存在本仓库，各 agent 的 skills 目录均软链到此：

```
~/skills/<name>/                 # 唯一真源（本仓库）
~/.agents/skills/<name>          -> ~/skills/<name>
~/.claude/skills/<name>          -> ~/skills/<name>
~/.codex/skills/<name>           -> ~/skills/<name>
~/.zcode/skills/<name>           -> ~/skills/<name>
~/.config/opencode/skills/<name> -> ~/skills/<name>
```

改技能只需改本仓库，所有 agent 立即生效。

## 精选技能

| 技能 | 用途 | 来源 |
| --- | --- | --- |
| [agent-browser](agent-browser/SKILL.md) | 通过 `agent-browser` CLI 自动操作浏览器；完整操作指南由 CLI 提供。 | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) |
| [ai-working-principles](ai-working-principles/SKILL.md) | 跨主题 AI 做事准则：简洁回答、证据与时效核对、按需澄清、诊断日志和验证。 | 本仓库；[参考来源](ai-working-principles/references/SOURCES.md) |
| [find-skills](find-skills/SKILL.md) | 搜索并推荐可安装的 agent skills。 | [vercel-labs/skills](https://github.com/vercel-labs/skills) |
| [humanizer](humanizer/SKILL.md) | 修改 AI 痕迹较重的文字，同时保留原意和作者语气。 | [blader/humanizer](https://github.com/blader/humanizer) |
| [karpathy-guidelines](karpathy-guidelines/SKILL.md) | 编码和代码审查时减少过度设计、未经确认的假设和无关改动。 | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) |
| [leader](leader/SKILL.md) | 把一句话想法拆成带调研、边界和验收标准的 agent 任务书。 | [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) |
| [ltx-2-5-prompter](ltx-2-5-prompter/SKILL.md) | 将视频创意整理为 LTX 2.5 单镜头、多镜头或剧本式生成提示词。 | [benjiyaya/LTX-2.5-Agent-Prompt-Skill](https://github.com/benjiyaya/LTX-2.5-Agent-Prompt-Skill) |
| [openviking-memory](openviking-memory/SKILL.md) | 检索、读取和管理 OpenViking 中的记忆与资源，并判断何时写入。 | [volcengine/OpenViking](https://github.com/volcengine/OpenViking) |
| [openviking-skills](openviking-skills/SKILL.md) | 管理 OpenViking 中的技能，包括查找、安装、更新、迁移和校验。 | [volcengine/OpenViking](https://github.com/volcengine/OpenViking) |
| [sc-clsemi-flow](sc-clsemi-flow/SKILL.md) | Clsemi/OpenWrt 板端开发、编译、刷机和验证流程。 | 本仓库 |
| [sort-out](sort-out/SKILL.md) | 整理并持续维护项目文档。 | 本仓库 |

## 全部技能（53）

| 技能 | 说明 |
| --- | --- |
| [3d-animation-short-generator](3d-animation-short-generator/SKILL.md) | Create complete stylized 3D animated shorts from a story idea through an ordered production workflow coverin… |
| [agent-browser](agent-browser/SKILL.md) | Browser automation CLI for AI agents. |
| [ai-working-principles](ai-working-principles/SKILL.md) | Apply the user's cross-topic AI working principles for concise answers, reliable and current evidence, focus… |
| [android-dev](android-dev/SKILL.md) | Build, run, inspect, and lightly automate Android apps with the android-emulator MCP tools. |
| [brand-promo-video-generator](brand-promo-video-generator/SKILL.md) | For marketers and creators producing promotional content for brands, products, websites, apps, shops, or per… |
| [co-op-game-intro-generator](co-op-game-intro-generator/SKILL.md) | For users creating a two-player co-op game menu or opening animation. |
| [codex-imagegen](codex-imagegen/SKILL.md) | Use Codex's own ChatGPT quota to generate or edit images when the user explicitly asks for "Codex 内置生图", "用… |
| [comfyui-h3-generate-video](comfyui-h3-generate-video/SKILL.md) | Use ONLY for local/remote ComfyUI MiniMax H3 video generation. |
| [computer-use](computer-use/SKILL.md) | Use when a task needs a native desktop app's own UI or the OS. |
| [control-browser](control-browser/SKILL.md) | Main-agent-only Browser Use. |
| [diagnosing-commands](diagnosing-commands/SKILL.md) | Use to diagnose and fix ZCode custom slash-command (/command) configuration problems in the ZCode client. |
| [diagnosing-hooks](diagnosing-hooks/SKILL.md) | Use to diagnose and fix ZCode hook configuration problems in the ZCode client. |
| [diagnosing-mcp](diagnosing-mcp/SKILL.md) | Use to diagnose and fix ZCode MCP (Model Context Protocol) server configuration problems in the ZCode client. |
| [diagnosing-plugins](diagnosing-plugins/SKILL.md) | Use to diagnose and fix ZCode plugin and marketplace problems in the ZCode client. |
| [diagnosing-skills](diagnosing-skills/SKILL.md) | Use to diagnose and fix ZCode skill configuration problems in the ZCode client. |
| [docx](docx/SKILL.md) | Complete DOCX document creation, editing, and analysis capabilities with support for revisions, comments, fo… |
| [dot-skill](dot-skill/SKILL.md) | Unified meta-skill engine for distilling colleague, relationship, or celebrity characters into reusable Skil… |
| [dynamic-workflows](dynamic-workflows/SKILL.md) | Use when writing, debugging, or resubmitting a dynamic-workflow script for the CreateWorkflow tool: choosing… |
| [find-skills](find-skills/SKILL.md) | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill fo… |
| [gpt-image-2-skill](gpt-image-2-skill/SKILL.md) | This skill should be used when the user asks to "generate an image", "create a logo", "draw an icon", "edit… |
| [graphic-content-creation](graphic-content-creation/SKILL.md) | Use when creating image-based posts for Xiaohongshu, designing carousel content with multiple images, struct… |
| [h3-prompt-writing](h3-prompt-writing/SKILL.md) | Write MiniMax H3 video generation prompts for T2VA, I2VA, FL2VA, L2VA, and Ref2VA. |
| [handdrawn-live-video-generator](handdrawn-live-video-generator/SKILL.md) | For creators making surreal short videos that blend rough glowing hand-drawn animation with live-action spac… |
| [hashtag-optimization](hashtag-optimization/SKILL.md) | Use when optimizing hashtags and topic tags on Xiaohongshu posts to increase discoverability, improving sear… |
| [humanizer](humanizer/SKILL.md) | Rewrite AI-sounding text so it reads like the writer without changing what it says. |
| [ios-dev](ios-dev/SKILL.md) | Build, run, inspect, and lightly automate iOS simulator apps with the ios-simulator MCP tools. |
| [karpathy-guidelines](karpathy-guidelines/SKILL.md) | Behavioral guidelines to reduce common LLM coding mistakes. |
| [leader](leader/SKILL.md) | 把一句话的想法拆成 AI agent 能独立跑完的目标任务书。 |
| [liaozhai-2d-animation-short-generator](liaozhai-2d-animation-short-generator/SKILL.md) | Plan and produce Liaozhai-inspired Chinese 2D animated shorts with dialogue-first timing, uncanny held beats… |
| [ltx-2-5-prompter](ltx-2-5-prompter/SKILL.md) | Use when making LTX 2.5 video prompts from ideas or media. |
| [mihomo-antigravity-fix](mihomo-antigravity-fix/SKILL.md) | Use when Google Antigravity (`agy`, the user may call it "agr") or Gemini Code Assist fails with `FAILED_PRE… |
| [minimalist-product-ad-generator](minimalist-product-ad-generator/SKILL.md) | Turn product images and ad requirements into minimalist product ad shorts for e-commerce promotion and produ… |
| [music-video-subtitle-generator](music-video-subtitle-generator/SKILL.md) | For musicians, video creators, and social-media editors producing AI music videos or emotional short films w… |
| [openviking-memory](openviking-memory/SKILL.md) | Work with OpenViking, the persistent context database behind this agent's memory. |
| [openviking-skills](openviking-skills/SKILL.md) | Find, use, create, install, share, update, and migrate agent skills stored in OpenViking (viking://~/skills… |
| [ov-experience-memory](ov-experience-memory/SKILL.md) | Retrieve and apply OpenViking Experience memories through the Agent runtime's generic OpenViking search and… |
| [paper-collage-explainer-generator](paper-collage-explainer-generator/SKILL.md) | For creators, educators, and social-video editors who need a tactile paper-collage language for narration, k… |
| [papercraft-stop-motion-explainer](papercraft-stop-motion-explainer/SKILL.md) | For creators explaining science, education, or general knowledge through tactile handmade papercraft visuals. |
| [pdf](pdf/SKILL.md) | Professional PDF toolkit covering four production workflows: reports, creative visuals, academic LaTeX, and… |
| [plugin-creator](plugin-creator/SKILL.md) | Create or update ZCode plugin source and a local test marketplace, then guide the user to add, install, upda… |
| [pptx](pptx/SKILL.md) | Create and edit pptx file via pptxgenjs/python-pptx |
| [restore-legacy-sessions](restore-legacy-sessions/SKILL.md) | Use when ZCode needs to inspect, plan, or execute restoration of old ACP-era ZCode sessions from ~/.zcode/v2… |
| [sc-clsemi-flow](sc-clsemi-flow/SKILL.md) | clsemi（Clourney Semi，WA7220-G / WA7230-G，CS8862A，OpenWrt）板端自动化开发流程。 |
| [seeding-content-creation](seeding-content-creation/SKILL.md) | Use when creating product recommendation content on Xiaohongshu, writing posts that naturally lead to purcha… |
| [seeding-copywriting](seeding-copywriting/SKILL.md) | Use when writing product recommendation content (种草文案) for Xiaohongshu, creating authentic product reviews,… |
| [skill-creator](skill-creator/SKILL.md) | Create new skills, edit existing skills, and iterate wording. |
| [sort-out](sort-out/SKILL.md) | 整理并持续维护项目文档（sort out / tidy up / 文档整理 / 文档梳理 / 把文档更新到最新 / 文档过期了）。 |
| [story-skill](story-skill/SKILL.md) | 基于罗伯特·麦基《故事：材质、结构、风格和银幕剧作的原理》的银幕剧作方法论。Use when analyzing, designing, structuring, or rewriting any narrative… |
| [tikhub-api-helper](tikhub-api-helper/SKILL.md) | Search and query TikHub APIs for TikTok, Douyin, Xiaohongshu, Lemon8, Instagram, YouTube, Twitter, Reddit, a… |
| [title-writing](title-writing/SKILL.md) | Use when writing Xiaohongshu post titles, creating headlines for content, improving click-through rates, or… |
| [web-gui-tester](web-gui-tester/SKILL.md) | Use the browser automation tooling available in the session to test web frontends interactively in a purely… |
| [xlsx](xlsx/SKILL.md) | Use this skill any time a spreadsheet file is the primary input or output. |
| [zcode-configuration-guide](zcode-configuration-guide/SKILL.md) | Use when configuring ZCode's extension resources (MCP servers, slash commands, skills, hooks, and plugins) o… |

## 安装

通过 Skills CLI 安装单个技能：

```bash
npx skills add https://github.com/moncishi/skills --skill <skill-name>
```

例如：

```bash
npx skills add https://github.com/moncishi/skills --skill humanizer
```

`agent-browser` 还需要安装其 CLI 和浏览器：

```bash
npm i -g agent-browser
agent-browser install
```
