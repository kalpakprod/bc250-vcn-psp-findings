import json
import re
from pathlib import Path

def load(path):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    d = json.loads(raw)
    res = d.get("result", d)
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except json.JSONDecodeError:
            return {"raw": res[:2000]}
    return res

def msgs(obj):
    if isinstance(obj, dict):
        for k in ("messages", "results", "items", "data"):
            if k in obj and isinstance(obj[k], list):
                return obj[k]
        # nested
        if "result" in obj:
            return msgs(obj["result"] if not isinstance(obj["result"], str) else json.loads(obj["result"]))
    if isinstance(obj, list):
        return obj
    return []

def fmt(m, i):
    if not isinstance(m, dict):
        return str(m)[:300]
    mid = m.get("id") or m.get("message_id") or m.get("msg_id")
    date = m.get("date") or m.get("time") or ""
    sender = m.get("sender") or m.get("from") or m.get("sender_name") or m.get("author") or ""
    if isinstance(sender, dict):
        sender = sender.get("username") or sender.get("name") or sender.get("first_name") or str(sender)
    text = m.get("text") or m.get("message") or m.get("body") or ""
    if isinstance(text, list):
        text = "".join(str(x) for x in text)
    topic = m.get("topic") or m.get("forum_topic") or m.get("reply_to") or ""
    link = m.get("link") or m.get("url") or ""
    return f"[{i}] id={mid} date={date} from={sender} topic={topic}\n{text}\nlink={link}\n---"

base = Path(r"C:\Users\OWNER\tmp_bc250\recon")
out_lines = []
for name in ["tg_bc250_hist.json", "tg_bc250_vcn.json", "tg_bc250_dave.json", "tg_bc250_unlock.json"]:
    p = base / name
    out_lines.append(f"\n===== {name} size={p.stat().st_size} =====\n")
    obj = load(p)
    # dump keys
    if isinstance(obj, dict):
        out_lines.append("keys=" + ",".join(obj.keys()) + "\n")
        out_lines.append(json.dumps(obj, ensure_ascii=False)[:2500] + "\n")
    ms = msgs(obj)
    out_lines.append(f"msg_count={len(ms)}\n")
    for i, m in enumerate(ms[:40]):
        out_lines.append(fmt(m, i) + "\n")
        if isinstance(m, dict):
            out_lines.append("raw_keys=" + ",".join(m.keys()) + "\n")

out = base / "tg_bc250_parsed.txt"
out.write_text("".join(out_lines), encoding="utf-8")
print("wrote", out, "chars", out.stat().st_size)
