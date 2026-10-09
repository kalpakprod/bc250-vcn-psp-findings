import json
from pathlib import Path

base = Path(r"C:\Users\OWNER\tmp_bc250\recon")
files = [
    "tg_bc250_vcn.json",
    "tg_bc250_dave2.json",
    "tg_bc250_gate.json",
    "tg_bc250_thelamer.json",
    "tg_bc250_smu.json",
    "tg_bc250_vcnen.json",
    "tg_bc250_vcnru.json",
    "tg_bc250_vibe.json",
    "tg_bc250_hist100.json",
]
parts = []
for name in files:
    p = base / name
    if not p.exists():
        parts.append(f"\n## {name} MISSING\n")
        continue
    d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    res = d.get("result", d)
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except json.JSONDecodeError:
            parts.append(f"\n## {name} RAW\n{res[:1500]}\n")
            continue
    ms = res.get("results", res) if isinstance(res, dict) else res
    if not isinstance(ms, list):
        parts.append(f"\n## {name} type={type(ms)}\n{str(ms)[:1500]}\n")
        continue
    parts.append(f"\n## {name} n={len(ms)}\n")
    for m in ms:
        if not isinstance(m, dict):
            continue
        text = m.get("text") or ""
        # hist100: only VCN-ish
        if name == "tg_bc250_hist100.json":
            low = text.lower()
            if not any(k in low for k in ["vcn", "dave", "github.com", "smu", "unlock", "разблок", "enable", "discord", "вайб", "media", "vaapi"]):
                continue
        parts.append(
            f"{m.get('date')} | {m.get('sender')} (@{m.get('username')}) | "
            f"id={m.get('id')} reply={m.get('reply_to')}\n{text}\n---\n"
        )

out = base / "tg_bc250_full_digest.txt"
out.write_text("".join(parts), encoding="utf-8")
print("wrote", out, out.stat().st_size)
