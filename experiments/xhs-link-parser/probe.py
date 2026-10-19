#!/usr/bin/env python3
"""Probe public Xiaohongshu URLs without bypassing access controls."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


def probe(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9"},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(5_000_000)
            text = body.decode("utf-8", errors="replace")
            title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
            return {
                "input_url": url,
                "final_url": response.geturl(),
                "status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "bytes_read": len(body),
                "title": re.sub(r"\s+", " ", title_match.group(1)).strip()
                if title_match
                else None,
                "signals": {
                    "has_initial_state": any(
                        token in text
                        for token in ("__INITIAL_STATE__", "window.__INITIAL_STATE__")
                    ),
                    "has_note_desc": any(
                        token in text for token in ('"desc"', "noteDetail", "noteData")
                    ),
                    "has_image_url": any(
                        token in text for token in ("imageList", "urlDefault", "og:image")
                    ),
                    "looks_like_login_or_block": any(
                        token in text for token in ("登录", "验证码", "访问频繁", "安全验证")
                    ),
                },
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "error": None,
            }
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {
            "input_url": url,
            "final_url": None,
            "status": getattr(exc, "code", None),
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "error": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(args.urls, start=1):
        result = probe(url)
        path = args.out / f"case-{index:02d}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"{path}: {result.get('status')} {result.get('final_url') or result.get('error')}")


if __name__ == "__main__":
    main()
