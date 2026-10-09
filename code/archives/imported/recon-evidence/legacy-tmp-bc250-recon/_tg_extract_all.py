import json
import re
from pathlib import Path

base = Path(r"C:\Users\OWNER\tmp_bc250\recon")

def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    res = d.get("result", d)
    if isinstance(res, str):
        res = json.loads(res)
    if isinstance(res, dict):
        return res.get("results", res.get("messages", []))
    return res if isinstance(res, list) else []

parts = []
for path in sorted(base.glob("tg_bc250_*.json")):
    ms = load(path)
    parts.append(f"\n## {path.name} n={len(ms)}\n")
    for m in ms:
        if not isinstance(m, dict):
            parts.append(str(m)[:500] + "\n")
            continue
        text = m.get("text") or ""
        # for hist keep only relevant; for search dumps keep all
        if path.name == "tg_bc250_hist.json" and not re.search(
            r"vcn|dave|github\.com|разблок|unlock|smu|psp|media|vaapi|encode|decode|domain|gate|thelamer|discord|enable_vcn|bc250-vcn",
            text,
            re.I,
        ):
            continue
        parts.append(
            f"{m.get('date')} | {m.get('sender')} (@{m.get('username')}) | "
            f"id={m.get('id')} reply={m.get('reply_to')}\n{text}\n---\n"
        )

out = base / "tg_bc250_vcn_digest.txt"
text = "".join(parts)
out.write_text(text, encoding="utf-8")
print("wrote", out, "bytes", out.stat().st_size)
print("files", [p.name for p in sorted(base.glob('tg_bc250_*.json'))])
