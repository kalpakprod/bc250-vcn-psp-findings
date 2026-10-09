# B1c: final dispatcher command map. fn@0xBA98 = mailbox dispatcher (cmd = [r4]).
# Switch head at 0xBB04 (movw r2,#0x106e; ldr.w sl,[pc,#0x21c] => lit@0xBD28).
# Concrete-emulate the decode chain for cmd 0..0x10000 plus special values
# (0xFFFF0000.., 0xF1000, gasket 0x210 command words and masks). Terminate at
# first non-decode instruction => action address; extract first bl/svc.
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True
INS = {}
FRESH = {}


def ins_at(a):
    """fresh decode at exact address; linear stream cache is unreliable (pools)"""
    if a in FRESH:
        return FRESH[a]
    for i in md.disasm(body[a:a + 8], a):
        FRESH[a] = (i.mnemonic, i.op_str, i.size)
        return FRESH[a]
    FRESH[a] = (".byte", "", 2)
    return FRESH[a]

LIT = lambda a: struct.unpack_from("<I", body, a)[0]

ALIAS = {"sl": "r10", "fp": "r11", "ip": "r12", "sb": "r9", "sp": "r13",
         "lr": "r14", "pc": "r15"}


COND = {"eq": lambda f: f["Z"], "ne": lambda f: not f["Z"],
        "hs": lambda f: f["C"], "lo": lambda f: not f["C"],
        "hi": lambda f: f["C"] and not f["Z"], "ls": lambda f: (not f["C"]) or f["Z"],
        "ge": lambda f: f["N"] == f["V"], "lt": lambda f: f["N"] != f["V"],
        "gt": lambda f: (not f["Z"]) and (f["N"] == f["V"]),
        "le": lambda f: f["Z"] or (f["N"] != f["V"]),
        "mi": lambda f: f["N"], "pl": lambda f: not f["N"],
        "vs": lambda f: f["V"], "vc": lambda f: not f["V"]}
S32 = lambda v: v - 0x100000000 if v & 0x80000000 else v
M = 0xFFFFFFFF


def sub_flags(a, b):
    r = (a - b) & M
    return r, {"N": bool(r >> 31), "Z": r == 0, "C": a >= b,
               "V": (S32(a) < 0) != (S32(b) < 0) and (S32(a) < 0) != (S32(r) < 0)}


def add_flags(a, b):
    r = (a + b) & M
    return r, {"N": bool(r >> 31), "Z": r == 0, "C": a + b > M,
               "V": (S32(a) < 0) == (S32(b) < 0) and (S32(a) < 0) != (S32(r) < 0)}


def emulate(cmd, start=0xBB04, limit=400):
    regs = {"r%d" % i: 0 for i in range(16)}
    regs["r0"] = cmd & M
    f = {"N": False, "Z": False, "C": False, "V": False}
    pc = start
    for _ in range(limit):
        m, o, sz = ins_at(pc)
        ops = [x.strip() for x in o.split(",")] if o else []
        nxt = pc + sz

        def val(tok):
            tok = tok.strip().rstrip("!")
            if tok.startswith("#"):
                return int(tok[1:], 0) & M
            if tok in ("sp", "pc", "lr"):
                return 0
            r = ALIAS.get(tok, tok)
            if r in regs:
                return regs[r]
            raise ValueError("op? " + tok)

        try:
            if m == "movw":
                regs[ALIAS.get(ops[0], ops[0])] = val(ops[1]); pc = nxt
            elif m in ("mov", "mov.w", "movs", "movs.w"):
                regs[ALIAS.get(ops[0], ops[0])] = val(ops[1]); pc = nxt
            elif m in ("ldr", "ldr.w") and len(ops) >= 2 and "pc" in ",".join(ops[1:]):
                imm = int(",".join(ops[1:]).split("#")[-1].rstrip("]"), 0)
                regs[ALIAS.get(ops[0], ops[0])] = LIT(((pc + 4) & ~3) + imm)
                pc = nxt
            elif m in ("cmp", "cmp.w"):
                _, f = sub_flags(regs[ALIAS.get(ops[0], ops[0])], val(ops[1])); pc = nxt
            elif m in ("cmn", "cmn.w"):
                _, f = add_flags(regs[ALIAS.get(ops[0], ops[0])], val(ops[1])); pc = nxt
            elif m in ("subs", "subs.w"):
                rd = ALIAS.get(ops[0], ops[0])
                if len(ops) == 3:
                    r, f = sub_flags(val(ops[1]), val(ops[2]))
                else:
                    r, f = sub_flags(regs[rd], val(ops[1]))
                regs[rd] = r; pc = nxt
            elif m in ("sub", "sub.w", "subw") and len(ops) == 3:
                regs[ALIAS.get(ops[0], ops[0])] = (val(ops[1]) - val(ops[2])) & M
                pc = nxt
            elif m == "adds" or m == "adds.w":
                rd = ALIAS.get(ops[0], ops[0])
                if len(ops) == 3:
                    r, f = add_flags(val(ops[1]), val(ops[2]))
                else:
                    r, f = add_flags(regs[rd], val(ops[1]))
                regs[rd] = r; pc = nxt
            elif m in ("add", "add.w", "addw") and len(ops) == 3:
                regs[ALIAS.get(ops[0], ops[0])] = (val(ops[1]) + val(ops[2])) & M
                pc = nxt
            elif m == "mvn" or m == "mvn.w":
                regs[ALIAS.get(ops[0], ops[0])] = (~val(ops[-1])) & M
                if m == "mvn.w":
                    _, f = sub_flags(0, val(ops[-1]))
                pc = nxt
            elif m == "tbb":
                base = (pc + 4) & ~3
                rn = ops[1].split(",")[-1].strip(" ]") if len(ops) > 1 else ops[0].split(",")[-1].strip(" ]")
                rn = ALIAS.get(rn, rn)
                pc = base + 2 * body[base + regs[rn]]
            elif m == "tbh":
                base = (pc + 4) & ~3
                rn = ops[1].split(",")[-1].strip(" ]")
                rn = ALIAS.get(rn, rn)
                half = struct.unpack_from("<H", body, base + 2 * regs[rn])[0]
                pc = base + 2 * half
            elif m in ("b", "b.w"):
                pc = int(o.split("#")[-1], 0)
            elif m in COND:
                pc = (int(o.split("#")[-1], 0) if COND[m](f) else nxt)
            elif m.startswith("b") and m[1:] in COND:
                pc = (int(o.split("#")[-1], 0) if COND[m[1:]](f) else nxt)
            else:
                return ("ACTION", pc, "%s %s" % (m, o))
        except Exception as e:
            return ("ACTION", pc, "%s %s (!%s)" % (m, o, e))
    return ("LIMIT", pc, "")


def arm_action(addr):
    pc = addr
    for _ in range(12):
        m, o, sz = ins_at(pc)
        if m == ".byte":
            return "?"
        if m in ("bl", "blx") and "#" in o:
            return "bl " + o.split("#")[-1]
        if m == "svc":
            return "svc " + o
        if m == "pop" or (m in ("b", "b.w") and int(o.split("#")[-1], 0) in (0xC394, 0xC7AA)):
            return "b %#x (tail)" % int(o.split("#")[-1], 0)
        pc += sz
    return "?"


out = []
P = out.append
P("== dispatcher fn@0xBA98: cmd([r4]) -> action; emulate from 0xBB04 ==")
P("   sl literal @0xBD28 = %#x (then sl-5); donor literal @0xBD2C = %#x"
  % (LIT(0xBD28), LIT(0xBD2C)))

words = [0x2232C240, 0x2233C241, 0x2262C24E, 0x226EC250, 0x2278C261, 0x244FC441,
         0x244EC442, 0x244DC443, 0x226CC24F, 0x2440C440, 0x2544C382, 0xF853C480]
extra = list(range(0xFFFF0000, 0xFFFF0010)) + [0xF1000, 0x185103, 0x1F820]
for w in words:
    extra += [w, w & 0xFFFF, w >> 16, w & 0xFFF, w & 0x1FFF, (w >> 16) & 0xFFF,
              (w & 0xFFFF) | 0x1000, (w & 0xFFFF) | 0x2000, (w & 0xFFF) | 0x3000]

results = {}
for cmd in sorted(set(list(range(0, 0x10000)) + extra)):
    results[cmd] = emulate(cmd)

runs = []
prev = None
for cmd in sorted(results):
    k = results[cmd][:2]
    if k != prev:
        runs.append([cmd, cmd, results[cmd]])
        prev = k
    else:
        runs[-1][1] = cmd
P("")
P("== cmd ranges -> action address ==")
for lo, hi, r in runs:
    rng = "%#x" % lo if lo == hi else "%#x..%#x" % (lo, hi)
    P("  cmd %-18s -> %#08x  %-40s ; action: %s" %
      (rng, r[1], r[2][:40], arm_action(r[1]) if r[0] == "ACTION" else r[2]))

P("")
P("== special word-derived cmds ==")
for w in words:
    for cand, desc in ((w, "raw"), (w & 0xFFFF, "&0xFFFF"), (w >> 16, ">>16"),
                       (w & 0xFFF, "&0xFFF"), ((w >> 16) & 0xFFF, "hi12")):
        r = results.get(cand)
        if r and r[0] == "ACTION" and r[1] not in (0xC7A8, 0xC7AA):
            P("  %#010x (%s) -> %#08x %s" % (cand, desc, r[1], arm_action(r[1])))

open(r"C:\Users\OWNER\bc250-bios\evidence\b1_emul2.txt", "w").write("\n".join(out))
print("written b1_emul2.txt, %d lines, %d ranges" % (len(out), len(runs)))
