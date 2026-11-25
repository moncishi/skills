---
name: mihomo-antigravity-fix
description: Use when Google Antigravity (`agy`, the user may call it "agr") or Gemini Code Assist fails with `FAILED_PRECONDITION (code 400): User location is not supported for the API use.` while routing through mihomo / Clash, or when Google / Antigravity traffic through mihomo stops working. Diagnoses the mihomo setup, probes proxy nodes for Antigravity compatibility (datacenter/hosting exit IPs are rejected even in supported countries), and switches the `AGY` proxy-group to a working node following multiplier rules (AGY prefers 3x, then 5x, avoiding 1x; all other groups use 1x only).
---

# mihomo × Google Antigravity 修复与倍率规范

修复「mihomo 不能给 `agy`（Antigravity CLI）用了」这一类问题：
对话报 `FAILED_PRECONDITION (code 400): User location is not supported for the API use.`

## 先记住结论

> **看到 `location is not supported` 一律先排「出口 IP」，不要先怀疑 mihomo 坏了。**
> Antigravity 的 agent 执行链路除了校验**国家**，还校验出口 IP 的 **ASN / 机房托管属性**。
> 机房 / 云主机 / 数据中心 IP 会被拒；同一国家下不同 ASN 结果可能完全不同。
> 「能连上 Google」不等于「Antigravity 能用」。

## 倍率策略（硬规范）

1. **只有 `AGY` 组允许使用倍率节点；其他所有分组（`🚀 节点选择`、`♻️ 自动选择`、`🔯 故障转移`）一律只允许使用 `1x`（`1倍消耗`）节点**。
   - 非 `AGY` 组在 `config.yaml` 中统一通过 `filter: "(^|[^0-9.])1[倍xX]"` 限制，禁止测速或故障转移误切到 3x/5x 高倍率节点。
2. **`AGY` 组选路优先级：尽量使用 `3x`（3倍消耗）节点，其次才是 `5x`（5倍消耗）节点，避免使用 `1x` 节点**。
   - `AGY` 组在 `config.yaml` 中使用 `filter: "住宅|家宽"` 并配合 `exclude-filter: "(^|[^0-9.])1[倍xX]"`，既保证住宅/家宽 ASN 质量，又排除 `1x` 节点。
   - 探测与切换脚本（`probe-and-fix.sh`、`scan-llm-agy.sh`）默认跳过 `1x` 与香港节点（香港出口必被拒），并按 **`3x` 优先 → `5x` 其次** 的顺序探测与选用。

## 环境事实（本机）

| 项 | 值 |
| --- | --- |
| mihomo | `/home/gryphon/.local/bin/mihomo -d /home/gryphon/.config/mihomo`，systemd user unit `mihomo` |
| 混合端口 | `127.0.0.1:7890`（http+socks） |
| 外部控制 API | `127.0.0.1:9090`，`secret` 从 `~/.config/mihomo/config.yaml` 动态读取 |
| agy | `/home/gryphon/.local/bin/agy`，凭据在 gnome-keyring + `~/.gemini/antigravity-cli/antigravity-oauth-token` |
| 唯一订阅 provider | `wjkc`（快车订阅，`./providers/wjkc.yaml`，`User-Agent: clash.meta`，经 `♻️ 自动选择` 拉取） |
| Google / Antigravity 分流组 | `AGY`（`type: select`，`filter: "住宅|家宽"`，`exclude-filter: "(^|[^0-9.])1[倍xX]"`） |

## 当前分流组（以 `/home/gryphon/.config/mihomo/config.yaml` 为准）

| 分组 | 类型 | 承载流量 | 节点过滤策略 |
| --- | --- | --- | --- |
| `🚀 节点选择` | `select` | 默认兜底流量（`MATCH`） | 含 `♻️ 自动选择`、`🔯 故障转移`、`DIRECT` + `wjkc` 中 `1x` 节点（`filter: "(^|[^0-9.])1[倍xX]"`） |
| `♻️ 自动选择` | `url-test` | 自动测速最低延迟线路 | 仅 `wjkc` 中 `1x` 节点（`filter: "(^|[^0-9.])1[倍xX]"`） |
| `🔯 故障转移` | `fallback` | 自动故障切换线路 | 仅 `wjkc` 中 `1x` 节点（`filter: "(^|[^0-9.])1[倍xX]"`） |
| `AGY` | `select` | Google / Antigravity 域名 | 仅 `wjkc` 住宅/家宽倍率节点，排除 `1x`；选用顺序 **优先 `3x`，其次 `5x`** |
| `LLM_SCAN`、`LLM_SCAN_2`…`LLM_SCAN_8` | `select` | AGY 扫描临时分组 | 扫描脚本按 worker 临时创建，完成后清理；不是常规业务分流组 |

当前 `wjkc` 订阅中的倍率节点分布（2026-11-25 核对）：
- **`3x`（3倍消耗）**：`日本家宽·AWSJP·3倍消耗`、`台湾家宽·直连·3倍消耗`、`台湾家宽·AWSJP·3倍消耗`、`香港家宽·直连·3倍消耗`（注：香港不可用于 AGY）
- **`5x`（5倍消耗）**：`美国住宅·直连·5倍消耗`、`美国住宅·AWSJP·5倍消耗`、`美国住宅·AWSSG·5倍消耗`
- **`1x`（1倍消耗）**：其余 13 个节点，仅允许在 `🚀 节点选择` / `♻️ 自动选择` / `🔯 故障转移` 中使用

## 快速修复（最常见路径）

```bash
# 1) 看 AGY 组现在指向谁
SECRET=$(sed -n 's/^secret:[[:space:]]*"\?\([^"]*\)"\?.*/\1/p' ~/.config/mihomo/config.yaml | head -1)
curl -s --noproxy '*' -H "Authorization: Bearer $SECRET" http://127.0.0.1:9090/proxies/AGY \
  | python3 -c 'import sys,json;print("now =",json.load(sys.stdin)["now"])'

# 2) 一键扫描并切换（默认优先试 3x，再试 5x，跳过香港和 1x）
bash ~/.agents/skills/mihomo-antigravity-fix/scripts/probe-and-fix.sh

# 3) 手动切换到已知可用 3x 节点（优先 3x，不可用再考虑 5x）
curl -s --noproxy '*' -X PUT -H "Authorization: Bearer $SECRET" -H 'Content-Type: application/json' \
  -d '{"name":"日本家宽·AWSJP·3倍消耗"}' http://127.0.0.1:9090/proxies/AGY

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
4. **扫描出口节点**：`scan-llm-agy.sh`（全量、不影响当前分流；加 `--fast` 用 HTTP 探针，可并发扫描；默认按 `3x → 5x` 顺序扫描并跳过 `1x` 与香港）
   或 `probe-and-fix.sh`（在 `AGY` 组内按 `3x → 5x` 顺序用真实 `agy` 验证，挑第一个返回 `PONG` 的节点）。**注意**：
   Antigravity 按每次连接的出口 IP 随机判定，同一节点时好时坏；单次 `LOCATION` 不下结论，
   同一节点**最多探测 3 次、≥2 次 PONG 才算通过**（快速探针同理：6 次里 ≥4 次 OK）。
5. **仍无节点可用** → 刷新 provider（`--refresh`）或更换/新增订阅（要**非机房/住宅/干净 IP**）。

## scan-llm-agy.sh 用法（全量扫描，默认 3x 优先、排除 1x 与香港）

```bash
S=~/.agents/skills/mihomo-antigravity-fix/scripts/scan-llm-agy.sh
bash $S                      # 真实 agy 扫描（默认只扫非 1x 非香港，3x -> 5x 排序）
bash $S --fast               # HTTP 快速探针（默认 4 路并发，判定与 agy 一致）
bash $S --fast --jobs 1      # 串行快速扫描
bash $S --fast --limit 3     # 冒烟测试：只扫前 3 个候选
bash $S --fast --nodes "日本家宽·AWSJP·3倍消耗,台湾家宽·直连·3倍消耗"
bash $S --fast --verify 3    # 快速扫完后，对前 3 个 PASS 节点补真实 agy 抽查
bash $S --include-1x         # 仅排查用：把 1x 节点也纳入扫描（不建议用于 AGY）
bash $S --include-hk         # 仅排查用：把香港节点也纳入扫描
bash $S --probe-count 8      # 快速模式每节点最多探测次数（默认 6）
bash $S --keep               # 扫描后保留临时组 LLM_SCAN / 端口 7891
```

- 扫描用临时 selector 组和本地监听端口：worker 1 用 `LLM_SCAN` / `7891`，后续 worker 用
  `LLM_SCAN_2`…`LLM_SCAN_8` / `7892`…`7898`。每个 worker 只改自己的 selector，避免并发时节点路由串线。
  **不动** `AGY` 组当前选择和正常分流；开始/结束自动注入/移除临时配置并重载
  （`PUT /configs?force=true`），结束时恢复扫描前的配置内容；`--keep` 才会保留临时配置。
- 默认模式判定：真实 `agy --print "reply with exactly PONG"`，每节点 ≤3 次、`PONG` ≥2 次 = PASS；
  `L`=LOCATION、`O`=超时/其他、`A`=登录态问题（连续 3 个 A 会中止）。
- `--fast` 判定：HTTP 探针，每节点最多 `--probe-count` 次（默认 6），OK ≥ ⌈2K/3⌉ = PASS
  （6 次里 ≥4 次）；`P`=OK、`L`=LOCATION、`N`=节点不通（首个探测即 N 直接判死节点，省时）。
- 结果落盘 `/tmp/opencode/agy_scan_<ts>.tsv|.log`。

## probe-fast.sh 用法（单节点秒级体检）

```bash
PF=~/.agents/skills/mihomo-antigravity-fix/scripts/probe-fast.sh
bash $PF --node "日本家宽·AWSJP·3倍消耗"            # 单节点体检；PASS 退出码 0，fail 退出码 1
bash $PF --node "台湾家宽·直连·3倍消耗" --count 6    # 指定探测次数
bash $PF --nodes "a,b"                               # 多节点
bash $PF --teardown                                  # 移除临时组 LLM_SCAN / 端口 7891
```

> `PF_CSE`（Antigravity 公开 OAuth client secret）不再硬编码在脚本里。需要刷新 token 时先
> `export PF_CSE=<secret>`；未设置时会退回使用 agy 自己未过期的 token。

## probe-and-fix.sh 用法

```bash
S=~/.agents/skills/mihomo-antigravity-fix/scripts/probe-and-fix.sh
bash $S                 # 探测 AGY 候选池（优先 3x，再 5x，跳过香港和 1x），命中即切换
bash $S --list          # 列出 AGY 当前选择与按 3x -> 5x 排序的候选节点
bash $S --nodes "日本家宽·AWSJP·3倍消耗,台湾家宽·直连·3倍消耗"
bash $S --dry-run       # 只扫描不切换
bash $S --refresh       # 先强制刷新所有 provider 再扫描
bash $S --verify        # 只做一次 agy 验证，不扫描
```

## 判定标准

- 成功：`agy --print "reply with exactly PONG"` 输出包含 `PONG`。
- 失败：输出包含 `location is not supported`（换节点）、`PERMISSION_DENIED` /
  `SUBSCRIPTION_REQUIRED`（账号资格/订阅问题，非代理）、超时（节点太慢，换）。

## 注意事项 / 易踩坑

- **倍率红线**：`🚀 节点选择`、`♻️ 自动选择`、`🔯 故障转移` 绝不能放行 `3x`/`5x` 节点；只有 `AGY` 允许倍率节点，且 `AGY` 优先用 `3x`、其次 `5x`、避免 `1x`。
- 所有对 9090 的 curl 都要 `--noproxy '*'`。
- 节点名里的地区 ≠ 真实出口；以实际探测结果为准。
- 不要把 `AGY` 组选中到香港/中国节点（国家本身不支持，必挂）。
- 订阅里混有非节点信息行（「官网：…」「永久流量:…」「剩余流量：…」等），脚本与 `exclude-filter` 会跳过。
- 修改 `config.yaml` 前先备份（`config.yaml.bak-YYYYmmddHHMMSS`），改完用 `mihomo -t -d ~/.config/mihomo` 校验后再重载。
