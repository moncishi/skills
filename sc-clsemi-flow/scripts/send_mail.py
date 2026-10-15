#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 注意: 必须用 /usr/bin/python3 (3.10, 含 ssl)；/usr/local/bin/python3 (3.8) 缺 _ssl 模块
"""send_mail.py - SMTP 邮件发送工具

凭证从同目录 mail.conf 读取（权限 600，不入库）。

用法:
  send_mail.py -s "主题" -b "正文"
  send_mail.py -s "主题" -f body.txt -t a@example.com,b@example.com
  send_mail.py -s "主题" -b "正文" -a log.txt -a diff.patch
"""

import argparse
import mimetypes
import os
import smtplib
import sys
from configparser import ConfigParser
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONF_FILE = os.path.join(SCRIPT_DIR, "mail.conf")
DEFAULT_TO = os.environ.get("MAIL_TO", "")  # 收件人由调用方经环境变量传入


def load_conf():
    if not os.path.exists(CONF_FILE):
        sys.exit("错误: 找不到配置文件 %s" % CONF_FILE)
    cp = ConfigParser()
    with open(CONF_FILE, encoding="utf-8") as f:
        cp.read_file(f)
    return {
        "host": cp.get("smtp", "host"),
        "port": cp.getint("smtp", "port"),
        "user": cp.get("smtp", "user"),
        "passwd": cp.get("smtp", "password"),
        "sender_name": cp.get("smtp", "sender_name", fallback="dev-flow"),
    }


def build_message(cfg, subject, body, to_list, attachments):
    msg = MIMEMultipart()
    msg["From"] = formataddr((str(Header(cfg["sender_name"], "utf-8")), cfg["user"]))
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for path in attachments:
        if not os.path.isfile(path):
            sys.exit("错误: 附件不存在 %s" % path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            if maintype == "text":
                part = MIMEText(f.read().decode("utf-8", "replace"), "plain", "utf-8")
            else:
                part = MIMEApplication(f.read(), _subtype=subtype)
        part["Content-Disposition"] = 'attachment; filename="%s"' % os.path.basename(path)
        msg.attach(part)
    return msg


def main():
    ap = argparse.ArgumentParser(description="通过 SMTP 发送邮件（凭证见 mail.conf）")
    ap.add_argument("-s", "--subject", required=True, help="主题")
    ap.add_argument("-b", "--body", default="", help="正文内容")
    ap.add_argument("-f", "--body-file", help="从文件读正文（与 -b 互斥）")
    ap.add_argument("-t", "--to", default=None,
                    help="收件人，逗号分隔（默认读环境变量 MAIL_TO）")
    ap.add_argument("-a", "--attach", action="append", default=[],
                    help="附件路径，可多次指定")
    args = ap.parse_args()

    if args.body and args.body_file:
        ap.error("-b 与 -f 只能用一个")
    body = args.body
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            body = f.read()

    raw_to = args.to if args.to is not None else DEFAULT_TO
    to_list = [x.strip() for x in raw_to.split(",") if x.strip()]
    if not to_list:
        ap.error("未指定收件人：用 -t 或设置环境变量 MAIL_TO")
    cfg = load_conf()
    msg = build_message(cfg, args.subject, body, to_list, args.attach)

    try:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=30) as srv:
            srv.login(cfg["user"], cfg["passwd"])
            srv.sendmail(cfg["user"], to_list, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        sys.exit("错误: SMTP 认证失败，请检查 mail.conf 中的账号与授权码")
    except Exception as e:
        sys.exit("错误: 发送失败 - %s" % e)
    print("已发送: %s -> %s" % (cfg["user"], ", ".join(to_list)))


if __name__ == "__main__":
    main()
