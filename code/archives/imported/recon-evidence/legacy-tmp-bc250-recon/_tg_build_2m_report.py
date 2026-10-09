#!/usr/bin/env python3
"""Build 2-month BC-250 VCN/unlock progress report from TG dumps + GH metadata."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"C:\Users\OWNER\tmp_bc250\recon")
TG2M = BASE / "tg2m"
OUT = BASE / "tg_2m_progress_digest.md"
REPORT = BASE.parent / "specs" / "2026-08-25-bc250-vcn-2month-progress.md"
CUTOFF = datetime(2026, 6, 25, tzinfo=timezone.utc)

KW = re.compile(
    r"vcn|vaapi|encode|decode|/dev/video|psp|smu|domain\s*6|thelamer|daveconde|"
    r"bc250-vcn|skillfish|cyan_skillfish|navi10_vcn|firmware|прошивк|разблок|unlock|"
    r"deucher|amdgpu|ip\s*block|discovery|direct.?load|vclk|dclk|power.?gat|"
    r"isolation|second\s*gate|mailbox|bc250-collective|core.?unlock|8\s*ядер|"
    r"discord|вайб|claude|клод|media|ring\s*test|CAFEDEAD|FUN_|gpu_metrics|"
    r"harvest|0xffff|item_not_found|power\s*domain|vcn_v2|подпис",
    re.I,
)

CLAIM = re.compile(
    r"(работает|не\s*работает|завелось|не\s*завелось|успех|fail|failed|success|"
    r"PSP|SMU|domain\s*6|VCLK|DCLK|direct.?load|signature|подпис|вайб|Claude|клод|"
    r"Deucher|firmware|прошивк|ip\s*block|discovery|encode|decode|VAAPI|"
    r"github\.com/\S+|discord\.(?:gg|com)/\S+|harvest|power\s*domain|"
    r"FUN_\w+|0x98|0xffff0008|ITEM_NOT_FOUND|second\s*gate|ring)",
    re.I,
)


def load_msgs(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size < 20:
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
    return [m for m in ms if isinstance(m, dict)]


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


def load_commits(path: Path) -> list[tuple[str, str, str]]:
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return []
    if not isinstance(d, list):
        return []
    out = []
    for c in d:
        try:
            sha = c["sha"][:7]
            date = c["commit"]["author"]["date"]
            msg = c["commit"]["message"].split("\n")[0]
            out.append((sha, date, msg))
        except Exception:
            continue
    return out


def main() -> None:
    by_id: dict[int, dict] = {}
    srcs: dict[int, set[str]] = defaultdict(set)

    paths = list(TG2M.glob("q_*.json")) + list(BASE.glob("tg_bc250_*.json"))
    for p in paths:
        for m in load_msgs(p):
            mid = m.get("id")
            if mid is None:
                continue
            by_id[mid] = m
            srcs[mid].add(p.name)

    rows = []
    for mid, m in by_id.items():
        text = m.get("text") or ""
        dt = parse_dt(m.get("date"))
        if not KW.search(text):
            continue
        if dt and dt < CUTOFF:
            continue
        rows.append((dt, mid, m))

    rows.sort(key=lambda x: (x[0] or datetime.min.replace(tzinfo=timezone.utc), x[1]))

    months: dict[str, list] = defaultdict(list)
    for dt, mid, m in rows:
        months[dt.strftime("%Y-%m") if dt else "unknown"].append((dt, mid, m))

    # phase tags
    phases = {
        "psp_wall": [],
        "driver_ip": [],
        "smu_power": [],
        "daveconde": [],
        "core_unlock": [],
        "deucher": [],
        "firmware_blob": [],
        "vibe_skepticism": [],
        "other": [],
    }
    for dt, mid, m in rows:
        t = (m.get("text") or "").lower()
        tagged = False
        if "daveconde" in t or "bc250-vcn-enable" in t:
            phases["daveconde"].append((dt, mid, m)); tagged = True
        if "deucher" in t:
            phases["deucher"].append((dt, mid, m)); tagged = True
        if any(k in t for k in ["psp", "подпис", "0xffff", "item_not_found", "signed"]):
            phases["psp_wall"].append((dt, mid, m)); tagged = True
        if any(k in t for k in ["ip block", "ip_block", "discovery", "cyan_skillfish", "vcn драйвер", "vcn driver"]):
            phases["driver_ip"].append((dt, mid, m)); tagged = True
        if any(k in t for k in ["smu", "domain", "power", "vclk", "dclk", "fun_", "mailbox", "power gate"]):
            phases["smu_power"].append((dt, mid, m)); tagged = True
        if any(k in t for k in ["8 ядер", "core unlock", "bc250-core-unlock", "разблок"]):
            phases["core_unlock"].append((dt, mid, m)); tagged = True
        if any(k in t for k in ["navi10_vcn", "прошивк", "firmware", ".bin"]):
            phases["firmware_blob"].append((dt, mid, m)); tagged = True
        if any(k in t for k in ["вайб", "claude", "клод", "не рабоч"]):
            phases["vibe_skepticism"].append((dt, mid, m)); tagged = True
        if not tagged:
            phases["other"].append((dt, mid, m))

    lines: list[str] = []
    lines.append("# BC-250 VCN / unlock — 2-month progress digest\n\n")
    lines.append(f"Generated: 2026-08-25  \n")
    lines.append(f"Window: {CUTOFF.date()} → 2026-08-25 UTC  \n")
    lines.append(f"Source: Telegram MCP chat `-1002424231195` + GitHub APIs  \n")
    lines.append(f"Unique relevant TG msgs: **{len(rows)}**  \n")
    lines.append(f"TG dump files: {len(list(TG2M.glob('q_*.json')))}  \n\n")

    lines.append("## Counts by month\n\n")
    for k in sorted(months):
        lines.append(f"- **{k}**: {len(months[k])} msgs\n")

    senders: dict[str, int] = defaultdict(int)
    for _, _, m in rows:
        senders[str(m.get("sender") or "?")] += 1
    lines.append("\n## Top senders (relevant)\n\n")
    for name, c in sorted(senders.items(), key=lambda x: -x[1])[:25]:
        lines.append(f"- {name}: {c}\n")

    lines.append("\n## Theme buckets\n\n")
    for k, v in phases.items():
        lines.append(f"- **{k}**: {len(v)}\n")

    # key chronological milestones (hand-picked patterns + all high-signal)
    lines.append("\n## Chronological timeline (relevant)\n\n")
    for dt, mid, m in rows:
        text = (m.get("text") or "").replace("\n", " | ")
        if len(text) > 380:
            text = text[:380] + "…"
        ds = dt.isoformat() if dt else "?"
        who = m.get("sender") or "?"
        un = m.get("username")
        if un:
            who = f"{who} (@{un})"
        lines.append(f"- `{ds}` id={mid} **{who}** r={m.get('reply_to')}\n  {text}\n")

    lines.append("\n## Claim / URL hits\n\n")
    for dt, mid, m in rows:
        text = m.get("text") or ""
        urls = re.findall(r"https?://\S+", text)
        hits = CLAIM.findall(text)
        if not urls and not hits:
            continue
        ds = dt.date().isoformat() if dt else "?"
        hit_s = []
        for h in hits[:10]:
            hit_s.append(h if isinstance(h, str) else str(h))
        lines.append(f"- {ds} id={mid} {m.get('sender')}: urls={urls[:4]} hits={hit_s}\n")

    # GH section
    lines.append("\n## GitHub commit timelines\n\n")
    for label, path in [
        ("thelamer/bc250-vcn", BASE / "thelamer_commits.json"),
        ("daveconde/bc250-vcn-enable", BASE / "dave_commits.json"),
        ("bc250-collective/amd_smu_reverse_engineering", BASE / "smu_re_commits.json"),
        ("rw-r-r-0644/bc250-core-unlock", BASE / "core_unlock_commits.json"),
    ]:
        commits = load_commits(path)
        lines.append(f"### {label} ({len(commits)} commits listed)\n\n")
        for sha, date, msg in commits[:25]:
            lines.append(f"- `{date[:10]}` `{sha}` {msg}\n")
        lines.append("\n")

    repos_path = BASE / "gh_bc250_repos.json"
    if repos_path.exists():
        try:
            repos = json.loads(repos_path.read_text(encoding="utf-8"))
            lines.append("## Recently updated BC-250 repos\n\n")
            for r in repos[:30]:
                desc = (r.get("description") or "")[:90]
                lines.append(
                    f"- `{r.get('pushedAt','')[:10]}` ★{r.get('stargazersCount',0)} "
                    f"**{r.get('fullName')}** — {desc}\n"
                )
        except Exception:
            pass

    OUT.write_text("".join(lines), encoding="utf-8")
    print(f"digest {OUT} msgs={len(rows)} months={ {k:len(v) for k,v in months.items()} }")
    print(f"themes { {k:len(v) for k,v in phases.items()} }")


if __name__ == "__main__":
    main()
