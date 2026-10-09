#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ARM/Thumb hunt disassembler for PSP blobs (t02 TOS, t28 drivers).

Produces:
  - ARM listing + Thumb listing (linear)
  - literal-pool resolution: every `ldr rX, [pc, #imm]` annotated with the
    u32 it loads (data pools are invisible to naive constant scans)
  - watch-list report: interesting constants (APCB group IDs, magics,
    SMN addresses, APCB instance stamps)
"""
import sys, re, struct
import capstone

WATCH = {
    0x1703: "DFG GroupId (Data Fabric Group)",
    0x1701: "PSPG GroupId",
    0x1702: "CCXG GroupId",
    0x1704: "MEMG GroupId",
    0x1705: "GNBG GroupId",
    0x1706: "FCHG GroupId",
    0x1708: "OEMG GroupId",
    0x3000: "TOKN GroupId",
    0x42435041: "'APCB' magic u32",
    0x00200020: "APCB hdr {0x20,0x20} pair",
    0x31535024: "'$PS1' magic u32",
    0x47435041: "'ACPG'?",
    0x220E: "UniqueApcbInstance 3.00",
    0x1C05: "UniqueApcbInstance 5.00",
    0x25DE: "UniqueApcbInstance 4.00",
    0x0900C234: "VCN SMN ctrl",
    0x0900C914: "VCN SMN policy",
    0x1C76: "DF fabric window 0x1C76x",
    0x1C78: "DF fabric window 0x1C78x",
    0x0024: "gasket type 0x24",
    0xAB1000: "APCB flash offset",
    0x0030: "APCB v3 version",
    0x67452301: "SHA256 h0",
    0xEFCDAB89: "SHA256 h1",
    0x9E3779B9: "TEA/xxhash delta",
}


def disasm_mode(data, base, start, size, mode, mode_name):
    md = capstone.Cs(capstone.CS_ARCH_ARM, mode)
    md.detail = True
    md.skipdata = True  # continue past undecodable bytes (pools/data)
    out = []
    pool_refs = []
    text = data[start:start + size]
    for ins in md.disasm(text, base + start):
        if ins.mnemonic == ".byte":
            continue  # skipdata filler
        line = "0x%08x: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str)
        # literal pool load resolution (op_str has no mnemonic!)
        m = re.match(r"^(\w+),\s*\[pc,\s*#(-?0x[0-9a-f]+|-?\d+)\]$", ins.op_str, re.I)
        if m:
            off = int(m.group(2), 0)
            # ARM: pc = addr+8; Thumb: pc = addr+4
            pc = ins.address + (8 if mode_name == "arm" else 4)
            target = pc + off
            rel = target - base
            if 0 <= rel <= len(data) - 4:
                val = struct.unpack_from("<I", data, rel)[0]
                note = "  ; [pool@0x%x] = 0x%08x" % (target, val)
                if val in WATCH:
                    note += "  <<< %s" % WATCH[val]
                line += note
                pool_refs.append((ins.address, target, val))
        # watch-list immediates
        for mm in re.finditer(r"#(0x[0-9a-f]+|\d+)\b", ins.op_str):
            try:
                v = int(mm.group(1), 0)
            except ValueError:
                continue
            if v in WATCH:
                line += "  ; IMM <<< %s" % WATCH[v]
        out.append(line)
    return out, pool_refs


def main():
    if len(sys.argv) < 3:
        print("usage: psp_disasm_hunt.py <blob.bin> <body_off> [size]")
        return 1
    path = sys.argv[1]
    body_off = int(sys.argv[2], 0)
    data = open(path, "rb").read()
    size = int(sys.argv[3], 0) if len(sys.argv) > 3 else len(data) - body_off
    base = 0  # addresses = file offsets

    results = {}
    for mode, name in ((capstone.CS_MODE_ARM, "arm"), (capstone.CS_MODE_THUMB, "thumb")):
        lines, pool = disasm_mode(data, base, body_off, size, mode, name)
        results[name] = (lines, pool)
        # validity score: count lines that look like real instructions
        print("%s: %d instructions decoded" % (name, len(lines)))

    # choose better mode per 0x400 window: score = decoded BYTE coverage
    best = []
    window = 0x400
    cov = {}
    for name in ("arm", "thumb"):
        c = {}
        for l in results[name][0]:
            a = int(l.split(":")[0], 16)
            w = a & ~(window - 1)
            c[w] = c.get(w, 0) + (4 if name == "arm" else 2)  # approx insn size
        cov[name] = c
    for wstart in range(body_off, body_off + size, window):
        wend = min(wstart + window, body_off + size)
        wkey = wstart & ~(window - 1)
        armc = cov["arm"].get(wkey, 0)
        thc = cov["thumb"].get(wkey, 0)
        pick = "arm" if armc >= thc else "thumb"
        src = results[pick][0]
        for l in src:
            a = int(l.split(":")[0], 16)
            if wstart <= a < wend:
                best.append((a, "[%s] %s" % (pick[0].upper(), l)))
    best.sort()

    outfile = path + ".hunt.txt"
    with open(outfile, "w", encoding="utf-8") as f:
        for a, l in best:
            f.write(l + "\n")
    print("mixed listing ->", outfile, "(%d lines)" % len(best))

    # watch-list report from pool refs (both modes)
    print("\n=== WATCH-LIST POOL HITS ===")
    seen = set()
    for name in ("arm", "thumb"):
        for addr, target, val in results[name][1]:
            if val in WATCH and (target, val) not in seen:
                seen.add((target, val))
                print("  [%s] insn@0x%08x pool@0x%x = 0x%08x  <<< %s"
                      % (name, addr, target, val, WATCH[val]))
    # raw u32 pool scan (data, not instructions) for watch values
    print("\n=== RAW u32 WATCH HITS (whole blob) ===")
    for off in range(0, len(data) - 3, 4):
        v = struct.unpack_from("<I", data, off)[0]
        if v in WATCH:
            print("  @0x%06x = 0x%08x  <<< %s" % (off, v, WATCH[v]))

    # constant census: all u32s in interesting address ranges
    print("\n=== u32 CENSUS (SMN 0x03xx/0x09xx, TMR 0x0Exx, DF 0x1C7x ranges) ===")
    def interesting(v):
        if 0x03000000 <= v < 0x03300000: return "SMN 0x03xx"
        if 0x09000000 <= v < 0x0A000000: return "SMN 0x09xx (DF/gasket banks)"
        if 0x0E000000 <= v < 0x0E200000: return "PSP TMR"
        if 0x1C760000 <= v < 0x1C790000: return "DF fabric 0x1C7x"
        return None
    census = {}
    for off in range(0, len(data) - 3, 4):
        v = struct.unpack_from("<I", data, off)[0]
        cat = interesting(v)
        if cat:
            census.setdefault(cat, []).append((off, v))
    for cat, items in census.items():
        print("  %s: %d hits" % (cat, len(items)))
        for off, v in items[:20]:
            print("    @0x%06x = 0x%08x" % (off, v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
