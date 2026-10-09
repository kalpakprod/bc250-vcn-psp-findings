import json, subprocess, re, sys
from pathlib import Path

raw = subprocess.check_output(
    ["gh", "api", "repos/daveconde/bc250-vcn-enable/commits?per_page=100"],
    text=True,
)
commits = json.loads(raw)
print("n_commits", len(commits))
for c in commits:
    msg = c["commit"]["message"].splitlines()[0]
    print(c["sha"][:7], c["commit"]["author"]["date"][:16], msg)

src = Path(r"C:\Users\OWNER\tmp_bc250\upstream\daveconde-bc250-vcn-enable\enable_vcn.py").read_text(encoding="utf-8", errors="replace")
rd = Path(r"C:\Users\OWNER\tmp_bc250\upstream\daveconde-bc250-vcn-enable\README.md").read_text(encoding="utf-8", errors="replace")
both = src + rd
print("dates", sorted(set(re.findall(r"2026-08-\d\d", both))))
print("night_hits", len(re.findall(r"night[-\s]?\d", both, re.I)))
print("measured", len(re.findall(r"measured", both, re.I)))
print("wedge", len(re.findall(r"wedge", both, re.I)))
print("vacuous", len(re.findall(r"vacuous", both, re.I)))
print("unresolved", len(re.findall(r"unresolved", both, re.I)))
print("emdash_rd", rd.count("\u2014"))
print("designed_noop", len(re.findall(r"designed no-op|designed noop", both, re.I)))
print("all_ones", len(re.findall(r"all-ones|0xffffffff", both, re.I)))
# outcome honesty snippets
for pat in [
    r"designed no-op[^\n]{0,80}",
    r"writes are vacuous[^\n]{0,80}",
    r"HARD-WEDGE[^\n]{0,80}",
    r"board does NOT[^\n]{0,80}",
    r"unresolved[^\n]{0,100}",
    r"fire is a designed[^\n]{0,100}",
]:
    ms = re.findall(pat, both, re.I)
    print("PAT", pat[:40], "->", len(ms))
    for m in ms[:3]:
        print(" ", m[:140])
