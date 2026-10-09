#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase E: extract dedup'd GDDR6/memory question table from e1_setup_ifr.txt
into evidence/e1_gddr6_questions.txt."""
import re

SRC = r"C:\Users\OWNER\bc250-bios\evidence\e1_setup_ifr.txt"
DST = r"C:\Users\OWNER\bc250-bios\evidence\e1_gddr6_questions.txt"
FORMS = (
    "I Accept", "GDDR6 Common Options", "DRAM Timing Configuration",
    "DRAM Memory Mapping", "GDDR6 Debug Options", "GDDR6 DRAM Timing Configuration",
    "GDDR6 DRAM Controller Configuration", "DRAM Power Options",
    "GDDR6 Diagnostic and Debug Features", "SMU Features", "SMU Debug",
    "GFX Configuration", "AMD CBS",
)


def main():
    t = open(SRC, encoding="utf-8", errors="replace").read()
    seen = set()
    out = []
    for l in t.splitlines():
        if not ("ONE_OF" in l or "NUMERIC" in l or "TEXT" in l or "FORM" in l):
            continue
        if "var=AmdSetup" not in l and "FORM" not in l:
            continue
        m = re.search(r"@form='([^']*)'", l)
        if m and m.group(1).rstrip("\x00 ").strip() not in FORMS:
            continue
        k = l.strip()
        if k in seen:
            continue
        seen.add(k)
        out.append(k)
    open(DST, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("written", DST, len(out), "lines")


if __name__ == "__main__":
    main()
