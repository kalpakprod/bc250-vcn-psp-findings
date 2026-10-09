#!/usr/bin/env python3
"""Fetch multi-query TG search dumps for BC-250 2-month progress review."""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

OUT = Path(r"C:\Users\OWNER\tmp_bc250\recon\tg2m")
OUT.mkdir(parents=True, exist_ok=True)
CHAT = "-1002424231195"

QUERIES = [
    "VCN",
    "VAAPI",
    "SMU",
    "PSP",
    "thelamer",
    "daveconde",
    "skillfish",
    "navi10_vcn",
    "Deucher",
    "domain",
    "firmware",
    "unlock",
    "encode",
    "decode",
    "vclk",
    "dclk",
    "isolation",
    "mailbox",
    "ip block",
    "discovery",
    "amdgpu",
    "core unlock",
    "8 ядер",
    "Claude",
    "вайбкод",
    "bc250-vcn",
    "FUN_",
    "CAFEDEAD",
    "media",
    "power gate",
    "direct load",
    "ring test",
    "gpu_metrics",
    "cyan_skillfish",
    "bc250-collective",
    "rw-r-r-0644",
    "second gate",
    "подпис",
    "прошивк",
    "разблок",
]


def safe_name(q: str) -> str:
    return re.sub(r"[^\w\-]+", "_", q, flags=re.U).strip("_") or "q"


def fetch(q: str) -> Path:
    name = safe_name(q)
    path = OUT / f"q_{name}.json"
    cmd = [
        "mcporter.cmd",
        "call",
        "telegram.search_messages",
        f"chat_id={CHAT}",
        f"query={q}",
        "limit=50",
        "--output",
        "json",
    ]
    print(f"QUERY {q!r} -> {path.name}", flush=True)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        body = r.stdout if r.stdout.strip() else r.stderr
        path.write_text(body, encoding="utf-8")
        print(f"  bytes={path.stat().st_size} rc={r.returncode}", flush=True)
    except Exception as e:
        path.write_text(json.dumps({"error": str(e)}), encoding="utf-8")
        print(f"  ERR {e}", flush=True)
    time.sleep(0.35)
    return path


def main() -> None:
    for q in QUERIES:
        fetch(q)
    files = list(OUT.glob("q_*.json"))
    print(f"DONE files={len(files)} total_bytes={sum(p.stat().st_size for p in files)}")


if __name__ == "__main__":
    main()
