#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APCB checksum brute-force (D1).
Samples: BC250_3.00 (0x220E, size 0xB64), dump_5.00 (0x1C05, 0xB64),
my_4.0_MODED (0x25DE, 0xB64), Robin5.00 (0x1C05, 0x488).
Try: u8/u16/u32 sums (LE/BE), ones-complement, rotate/BSD, fletcher16,
CRC16 variants, CRC32&0xFFFF, over spans with/without zeroed cks field.
An algorithm is SOLVED only if it reproduces ALL samples.
"""
import struct, sys, zipfile, functools, itertools

FILES = [
    (r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00_CHIPSETMENU.ROM", 0x220E, "3.00"),
    (r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\dump_5.00.bin",              0x1C05, "5.00dump"),
    (r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\my_4.0_MODED.bin",           0x25DE, "4.0mod"),
    (r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\Robin5.00",                  0x1C05, "Robin5"),
    # 4700S (0x24ed) — separate BIOS file, loaded below if present
]

def load_samples():
    samples = []
    for path, cks, name in FILES:
        try:
            with open(path, "rb") as f:
                d = bytearray(f.read())
        except OSError as e:
            print("skip", name, e); continue
        base = 0xAB1000
        size = struct.unpack_from("<I", d, base + 8)[0]
        samples.append((name, bytearray(d[base:base + max(size, 0x488 + 4)]), size, cks))
    # 4700S from extracted dir
    p4700 = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\4700S\C0A\4700S_c0a_BIOS.bin"
    import os
    cands = [p4700]
    for root, _, fs in os.walk(r"C:\Users\OWNER\tmp_bc250\bc250_firmware\4700S"):
        for f in fs:
            if f.lower().endswith((".bin", ".rom", ".cap")) and "flash" not in f.lower():
                cands.append(os.path.join(root, f))
    for c in cands:
        try:
            with open(c, "rb") as f:
                d = bytearray(f.read())
        except OSError:
            continue
        if len(d) < 0xAB2000:
            continue
        off = d.find(b"APCB", 0, 0x2000000)
        while off != -1:
            if struct.unpack_from("<I", d, off + 8)[0] > 0x100:
                size = struct.unpack_from("<I", d, off + 8)[0]
                cks = struct.unpack_from("<H", d, off + 12)[0]
                samples.append(("4700S@%X" % off, bytearray(d[off:off + size]), size, cks))
                break
            off = d.find(b"APCB", off + 1, 0x2000000)
        break
    return samples

def crc16_variants():
    # (name, poly, init, refin, refout, xorout)
    return {
        "ccitt-false": (0x1021, 0xFFFF, False, False, 0x0000),
        "xmodem":      (0x1021, 0x0000, False, False, 0x0000),
        "kermit":      (0x1021, 0x0000, True,  True,  0x0000),
        "modbus":      (0x8005, 0xFFFF, True,  True,  0x0000),
        "arc/ibm":     (0x8005, 0x0000, True,  True,  0x0000),
        "usb":         (0x8005, 0xFFFF, True,  True,  0xFFFF),
        "maxim":       (0x8005, 0x0000, True,  True,  0xFFFF),
        "dnp":         (0x3D65, 0x0000, True,  True,  0xFFFF),
    }

def crc16(data, poly, init, refin, refout, xorout):
    crc = init
    for b in data:
        if refin:
            crc ^= b
            for _ in range(8):
                crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
        else:
            crc ^= b << 8
            for _ in range(8):
                crc = (crc << 1) ^ poly if crc & 0x8000 else (crc << 1)
                crc &= 0xFFFF
    if refout != refin:
        # bit-reflect 16
        crc = int('{:016b}'.format(crc)[::-1], 2)
    return (crc ^ xorout) & 0xFFFF

def fletcher16(data):
    a = b = 0
    for x in data:
        a = (a + x) % 255
        b = (b + a) % 255
    return (b << 8) | a

def crc32(data):
    return zipfile.zlib.crc32(bytes(data)) & 0xFFFFFFFF

def span_variants(blob, size):
    """yield (span_name, bytes) covering plausible coverage regions"""
    cks_off = 12
    full = blob[:size]
    zeroed = bytearray(full); zeroed[cks_off:cks_off+2] = b"\x00\x00"
    hdr_end = 0x20
    yield "full_raw", bytes(full)
    yield "full_zeroed", bytes(zeroed)
    yield "body", bytes(full[hdr_end:])
    yield "body_zeroed_skip_hdr", bytes(zeroed[hdr_end:])
    yield "hdr_only", bytes(full[:hdr_end])

def main():
    samples = load_samples()
    print("loaded %d samples:" % len(samples))
    for name, blob, size, cks in samples:
        print("  %-12s size=0x%-5X cks=0x%04X" % (name, size, cks))
    print()
    winners = []
    tested = 0
    # --- sum family ---
    for name, blob, size, exp in samples:
        for span_name, data in span_variants(blob, size):
            tested += 1
    # (compute per algorithm across all samples; collect match count)
    algos = {}
    def reg(aname, fn):
        algos[aname] = fn
    reg("u8sum", lambda d: sum(d) & 0xFFFF)
    reg("u16sum_LE", lambda d: sum(struct.unpack("<%dH" % (len(d)//2), d[:len(d)//2*2])) & 0xFFFF)
    reg("u16sum_BE", lambda d: sum(struct.unpack(">%dH" % (len(d)//2), d[:len(d)//2*2])) & 0xFFFF)
    reg("u32sum_LE", lambda d: sum(struct.unpack("<%dI" % (len(d)//4), d[:len(d)//4*4])) & 0xFFFF)
    reg("u8sum_neg", lambda d: (-sum(d)) & 0xFFFF)
    reg("u16sum_neg", lambda d: (-sum(struct.unpack("<%dH" % (len(d)//2), d[:len(d)//2*2]))) & 0xFFFF)
    reg("u8sum_xor", lambda d: functools.reduce(lambda a, b: a ^ b, d, 0) & 0xFFFF)
    reg("u8sum_onescomp", lambda d: ((~sum(d)) & 0xFFFF))
    reg("fletcher16", fletcher16)
    reg("crc32_low", lambda d: crc32(d) & 0xFFFF)
    reg("crc32_high", lambda d: crc32(d) >> 16)
    for vname, (poly, init, refin, refout, xorout) in crc16_variants().items():
        reg("crc16_" + vname, lambda d, p=poly, i=init, ri=refin, ro=refout, x=xorout: crc16(d, p, i, ri, ro, x))
    # BSD rotate-right sum
    def bsd(d):
        c = 0
        for x in d:
            c = ((c >> 1) | ((c & 1) << 15)) & 0xFFFF
            c = (c + x) & 0xFFFF
        return c
    reg("bsd_rot", bsd)
    def bsd2(d):
        c = 0
        for x in d:
            c = ((c >> 1) | ((c & 1) << 15)) & 0xFFFF
            c = (c + x + 1) & 0xFFFF
        return c
    reg("bsd_rot_plus1", bsd2)
    # sum of u16 pairs of (byte,byte) as BE inside LE walk etc.
    def sum16_mixed(d):
        s = 0
        for i in range(0, len(d) - 1, 2):
            s += d[i] + (d[i+1] << 8)
        return s & 0xFFFF
    reg("u16pair_sum", sum16_mixed)

    for aname, fn in sorted(algos.items()):
        per_sample = []
        for name, blob, size, exp in samples:
            got = None
            for span_name, data in span_variants(blob, size):
                try:
                    v = fn(data)
                except Exception:
                    v = None
                if v == exp:
                    got = span_name
                    break
            per_sample.append((name, got))
        nm = sum(1 for _, g in per_sample if g)
        if nm == len(samples):
            print("[ALL-MATCH] %-16s %s" % (aname, ["%s:%s" % (n, g) for n, g in per_sample]))
            winners.append((aname, per_sample))
        elif nm >= 2:
            print("[partial %d/%d] %-16s %s" % (nm, len(samples), aname, ["%s:%s" % (n, g) for n, g in per_sample]))
    if not winners:
        print("\nno algorithm matched all samples yet (tried %d combos x %d algos)" % (tested//max(1,len(samples)), len(algos)))
    return winners

if __name__ == "__main__":
    main()
