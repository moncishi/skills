#!/usr/bin/env python3
"""MCP HTTP 调用助手：从 stdin 读工具参数 JSON，调用 PC 侧 ica-mcp-tools。

用法:
  echo '{"action":"status"}' | python3 <本脚本> tftp_control
  echo '{"connection_id":"serial://COM20:9600","timeout_s":60}' | python3 <本脚本> serial_read
  echo '<args-json>' | python3 <本脚本> serial_expect_send 300   # 第二参数=超时秒
输出: structuredContent（或 content）的 JSON。MCP_URL 环境变量可覆盖默认地址。
"""
import json
import os
import sys
import urllib.request

URL = os.environ.get("MCP_URL", "http://172.21.53.161:3456/mcp")


def call(tool, args, timeout):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }).encode()
    req = urllib.request.Request(URL, data=payload, headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", "replace")
    for line in body.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    return None


def main():
    tool = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    raw = sys.stdin.read().strip()
    args = json.loads(raw) if raw else {}
    r = call(tool, args, timeout + 30) or {}
    result = r.get("result", {})
    out = result.get("structuredContent") or result.get("content") or {}
    print(json.dumps(out, ensure_ascii=False))
    if result.get("isError"):
        sys.exit(1)


if __name__ == "__main__":
    main()
