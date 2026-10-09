#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase G1: full inventory of ALL Setup forms across ALL formsets.

Scans every PE32/TE body in the extracted FFS dump (fv_extract) for HII
package lists; decodes every forms package (IFR) with full per-question
rows: type, varstore+offset, prompt, bounds, options, defaults, and
visibility (SUPPRESS_IF / GRAY_OUT_IF nesting). Formsets are deduped by
GUID; module attribution = the FFS file whose body contains the package.
Output: evidence/g1_forms_inventory.txt
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from e1_ifr_dump import parse_sibt, find_packages, fmtguid, OPN, NUMSZ, OPTVAL_SZ  # noqa: E402

DUMP = r"C:\Users\OWNER\bc250-bios\evidence\fv_extract\BC250_3.00.ROM.dump"
OUT = r"C:\Users\OWNER\bc250-bios\evidence\g1_forms_inventory.txt"

SECTION_NAMES = {
    "PE32 image section", "TE image section", "UI section", "Version section",
    "Raw section", "PEI dependency section", "DXE dependency section",
    "Compressed section", "Guided section", "Freeform subtype section",
    "Volume image section", "Firmware volume image section", "Depex section",
    "Section raw", "Raw file section", "Section GUIDed", "Discardable section",
}


def modname_of(root):
    """walk up from a section dir to the owning FFS module dir name."""
    p = root
    while len(p) > len(DUMP):
        base = os.path.basename(p)
        if re.match(r"^\d+ ", base) and base not in SECTION_NAMES:
            return re.match(r"^\d+ (.+)$", base).group(1)
        p = os.path.dirname(p)
    return None


def iter_bodies():
    """yield (module_name, relpath, bytes) for every body.bin in the dump tree."""
    for root, dirs, files in os.walk(DUMP):
        for f in files:
            if f != "body.bin":
                continue
            mod = modname_of(root)
            if mod is None or mod in ("Padding", "info.txt"):
                continue
            with open(os.path.join(root, f), "rb") as fh:
                data = fh.read()
            if len(data) < 64:
                continue
            yield mod, os.path.relpath(root, DUMP), data


# blobs whose containing module is compressed inside the FV: scan the
# decompressed DXE FV itself; formsets not found in any uncompressed module
# body get attributed to "<compressed module in DXE FV>".
EXTRA_BLOBS = [
    ("DXE_FV(compressed)", r"C:\Users\OWNER\bc250-bios\evidence\fv_extract\STOCK_FV.dec"),
]


def decode_struct(ifr, smap):
    """Structured IFR decode -> (varstores, forms list)."""
    varstores = {}
    forms = []
    cur = None
    q = None
    scope = []          # stack: 'S'=suppress 'G'=gray 'X'=other 'Q'=question
    p = 0
    while p + 2 <= len(ifr):
        op = ifr[p]
        ln = ifr[p + 1] & 0x7F
        sc = ifr[p + 1] >> 7
        if ln < 2 or p + ln > len(ifr):
            break
        body = ifr[p + 2:p + ln]
        hid = "S" in scope
        gry = "G" in scope
        if op == 0x0E:
            g = body[:16]
            t, h = struct.unpack_from("<HH", body, 16)
            forms_meta = {"guid": fmtguid(g), "title": smap.get(t, "#%d" % t)}
            forms.append(("META", forms_meta))
        elif op == 0x01:
            fid, prompt = struct.unpack_from("<HH", body, 0)
            cur = {"id": fid, "title": smap.get(prompt, "#%d" % prompt),
                   "hidden": hid, "questions": []}
            forms.append(("FORM", cur))
        elif op in (0x24, 0x26):
            g = body[:16]
            vid, size = struct.unpack_from("<HH", body, 16)
            nu = body[20:].decode("utf-16-le", "ignore").rstrip("\x00")
            na = body[20:].split(b"\x00")[0].decode("latin1", "ignore")
            nm = na if len(na) >= 3 and na.isascii() and all(32 <= ord(c) < 127 for c in na) else nu
            varstores[vid] = (nm or fmtguid(g), size, fmtguid(g))
        elif op in (0x05, 0x06, 0x07, 0x08, 0x1C, 0x23):
            prompt, help_, qid, vid, voff, flags = struct.unpack_from("<HHHHHB", body, 0)
            q = {"op": OPN.get(op, hex(op)), "qid": qid, "vid": vid, "voff": voff,
                 "prompt": smap.get(prompt, "#%d" % prompt),
                 "help": smap.get(help_, "#%d" % help_) if len(body) >= 6 else "",
                 "hidden": hid, "gray": gry, "opts": [], "def": None, "bounds": None}
            if op == 0x07 and len(body) >= 12:
                nf = NUMSZ.get(body[11] & 0x03, 1)
                r = 12
                vals = []
                for _ in range(3):
                    if len(body) >= r + nf:
                        vals.append(int.from_bytes(body[r:r + nf], "little"))
                        r += nf
                if len(vals) == 3:
                    q["bounds"] = tuple(vals)
            if cur is not None:
                cur["questions"].append(q)
        elif op == 0x09:
            if q is not None and len(body) >= 4:
                opt, ofl, otyp = struct.unpack_from("<HBB", body, 0)
                vsz = OPTVAL_SZ.get(otyp, 0)
                val = int.from_bytes(body[4:4 + vsz], "little") if vsz else None
                q["opts"].append((smap.get(opt, "#%d" % opt), val))
        elif op == 0x5B:
            if q is not None and len(body) >= 3:
                q["def"] = body[3:].hex()
        elif op == 0x0F and len(body) >= 13:
            prompt, help_, qid, vid, voff, flags, fform = struct.unpack_from("<HHHHHBH", body, 0)
            if cur is not None:
                cur["questions"].append(
                    {"op": "REF", "qid": qid, "vid": vid, "voff": voff,
                     "prompt": smap.get(prompt, "#%d" % prompt), "target": fform,
                     "hidden": hid, "gray": gry, "opts": [], "def": None, "bounds": None})
        elif op in (0x0A, 0x19, 0x1E):
            if sc:
                scope.append("S" if op == 0x0A else ("G" if op == 0x19 else "X"))
        elif op == 0x29:
            if scope:
                scope.pop()
        if sc and op != 0x29 and op not in (0x0A, 0x19, 0x1E):
            scope.append("Q")
        p += ln
    return varstores, forms


def main():
    out = ["# Phase G1: full forms inventory (all formsets, all modules)"]
    seen = {}   # formset guid -> (module, varstores, forms)
    srcs = list(iter_bodies())
    for (m, path) in EXTRA_BLOBS:
        if os.path.exists(path):
            srcs.append((m, path, open(path, "rb").read()))
    for mod, rel, data in srcs:
        pkgs = find_packages(data)
        forms_pkgs = [(o, l) for (o, t, l) in pkgs if t == 0x02]
        if not forms_pkgs:
            continue
        # best strings package in same module
        str_pkgs = [(o, l) for (o, t, l) in pkgs if t == 0x04]
        for (off, ln) in forms_pkgs:
            ifr = data[off + 4:off + 4 + ln]
            g = fmtguid(ifr[2:18]) if ifr[0] == 0x0E else "?"
            # choose strings pkg maximizing coverage
            best = None
            for (so, sl) in str_pkgs:
                strs = parse_sibt(data[so:so + 4 + sl])
                if not strs or not isinstance(strs, tuple):
                    continue
                smap = dict(strs[1])
                cov = sum(1 for qq in range(0, min(ln, 0x4000), 2)
                          if ifr[qq] == 0x05 and struct.unpack_from("<H", ifr, qq + 2)[0] < len(smap))
                if best is None or cov > best[0]:
                    best = (cov, smap)
            smap = best[1] if best else {}
            varstores, forms = decode_struct(ifr, smap)
            meta = next((f for t, f in forms if t == "META"), None)
            key = (meta or {}).get("guid", "?")
            if key in seen:  # dedup identical formsets across copies
                continue
            seen[key] = (mod, rel, off, varstores, forms)

    nq_total = nhid_total = nform_total = 0
    for guid, (mod, rel, off, varstores, forms) in sorted(seen.items(), key=lambda kv: kv[1][0]):
        meta = next((f for t, f in forms if t == "META"), None) or {}
        fl = [f for t, f in forms if t == "FORM"]
        nq = sum(len(f["questions"]) for f in fl)
        nh = sum(1 for f in fl for q in f["questions"] if q["hidden"])
        ng = sum(1 for f in fl for q in f["questions"] if q["gray"])
        nform_total += len(fl)
        nq_total += nq
        nhid_total += nh
        out.append("=" * 100)
        out.append("FORMSET %s  '%s'  module=%s  pkg@%#x" % (
            guid, meta.get("title", "?"), mod, off))
        out.append("  stats: forms=%d questions=%d hidden=%d grayed=%d" % (len(fl), nq, nh, ng))
        for vid, (nm, size, vg) in sorted(varstores.items()):
            out.append("  VARSTORE id=%#x name=%s guid=%s size=%#x" % (vid, nm, vg, size))
        for f in fl:
            out.append("  FORM id=%#06x '%s'%s" % (
                f["id"], f["title"], " [HIDDEN]" if f["hidden"] else ""))
            for q in f["questions"]:
                vs = varstores.get(q["vid"], ("?", 0, "?"))
                tag = ("HIDDEN " if q["hidden"] else "") + ("GRAY " if q["gray"] else "")
                line = "    %s%s qid=%#06x %s+%#06x  '%s'" % (
                    tag, q["op"], q["qid"], vs[0], q["voff"], q["prompt"])
                if q["bounds"]:
                    line += "  bounds=%s" % (q["bounds"],)
                if q["def"] is not None:
                    line += "  default=%s" % q["def"]
                if q["op"] == "REF":
                    line = "    %sREF qid=%#06x -> form %#06x  '%s'" % (
                        tag, q["qid"], q["target"], q["prompt"])
                out.append(line)
                for (oname, oval) in q["opts"][:24]:
                    out.append("        opt '%s' = %s" % (oname, ("%#x" % oval) if oval is not None else "?"))
                if len(q["opts"]) > 24:
                    out.append("        ... %d more options" % (len(q["opts"]) - 24))
    out.append("=" * 100)
    out.append("# TOTAL: formsets=%d forms=%d questions=%d hidden=%d" % (
        len(seen), nform_total, nq_total, nhid_total))
    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("written:", OUT)
    print("formsets=%d forms=%d questions=%d hidden=%d" % (len(seen), nform_total, nq_total, nhid_total))


if __name__ == "__main__":
    main()
