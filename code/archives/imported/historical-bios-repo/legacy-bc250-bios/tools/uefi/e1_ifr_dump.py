#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase E: HII package scanner + IFR forms decoder + SIBT strings decoder.

Scans blobs (decompressed DXE FV, inner LZMA decs, PE32s of Setup/CbsSetupDxe)
for EFI_HII_PACKAGE_LIST structures; decodes forms packages (IFR) and string
packages (SIBT). Emits per-question rows: prompt text, varstore, var offset,
defaults/options, and suppress-if/gray-out-if visibility state.
Opcode map per MdePkg UefiInternalFormRepresentation.h (EDK2 checkout).
Output: evidence/e1_setup_ifr.txt
"""
import struct, glob, os, sys

RECON = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
BLOBS = [
    ("DXE_FV_dec", RECON + r"\FV@ae0000_0b_9E21FD93_78.LZMA.dec"),
    ("Setup_PE32", RECON + r"\Setup.PE32"),
    ("CbsSetupDxe_PE32", RECON + r"\CbsSetupDxe.PE32"),
] + [("lzmadec_" + os.path.basename(p), p)
     for p in glob.glob(RECON + r"\*LZMA.dec*") + glob.glob(RECON + r"\V@*.LZMA.dec")]
OUT = r"C:\Users\OWNER\bc250-bios\evidence\e1_setup_ifr.txt"

# IFR opcode names (EDK2)
OPN = {
    0x01: "FORM", 0x02: "SUBTITLE", 0x03: "TEXT", 0x04: "IMAGE", 0x05: "ONE_OF",
    0x06: "CHECKBOX", 0x07: "NUMERIC", 0x08: "PASSWORD", 0x09: "ONE_OF_OPTION",
    0x0A: "SUPPRESS_IF", 0x0B: "LOCKED", 0x0C: "ACTION", 0x0D: "RESET_BUTTON",
    0x0E: "FORM_SET", 0x0F: "REF", 0x10: "NO_SUBMIT_IF", 0x11: "INCONSISTENT_IF",
    0x19: "GRAY_OUT_IF", 0x1A: "DATE", 0x1B: "TIME", 0x1C: "STRING",
    0x1D: "REFRESH", 0x1E: "DISABLE_IF", 0x23: "ORDERED_LIST",
    0x24: "VARSTORE", 0x25: "VARSTORE_NAME_VALUE", 0x26: "VARSTORE_EFI",
    0x27: "VARSTORE_DEVICE", 0x28: "VERSION", 0x29: "END",
    0x5B: "DEFAULT", 0x5C: "DEFAULTSTORE", 0x5D: "FORM_MAP", 0x5F: "GUID",
}
NUMSZ = {0x00: 1, 0x01: 2, 0x02: 4, 0x03: 8}  # EFI_IFR_NUMERIC_SIZE flags

def fmtguid(g):
    return "%08X-%04X-%04X-%s-%s" % (struct.unpack("<I", g[:4])[0], struct.unpack("<H", g[4:6])[0],
                                    struct.unpack("<H", g[6:8])[0], g[8:10].hex().upper(), g[10:16].hex().upper())


def parse_sibt(pkg):
    """strings package bytes -> list of (string_id, text)."""
    hdr, = struct.unpack_from("<I", pkg, 0)
    if (hdr >> 24) != 0x04:
        return None
    if len(pkg) < 16:
        return []
    hdrsize, infooff = struct.unpack_from("<II", pkg, 4)
    if not (0x14 <= hdrsize <= len(pkg)) or not (hdrsize <= infooff < len(pkg)):
        return None
    lang = pkg[0x30:hdrsize].split(b"\x00")[0].decode("latin1", "ignore")
    out = []
    sid = 1
    p = infooff
    end = len(pkg)
    while p < end:
        t = pkg[p]
        if t == 0x00:  # SIBT_END
            break
        elif t in (0x10, 0x11):  # SCSU
            p += 2 if t == 0x11 else 1
            e = pkg.find(b"\x00", p)
            out.append((sid, pkg[p:e].decode("cp437", "replace")))
            sid += 1
            p = e + 1
        elif t == 0x12 or t == 0x13:  # STRINGS_SCSU
            p += 1
            cnt, = struct.unpack_from("<H", pkg, p); p += 2
            if t == 0x13:
                p += 1
            for _ in range(cnt):
                e = pkg.find(b"\x00", p)
                if e < 0:
                    return out
                out.append((sid, pkg[p:e].decode("cp437", "replace")))
                sid += 1
                p = e + 1
        elif t in (0x14, 0x15):  # STRING_UCS2
            p += 2 if t == 0x15 else 1
            e = p
            while e + 1 < end and (pkg[e] or pkg[e + 1]):
                e += 2
            out.append((sid, pkg[p:e + 2].decode("utf-16-le", "replace")))
            sid += 1
            p = e + 2
        elif t in (0x16, 0x17):  # STRINGS_UCS2
            p += 1
            cnt, = struct.unpack_from("<H", pkg, p); p += 2
            if t == 0x17:
                p += 1
            for _ in range(cnt):
                e = p
                while e + 1 < end and (pkg[e] or pkg[e + 1]):
                    e += 2
                out.append((sid, pkg[p:e + 2].decode("utf-16-le", "replace")))
                sid += 1
                p = e + 2
        elif t == 0x20:  # DUPLICATE
            src, = struct.unpack_from("<H", pkg, p + 1)
            out.append((sid, next((s for i, s in out if i == src), "=dup%d" % src)))
            sid += 1
            p += 3
        elif t == 0x21:  # SKIP2
            cnt, = struct.unpack_from("<H", pkg, p + 1)
            sid += cnt
            p += 3
        elif t == 0x22:  # SKIP1
            sid += pkg[p + 1]
            p += 2
        elif t in (0x30, 0x31, 0x32):  # EXT
            if t == 0x30:
                ln = pkg[p + 2]; p += 3
            elif t == 0x31:
                ln, = struct.unpack_from("<H", pkg, p + 2); p += 4
            else:
                ln, = struct.unpack_from("<I", pkg, p + 2); p += 6
            p = p - (3, 4, 6)[(0x30, 0x31, 0x32).index(t)] + ln
        elif t == 0x40:  # FONT
            ln, = struct.unpack_from("<H", pkg, p + 2)
            p += ln
        else:
            break
    return lang, out


def find_packages(blob):
    """-> list of (offset, type, length). Scan u32 at every offset:
    v>>24 in 1..8, len plausible, and either forms-IFR validates (type 7) or
    strings SIBT validates (type 2); other types accepted only inside a
    validated consecutive run (not needed here)."""
    hits = []
    n = len(blob)
    for i in range(0, n - 4):
        v, = struct.unpack_from("<I", blob, i)
        typ = v >> 24
        ln = v & 0xFFFFFF
        if typ == 0x02 and 0x20 <= ln <= 0x400000 and i + 4 + ln <= n:
            ifr = blob[i + 4:i + 4 + ln]
            if ifr[0] == 0x0E and ifr[1] >= 0x26:
                hits.append((i, typ, ln))
        elif typ == 0x04 and 0x20 <= ln <= 0x800000 and i + 4 + ln <= n:
            r = parse_sibt(blob[i:i + 4 + ln])
            if r and isinstance(r, tuple) and r[1]:
                hits.append((i, typ, ln))
    return hits


OPTVAL_SZ = {0x00: 1, 0x01: 1, 0x02: 2, 0x03: 4, 0x04: 8, 0x05: 1, 0x06: 8, 0x07: 8, 0x08: 2, 0x09: 2}


def decode_ifr(ifr, strings, lines):
    """ifr: forms package body (after 4-byte package header).
    Record header: op u8; len:7 bits; scope:1 bit. Scope'd records are closed by END."""
    smap = dict(strings)
    varstores = {}
    p = 0
    cur_form = "?"
    scope_stack = []  # 'S' suppress / 'G' gray / 'X' other scope / 'Q' question
    out = lines
    while p + 2 <= len(ifr):
        op = ifr[p]
        ln = ifr[p + 1] & 0x7F
        scope = ifr[p + 1] >> 7
        if ln < 2 or p + ln > len(ifr):
            out.append("  !! bad record at +%#x op=%#x raw=%#x" % (p, op, ifr[p + 1]))
            break
        body = ifr[p + 2:p + ln]
        hid = any(x == "S" for x in scope_stack)
        grayed = any(x == "G" for x in scope_stack)
        if op == 0x0E:  # FORM_SET
            g = body[:16]
            title, help_ = struct.unpack_from("<HH", body, 16)
            out.append("  FORM_SET guid=%s title='%s' help='%s'" % (
                fmtguid(g), smap.get(title, "#%d" % title), smap.get(help_, "#%d" % help_)))
        elif op == 0x01:  # FORM {FormId u16, FormTitle u16}
            formid, prompt = struct.unpack_from("<HH", body, 0)
            cur_form = smap.get(prompt, "#%d" % prompt)
            out.append("  FORM id=%#06x title='%s'%s" % (formid, cur_form, " [HIDDEN]" if hid else ""))
        elif op in (0x24, 0x26):  # VARSTORE / VARSTORE_EFI
            g = body[:16]
            vid, size = struct.unpack_from("<HH", body, 16)
            name_u = body[20:].decode("utf-16-le", "ignore").rstrip("\x00")
            name_a = body[20:].split(b"\x00")[0].decode("latin1", "ignore")
            name = name_a if len(name_a) >= 3 and name_a.isascii() and all(32 <= ord(c) < 127 for c in name_a) else name_u
            varstores[vid] = (name or fmtguid(g), size)
            out.append("  VARSTORE id=%#x name=%s guid=%s size=%#x" % (vid, name, fmtguid(g), size))
        elif op in (0x05, 0x06, 0x07, 0x08, 0x1C, 0x23):  # questions
            prompt, help_, qid, vid, voff, flags = struct.unpack_from("<HHHHHB", body, 0)
            vs, vsize = varstores.get(vid, ("?", 0))
            tag = ("HIDDEN " if hid else "") + ("GRAY " if grayed else "")
            out.append("  %s%s @form='%s' qid=%#x var=%s+%#x flags=%#x '%s'" % (
                tag, OPN.get(op, hex(op)), cur_form, qid, vs, voff, flags,
                smap.get(prompt, "#%d" % prompt)))
            if op == 0x07 and len(body) >= 12:  # NUMERIC bounds
                nf = NUMSZ.get(body[11] & 0x03, 1)
                q = 12
                vals = []
                for _ in range(3):
                    if len(body) >= q + nf:
                        vals.append(int.from_bytes(body[q:q + nf], "little"))
                        q += nf
                if len(vals) == 3:
                    out.append("     NUMERIC min=%d max=%d step=%d" % tuple(vals))
        elif op == 0x09:  # ONE_OF_OPTION {Option u16, Flags u8, Type u8, Value}
            if len(body) >= 4:
                opt, oflags, otyp = struct.unpack_from("<HBB", body, 0)
                vsz = OPTVAL_SZ.get(otyp, 0)
                val = int.from_bytes(body[4:4 + vsz], "little") if vsz else None
                out.append("     OPTION '%s' = %s (type=%#x flags=%#x)" % (
                    smap.get(opt, "#%d" % opt),
                    ("%#x" % val) if val is not None else body[4:].hex(), otyp, oflags))
        elif op == 0x5B:  # DEFAULT {DefaultId u16, Type u8, Value}
            if len(body) >= 3:
                did, dtyp = struct.unpack_from("<HB", body, 0)
                out.append("     DEFAULT id=%#x type=%#x value=%s" % (
                    did, dtyp, body[3:].hex()))
        elif op in (0x0A, 0x19, 0x1E):  # SUPPRESS_IF / GRAY_OUT_IF / DISABLE_IF
            out.append("  %s [+%#x] expr=%s" % (OPN[op], p, body.hex()))
            if scope:
                scope_stack.append("S" if op == 0x0A else ("G" if op == 0x19 else "X"))
        elif op == 0x03 and len(body) >= 4:  # TEXT {Prompt, Help, ...}
            prompt, help_ = struct.unpack_from("<HH", body, 0)
            txt = smap.get(prompt, "")
            if txt:
                out.append("  %sTEXT '%s'" % ("HIDDEN " if hid else "", txt))
        elif op == 0x0F and len(body) >= 13:  # REF {QHeader(11), FormId u16, ...}
            prompt, help_, qid, vid, voff, flags, fform = struct.unpack_from("<HHHHHBH", body, 0)
            out.append("  %sREF @form=%#x '%s'" % ("HIDDEN " if hid else "", fform,
                                                  smap.get(prompt, "#%d" % prompt)))
        elif op == 0x29:  # END closes innermost scope
            if scope_stack:
                scope_stack.pop()
        if scope and op != 0x29 and op not in (0x0A, 0x19, 0x1E):
            scope_stack.append("Q")
        p += ln
    return out


def main():
    out = ["# HII package scan: forms (IFR) and strings (SIBT)"]
    for label, path in BLOBS:
        if label == "DXE_FV_dec" and not os.path.exists(path):
            continue
        try:
            blob = open(path, "rb").read()
        except OSError as e:
            out.append("!! %s: %s" % (label, e))
            continue
        pkgs = find_packages(blob)
        if not pkgs:
            continue
        out.append("=" * 90)
        out.append("### blob %s (%d bytes): %d packages" % (label, len(blob), len(pkgs)))
        # group into consecutive package-list runs
        for (off, typ, ln) in pkgs:
            out.append("- package type=%d @%#x len=%#x" % (typ, off, ln))
        for (off, typ, ln) in pkgs:
            if typ == 0x04:
                lang, strs = parse_sibt(blob[off:off + 4 + ln])
                out.append("--- strings package @%#x lang=%s strings=%d" % (off, lang, len(strs)))
                # save full string table to a separate file
                sfn = OUT.replace(".txt", "_strings_%x.txt" % off)
                open(sfn, "w", encoding="utf-8").write(
                    "\n".join("%d\t%s" % (i, s) for i, s in strs) + "\n")
                out.append("    string table -> %s" % sfn)
        for (off, typ, ln) in pkgs:
            if typ != 0x02:
                continue
            # pick strings package maximizing prompt coverage, tie-break by proximity
            best = None
            for c in pkgs:
                if c[1] != 0x04:
                    continue
                strs = parse_sibt(blob[c[0]:c[0] + 4 + c[2]])[1]
                cov = sum(1 for q in range(0, min(ln, 0x4000), 2)
                          if blob[off + 4 + q] == 0x05 and struct.unpack_from("<H", blob, off + 6 + q)[0] < len(strs))
                prox = abs(c[0] - off)
                if best is None or (cov, -prox) > best[0]:
                    best = ((cov, -prox), c, strs)
            if best:
                _, c, strs = best
                out.append("--- forms package @%#x len=%#x (strings pkg @%#x, %d strings)" % (off, ln, c[0], len(strs)))
            else:
                strs = []
                out.append("--- forms package @%#x len=%#x (no strings pkg)" % (off, ln))
            try:
                decode_ifr(blob[off + 4:off + 4 + ln], strs, out)
            except Exception as e:
                out.append("  !! decode error: %r" % e)
    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("written:", OUT, len(out), "lines")


if __name__ == "__main__":
    main()
