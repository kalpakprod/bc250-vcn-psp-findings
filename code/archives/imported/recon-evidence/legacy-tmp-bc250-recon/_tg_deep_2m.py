#!/usr/bin/env python3
"""Parse multi-query TG dumps into a 2-month VCN/unlock progress digest."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(r"C:\Users\OWNER\tmp_bc250\recon")
OUT = BASE / "tg_2m_progress_digest.md"
CUTOFF = datetime(2026, 6, 25, tzinfo=timezone.utc)  # ~2 months before 2026-08-25

QUERIES = [
    "VCN",
    "vcn",
    "VAAPI",
    "vaapi",
    "encode",
    "decode",
    "media",
    "PSP",
    "psp",
    "SMU",
    "smu",
    "domain",
    "thelamer",
    "daveconde",
    "bc250-vcn",
    "skillfish",
    "cyan_skillfish",
    "navi10_vcn",
    "firmware",
    "прошивк",
    "разблок",
    "unlock",
    "Deucher",
    "amdgpu",
    "ip block",
    "discovery",
    "direct load",
    "direct-load",
    "ring",
    "VCLK",
    "DCLK",
    "vclk",
    "dclk",
    "power gate",
    "powergate",
    "isolation",
    "second gate",
    "FUN_",
    "mailbox",
    "bc250-collective",
    "rw-r-r-0644",
    "core unlock",
    "8 ядер",
    "8 core",
    "Discord",
    "discord.gg",
    "вайбкод",
    "Claude",
    "клод",
]

KEYWORDS = re.compile(
    r"vcn|vaapi|encode|decode|/dev/video|psp|smu|domain\s*6|thelamer|daveconde|"
    r"bc250-vcn|skillfish|cyan_skillfish|navi10_vcn|firmware|прошивк|разблок|unlock|"
    r"deucher|amdgpu|ip\s*block|discovery|direct.?load|vclk|dclk|power.?gat|"
    r"isolation|second\s*gate|mailbox|bc250-collective|core.?unlock|8\s*ядер|"
    r"discord|вайб|claude|клод|media|ring\s*test|CAFEDEAD|FUN_|gpu_metrics",
    re.I,
)

def load_msgs(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size < 10:
        return []
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return []
    res = d.get("result", d)
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except json.JSONDecodeError:
            return []
    if isinstance(res, dict):
        ms = res.get("results") or res.get("messages") or []
    elif isinstance(res, list):
        ms = res
    else:
        return []
    out = []
    for m in ms:
        if isinstance(m, dict) and (m.get("text") or m.get("id")):
            out.append(m)
    return out


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def main() -> None:
    by_id: dict[int, dict] = {}
    sources: dict[int, set[str]] = defaultdict(set)

    for p in sorted(BASE.glob("tg_bc250_*.json")):
        for m in load_msgs(p):
            mid = m.get("id")
            if mid is None:
                continue
            by_id[mid] = m
            sources[mid].add(p.name)

    # filter relevant + date
    rows = []
    for mid, m in by_id.items():
        text = m.get("text") or ""
        dt = parse_dt(m.get("date"))
        if not KEYWORDS.search(text):
            continue
        if dt and dt < CUTOFF:
            continue
        rows.append((dt, mid, m, sources[mid]))

    rows.sort(key=lambda x: (x[0] or datetime.min.replace(tzinfo=timezone.utc), x[1]))

    # monthly buckets
    months: dict[str, list] = defaultdict(list)
    for dt, mid, m, src in rows:
        key = dt.strftime("%Y-%m") if dt else "unknown"
        months[key].append((dt, mid, m, src))

    lines: list[str] = []
    lines.append("# BC-250 TG progress digest (~2 months)\n")
    lines.append(f"Cutoff: {CUTOFF.date()} UTC → now\n")
    lines.append(f"Unique relevant msgs: {len(rows)}\n")
    lines.append(f"Sources scanned: {len(list(BASE.glob('tg_bc250_*.json')))} json dumps\n")

    # timeline bullets (compact)
    lines.append("\n## Timeline (relevant only)\n")
    for dt, mid, m, src in rows:
        sender = m.get("sender") or "?"
        uname = m.get("username") or ""
        text = (m.get("text") or "").replace("\n", " | ")
        if len(text) > 420:
            text = text[:420] + "…"
        ds = dt.isoformat() if dt else "?"
        who = f"{sender}" + (f" (@{uname})" if uname else "")
        lines.append(f"- `{ds}` id={mid} **{who}** reply={m.get('reply_to')}\n  {text}\n")

    # month summaries placeholders filled by counts
    lines.append("\n## Counts by month\n")
    for k in sorted(months):
        lines.append(f"- {k}: {len(months[k])} msgs\n")

    # top senders
    senders: dict[str, int] = defaultdict(int)
    for _, _, m, _ in rows:
        senders[str(m.get("sender") or "?")] += 1
    lines.append("\n## Top senders (relevant)\n")
    for name, c in sorted(senders.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"- {name}: {c}\n")

    # claim extraction
    claim_re = re.compile(
        r"(работает|не работает|завелось|не завелось|успех|fail|failed|success|"
        r"PSP|SMU|domain|VCLK|DCLK|direct.?load|signature|подпис|вайб|Claude|"
        r"Deucher|firmware|прошивк|ip block|discovery|encode|decode|VAAPI|"
        r"github\.com/\S+|discord\.(gg|com)/\S+)",
        re.I,
    )
    lines.append("\n## Claim / link hits\n")
    for dt, mid, m, src in rows:
        text = m.get("text") or ""
        hits = claim_re.findall(text)
        if not hits and "http" not in text.lower():
            continue
        urls = re.findall(r"https?://\S+", text)
        if not urls and not hits:
            continue
        ds = dt.date().isoformat() if dt else "?"
        lines.append(
            f"- {ds} id={mid} {m.get('sender')}: urls={urls[:3]} hits={[h if isinstance(h,str) else h[0] for h in hits[:8]]}\n"
        )

    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {OUT} msgs={len(rows)} months={dict((k,len(v)) for k,v in months.items())}")


if __name__ == "__main__":
    main()
