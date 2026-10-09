#!/usr/bin/env python3
"""Independent verification of the BC-250 board voltage sources inventory.

Verified artifacts (produced by the dispatched builder):
    scan_vr_mailbox_writers.py
    vr-mailbox-writers-result.json

This verifier uses a different evidence path than the scanner:
  * the match set is re-derived from the pinned objdump text (`<stem>-0.asm`) with an
    independently written anchor conjunction over the disassembled byte stream;
  * every module image is located inside the immutable ROM by whole-image content
    search, not by census offset arithmetic;
  * every recorded anchor offset, helper entry, owned anchor and call site is re-read
    from the asm text at its RVA.

Read-only. Output: one JSON verdict document on stdout.
"""

import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
DONOR = os.path.join(ROOT, "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin")
CORPUS = os.path.join(ROOT, "evidence/firmware-audit/20260919-inv-token-consumers")
RESULT = os.path.join(HERE, "vr-mailbox-writers-result.json")
SCANNER = os.path.join(HERE, "scan_vr_mailbox_writers.py")

DONOR_SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
DONOR_SIZE = 16777216
CENSUS_SHA256 = "506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39"
EXPECTED_WRITERS = ["ISL69247-3e1f753a6279", "ISL95712-c0cc17d2d54f"]
SCANNER_SHA256 = "63ae081c8588f7a4bfdf1ebabe9c912238b347689781b4b66ff3e850f8a037d8"

VERIFY_GROUPS = [
    ("ec_data_window_base_a20", ["b9200a0000", "ba200a0000"]),
    ("ec_config_index_port_2e", ["6a2e", "e62e"]),
    ("ec_mailbox_staging_regs", ["6a65", "6a66", "6a60"]),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def asm_stream(stem):
    out = {}
    for line in open(os.path.join(CORPUS, stem + "-0.asm"), encoding="utf-8", errors="replace"):
        if ":\t" not in line:
            continue
        head, rest = line.split(":\t", 1)
        head = head.strip()
        if not re.fullmatch(r"[0-9a-f]+", head):
            continue
        fields = rest.split("\t")
        raw = fields[0].strip()
        if not raw:
            continue
        try:
            blob = bytes.fromhex(raw)
        except ValueError:
            continue
        out[int(head, 16)] = (blob, fields[1].strip() if len(fields) > 1 else "")
    return out


def site_bytes(stream, blob, off, d, pattern_hex):
    """Re-read one reported pattern offset against an independent evidence path.

    The scanner reports the offset of the matched pattern bytes; for operand-encoded
    anchors (e.g. `200a0000` inside `b9 20 0a 00 00`) that offset sits inside the
    instruction.  The asm text is keyed by instruction start, so the pattern is read
    inside the instruction that covers the address.  Where objdump covered no
    instruction at that address (data gaps in large modules) the immutable module
    image is used instead and the readback source is reported separately.
    """
    pat = bytes.fromhex(pattern_hex)
    rva = off + d
    start = max((r for r in stream if r <= rva), default=None)
    if start is not None and rva + len(pat) <= start + len(stream[start][0]):
        return stream[start][0][rva - start:rva - start + len(pat)] == pat, "asm"
    return blob[off:off + len(pat)] == pat, "image"


def verifier_match(stream):
    code = b"".join(v[0] for _, v in sorted(stream.items()))
    return all(any(bytes.fromhex(p) in code for p in pats) for _, pats in VERIFY_GROUPS)


def main():
    checks = 0
    failures = []
    notes = []

    def check(cond, label):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(label)
        return bool(cond)

    rom = open(DONOR, "rb").read()
    check(sha256_file(DONOR) == DONOR_SHA256, "donor sha256")
    check(len(rom) == DONOR_SIZE, "donor size 16 MiB")
    check(sha256_file(os.path.join(CORPUS, "census.json")) == CENSUS_SHA256, "census sha256")
    check(sha256_file(SCANNER) == SCANNER_SHA256, "scanner sha256")

    result = json.load(open(RESULT, encoding="utf-8"))
    check(result["status"] == "PASS", "scanner status PASS")
    check(result["failed"] == 0, "scanner failed == 0")
    check(result["donor"]["sha256"] == DONOR_SHA256, "scanner donor sha256")

    census = json.load(open(os.path.join(CORPUS, "census.json"), encoding="utf-8"))
    meta = {r["stem"]: r for r in census["records"] if r.get("stem")}
    delta = {s: meta[s]["sections"][0]["rva"] - meta[s]["sections"][0]["raw"] for s in meta}

    writer_stems = sorted(w["stem"] for w in result["writers"])
    check(writer_stems == sorted(EXPECTED_WRITERS), "scanner writer set == expected two")

    asm_matches = [s for s in sorted(meta) if verifier_match(asm_stream(s))]
    check(asm_matches == sorted(EXPECTED_WRITERS), "asm-derived match set == expected two")
    check(asm_matches == writer_stems, "asm-derived set == scanner writer set")

    anchors = {a["name"]: a["bytes"] for a in result["anchor_definitions"]}
    table = result["anchor_hit_table"]
    streams = {}

    # 2a. Corpus-wide module census per anchor, recomputed over all 233 module images.
    census_counts = {name: 0 for name in anchors}
    blobs = {}
    for stem in sorted(meta):
        blob = open(os.path.join(CORPUS, stem + ".bin"), "rb").read()
        blobs[stem] = blob
        for name, hexpat in anchors.items():
            if bytes.fromhex(hexpat) in blob:
                census_counts[name] += 1
    for name, reported in table.items():
        check(census_counts.get(name) == reported,
              "corpus module census %s reported=%s recomputed=%s" % (name, reported, census_counts.get(name)))

    # 2b. Every per-module anchor offset re-read from the asm text at its RVA.
    offset_entries = 0
    readback_sources = {}

    def verify_offsets(stem, per_anchor):
        nonlocal offset_entries
        check(stem in meta, "anchor offset stem known " + stem)
        stream = streams.setdefault(stem, asm_stream(stem))
        for name, offsets in per_anchor.items():
            pattern = anchors.get(name)
            check(pattern is not None, "anchor defined " + name)
            if pattern is None:
                continue
            for off in offsets:
                offset_entries += 1
                rva = int(off, 16) + delta[stem]
                ok, src = site_bytes(stream, blobs[stem], int(off, 16), delta[stem], pattern)
                readback_sources[src] = readback_sources.get(src, 0) + 1
                check(ok, "anchor %s %s@%s -> rva %s [%s]" % (name, stem, off, hex(rva), src))

    for w in result["writers"]:
        verify_offsets(w["stem"], w["anchor_offsets"])
    for m in result["ec_window_only_modules"]:
        verify_offsets(m["stem"], m["per_anchor_offsets"])

    for w in result["writers"]:
        stem = w["stem"]
        blob = open(os.path.join(CORPUS, stem + ".bin"), "rb").read()
        check(hashlib.sha256(blob).hexdigest() == meta[stem]["sha256"], "module sha256 " + stem)
        check(w["sha256"] == meta[stem]["sha256"], "reported sha256 " + stem)
        check(len(blob) == w["size"], "reported size " + stem)
        offsets = []
        start = 0
        while True:
            i = rom.find(blob[:64], start)
            if i < 0:
                break
            if rom[i:i + len(blob)] == blob:
                offsets.append(i)
            start = i + 1
        check(len(offsets) == 1, "unique whole-ROM occurrence " + stem)
        if offsets:
            ffs_off = int(w["ffs_offset"], 16)
            check(0 <= offsets[0] - ffs_off < 0x100, "TE image inside reported FFS file " + stem)
            notes.append("%s: TE image at ROM %s, reported ffs_offset %s"
                         % (stem, hex(offsets[0]), w["ffs_offset"]))

        stream = streams.setdefault(stem, asm_stream(stem))
        for helper in w["helpers"]:
            entry_rva = int(helper["entry"], 16) + delta[stem]
            check(entry_rva in stream, "helper entry instruction " + stem + " " + helper["entry"])
            prev = max((r for r in stream if r < entry_rva), default=None)
            check(prev is not None and "ret" in stream[prev][1],
                  "helper entry follows ret " + stem + " " + helper["entry"])
            for owned in helper["owns_ec_window_immediate"]:
                rva = int(owned, 16) + delta[stem]
                ok, src = site_bytes(stream, blobs[stem], int(owned, 16), delta[stem], "200a0000")
                readback_sources[src] = readback_sources.get(src, 0) + 1
                check(ok, "owned EC window immediate " + stem + " " + owned + " [" + src + "]")
            for owned in helper["owns_unlock_byte"]:
                rva = int(owned, 16) + delta[stem]
                check(rva in stream and stream[rva][0].hex().startswith("b087"),
                      "owned unlock byte " + stem + " " + owned)
            check(helper["full_transport_helper"] is True, "full transport helper " + stem)

        for call in w["call_sites"]:
            rva = int(call["call_addr"], 16) + delta[stem]
            target_rva = int(call["helper"], 16) + delta[stem]
            check(rva in stream and stream[rva][1].startswith("call"),
                  "call site instruction " + stem + " " + call["call_addr"])
            check(stream[rva][1].endswith(hex(target_rva)),
                  "call site targets helper " + stem + " " + call["call_addr"])
            raw_index = call.get("pushed_register_index_raw")
            if raw_index and raw_index.startswith("0x"):
                check(call["pushes"][-1] == raw_index,
                      "pushed register index matches last push " + stem + " " + call["call_addr"])
                check(call["pushed_register_index"] == int(raw_index, 16),
                      "pushed register index value " + stem + " " + call["call_addr"])
            if call.get("staged_value_resolution") == "immediate":
                check(call["staged_value"] == int(call["staged_value_raw"], 16),
                      "staged immediate value " + stem + " " + call["call_addr"])

    weak = sorted(m["stem"] for m in result["ec_window_only_modules"])
    check(len(weak) == len(set(weak)), "weak bucket has no duplicates")
    check(not set(weak) & set(writer_stems), "weak bucket disjoint from writers")
    for m in result["ec_window_only_modules"]:
        check(m["sha256"] == meta[m["stem"]]["sha256"], "weak module sha256 " + m["stem"])
        check(bool(m["per_anchor_offsets"]), "weak module has recorded offsets " + m["stem"])

    verifier_weak = sorted(
        s for s in meta
        if s not in asm_matches and any(
            any(bytes.fromhex(p) in b"".join(v[0] for _, v in sorted(streams.setdefault(s, asm_stream(s)).items()))
                for p in pats) for _, pats in VERIFY_GROUPS)
    )
    notes.append(
        "weak-bucket definitions differ by design: scanner=%d modules under its 10-anchor set, "
        "verifier=%d under its 3-group set; scanner-only=%s; verifier-only=%s"
        % (len(weak), len(verifier_weak), sorted(set(weak) - set(verifier_weak)),
           sorted(set(verifier_weak) - set(weak)))
    )

    prior = result["prior_result_crosscheck"]
    check(prior["agree"] is True, "prior crosscheck agree")
    check(sorted(prior["prior_writer_stems"]) == sorted(EXPECTED_WRITERS), "prior writer stems")

    verdict = {
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failed": len(failures),
        "failures": failures,
        "anchor_offset_entries_verified": offset_entries,
        "per_site_readback_sources": readback_sources,
        "inputs": {
            "donor": os.path.relpath(DONOR, ROOT),
            "corpus": os.path.relpath(CORPUS, ROOT),
            "verified_result": os.path.relpath(RESULT, ROOT),
            "verified_scanner": os.path.relpath(SCANNER, ROOT),
            "scanner_sha256": SCANNER_SHA256,
        },
        "notes": notes,
        "verified_conclusion": (
            "An independently written asm-text anchor conjunction over the same pinned corpus "
            "reproduces exactly the two EC-window VR mailbox writers reported by the scanner "
            "(ISL69247, ISL95712); each writer image occurs exactly once in the immutable ROM "
            "inside the reported FFS file; every recorded anchor offset, helper entry, owned "
            "anchor and call site re-reads consistently from the disassembly text."
        ),
    }
    json.dump(verdict, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
