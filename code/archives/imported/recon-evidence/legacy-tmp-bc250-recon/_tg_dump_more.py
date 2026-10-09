import json
from pathlib import Path

base = Path(r"C:\Users\OWNER\tmp_bc250\recon")
parts = []
for name in [
    "tg_bc250_pavel.json",
    "tg_bc250_nerab.json",
    "tg_bc250_discord.json",
    "tg_bc250_alex.json",
    "tg_bc250_vibe.json",
    "tg_bc250_vcnru.json",
    "tg_bc250_vcnen.json",
    "tg_bc250_smu.json",
    "tg_bc250_thelamer.json",
    "tg_bc250_gate.json",
    "tg_bc250_dave2.json",
]:
    p = base / name
    if not p.exists():
        parts.append(f"## {name} MISSING\n")
        continue
    d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    res = d.get("result", d)
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except Exception:
            parts.append(f"## {name} raw {res[:300]}\n")
            continue
    ms = res.get("results", []) if isinstance(res, dict) else res
    parts.append(f"## {name} n={len(ms) if isinstance(ms,list) else '?'}\n")
    if not isinstance(ms, list):
        continue
    for m in ms[:25]:
        if not isinstance(m, dict):
            continue
        text = m.get("text") or ""
        parts.append(
            f"{m.get('date')} | {m.get('sender')} (@{m.get('username')}) | "
            f"id={m.get('id')} reply={m.get('reply_to')}\n{text}\n---\n"
        )

out = base / "tg_bc250_more.txt"
out.write_text("".join(parts), encoding="utf-8")
print(out, out.stat().st_size)
