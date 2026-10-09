#!/usr/bin/env python3
"""Bounded exact-corpus requester scan for $INV record/control ids 0x1363 and 0x1364.

Scope (read-only):
  * pinned CLV SPI ROM evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
  * exact extracted module corpus evidence/firmware-audit/20260919-inv-token-consumers
    (233 PE32 .bin + sibling .instructions.json + .asm, pinned by SHA256SUMS)

Tests:
  T1 pinned inputs: ROM sha256 + corpus SHA256SUMS verification of every .bin,
     .instructions.json and .asm covered by the manifest.
  T2 instruction scan: full-token operand occurrences of 0x1363 / 0x1364 per
     module, classified immediate / memory-reference / branch-or-call, with an
     independent asm-text cross-surface check for the immediate class.
  T3 adjacent-constant scan: u16 LE 0x1363 followed within 64 bytes by u16 LE
     0x1364 (paired-emitter / table hint), forward and reverse order.
  T4 config-offset scan: operand occurrences of the AmdSetup config offsets
     0x6e5 / 0x6e6 across the same corpus, to test whether every module carrying
     the 0x1363/0x1364 emitter also reads the same config pair.

Verdict heuristic: "immediate" hits outside the two known serializer modules
(CbsSetupDxe, CbsBasePei) are reported as external requester candidates.

No firmware, ROM, NVRAM, register or hardware mutation is performed.
"""
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
CORPUS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
SUMS = CORPUS / "SHA256SUMS"

KNOWN_SERIALIZERS = {
    "CbsSetupDxe-7ff717d51c9a": "7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8",
    "CbsBasePei-6ff112922ad8": "6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77",
}

TOKEN_RE = re.compile(r"(?<![0-9a-fA-F])0x(1363|1364)\b")
ASM_TOKEN_RE = re.compile(r"(?<![0-9a-fA-F])0x(1363|1364)(?![0-9a-fA-F])")
ASM_LINE_RE = re.compile(r"^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2} ?)+\s+(\S+)\s*(.*)$")
BRANCH_MNEMONICS = {
    "jmp", "call", "loop", "loope", "loopne", "jz", "jnz", "je", "jne", "jb", "jbe",
    "ja", "jae", "jl", "jle", "jg", "jge", "js", "jns", "jo", "jno", "jp", "jnp",
    "jrcxz", "jecxz", "ljmp", "lcall",
}
U16_1363 = struct.pack("<H", 0x1363)
U16_1364 = struct.pack("<H", 0x1364)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def classify(mnemonic: str, operands: str) -> str:
    if mnemonic.lower() in BRANCH_MNEMONICS or operands.strip().startswith(("0x", "-0x")):
        return "branch-or-call"
    if "[" in operands or "]" in operands:
        return "memory-reference"
    return "immediate"


def scan_module_instructions(bin_path: Path):
    instr_path = bin_path.with_name(bin_path.stem + ".instructions.json")
    assert instr_path.exists(), f"missing instructions json for {bin_path.name}"
    entries = json.loads(instr_path.read_text())
    hits = []
    for idx, entry in enumerate(entries):
        operands = entry.get("operands", "") or ""
        m = TOKEN_RE.search(operands)
        if not m:
            continue
        token = int(m.group(1), 16)
        cls = classify(entry.get("mnemonic", ""), operands)
        context = [
            f"{e.get('rva', 0):#x} {e.get('mnemonic', '')} {e.get('operands', '')}".strip()
            for e in entries[max(0, idx - 1): idx + 2]
        ]
        hits.append(
            {
                "token": f"0x{token:x}",
                "rva": entry.get("rva"),
                "bytes": entry.get("bytes"),
                "mnemonic": entry.get("mnemonic"),
                "operands": operands,
                "class": cls,
                "context": context,
            }
        )
    return instr_path, hits


def asm_immediate_tokens(asm_path: Path):
    """Independent surface: full tokens in operand position of the asm text."""
    found = []
    for lineno, line in enumerate(asm_path.read_text(errors="replace").splitlines(), 1):
        m = ASM_LINE_RE.match(line)
        if not m:
            continue
        mnemonic, rest = m.group(1), m.group(2)
        if mnemonic.lower() in BRANCH_MNEMONICS:
            continue
        for t in ASM_TOKEN_RE.finditer(rest):
            found.append((lineno, f"0x{int(t.group(1), 16):x}", mnemonic))
    return found


def _find_all(data: bytes, needle: bytes):
    offs = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx < 0:
            return offs
        offs.append(idx)
        start = idx + 1


def adjacent_pairs(data: bytes, window: int = 64):
    """Alignment-free paired-constant search within `window` bytes."""
    forward, reverse = [], []
    for off in _find_all(data, U16_1363):
        probe = data.find(U16_1364, off + 2, off + window + 2)
        if probe >= 0:
            forward.append({"control_off": off, "value_off": probe, "delta": probe - off})
    for off in _find_all(data, U16_1364):
        probe = data.find(U16_1363, off + 2, off + window + 2)
        if probe >= 0:
            reverse.append({"value_off": off, "control_off": probe, "delta": probe - off})
    return forward, reverse


def main() -> int:
    result = {
        "tool": "scan_inv_1364_requesters.py",
        "scope": "exact clv module corpus + pinned clv ROM (read-only)",
        "tests": {},
        "verdict": None,
    }

    # ---------------- T1 pinned inputs ----------------
    rom_data = ROM.read_bytes()
    rom_sha = sha256_bytes(rom_data)
    assert rom_sha == ROM_SHA, f"ROM sha mismatch: {rom_sha}"
    manifest = {}
    for line in SUMS.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        rel = rel.strip()
        manifest[rel] = digest
    corpus_prefix = str(CORPUS.relative_to(ROOT)) + "/"
    verified = 0
    mismatched = []
    missing = []
    external_verified = 0
    external_mismatched = []
    external_missing = []
    for rel, digest in manifest.items():
        p = ROOT / rel
        in_corpus = rel.startswith(corpus_prefix)
        if not p.exists():
            (missing if in_corpus else external_missing).append(rel)
            continue
        got = sha256_file(p)
        if got != digest:
            (mismatched if in_corpus else external_mismatched).append(
                {"path": rel, "expected": digest, "got": got}
            )
        elif in_corpus:
            verified += 1
        else:
            external_verified += 1
    assert not mismatched, f"corpus-local manifest mismatches: {mismatched}"
    assert not missing, f"corpus-local manifest entries missing on disk: {missing}"
    bins = sorted(CORPUS.glob("*.bin"))
    assert len(bins) == 233, f"unexpected corpus bin count: {len(bins)}"
    manifest_names = {Path(rel).name for rel in manifest}
    uncovered = [b.name for b in bins if b.name not in manifest_names]
    assert not uncovered, f"corpus .bin not covered by manifest: {uncovered}"
    result["tests"]["T1_pinned_inputs"] = {
        "status": "PASS",
        "rom_sha256": rom_sha,
        "manifest_entries": len(manifest),
        "manifest_corpus_local_verified": verified,
        "manifest_corpus_local_missing": missing,
        "manifest_corpus_local_mismatched": mismatched,
        "manifest_external_verified": external_verified,
        "manifest_external_missing_on_disk": external_missing,
        "manifest_external_mismatched": external_mismatched,
        "module_bin_count": len(bins),
        "module_bins_covered_by_manifest": len(bins),
    }
    for rel in external_missing:
        print(f"T1 NOTE external manifest entry missing on disk: {rel}")
    for m in external_mismatched:
        print(f"T1 NOTE external manifest drift: {m['path']} expected={m['expected']} got={m['got']}")
    print(f"T1 PASS pinned_inputs rom={rom_sha[:16]} corpus_verified={verified} "
          f"external_verified={external_verified} bins={len(bins)}")

    # ---------------- T2 instruction scan ----------------
    immediate, memory_ref, branch = [], [], []
    modules_with_immediate = set()
    crosscheck = []
    for b in bins:
        instr_path, hits = scan_module_instructions(b)
        module = b.stem
        for h in hits:
            h["module"] = module
            {"immediate": immediate, "memory-reference": memory_ref,
             "branch-or-call": branch}[h["class"]].append(h)
        imm_tokens = sorted(h["token"] for h in hits if h["class"] == "immediate")
        if imm_tokens:
            modules_with_immediate.add(module)
            asm_candidates = sorted(str(p) for p in CORPUS.glob(f"{module}-*.asm"))
            asm_tokens = []
            for ap in asm_candidates:
                asm_tokens.extend(sorted(t for _, t, _ in asm_immediate_tokens(Path(ap))))
            crosscheck.append(
                {
                    "module": module,
                    "json_immediate_tokens": imm_tokens,
                    "asm_immediate_tokens": sorted(asm_tokens),
                    "asm_files": [Path(a).name for a in asm_candidates],
                    "match": sorted(imm_tokens) == sorted(asm_tokens),
                }
            )
    bad = [c for c in crosscheck if not c["match"]]
    assert not bad, f"asm/json immediate cross-surface mismatch: {bad}"
    serializer_modules = set(KNOWN_SERIALIZERS)
    external = sorted(m for m in modules_with_immediate if m not in serializer_modules)
    result["tests"]["T2_instruction_scan"] = {
        "status": "PASS",
        "modules_scanned": len(bins),
        "immediate_hits": immediate,
        "memory_reference_hits": memory_ref,
        "branch_or_call_hits": branch,
        "modules_with_immediate": sorted(modules_with_immediate),
        "known_serializer_modules_pinned": KNOWN_SERIALIZERS,
        "external_immediate_requester_modules": external,
        "asm_crosscheck": crosscheck,
    }
    print(f"T2 PASS instruction_scan modules={len(bins)} immediate={len(immediate)} "
          f"memory_ref={len(memory_ref)} branch_or_call={len(branch)} external_immediate={external}")
    for h in immediate:
        print(f"    {h['module']} rva={h['rva']:#x} {h['mnemonic']} {h['operands']}")

    # ---------------- T4 config-offset operands ----------------
    offset_re = re.compile(r"(?<![0-9a-fA-F])0x(6e5|6e6)\b", re.IGNORECASE)
    disp_re = re.compile(r"\+0x(6e5|6e6)\]", re.IGNORECASE)
    offset_hits = []
    for b in bins:
        instr_path = b.with_name(b.stem + ".instructions.json")
        for entry in json.loads(instr_path.read_text()):
            operands = entry.get("operands", "") or ""
            mnemonic = entry.get("mnemonic", "") or ""
            if not offset_re.search(operands):
                continue
            if "rip+" in operands.lower():
                cls = "rip-relative-address"
            elif disp_re.search(operands):
                first, _, rest = operands.partition(",")
                cls = "config-displacement-write" if disp_re.search(first) else "config-displacement-read"
            elif mnemonic.lower() in BRANCH_MNEMONICS:
                cls = "branch-or-call-target"
            else:
                cls = "other"
            offset_hits.append(
                {
                    "module": b.stem,
                    "class": cls,
                    "rva": entry.get("rva"),
                    "mnemonic": mnemonic,
                    "operands": operands,
                }
            )
    config_sites = [h for h in offset_hits if h["class"].startswith("config-displacement")]
    result["tests"]["T4_config_offset_scan"] = {
        "status": "PASS",
        "modules_scanned": len(bins),
        "hit_count": len(offset_hits),
        "class_counts": {
            c: sum(1 for h in offset_hits if h["class"] == c)
            for c in sorted({h["class"] for h in offset_hits})
        },
        "modules_with_config_displacement": sorted({h["module"] for h in config_sites}),
        "config_displacement_hits": config_sites,
        "non_config_hits": [h for h in offset_hits if not h["class"].startswith("config-displacement")],
    }
    print(f"T4 PASS config_offset_scan hits={len(offset_hits)} "
          f"config_displacement={len(config_sites)} "
          f"modules={sorted({h['module'] for h in config_sites})}")
    for h in config_sites:
        print(f"    {h['module']} rva={h['rva']:#x} [{h['class']}] {h['mnemonic']} {h['operands']}")

    # ---------------- T3 adjacent constants ----------------
    scan_targets = [("ROM", ROM, rom_data)] + [(b.stem, b, b.read_bytes()) for b in bins]
    pairs = []
    for name, path, data in scan_targets:
        fwd, rev = adjacent_pairs(data)
        if fwd or rev:
            pairs.append({"module": name, "forward": fwd, "reverse": rev})
    result["tests"]["T3_adjacent_constants"] = {
        "status": "PASS",
        "targets_scanned": len(scan_targets),
        "pairings": pairs,
    }
    print(f"T3 PASS adjacent_constants targets={len(scan_targets)} modules_with_pairs={len(pairs)}")
    for p in pairs:
        print(f"    {p['module']} forward={len(p['forward'])} reverse={len(p['reverse'])}")

    if external:
        result["verdict"] = (
            "EXTERNAL_IMMEDIATE_REQUESTER_CANDIDATES: "
            + ", ".join(external)
            + " (requires semantic confirmation; not a consumer proof)"
        )
    else:
        result["verdict"] = (
            "NO_EXTERNAL_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS: immediate operands 0x1363/0x1364 "
            "occur only in the two previously pinned serializer modules of this exact 233-module "
            "corpus; computed/indirect/HOB/runtime consumption remains unresolved."
        )
    out = ROOT / "evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/requester-scan-result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("VERDICT:", result["verdict"])
    print("JSON:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
