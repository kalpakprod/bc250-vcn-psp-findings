#!/usr/bin/env python3
"""Extract high-signal milestone lines from 2m digest for the progress report."""
from __future__ import annotations

import re
from pathlib import Path

src = Path(r"C:\Users\OWNER\tmp_bc250\recon\tg_2m_progress_digest.md").read_text(
    encoding="utf-8"
)
# pull timeline bullets
pat = re.compile(
    r"^- `(20\d\d-\d\d-\d\dT[^`]+)` id=(\d+) \*\*(.+?)\*\*.*?\n  (.+)$",
    re.M,
)
hi = re.compile(
    r"vcn|vaapi|psp|smu|domain|deucher|dave|thelamer|direct.?load|vclk|dclk|"
    r"ip block|discovery|firmware|прошивк|подпис|FUN_|0x98|harvest|power|"
    r"hang|завес|не работ|encode|decode|navi10|skillfish|mailbox|ring|"
    r"github\.com|discord|claude|вайб|core.?unlock|8 ядер|разблок",
    re.I,
)
rows = []
for m in pat.finditer(src):
    date, mid, who, text = m.groups()
    if hi.search(text) or hi.search(who):
        rows.append((date, mid, who, text))

# score by keyword density
def score(t: str) -> int:
    keys = [
        "vcn",
        "psp",
        "smu",
        "domain",
        "deucher",
        "direct",
        "vclk",
        "hang",
        "dave",
        "thelamer",
        "firmware",
        "ip block",
        "discovery",
        "FUN_",
        "0x98",
        "encode",
        "navi10",
        "power",
        "claude",
        "вайб",
    ]
    tl = t.lower()
    return sum(1 for k in keys if k.lower() in tl)

rows.sort(key=lambda r: (-score(r[3] + r[2]), r[0]))
out = Path(r"C:\Users\OWNER\tmp_bc250\recon\tg_milestones_ranked.txt")
lines = []
for date, mid, who, text in rows[:80]:
    lines.append(f"{date[:10]} id={mid} s={score(text)} {who}\n  {text[:300]}\n")
out.write_text("".join(lines), encoding="utf-8")
print("wrote", out, "n", len(rows))
