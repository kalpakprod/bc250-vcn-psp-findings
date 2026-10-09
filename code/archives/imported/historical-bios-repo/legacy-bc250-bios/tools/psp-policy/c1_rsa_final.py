# C1: final RSA attempt: use the $KDB record modulus parsed with the 0x150-stride
# layout (record whose kid == envelope kid), decrypt sig, inspect plaintext, and
# brute spans/hashes/endians for a match.
import struct
import hashlib

ROM = open(r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
           r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
D = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM"
DI = {"sha256": bytes.fromhex("3031300d060960864801650304020105000420"),
      "sha384": bytes.fromhex("3041300d060960864801650304020205000430"),
      "sha512": bytes.fromhex("3051300d060960864801650304020305000440"),
      "sha1": bytes.fromhex("3021300906052b0e03021a05000414")}


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def parse_kdb(buf, tag):
    body = buf[0x100:]
    keys, off = [], 0x50
    while off + 0x150 <= len(body):
        rec = body[off:off + 0x150]
        size, idx = struct.unpack_from("<II", rec, 0)
        exp = struct.unpack_from("<I", rec, 0x0C)[0]
        kid = rec[0x10:0x20]
        bits = struct.unpack_from("<I", rec, 0x20)[0]
        if size not in (0, 0x150) or bits not in (2048, 1024) or exp not in (3, 5, 17, 0x10001):
            break
        keys.append(dict(tag=tag, off=off, idx=idx, exp=exp, kid=kid.hex(),
                         bits=bits, mod=rec[0x50:0x50 + (bits // 8)]))
        off += 0x150
    return keys


keys = []
for tag, buf in [("own t50", ROM[0x9dad00:0x9dad00 + 0xDD0]),
                 ("own t51", ROM[0x9dbb00:0x9dbb00 + 0x740]),
                 ("chipset t50", open(D + r"\17_t50_0x9DAD00_DD0.bin", "rb").read()),
                 ("chipset t51", open(D + r"\18_t51_0x9DBB00_740.bin", "rb").read())]:
    ks = parse_kdb(buf, tag)
    print("%s: %d keys" % (tag, len(ks)))
    for k in ks:
        print("  idx=%d exp=%#x bits=%d kid=%s" % (k["idx"], k["exp"], k["bits"], k["kid"]))
    keys += ks

for name, addr, size in [("GASKET 0x24", 0x982000, 0x2E50), ("POLICY 0x45", 0x9CA400, 0x6E0)]:
    blob = ROM[addr:addr + size]
    kid = blob[0x38:0x48].hex()
    rom_size = u32(blob, 0x6C) or size
    sig = blob[rom_size - 0x100:rom_size]
    print("\n== %s kid=%s rom=%#x ==" % (name, kid, rom_size))
    cands = [k for k in keys if k["kid"] == kid]
    print("  matching keys: %s" % [(k["tag"], k["idx"]) for k in cands] or "none")
    spans = {
        "env+body": blob[:rom_size - 0x100],
        "body": blob[0x100:rom_size - 0x100],
        "env[0x10:]+body": blob[0x10:rom_size - 0x100],
        "env[0x30:]+body": blob[0x30:rom_size - 0x100],
        "env[0x38:]+body": blob[0x38:rom_size - 0x100],
    }
    # sweep: modulus taken at various record offsets and endiannesses
    mods = []
    for k in cands:
        rec = None
        for tag, buf in [("own t50", ROM[0x9dad00:0x9dad00 + 0xDD0]),
                         ("chipset t50", open(D + r"\17_t50_0x9DAD00_DD0.bin", "rb").read())]:
            if tag == k["tag"]:
                rec = buf[0x100 + k["off"]:0x100 + k["off"] + 0x150]
        if rec is None:
            continue
        for moff in (0x24, 0x28, 0x2C, 0x30, 0x34, 0x38, 0x3C, 0x40, 0x44, 0x48,
                     0x4C, 0x50, 0x54, 0x58):
            for m_e in ("little", "big"):
                mods.append(("%s mod@+%#x %s" % (k["tag"], moff, m_e),
                            rec[moff:moff + 0x100], k["exp"]))
    print("  modulus sweep: %d candidates" % len(mods))
    for mtag, mod, e in mods:
        n = int.from_bytes(mod, "little") if mtag.endswith("little") else \
            int.from_bytes(mod, "big")
        if n.bit_length() < 2047 or n.bit_length() > 2048:
            continue
        for s_e in ("little", "big"):
            m = pow(int.from_bytes(sig, s_e), e, n)
            for out_e in ("little", "big"):
                dec = m.to_bytes(256, out_e)
                if dec[:1] == b"\x00" and dec[1:2] == b"\x01":
                    print("  PKCS1-LIKE: %s sig=%s out=%s" % (mtag, s_e, out_e))
                for sname, msg in spans.items():
                    for halg, hfn in (("sha256", hashlib.sha256),
                                      ("sha384", hashlib.sha384),
                                      ("sha512", hashlib.sha512),
                                      ("sha1", hashlib.sha1)):
                        h = hfn(msg).digest()
                        if (DI[halg] + h) in dec or h in dec or h[::-1] in dec:
                            print("    VERIFIED %s span=%s alg=%s sig=%s out=%s"
                                  % (mtag, sname, halg, s_e, out_e))
