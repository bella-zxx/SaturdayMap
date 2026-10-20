#!/usr/bin/env python3
"""One-call Xiaohongshu feasibility test using TikHub's official Python SDK."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

from tikhub_probe import CASES, save_private, summarize


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument(
        "--out", type=Path, default=Path("/private/tmp/saturdaymap-tikhub")
    )
    args = parser.parse_args()

    try:
        from tikhub import TikHub
    except ImportError:
        print("未安装 TikHub 官方 Python SDK（tikhub）；没有发起请求。", file=sys.stderr)
        return 1

    token = os.environ.get("TIKHUB_API_KEY")
    if not token:
        if not sys.stdin.isatty():
            parser.error("请在交互式终端运行，私密输入 API Key")
        token = getpass.getpass("TikHub API Key（输入时不会显示）: ")
    token = token.strip()
    if not token:
        parser.error("API Key 不能为空")

    label, share_url = CASES[args.case]
    print(f"测试 Case {args.case}：{label}（官方 SDK，最多发起 1 次接口请求）")
    try:
        with TikHub(api_key=token, max_retries=0) as client:
            response = client.xiaohongshu_app_v2.get_image_note_detail(
                share_text=share_url
            )
    except Exception as exc:
        # SDK error strings may include request details; never print them or the key.
        print(
            f"请求未取得笔记数据；错误类型={type(exc).__name__}；"
            "请先核对 TikHub 调用次数和余额，不要自动重试。",
            file=sys.stderr,
        )
        return 1

    payload = response.model_dump(mode="json") if hasattr(response, "model_dump") else response
    if not isinstance(payload, dict):
        print("接口返回格式无法识别；没有保存响应。", file=sys.stderr)
        return 1

    raw_path = save_private(args.out, f"case-{args.case}-sdk-raw-", payload)
    summary = {"case": args.case, "source_url": share_url, **summarize(payload)}
    summary_path = save_private(args.out, f"case-{args.case}-sdk-summary-", summary)
    print(f"API code={summary['api_code']}；原始响应：{raw_path}")
    print(f"不含 API Key 的摘要：{summary_path}")
    return 0 if summary["api_code"] == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
