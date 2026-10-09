# C2: $PS1 blob builder for the runtime (mailbox, cmd 0x100C) unlock channel.
#
# Channel facts (see evidence/c2_disasm.txt, c1_loader.txt):
#   fn@0x13468 (cmd 0x100C) requires blob body[0:0x40] == {token@0xE25814 (0x20 bytes)
#   || zeros} (memcmp#2, fn@0x1450 @0x1354a). RSA tail NOT checked. Hash expectation
#   comes FROM our message (memcmp#1 vs [descriptor+4]) - any value passes.
#   The supervisor (on-die) is notified via svc 0x90/0x88 + svc 0x68 with a 0x1000-byte
#   copy from blob start (buf+0x8000) - it is the presumed registry (0xE5CBDC) filler.
#
# Blob layout produced (gasket-style 0x100-byte header, see groups_of in
# a26_donor_pairs.py for the flash-blob reference parse):
#   +0x10: "$PS1"   +0x14: total size   +0x30: 1 (version)   +0x38/0x3C: kid (copied,
#                                                                not verified on this path)
#   +0x100 body:
#     +0x00..0x40: token || zeros   (memcmp#2; token = parameter, per-boot, from cmd 0x100B)
#     +0x40: group entries {u32 type, u32 count, count x {u32 addr, u32 val}}, direct,
#            no global count word (--layout entries-direct, default) or
#            {u32 count} at +0x40 then entries at +0x48 (--layout count-then-entries,
#            for hw probing of the supervisor parser).
#
# Groups (D3-B2 VCN tail, order preserved exactly as in donor 0x201):
#   0x201: 0x0900C234->0, 0x0900C914->0, 0x0900C930->0, 0x0900CB80->0,
#          0x0900C234->1 (recommit AFTER programming), 0x0322011C->0x107FF
#   0x210: 0x03E810->6, 0x03E814->0x2544C382
# Apply with cmd 0x1033 (sequencer fn@0x20d4: 0x201 before 0x210).
import struct
import sys
import io
import os

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"..\..\evidence")
OUT = os.path.join(OUTDIR, "c2_blob_builder.txt")
BLOB_OUT = os.path.join(OUTDIR, "fv_extract", "c2_runtime_unlock_blob.bin")

TOKEN_SIZE = 0x20
GROUPS = [
    (0x201, [
        (0x0900C234, 0x00000000),  # program VCN gasket bank-12 base
        (0x0900C914, 0x00000000),
        (0x0900C930, 0x00000000),
        (0x0900CB80, 0x00000000),
        (0x0900C234, 0x00000001),  # commit AFTER programming (order!)
        (0x0322011C, 0x000107FF),
    ]),
    (0x210, [
        (0x03E810, 0x00000006),
        (0x03E814, 0x2544C382),
    ]),
]


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def build(token, layout="entries-direct"):
    assert len(token) == TOKEN_SIZE, "token must be %d bytes" % TOKEN_SIZE
    body = bytearray(token + b"\x00" * 0x20)  # memcmp#2 region: token || zeros
    if layout == "count-then-entries":
        body += struct.pack("<I", len(GROUPS))
    for gtype, pairs in GROUPS:
        body += struct.pack("<II", gtype, len(pairs))
        for a, v in pairs:
            body += struct.pack("<II", a, v)
    hdr = bytearray(b"\x00" * 0x100)
    hdr[0x10:0x14] = b"$PS1"
    struct.pack_into("<I", hdr, 0x14, 0x100 + len(body))
    struct.pack_into("<I", hdr, 0x30, 1)
    struct.pack_into("<I", hdr, 0x38, 0xFE7CEA96)  # kid 96EA (LE), copied from gasket
    struct.pack_into("<I", hdr, 0x3C, 0x2A4C9DC5)
    return bytes(hdr) + bytes(body)


def groups_of_flash(buf, addr):
    """Reference parser from a26_donor_pairs.py - flash-blob layout (count at body[0])."""
    if addr + 0x104 > len(buf) or buf[addr + 0x10:addr + 0x14] != b"$PS1":
        return None
    b = addr + 0x100
    cnt = u32(buf, b)
    if cnt > 0x40:
        return None
    out = []
    o = b + 0x40
    for i in range(cnt):
        t, c = u32(buf, o), u32(buf, o + 4)
        if c > 0x20000:
            return None
        out.append((t, c, o + 8))
        o += 8 + 8 * c
    return out


def groups_of_runtime(blob):
    """C2 runtime parse: $PS1 header, body[0:0x40] = token region, entries follow."""
    if blob[0x10:0x14] != b"$PS1":
        return None
    size = u32(blob, 0x14)
    if size != len(blob):
        return None
    o = 0x100 + 0x40
    out = []
    while o < len(blob):
        if o + 8 > len(blob):
            return None
        t, c = u32(blob, o), u32(blob, o + 4)
        if c > 0x20000 or o + 8 + 8 * c > len(blob):
            return None
        out.append((t, c, o + 8))
        o += 8 + 8 * c
    return out


def pairlist(blob, po, c):
    return [(u32(blob, po + 8 * j), u32(blob, po + 4 + 8 * j)) for j in range(c)]


def main():
    log = io.StringIO()

    def P(s=""):
        print(s)
        log.write(s + "\n")

    # token = parameter; placeholder zeros mean "fill after cmd 0x100B returned the
    # per-boot token at message-buffer+0x100"
    token = bytes.fromhex(sys.argv[1]) if len(sys.argv) > 1 else b"\x00" * TOKEN_SIZE
    layout = sys.argv[2] if len(sys.argv) > 2 else "entries-direct"
    blob = build(token, layout)

    P("== c2 runtime unlock blob ==")
    P("token      : %s%s" % (token.hex(),
                             "" if any(token) else "  (PLACEHOLDER - fill per-boot)"))
    P("layout     : %s" % layout)
    P("blob size  : %#x (header 0x100 + body %#x)" % (len(blob), len(blob) - 0x100))
    P("header     : $PS1@+0x10, size=%#x@+0x14, ver=1@+0x30, kid=%08x %08x@+0x38" %
      (u32(blob, 0x14), u32(blob, 0x38), u32(blob, 0x3C)))
    P("body[0:40] : memcmp#2 region = token||zeros")
    P("")

    gl = groups_of_runtime(blob)
    P("== parse via groups_of_runtime ==")
    assert gl is not None, "runtime parse failed"
    for t, c, po in gl:
        P("  grp %#05x count=%d" % (t, c))
        for a, v in pairlist(blob, po, c):
            P("    %#010x -> %#010x" % (a, v))
    P("")
    # cross-check groups against the requested set
    want = {t: pairs for t, pairs in GROUPS}
    got = {t: pairlist(blob, po, c) for t, c, po in gl}
    P("groups match requested set: %s" % (got == want))
    # reference flash parser note: count word sits inside the token region on this channel
    fl = groups_of_flash(blob, 0)
    P("reference groups_of (flash layout) result: %s" %
      ("count=%d (count word == token[0:4])" % u32(blob, 0x100) if fl else "None (expected: "
       "count word is part of the memcmp#2 token region on the runtime channel)"))
    P("")
    P("known open point: supervisor-side parser of the runtime blob is off-die;")
    P("if it instead expects a count at body[0] (flash layout), token[0:4] must equal")
    P("group count (2) - probe on hw with --layout count-then-entries variant if 0x1033")
    P("yields no effect.")

    os.makedirs(os.path.dirname(BLOB_OUT), exist_ok=True)
    with open(BLOB_OUT, "wb") as f:
        f.write(blob)
    P("")
    P("blob written: %s" % os.path.abspath(BLOB_OUT))
    open(OUT, "w").write(log.getvalue())
    print("saved: %s" % OUT)


if __name__ == "__main__":
    main()
