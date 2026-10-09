#!/usr/bin/env python3
"""Decode the PSP type-0x24 SEC GASKET policy record structure.

Ground truth: A1-replay WRITES (from the board campaign) = [window, smn_addr, value].
Hypothesis: the policy stores records of (window?, addr, value, ...) around the
pattern hits. Dump dword context around each hit and test adjacency of known
(addr, value) pairs from the A1 list.
"""
import os, struct, sys, re

GK = (r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries"
      r"\BC250_3.00_CHIPSETMENU.ROM\07_t24_0x982000_2E50.bin")
REPLAY = (r"C:\Users\OWNER\tmp_bc250\bc250_firmware\campaign"
          r"\smn_full_gasket_replay.py")

def load_replay_writes():
    """Parse WRITES = [["0x201",151138868,0], ...] from the replay script."""
    with open(REPLAY, "r", encoding="utf-8") as f:
        src = f.read()
    m = re.search(r"WRITES\s*=\s*(\[.*?\])\s*\n", src, re.S)
    if not m:
        sys.exit("WRITES not found in replay")
    wr = eval(m.group(1))  # trusted local campaign file
    return [(w[0], w[1], w[2]) for w in wr]

def hexdump(data, base, rows, width=16):
    out = []
    for r in range(rows):
        off = base + width * r
        chunk = data[off:off + width]
        if not chunk:
            break
        hexs = " ".join(f"{b:02x}" for b in chunk)
        txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"  {off:06X}: {hexs}  {txt}")
    return "\n".join(out)

def main():
    with open(GK, "rb") as f:
        g = f.read()
    writes = load_replay_writes()
    print(f"blob: {len(g):,} bytes; A1 writes: {len(writes)}")
    print(f"windows in A1: {sorted({w[0] for w in writes})}")

    # 1) dword dump around key hit offsets
    for off, label in [(0x100, "hit 0x09023234 @0x148 area"),
                       (0x2540, "DF win 0x03A2011C @0x2560 area"),
                       (0x27A0, "DF win 0x0322011C @0x27C0 area"),
                       (0x28A0, "VCN_SEG records @0x28C0..0x2930"),
                       (0x2AA0, "0x09023234 @0x2AC0 + 0x0322011C @0x2C58 area")]:
        print("=" * 96)
        print(f"REGION {label}:")
        print(hexdump(g, off, rows=14))

    # 2) adjacency test: for each A1 write, is (addr) found in blob with the
    #    A1 value within +/- 16 bytes?
    print("=" * 96)
    print("ADJACENCY TEST (A1 addr->value in blob):")
    stats = {"adj+4": 0, "adj-4": 0, "addr-only": 0, "missing": 0}
    examples = []
    for win, addr, val in writes[:400]:
        pat = struct.pack("<I", addr)
        i = g.find(pat)
        if i < 0:
            stats["missing"] += 1
            continue
        vpat = struct.pack("<I", val)
        found = None
        for delta in (4, 8, -4, 12, 16):
            if 0 <= i + delta <= len(g) - 4:
                if g[i + delta:i + delta + 4] == vpat:
                    found = delta
                    break
        if found == 4:
            stats["adj+4"] += 1
        elif found == -4:
            stats["adj-4"] += 1
        elif found is not None:
            stats[f"adj{found:+d}"] = stats.get(f"adj{found:+d}", 0) + 1
        else:
            stats["addr-only"] += 1
            if len(examples) < 8:
                examples.append((hex(addr), hex(val), hex(i)))
    print(" ", stats)
    print("  addr-found-but-value-not-adjacent examples:",
          examples)
    # 3) count total addr hits for all A1 writes
    hitcount = 0
    for win, addr, val in writes:
        if g.find(struct.pack("<I", addr)) >= 0:
            hitcount += 1
    print(f"  A1 addrs present in blob: {hitcount}/{len(writes)}")

if __name__ == "__main__":
    sys.exit(main())
