#!/usr/bin/env python3
"""Phase 17.1: parse EFI Firmware Volumes from stock ROMs and dump TE images,
recursing through compressed (LZMA) and GUIDed sections. Names come from UI
sections (UCS-2)."""
import os, re, struct, lzma

OUT = r"C:\Users\OWNER\tmp_bc250\recon\stock_te_out"
os.makedirs(OUT, exist_ok=True)

ROMS = {
    "renoir": r"C:\Users\OWNER\tmp_bc250\recon\renoir_a3mstx_360\A3MSTX_3.60",
    "cezanne": r"C:\Users\OWNER\tmp_bc250\recon\cezanne_a3mstx_370e\A3MSTX_3.70E",
}

SECTION_COMPRESSION = 0x01
SECTION_GUIDED = 0x02
SECTION_PE32 = 0x10
SECTION_TE = 0x12
SECTION_RAW = 0x19
SECTION_UI = 0x15
SECTION_DEPEX = 0x13
SECTION_VERSION = 0x14

def u24(b, o):
    return int.from_bytes(b[o:o + 3], "little")

def read_ui(data, off):
    try:
        return data[off:].split(b"\x00\x00", 1)[0].decode("utf-16-le", "ignore")
    except Exception:
        return ""

def lzma_decompress(body):
    """EFI LZMA: props(1) + dict(4) + raw stream."""
    p = body[0]
    lc = p % 9
    lp = (p // 9) % 5
    pb = p // 45
    dsize = int.from_bytes(body[1:5], "little")
    raw = body[5:]
    for d in ((dsize, 1 << 27, 1 << 24, 1 << 20)):
        try:
            dec = lzma.LZMADecompressor(format=lzma.FORMAT_RAW,
                                        filters=[{"id": lzma.FILTER_LZMA1,
                                                  "dict_size": d, "lc": lc,
                                                  "lp": lp, "pb": pb}])
            return dec.decompress(raw)
        except lzma.LZMAError:
            continue
    return None

def iter_sections(data, base, n, ctx, depth):
    off = base
    end = base + n
    sections = []
    while off + 4 <= end and depth < 6:
        sz = u24(data, off)
        t = data[off + 3]
        if sz < 4 or off + sz > end:
            break
        body = data[off + 4:off + sz]
        sections.append((t, body, off))
        off += (sz + 3) & ~3
    return sections

def walk_level(data, base, n, ctx, depth=0):
    buf = data[base:base + n]
    for t, body, soff in iter_sections(data, base, n, ctx, depth):
        if t == SECTION_UI:
            ctx["ui"] = read_ui(body, 0)
        elif t == SECTION_TE and body[:2] == b"VZ":
            name = ctx.get("ui") or f"te_{ctx['fv']:#x}_{base + soff:#x}"
            fn = os.path.join(OUT, f"{ctx['rom']}_{name}.te")
            if not os.path.exists(fn):
                open(fn, "wb").write(body)
            print(f"[TE] {fn} ({len(body)} B)")
        elif t == SECTION_PE32:
            pass  # x86 executables are TE on AMI PEI; keep quiet
        elif t == SECTION_COMPRESSION:
            if len(body) >= 5 and body[4] == 1:
                u = lzma_decompress(body[5:])
            else:
                u = None
            if u is None:
                print(f"[compr] skip (unrecognized) @{base + soff + 4:#x}")
                continue
            child = dict(ctx)
            walk_level(u, 0, len(u), child, depth + 1)
        elif t == SECTION_GUIDED:
            # GUIDed body: GUID(16) + payload (often plain when auth absent)
            if len(body) > 16:
                child = dict(ctx)
                walk_level(body[16:], 0, len(body) - 16, child, depth + 1)
        elif t == SECTION_RAW:
            # nested FV heuristic
            inner = body
            if inner[:4] == b"\xff" * 4:
                continue
            k = inner.find(b"_FVH")
            if k >= 0:
                fvs = inner[k - 0x28:]
                child = dict(ctx)
                walk_fv(fvs, 0, child, depth + 1)

def walk_fv(data, start, ctx, depth=0):
    if depth > 8 or start + 0x30 > len(data):
        return
    hdr = data[start:start + 0x30]
    if hdr[0x18:0x1c] != b"_FVH":
        return
    # sanity: header GUID should be non-trivial and length plausible
    if all(b == 0 for b in hdr[:16]) or all(b == 0xff for b in hdr[:16]):
        return
    fv_len = int.from_bytes(data[start + 0x10:start + 0x18], "little")
    if not (0x1000 <= fv_len <= 0x4000000):
        return
    ctx["fv"] = start
    hdr_len = int.from_bytes(data[start + 0x20:start + 0x22], "little") or 0x48
    f_off = start + hdr_len
    f_end = min(start + fv_len, len(data))
    print(f"[FV] {ctx['rom']} @{start:#x} len={fv_len:#x}")
    n_ffs = 0
    while f_off + 0x18 <= f_end:
        if data[f_off:f_off + 16] == b"\xff" * 16:
            f_off += 8
            continue
        ftype = data[f_off + 0x12]
        fsize = u24(data, f_off + 0x14)
        if fsize < 0x18 or f_off + fsize > f_end:
            break
        n_ffs += 1
        if n_ffs <= 4:
            print(f"  [FFS] type={ftype:#x} size={fsize:#x} @{f_off:#x}")
        if ftype in (0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x0a, 0x0b, 0xf0) \
                and fsize >= 0x1c:
            child = dict(ctx)
            inner = data[f_off + 0x18:f_off + fsize]
            walk_sections_raw(inner, 0, len(inner), child, depth + 1)
        f_off += (fsize + 7) & ~7
    print(f"  {n_ffs} FFS files walked")

def walk_sections_raw(data, base, n, ctx, depth):
    buf = data
    for t, body, soff in iter_sections(data, base, n, ctx, depth):
        if t == SECTION_UI:
            ctx["ui"] = read_ui(body, 0)
        elif t == SECTION_TE and body[:2] == b"VZ":
            name = ctx.get("ui") or f"te_{ctx.get('fv',0):#x}_{base + soff:#x}"
            fn = os.path.join(OUT, f"{ctx['rom']}_{name}.te")
            if not os.path.exists(fn):
                open(fn, "wb").write(body)
            print(f"[TE] {fn} ({len(body)} B)")
        elif t == SECTION_COMPRESSION:
            if len(body) >= 5 and body[4] == 1:
                u = lzma_decompress(body[5:])
            else:
                u = None
            if u is None:
                print(f"[compr] skip unrecognized @{base + soff + 4:#x}")
                continue
            child = dict(ctx)
            walk_sections_raw(u, 0, len(u), child, depth + 1)
        elif t == SECTION_GUIDED and len(body) > 16:
            child = dict(ctx)
            walk_sections_raw(body[16:], 0, len(body) - 16, child, depth + 1)
        elif t == SECTION_RAW:
            k = body.find(b"_FVH")
            if k >= 0:
                child = dict(ctx)
                walk_fv(body[k - 0x28:], 0, child, depth + 1)

for rom, path in ROMS.items():
    data = open(path, "rb").read()
    ctx = {"rom": rom, "ui": ""}
    hits = [m.start() for m in re.finditer(b"_FVH", data)]
    print(f"\n===== {rom}: {len(hits)} _FVH")
    for h in hits:
        walk_fv(data, h - 0x18, dict(ctx), 0)
