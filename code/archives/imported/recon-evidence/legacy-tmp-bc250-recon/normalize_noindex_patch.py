#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def normalize_header(line: str) -> str:
    normalized = line.lstrip("\ufeff").replace("\\", "/")
    diff = re.fullmatch(r'diff --git (?:"a/)?(?:a/)?[^ ]*/drivers/(.+?)(?:")? (?:"b/)?(?:b/)?[^ ]*/drivers/(.+?)(?:")?', normalized)
    if diff:
        return f"diff --git a/drivers/{diff.group(1)} b/drivers/{diff.group(2)}"
    for marker, side in (("--- ", "a"), ("+++ ", "b")):
        if not normalized.startswith(marker):
            continue
        path = normalized[len(marker):].strip('"')
        match = re.fullmatch(rf"{side}/.*/drivers/(.+)", path)
        if match:
            return f"{marker}{side}/drivers/{match.group(1)}"
        if f"/{side}/" in path or "/drivers/" in path:
            raise SystemExit(f"cannot normalize patch header: {line}")
    return normalized


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} INPUT OUTPUT")
    source = Path(sys.argv[1]).read_text(encoding="utf-8")
    lines = [normalize_header(line) for line in source.splitlines()]
    output = "\n".join(lines) + "\n"
    forbidden = ("vcn-probe-base", "vcn-probe-new", "tmp_bc250")
    if any(token in output for token in forbidden):
        raise SystemExit("normalized patch retains workspace prefixes")
    Path(sys.argv[2]).write_text(output, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
