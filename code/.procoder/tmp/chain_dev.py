# Ghidra postScript for 2026-09-23 SMU chain development (Xtensa LE32)
# Outputs: handler bytes @0x2d620, refs into overflow window, callers of window helpers.
import struct

prog = currentProgram
af = prog.getAddressFactory().getDefaultAddressSpace()
fm = prog.getFunctionManager()
listing = prog.getListing()
refmgr = prog.getReferenceManager()

def A(x):
    return af.getAddress(x)

out = []

# 1. instruction bytes of handler 0x2d620 .. 0x2d760
out.append("=== DISASM 0x2d620 ===")
ia = listing.getInstructions(A(0x2d620), True)
n = 0
for i in ia:
    if n > 120:
        break
    out.append("%s  %s  %s" % (i.getAddress(), i.getBytes().hex(), i))
    n += 1

# 2. all references (from any instruction) into overflow window 0x188a0..0x1a5d0
out.append("=== REFS INTO WINDOW 0x188a0-0x1a5d0 ===")
low, high = A(0x188a0), A(0x1a5d0)
it = refmgr.getReferenceSourceIterator(low, high, True)
for src in it:
    for r in refmgr.getReferencesFrom(src):
        out.append("src %s -> %s type %s" % (src, r.getToAddress(), r.getReferenceType()))

# 3. also scan raw body for 4-byte LE literals in window (l32r pool entries)
data = open("/home/OWNER/orca/projects/bc250/archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5", "rb").read()
out.append("=== RAW WORDS IN WINDOW 0x188a0-0x1a5d0 (file==sram) ===")
off = 0x188a0
while off < 0x1a5d0:
    w = struct.unpack_from("<I", data, off)[0]
    if w:
        out.append("%06x: %08x" % (off, w))
    off += 4

# 4. find functions calling 0x2a74 / 0x29f8 / 0x235c8 and any function whose body
#    references them; also decompile-lite: just list call sites
out.append("=== CALLERS of 0x2a74 / 0x29f8 / 0x235c8 / 0x1b514 ===")
targets = [0x2a74, 0x29f8, 0x235c8, 0x1b514]
for t in targets:
    ta = A(t)
    refs = refmgr.getReferencesTo(ta)
    callers = sorted(set(str(r.getFromAddress()) for r in refs if str(r.getReferenceType()).startswith("CALL")))
    out.append("target %x: %s" % (t, callers))

# 5. scan disassembly of whole program for calls to those helpers and preceding l32r/addi constants
out.append("=== CALL SITES with context (linear instruction scan) ===")
from ghidra.program.model.symbol import RefType
inst_it = listing.getInstructions(True)
insts = []
for i in inst_it:
    insts.append(i)

# build map addr->index for context lookup
idx = {}
for k, i in enumerate(insts):
    idx[i.getAddress().getOffset()] = k

for k, i in enumerate(insts):
    t = str(i)
    for tgt in targets:
        if ("0x%x" % tgt) in t or ("0%0*x" % (0, tgt)) == "":
            pass
    ft = i.getFlowType()
    if ft.isCall():
        dests = [r.getToAddress().getOffset() for r in i.getReferencesFrom()]
        if any(d in targets for d in dests):
            # print 12 preceding instructions
            s = []
            for j in range(max(0, k - 14), k + 1):
                ii = insts[j]
                s.append("  %s %s %s" % (ii.getAddress(), ii.getBytes().hex(), ii))
            out.append("CALLSITE at %s -> %s" % (i.getAddress(), ["%x" % d for d in dests]))
            out.extend(s)

with open("/home/OWNER/orca/projects/bc250/.procoder/tmp/chain_dev_out.txt", "w") as f:
    f.write("\n".join(out))
print("DONE, lines=%d" % len(out))
