# A2d: (a) svc-0xF2 wrapper service table + callers of the RSA-verify service (#6) + error branches
#      (b) donor 0x45 VCN tail pairs + robin 0x45 vs gasket 0x280 pair comparison (surgical spec for D3-B v2)
import struct, re
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
TOS = ROM[0x8EAC00 + 0x100:0x8EAC00 + 0x100 + 0x14150]

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(TOS, 0) if i.mnemonic != ".byte"]
IDX = {a: k for k, (a, m, o) in enumerate(INS)}


def dump(lo, hi):
    out = []
    for a, m, o in INS:
        if lo <= a < hi:
            out.append("%#08x  %-8s %s" % (a, m, o))
    return "\n".join(out)


# --- service table: find wrappers 'movs r0,#N ... svc #0xf2' ---
print("== svc 0xF2 wrappers: service numbers ==")
wraps = {}
for k, (a, m, o) in enumerate(INS):
    if m == "svc" and o.strip() in ("#0xf2", "0xf2"):
        # look back up to 6 ins for movs r0,#N
        n = None
        for j in range(k - 1, max(0, k - 7), -1):
            am, mm, om = INS[j]
            if mm in ("movs", "mov", "mov.w") and om.lower().startswith("r0,"):
                try:
                    n = int(om.split("#")[1], 0)
                except Exception:
                    n = None
                break
            if mm in ("push", "push.w", "pop", "pop.w"):
                break
        if n is not None:
            wraps.setdefault(n, []).append(a)
for n in sorted(wraps):
    print("  service #%d: %s" % (n, [hex(a) for a in wraps[n]]))

# --- fn boundaries (push with lr) ---
fstarts = sorted(a for a, m, o in INS if m in ("push", "push.w") and "lr" in o)


def fn_of(addr):
    prev = fstarts[0]
    for f in fstarts:
        if f <= addr:
            prev = f
        else:
            break
    return prev


# callers of verify service fn
if 6 in wraps:
    f6 = fn_of(wraps[6][0])
    print("\n== service#6 (RSA verify?) fn@%#x callers + error branches ==" % f6)
    for a, m, o in INS:
        if m == "bl":
            try:
                t = int(o.split("#")[1] if "#" in o else o, 0)
            except Exception:
                continue
            if fn_of(t) == f6 and fn_of(a) != f6:
                print("\n---- caller BL @%#x (fn@%#x) ----" % (a, fn_of(a)))
                print(dump(max(0, a - 0x40), a + 0x50))

# --- (b) donor 0x45 tails ---
def body_of(blob):
    size = struct.unpack_from("<I", blob, 0x14)[0]
    return blob[0x100:0x100 + size]


def groups(body):
    out, off = [], 0x40
    while off + 8 <= len(body):
        t, c = struct.unpack_from("<II", body, off)
        if t == 0 or t > 0xFFFF or c > 0x100000:
            break
        out.append((t, off, [(struct.unpack_from("<II", body, off + 8 + 8 * i)) for i in range(c)]))
        off += 8 + c * 8
    return out


G = r"C:\Users\OWNER\tmp_bc250\recon"
print("\n== donor 0x45: VCN-bank pairs + 0x210 groups ==")
for tag, rel in [("cz_d0/e13", r"keys_raw\cezanne_d0\d00_e13_TOS_SECURITY_POLICY_0x45.bin"),
                 ("cz_d0/e14", r"keys_raw\cezanne_d0\d00_e14_TOS_SECURITY_POLICY_0x45.bin")]:
    b = body_of(open(G + "\\" + rel, "rb").read())
    for t, off, pairs in groups(b):
        vcn = [(a, v) for a, v in pairs if 0x0900C000 <= a <= 0x0900CFFF]
        if t == 0x210 or vcn:
            print("  %s grp %#06x n=%d" % (tag, t, len(pairs)))
            if t == 0x210:
                for a, v in pairs:
                    print("      210: {%#010x, %#010x}" % (a, v))
            for a, v in vcn:
                print("      VCN: {%#010x, %#010x}" % (a, v))

print("\n== robin 0x45 grp 0x280 vs robin gasket grp 0x280: identical? ==")
r45 = groups(body_of(ROM[0x9CA400:0x9CA400 + 0x6E0]))
rg = groups(body_of(ROM[0x982000:0x982000 + 0x2E50]))
r45_280 = [p for t, o, ps in r45 if t == 0x280 for p in ps]
rg_280 = [p for t, o, ps in rg if t == 0x280 for p in ps]
print("  robin45 0x280 n=%d, gasket 0x280 n=%d, identical=%s" % (len(r45_280), len(rg_280), r45_280 == rg_280))
print("\n== gasket VCN tail (our UNSIGNED 0x280 5 pairs) for reference ==")
u = open(G + r"\bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin", "rb").read()
for t, off, pairs in groups(u):
    if t == 0x280:
        for a, v in pairs:
            if 0x0900C000 <= a <= 0x0900CFFF:
                print("      {%#010x, %#010x}" % (a, v))
