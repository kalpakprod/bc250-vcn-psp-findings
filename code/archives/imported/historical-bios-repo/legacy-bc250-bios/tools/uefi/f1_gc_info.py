#!/usr/bin/env python3
"""F1: dump GC_INFO and HARVEST tables from AMD IP-discovery blobs in images.

Finds every 0x28211407 binary_header, parses the GC info table (v1/v2,
SA/WGP/CU counts) and the harvest table, prints raw hex.
Also dumps the same from the Cezanne donor BIOS for comparison.
"""
import struct, sys, os

IMAGES = [
    ("STOCK_BC250_3.00",
     r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM"),
    ("DONOR_CEZANNE",
     r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin"),
]
DISCOVERY_SIG = b"\x07\x14\x21\x28"

def gc_info_v1(b):
    # struct gc_info_v1 (amdgpu_discovery.c)
    (header_size, gc_num_se, gc_num_wgp0_per_sa, gc_num_wgp1_per_sa,
     gc_num_rb_per_se, gc_num_gl2c, gc_num_gprs, gc_num_max_gs_thds,
     lds_size_per_wgp, gc_num_spi_per_sa, gc_num_cu_per_sh) = \
        struct.unpack_from("<IIIIIIIIIII", b, 8)
    return ("v1 header_size=%#x num_se=%d wgp0_per_sa=%d wgp1_per_sa=%d "
            "rb_per_se=%d gl2c=%d gprs=%d max_gs_thds=%d lds/wgp=%d "
            "spi_per_sa=%d cu_per_sh=%d"
            % (header_size, gc_num_se, gc_num_wgp0_per_sa, gc_num_wgp1_per_sa,
               gc_num_rb_per_se, gc_num_gl2c, gc_num_gprs, gc_num_max_gs_thds,
               lds_size_per_wgp, gc_num_spi_per_sa, gc_num_cu_per_sh))

def gc_info_v2(b):
    (header_size, harvest_bitmap, gc_num_se, gc_num_cu_per_sh,
     gc_num_sh_per_se, gc_num_rb_per_se, gc_num_gl2c, wave_size,
     lds_size_per_wgp, gprs, max_gs_thds, spi_per_sa,
     num_sc_per_sh, num_packer_per_sc) = struct.unpack_from("<IIIIIIIIIIIIII", b, 8)
    return ("v2 header_size=%#x harvest_bitmap=%#x num_se=%d cu_per_sh=%d "
            "sh_per_se=%d rb_per_se=%d gl2c=%d wave_size=%d lds/wgp=%d gprs=%d "
            "max_gs_thds=%d spi_per_sa=%d sc_per_sh=%d packer/sc=%d"
            % (header_size, harvest_bitmap, gc_num_se, gc_num_cu_per_sh,
               gc_num_sh_per_se, gc_num_rb_per_se, gc_num_gl2c, wave_size,
               lds_size_per_wgp, gprs, max_gs_thds, spi_per_sa,
               num_sc_per_sh, num_packer_per_sc))

def dump(rom, off, log):
    vmaj, vmin = struct.unpack_from("<HH", rom, off + 4)
    if vmaj >= 2:
        ntab, _pad = struct.unpack_from("<HH", rom, off + 10)
        tbl_base = 16
    else:
        ntab, tbl_base = 6, 12
    log("  discovery @0x%X ver %d.%d ntables=%d" % (off, vmaj, vmin, ntab))
    tbls = {}
    for t in range(ntab):
        to, tc, ts, tp = struct.unpack_from("<HHHH", rom, off + tbl_base + 8 * t)
        tbls[t] = (to, ts)
    names = {0: "IP_DISCOVERY", 1: "GC", 2: "HARVEST_INFO", 3: "VCN_INFO",
             4: "MALL_INFO", 5: "NPS_INFO"}
    go = tbls.get(1, (0, 0))
    if go[0]:
        p = off + go[0]
        gid = rom[p:p + 4]
        ver = struct.unpack_from("<I", rom, p + 4)[0]
        log("  %s table @0x%X id=%r ver=%#x size=%#x" %
            (names[1], p, gid, ver, go[1]))
        for r in range(0, min(go[1], 0x60), 16):
            log("    %06X: %s" % (p + r, rom[p + r:p + r + 16].hex(" ")))
        try:
            if ver == 2:
                log("    " + gc_info_v2(rom[p:]))
            else:
                log("    " + gc_info_v1(rom[p:]))
        except Exception as e:
            log("    parse err: %s" % e)
    ho = tbls.get(2, (0, 0))
    if ho[0]:
        p = off + ho[0]
        log("  HARVEST table @0x%X sig=%r ver=%d size=%#x" %
            (p, rom[p:p + 4], struct.unpack_from("<I", rom, p + 4)[0], ho[1]))
        n = struct.unpack_from("<I", rom, p + 8)[0] if ho[1] >= 12 else 0
        log("    num entries = %d" % n)
        for i in range(min(n, 32)):
            hwid, inst, res = struct.unpack_from("<HBB", rom, p + 12 + 4 * i)
            if hwid == 0 and inst == 0 and res == 0:
                break
            log("    harvest[%d] hw_id=%d inst=%d reserved=%d" %
                (i, hwid, inst, res))

def main():
    out = []
    log = out.append
    for name, path in IMAGES:
        if len(sys.argv) > 1 and sys.argv[1] not in name:
            continue
        log("=" * 72)
        log("=== %s" % name)
        rom = open(path, "rb").read()
        i, hits = 0, 0
        while hits < 10:
            j = rom.find(DISCOVERY_SIG, i)
            if j < 0:
                break
            i = j + 1
            # require plausible header
            vmaj, vmin, csum, bsize = struct.unpack_from("<HHHH", rom, j + 4)
            if 0 < bsize < 0x4000:
                try:
                    dump(rom, j, log)
                    hits += 1
                except Exception as e:
                    log("  @0x%X parse error: %s" % (j, e))
        if not hits:
            log("  no IP-discovery blob found")
    txt = "\n".join(out)
    print(txt)
    with open(r"C:\Users\OWNER\bc250-bios\evidence\f1_gc_info.txt", "w",
              encoding="utf-8") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
