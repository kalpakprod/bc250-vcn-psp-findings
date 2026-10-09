# A26b: per-address ordered value sequences of the xx234 family (SMN 0x090xxxxx + 0x234)
# and D3-B2 targets, in stock/donor, groups 0x201/0x280. Answers: what final value does
# each side leave (last-writer-wins), and which addresses exist on each side only.
import re, io, os

EV = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"..\..\evidence")
FILES = {
    ("STOCK", 0x201): "a26_STOCK_24_grp201_full.txt",
    ("STOCK", 0x280): "a26_STOCK_24_grp280_full.txt",
    ("DONOR", 0x201): "a26_DONOR_24_grp201_full.txt",
    ("DONOR", 0x280): "a26_DONOR_24_grp280_full.txt",
}
TARGETS = {0x0900C234, 0x0900C914, 0x0900C930, 0x0900CB80}

data = {}
for (tag, grp), fn in FILES.items():
    seq = []
    for line in open(os.path.join(EV, fn)):
        m = re.match(r"0x([0-9a-f]+) -> 0x([0-9a-f]+)", line)
        if m:
            seq.append((int(m.group(1), 16), int(m.group(2), 16)))
    data[(tag, grp)] = seq

xx234 = lambda a: (a & 0xFFF) == 0x234

out = io.StringIO()


def P(s=""):
    print(s)
    out.write(s + "\n")


P("== xx234 family: per-address sequences (in order) and final value ==")
for (tag, grp), seq in sorted(data.items()):
    fam = [(a, v) for a, v in seq if xx234(a)]
    per = {}
    for a, v in fam:
        per.setdefault(a, []).append(v)
    P("%s grp %03x: %d pairs, %d uniq addrs" % (tag, grp, len(fam), len(per)))
    finals0 = sum(1 for a, vs in per.items() if vs[-1] == 0)
    finals1 = sum(1 for a, vs in per.items() if vs[-1] == 1)
    finalsx = sum(1 for a, vs in per.items() if vs[-1] not in (0, 1))
    P("  final: ->0 %d, ->1 %d, ->other %d" % (finals0, finals1, finalsx))
    # collapse identical value patterns
    pats = {}
    for a, vs in per.items():
        pats.setdefault(tuple(vs), []).append(a)
    for vs, addrs in sorted(pats.items(), key=lambda kv: -len(kv[1])):
        P("  %s : %d addrs %s" % ("->".join(hex(v) for v in vs), len(addrs),
                                  " ".join("%x" % a for a in addrs[:12]) + (" ..." if len(addrs) > 12 else "")))

P("")
P("== D3-B2 targets per side/group (ordered) ==")
for (tag, grp), seq in sorted(data.items()):
    for a in sorted(TARGETS):
        vs = [v for x, v in seq if x == a]
        if vs:
            P("%s grp %03x: %#x -> %s" % (tag, grp, a, ["%#x" % v for v in vs]))

P("")
P("== xx234 address sets: stock-only / donor-only / shared ==")
s201 = {a for a, v in data[("STOCK", 0x201)] if xx234(a)}
d201 = {a for a, v in data[("DONOR", 0x201)] if xx234(a)}
P("stock-0x201 uniq: %d, donor-0x201 uniq: %d, shared: %d" % (len(s201), len(d201), len(s201 & d201)))
P("stock-only: %s" % " ".join("%x" % a for a in sorted(s201 - d201)))
P("donor-only: %s" % " ".join("%x" % a for a in sorted(d201 - s201)))

open(os.path.join(EV, "a26b_xx234_semantics.txt"), "w").write(out.getvalue())
print("\nsaved: a26b_xx234_semantics.txt")
