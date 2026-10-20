#!/usr/bin/env python3
"""Test one user-provided Xiaohongshu share link with TikHub App V2."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ENDPOINT = "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/get_image_note_detail"
CASES = {
    "01": ("巨富长半日逛吃", "https://xhslink.cn/o/2HAggjcl6B9"),
    "02": ("上海邮政博物馆", "https://xhslink.cn/o/70UIcO0TOQM"),
    "03": ("上海 City Walk 七条线路", "https://xhslink.cn/o/5QWTrTolxTI"),
}


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def summarize(payload: object) -> dict:
    candidates: dict[str, list[dict]] = {"titles": [], "descriptions": [], "images": []}

    def walk(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in ("title", "note_title") and isinstance(child, str) and child:
                    candidates["titles"].append({"path": child_path, "value": child[:120]})
                if key in ("desc", "description", "content") and isinstance(child, str) and child:
                    candidates["descriptions"].append(
                        {"path": child_path, "length": len(child)}
                    )
                if key in ("image_list", "images_list", "imageList", "images") and isinstance(child, list):
                    candidates["images"].append({"path": child_path, "count": len(child)})
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    data = payload.get("data") if isinstance(payload, dict) else None
    walk(data, "data")
    return {
        "api_code": payload.get("code") if isinstance(payload, dict) else None,
        "api_message": payload.get("message") if isinstance(payload, dict) else None,
        "data_type": type(data).__name__,
        "titles": candidates["titles"][:5],
        "descriptions": sorted(
            candidates["descriptions"], key=lambda item: item["length"], reverse=True
        )[:5],
        "images": sorted(
            candidates["images"], key=lambda item: item["count"], reverse=True
        )[:5],
    }


def save_private(directory: Path, prefix: str, payload: object) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json", prefix=prefix, dir=directory,
        delete=False,
    ) as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
        return Path(file.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES, help="Run exactly one request")
    parser.add_argument(
        "--out", type=Path, default=Path("/private/tmp/saturdaymap-tikhub")
    )
    args = parser.parse_args()

    token = os.environ.get("TIKHUB_API_KEY")
    if not token:
        if not sys.stdin.isatty():
            parser.error("Set TIKHUB_API_KEY or run in an interactive terminal")
        token = getpass.getpass("TikHub API Key（输入时不会显示）: ")
    token = token.strip()
    if not token:
        parser.error("API Key cannot be empty")

    label, share_url = CASES[args.case]
    url = ENDPOINT + "?" + urllib.parse.urlencode({"share_text": share_url})
    request = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    )
    print(f"测试 Case {args.case}：{label}（本次仅调用 1 次接口，可能消耗额度）")
    try:
        opener = urllib.request.build_opener(NoRedirects())
        with opener.open(request, timeout=45) as response:
            body = response.read(10_000_001)
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read(10_000_001)
        status = exc.code
    except urllib.error.URLError as exc:
        print(f"网络请求失败：{exc.reason}", file=sys.stderr)
        return 1

    if len(body) > 10_000_000:
        print("响应超过 10 MB，未保存。", file=sys.stderr)
        return 1
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        print(f"HTTP {status}，响应不是 JSON；未保存原始内容。", file=sys.stderr)
        return 1

    raw_path = save_private(args.out, f"case-{args.case}-raw-", payload)
    summary = {
        "case": args.case,
        "source_url": share_url,
        "http_status": status,
        **summarize(payload),
    }
    summary_path = save_private(args.out, f"case-{args.case}-summary-", summary)
    print(f"HTTP {status}；API code={summary['api_code']}；原始响应：{raw_path}")
    print(f"不含 API Key 的摘要：{summary_path}")
    return 0 if status == 200 and summary["api_code"] == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
