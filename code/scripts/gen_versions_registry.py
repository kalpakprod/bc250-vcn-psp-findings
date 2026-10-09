#!/usr/bin/env python3
"""Generate candidates/VERSIONS.md — the candidate registry.

Deterministic inventory: every root candidates/*.bin with sha256, manifest
presence, flash-package staging, and a curated status. Nested campaign trees
(d*/s*/clv-*/t44*/...) get one line each (they carry their own manifests).
Re-run after any build; hand edits go to OVERRIDES below, nowhere else.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAND = REPO / "candidates"
PKG = REPO / "firmware-flash-pkg"

# Curated ground truth: filename -> (status, note). Everything else is derived.
# Statuses: FLASHED-OK | FLASHED-HUNG | FLASHED-VERDICT-PENDING | STAGED |
# SUPERSEDED | PACKAGED | UNKNOWN | ORPHAN. Only assert what this project verified.
# PACKAGED = basename found in some SHA256SUMS (package may be old); STAGED is
# reserved for curated next-up images in OVERRIDES.
# List + dup guard: a literal dict would silently collapse a repeated
# filename (bit us twice on 2026-09-24: STUB-app, safe-reads).
_OVERRIDE_PAIRS = [
    # Plain-name canon since 2026-09-24 (MISTAKES.md): filename says what is
    # inside; the old vNN tag survives only as the "alias" in .build.json.
    (
        "SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.bin",
        ("FLASHED-HUNG", "1 blink only; DEPEX-less driver (2026-09-24)"),
    ),
    (
        "BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin",
        ("FLASHED-HUNG", "1 blink only; unknown LZMA size (2026-09-24)"),
    ),
    (
        "BC250_vcn-driver-FULL_lzma-FIXED_early-slot.bin",
        ("FLASHED-HUNG", "2 blinks, no LAN/video; LZMA fixed, DXE wedge (2026-09-24)"),
    ),
    (
        "SUPERSEDED-BC250_pre_dump_vcn_own_fv_v006_noop.bin",
        (
            "SUPERSEDED",
            "by STUB_no-hw-ops_early-slot (audit F1 stale File-checksum); never flashed)",
        ),
    ),
    (
        "BC250_vcn-driver-STUB_no-hw-ops_early-slot.bin",
        (
            "FLASHED-OK",
            "BOOTS to Linux 2026-09-24 (kernel 7.2.6-1.206-cachyos-bc250, amdgpu up); DXE completes, insertion surgery innocent)",
        ),
    ),
    (
        "SUPERSEDED-BC250_pre_dump_vcn_noop_append_v007.bin",
        (
            "SUPERSEDED",
            "by STUB_no-hw-ops_appended-at-end (inherited F1); never flashed)",
        ),
    ),
    (
        "BC250_vcn-driver-FULL_lzma-FIXED_appended-at-end.bin",
        (
            "FLASHED-HUNG",
            "1 blink only, no LAN/video (2026-09-24); pre-dispatch signature, FV statically valid)",
        ),
    ),
    (
        "BC250_vcn-driver-STUB_no-hw-ops_appended-at-end.bin",
        (
            "FLASHED-OK",
            "BOOTS to Linux 2026-09-24; H19 WINS: append structure fine, FULL code wedges only late)",
        ),
    ),
    (
        "BC250_vcn-driver-FULL_safe-reads-only_appended-at-end.bin",
        (
            "STAGED",
            "NEXT: flash now (H19: code wedges late; tests raw reads as the stuck mechanism)",
        ),
    ),
    (
        "BC250_vcn-driver-FULL_deferred-to-readyboot_appended-at-end.bin",
        ("STAGED", "flash IF safe-reads hangs (FULL-app hung, STUB-app boots)"),
    ),
]
OVERRIDES: dict[str, tuple[str, str]] = {}
for _k, _v in _OVERRIDE_PAIRS:
    assert _k not in OVERRIDES, f"duplicate OVERRIDES key: {_k}"
    OVERRIDES[_k] = _v


def sha12(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:12]


def staged_names() -> set[str]:
    out = set()
    if PKG.is_dir():
        for s in PKG.glob("*/SHA256SUMS"):
            for ln in s.read_text().splitlines():
                parts = ln.split()
                if len(parts) == 2:
                    out.add(parts[1])
    return out


def main() -> int:
    staged = staged_names()
    bins = sorted(CAND.glob("*.bin"))
    rows = []
    for b in bins:
        man = b.with_suffix(".build.json")
        has_man = man.exists()
        variant = ""
        if has_man:
            try:
                variant = json.loads(man.read_text()).get("variant", "")
            except Exception:
                variant = "UNPARSEABLE"
        ov = OVERRIDES.get(b.name)
        if ov:
            status, note = ov
        elif not has_man:
            status, note = (
                "ORPHAN",
                "no .build.json; provenance in action-logs (unmapped)",
            )
        elif b.name in staged:
            status, note = "PACKAGED", "basename in a flash package (age unknown)"
        else:
            status, note = "UNKNOWN", "manifest exists; outcome unmapped (see U-C2)"
        rows.append((b.name, sha12(b), b.stat().st_size, variant, status, note))

    trees = []
    for d in sorted(p for p in CAND.iterdir() if p.is_dir()):
        nbin = sum(1 for _ in d.rglob("*.bin"))
        man = "manifest" if list(d.glob("*manifest*.json")) else "no-manifest"
        trees.append((d.name, nbin, man))

    L = []
    L.append("# Candidate registry (GENERATED — do not hand-edit)")
    L.append("")
    L.append(
        f"Generated {date.today().isoformat()} by `scripts/gen_versions_registry.py`."
    )
    L.append(
        "Curated statuses live in that script's OVERRIDES dict; everything else is derived."
    )
    L.append(
        "Naming convention for NEW builds: `docs/RELEASES.md`. Old names are frozen history."
    )
    L.append("")
    L.append(f"## Root images ({len(rows)} files)")
    L.append("")
    L.append("| file | sha12 | size | variant | status | note |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        L.append("| %s | %s | %d | %s | %s | %s |" % r)
    L.append("")
    L.append(f"## Campaign trees ({len(trees)} dirs)")
    L.append("")
    L.append("| dir | .bin inside | manifest |")
    L.append("|---|---|---|")
    for t in trees:
        L.append("| %s | %d | %s |" % t)
    (CAND / "VERSIONS.md").write_text("\n".join(L) + "\n")
    orphans = sum(1 for r in rows if r[4] == "ORPHAN")
    print(f"registry: {len(rows)} root images ({orphans} orphans), {len(trees)} trees")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
