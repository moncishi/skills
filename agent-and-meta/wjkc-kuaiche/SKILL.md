---
name: wjkc-kuaiche
description: 网际快车（wjkc / 快车 / 任意.快车.com）机场账户操作：登录、每日签到、查询剩余流量和流量消耗（按日、按节点）。当用户说“快车签到”“查快车流量”“快车流量怎么用掉的”时使用。
---

# 网际快车（wjkc）操作指南

## 环境事实

- 官网域名：`任意.快车.com`（Punycode：`xn--boqq45b.xn--66tw07h.com`）
- 面板与订阅域名：`https://p1x.wjkc.xyz`
- 本机 mihomo 配置：`~/.config/mihomo/config.yaml` 中的 `proxy-providers.wjkc`
- **代理要求**：当前网络存在 Fortinet SSL 拦截，直连会被拦；必须通过本机 mihomo 代理 `http://127.0.0.1:7890` 访问。
- **Agent 沙箱提醒**：若在沙箱中调用脚本，执行网络命令时需设置 `BypassSandbox: true`。

## 凭据设置

脚本不包含内置账号密码，使用前请通过环境变量或 `--email` / `--password` 参数提供：

```bash
export WJKC_EMAIL="your@example.com"
export WJKC_PASSWORD="your_password"
```

可选覆盖环境变量：`WJKC_BASE`（默认 `https://p1x.wjkc.xyz`）、`WJKC_PROXY`（默认 `http://127.0.0.1:7890`）。

## 常用命令

```bash
# 查看账户与剩余额度
python3 scripts/wjkc.py info

# 每日签到（已签到时不会重复请求签到接口）
python3 scripts/wjkc.py sign

# 查询流量消耗（默认最近 30 天 + 节点分布；可用 --no-chart 仅看每日）
python3 scripts/wjkc.py traffic --days 14

# 查询签到历史
python3 scripts/wjkc.py sign-records

# 输出原始解码 JSON（适合程序解析）
python3 scripts/wjkc.py --json traffic --days 10
```

## API 协议摘要

- 所有接口均为 `POST`，请求体格式：`{"data": "<base64(compact_json)>"}`，带 `Content-Type: application/json`、`Origin`/`Referer` 及浏览器 `User-Agent`，使用 Cookie 维持会话。
- 响应格式：`{"data": "<base64url>"}`（替换 `-`/`_` 并补 `=` 后解码为 `{"code", "msg", "data"}`；`code == 0` 表示成功，`1002` 表示登录过期）。
- 主要端点与单位：
  - `/api/user/login`：`{"email", "password": md5(明文)}`
  - `/api/user/userinfo` `{}`：永久/月/时长包额度字段单位为 **bytes**
  - `/api/user/sign_use_info` `{}`：签到奖励配置单位为 **MB**
  - `/api/user/sign_use` `{}`：`addTraffic` 单位为 **bytes**
  - `/api/user/sign_use_records` `{"limit": 200}`
  - `/api/traffic/my_traffic_records` `{"page": 1, "pageSize": N}`：`trafficChange` 单位为 **bytes**（消耗为负）
  - `/api/traffic/my_traffic_chart` `{}`：`series[].total` 与 `points[][1]` 单位为 **GB**

## 注意事项

- **倍率计费**：部分节点名称带有倍率标记（如 `美国住宅·直连·5倍消耗`），流量图与记录中的数值均为**按倍率计费后**的流量。
- **签到规则**：每日签到基础奖励 `200 MB`，连续签到 `30` 天额外奖励 `1024 MB`；仅付费用户（`paidUser: true`）可签到。
- **前端限制对比**：网页前端通过本地 cookie `last-signUse-time` 限制同设备一天只签一个账号，本 CLI 直接调用接口不受该本地限制影响。
