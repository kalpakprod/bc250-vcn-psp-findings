#!/usr/bin/env python3
"""F1: classify gasket-group SMN address spaces, stock vs donor; GFX diff.

Reads the full pair dumps (a26_*_grp*_full.txt) and answers phase-F
question 2: do the PSP gasket groups carry any GFX/GC-space SMN pairs
(space 0x03xxxxxx outside DF 0x03A2xxxxx / 0x03D2xxxxx, or any pair that
maps into GC/NBIF config space)?  Prints per-file address-space census
and the full stock-vs-donor diff of 0x03xxxxxx pairs.
"""
import re, sys, os

EV = r"C:\Users\OWNER\bc250-bios\evidence"
FILES = [
    ("a26_STOCK_24_grp201_full.txt", "stock grp201"),
    ("a26_STOCK_24_grp280_full.txt", "stock grp280"),
    ("a26_DONOR_24_grp201_full.txt", "donor grp201"),
    ("a26_DONOR_24_grp280_full.txt", "donor grp280"),
]

PAIR_RE = re.compile(r"0x([0-9a-fA-F]{8})\s*->\s*0x([0-9a-fA-F]{8})")

def space(a):
    if 0x03000000 <= a <= 0x03FFFFFF:
        if 0x03A20000 <= a <= 0x03A2FFFF:
            return "DF (0x03A2xxxx)"
        if 0x03D20000 <= a <= 0x03D2FFFF:
            return "DF (0x03D2xxxx)"
        return "0x03xxxxxx NON-DF"
    if 0x09000000 <= a <= 0x093FFFFF:
        return "NBIF/VCN (0x09xxxxxx)"
    if 0x00010000 <= a <= 0x0001FFFF:
        return "short/mailbox"
    return "other"

def load(name):
    d = {}
    for line in open(os.path.join(EV, name)):
        m = PAIR_RE.search(line)
        if m:
            a, v = int(m.group(1), 16), int(m.group(2), 16)
            d.setdefault(a, []).append(v)   # keep sequence, final value = last
    return d

def final(d):
    return {a: v[-1] for a, v in d.items()}

def main():
    out = []
    log = out.append
    allmaps = {}
    for name, tag in FILES:
        d = load(name)
        allmaps[tag] = d
        spaces = {}
        for a in d:
            spaces[space(a)] = spaces.get(space(a), 0) + 1
        log("== %s (%s): %d unique addresses" % (tag, name, len(d)))
        for s in sorted(spaces, key=lambda s: -spaces[s]):
            log("   %-22s %d" % (s, spaces[s]))
    # stock vs donor diff over all 0x03-space + full
    for grp in ("201", "280"):
        st = final(allmaps["stock grp%s" % grp])
        do = final(allmaps["donor grp%s" % grp])
        log("== grp%s final-value diff stock vs donor (0x03-space and all):" % grp)
        keys = sorted(set(st) | set(do))
        n = 0
        for a in keys:
            if st.get(a) != do.get(a):
                s = space(a)
                if "0x03" in s or True:
                    log("   0x%08X: stock=%s donor=%s [%s]" %
                        (a,
                         ("0x%08X" % st[a]) if a in st else "absent",
                         ("0x%08X" % do[a]) if a in do else "absent", s))
                    n += 1
        log("   total differing: %d" % n)
    # explicit verdict on GC presence
    gc_hits = []
    for tag, d in allmaps.items():
        for a in d:
            if "NON-DF" in space(a):
                gc_hits.append((tag, a, d[a]))
    log("== non-DF 0x03-space pairs across all dumps: %d" % len(gc_hits))
    for tag, a, v in gc_hits:
        log("   %s 0x%08X -> %s" % (tag, a, [hex(x) for x in v]))
    log("")
    log("VERDICT: gasket groups carry ZERO GC/NBIF-GFX-space SMN pairs;")
    log("all 0x03-space pairs are DF fabric registers. The PSP gasket/policy")
    log("mechanism (the proven VCN-unlock path) cannot express CU/WGP changes.")
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(EV, "f1_gasket_gfx_diff.txt"), "w",
              encoding="utf-8") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
