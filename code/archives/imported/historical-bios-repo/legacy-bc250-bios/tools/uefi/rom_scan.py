#!/usr/bin/env python3
"""Full-image RE scan of the BC-250/PS5 ROM corpus.

For each image:
  - full scan for: $PSP / $BIOS / $VRM cookies, 0x55AA, ATOMBIOS, discovery sig
    0x28211407, SLB2, AMDRBN
  - parse any AMD IP-discovery blob found (binary_header + ip_discovery_header +
    die/IP records + harvest table + VCN info table)  [structs: discovery.h]
  - light-parse $PSP / $BIOS directories (hexdump + 16B-entry guess)
  - scan for AMD fw-header signature ([total][hdr2][1][type][ver][total-0x100][0x100][hash])
"""
import struct, sys, os

CHAT = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
FIRM = r"C:\Users\OWNER\tmp_bc250\bc250_firmware"

IMAGES = [
    os.path.join(CHAT, "BC250_3.00_CHIPSETMENU.ROM"),
    os.path.join(CHAT, "BC250_3.00.ROM"),
    os.path.join(CHAT, "bc250 modded bios.ROM"),
    os.path.join(CHAT, "8_cores_Steam.rom"),
    os.path.join(CHAT, "bc250-Steam.rom"),
    os.path.join(CHAT, "Robin5.00"),
    os.path.join(CHAT, "W25Q128BV@WSON8_20250122_140516.BIN"),
    os.path.join(CHAT, "PS5 Disk Edition EDM-010 (CFI-1015A) working BIOS.bin"),
    os.path.join(CHAT, "MX25L4006E_BC-250.bin"),
    os.path.join(FIRM, "vbios_robin.bin"),
    os.path.join(FIRM, "discovery_robin.bin"),
]
if len(sys.argv) > 1:
    IMAGES = sys.argv[1:]

DISCOVERY_SIG = b"\x07\x14\x21\x28"

# hw_id names (soc15_hw_ip.h, subset + full list from amdgpu_discovery.c)
HWID = {
    0: "UNKNOWN", 1: "SMUIO", 2: "FUSE", 3: "CLKA", 4: "PWR", 5: "GC", 6: "UVD(VCN)",
    7: "AUDIO_AZ", 8: "ACP", 9: "DCI", 10: "DMU(DCE)", 11: "DCO", 12: "DIO", 13: "XDMA",
    14: "DCEAZ", 15: "DAZ", 16: "SDPMUX", 17: "NTB", 18: "IOHC", 19: "L2IMU", 20: "VCE",
    21: "MMHUB", 22: "ATHUB", 23: "DBGU_NBIO", 24: "DFX", 25: "DBGU0", 26: "DBGU1",
    27: "OSSSYS", 28: "HDP", 32: "SDMA0", 33: "SDMA1", 34: "SDMA2", 35: "SDMA3",
    36: "ISP", 37: "DBGU_IO", 38: "DF", 40: "CLKB", 41: "FCH", 42: "DFX_DAP",
    43: "L1IMU_PCIE", 44: "L1IMU_NBIF", 45: "L1IMU_IOAGR", 59: "PCIE", 60: "PCS",
    62: "IOAGR", 63: "NBIF", 64: "IOAPIC", 65: "SYSTEMHUB", 66: "NTBCCP", 67: "UMC",
    68: "SATA", 69: "USB", 70: "CCXSEC", 71: "XGMI", 72: "XGBE", 80: "MP0",
    81: "MP1", 88: "THM", 90: "MP2",
}

def read_all(path):
    with open(path, "rb") as f:
        return f.read()

def find_all(blob, sig, limit=40):
    out, i = [], 0
    while len(out) < limit:
        j = blob.find(sig, i)
        if j < 0:
            break
        out.append(j)
        i = j + 1
    return out

def parse_discovery(blob, off, log, tag):
    """Parse an AMD IP-discovery binary at blob offset off. Returns True on success."""
    def rd(fmt, o):
        return struct.unpack_from("<" + fmt, blob, off + o)
    sig, vmaj, vmin, csum, bsize = rd("IHHHH", 0)
    if sig != 0x28211407:
        return False
    log(f"  {tag}: DISCOVERY binary_header @0x{off:X}: ver {vmaj}.{vmin}, "
        f"checksum 0x{csum:04X}, binary_size 0x{bsize:X}")
    if vmaj >= 2:
        ntab, pad = rd("HH", 10)
        tbl_base = 16
    else:
        ntab = 6
        tbl_base = 12
    tables = {}
    for t in range(ntab):
        to, tc, ts, tp = rd("HHHH", tbl_base + 8 * t)
        tables[t] = (to, tc, ts)
        names = {0: "IP_DISCOVERY", 1: "GC", 2: "HARVEST_INFO", 3: "VCN_INFO",
                 4: "MALL_INFO", 5: "NPS_INFO"}
        log(f"    table[{t}] {names.get(t, '?'):14s} off=0x{to:04X} size=0x{ts:04X} "
            f"checksum=0x{tc:04X}")
    # --- IP discovery table ---
    io = tables.get(0, (0, 0, 0))[0]
    if io:
        tsig, tver, tsize, tid, ndies = rd("IHHIH", io)
        log(f"  ip_discovery_header @0x{off+io:X}: sig 0x{tsig:08X} ('"
            f"{blob[off+io:off+io+4].decode('latin1')}'), ver {tver}, size 0x{tsize:X}, "
            f"num_dies {ndies}")
        for d in range(ndies):
            did, doff = rd("HH", io + 8 + 4 * d + 2 + 4)
            # die_info[d]: at io + 10(signum) ... layout: sig4 ver2 size2 id4 num2 then die_info
            dpos = io + 14 + 4 * d
            did, doff = struct.unpack_from("<HH", blob, off + dpos)
            dnum = struct.unpack_from("<H", blob, off + doff + 2)[0]
            log(f"    die[{d}] id={did} off=0x{doff:X} num_ips={dnum}")
            p = doff + 4
            vcn_found = []
            for k in range(dnum):
                hw, inst, nbase, maj, mnr, rev, hr = struct.unpack_from(
                    "<HBBBBBB", blob, off + p)
                bases = struct.unpack_from("<" + "I" * nbase, blob, off + p + 8)
                harvest = hr & 0xF
                name = HWID.get(hw, f"hw{hw}")
                mark = ""
                if "VCN" in name or hw in (6, 20):
                    mark = f"  <<<<< VCN/UVD inst={inst} harvest={harvest}"
                    vcn_found.append((hw, inst, harvest, bases))
                log(f"      ip[{k:02d}] hw_id={hw:<3d} {name:14s} inst={inst} "
                    f"v{maj}.{mnr}.{rev} harvest={harvest} bases="
                    + "+".join(f"0x{b:08X}" for b in bases) + mark)
                p += 8 + 4 * nbase
            for hw, inst, harvest, bases in vcn_found:
                log(f"    *** VCN RECORD: hw_id={hw} inst={inst} harvest={harvest} "
                    f"(0=live,1=harvested) bases={[hex(b) for b in bases]}")
    # --- harvest table ---
    ho = tables.get(2, (0, 0, 0))[0]
    if ho:
        hsig, hver = rd("II", ho)
        log(f"  harvest_table @0x{off+ho:X}: sig 0x{hsig:08X} ('"
            f"{blob[off+ho:off+ho+4].decode('latin1')}') ver {hver}")
        for i in range(32):
            hwid, inst, res = rd("HBB", ho + 8 + 4 * i)
            if hwid == 0:
                break
            log(f"    harvest[{i}] hw_id={hwid} ({HWID.get(hwid, '?')}) instance={inst}")
    # --- VCN info table ---
    vo = tables.get(3, (0, 0, 0))[0]
    if vo:
        vid, vvmaj, vvmin, vsize = rd("IHHI", vo)
        log(f"  vcn_info @0x{off+vo:X}: id 0x{vid:08X} ('"
            f"{blob[off+vo:off+vo+4].decode('latin1')}') ver {vvmaj}.{vvmin} "
            f"size 0x{vsize:X}")
        ninst = rd("I", vo + 12)[0]
        log(f"    num_of_instances={ninst}")
        for i in range(min(ninst, 4)):
            inum, fuse = rd("II", vo + 16 + 16 * i)
            dis = []
            if fuse & 1: dis.append("AV1")
            if fuse & 2: dis.append("VP9")
            if fuse & 4: dis.append("HEVC")
            if fuse & 8: dis.append("H264")
            log(f"    vcn_inst[{i}] instance={inum} fuse=0x{fuse:08X} "
                f"disabled=[{','.join(dis) or 'NONE'}]")
    return True

def parse_psp_dir(blob, off, log, tag):
    log(f"  {tag}: dir @0x{off:X}: hexdump:")
    for r in range(4):
        row = blob[off + 16 * r: off + 16 * (r + 1)]
        log("    " + " ".join(f"{b:02x}" for b in row))
    # entry guess: u32 type, u32 size, u64 loc (16B) starting at 0x10
    for e in range(6):
        t, sz, loc = struct.unpack_from("<IIQ", blob, off + 16 + 16 * e)
        log(f"    entry[{e}] type=0x{t:X} size=0x{sz:X} loc=0x{loc:X}")

def scan_fw_headers(blob, log, base_note=""):
    """AMD fw-header sig: at some offset X: u32 total; u32 hdr2; u32==1; u32 type;
    u32 ver; u32==total-0x100; u32==0x100."""
    hits = 0
    for x in range(0, len(blob) - 0x120, 4):
        total, hdr2, one, typ, ver, t2, s2 = struct.unpack_from("<IIIIIII", blob, x)
        if one == 1 and total > 0x200 and t2 == total - 0x100 and s2 == 0x100:
            names = {0x0001000A: "CP", 5: "SDMA", 3: "VCN3", 0x00020002: "RLC/VCN2",
                     0xB: "PSP", 0x00020003: "VCN?", 9: "DMCU"}
            log(f"    fw-header @0x{x:X}: type=0x{typ:08X} ({names.get(typ, '?')}) "
                f"ver=0x{ver:08X} total=0x{total:X} hdr2=0x{hdr2:X}{base_note}")
            hits += 1
            if hits > 60:
                log("    ... (more truncated)")
                return
    return

def main():
    out = []
    def log(s=""):
        out.append(s)
        print(s)
    for path in IMAGES:
        if not os.path.exists(path):
            log(f"== MISSING: {path}")
            continue
        blob = read_all(path)
        log("=" * 100)
        log(f"IMAGE: {os.path.basename(path)}  ({len(blob):,} bytes)")
        psp = find_all(blob, b"$PSP")
        bios = find_all(blob, b"$BIOS")
        vrm = find_all(blob, b"$VRM")
        disc = find_all(blob, DISCOVERY_SIG)
        atom = find_all(blob, b"ATOMBIOS")
        slb2 = find_all(blob, b"SLB2")
        rb = find_all(blob, b"AMDRBN")
        log(f"  $PSP@{[hex(x) for x in psp]}  $BIOS@{[hex(x) for x in bios]}  "
            f"$VRM@{[hex(x) for x in vrm]}")
        log(f"  discovery@{[hex(x) for x in disc]}  ATOMBIOS@{[hex(x) for x in atom]}  "
            f"SLB2@{[hex(x) for x in slb2]}  AMDRBN@{[hex(x) for x in rb]}")
        for o in psp[:2]:
            parse_psp_dir(blob, o, log, "$PSP")
        for o in bios[:2]:
            parse_psp_dir(blob, o, log, "$BIOS")
        for o in disc[:3]:
            try:
                parse_discovery(blob, o, log, f"disc@0x{o:X}")
            except Exception as e:
                log(f"    parse error: {e}")
        # 55AA check at 0 and at last-64K
        if blob[0:2] == b"\x55\xaa":
            log("  55AA at 0")
        tail = blob[-65536:]
        j = tail.find(b"\x55\xaa")
        if j >= 0 and j < 4096:
            log(f"  55AA near tail: 0x{len(blob)-65536+j:X}")
        scan_fw_headers(blob, log)
    with open(os.path.join(FIRM, "rom_scan.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    main()
