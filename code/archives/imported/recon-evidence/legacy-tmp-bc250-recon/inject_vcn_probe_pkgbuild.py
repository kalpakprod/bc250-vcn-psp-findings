#!/usr/bin/env python3
"""Inject the VCN probe patch into a freshly generated BC250 PKGBUILD."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


QUOTED_ITEM_RE = re.compile(r"(['\"])(?:\\.|(?!\1)[\s\S])*\1")
PREPARE_PATCH_ANCHOR_RE = re.compile(
    r'^([ \t]*)src="\$\{src%\.zst\}"\n\1\[\[ \$src = \*\.patch \]\] \|\| continue$',
    re.MULTILINE,
)
AUDIO_PATCH_SKIP_RE = re.compile(
    r'^[ \t]*\[\[ \$src == 0002-bc250-audio\.patch \]\] && continue$', re.MULTILINE
)


def fail(message: str) -> None:
    raise ValueError(message)


def exact_anchor_once(text: str, anchor: str) -> None:
    if len(re.findall(rf"^{re.escape(anchor)}(?=\n|\Z)", text, re.MULTILINE)) != 1:
        fail(f"expected exactly one {anchor!r} anchor")


def prepare_patch_anchor_once(text: str) -> re.Match[str]:
    matches = list(PREPARE_PATCH_ANCHOR_RE.finditer(text))
    if len(matches) != 1:
        fail("expected exactly one prepare patch-loop anchor")
    if AUDIO_PATCH_SKIP_RE.search(text):
        fail("BC-250 audio patch skip is already present")
    return matches[0]


def array_match(text: str, name: str) -> tuple[int, int]:
    openers = list(re.finditer(rf"^{re.escape(name)}=\(", text, re.MULTILINE))
    if len(openers) != 1:
        fail(f"expected exactly one {name} array opener")

    body_start = openers[0].end()
    single_quoted = False
    double_quoted = False
    index = body_start
    while index < len(text):
        char = text[index]
        if single_quoted:
            if char == "'":
                single_quoted = False
        elif double_quoted:
            if char == "\\":
                index += 1
            elif char == '"':
                double_quoted = False
        elif char == "'":
            single_quoted = True
        elif char == '"':
            double_quoted = True
        elif char == ")":
            return body_start, index
        index += 1

    fail(f"unterminated {name} array")


def quoted_items(body: str) -> list[str]:
    return [match.group(0) for match in QUOTED_ITEM_RE.finditer(body)]


def shell_quote(value: str) -> str:
    return '"' + re.sub(r'([\\"$`])', r'\\\1', value) + '"'


def append_array_item(text: str, name: str, item: str) -> str:
    body_start, body_end = array_match(text, name)
    body = text[body_start:body_end]
    indents = re.findall(r"(?m)^([ \t]+)(?=['\"])", body)
    indent = indents[-1] if indents else "  "
    separator = "" if body.endswith("\n") else "\n"
    return text[:body_end] + f"{separator}{indent}{item}\n" + text[body_end:]


def insert_before_last_quoted_array_item(text: str, name: str, item: str) -> str:
    body_start, body_end = array_match(text, name)
    body = text[body_start:body_end]
    items = list(QUOTED_ITEM_RE.finditer(body))
    if not items:
        fail(f"{name} must contain at least one quoted item")

    last_item = items[-1]
    line_start = body.rfind("\n", 0, last_item.start()) + 1
    indent = re.match(r"[ \t]*", body[line_start:last_item.start()]).group(0)
    separator = "\n" if line_start == 0 else ""
    insertion = f"{separator}{indent}{item}\n"
    insert_at = body_start + line_start
    return text[:insert_at] + insertion + text[insert_at:]


def inject(pkgbuild: Path, patches: list[Path]) -> tuple[int, int]:
    text = pkgbuild.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    patch_names = [patch.name for patch in patches]
    if any(not name for name in patch_names):
        fail("PATCH must name a readable file")
    if len(set(patch_names)) != len(patch_names):
        fail("PATCH basenames must be unique")

    checksums: list[str] = []
    for patch, patch_name in zip(patches, patch_names):
        if not patch.is_file():
            fail(f"patch {patch_name!r} must name a readable file")
        try:
            checksums.append(hashlib.blake2b(patch.read_bytes()).hexdigest())
        except OSError as error:
            fail(f"patch {patch_name!r} must name a readable file: {error}")
        if patch_name in text:
            fail(f"patch {patch_name!r} is already present")

    suffix_anchor = '_pkgsuffix="cachyos-bc250"'
    pkgbase_anchor = 'pkgbase="linux-$_pkgsuffix"'
    pkgrel_anchor = "pkgrel=1.1"
    for anchor in (suffix_anchor, pkgbase_anchor, pkgrel_anchor):
        exact_anchor_once(text, anchor)
    prepare_anchor = prepare_patch_anchor_once(text)

    prepare_insert_at = prepare_anchor.end()
    text = (
        text[:prepare_insert_at]
        + f"\n{prepare_anchor.group(1)}[[ $src == 0002-bc250-audio.patch ]] && continue"
        + text[prepare_insert_at:]
    )

    source_before = array_match(text, "source")
    sums_before = array_match(text, "b2sums")
    source_items_before = quoted_items(text[source_before[0] : source_before[1]])
    sum_items_before = quoted_items(text[sums_before[0] : sums_before[1]])
    if not sum_items_before:
        fail("b2sums must contain at least one quoted item")

    source_items = [shell_quote(patch_name) for patch_name in patch_names]
    checksum_items = [shell_quote(checksum) for checksum in checksums]
    source_index = len(source_items_before)
    checksum_index = len(sum_items_before) - 1

    for source_item in source_items:
        text = append_array_item(text, "source", source_item)
    for checksum_item in checksum_items:
        text = insert_before_last_quoted_array_item(text, "b2sums", checksum_item)
    text = text.replace(suffix_anchor, '_pkgsuffix="cachyos-vcn-bc250"', 1)
    text = text.replace(pkgrel_anchor, "pkgrel=1.92", 1)

    source_after_span = array_match(text, "source")
    sums_after_span = array_match(text, "b2sums")
    source_after = quoted_items(text[source_after_span[0] : source_after_span[1]])
    sums_after = quoted_items(text[sums_after_span[0] : sums_after_span[1]])
    if (
        len(source_after) != len(source_items_before) + len(source_items)
        or len(sums_after) != len(sum_items_before) + len(checksum_items)
        or source_after[source_index : source_index + len(source_items)] != source_items
        or sums_after[checksum_index : checksum_index + len(checksum_items)] != checksum_items
        or sums_after[-1] != sum_items_before[-1]
    ):
        fail("source and b2sums insertion validation failed")

    pkgbuild.write_bytes(text.encode("utf-8"))
    return source_index, checksum_index


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(f"usage: {Path(argv[0]).name} PKGBUILD PATCH [PATCH ...]", file=sys.stderr)
        return 2
    try:
        patches = [Path(patch) for patch in argv[2:]]
        source_index, checksum_index = inject(Path(argv[1]), patches)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(
        f"VCN_PROBE_PKGBUILD_PASS patches={len(patches)} "
        f"source_start={source_index} checksum_start={checksum_index}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
