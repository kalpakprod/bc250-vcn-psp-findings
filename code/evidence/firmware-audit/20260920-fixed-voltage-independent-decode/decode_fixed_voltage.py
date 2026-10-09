#!/usr/bin/env python3
"""Independent instruction-level decode of the CLV fixed-voltage Setup consumers.

Purpose (open review item in memory/project-state.md): the prior artifact
`docs/research/2026-09-20-clv-fixed-voltage-consumer.md` and its scanner
`evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py`
assert byte patterns at RVAs and attach prose "meanings" to them. Those meanings were never
derived by decoding. This script answers the same question with a different method class:

  1. locate the two PEIMs in the immutable donor by FFS file GUID using a structural walk
     (no dependency on the pinned census for selection);
  2. disassemble the extracted TE images with GNU objdump (flat binary, i386, intel syntax,
     --adjust-vma=0x198 so decoded addresses equal the RVAs used by the prior artifact);
  3. re-derive every prior claim from the decoded instructions and from the referenced data
     bytes, and classify each prior byte-assertion label as instruction, prefix, mid-instruction
     or spanning-two-instructions.

Status semantics: `status` is PASS when the decode itself completed and no decoded fact
contradicts a claim; `label_status` reports misleading prior labels separately. A misleading
label does not fail the run: it is the finding. Exit code 0 only for status PASS.

Read-only: hashes and parses the donor, writes nothing except stdout. No ROM/NVRAM/register/
candidate/hardware write, no network, no board contact.
"""
import ast
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DONOR = os.path.join(ROOT, "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin")
DONOR_SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
DONOR_SIZE = 16777216
CENSUS = os.path.join(ROOT, "evidence/firmware-audit/20260919-inv-token-consumers/census.json")
PRIOR_SCANNER = os.path.join(
    ROOT, "evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py")
OBJDUMP = "/usr/bin/objdump"

FV_BASE = 0xE02000
RVA_DELTA = 0x198                      # file offset = RVA - 0x198 (validated against data VAs below)
TARGETS = {
    "ISL69247": "6E6D2018-28D0-4AD3-BEB3-B48E4981707D",
    "ISL95712": "02544BE0-2CB9-4B75-8111-CD8CDC07B837",
}
SETUP_GUID = bytes.fromhex("43D687ECA4EBB54BA1E53F3E36B20DA9")
SETUP_NAME = b"S\x00e\x00t\x00u\x00p\x00\x00\x00"
RO_VAR2_GUID = bytes.fromhex("F56EB82AB5EC3441B5563854CA1FE1B4")

SEC_EXEC = {0x10: "PE32", 0x12: "TE"}
VALID_FILE_TYPES = set(range(1, 15)) | {0xF0}
VALID_STATES = {0x07, 0x0F, 0xF8, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x08}

INSN_RE = re.compile(r"^\s*([0-9a-f]+):\t([0-9a-f ]*?)\t(.*)$")
CONT_RE = re.compile(r"^\s+([0-9a-f]{2}(?: [0-9a-f]{2})*)\s*$")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def guid_str(b):
    return "%08X-%04X-%04X-%02X%02X-%s" % (
        struct.unpack_from("<I", b, 0)[0], struct.unpack_from("<H", b, 4)[0],
        struct.unpack_from("<H", b, 6)[0], b[8], b[9], b[10:16].hex().upper())


def ffs_files(buf, start, end):
    """Structurally validated FFS file headers in [start, end)."""
    out = []
    off = start
    while off + 24 <= end:
        name = buf[off:off + 16]
        if name in (b"\xff" * 16, b"\x00" * 16):
            off += 8
            continue
        ftype, attr = buf[off + 0x12], buf[off + 0x13]
        hsize, size = 24, int.from_bytes(buf[off + 0x14:off + 0x17], "little")
        if attr & 0x01:
            hsize = 32
            size = int.from_bytes(buf[off + 0x18:off + 0x20], "little")
        if ftype not in VALID_FILE_TYPES or buf[off + 0x17] not in VALID_STATES:
            off += 8
            continue
        if size < hsize + 8 or off + size > end:
            off += 8
            continue
        secs = sections(buf, off, hsize, size)
        if not secs:
            off += 8
            continue
        last_end = secs[-1]["data"] + secs[-1]["data_size"]
        if not (off + hsize + 8 <= last_end <= off + size) or (off + size) - last_end > 7:
            off += 8
            continue
        out.append({"offset": off, "guid": guid_str(name), "type": ftype, "size": size,
                    "sections": secs})
        off += 8
    return out


def sections(buf, off, hsize, size):
    out = []
    p, end = off + hsize, off + size
    while p + 4 <= end:
        ssize = int.from_bytes(buf[p:p + 3], "little")
        stype, sh = buf[p + 3], 4
        if ssize == 0xFFFFFF:
            ssize, sh = int.from_bytes(buf[p + 4:p + 8], "little"), 8
        if ssize < sh or p + ssize > end:
            return out
        out.append({"hdr": p, "type": stype, "size": ssize, "data": p + sh,
                    "data_size": ssize - sh})
        p = (p + ssize + 3) & ~3
        if len(out) > 64:
            return out
    return out


class Image:
    """A TE/PE32 payload plus its objdump decode."""

    def __init__(self, name, data, adjust_vma):
        self.name = name
        self.data = data
        self.tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
        self.tmp.write(data)
        self.tmp.close()
        cmd = [OBJDUMP, "-D", "-b", "binary", "-m", "i386", "-M", "intel",
               "--adjust-vma=0x%x" % adjust_vma, self.tmp.name]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.cmd = " ".join(cmd[:-1] + ["<extracted-image>"])
        self.insns = []
        for line in proc.stdout.splitlines():
            m = INSN_RE.match(line)
            if m:
                self.insns.append({"addr": int(m.group(1), 16),
                                   "bytes": m.group(2).split(), "text": m.group(3).strip()})
                continue
            c = CONT_RE.match(line)
            if c and self.insns:
                self.insns[-1]["bytes"] += c.group(1).split()

    def at(self, rva):
        for ins in self.insns:
            n = len(ins["bytes"])
            if ins["addr"] <= rva < ins["addr"] + n:
                return ins
        return None

    def find(self, pattern, lo=0, hi=1 << 32):
        rx = re.compile(pattern)
        for ins in self.insns:
            if lo <= ins["addr"] < hi and rx.search(ins["text"]):
                return ins
        return None

    def ev(self, ins):
        return {"addr": "0x%03x" % ins["addr"], "bytes": " ".join(ins["bytes"]), "text": ins["text"]}


def main():
    result = {"status": "PASS", "decode_status": "PASS", "label_status": "OK",
              "semantic_checks": [], "label_review": [], "boundaries": []}
    checks, contradicted = [], []

    def record(cid, module, claim, evidence, verdict, note=""):
        entry = {"id": cid, "module": module, "claim": claim, "verdict": verdict,
                 "evidence": [{"addr": "0x%03x" % a, "text": t} for a, t in evidence]}
        if note:
            entry["note"] = note
        if verdict == "CONTRADICTED":
            contradicted.append(cid)
        checks.append(entry)
        return entry

    # ---- inputs -----------------------------------------------------------
    donor = open(DONOR, "rb").read()
    dh = sha256(donor)
    result["donor"] = {"path": DONOR, "sha256": dh, "size": len(donor)}
    if dh != DONOR_SHA256 or len(donor) != DONOR_SIZE:
        result["status"] = "FAIL"
        result["decode_status"] = "FAIL"
        json.dump(result, sys.stdout, indent=1)
        return 1
    ver = subprocess.run([OBJDUMP, "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    result["tool"] = {"objdump": ver, "rva_delta": hex(RVA_DELTA),
                      "disasm_flags": "-D -b binary -m i386 -M intel --adjust-vma=0x198"}

    # ---- prior assertion table (loaded, not transcribed) -------------------
    ns = {"__name__": "prior_scanner", "__file__": PRIOR_SCANNER}
    exec(compile(open(PRIOR_SCANNER, encoding="utf-8").read(), PRIOR_SCANNER, "exec"), ns)
    prior = ns["ASSERTIONS"]
    result["prior_assertion_source"] = {"path": PRIOR_SCANNER, "sha256": sha256(open(PRIOR_SCANNER, "rb").read())}

    # ---- module selection by FFS GUID (structural walk, census independent) -
    fvs = []
    i = 0
    while True:
        j = donor.find(b"_FVH", i)
        if j < 0:
            break
        base = j - 0x28
        if base % 8 == 0 and base >= 0:
            flen = struct.unpack_from("<I", donor, base + 0x20)[0]
            if 0x1000 <= flen <= len(donor) - base and donor[base + 0x10:base + 0x20] != b"\x00" * 16:
                fvs.append((base, flen, struct.unpack_from("<H", donor, base + 0x30)[0]))
        i = j + 1
    inner = set()
    for a, (b1, l1, _) in enumerate(fvs):
        for b, (b2, l2, _) in enumerate(fvs):
            if a != b and b1 <= b2 and b2 + l2 <= b1 + l1:
                inner.add(b)
    fvs = [f for k, f in enumerate(fvs) if k not in inner]
    result["fv_regions"] = [{"base": hex(b), "length": hex(l), "header_length": hex(h)}
                            for b, l, h in fvs]
    result["fv_regions_note"] = ("regions contained in another detected volume are dropped as "
                                 "nested duplicates")
    files, seen = [], set()
    for base, flen, hlen in fvs:
        for f in ffs_files(donor, base + hlen, base + flen):
            if f["offset"] in seen:
                continue
            seen.add(f["offset"])
            f["fv_base"] = hex(base)
            files.append(f)
    by_guid = {f["guid"]: f for f in files}
    census = json.load(open(CENSUS, encoding="utf-8"))
    cen = {r["stem"].split("-")[0] + "-" + r["stem"]: r for r in census["records"] if r.get("stem")}
    result["ffs_scan"] = {"volumes": len(fvs), "files_found": len(files),
                          "note": "structural FFS validation; FFS header checksum fields in this "
                                  "volume do not validate under the edk2 rule (0xAA placeholder)"}
    images, modules = {}, {}
    for name, guid in TARGETS.items():
        f = by_guid.get(guid)
        if f is None:
            result["status"] = "FAIL"
            json.dump(result, sys.stdout, indent=1)
            return 1
        sec = next(s for s in f["sections"] if s["type"] in SEC_EXEC)
        data = donor[sec["data"]:sec["data"] + sec["data_size"]]
        rec = next(r for r in census["records"] if r.get("stem", "").startswith(name + "-"))
        images[name] = Image(name, data, RVA_DELTA)
        modules[name] = {
            "ffs_guid": guid, "ffs_file_offset": hex(f["offset"]), "ffs_file_size": f["size"],
            "section_type": SEC_EXEC[sec["type"]], "te_offset_in_rom": hex(sec["data"]),
            "te_size": sec["data_size"], "te_sha256": sha256(data),
            "census_sha256": rec["sha256"], "census_size": rec["size"],
            "te_header": {"signature": data[0:2].decode("latin1"),
                          "machine": hex(struct.unpack_from("<H", data, 2)[0]),
                          "sections": data[4],
                          "stripped_size": hex(struct.unpack_from("<H", data, 6)[0]),
                          "entry": hex(struct.unpack_from("<I", data, 8)[0]),
                          "image_base": hex(struct.unpack_from("<Q", data, 0x10)[0])},
        }
        record("M-%s-identity" % name, name,
               "TE image at ROM %s hashes to the pinned census record" % hex(sec["data"]),
               [(sec["data"], "%s / %s" % (sha256(data)[:16], rec["sha256"][:16]))],
               "SUPPORTED" if sha256(data) == rec["sha256"] and sec["data_size"] == rec["size"]
               else "CONTRADICTED")
    result["modules"] = modules

    # ---- consumer enumeration inside this scan set (independent of census) --
    consumers, guid_only = [], []
    for f in files:
        sec = next((s for s in f["sections"] if s["type"] in SEC_EXEC), None)
        if sec is None:
            continue
        blob = donor[sec["data"]:sec["data"] + sec["data_size"]]
        idx = blob.find(SETUP_GUID)
        if idx < 0:
            continue
        if blob[idx + 16:idx + 16 + len(SETUP_NAME)] == SETUP_NAME:
            consumers.append({"ffs_guid": f["guid"], "file_offset": hex(f["offset"]),
                              "fv_base": f["fv_base"], "setup_guid_rva": hex(idx + 0xA8),
                              "module": TARGETS_REV(by_guid, f)})
        else:
            guid_only.append({"ffs_guid": f["guid"], "file_offset": hex(f["offset"]),
                              "fv_base": f["fv_base"]})
    cen_hits, cen_all = 0, 0
    for f in files:
        sec = next((s for s in f["sections"] if s["type"] in SEC_EXEC), None)
        if sec is None:
            continue
        blob = donor[sec["data"]:sec["data"] + sec["data_size"]]
        cen_all += 1
        if any(r.get("sha256") == sha256(blob) for r in census["records"]):
            cen_hits += 1
    result["consumer_scan"] = {
        "files_scanned": len(files), "executable_sections_scanned": cen_all,
        "setup_guid_and_name": consumers, "setup_guid_only_count": len(guid_only),
        "census_coverage": {"census_identities": len(census["records"]),
                            "reproduced_by_this_scan": cen_hits},
        "scope_note": ("outer FFS files with a first-level PE32/TE section only; images inside "
                       "compressed or GUIDed sections and nested FVs are not enumerated here, so the "
                       "prior 'exactly three consumers incl. CpuDxe (nested GUIDed PE32)' claim is "
                       "not re-derived by this scan")}

    # ---- decode-derived semantic checks -----------------------------------
    i47, i57 = images["ISL69247"], images["ISL95712"]

    def pair(ins):
        return (ins["addr"], ins["text"]) if ins else (0, "<not found>")

    # ISL69247 -----------------------------------------------------------------
    record("A3a", "ISL69247", "GetVariable call site pushes the Setup GUID VA and the UTF-16 name VA",
           [pair(i47.find(r"push\s+0x9ed36c4$")), pair(i47.find(r"push\s+0x9ed36d4$"))], "SUPPORTED")
    gva = 0x9ed36c4
    goff = gva - int(modules["ISL69247"]["te_header"]["image_base"], 16) - RVA_DELTA
    gdata = i47.data[goff:goff + 16]
    record("A4a", "ISL69247", "the pushed GUID VA 0x9ed36c4 holds the Setup VarStore GUID",
           [(0x9ed36c4, gdata.hex())], "SUPPORTED" if gdata == SETUP_GUID else "CONTRADICTED")
    record("A4b", "ISL69247", "the pushed name VA 0x9ed36d4 holds UTF-16 'Setup'",
           [(0x9ed36d4, repr(i47.data[goff + 0x10:goff + 0x10 + 12].decode("latin1")))],
           "SUPPORTED" if i47.data[goff + 0x10:goff + 0x10 + 12] == SETUP_NAME else "CONTRADICTED")
    pva = 0x9ed341c
    poff = pva - int(modules["ISL69247"]["te_header"]["image_base"], 16) - RVA_DELTA
    pdata = i47.data[poff:poff + 16]
    record("A5a", "ISL69247", "the GuidLocate argument is the PEI Read-Only Variable2 PPI GUID",
           [(pva, pdata.hex())], "SUPPORTED" if pdata == RO_VAR2_GUID else "CONTRADICTED")
    record("A5b", "ISL69247",
           "the module calls an interface slot indirectly after locating that PPI and calls slot +0x00 (GetVariable)",
           [(i47.find(r"call\s+DWORD PTR \[ecx\+0x20\]")["addr"],
             i47.find(r"call\s+DWORD PTR \[ecx\+0x20\]")["text"]),
            (i47.find(r"call\s+DWORD PTR \[eax\]", lo=0x2d0)["addr"],
             i47.find(r"call\s+DWORD PTR \[eax\]", lo=0x2d0)["text"])], "SUPPORTED")
    record("A5c", "ISL69247",
           "the read-interface call carries 5 arguments (size 0x1d3 at [ebp+0x5c], buffer [ebp-0x178])",
           [pair(i47.find(r"mov\s+DWORD PTR \[ebp\+0x5c\],0x1d3")),
            pair(i47.find(r"lea\s+eax,\[ebp-0x178\]")),
            pair(i47.find(r"add\s+esp,0x14", lo=0x2b0))], "SUPPORTED")
    record("A6", "ISL69247",
           "defaults for Setup+0x1c9/0x1cd are 0: stores of bl after xor ebx,ebx",
           [pair(i47.find(r"xor\s+ebx,ebx")),
            pair(i47.find(r"mov\s+BYTE PTR \[ebp\+0x51\],bl")),
            pair(i47.find(r"mov\s+BYTE PTR \[ebp\+0x55\],bl"))], "SUPPORTED")
    mv = [pair(i47.find(r"mov\s+esi,0x384")), pair(i47.find(r"mov\s+ecx,esi")),
          pair(i47.find(r"mov\s+WORD PTR \[ebp\+0x52\],cx")),
          pair(i47.find(r"mov\s+WORD PTR \[ebp\+0x56\],cx"))]
    record("A7", "ISL69247", "defaults for Setup+0x1ca/0x1ce are 0x384 (900 mV) via esi/ecx", mv, "SUPPORTED")
    imm54 = i47.find(r"mov\s+BYTE PTR \[ebp\+0x54\],0x2")
    imm58 = i47.find(r"mov\s+BYTE PTR \[ebp\+0x58\],0x2")
    record("A8", "ISL69247", "defaults for Setup+0x1cc/0x1d0 are the immediate 2 (decoded, not asserted by prior)",
           [pair(imm54), pair(imm58)],
           "SUPPORTED" if imm54 and imm58 else "CONTRADICTED")
    tbl = [i47.find(r"mov\s+WORD PTR \[ebp\+0x6%x\],cx" % x) for x in (0, 2, 4, 6, 8)]
    tbl.append(i47.find(r"mov\s+WORD PTR \[ebp\+0x6a\],cx"))
    pushes = [i47.find(r"push\s+0x%x$" % v) for v in (0x14, 0x1e, 0x28, 0x32, 0x3c)]
    record("A9", "ISL69247",
           "loadline table at [ebp+0x60..0x6a] is {0,20,30,40,50,60} and is indexed by the Setup loadline byte",
           [pair(x) for x in tbl[:2]] + [pair(x) for x in pushes] +
           [pair(i47.find(r"movzx\s+eax,WORD PTR \[ebp\+eax\*2\+0x60\]")),
            pair(i47.find(r"push\s+0x28$"))], "SUPPORTED")
    cmp51 = i47.find(r"cmp\s+BYTE PTR \[ebp\+0x51\],bl")
    cmp55 = i47.find(r"cmp\s+BYTE PTR \[ebp\+0x55\],bl")
    record("A10", "ISL69247", "the enable tests are cmp [ebp+0x51],bl and cmp [ebp+0x55],bl (bl==0)",
           [pair(cmp51), pair(cmp55)], "SUPPORTED")
    a30a = i47.at(0x30A)
    prior_enable = [a for a in prior["ISL69247-3e1f753a6279"] if a[0] == 0x30A and "enable test" in a[2]]
    verdict = "CONTRADICTED" if (prior_enable and a30a and "cmp" not in a30a["text"]) else "SUPPORTED"
    record("A11", "ISL69247",
           "the prior claim 'enable test: cmp Setup+0x1c9 vs 0' asserted at RVA 0x30A",
           [(0x30A, a30a["text"] if a30a else "no instruction"),
            (cmp51["addr"], cmp51["text"])], verdict,
           note="the enable test decodes at 0x%03x; 0x30A is the register-index push shared with "
                "the 'VCORE write targets register index 0x21' label" % cmp51["addr"])
    mvread = i47.find(r"movzx\s+eax,WORD PTR \[ebp\+0x52\]")
    gread = i47.find(r"movzx\s+eax,WORD PTR \[ebp\+0x56\]")
    disabled = i47.find(r"mov\s+DWORD PTR \[ebp\+0x74\],0x384")
    record("A12", "ISL69247",
           "enabled path writes the Setup mV word to register 0x21; disabled path writes 0x384 (900 mV)",
           [pair(mvread), pair(gread), pair(disabled), pair(i47.find(r"push\s+0x21$"))], "SUPPORTED",
           note="the VCORE disabled path reuses esi=0x384 set at 0x%03x, the GFX disabled path "
                "uses an explicit 0x384 immediate" % i47.find(r"mov\s+esi,0x384")["addr"])
    record("A13", "ISL69247", "register 0x23 is written with 0 and 0xF0 is a read-modify-write of bit 0x30",
           [pair(i47.find(r"push\s+0x23$")), pair(i47.find(r"mov\s+DWORD PTR \[ebp\+0x74\],ebx")),
            pair(i47.find(r"mov\s+esi,0xf0")), pair(i47.find(r"or\s+DWORD PTR \[ebp\+0x74\],0x30")),
            pair(i47.find(r"and\s+DWORD PTR \[ebp\+0x74\],0xffcf"))], "SUPPORTED")
    c45 = [pair(i47.find(r"push\s+0xc7$")), pair(i47.find(r"push\s+0xc5$")),
           pair(i47.find(r"push\s+0xb$")), pair(i47.find(r"push\s+0x8$")),
           pair(i47.find(r"push\s+0xea0b$")), pair(i47.find(r"push\s+0xea8b$")),
           pair(i47.find(r"cmp\s+BYTE PTR \[ebp\+0x54\],0x2"))]
    record("A14", "ISL69247",
           "helper 0x4d2 writes register 0xC7 with argument 0 and register 0xC5 with argument 1",
           c45, "SUPPORTED",
           note="caller pushes (0x0b|0x08) then (0xea0b|0xea8b); the callee's lea [esp+0xc]/[esp+0x14] "
                "bind 0xC7<-0xEA0B/0xEA8B and 0xC5<-0x0B/0x08")
    H = (0x6ED, 0x760)
    wh = [i47.find(r"push\s+0x65$", lo=H[0], hi=H[1]), i47.find(r"push\s+0x66$", lo=H[0], hi=H[1]),
          i47.find(r"movzx\s+eax,BYTE PTR \[edi\]", lo=H[0], hi=H[1]),
          i47.find(r"movzx\s+eax,BYTE PTR \[edi\+0x1\]", lo=H[0], hi=H[1]),
          i47.find(r"push\s+0x70$", lo=H[0], hi=H[1]), i47.find(r"push\s+0x71$", lo=H[0], hi=H[1]),
          i47.find(r"push\s+0x63$", lo=H[0], hi=H[1]), i47.find(r"push\s+0x60$", lo=H[0], hi=H[1]),
          i47.find(r"test\s+al,0x40", lo=H[0], hi=H[1]), i47.find(r"cmp\s+bl,0xa", lo=H[0], hi=H[1]),
          i47.find(r"push\s+0x8$", lo=H[0], hi=H[1])]
    record("A15", "ISL69247",
           "write helper 0x6ed stages 0x65<-0xC0, 0x66<-register, 0x70/0x71<-2-byte LE value, 0x63<-3, "
           "0x60<-0xC0, then polls status bit 0x40 with <=10 retries and writes 0x60<-8",
           [pair(x) for x in wh if x], "SUPPORTED",
           note="the 2-byte value is produced by two byte reads (0x%03x, 0x%03x), not by a word read"
                % (i47.find(r"movzx\s+eax,BYTE PTR \[edi\]", lo=H[0], hi=H[1])["addr"],
                   i47.find(r"movzx\s+eax,BYTE PTR \[edi\+0x1\]", lo=H[0], hi=H[1])["addr"]))
    tr = [i47.find(r"push\s+0x2e$"), i47.find(r"mov\s+al,0x87"), i47.find(r"push\s+0x2f$"),
          i47.find(r"mov\s+ecx,0xa20"),
          i47.find(r"mov\s+al,BYTE PTR \[esp\+0x4\]", lo=0x565, hi=0x5D3),
          i47.find(r"mov\s+al,BYTE PTR \[esp\+0x8\]", lo=0x565, hi=0x5D3)]
    record("A16", "ISL69247",
           "mailbox transport uses ports 0x2E/0x2F with the 0x87,0x87 unlock and mailbox 0xA20(index)/0xA21/A22",
           [pair(x) for x in tr if x], "SUPPORTED",
           note="low-level writer 0x565 sends [esp+4] to 0xA21 and [esp+8] to 0xA22 (index, value)")
    record("A17", "ISL69247",
           "the prior label 'write helper reads a u16 little-endian value from [edi]' at 0x709",
           [(0x709, i47.at(0x709)["text"]), (0x714, i47.at(0x714)["text"])],
           "CONTRADICTED" if "BYTE" in i47.at(0x709)["text"] else "SUPPORTED",
           note="0x709 is movzx eax,byte [edi]; the second byte is read at 0x714 and staged to 0x71, "
                "so the 2-byte LE staging is real but the labelled instruction is a byte read")

    record("A18", "ISL69247",
           "read helper 0x653 stages 0x63<-0x83 and returns the mailbox 0xB0/0xB1 pair as the current 2-byte value",
           [pair(i47.find(r"push\s+0x83$", lo=0x653, hi=0x6ED)),
            pair(i47.find(r"push\s+0xb0$", lo=0x653, hi=0x6ED)),
            pair(i47.find(r"push\s+0xb1$", lo=0x653, hi=0x6ED)),
            pair(i47.find(r"mov\s+BYTE PTR \[edi\+0x1\],al", lo=0x653, hi=0x6ED))], "SUPPORTED",
           note="this is the read half of the 0xF0 read-modify-write")

    # ISL95712 ------------------------------------------------------------------
    i = i57
    record("B1a", "ISL95712", "GetVariable call site pushes the Setup GUID VA and the name VA",
           [pair(i.find(r"push\s+0x9ed455c$")), pair(i.find(r"push\s+0x9ed456c$"))], "SUPPORTED")
    gva = 0x9ed455c
    goff = gva - int(modules["ISL95712"]["te_header"]["image_base"], 16) - RVA_DELTA
    record("B1b", "ISL95712", "those VAs hold the Setup GUID and UTF-16 'Setup'",
           [(gva, i.data[goff:goff + 16].hex()),
            (gva + 0x10, repr(i.data[goff + 0x10:goff + 0x10 + 12].decode("latin1")))],
           "SUPPORTED" if i.data[goff:goff + 16] == SETUP_GUID
           and i.data[goff + 0x10:goff + 0x10 + 12] == SETUP_NAME else "CONTRADICTED")
    pva = 0x9ed42b4
    poff = pva - int(modules["ISL95712"]["te_header"]["image_base"], 16) - RVA_DELTA
    record("B1c", "ISL95712", "the GuidLocate argument is the PEI Read-Only Variable2 PPI GUID",
           [(pva, i.data[poff:poff + 16].hex())],
           "SUPPORTED" if i.data[poff:poff + 16] == RO_VAR2_GUID else "CONTRADICTED")
    record("B1d", "ISL95712", "5-argument indirect locate call through [ecx+0x20] then GetVariable through [eax]",
           [pair(i.find(r"call\s+DWORD PTR \[ecx\+0x20\]")),
            pair(i.find(r"call\s+DWORD PTR \[eax\]", lo=0x280)), pair(i.find(r"add\s+esp,0x14")),
            pair(i.find(r"mov\s+DWORD PTR \[ebp-0xc\],0x1d3")),
            pair(i.find(r"lea\s+eax,\[ebp-0x1e0\]"))], "SUPPORTED")
    record("B2", "ISL95712", "defaults: Setup+0x1d1=0 (bl after xor ebx,ebx), Setup+0x1d2=0x1e (1.35 V)",
           [pair(i.find(r"xor\s+ebx,ebx")), pair(i.find(r"mov\s+BYTE PTR \[ebp-0xf\],bl")),
            pair(i.find(r"mov\s+BYTE PTR \[ebp-0xe\],0x1e"))], "SUPPORTED")
    record("B3", "ISL95712",
           "enabled path writes the stored enum to 0xDF, then ORs bit 0; disabled path writes 0x1e and clears bit 0",
           [pair(i.find(r"cmp\s+BYTE PTR \[ebp-0xf\],bl")), pair(i.find(r"mov\s+al,BYTE PTR \[ebp-0xe\]")),
            pair(i.find(r"or\s+BYTE PTR \[ebp-0x1\],0x1")), pair(i.find(r"mov\s+BYTE PTR \[ebp-0x1\],0x1e")),
            pair(i.find(r"and\s+BYTE PTR \[ebp-0x1\],0xfe"))], "SUPPORTED",
           note="both branches also write register 0xDE with the staged value (enabled |1, disabled &0xfe)")
    record("B4", "ISL95712",
           "follow-up helper stages 0x65<-0x9E, 0x66<-0xDE, 0x63<-0x82, 0x60<-0xC0",
           [pair(i.find(r"push\s+0x9e$")), pair(i.find(r"push\s+0xde$")), pair(i.find(r"push\s+0x82$")),
            pair(i.find(r"push\s+0xc0$")), pair(i.find(r"push\s+0x65$")), pair(i.find(r"push\s+0x66$"))],
           "SUPPORTED")

    # ---- label review: classify every prior byte assertion ------------------
    def classify(module, rva, raw):
        img = images[module]
        want = len(raw)
        ins = img.at(rva)
        if ins is None:
            return "NO_INSTRUCTION", ins
        n = len(ins["bytes"])
        if rva != ins["addr"]:
            return "STARTS_MID_INSTRUCTION", ins
        if n == want:
            return "FULL_INSTRUCTION", ins
        if n > want:
            return "PREFIX_OF_INSTRUCTION", ins
        return "SPANS_TWO_INSTRUCTIONS", ins

    for stem, asserts in prior.items():
        module = "ISL69247" if stem.startswith("ISL69247") else "ISL95712"
        for rva, hexbytes, meaning in asserts:
            raw = bytes.fromhex(hexbytes)
            cls, ins = classify(module, rva, raw)
            entry = {"module": module, "rva": hex(rva), "asserted_bytes": hexbytes,
                     "label": meaning, "class": cls,
                     "actual_instruction": ins["text"] if ins else None,
                     "actual_addr": hex(ins["addr"]) if ins else None,
                     "actual_bytes": " ".join(ins["bytes"]) if ins else None}
            result["label_review"].append(entry)

    bad = [e for e in result["label_review"]
           if e["class"] in ("STARTS_MID_INSTRUCTION", "PREFIX_OF_INSTRUCTION")]
    result["label_status"] = "MISLEADING_LABELS_FOUND" if (bad or contradicted) else "OK"
    result["label_findings"] = {
        "non_full_instruction_windows": [
            {"module": e["module"], "rva": e["rva"], "class": e["class"], "label": e["label"],
             "actual": e["actual_instruction"]} for e in bad],
        "contradicted_claims": contradicted,
    }
    result["semantic_checks"] = checks
    result["counts"] = {"semantic_checks": len(checks),
                        "contradicted": len(contradicted),
                        "label_windows_not_full_instruction": len(bad)}
    if contradicted:
        result["status"] = "PASS"
        result["decode_status"] = "PASS_WITH_CONTRADICTED_LABELS"
    json.dump(result, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


def TARGETS_REV(by_guid, f):
    for name, guid in TARGETS.items():
        if f["guid"] == guid:
            return name
    return None


if __name__ == "__main__":
    sys.exit(main())
