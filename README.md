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

## 全部技能（85）

| 技能 | 说明 |
| --- | --- |
| [3d-animation-short-generator](3d-animation-short-generator/SKILL.md) | Create complete stylized 3D animated shorts from a story idea through an ordered production workflow coverin… |
| [9router](9router/SKILL.md) | Entry point for 9Router — local/remote AI gateway with OpenAI-compatible REST for chat, image, TTS, embeddin… |
| [9router-chat](9router-chat/SKILL.md) | Chat / code generation via 9Router using OpenAI /v1/chat/completions or Anthropic /v1/messages format with s… |
| [9router-embeddings](9router-embeddings/SKILL.md) | Generate vector embeddings via 9Router /v1/embeddings using OpenAI / Gemini / Mistral / Voyage / Nvidia / Gi… |
| [9router-image](9router-image/SKILL.md) | Generate images via 9Router /v1/images/generations using OpenAI / Gemini Imagen / DALL-E / FLUX / MiniMax /… |
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
| [lark-approval](lark-approval/SKILL.md) | 飞书审批：查询和处理审批待办/已办/实例，搜索可发起审批定义、查看定义详情并发起原生审批实例。 |
| [lark-apps](lark-apps/SKILL.md) | 妙搭（Spark/Miaoda）应用开发与托管：应用创建、本地全栈开发、云端生成迭代、创意设计（UI mockup / 可交互原型 / 线框图 / 落地页 / 仪表盘 / 幻灯片 deck / 视觉探索）、AI相关能… |
| [lark-attendance](lark-attendance/SKILL.md) | 飞书考勤打卡：查询自己的考勤打卡记录 |
| [lark-base](lark-base/SKILL.md) | 飞书多维表格（Base）操作：建表、字段、记录、视图、统计、公式/lookup、表单、仪表盘、workflow、角色权限；遇到 Base/多维表格/bitable 或 /base/ 链接时使用。 |
| [lark-calendar](lark-calendar/SKILL.md) | 飞书日历：管理日历日程和会议室。查看/搜索日程、创建/更新日程、管理参会人、查询忙闲和推荐时段、预定会议室。当用户需要查看日程安排、创建/修改会议、查询/预定会议室时使用。不负责：查询过去的视频会议记录（走 lark… |
| [lark-contact](lark-contact/SKILL.md) | 飞书 / Lark 通讯录:按姓名 / 邮箱解析成 open_id,或按 open_id 反查姓名 / 部门 / 邮箱 / 联系方式 / 个人状态 / 签名。 |
| [lark-doc](lark-doc/SKILL.md) | 飞书云文档（Docx / Wiki 文档）：读取和编辑飞书文档内容。 |
| [lark-drive](lark-drive/SKILL.md) | 飞书云空间（云盘/云存储）：管理 Drive 文件和文件夹，包含上传/下载、创建文件夹、复制/移动/删除、查看元数据、评论/权限/订阅、标题、版本、飞书文档密级标签（secure labels）和本地文件导入。 |
| [lark-event](lark-event/SKILL.md) | Lark/Feishu real-time event listening / subscribing / consuming: stream events as NDJSON via `lark-cli event… |
| [lark-im](lark-im/SKILL.md) | 飞书即时通讯：收发消息和管理群聊。发送和回复消息、搜索聊天记录、管理群聊成员、上传下载图片和文件（支持大文件分片下载）、管理表情回复、发送应用内/短信/电话加急、发送和处理交互卡片（Interactive Card）… |
| [lark-mail](lark-mail/SKILL.md) | 飞书邮箱：Use when user mentions 起草邮件、写邮件、草稿、发送/回复/转发邮件、查阅邮件、看邮件、搜索邮件、邮件文件夹、邮件标签、邮件联系人、监听新邮件、邮件收信规则等；use for mail… |
| [lark-markdown](lark-markdown/SKILL.md) | 飞书 Markdown：查看、创建、上传、编辑和比较 Markdown 文件。 |
| [lark-minutes](lark-minutes/SKILL.md) | 飞书妙记：搜索妙记、查看妙记基础信息、下载/上传音视频、读取或编辑妙记的产物内容、改标题、替换说话人/关键词、申请妙记查看/编辑权限。 |
| [lark-note](lark-note/SKILL.md) | 飞书会议纪要（Note）直查：已知 note_id 时查询纪要详情、展示类型、关联文档 token，并读取 unified 原始逐字记录。 |
| [lark-okr](lark-okr/SKILL.md) | 飞书 OKR：管理目标与关键结果。查看和编辑 OKR 周期、目标、关键结果、对齐关系、量化指标和进展记录。当用户需要查看或创建 OKR、管理目标和关键结果、查看对齐关系时使用。不负责：待办任务管理（lark-task… |
| [lark-openapi-explorer](lark-openapi-explorer/SKILL.md) | 飞书/Lark 原生 OpenAPI 探索：从官方文档库中挖掘未经 CLI 封装的原生 OpenAPI 接口。 |
| [lark-shared](lark-shared/SKILL.md) | Use for lark-cli setup/auth tasks: auth login/status/logout, user vs bot identity, business-domain permissio… |
| [lark-sheets](lark-sheets/SKILL.md) | 飞书电子表格：创建和操作电子表格。支持创建表格、管理工作表与行列结构（增删/合并/调整尺寸/隐藏/冻结）、读写单元格（值/公式/样式/批注/单元格图片）、查找替换、多操作原子批量更新，以及图表、透视表、条件格式、筛选… |
| [lark-skill-maker](lark-skill-maker/SKILL.md) | 创建 lark-cli 的自定义 Skill。当用户需要把飞书 API 操作封装成可复用的 Skill（包装原子 API 或编排多步流程）时使用。 |
| [lark-slides](lark-slides/SKILL.md) | 飞书幻灯片：创建和编辑幻灯片。创建演示文稿、读取幻灯片内容、管理幻灯片页面（创建、删除、读取、局部替换）。当用户需要创建或编辑幻灯片、读取或修改单个页面时使用。当用户给出 doubao.com 的 /slides/… |
| [lark-task](lark-task/SKILL.md) | 飞书任务：管理任务、清单和任务智能体。创建待办任务、查看和更新任务状态、拆分子任务、组织任务清单、分配协作成员、上传任务附件、注册或注销任务智能体、更新任务智能体的主页数据、写入智能体任务记录。当用户需要创建待办事项… |
| [lark-vc](lark-vc/SKILL.md) | 飞书视频会议：搜索历史会议记录、查询会议纪要（总结/待办/章节/逐字稿）、查询参会人快照。 |
| [lark-vc-agent](lark-vc-agent/SKILL.md) | 飞书视频会议会中能力：用于让应用机器人真实加入或离开正在进行的会议，并读取当前身份可见的会中事件、发送会中文本消息或会中表情。 |
| [lark-whiteboard](lark-whiteboard/SKILL.md) | 飞书画板：查询和编辑飞书云文档中的画板。支持导出画板为预览图片、导出原始节点结构、使用多种格式更新画板内容。 当用户需要查看画板内容、导出画板图片、编辑画板时使用此 skill。不负责：飞书云文档内容编辑（lark-… |
| [lark-wiki](lark-wiki/SKILL.md) | 飞书知识库：管理知识空间、空间成员和文档节点。创建和查询知识空间、查看和管理空间成员、管理节点层级结构、在知识库中组织文档和快捷方式。当用户需要在知识库中查找或创建文档、浏览知识空间结构、查看或管理空间成员、移动或复… |
| [lark-workflow-meeting-summary](lark-workflow-meeting-summary/SKILL.md) | 会议纪要整理工作流：汇总指定时间范围内的会议纪要并生成结构化报告。当用户需要整理会议纪要、生成会议周报、回顾一段时间内的会议内容时使用。 |
| [lark-workflow-standup-report](lark-workflow-standup-report/SKILL.md) | 日程待办摘要：编排 calendar +agenda 和 task +get-my-tasks，生成指定日期的日程与未完成任务摘要。适用于了解今天/明天/本周的安排。 |
| [leader](leader/SKILL.md) | 把一句话的想法拆成 AI agent 能独立跑完的目标任务书。 |
| [liaozhai-2d-animation-short-generator](liaozhai-2d-animation-short-generator/SKILL.md) | Plan and produce Liaozhai-inspired Chinese 2D animated shorts with dialogue-first timing, uncanny held beats… |
| [ltx-2-5-prompter](ltx-2-5-prompter/SKILL.md) | Use when making LTX 2.5 video prompts from ideas or media. |
| [mihomo-antigravity-fix](mihomo-antigravity-fix/SKILL.md) | Use when Google Antigravity (`agy`, the user may call it "agr") or Gemini Code Assist fails with `FAILED_PRE… |
| [minimalist-product-ad-generator](minimalist-product-ad-generator/SKILL.md) | Turn product images and ad requirements into minimalist product ad shorts for e-commerce promotion and produ… |
| [music-video-subtitle-generator](music-video-subtitle-generator/SKILL.md) | For musicians, video creators, and social-media editors producing AI music videos or emotional short films w… |
| [omc-reference](omc-reference/SKILL.md) | OMC agent catalog, available tools, team pipeline routing, commit protocol, and skills registry. |
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
