---
name: sc-clsemi-flow
description: clsemi（Clourney Semi，WA7220-G / WA7230-G，CS8862A，OpenWrt）板端自动化开发流程。当用户提出板端开发需求（改码并编译、刷机、验证一条龙）、要用 U-Boot/tftp 刷机、要编译 clsemi-openwrt 固件、要初始化新项目或新板子接入本流程（init）、要体检编译/串口/MCP/刷机环境（doctor、体检、环境检查）时使用。也可用 /sc-clsemi-flow <需求|init|doctor> 显式触发。覆盖流水线：需求→环境预检→建分支→改码→docker 编译→U-Boot 刷机→验证→commit→review 邮件→合并。
---

# sc-clsemi-flow 自动化开发流程

一个入口三个模式，按用户输入分发：

| 输入 | 模式 |
|------|------|
| `/sc-clsemi-flow init [项目路径]`、"初始化新项目"、"接入新项目/新板子" | **init**：为项目生成 `.zcode/` 配置 |
| `/sc-clsemi-flow doctor`、"体检"、"检查环境"、"doctor" | **doctor**：环境与配置体检 |
| `/sc-clsemi-flow <需求描述>`，或直接提板端开发需求 | **开发流程**：完整流水线 |

## 通用第一步：读项目配置

读工作区 `.zcode/sc_clsemi_flow.env`（项目级环境配置，所有环境参数只从它取，禁止硬编码）：

- 开发流程 / doctor 模式：文件不存在 → 停止，提示先运行 init
- init 模式：文件已存在 → 不覆盖，向用户说明除非明确要求覆盖

从 env 取参数：`PROJECT_ROOT`（工作区根，运行日志等相对路径的锚点）`SDK_ROOT` `DOCKER_CONTAINER` `DOCKER_USER` `BUILD_TARGET` `GIT_BRANCH` `BUILD_DOC` `SERVERIP` `SSH_USER` `SSH_PASS` `BOARD_IP` `BOARD_USER` `BOARD_PASS` `DUT_TUNNEL_PORT` `TELNET_TUNNEL_PORT` `ENTERBOOT_VAR` `MCP_URL` `SERVERIP_PC` `WORK_DIR_PC` `SERIAL_PORT` `SERIAL_BAUD` `UBOOT_CMDS_FILE` `UBOOT_PROMPT` `LINUX_PROMPT` `BOOT_DONE_PATTERN` `MAIL_CONF` `MAIL_TO`。

## init 模式

目的：新项目接入 = 一条 init + 改几个值。模板在本 skill `templates/`，通用脚本在 `scripts/`。

1. 用 AskUserQuestion 收集项目特有值（只问这 5 个，给默认值候选，用户不想打字）：
   - 项目根路径（默认当前工作区）→ 模板 `{{PROJECT_ROOT}}`
   - `SDK_ROOT`：clsemi-openwrt 绝对路径 → `{{SDK_ROOT}}`
   - `DOCKER_CONTAINER`：编译 docker 容器 ID → `{{DOCKER_CONTAINER}}`
   - `BUILD_TARGET`：板型（wa7220-g / wa7230-g）→ `{{BUILD_TARGET}}`
   - `GIT_BRANCH`：主分支名 → `{{GIT_BRANCH}}`（默认 master）
   - 其余值（服务器、PC 通道、串口、板子登录、邮件）已按环境设施默认值**烤在模板里**，生成后用户改 env 即可
2. 模板替换 `{{占位符}}` 后写入 `<项目>/.zcode/`（已存在则跳过并报告）：
   - `templates/sc_clsemi_flow.env.tpl` → `.zcode/sc_clsemi_flow.env`
   - `templates/build_flow.md.tpl` → `.zcode/build_flow.md`（env 的 `BUILD_DOC`，编译+制档引导文档）
   - `templates/uboot_flash_cmds.txt.tpl` → `.zcode/uboot_flash_cmds.txt`（env 的 `UBOOT_CMDS_FILE`，刷机命令序列）

   **对已存在的文件一律不写**：禁止重定向覆盖、禁止 `cp -f`。重复调用 init 是安全的——
   已生成的跳过、缺失的补齐，用户手改过的配置绝不会被模板值冲掉。只有用户明确要求覆盖时才动
   已有文件，且覆盖前先备份为 `<文件>.bak`。init 中途被打断后重跑同样安全（继续补齐缺的）。

   注意：`build_flow.md` 的 mfg 路径含 `cs8862a`（mkbin 目录名随 SoC 型号）——CS8862A 项目
   （wa7220-g / wa7230-g）直接可用；将来换 SoC 的项目需手改该文档的 mfg 路径。
3. 通用脚本不放项目里：MCP 助手直接用本 skill `scripts/mcp_call.py`。若项目缺少
   `sc_script/tools/send_mail.py`（与 `MAIL_CONF` 同目录），从 `scripts/send_mail.py` 拷入；
   `mail.conf` 含 SMTP 凭据属用户级文件，由用户提供（doctor 会检查）。
4. 输出生成清单，建议下一步跑 doctor 体检。

## doctor 模式

逐项检查，输出体检报告（每项 PASS/FAIL/SKIP + 一句话证据），写入 `.zcode/sc_clsemi_flow.log`。FAIL 附修复建议。

1. 配置完整性：env 存在且关键键非空；`$BUILD_DOC`、`$UBOOT_CMDS_FILE` 文件存在
2. docker：`docker ps` 包含 `$DOCKER_CONTAINER`
3. git：`git -C $SDK_ROOT status --porcelain` 干净（不干净=FAIL，见避坑 7）；`git remote -v` 为空不算 FAIL，标注"无远程"
4. MCP 可达：向 `$MCP_URL` 发 initialize，正常返回
5. TFTP：`tftp_control(action="status")`；未运行**不判 FAIL**——像隧道一样调 `tftp_control(action="start")` 自动拉起后重查（阶段 5 本来也会 start）
6. 隧道：`ss -tln | grep $DUT_TUNNEL_PORT`；不通→调 `tunnel_control(action="start", password=$SSH_PASS)` 自动拉起后重查（隧道参数见 PC 侧 config）
7. DUT SSH：`sshpass -p $BOARD_PASS ssh -p $DUT_TUNNEL_PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $BOARD_USER@127.0.0.1 'echo ok'`；板子在 U-Boot 或未开机 → SKIP 并注明
8. 串口：`serial_connect($SERIAL_PORT, $SERIAL_BAUD)` 后立即 `serial_disconnect`；Permission error → 先 `serial_disconnect` 清残留旧会话再连一次，仍失败 = 用户终端占用，请用户关闭后重试
9. 邮件：`MAIL_CONF` 文件存在（不真发信）

## MCP 调用方式

PC 侧 MCP server（ica-mcp-tools）优先用本会话的 mcp 工具；工具不可用时用 curl（服务端 stateless_http，每次 POST 自包含，响应为 SSE，取 `data:` 行解析）：

```bash
curl -s --max-time 30 -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":N,"method":"tools/call","params":{"name":"<工具名>","arguments":{...}}}' \
  | sed -n 's/^data: //p'
```

或用本 skill 自带助手（stdin 传参数 JSON，输出 structuredContent）：

```bash
echo '{"action":"status"}' | python3 ~/.agents/skills/sc-clsemi-flow/scripts/mcp_call.py tftp_control
echo '<args-json>' | python3 ~/.agents/skills/sc-clsemi-flow/scripts/mcp_call.py serial_expect_send 300   # 第二参数=超时秒
```

可用工具：`serial_connect / serial_disconnect / serial_expect_send / serial_read / serial_send / tftp_control / file_pull / file_get` + SSH 六件套（含 tunnel_control）。
注意参数名：`serial_send` 是 `data`；`serial_expect_send` 才是 `send_data`——混用被 pydantic 拒绝且报错藏在列表里，容易误判为"没发出去"。

## 开发流程模式

本次需求：$ARGUMENTS（未被替换时取用户触发本 skill 的原始输入文本）

### 阶段 1 环境预检

按 doctor 模式完整跑一遍；任一 FAIL 即中止并报告，绝不跳过刷机验证强行 commit。

### 阶段 2 Git 准备

1. `git -C $SDK_ROOT fetch origin` → `git checkout $GIT_BRANCH` → `git pull --ff-only`（工作区不干净→中止报告；**仓库可能没配远程**，`git remote -v` 为空则跳过 fetch/pull 并在日志注明）
2. 按需求类型提议分支名（`feat/<英文简述>` 或 `fix/<英文简述>`），用 AskUserQuestion 给 2-3 个候选让用户确认
3. `git checkout -b <分支>`

### 阶段 3 修改代码

1. 按需求正常开发，参考项目现有实现模式；编译构建类命令只在 docker 容器内执行
2. 验收点：需求描述没有明确验收标准时，用 AskUserQuestion 向用户确认；验收点记入 `.zcode/sc_clsemi_flow.log`（不进代码仓库）

### 阶段 4 编译与镜像

1. 读取并**严格按** `$BUILD_DOC`（`.zcode/build_flow.md`）执行：docker 内全量编译 → mfg 三段脚本 → 产物校验
2. 长命令（编译）后台运行、日志落运行日志；失败→读日志→定位修复→重试，最多 3 轮，仍失败停下报告（带日志摘录）
3. 看到文档第 3 步的通过标准（整包存在 + md5 落盘 + 版本时间戳 TS ≥ 第 0 步 T0）即过，进入阶段 5

### 阶段 5 部署

0. **串口占用检查 + 连接 + 断点判定**：
   - 先尝试 `serial_connect($SERIAL_PORT, $SERIAL_BAUD, capture_file="logs/<yyyymmdd_hhmmss>.log")`；报 Permission error → ① 先 `serial_disconnect` 清残留旧会话→重连一次；② 仍失败=用户手动终端占用→请用户关闭后重试，勿反复连。连接成功后**全程复用至阶段 6 验证完成才 disconnect**（中途必须换会话时在运行日志标注"日志空洞区间 <起-止>"）
   - 发裸 `\r`，按最先命中的提示符判定板子状态（U-Boot `$UBOOT_PROMPT`，Linux `$LINUX_PROMPT` 以 # 结尾）：
     - **板子在 U-Boot**（断点恢复场景）→ 跳过步骤 1-4；固件已在 PC TFTP 目录且校验通过时连步骤 1 也跳过，直接从步骤 5 继续
     - **板子在 Linux** → 走完整步骤 1-10
1. `file_pull(<整包在服务器上的绝对路径>, $SSH_PASS)`——密码取自 env；固件落入 PC 交换目录（=TFTP 服务目录）。校验**优先 md5sum**（阶段 4 整包 md5 ↔ file_pull 返回 md5 字段；该字段待 PC 侧 MCP 补上，过渡期用 sha256 与服务器 `sha256sum` 比对）。不一致=传输损坏，重拉 ≤3 次
2. `tftp_control(action="start")`
3. 经隧道 SSH：`fw_setenv $ENTERBOOT_VAR 1 && reboot`；若本次 diff 涉及 `package/boot/uboot-clsemi/` 或 U-Boot 源码，按项目约定先刷 boot（当前流程暂不覆盖 boot 刷写）
4. 等 U-Boot（从 Linux 进入时）：expect `$ENTERBOOT_VAR` 的 bootcmd 标记（如 `re:enterboot=1, stop at u-boot`）再到 `$UBOOT_PROMPT`；若板子正常启动进了 Linux，说明板上 bootcmd 未装 enterboot 检查——经隧道 SSH 安装后重新 reboot 重试
5. 逐行执行 `$UBOOT_CMDS_FILE`：`serial_expect_send(send_data="<该行>\r", post_pattern=$UBOOT_PROMPT, timeout_s=10)`；`mtd erase/write` 等长耗时行 timeout 300+。**tftp 行**：post_pattern 用 `re:Bytes transferred = <期望字节数>` 并回读核对；不一致重跑 tftp **最多 3 次**，仍不一致停下报告（板子停 U-Boot），绝不带病刷写
6. **刷写前数据抽查**（防传输截断/翻位；U-Boot 无 md5sum，仅 crc32 且未必有工具）：
    `md.b 0x400000 16`（镜像头部）与 `md.b <0x400000+整包字节数-0x10> 16`（尾部，地址按大小现算），
    与服务器侧整包的头/尾 16 字节（`xxd` 取）逐一比对，不一致→回步骤 5 重跑 tftp
7. 刷写完成、`boot` 之前：**先在 U-Boot 执行 `setenv $ENTERBOOT_VAR 0; saveenv`**（实测刷机后 env 分区保留、enterboot=1 残留，boot 会再次被拦截）
8. `serial_expect_send(send_data="boot\r", post_pattern=$BOOT_DONE_PATTERN, timeout_s=300)`
9. 系统起来后经隧道 SSH 确认 `$ENTERBOOT_VAR` 为 0（bootcmd 检查已写入 U-Boot env，一般无需再动）
10. 失败停靠：任一步失败，板子停在 U-Boot（最安全位置），告警用户等指示，不自动回滚

### 阶段 6 验证

1. 经隧道 SSH：`cat /proc/device-tree/compatible`（板型正确）；`cat /etc/sercomm/_sercomm_build_time.txt`（与阶段 4 期望值比对一致——**版本校验以此文件为准**；`sc.ver` 受 /etc/profile 加载时机影响，见避坑 10）
2. `file_get` 拉串口日志回本地，扫描：启动走完、无 kernel panic / oops / 反复重启。串口里看不到内核消息（无 "Linux version"）**≠异常**：bootargs 的 loglevel 可能静音内核打印——`cat /proc/cmdline` 看日志等级，用 `dmesg` 取内核打印核对版本与启动健康（勿用 `dmesg -c`，会清环缓冲）
3. 刷机重启后隧道 SSH 首连可能报 `kex_exchange_identification: Connection closed`（DUT sshd/隧道就绪需 ~20-30s）——等 15s 重试即可，非隧道故障
3. 按本次 diff 涉及的模块加功能检查项；逐项执行阶段 3 确认的验收点
4. 出 PASS/FAIL 报告（写入运行日志）；FAIL→定位修复→回阶段 4 循环

### 阶段 7 Commit 与 review 邮件

1. `git add` 仅本次相关文件；commit message 沿用 `git log` 既有风格
2. 生成改动说明文件（需求、分支、commit id、diffstat），然后：
   `MAIL_TO=$MAIL_TO <MAIL_CONF 所在目录>/send_mail.py -s "review: <分支> <一句话摘要>" -f <改动说明文件> -a <diff.patch>`
3. 挂起，向用户报告并等待 review

### Review 后处理

- 用户提修改意见→原分支追加 commit→重走阶段 4→7→再发一封邮件
- 用户确认通过→`git checkout $GIT_BRANCH && git merge --no-ff <分支>`；**push 到 origin 前再向用户确认一次**；`git remote -v` 为空则跳过 push 并在日志注明"仓库无远程，本地合并完成"；合并完成可选删除特性分支

## 通用规则

- 分支/commit 是天然断点：流程中断后重进，先 `git status/log` + 检查产物与运行日志，向用户确认从哪步继续
- 一台板子同一时间只跑一个流程
- 运行日志始终写 `.zcode/sc_clsemi_flow.log`
- 用户偏好：能问就问（AskUserQuestion 给候选），不要瞎猜；不要催用户执行未确认的事

## 实战避坑清单（首刷演练踩过的，跨项目适用）

1. **工具参数名**：`serial_send` 的参数是 `data`；`serial_expect_send` 才是 `send_data`——混用被 pydantic 拒绝且报错信息藏在列表里，容易误判为"没发出去"
2. **COM 口占用**：旧会话未断开、或用户手动终端开着，`serial_connect` 都会报 Permission error。串口步骤失败先 `serial_disconnect` 再重连；仍占用=用户终端开着，请用户关闭。另：**同一 MCP 进程不能重复打开同一 COM 口**——换 capture 文件重连前必须先断开
3. **残留提示符竞态**：expect 的 post_pattern 若是裸提示符（`=>`），可能匹配到上一步遗留的提示符，导致"看似完成实际没完成"。U-Boot 的 tftp/刷写步骤必须用**命令特有完成标志**做 post_pattern（如 `re:Bytes transferred = <期望字节数>`），完成后回读缓冲/捕获文件核对
4. **U-Boot tftp 会静默中断**：曾一次在 124KB 处停了（filesize=1f000），提示符照常出现。凡下载必须核对 `Bytes transferred = <期望大小>`（整包大小，从阶段 4 带过来），不一致就重试 tftp，绝不带病刷写。复盘认定大概率是环境因素（如网线松动）而非软件 bug——重试前先查物理链路（网线/交换机口）
5. **console 激活态吞命令**：刷机后串口处于 "Please press Enter to activate this console." 状态时，第一条命令会被当作激活回车吞掉。先发一个裸 `\r` 并 expect 到 shell 提示符（`root@OpenWrt:~#`），再执行实际命令
6. **enterboot 残留**：`enterboot=1` 设过之后，刷机（擦 0-80MB）也不会清掉它（env 分区不在擦除范围）；`boot` 命令会重跑 bootcmd 又停在 U-Boot。刷写完成、`boot` 之前在 U-Boot 里 `setenv enterboot 0; saveenv`
7. **编译副作用污染 git**：build.sh 会拷贝 power table 到受跟踪文件（wa7230-g 共 6 个 txt）造成工作区脏。建分支前 `git checkout -- <这些文件>` 恢复；commit 时只 add 本次相关文件，副作用文件恢复之
8. **仓库可能无远程**：`git remote -v` 为空则 fetch/pull 跳过并日志注明，流程基于本地 master HEAD 继续
9. **用户手动终端占串口的信号**：用户开始从自己的串口贴板子输出时，MCP 侧 serial_connect 必失败——直接请用户帮忙在板子上跑诊断命令，或等其关闭终端，不要反复重试
10. **板子刚启动别依赖 PATH**：`sc.ver` 这类命令的 PATH 由 `/etc/profile` 注入，刚进命令行时还没加载，报 not found 不代表工具丢了。验证前确认 `uptime` ≥ 50 秒再做 PATH 依赖检查，不够就等或先 `source /etc/profile`；版本一致性仍以 `_sercomm_build_time.txt` 为准（读文件不受 PATH 影响）

## 经验与反思（持续改进本 skill）

完整经验账本在 `references/lessons.md`（现象/根因/处置/沉淀的完整记录）。约定：

- **读**：部署、刷机、环境体检前翻一遍账本；遇到异常先查有没有先例
- **写**：每轮流程收尾（尤其是失败处置后）把新经验按账本里的条目格式追加；根因没查清的也记，标注"根因未定"留待后补
- **提炼**：同一条经验第二次出现、或根因查清时，把可执行的规则提炼进上面的"实战避坑清单"或对应阶段步骤——清单是规则（以清单为准），账本是依据
- **每轮收尾自问三件事**：本次哪里卡住了？哪个判断出过错？下次怎么更早发现？
