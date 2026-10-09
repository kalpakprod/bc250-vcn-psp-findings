#!/usr/bin/env python3
"""Bounded static inventory of $INV / NVTB record readers and their requested token IDs.

Read-only over the pinned CLV donor and the pinned extracted module set.
Writes only its own JSON result next to this script.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
DONOR = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
EXT = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
OUT = ROOT / "evidence/firmware-audit/20260920-clv-voltage-consumer-trace"
DONOR_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
DONOR_SIZE = 16777216
MAGIC_NVTB = 0x4254564E
MAGIC_INV = 0x564E4924  # "$INV"

INSN_RE = re.compile(r"^\s*([0-9a-f]+):\t(.*)$")
BYTES_MNEM = re.compile(r"^(?P<bytes>(?:[0-9a-f]{2} ?)+)\s\s+(?P<mnem>.*)$")
BOUNDARY = ("ret", "int3", "hlt")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def parse_asm(p):
    insns = []
    for line in p.read_text(errors="replace").splitlines():
        m = INSN_RE.match(line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        rest = m.group(2).strip()
        bm = BYTES_MNEM.match(rest)
        if bm:
            byts, mnem = bm.group("bytes").replace(" ", ""), bm.group("mnem").strip()
        else:
            byts, mnem = "", rest
        insns.append({"addr": addr, "bytes": byts, "text": mnem})
    return insns


def function_entry(insns, idx):
    i = idx
    while i > 0:
        prev = insns[i - 1]["text"].split()
        head = prev[0] if prev else ""
        if head in BOUNDARY:
            break
        i -= 1
    return i


def fmt(addr):
    return "0x%x" % addr


def main():
    donor = DONOR.read_bytes()
    assert len(donor) == DONOR_SIZE, len(donor)
    got = sha256_bytes(donor)
    assert got == DONOR_SHA, got

    asms = sorted(p for p in EXT.glob("*.asm"))
    bins = sorted(p for p in EXT.glob("*.bin"))
    if not asms:
        sys.exit("no extracted .asm files found")

    result = {
        "donor": {"path": str(DONOR), "size": len(donor), "sha256": got},
        "extraction": {
            "dir": str(EXT),
            "asm_count": len(asms),
            "bin_count": len(bins),
            "asm_table_sha256": sha256_bytes(
                ("\n".join("%s %s" % (sha256_bytes(p.read_bytes()), p.name) for p in asms)).encode()
            ),
        },
        "readers": [],
        "token_scan": {},
        "data_magic_scan": {},
        "notes": [],
    }

    # ---- pass 1: find readers (magic immediates) -------------------------------
    readers = []  # (module, entry_idx, magic_insn_idx, magic)
    for p in asms:
        insns = parse_asm(p)
        for i, insn in enumerate(insns):
            t = insn["text"]
            if "0x%x" % MAGIC_NVTB in t.lower() and t.startswith("mov"):
                readers.append((p, insns, i, "NVTB"))
            if "0x%x" % MAGIC_INV in t.lower() and t.startswith("cmp"):
                readers.append((p, insns, i, "$INV"))

    reader_records = []
    for p, insns, i, magic in readers:
        e = function_entry(insns, i)
        entry_addr = insns[e]["addr"]
        # reader end: next boundary instruction address
        j = i
        while j < len(insns) and insns[j]["text"].split()[0] not in BOUNDARY:
            j += 1
        end_addr = insns[j]["addr"] if j < len(insns) else insns[-1]["addr"]
        call_re = re.compile(r"\bcall\s+0x([0-9a-f]+)")
        calls = []
        for k, insn in enumerate(insns):
            m = call_re.search(insn["text"])
            if m and int(m.group(1), 16) == entry_addr:
                calls.append(k)
        calls_out = []
        for k in calls:
            window = insns[max(0, k - 60):k]
            pushes = [(w["addr"], w["text"]) for w in window if w["text"].startswith("push")]
            movs = [(w["addr"], w["text"]) for w in window
                    if re.match(r"mov\s+(?:e|r)(?:cx|ecx|rcx),0x", w["text"])]
            win_imms = []
            for w in window:
                for imm in re.findall(r",0x([0-9a-f]+)", w["text"]):
                    win_imms.append((w["addr"], w["text"], int(imm, 16)))
            calls_out.append({
                "call_addr": fmt(insns[k]["addr"]),
                "nearest_push": None if not pushes else {"addr": fmt(pushes[-1][0]), "text": pushes[-1][1]},
                "nearest_mov_ecx": None if not movs else {"addr": fmt(movs[-1][0]), "text": movs[-1][1]},
                "window_immediates": [{"addr": fmt(a), "text": t, "imm": fmt(v)} for a, t, v in win_imms],
            })
        reader_records.append({
            "module": p.name,
            "magic": magic,
            "magic_site": fmt(insns[i]["addr"]),
            "reader_entry": fmt(entry_addr),
            "reader_last_addr": fmt(end_addr),
            "arch64": any(re.search(r"\br[a-z0-9]+\b", insn["text"]) for insn in insns[e:i + 1]),
            "call_sites": calls_out,
        })
    result["readers"] = reader_records

    # ---- pass 2: immediates in the CBS/$INV token range per module -------------
    token_re = re.compile(r"\b(?:push|mov|cmp|add|or|and|test|sub|lea|imul)\b.*?,0x([0-9a-f]{4,8})\b")
    for lo, hi, label in ((0x1360, 0x1367, "voltage_offset_tokens"),
                          (0x1000, 0x13FF, "cbs_token_range")):
        rows = []
        for p in asms:
            insns = parse_asm(p)
            hits = []
            for insn in insns:
                m = token_re.search(insn["text"])
                if not m:
                    continue
                v = int(m.group(1), 16)
                if lo <= v <= hi:
                    hits.append({"addr": fmt(insn["addr"]), "imm": fmt(v), "text": insn["text"]})
            if hits:
                rows.append({"module": p.name, "immediate_hits": hits})
        result["token_scan"][label] = {"range": [fmt(lo), fmt(hi)], "modules": rows}

    # ---- pass 3: data-level magic + 16-bit token encodings ---------------------
    data = {}
    for p in bins:
        b = p.read_bytes()
        entry = {}
        for name, pat in (("$INV", b"$INV"), ("NVTB", b"NVTB")):
            offs = [i for i in range(len(b)) if b.startswith(pat, i)]
            if offs:
                entry[name] = offs[:8]
        tok_hits = {}
        for tok in range(0x1360, 0x1368):
            pat = tok.to_bytes(2, "little")
            offs = []
            start = 0
            while True:
                i = b.find(pat, start)
                if i < 0:
                    break
                offs.append(i)
                start = i + 1
                if len(offs) >= 4:
                    break
            if offs:
                tok_hits[fmt(tok)] = offs
        if entry or tok_hits:
            data[p.name] = {"magic": entry, "token16_le": tok_hits}
    result["data_magic_scan"] = data

    # ---- pass 4: reader stride-switch signature (readers loading magic from data)
    sig = bytes.fromhex("83e103")  # and ecx,0x3
    sig32 = bytes.fromhex("80e203")  # and dl,0x3
    sig_mods = {}
    for p in asms:
        b = p.with_suffix(".bin")
        if not b.exists():
            continue
        raw = b.read_bytes()
        c = raw.count(sig) + raw.count(sig32)
        if c:
            sig_mods[p.name] = c
    result["stride_switch_signature_modules"] = sig_mods

    result["notes"] = [
        "Reader return convention: 0 = record found, 1 = terminator reached (record absent).",
        "32-bit reader (AmdFabricAriPei 0x1d3c) takes the token id as its single pushed stack argument.",
        "64-bit reader (AmdCcxVhAriDxe 0x5ac4) takes the token id in CX; out pointer in RDX.",
        "Record layout: u16 id, u8 format (bit0-1: 0=1B,1=2B,2=4B,3=8B), payload; terminated by id 0xFFFF.",
        "No global absence claim: only modules that inline the NVTB/$INV magic immediate are covered by pass 1.",
    ]

    out = OUT / "inv-consumer-scan.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "result": str(out),
        "readers": [{r["module"]: r["reader_entry"], "magic": r["magic"],
                     "calls": len(r["call_sites"])} for r in reader_records],
        "token_range_modules": {k: [m["module"] for m in v["modules"]] for k, v in result["token_scan"].items()},
        "data_magic_modules": sorted(data.keys()),
        "donor_sha256": got,
    }, indent=2))


if __name__ == "__main__":
    main()
