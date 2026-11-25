#!/usr/bin/env python3
"""网际快车（wjkc）CLI：登录、每日签到、账户额度与流量消耗查询。"""

import argparse
import base64
import hashlib
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

DEFAULT_BASE = "https://p1x.wjkc.xyz"
DEFAULT_PROXY = "http://127.0.0.1:7890"
DEFAULT_EMAIL = ""
DEFAULT_PASSWORD = ""
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
TZ_CN = timezone(timedelta(hours=8))


def format_bytes(num_bytes: float) -> str:
    """将字节数自动格式化为 MB 或 GB（保留两位小数）。"""
    abs_val = abs(num_bytes)
    if abs_val >= 1024 ** 3:
        return f"{num_bytes / (1024 ** 3):.2f} GB"
    return f"{num_bytes / (1024 ** 2):.2f} MB"


def format_ts_ms(ts_ms) -> str:
    """将毫秒时间戳或 ISO 时间格式化为本地可读时间。"""
    if not ts_ms:
        return "-"
    if isinstance(ts_ms, (int, float)):
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=TZ_CN)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(ts_ms, str):
        try:
            dt = datetime.fromisoformat(ts_ms.replace("Z", "+00:00")).astimezone(TZ_CN)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return ts_ms
    return str(ts_ms)


class WjkcClient:
    """网际快车 API 客户端（基于标准库 urllib + CookieJar）。"""

    def __init__(self, base_url: str, proxy_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.proxy_url = proxy_url.strip()
        self.cj = http.cookiejar.CookieJar()
        handlers = [urllib.request.HTTPCookieProcessor(self.cj)]
        if self.proxy_url:
            handlers.insert(
                0,
                urllib.request.ProxyHandler(
                    {"http": self.proxy_url, "https": self.proxy_url}
                ),
            )
        self.opener = urllib.request.build_opener(*handlers)

    def post(self, path: str, payload: dict) -> dict:
        """发送 base64 封包 POST 请求并解包返回 JSON。"""
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        b64 = base64.b64encode(raw).decode("ascii")
        body = json.dumps({"data": b64}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
            },
            method="POST",
        )
        try:
            with self.opener.open(req, timeout=20) as resp:
                resp_text = resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            proxy_hint = self.proxy_url or "(未使用代理)"
            raise RuntimeError(
                f"网络请求失败（{path}）：{exc}。请检查 mihomo 是否运行以及代理 {proxy_hint} 是否可用。"
            ) from exc

        try:
            outer = json.loads(resp_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"响应不是有效 JSON（{path}）：{resp_text[:200]}") from exc

        if isinstance(outer, dict) and isinstance(outer.get("data"), str):
            encoded = outer["data"].replace("-", "+").replace("_", "/")
            encoded += "=" * (-len(encoded) % 4)
            try:
                decoded = base64.b64decode(encoded).decode("utf-8")
                return json.loads(decoded)
            except Exception as exc:
                raise RuntimeError(f"响应 data 字段解码失败（{path}）：{exc}") from exc
        return outer

    def login(self, email: str, password: str) -> dict:
        """使用邮箱和明文密码（MD5 后提交）登录。"""
        pw_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        res = self.post("/api/user/login", {"email": email, "password": pw_md5})
        if res.get("code") != 0:
            msg = res.get("msg") or "未知错误"
            raise RuntimeError(f"登录失败（code={res.get('code')}）：{msg}")
        return res


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """按 命令行参数 -> 环境变量 -> 默认值 顺序解析邮箱和密码。"""
    email = args.email or os.environ.get("WJKC_EMAIL") or DEFAULT_EMAIL
    password = args.password or os.environ.get("WJKC_PASSWORD") or DEFAULT_PASSWORD
    if not email or not password:
        print(
            "错误：缺少账号或密码。\n"
            "请通过环境变量提供：\n"
            "  export WJKC_EMAIL='your@email.com'\n"
            "  export WJKC_PASSWORD='your_password'\n"
            "或通过参数 --email / --password 传入。",
            file=sys.stderr,
        )
        sys.exit(2)
    return email, password


def require_ok(res: dict, action: str) -> dict:
    """校验接口返回 code==0；1002 提示登录过期。"""
    code = res.get("code")
    if code == 0:
        return res.get("data") if res.get("data") is not None else {}
    msg = res.get("msg") or "未知错误"
    if code == 1002:
        raise RuntimeError(f"{action}失败：登录已过期（code=1002，{msg}）")
    raise RuntimeError(f"{action}失败（code={code}）：{msg}")


def cmd_info(client: WjkcClient, args: argparse.Namespace) -> int:
    res = client.post("/api/user/userinfo", {})
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("code") == 0 else 1

    data = require_ok(res, "获取用户信息")
    sub = data.get("subSummary") or {}
    perm = sub.get("permanent") or {}
    monthly = sub.get("monthly") or {}
    duration = sub.get("duration") or {}

    quota_gb = (perm.get("quotaBytes") or 0) / (1024 ** 3)
    used_gb = (perm.get("usedBytes") or 0) / (1024 ** 3)
    rem_gb = (perm.get("remainingBytes") or 0) / (1024 ** 3)

    print(f"邮箱：{data.get('email', '-')}")
    print(f"付费用户：{bool(data.get('paidUser'))}")
    print(
        f"永久包：总额 {quota_gb:.2f} GB | 已用 {used_gb:.2f} GB | 剩余 {rem_gb:.2f} GB"
    )
    print(
        f"月套餐 active：{bool(monthly.get('active'))} | 时长包 active：{bool(duration.get('active'))}"
    )
    print(f"今日已签到：{bool(data.get('signUseToday'))}")
    print(f"连续签到天数：{data.get('haveContinueSignUseData', 0)}")
    return 0


def cmd_sign(client: WjkcClient, args: argparse.Namespace) -> int:
    info_res = client.post("/api/user/userinfo", {})
    uinfo = require_ok(info_res, "获取用户信息")

    if not uinfo.get("paidUser"):
        msg = "付费用户才能签到"
        if args.json:
            print(json.dumps({"code": 1, "msg": msg, "data": {}}, ensure_ascii=False, indent=2))
        else:
            print(msg)
        return 1

    if uinfo.get("signUseToday"):
        if args.json:
            print(
                json.dumps(
                    {
                        "code": 0,
                        "msg": "今日已签到",
                        "data": {
                            "alreadySigned": True,
                            "haveContinueSignUseData": uinfo.get("haveContinueSignUseData", 0),
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"今日已签到（当前连续签到 {uinfo.get('haveContinueSignUseData', 0)} 天）")
        return 0

    sign_res = client.post("/api/user/sign_use", {})
    if sign_res.get("code") != 0:
        if args.json:
            print(json.dumps(sign_res, ensure_ascii=False, indent=2))
        else:
            print(f"签到失败：{sign_res.get('msg') or '未知错误'}")
        return 1

    after_res = client.post("/api/user/userinfo", {})
    after_uinfo = require_ok(after_res, "刷新用户信息")

    if args.json:
        print(
            json.dumps(
                {"sign": sign_res, "userinfo": after_uinfo},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    sdata = sign_res.get("data") or {}
    add_mb = (sdata.get("addTraffic") or 0) / (1024 ** 2)
    cont_days = sdata.get("haveContinueSignUseData", 0)
    extra = bool(sdata.get("extraReward"))
    perm = (after_uinfo.get("subSummary") or {}).get("permanent") or {}
    rem_gb = (perm.get("remainingBytes") or 0) / (1024 ** 3)

    print(
        f"签到成功：增加 {add_mb:.0f} MB | 连续签到 {cont_days} 天 | "
        f"额外奖励：{'是' if extra else '否'}"
    )
    print(f"当前永久包剩余额度：{rem_gb:.2f} GB")
    return 0


def cmd_traffic(client: WjkcClient, args: argparse.Namespace) -> int:
    rec_res = client.post(
        "/api/traffic/my_traffic_records", {"page": 1, "pageSize": args.days}
    )
    chart_res = client.post("/api/traffic/my_traffic_chart", {}) if args.chart else None

    if args.json:
        out = {"records": rec_res}
        if chart_res is not None:
            out["chart"] = chart_res
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if rec_res.get("code") == 0 else 1

    rec_data = require_ok(rec_res, "获取每日流量记录")
    rec_list = rec_data.get("list") or []
    print(f"=== 每日流量消耗（最近 {len(rec_list)} 条 / 共 {rec_data.get('total', 0)} 条）===")
    total_spend_bytes = 0.0
    for item in rec_list:
        day = item.get("day", "-")
        rtype = item.get("type", "-")
        change = float(item.get("trafficChange") or 0.0)
        spent = -change if change < 0 else change
        if rtype == "spend" or change < 0:
            total_spend_bytes += spent
        label = format_bytes(spent)
        print(f"  {day}  [{rtype}]  {label}")
    print(f"合计消耗：{format_bytes(total_spend_bytes)}")

    if chart_res is not None:
        chart_data = require_ok(chart_res, "获取节点流量分布")
        series = chart_data.get("series") or []
        series_sorted = sorted(
            series, key=lambda s: float(s.get("total") or 0.0), reverse=True
        )
        print("\n=== 节点流量分布（计费后，按总计降序）===")
        print(f"  {'节点':<18} | {'线路':<10} | {'消耗'}")
        print(f"  {'-' * 18}-+-{'-' * 10}-+-{'-' * 12}")
        for s in series_sorted:
            node = str(s.get("node") or "-")
            line = str(s.get("line") or "-")
            total_mb = float(s.get("total") or 0.0) * 1024.0
            print(f"  {node:<18} | {line:<10} | {total_mb:.2f} MB")
    return 0


def cmd_sign_records(client: WjkcClient, args: argparse.Namespace) -> int:
    res = client.post("/api/user/sign_use_records", {"limit": 200})
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("code") == 0 else 1

    data = require_ok(res, "获取签到记录")
    records = data if isinstance(data, list) else (data.get("list") or [])
    print(f"=== 签到记录（共 {len(records)} 条）===")
    for item in records:
        ts = item.get("createTime") or item.get("signTime") or item.get("time") or item.get("day")
        add_val = item.get("addTraffic") or item.get("traffic") or 0
        add_mb = float(add_val) / (1024 ** 2) if add_val else 0.0
        print(f"  {format_ts_ms(ts)}  +{add_mb:.0f} MB")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--base",
        default=argparse.SUPPRESS,
        help=f"面板 Base URL（默认 {DEFAULT_BASE}，或环境变量 WJKC_BASE）",
    )
    common.add_argument(
        "--proxy",
        default=argparse.SUPPRESS,
        help=f"HTTP 代理地址（默认 {DEFAULT_PROXY}，或环境变量 WJKC_PROXY）",
    )
    common.add_argument("--email", default=argparse.SUPPRESS, help="账号邮箱（或 WJKC_EMAIL）")
    common.add_argument("--password", default=argparse.SUPPRESS, help="账号密码（或 WJKC_PASSWORD）")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="输出原始 JSON")

    parser = argparse.ArgumentParser(
        description="网际快车（wjkc）命令行工具",
        parents=[common],
    )
    parser.set_defaults(
        base=os.environ.get("WJKC_BASE", DEFAULT_BASE),
        proxy=os.environ.get("WJKC_PROXY", DEFAULT_PROXY),
        email=None,
        password=None,
        json=False,
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", parents=[common], help="查询账户信息与剩余额度")
    sub.add_parser("sign", parents=[common], help="执行每日签到")

    p_traffic = sub.add_parser("traffic", parents=[common], help="查询每日与节点流量消耗")
    p_traffic.add_argument("--days", type=int, default=30, help="获取最近 N 条每日记录（默认 30）")
    p_traffic.add_argument(
        "--chart",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否同时输出节点流量分布（默认开启，可用 --no-chart 关闭）",
    )

    sub.add_parser("sign-records", parents=[common], help="查询签到历史记录")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    email, password = resolve_credentials(args)

    client = WjkcClient(args.base, args.proxy)
    try:
        client.login(email, password)
        if args.command == "info":
            return cmd_info(client, args)
        if args.command == "sign":
            return cmd_sign(client, args)
        if args.command == "traffic":
            return cmd_traffic(client, args)
        if args.command == "sign-records":
            return cmd_sign_records(client, args)
    except RuntimeError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
