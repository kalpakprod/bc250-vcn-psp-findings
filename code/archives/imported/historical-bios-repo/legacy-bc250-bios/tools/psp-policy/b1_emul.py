# B1b: concrete emulator of the mailbox-dispatcher decode chain (0xBC3C .. arms).
# Sweep r1 = command over 0..0xFFFF, emulate the compare/binary-search + tbb tables,
# resolve every command to its arm (first dispatcher arm reached in 0xBE00..0xC7AA
# or a thunk "b #arm" in 0xBD24..0xBDFF). Also dump entry head 0xB9F4..0xBC3C raw
# so preprocessing of the command word is visible.
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = {}
for i in md.disasm(body, 0):
    INS[i.address] = (i.mnemonic, i.op_str)


def ins_at(a):
    """decode on demand from arbitrary address (linear stream may not cover it)"""
    if a in INS:
        return INS[a]
    for i in md.disasm(body[a:a + 8], a):
        INS[a] = (i.mnemonic, i.op_str)
        return INS[a]
    INS[a] = (".byte", "")
    return INS[a]

out = []
P = out.append
P("== raw u16 0xB9F4..0xBC5C (entry head) ==")
for a in range(0xB9F4, 0xBC5C, 4):
    w1, w2 = struct.unpack_from("<HH", body, a)
    P("  %#08x: %04x %04x   ;; %s %s | %s %s" % (
        a, w1, w2,
        INS.get(a, ("?", "?"))[0], INS.get(a, ("?", "?"))[1],
        INS.get(a + 2, ("?", "?"))[0], INS.get(a + 2, ("?", "?"))[1]))

COND = {"eq": lambda f: f["Z"], "ne": lambda f: not f["Z"],
        "hs": lambda f: f["C"], "lo": lambda f: not f["C"],
        "hi": lambda f: f["C"] and not f["Z"], "ls": lambda f: (not f["C"]) or f["Z"],
        "ge": lambda f: f["N"] == f["V"], "lt": lambda f: f["N"] != f["V"],
        "gt": lambda f: (not f["Z"]) and (f["N"] == f["V"]),
        "le": lambda f: f["Z"] or (f["N"] != f["V"]),
        "mi": lambda f: f["N"], "pl": lambda f: not f["N"],
        "vs": lambda f: f["V"], "vc": lambda f: not f["V"]}
S32 = lambda v: v - 0x100000000 if v & 0x80000000 else v


def sub_flags(a, b):
    r = (a - b) & 0xFFFFFFFF
    return r, {"N": bool(r >> 31), "Z": r == 0,
              "C": a >= b, "V": (S32(a) < 0) != (S32(b) < 0) and (S32(a) < 0) != (S32(r) < 0)}


def add_flags(a, b):
    r = (a + b) & 0xFFFFFFFF
    return r, {"N": bool(r >> 31), "Z": r == 0,
              "C": r < a, "V": (S32(a) < 0) == (S32(b) < 0) and (S32(a) < 0) != (S32(r) < 0)}


def val(tok, regs):
    tok = tok.strip()
    if tok.startswith("#"):
        return int(tok[1:].rstrip("!"), 0) & 0xFFFFFFFF
    if tok in regs:
        return regs[tok]
    raise ValueError("reg? " + tok)


def emulate(cmd, start=0xBC3C, limit=300):
    regs = {"r%d" % i: 0 for i in range(13)}
    regs["ip"] = regs["r12"]
    regs["r1"] = cmd & 0xFFFFFFFF
    f = {"N": False, "Z": False, "C": False, "V": False}
    pc = start
    for _ in range(limit):
        m, o = ins_at(pc)
        if m == ".byte":
            return ("NOCODE", pc)
        ops = [x.strip() for x in o.split(",")] if o else []
        nxt = pc + (4 if m.endswith(".w") and pc in INS else 2)
        if m == "movw":
            regs[ops[0]] = val(ops[1], regs); pc = nxt
        elif m in ("mov", "mov.w", "movs", "lsls"):
            if m == "lsls":
                r, fl = sub_flags(0, 0)  # placeholder, not expected in chain
                pc = nxt
            else:
                if ops[1].startswith("#"):
                    regs[ops[0]] = val(ops[1], regs)
                else:
                    regs[ops[0]] = regs[ops[1]]
                pc = nxt
        elif m in ("cmp", "cmp.w"):
            _, f = sub_flags(regs[ops[0]], val(ops[1], regs)); pc = nxt
        elif m in ("subs", "sub.w", "subw"):
            r, f = sub_flags(val(ops[1], regs), val(ops[2], regs))
            if ops[0] != "sb":  # 'sb' = no-write sub variant (capstone op)
                regs[ops[0]] = r
            pc = nxt
        elif m in ("adds", "add.w", "addw"):
            r, f = add_flags(val(ops[1], regs), val(ops[2], regs))
            regs[ops[0]] = r; pc = nxt
        elif m == "tbb":
            base = (pc + 4) & ~3
            idx = regs[ops[1].split(",")[-1].strip(" ]")]
            pc = base + 2 * body[base + idx]
        elif m == "tbh":
            base = (pc + 4) & ~3
            rn = ops[1].split(",")[-1].strip(" ]")
            idx = regs[rn] >> 1 if "lsl" in ops[1] else regs[rn]
            pc = base + 2 * struct.unpack_from("<H", body, base + 2 * (regs[rn] // 2 if False else idx))[0] \
                if False else base + 2 * (idx // 2 * 0 + idx)  # placeholder; see below
            # tbh [pc, rx, lsl #1]: entry = halfword at base + 2*rx
            half = struct.unpack_from("<H", body, base + 2 * regs[rn])[0]
            pc = base + 2 * half
        elif m == "b" or m == "b.w":
            t = int(o.split("#")[-1], 0)
            # thunk?
            if 0xBD24 <= t < 0xBE00 and ins_at(t)[0] == "b":
                t2 = int(INS[t][1].split("#")[-1], 0)
                return ("ARM", t2) if 0xBE00 <= t2 <= 0xC7AA else ("THUNK2", t2)
            if 0xBE00 <= t <= 0xC7AA:
                return ("ARM", t)
            pc = t
        elif m in COND or (m.startswith("b") and m[1:] in COND):
            t = int(o.split("#")[-1], 0)
            if COND[m[1:] if m.startswith("b") else m](f):
                pc = t
            else:
                pc = nxt
        elif m == "svc":
            return ("SVC", o)
        else:
            return ("STOP %s %s" % (m, o), pc)
    return ("LIMIT", pc)


res = {}
stops = {}
for cmd in range(0x10000):
    r = emulate(cmd)
    if r[0] == "ARM":
        res[cmd] = r[1]
    else:
        stops.setdefault(r[0], []).append((cmd, r[1] if len(r) > 1 else 0))

P("")
P("== command -> arm (concrete sweep 0..0xFFFF, entry 0xBC3C) ==")
cur = None
for cmd in sorted(res):
    if res[cmd] != cur:
        P("  cmd %#06x -> arm %#06x" % (cmd, res[cmd]))
        cur = res[cmd]
# also full map compact
P("")
P("== full map (cmd: arm) ==")
P("  " + " ".join("%#x:%#x" % (c, res[c]) for c in sorted(res)))

P("")
P("== non-resolved outcomes ==")
for k, v in sorted(stops.items()):
    P("  %-24s x%d  first cmd %#x -> %#x" % (k, len(v), v[0][0], v[0][1]))

open(r"C:\Users\OWNER\bc250-bios\evidence\b1_emul.txt", "w").write("\n".join(out))
print("written b1_emul.txt, %d lines; arms=%d stops=%s" %
      (len(out), len(res), {k: len(v) for k, v in stops.items()}))
