---
name: mihomo-antigravity-fix
description: Use when Google Antigravity (`agy`, the user may call it "agr") or Gemini Code Assist fails with `FAILED_PRECONDITION (code 400): User location is not supported for the API use.` while routing through mihomo / Clash, or when Google / Antigravity traffic through mihomo stops working. Diagnoses the mihomo setup, probes proxy nodes for Antigravity compatibility (datacenter/hosting exit IPs are rejected even in supported countries), and switches the `LLM` proxy-group to a working node.
---

# mihomo × Google Antigravity 修复

修复「mihomo 不能给 `agy`（Antigravity CLI）用了」这一类问题：
对话报 `FAILED_PRECONDITION (code 400): User location is not supported for the API use.`

## 先记住结论

> **看到 `location is not supported` 一律先排「出口 IP」，不要先怀疑 mihomo 坏了。**
> Antigravity 的 agent 执行链路除了校验**国家**，还校验出口 IP 的 **ASN / 机房托管属性**。
> 机房 / 云主机 / 数据中心 IP 会被拒；同一国家下不同 ASN 结果可能完全不同。
> 「能连上 Google」不等于「Antigravity 能用」。

## 环境事实（本机）

| 项 | 值 |
| --- | --- |
| mihomo | `/usr/local/bin/mihomo -d /home/monci/.config/mihomo`，systemd user unit `mihomo` |
| 混合端口 | `127.0.0.1:7890`（http+socks） |
| 外部控制 API | `127.0.0.1:9090`，`secret` 在 `config.yaml` |
| agy | `/home/monci/.local/bin/agy`，凭据在 gnome-keyring + `~/.gemini/antigravity-cli/antigravity-oauth-token` |
| 关键分流组 | `LLM`（2026-10-11 前叫 `GOOGLE`；承载 `googleapis.com` / `google.com` / `goog` 等，Antigravity 全部走它） |
| provider | `subscription`（主机房订阅，节点多为机房 IP，**常被拒**）、`feiniao`（飞鸟云 Hysteria2，**更可能可用**） |

配置与更多背景见 `/home/monci/.config/mihomo/README.md`。

## 快速修复（最常见路径）

```bash
# 1) 看 LLM 组现在指向谁
SECRET=$(sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' ~/.config/mihomo/config.yaml | head -1)
curl -s --noproxy '*' -H "Authorization: Bearer $SECRET" http://127.0.0.1:9090/proxies/LLM \
  | python3 -c 'import sys,json;print("now =",json.load(sys.stdin)["now"])'

# 2) 一键扫描并切换（推荐，见下）
bash ~/.agents/skills/mihomo-antigravity-fix/scripts/probe-and-fix.sh

# 3) 手动切换到已知可用节点
curl -s --noproxy '*' -X PUT -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' \
  -d '{"name":"日本14aws"}' http://127.0.0.1:9090/proxies/LLM

# 4) 用真实 agy 验证（必须返回 PONG）
~/.local/bin/agy --print "reply with exactly PONG"
```

> `agy` 需要桌面会话环境（`DISPLAY` / `DBUS_SESSION_BUS_ADDRESS` / `XDG_RUNTIME_DIR`）
> 才能读到 keyring 里的登录态；脚本会自动补齐。
> 调用本机 9090 API 必须加 `--noproxy '*'`，否则会被环境代理劫持产生假 502。

## 完整排查顺序

1. **确认 mihomo 活着**
   `systemctl --user is-active mihomo`；`journalctl --user -u mihomo -n 20 --no-pager`。
2. **确认失败点在 Antigravity 而非代理链路**
   `agy` 的日志在 `~/.gemini/antigravity-cli/log/*.log`（最新一个）。
   - 出现 `agent executor error: ... User location is not supported` → 出口 IP 问题（本技能）。
   - 出现 `error getting token source: You are not logged into Antigravity` → 先修登录/凭据，不是代理问题。
   - 出现 `proxyconnect ... connection refused` / 超时 → 代理没走通，先修 mihomo 连通性。
3. **确认 agy 真的走 mihomo**（可选）
   把 `https_proxy` 指向黑洞端口再跑一次：若报 `proxyconnect ... connection refused` 而非
   location 错误，说明它确实用了代理。
4. **扫描出口节点**：`scan-llm-agy.sh`（全量、不影响当前分流；加 `--fast` 用 HTTP 探针，约 10 分钟）
   或 `probe-and-fix.sh`（在 LLM 组内逐个用真实 `agy` 验证，挑返回 `PONG` 的节点）。**注意**：
   Antigravity 按每次连接的出口 IP 随机判定，同一节点时好时坏；单次 `LOCATION` 不下结论，
   同一节点**最多探测 3 次、≥2 次 PONG 才算通过**（快速探针同理：6 次里 ≥4 次 OK）。
5. **仍无节点可用** → 刷新 provider（`--refresh`）或更换/新增订阅（要**非机房/住宅/干净 IP**）。

## scan-llm-agy.sh 用法（全量重扫白名单，推荐）

```bash
S=~/.agents/skills/mihomo-antigravity-fix/scripts/scan-llm-agy.sh
bash $S                      # 真实 agy 全量扫描（最稳，约 1 小时）
bash $S --fast               # HTTP 快速探针全量（约 10 分钟，判定与 agy 一致）
bash $S --fast --limit 3     # 冒烟测试：只扫前 3 个候选
bash $S --fast --nodes "印度-优化,香港WAP-优化"   # 只扫指定节点
bash $S --fast --verify 3    # 快速扫完后，对前 3 个 PASS 节点补真实 agy 抽查
bash $S --probe-count 8      # 快速模式每节点最多探测次数（默认 6）
bash $S --keep               # 扫描后保留临时组 LLM_SCAN / 端口 7891
```

- 两种模式都经临时组 `LLM_SCAN` + 本地端口 `127.0.0.1:7891` 进行，**不动** `LLM` 组当前选择和正常分流；
  开始/结束自动注入/移除临时配置并重载（`PUT /configs?force=true`）。
- 默认模式判定：真实 `agy --print "reply with exactly PONG"`，每节点 ≤3 次、`PONG` ≥2 次 = PASS；
  `L`=LOCATION、`O`=超时/其他、`A`=登录态问题（连续 3 个 A 会中止）。
- `--fast` 判定：HTTP 探针（见下），每节点最多 `--probe-count` 次（默认 6），OK ≥ ⌈2K/3⌉ = PASS
  （6 次里 ≥4 次）；`P`=OK、`L`=LOCATION、`N`=节点不通（首个探测即 N 直接判死节点，省时）。
- 结果落盘 `/tmp/opencode/agy_scan_<ts>.tsv|.log`；**白名单不自动改**，人工复核后把打印出的
  filter 正则粘进 `~/.config/mihomo/config.yaml` 的 `LLM` 组并重载。

## probe-fast.sh 用法（单节点秒级体检）

```bash
PF=~/.agents/skills/mihomo-antigravity-fix/scripts/probe-fast.sh
bash $PF --node 日本14aws            # 单节点体检；PASS 退出码 0，fail 退出码 1
bash $PF --node 印度-优化 --count 6  # 指定探测次数
bash $PF --nodes "a,b"               # 多节点
bash $PF --teardown                  # 移除临时组 LLM_SCAN / 端口 7891
```

> `PF_CSE`（Antigravity 公开 OAuth client secret）不再硬编码在脚本里。需要刷新 token 时先
> `export PF_CSE=<secret>`；未设置时会退回使用 agy 自己未过期的 token。

原理（2026-10-15 逆向 + 校准）：
- 复刻 agy 真实生成请求：`POST https://daily-cloudcode-pa.googleapis.com/v1internal:streamGenerateContent?alt=sse`，
  body `{"model":"gemini-3-flash","request":{…一条 "ping"，maxOutputTokens:1}}`，带 Antigravity 系
  请求头（UA / X-Goog-Api-Client / Client-Metadata；**不带** x-goog-user-project）。
- 结果分类：`HTTP 200` = 该出口通过地区校验；`400 … location is not supported` = 被拒；
  网络错误 = 节点死。单次 **1-4 秒**（真实 agy 需 9-30 秒且要桌面环境）。
- 校准（11 节点 × 6 探测 vs 当日真实 agy 扫描，判定完全一致）：
  `印度-优化` 6/6 OK ↔ agy PP；`香港WAP-优化` / `新加坡-优化2-GPT` / `日本-优化` 等 0/6 ↔ agy LLL；
  `台湾-优化2-GPT` 2/6 ↔ agy OLO/PLO（不稳定；补测真实 agy 2/2 LOCATION 吻合）。
- Token 自动管理：读 agy 凭证文件的 refresh_token，用公开 OAuth client 刷新，缓存 50 分钟
  （`/tmp/opencode/agy_probe_token.txt`）；不写回/不破坏 agy 自己的凭证。
- 注意：同一账号走 **PROD 端点**（cloudcode-pa.googleapis.com）会 429 配额不足，**必须用 daily 端点**。

## probe-and-fix.sh 用法

```bash
S=~/.agents/skills/mihomo-antigravity-fix/scripts/probe-and-fix.sh
bash $S                 # 默认候选池扫描，命中即切到 LLM 组
bash $S --full          # 扫描 LLM 组全部节点（很慢，45+ 节点 * ~60s）
bash $S --nodes "日本14aws 新加坡01aws"
bash $S --list          # 只列出 LLM 组可选节点
bash $S --dry-run       # 只扫描不切换
bash $S --refresh       # 先强制刷新所有 provider 再扫描
bash $S --verify        # 只做一次 agy 验证，不扫描
```

## 判定标准

- 成功：`agy --print "reply with exactly PONG"` 输出包含 `PONG`。
- 失败：输出包含 `location is not supported`（换节点）、`PERMISSION_DENIED` /
  `SUBSCRIPTION_REQUIRED`（账号资格/订阅问题，非代理）、超时（节点太慢，换）。

## 已知可用节点（2026-10-15 重扫，76 → 30 个通过）

白名单与每次重扫结果以 `/home/monci/.config/mihomo/README.md` 的「LLM 白名单」节为准；
`LLM` 组的 `filter` 正则即白名单本体（当前 30 个）。最近一次结果：

- 通过（30）：`新加坡01/03/04/05/09/13aws`、`美国03/04/05/06/08/10/11/12aws`、
  `日本02/05/06/10/14/16/17aws`、`hy2台湾02-09`、`印度-优化`
  （晚间 `--fast` 重扫 + agy 抽查新增 `美国11aws`、`hy2台湾02`）
- 主机房订阅除 `印度-优化` 外基本 ❌（机房 IP 被拒或超时）；`IPv6新加坡01-03` ❌（本机无 IPv6 出口）
- 节点池每天轮换，白名单几天就会失真 → 失效先跑 `scan-llm-agy.sh --fast` 重扫
- **边界判定不可直接提拔**：快速探针恰好 4/6（及格线）的节点（当晚 `新加坡02aws`、`新加坡10aws`、
  `台湾-优化2-GPT`、`台湾-优化3`）经真实 agy 抽查全部 LOCATION。白名单新增前必须 agy 抽查，
  或只采纳 ≥5/6 的结果
- **N ≠ L**：`N`（首个探测就不通）说明线路死了（如 2026-10-15 20:15 起飞鸟云全部 Hysteria2 节点
  UDP 整段宕机，20:57 时仍半瘫），无需重扫白名单，换活节点即可；`L` 才是地区被拒
- `--fast` 全量一次约 400 次探测请求，实测未触发 429；探针请求必须走 **daily** 端点
  （`daily-cloudcode-pa.googleapis.com`），PROD 端点会因配额池不同返回 429

## 修复「根因」而不是「现象」

- 如果候选池命中率很低，说明订阅节点质量差：给 `LLM` 组补一个**住宅/非机房**来源。
- 换订阅/改 `config.yaml` 后必须重启并强制刷新 provider：
  ```bash
  systemctl --user restart mihomo
  curl -s --noproxy '*' -X PUT -H "Authorization: Bearer $SECRET" \
    http://127.0.0.1:9090/providers/proxies/feiniao -o /dev/null -w '%{http_code}\n'
  ```
- 不要把 `LLM` 组选中到香港/中国节点（国家本身不支持，必挂）。
- **不要用对同一个节点的单次探测下结论**：实时测得同一节点连续 4 次 LOCATION 后 1 分钟内又能
  PONG（per-connection 出口 IP 随机）；判定一律「≤3 次探测、≥2 次 PONG」。

## 注意事项 / 易踩坑

- 所有对 9090 的 curl 都要 `--noproxy '*'`。
- 节点名里的地区 ≠ 真实出口；以实际结果为准。
- 订阅里混有非节点信息行（「剩余流量：…」「套餐到期：…」「过滤掉N条线路」），探测时跳过。
- `agy --print` 每次约 20–60s（启动慢），全量扫描要有耐心；**优先用 `--fast` 快速探针（1-4s/次）**。
- 修改 `config.yaml` 前先备份（`config.yaml.bak-YYYYmmddHHMMSS`）。
