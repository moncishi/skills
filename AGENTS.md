# Skills 仓库规范（AGENTS.md）

## 1. 仓库定位与目录结构

- 本仓库（`moncishi/skills`）收录跨 Agent 可复用的 skills，按 5 个一级分类目录组织：
  - `coding-and-engineering/`
  - `agent-and-meta/`
  - `office-docs/`
  - `video-and-image/`
  - `content-and-social/`
- 每个 skill 目录内必须包含 `SKILL.md`（frontmatter 的 `name` 与目录名保持一致）；新增、删除或移动 skill 时，同步更新 [README.md](README.md) 中的索引和数量统计。
- **安全红线**：严禁将任何账号、密码、Token、API Key 或私有服务端点凭据写入本仓库；凭据统一通过环境变量、本地 `.gitignore` 忽略文件或 OpenViking 私有记忆获取。

---

## 2. 目标项目配置文件管理：统一由 `sort-out` 联动

本仓库中的 [sort-out](coding-and-engineering/sort-out/SKILL.md) 负责在目标项目中管理文档与配置文件的**清单、角色、入库/本地边界、权威范围与更新时机**（维护在目标项目根目录的 `sort-out.config.txt`）。

凡是会**读取、初始化、生成或更新**目标项目配置文件/文档的 skill（例如 [embedded-dev-workflow](coding-and-engineering/embedded-dev-workflow/SKILL.md)、[sc-clsemi-flow](coding-and-engineering/sc-clsemi-flow/SKILL.md) 以及后续新增的同类 skill），都必须与 `sort-out` 联动，不得各自在项目里另起一套互不感知的孤立配置体系。

---

## 3. 多对多（M:N）兼容模型

项目中的配置文件与 skill 之间是**多对多（M:N）**关系，设计与执行时必须同时兼容以下两种情况：

1. **一个配置文件被多个 skill 共用（1 File ← N Skills）**
   - 示例：`AGENTS.md`、`docs/build_and_flash.md`、`STATE.md` 可能同时被 `sort-out`、`embedded-dev-workflow`、`sc-clsemi-flow` 读取或维护。
   - **约束**：严禁单个 skill 对共享配置文件做整文件覆盖（`>` 或无条件 `cp -f`）；必须按章节或键值做增量更新，遵守「单源 + 指针」原则，并以 `sort-out.config.txt` 中声明的「权威」为准。

2. **一个 skill 使用多个配置文件（1 Skill → N Files）**
   - 示例：
     - `embedded-dev-workflow` 依赖 `AGENTS.md`、`STATE.md`、`docs/hardware/*`、`docs/build_and_flash.md`、`reports/*`；
     - `sc-clsemi-flow` 依赖 `.zcode/sc_clsemi_flow.env`、`.zcode/build_flow.md`、`.zcode/uboot_flash_cmds.txt`。
   - **约束**：按职责与稳定度拆文件（长期硬件事实、动态调试状态、本地敏感环境参数分开存放），不要为了省事把动态状态或敏感参数硬塞进同一份文件。

---

## 4. 与 `sort-out` 的联动协议

### 4.1 在 `sort-out.config.txt` 中登记多对多关系
每份配置文件在目标项目 `sort-out.config.txt` 中占一个 `[...]` 小节，通过 **`关联Skill`**（逗号分隔的多值字段）登记所有读取或维护该文件的 skill。这样既可从「配置文件 → 全部依赖它的 skill」反查影响范围，也可从「skill → 全部依赖配置文件」汇总清单：

```text
[AGENTS.md]
角色: 必备
位置: 入库
作用: Agent 工作说明、板级硬约束与红线
权威: 硬约束、红线、入口索引
更新时机: 每次运行
关联Skill: sort-out, embedded-dev-workflow, sc-clsemi-flow

[docs/build_and_flash.md]
角色: 推荐
位置: 入库
作用: 经源码核对的编译、打包、刷机命令与救砖步骤
权威: 编译与刷机命令
更新时机: 相关变更时
关联Skill: sort-out, embedded-dev-workflow, sc-clsemi-flow

[.zcode/sc_clsemi_flow.env]
角色: 自定义
位置: 本地
作用: 板端编译/串口/TFTP/刷机环境参数（含本机与凭据信息，严禁入库）
权威: sc-clsemi-flow 运行时环境参数
更新时机: 相关变更时
关联Skill: sc-clsemi-flow
```

### 4.2 业务 Skill 读写/初始化配置文件的四条联动规则
1. **先查再建（无配置先调 `sort-out`）**：在目标项目读取、初始化或写入配置文件前，先检查项目根目录是否存在 `sort-out.config.txt`。**如果不存在，应先调用一次 `sort-out` skill 初始化 `sort-out.config.txt`**，再继续复用已登记路径或登记本 skill 的配置文件。
2. **新建或变更同步登记**：每个 skill 都要把自身使用的全部配置文件/持久化文件路径登记到 `sort-out.config.txt`，通过 `关联Skill` 标明是哪个（或哪些）skill 使用，写明 `位置`（`入库` / `本地`）、`权威`与`更新时机`；后续运行 `sort-out` 时，也可适当补充遗漏的配置文件或完善 `关联Skill` 说明。
3. **共享文件增量写入与变更前核对**：更新被多个 `关联Skill` 引用的文件时，只做局部/增量修改，保留其他 skill 或人工维护的段落；若需重命名、移动、合并或删除该文件，必须先核对全部 `关联Skill` 的引用并在用户批准后同步更新相关引用。
4. **入库 / 本地红线统一裁决**：包含密码、密钥、个人路径或临时实验日志的配置文件，一律标为 `位置: 本地` 并保持在 `.gitignore` 中，不因联动而越界入库。
