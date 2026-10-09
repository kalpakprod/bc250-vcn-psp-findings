import json
import re
from pathlib import Path

p = Path(r"C:\Users\OWNER\tmp_bc250\recon\tg_chats.json")
raw = p.read_text(encoding="utf-8", errors="replace")
d = json.loads(raw)
res = d.get("result", d)
if isinstance(res, str):
    res = json.loads(res)
items = res.get("results", res) if isinstance(res, dict) else res
out = Path(r"C:\Users\OWNER\tmp_bc250\recon\tg_chats_titles.txt")
lines = []
keys = re.compile(r"bc.?250|bc250|skillfish|cyan|vcn|steammachine|AMD BC|BC-250", re.I)
hits = []
for it in items:
    title = str(it.get("title") or it.get("name") or "")
    uname = str(it.get("username") or "")
    line = f"{it.get('chat_id')}|{it.get('type')}|{title}|{uname}|u{it.get('unread')}"
    lines.append(line)
    blob = title + " " + uname
    if keys.search(blob) or ("AMD" in title and "BC" in title.upper()) or ("250" in title and "BC" in title.upper()):
        hits.append(line)
out.write_text("\n".join(lines), encoding="utf-8")
print("TOTAL", len(items))
print("HITS", len(hits))
for h in hits:
    print("HIT", h)
# broader
print("---BROAD---")
for line in lines:
    if re.search(r"250|BC-|AMD BC|VCN|Skillfish|Cyan|Steam.?Machine|флуд|Flood|Разгон|Bios", line, re.I):
        print("B", line)
