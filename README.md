# Agent Skills

本仓库收录可供 Codex 和其他兼容 agent 使用的 skills。每个技能独立放在同名目录中，入口文件为 `SKILL.md`。

## 技能列表

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

第三方技能目录中的 `references/UPSTREAM.md` 记录了上游链接和当前同步的 commit；上游提供独立许可证文件时，也会一并保留。
