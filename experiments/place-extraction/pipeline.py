#!/usr/bin/env python3
"""Prepare a TikHub note and validate grounded place extraction output.

No model or paid API is called by this script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")


def prepare(raw: dict, source_url: str) -> dict:
    parsed_url = urlparse(source_url)
    if parsed_url.scheme != "https" or parsed_url.hostname not in {
        "xhslink.cn", "xhslink.com", "www.xiaohongshu.com", "xiaohongshu.com"
    }:
        raise ValueError("source_url must be an HTTPS Xiaohongshu share URL")
    if raw.get("code") != 200:
        raise ValueError("TikHub API did not return code=200")
    envelope = raw.get("data")
    if not isinstance(envelope, dict) or envelope.get("success") is not True or envelope.get("code") != 0:
        raise ValueError("TikHub did not return a successful note payload")
    groups = envelope.get("data")
    if not isinstance(groups, list) or not groups:
        raise ValueError("note group is missing")
    notes = groups[0].get("note_list") if isinstance(groups[0], dict) else None
    if not isinstance(notes, list) or not notes or not isinstance(notes[0], dict):
        raise ValueError("note_list is missing")
    note = notes[0]
    title, body, note_id = note.get("title"), note.get("desc"), note.get("id")
    if not all(isinstance(value, str) and value.strip() for value in (title, body, note_id)):
        raise ValueError("note title, body or ID is missing")
    images = note.get("images_list")
    image_urls = [item["url"] for item in images if isinstance(item, dict) and isinstance(item.get("url"), str) and item["url"]] if isinstance(images, list) else []
    return {
        "note_id": note_id,
        "title": title,
        "body": body,
        "source_url": source_url,
        "image_urls": image_urls,
    }


def validate(note: dict, result: dict) -> list[str]:
    errors: list[str] = []
    text = "\n".join((str(note.get("title", "")), str(note.get("body", ""))))
    places = result.get("places")
    if not isinstance(places, list):
        return ["places must be an array"]
    if len(places) > 50:
        errors.append("places must contain no more than 50 items")
    seen: set[str] = set()
    for index, place in enumerate(places):
        prefix = f"places[{index}]"
        if not isinstance(place, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("place_name", "city", "place_kind", "evidence", "recommendation", "source_url"):
            if not isinstance(place.get(key), str):
                errors.append(f"{prefix}.{key} must be a string")
        name = place.get("place_name")
        if isinstance(name, str):
            if not name.strip() or name.casefold() not in text.casefold():
                errors.append(f"{prefix}.place_name is not present in the note")
            if name.casefold() in seen:
                errors.append(f"{prefix}.place_name is duplicated")
            seen.add(name.casefold())
        if place.get("place_kind") not in ("poi", "street", "area"):
            errors.append(f"{prefix}.place_kind must be poi, street or area")
        if place.get("source_url") != note.get("source_url"):
            errors.append(f"{prefix}.source_url does not match the original share URL")
        for key in ("evidence", "recommendation"):
            value = place.get(key)
            if isinstance(value, str) and value and value not in text:
                errors.append(f"{prefix}.{key} is not a verbatim excerpt")
        if not place.get("evidence"):
            errors.append(f"{prefix}.evidence is required")
        elif isinstance(name, str) and isinstance(place.get("evidence"), str) and name.casefold() not in place["evidence"].casefold():
            errors.append(f"{prefix}.evidence must contain the place name")
        features = place.get("features")
        if not isinstance(features, list) or any(not isinstance(value, str) or not value or value not in text for value in features):
            errors.append(f"{prefix}.features must be an array of verbatim excerpts")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subcommands.add_parser("prepare")
    prepare_parser.add_argument("raw", type=Path)
    prepare_parser.add_argument("--source-url", required=True)
    prepare_parser.add_argument("--out", type=Path, required=True)
    validate_parser = subcommands.add_parser("validate")
    validate_parser.add_argument("note", type=Path)
    validate_parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            note = prepare(read_json(args.raw), args.source_url)
            write_json(args.out, note)
            print(f"prepared note {note['note_id']}: {len(note['body'])} chars, {len(note['image_urls'])} image URLs")
            return 0
        errors = validate(read_json(args.note), read_json(args.result))
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("extraction passed grounding checks")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
