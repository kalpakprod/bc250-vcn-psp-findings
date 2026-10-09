# A2e: callers of the $PS1 load+verify fn@0x12544 + their handling of its return.
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
TOS = ROM[0x8EAC00 + 0x100:0x8EAC00 + 0x100 + 0x14150]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(TOS, 0) if i.mnemonic != ".byte"]


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


fstarts = sorted(a for a, m, o in INS if m in ("push", "push.w") and "lr" in o)


def fn_of(addr):
    prev = fstarts[0]
    for f in fstarts:
        if f <= addr:
            prev = f
        else:
            break
    return prev


TARGET = 0x12544
print("== callers of fn@%#x ==" % TARGET)
for a, m, o in INS:
    if m == "bl":
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t == TARGET:
            print("\n---- caller @%#x (in fn@%#x) ----" % (a, fn_of(a)))
            print(dump(a - 0x60, a + 0x60))

# also: what does the common error handler fn@0x13134 do?
print("\n== fn@0x13134 (common error path) ==")
print(dump(0x13134, 0x131C0))
# and svc#63 wrapper(s): svc 0x63 sites
print("\n== svc #0x63 sites with context ==")
sites = [a for a, m, o in INS if m == "svc" and o.strip() in ("#0x63", "0x63")]
for s in sites[:6]:
    print("---- @%#x ----" % s)
    print(dump(s - 0x10, s + 0x10))
