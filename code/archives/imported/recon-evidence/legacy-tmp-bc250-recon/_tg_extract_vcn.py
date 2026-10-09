import json
import re
from pathlib import Path

def load(path):
    d = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    res = d.get("result", d)
    if isinstance(res, str):
        res = json.loads(res)
    return res.get("results", res)

base = Path(r"C:\Users\OWNER\tmp_bc250\recon")
out = []
for name in ["tg_bc250_hist.json", "tg_bc250_vcn.json", "tg_bc250_dave.json", "tg_bc250_unlock.json"]:
    ms = load(base / name)
    out.append(f"\n## {name} n={len(ms)}\n")
    for m in ms:
        text = m.get("text") or ""
        if name != "tg_bc250_hist.json" or re.search(
            r"vcn|dave|github|разблок|unlock|smu|psp|media|vaapi|encode|decode|domain|second gate|thelamer|discord",
            text,
            re.I,
        ):
            out.append(
                f"{m.get('date')} | {m.get('sender')} (@{m.get('username')}) | id={m.get('id')} reply={m.get('reply_to')}\n{text}\n---\n"
            )

Path(base / "tg_bc250_vcn_extract.txt").write_text("".join(out), encoding="utf-8")
print("ok", len("".join(out)))
for line in "".join(out).splitlines()[:120]:
    print(line)
