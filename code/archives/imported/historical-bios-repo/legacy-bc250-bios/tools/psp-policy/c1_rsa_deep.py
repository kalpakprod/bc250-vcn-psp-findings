# C1: data-driven $KDB scan (locate kid bytes, read modulus at kid+0x40), then
# decrypt the gasket/policy signature and inspect the plaintext structure.
import struct
import hashlib

ROM = open(r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
           r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
D = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM"
KID = bytes.fromhex("96ea7cfec59d4c2a991e2c1f10d33bd8")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


kdb_blobs = []
for tag, buf in [("own t50", ROM[0x9dad00:0x9dad00 + 0xDD0]),
                 ("own t51", ROM[0x9dbb00:0x9dbb00 + 0x740])]:
    kdb_blobs.append((tag, buf))
for tag, fn in [("chipset t50", "17_t50_0x9DAD00_DD0.bin"),
                ("chipset t51", "18_t51_0x9DBB00_740.bin")]:
    try:
        kdb_blobs.append((tag, open(D + "\\" + fn, "rb").read()))
    except OSError:
        pass

mods = []
for tag, buf in kdb_blobs:
    print("== %s (len %#x) $KDB=%r ==" % (tag, len(buf), buf[0x108:0x10C]))
    start = 0
    while True:
        o = buf.find(KID, start)
        if o < 0:
            break
        mod = buf[o + 0x10:o + 0x110]
        # look for exponent nearby: typical 65537
        exp = u32(buf, o - 4) if o >= 4 else 0
        print("  kid @%#x, exp_guess(u32@kid-4)=%#x, mod[0:16]=%s" % (o, exp, mod[:16].hex()))
        mods.append((tag, o, mod))
        start = o + 1

# verify blobs
targets = [("GASKET 0x24", 0x982000, 0x2E50), ("POLICY 0x45", 0x9CA400, 0x6E0)]
for name, addr, size in targets:
    blob = ROM[addr:addr + size]
    rom_size = u32(blob, 0x6C)
    sigtype = u32(blob, 0x34)
    ssig = 0x100 if sigtype == 0 else 0x200
    sig = blob[rom_size - ssig:rom_size] if rom_size else blob[-ssig:]
    signed = blob[:rom_size - ssig] if rom_size else blob[:-ssig]
    print("\n== %s: rom_size@0x6C=%#x sigtype@0x34=%#x sig=%#x ==" % (name, rom_size, sigtype, ssig))
    print("  sig[0:16]=%s" % sig[:16].hex())
    spans = {
        "whole-minus-sig": signed,
        "body[0x100:]": blob[0x100:len(signed)],
        "env[0x10:]+body": blob[0x10:0x100] + blob[0x100:len(signed)],
    }
    for tag, o, mod in mods:
        for e in (65537, 3, 17):
            n = int.from_bytes(mod, "little")
            if n == 0:
                continue
            for s_e in ("little", "big"):
                m = pow(int.from_bytes(sig, s_e), e, n)
                dec_le = m.to_bytes(256, "little")
                dec_be = m.to_bytes(256, "big")
                for sname, msg in spans.items():
                    for halg, hfn in (("sha256", hashlib.sha256), ("sha384", hashlib.sha384),
                                      ("sha512", hashlib.sha512), ("sha1", hashlib.sha1)):
                        h = hfn(msg).digest()
                        for dec, dl in ((dec_le, "le"), (dec_be, "be")):
                            if h in dec or h[::-1] in dec:
                                print("  VERIFIED: %s kid@%#x e=%d sig=%s span=%s alg=%s dec=%s"
                                      % (tag, o, e, s_e, sname, halg, dl))
            # structure dump of first candidate
            print("  decrypt diag (%s kid@%#x e=65537 sig=le): %s" % (tag, o, dec_le[:48].hex()))
            print("  decrypt diag (%s kid@%#x e=65537 sig=be): %s" % (tag, o, dec_be[:48].hex()))
