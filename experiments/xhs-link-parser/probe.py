#!/usr/bin/env python3
"""Probe public Xiaohongshu URLs without bypassing access controls."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.metadata: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        values = dict(attrs)
        name = values.get("property") or values.get("name")
        content = values.get("content")
        if name and content:
            self.metadata[name.lower()] = content


def inspect_initial_state(html: str, final_url: str) -> dict:
    marker = "window.__INITIAL_STATE__="
    start = html.find(marker)
    if start < 0:
        return {"present": False}

    try:
        state, _ = json.JSONDecoder().raw_decode(html[start + len(marker) :])
    except json.JSONDecodeError as exc:
        return {"present": True, "parse_error": str(exc)}

    note_id_match = re.search(r"/(?:item|explore)/([a-f0-9]+)", urlparse(final_url).path)
    note_id = note_id_match.group(1) if note_id_match else None
    descriptions = []
    image_lists = []

    def walk(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in ("desc", "description") and isinstance(child, str) and child:
                    descriptions.append({"path": child_path, "length": len(child)})
                if key in ("imageList", "images") and isinstance(child, list):
                    image_lists.append({"path": child_path, "count": len(child)})
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(state, "state")
    note_descriptions = [
        item for item in descriptions if note_id and note_id in item["path"]
    ]
    note_images = [item for item in image_lists if note_id and note_id in item["path"]]
    return {
        "present": True,
        "parse_error": None,
        "note_id": note_id,
        "top_level_keys": list(state) if isinstance(state, dict) else [],
        "note_descriptions": note_descriptions[:10],
        "note_image_lists": note_images[:10],
        "other_description_count": len(descriptions) - len(note_descriptions),
        "other_image_list_count": len(image_lists) - len(note_images),
    }


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
            final_url = response.geturl()
            meta_parser = MetaParser()
            meta_parser.feed(text)
            title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
            page_path = urlparse(final_url).path
            page_kind = (
                "login"
                if page_path == "/login"
                else "unavailable"
                if page_path == "/404"
                else "note"
                if "/discovery/item/" in page_path or "/explore/" in page_path
                else "other"
            )
            return {
                "input_url": url,
                "final_url": final_url,
                "status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "bytes_read": len(body),
                "title": re.sub(r"\s+", " ", title_match.group(1)).strip()
                if title_match
                else None,
                "page_kind": page_kind,
                "metadata": {
                    "description_length": len(
                        meta_parser.metadata.get("og:description")
                        or meta_parser.metadata.get("description", "")
                    )
                    if page_kind == "note"
                    else 0,
                    "has_og_image": page_kind == "note"
                    and bool(meta_parser.metadata.get("og:image")),
                },
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
                "initial_state": inspect_initial_state(text, final_url)
                if page_kind == "note"
                else None,
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
        print(
            f"{path}: status={result.get('status')} "
            f"page={result.get('page_kind', 'error')} "
            f"error={result.get('error') or 'none'}"
        )


if __name__ == "__main__":
    main()
