# A3: VCN bank register map (56 pairs) + commit protocol + reachability matrix.
import struct

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
U = open(r"C:\Users\OWNER\tmp_bc250\recon\bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin", "rb").read()

KNOWN = {
    0x0900C234: "bank commit/enable (0=program, 1=commit)",
    0x0900C910: "requester policy mask A (stock 0x497fff)",
    0x0900C914: "requester policy mask B",
    0x0900C930: "requester policy mask C",
    0x0900CB80: "bank lock (stock 0xff)",
}


def groups(body):
    out, off = [], 0x40
    while off + 8 <= len(body):
        t, c = struct.unpack_from("<II", body, off)
        if t == 0 or t > 0xFFFF or c > 0x100000:
            break
        out.append((t, [(struct.unpack_from("<II", body, off + 8 + 8 * i)) for i in range(c)]))
        off += 8 + c * 8
    return out


print("== VCN bank pairs in our build (UNSIGNED body) ==")
allp = []
for t, pairs in groups(U):
    v = [(a, val, t) for a, val in pairs if 0x0900C000 <= a <= 0x0900CFFF]
    allp += v
print("total VCN-bank pairs:", len(allp))
for a, val, t in allp:
    tag = KNOWN.get(a, "")
    print("  grp %#05x: {%#010x, %#010x} %s" % (t, a, val, tag))

# bucket by address pattern
print("\n== address buckets ==")
buck = {}
for a, val, t in allp:
    buck.setdefault(a & 0xFFFFFFF0, []).append((a, val))
for b in sorted(buck):
    print("  %#010x: %d regs: %s" % (b, len(buck[b]), [(hex(a), hex(v)) for a, v in buck[b]]))

# what the stock ROM applies to the same bank (Robin gasket 0.201 first pairs = commit regs of OTHER banks)
rg = groups(ROM[0x982000 + 0x100:0x982000 + 0x100 + 0x2C50])
print("\n== stock gasket 0x201: which banks get programmed (unique 0x...234 addrs) ==")
banks = sorted(set(a for t, ps in rg if t == 0x201 for a, v in ps if (a & 0xFFF) == 0x234))
print("  commit regs touched:", [hex(x) for x in banks])
vcn234 = [x for x in banks if 0x0900C000 <= x <= 0x0900CFFF]
print("  VCN bank (0x0900C234) present in stock:", bool(vcn234))

print("\n== DF aperture + SEG regs (step A) reachability notes ==")
for t, ps in groups(U):
    for a, v in ps:
        if a in (0x03E810, 0x03A2011C, 0x03A20124, 0x03A20120):
            print("  grp %#05x: {%#010x, %#010x}" % (t, a, v))

print("""
== REACHABILITY MATRIX (conclusions) ==
Register space: SMN (system managment network) 0x0900Cxxx / 0x03A201xx / 0x03E8xx.
- x86 DXE/UEFI: NO direct SMN write bridge (AmdFabricAriDxe 0xE0000000 window covers DF
  fabric registers only, not the PSP firewall SMN banks). => DXE-драйвер НЕ может писать банк.
- SMU: YES - privileged SMN write msg Q3 0x98 (smn_write32), field-proven on this board
  (VULN-1 PoC 2026-08-26: 56 writes accepted, readback OK).
- PSP/TOS: YES by design (gasket/TOS_SECURITY_POLICY apply engine, SMN bridge 0x0320xxxx).
=> Flash-путь (D3): не требует никаких записей — PSP сам применяет таблицу при загрузке.
=> Runtime-путь (путь A из VCN-ATTACK-PLAN): только через SMU (unlock Q2 0x23 -> Q3 0x98).
""")
