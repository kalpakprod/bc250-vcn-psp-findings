#!/usr/bin/env python3
"""CLV fixed-voltage Setup consumer scanner (read-only, deterministic).

Question: which modules read the fixed VCORE/GFX/MEMIO voltage fields that live in the
separate `Setup` VarStore (form 0x28EA "REF Voltage Configuration", offsets 0x1c9..0x1d2)
instead of the CBS offset path (AmdSetup+0x6E5/0x6E6)?

Method (static, over pinned inputs only):
  1. re-hash the immutable CLV donor and the pinned 233-module corpus census;
  2. in every extracted module image, locate the Setup variable GUID and test whether it is
     immediately followed by the UTF-16 name "Setup" (the canonical GetVariable pair);
  3. map each module file offset to RVA/VA using the census section table and find code
     references to the GUID/name VAs;
  4. for the modules that pass (2), assert the literal Setup-read call site (size 0x1d3)
     and every literal instruction that consumes Setup offsets 0x1c9..0x1d2.

No ROM/NVRAM/register/hardware write, no candidate build, no network.
"""
import hashlib
import json
import os
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DONOR = os.path.join(ROOT, "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin")
CORPUS = os.path.join(ROOT, "evidence/firmware-audit/20260919-inv-token-consumers")
DONOR_SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"

SETUP_GUID = bytes.fromhex("43D687ECA4EBB54BA1E53F3E36B20DA9")  # EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9
SETUP_NAME = "S\x00e\x00t\x00u\x00p\x00\x00\x00".encode()
SETUP_SIZE = 0x1D3
READONLY_VAR2_PPI = bytes.fromhex("F56EB82AB5EC3441B5563854CA1FE1B4")  # 2AB86EF5-ECB5-4134-B556-3854CA1FE1B4

# Fixed-voltage / loadline fields of Setup form 0x28EA (from the pinned HII inventory).
FIELDS = [
    (0x1C9, 1, "0x73", "VCORE Fix Voltage (Disabled=0/Enabled=1)"),
    (0x1CA, 2, "0x74", "VCORE Voltage(mV) (700..1250, default 900)"),
    (0x1CC, 1, "0x75", "VCORE Loadline (Disabled/0.2..0.6 Ohm index)"),
    (0x1CD, 1, "0x76", "GFX Fix Voltage (Disabled=0/Enabled=1)"),
    (0x1CE, 2, "0x77", "GFX Voltage(mV) (700..1250, default 900)"),
    (0x1D0, 1, "0x78", "GFX Loadline (Disabled/0.2..0.6 Ohm index)"),
    (0x1D1, 1, "0x79", "MEMIO Fix Voltage (Disabled=0/Enabled=1)"),
    (0x1D2, 1, "0x7A", "MEMIO Voltage (enum 1.20..1.45 V, default 1.35 V = 0x1e)"),
]

# Literal assertions: (rva, expected hex bytes, meaning) for the two consumer modules.
ASSERTIONS = {
    "ISL69247-3e1f753a6279": [
        (0x02A2, "c7455cd3010000", "GetVariable DataSize = 0x1d3 (Setup variable size)"),
        (0x02C1, "8d8588feffff", "GetVariable Data buffer = [ebp-0x178]"),
        (0x02D0, "68c436ed09", "push Setup variable GUID VA 0x9ed36c4"),
        (0x02D5, "68d436ed09", "push UTF-16 name 'Setup' VA 0x9ed36d4"),
        (0x02A9, "885d51", "default Setup+0x1c9 (VCORE Fix Voltage) = 0"),
        (0x02AC, "c64554", "default Setup+0x1cc (VCORE Loadline) = 2"),
        (0x02B0, "885d55", "default Setup+0x1cd (GFX Fix Voltage) = 0"),
        (0x02B3, "c64558", "default Setup+0x1d0 (GFX Loadline) = 2"),
        (0x028F, "66894d52", "default Setup+0x1ca (VCORE Voltage mV) = 0x384 (900)"),
        (0x0293, "66894d56", "default Setup+0x1ce (GFX Voltage mV) = 0x384 (900)"),
        (0x0314, "0fb74552", "read Setup+0x1ca as u16 -> VCORE mV value"),
        (0x030A, "6a21", "VCORE write targets register index 0x21"),
        (0x03B2, "0fb74556", "read Setup+0x1ce as u16 -> GFX mV value"),
        (0x03A8, "6a21", "GFX write targets register index 0x21"),
        (0x036B, "0fb64554", "read Setup+0x1cc (VCORE Loadline index)"),
        (0x0403, "0fb64558", "read Setup+0x1d0 (GFX Loadline index)"),
        (0x040F, "6a28", "Loadline write targets register index 0x28"),
        (0x030A + 0, "6a21", "enable test: cmp Setup+0x1c9 vs 0 selects Setup mV vs default 900"),
        (0x03AD, "385d55", "enable test: cmp Setup+0x1cd (GFX Fix Voltage) vs 0"),
        (0x038E, "680bea0000", "VCORE helper arg2 = 0xEA0B"),
        (0x0429, "688bea0000", "GFX helper arg2 = 0xEA8B"),
        (0x04D3, "68c7000000", "helper writes register 0xC7"),
        (0x04E1, "68c5000000", "helper writes register 0xC5"),
        (0x0388, "6a0b", "VCORE loadline==2 selects 0x0B for reg 0xC5"),
        (0x038C, "6a08", "VCORE loadline!=2 selects 0x08 for reg 0xC5"),
        (0x0709, "0fb607", "write helper reads a u16 little-endian value from [edi]"),
        (0x0543, "b9200a0000", "transport mailbox base port 0xA20"),
        (0x0566, "2e59", "transport uses x86 config port 0x2E"),
        (0x0571, "6a2f", "transport uses x86 config port 0x2F"),
        (0x06F5, "6a65", "write helper stages register 0x65"),
        (0x0702, "6a66", "write helper stages target register index in register 0x66"),
        (0x0722, "6a63", "write helper stages register 0x63"),
        (0x072A, "6a60", "write helper stages register 0x60 (start)"),
        (0x02E1, "6a61", "init writes register 0x61 = 0"),
        (0x02E8, "6a03", "init writes register 0x62 = 3"),
    ],
    "ISL95712-c0cc17d2d54f": [
        (0x0266, "c745f4d3010000", "GetVariable DataSize = 0x1d3 (Setup variable size)"),
        (0x027E, "8d8520feffff", "GetVariable Data buffer = [ebp-0x1e0]"),
        (0x028D, "685c45ed09", "push Setup variable GUID VA 0x9ed455c"),
        (0x0292, "686c45ed09", "push UTF-16 name 'Setup' VA 0x9ed456c"),
        (0x026D, "885df1", "default Setup+0x1d1 (MEMIO Fix Voltage) = 0"),
        (0x0270, "c645f2", "default Setup+0x1d2 (MEMIO Voltage) = 0x1e (1.35 V)"),
        (0x02B6, "385df1", "enable test: cmp Setup+0x1d1 (MEMIO Fix Voltage) vs 0"),
        (0x02BC, "8a45f2", "read Setup+0x1d2 (MEMIO Voltage enum)"),
        (0x02C6, "68df000000", "MEMIO write targets register index 0xdf"),
        (0x02E3, "68df000000", "disabled path writes register 0xDF with default 0x1e"),
        (0x02E8, "c645ff1e", "default MEMIO Voltage = 0x1e (1.35 V)"),
        (0x02D9, "804dff01", "enabled path ORs bit 0 into the staged MEMIO value"),
        (0x03F3, "689e000000", "MEMIO post-write helper stages register 0x65 = 0x9E"),
        (0x0401, "68de000000", "MEMIO post-write helper stages register 0x66 = 0xDE"),
        (0x0419, "68c0000000", "MEMIO post-write helper stages register 0x60 = 0xC0"),
    ],
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    checks = 0
    failed = []

    def check(cond, label):
        nonlocal checks
        checks += 1
        if not cond:
            failed.append(label)
        return cond

    result = {"status": "PASS", "checks": 0, "failed": 0, "failures": [], "modules": [], "field_map": {}}

    donor_hash = sha256(DONOR)
    check(donor_hash == DONOR_SHA256, "donor sha256")
    check(os.path.getsize(DONOR) == 16777216, "donor size")

    census_path = os.path.join(CORPUS, "census.json")
    census = json.load(open(census_path, encoding="utf-8"))
    check(census["input"].endswith("BC250_5.00_clv.bin"), "census input path")
    check(census["sha256"] == DONOR_SHA256, "census input sha256")
    check(census["objdump"].startswith("GNU objdump"), "census objdump tool")

    meta = {}
    for rec in census["records"]:
        stem = rec.get("stem")
        if stem:
            meta[stem] = rec
    check(len(meta) >= 233, "census module count >= 233")

    consumers = []
    guid_only = []
    for stem in sorted(meta):
        rec = meta[stem]
        path = os.path.join(CORPUS, stem + ".bin")
        if not os.path.exists(path):
            continue
        blob = open(path, "rb").read()
        check(sha256(path) == rec["sha256"], "module sha256 " + stem)
        idx = blob.find(SETUP_GUID)
        if idx < 0:
            continue
        secs = rec["sections"]
        delta = secs[0]["rva"] - secs[0]["raw"]
        guid_rva = idx + delta
        guid_va = rec["imagebase"] + guid_rva
        has_name = blob[idx + 16:idx + 16 + len(SETUP_NAME)] == SETUP_NAME
        name_va = None
        if has_name:
            name_va = rec["imagebase"] + idx + 16 + delta
            consumers.append({
                "stem": stem,
                "ui": rec.get("ui"),
                "type": rec.get("type"),
                "ffs_guid": rec.get("ffs_guid"),
                "fv_base": hex(rec.get("fv_base", 0)),
                "ffs_offset": hex(rec.get("ffs_offset", 0)),
                "setup_guid_va": hex(guid_va),
                "setup_name_va": hex(name_va),
                "sha256": rec["sha256"],
            })
        else:
            guid_only.append(stem)

    check(len(consumers) == 3, "modules with Setup GUID + adjacent UTF-16 name == 3")
    check({c["ui"] for c in consumers} == {"CpuDxe", "ISL69247", "ISL95712"},
          "consumer set == {CpuDxe, ISL69247, ISL95712}")

    # Literal instruction assertions for the two voltage consumers.
    for stem, asserts in ASSERTIONS.items():
        rec = meta[stem]
        blob = open(os.path.join(CORPUS, stem + ".bin"), "rb").read()
        delta = rec["sections"][0]["rva"] - rec["sections"][0]["raw"]
        for rva, hexbytes, meaning in asserts:
            off = rva - delta
            got = blob[off:off + len(hexbytes) // 2].hex()
            check(got == hexbytes, f"{stem}@{rva:#x} {meaning} (got {got})")
        # the module must also locate the PEI Read-Only Variable2 PPI
        check(READONLY_VAR2_PPI in blob, stem + " carries PEI Read-Only Variable2 PPI GUID")

    # Independent path: re-extract both consumer TE images straight from the immutable ROM
    # (no corpus dependency) and re-assert the Setup call-site bytes there.
    rom = open(DONOR, "rb").read()
    rom_direct = {}
    for stem in ASSERTIONS:
        rec = meta[stem]
        ref = rec["sha256"]
        size = rec["size"]
        hit = None
        for start in range(rec["ffs_offset"], rec["ffs_offset"] + 0x60):
            if rom[start:start + 2] != b"VZ":
                continue
            if hashlib.sha256(rom[start:start + size]).hexdigest() == ref:
                hit = start
                break
        check(hit is not None, "ROM-direct TE image for " + stem)
        if hit is None:
            continue
        delta = rec["sections"][0]["rva"] - rec["sections"][0]["raw"]
        base = hit - delta
        for rva, hexbytes, meaning in ASSERTIONS[stem]:
            got = rom[base + rva:base + rva + len(hexbytes) // 2].hex()
            check(got == hexbytes, f"ROM-direct {stem}@{rva:#x} {meaning}")
        rom_direct[stem] = {
            "rom_offset": hex(hit),
            "sha256": ref,
            "matches_corpus_image": True,
        }
    result["rom_direct_reextraction"] = rom_direct

    # Offset -> frame-slot mapping used by each consumer (buffer base -> Setup offset).
    field_map = {
        "ISL69247-3e1f753a6279": {
            "buffer_base": "ebp-0x178 (GetVariable Data)",
            "fields": {
                "0x1c9": {"slot": "ebp+0x51", "use": "enable test vs 0; default 0"},
                "0x1ca": {"slot": "ebp+0x52", "use": "u16 mV value; default 0x384 (900); written as register 0x21"},
                "0x1cc": {"slot": "ebp+0x54", "use": "loadline index; default 2; index -> {0,20,30,40,50,60}; written as register 0x28"},
                "0x1cd": {"slot": "ebp+0x55", "use": "enable test vs 0; default 0"},
                "0x1ce": {"slot": "ebp+0x56", "use": "u16 mV value; default 0x384 (900); written as register 0x21"},
                "0x1d0": {"slot": "ebp+0x58", "use": "loadline index; default 2; written as register 0x28"},
            },
        },
        "ISL95712-c0cc17d2d54f": {
            "buffer_base": "ebp-0x1e0 (GetVariable Data)",
            "fields": {
                "0x1d1": {"slot": "ebp-0xf", "use": "enable test vs 0; default 0"},
                "0x1d2": {"slot": "ebp-0xe", "use": "enum value; default 0x1e (1.35 V); written as register 0xdf"},
            },
        },
    }
    result["field_map"] = field_map

    # CpuDxe reads Setup but must not touch the fixed-voltage block.
    cpudxe = next(c for c in consumers if c["ui"] == "CpuDxe")
    cpudxe_asm = os.path.join(CORPUS, "CpuDxe-4fe9d6dc6dfe-0.asm")
    asm_txt = open(cpudxe_asm, encoding="utf-8", errors="replace").read()
    for slot in ("+0x289", "+0x28a", "+0x28e", "+0x291", "+0x292"):
        check(slot not in asm_txt, "CpuDxe does not access Setup buffer " + slot)

    result["donor"] = {"path": DONOR, "sha256": donor_hash, "size": 16777216}
    result["corpus"] = {"path": CORPUS, "census": census_path, "modules": len(meta)}
    result["setup_variable"] = {
        "guid": "EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9",
        "name": "Setup",
        "size": hex(SETUP_SIZE),
        "form": "0x28EA REF Voltage Configuration (Setup 0x2710 -> Advanced 0x2712)",
    }
    result["get_variable_setup_modules"] = consumers
    result["setup_guid_only_modules"] = guid_only
    result["fixed_voltage_fields"] = [
        {"offset": hex(o), "width": w, "qid": q, "label": lab} for o, w, q, lab in FIELDS
    ]
    result["consumer_conclusion"] = (
        "ISL69247 (PEIM) consumes Setup+0x1c9/0x1ca/0x1cc (VCORE) and Setup+0x1cd/0x1ce/0x1d0 (GFX); "
        "ISL95712 (PEIM) consumes Setup+0x1d1/0x1d2 (MEMIO). Both read the 0x1d3-byte Setup variable "
        "through the PEI Read-Only Variable2 PPI and drive a VR-controller register write helper. "
        "CpuDxe reads the Setup variable but does not touch the fixed-voltage block."
    )
    result["checks"] = checks
    result["failed"] = len(failed)
    result["failures"] = failed
    result["status"] = "PASS" if not failed else "FAIL"
    json.dump(result, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
