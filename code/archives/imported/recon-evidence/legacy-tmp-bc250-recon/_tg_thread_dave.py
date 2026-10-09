import json
from pathlib import Path

# Pull messages that reply into the daveconde thread (157865) or mention it.
base = Path(r"C:\Users\OWNER\tmp_bc250\recon")
all_ms = []
for p in base.glob("tg_bc250_*.json"):
    try:
        d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    res = d.get("result", d)
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except Exception:
            continue
    ms = res.get("results", []) if isinstance(res, dict) else res
    if isinstance(ms, list):
        for m in ms:
            if isinstance(m, dict):
                m["_src"] = p.name
                all_ms.append(m)

# unique by id
by_id = {}
for m in all_ms:
    by_id[m.get("id")] = m

# thread: root 157865 and replies to it or to known children
wanted = {157865, 157869, 157870, 157871}
# expand one hop
for m in list(by_id.values()):
    if m.get("reply_to") in wanted or m.get("id") in wanted:
        wanted.add(m.get("id"))
        if m.get("reply_to"):
            wanted.add(m.get("reply_to"))

# also any text with daveconde
for m in by_id.values():
    t = (m.get("text") or "").lower()
    if "daveconde" in t or "bc250-vcn-enable" in t or "vcn-enable" in t:
        wanted.add(m.get("id"))

rows = [by_id[i] for i in sorted(wanted) if i in by_id]
rows.sort(key=lambda m: m.get("date") or "")
out = []
for m in rows:
    out.append(
        f"{m.get('date')} | {m.get('sender')} (@{m.get('username')}) | "
        f"id={m.get('id')} reply={m.get('reply_to')} src={m.get('_src')}\n"
        f"{m.get('text') or ''}\n---\n"
    )
path = base / "tg_bc250_dave_thread.txt"
path.write_text("".join(out), encoding="utf-8")
print("thread_msgs", len(rows))
print(path.read_text(encoding="utf-8"))
