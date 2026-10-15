# 经验账本（lessons learned）

本 skill 的反思记录：完整记录现象、根因、处置与沉淀，只增不改，按时间追加。

**分工**：SKILL.md 的"实战避坑清单"是提炼后的可执行规则（每次触发都加载）；
本文件是规则背后的依据、复盘与未决问题，按需读取。历史条目留在这里，规则变更改 SKILL.md。
项目特有教训留在项目运行日志；本账本只收跨项目/机制级适用的经验。

**条目格式**：

```
### YYYY-MM-DD <一句话标题>
- 现象：
- 根因：（查不清就写"根因未定"，留待后补）
- 处置：
- 沉淀：（规则写入 SKILL.md 清单第 N 条 / 或"根因未定，规则先兜底"）
```

---

### 2026-10-12 U-Boot tftp 静默中断（124KB）（2026-10-13 复盘补记）

- 现象：tftp 下载整包在 124KB（filesize=0x1f000）处停住，U-Boot 提示符照常出现，看似成功
- 根因：复盘认定大概率是环境因素（如网线松动）导致链路中断，非软件缺陷；未抓到决定性证据
- 处置：重跑 tftp 后完整传完 55574528 字节；流程加"Bytes transferred 必核对、不一致重试 tftp ≤3 次"兜底
- 沉淀：SKILL.md 避坑清单第 3、4 条；遇静默中断先查物理链路（网线/交换机口）再重试

### 2026-10-13 sc.ver 不在 PATH（首刷验证误判，复盘补记）

- 现象：验证阶段在板子上执行 `sc.ver` 报 not found，一度误判新镜像丢了工具
- 根因：`sc.ver` 的 PATH 在 `/etc/profile` 里注册，开机后要等 profile 加载才生效；当时刚能进命令行就执行，uptime 太小
- 处置：版本校验改以 `/etc/sercomm/_sercomm_build_time.txt` 为准（读文件不依赖 PATH）；PATH 依赖的检查先确认 `uptime` ≥ 50 秒，不够就等或 `source /etc/profile`
- 沉淀：SKILL.md 阶段 6 与避坑清单第 10 条

---

### 2026-10-13 skill 逻辑评审（结合首刷演练历史）：6 处修正

- 现象：对 skill 逻辑整体评审，发现 init 模板默认值矛盾、doctor TFTP 判据过严，另有编号跳 4、build.sh 顺序描述过时、mfg 路径硬编码 SoC、env 缺 PROJECT_ROOT 四处小瑕疵
- 根因：init 步骤写"其余值用模板默认"但模板全是占位符——模板与引用它的步骤没有对账；doctor 把"流程可自动恢复的状态"（TFTP 未运行）误判成了环境故障
- 处置：模板烤入环境设施默认值（占位符只留 5 个项目特有值）；doctor TFTP 改自动拉起；阶段 5 重编号；build.sh 顺序描述改版本无关并标注以实际 build.sh 为准；mfg 路径加"换 SoC 需手改"标注；env 增加 PROJECT_ROOT
- 沉淀：模板与引用它的 init 步骤必须一起对账（对占位符清单）；FAIL 判据要区分"环境故障"与"流程可自动恢复的状态"

---

（以上为最新条目。历史踩坑的规则化条目见 SKILL.md"实战避坑清单"1-10。）

### 2026-10-13 bash 单引号 JSON 里 `\\r` 变字面量，U-Boot 命令积压不执行（V0.43 刷机实测）

- 现象：serial_expect_send 三连发 setenv/ping 全部 timeout 等不到 `=>`；capture 回读发现一行里是 `setenv ipaddr 192.168.1.1\rsetenv serverip ...` 的**字面量反斜杠+r**，无回车
- 根因：bash 单引号不处理转义，JSON 文本里 `\\r` 被 json.loads 解析成字面量 `\r` 两字符；而 serial 工具只展开 `\xNN` 转义、不认 `\r` 字符对——于是"回车"变成了敲进 readline 的两个普通字符，命令永远等不到回车执行。误写来源：把双引号 bash 里的转义习惯（`\\r`→`\r`）带进了单引号
- 处置：单引号 JSON 一律写单反斜杠 `\r`（json.loads → 真回车）；已积压的行发一个真 `\r` 让其执行（报 Unknown command 无碍）后重发，本例无实害。判定手段：serial_read/capture 里看到 `\r` 字样即中招
- 沉淀：项目记忆 mcp-tools-usage-pitfalls.md 第 8 条；serial_connect 返回的 connection_id 是 `serial://<port>:<baud>` 格式也一并记入（disconnect 传端口名会报 No active connection）

### 2026-10-13 串口无内核消息≠异常：loglevel 静音，用 /proc/cmdline + dmesg 验证（用户指点）

- 现象：V0.43 刷机后串口 capture 从 "Starting kernel ..." 直接跳到用户态（无 "Linux version"），一度当采集/启动异常排查
- 根因：U-Boot 传给内核的 bootargs 里 loglevel 静音了内核串口打印，属平台常态非缺陷；串口 capture 不含内核消息不代表没启动
- 处置：内核侧验证改走 `cat /proc/cmdline`（看 bootargs 与 loglevel）+ `dmesg`（取内核打印，一般含内核版本）；注意 `dmesg -c` 打印后会清环缓冲，排查中途勿用
- 沉淀：SKILL.md 阶段 6 步骤 2-3（含"重启后 SSH 首连 kex 失败等 15s 重试"签名）
