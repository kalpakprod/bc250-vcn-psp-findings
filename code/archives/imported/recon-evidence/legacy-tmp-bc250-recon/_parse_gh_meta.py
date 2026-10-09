#!/usr/bin/env python3
import json
from pathlib import Path

base = Path(r"C:\Users\OWNER\tmp_bc250\recon")
out = []
for p in [
    "dave_commits.json",
    "thelamer_commits.json",
    "gh_bc250_repos.json",
    "smu_re_commits.json",
    "core_unlock_commits.json",
]:
    pp = base / p
    out.append(f"== {p} exists={pp.exists()} size={pp.stat().st_size if pp.exists() else 0}\n")
    if not pp.exists():
        continue
    try:
        d = json.loads(pp.read_text(encoding="utf-8"))
    except Exception as e:
        out.append(f"parse err {e}\n head={pp.read_text(encoding='utf-8', errors='replace')[:200]!r}\n")
        continue
    if isinstance(d, list) and d and isinstance(d[0], dict) and "sha" in d[0]:
        out.append(f"commits {len(d)}\n")
        for c in d[:20]:
            out.append(
                f"  {c['sha'][:7]} {c['commit']['author']['date'][:10]} "
                f"{c['commit']['message'].split(chr(10))[0][:100]}\n"
            )
    elif isinstance(d, list) and d and isinstance(d[0], dict) and "fullName" in d[0]:
        out.append(f"repos {len(d)}\n")
        for r in d[:25]:
            out.append(
                f"  {r.get('pushedAt','')[:10]} ★{r.get('stargazersCount')} "
                f"{r.get('fullName')} {(r.get('description') or '')[:70]}\n"
            )
    else:
        out.append(f"type={type(d)} sample={str(d)[:200]}\n")

path = base / "gh_meta_summary.txt"
path.write_text("".join(out), encoding="utf-8")
print(path.read_text(encoding="utf-8"))
