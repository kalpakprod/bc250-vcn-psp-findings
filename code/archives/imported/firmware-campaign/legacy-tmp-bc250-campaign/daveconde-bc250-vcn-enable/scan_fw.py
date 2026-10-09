#!/usr/bin/env python3
"""
scan_fw.py -- LOCAL static scan of a BC250 SMU SRAM dump (no hardware, no
Ghidra). Answers: which code -- and therefore which Q3 message, if any --
reaches the fw's domain power-up machinery?

    0x23B14   FUN_00023b14  the dom sequencer (rail/gate protocol)
    0x246xx   the internal power-up wrapper (the 2026-08-25 dump found FOUR
              calls to 0x23B14 clustered at 0x246C3/0x246EE/0x2475E/0x2477A).
              NOTE: 0x246C3 is a CALL SITE inside it, not its entry -- the
              old "dom7 caller @0x246c3" label was a call site all along
              (unaligned labels cannot be call targets).

CALIBRATION GATE (runs first): counts call sites to 0xFE4/0xFA8 (500+
documented in the project notes) and 0x235C8/0x23744. If the fe4/fa8
controls show ~0, this fw reaches functions INDIRECTLY (l32r + callx) and
every direct-call NEGATIVE is blind -- the tool says so instead of letting
you trust a silent scan. Noise expectation is printed per target (~0.05
false hits per target in a 256 KB image: 0 hits is a REAL zero).

THE HUNT has two prongs:
  1. direct callers of 0x23B14 (attributed with BOTH the Q3 handler table
     and the known-function boundaries -- the first version mislabeled hits
     inside internal functions as 'msg 0x8f'; fixed);
  2. direct calls INTO the wrapper region 0x24600..0x24800 -- finds the
     wrapper's callers whatever its entry address is. A message handler in
     that list is the sendable vehicle.

Also: literal/pointer xrefs (l32r pools), including any dword pointing
into the wrapper region, hex context around every hit, and handler
attribution down to function granularity.

Usage:
    python3 scan_fw.py smu_sram.bin
    python3 scan_fw.py smu_sram.bin -t 0x23b14
    python3 scan_fw.py smu_sram.bin --literal 0x0116d054
    python3 scan_fw.py smu_sram.bin --target-range 0x24600 0x24800
"""
import argparse
import bisect
import struct
import sys

HANDLER_TABLE = 0x746C
HANDLER_COUNT = 0xC0
STRIDE = 8

# Known function boundaries (from the project's fw decode). 0x246C3 is
# deliberately ABSENT: it is a call site, not a function entry.
KNOWN_FNS = {
    0x00FE4: "fn_fe4 (set mailbox response)",
    0x00FA8: "fn_fa8 (mark message complete)",
    0x01B3A8: "TestMessage",
    0x023370: "fn @0x23370 (clock-program region, internal)",
    0x02362C: "soc_clk_program_slot",
    0x0235C8: "FUN_000235c8 (fw window store)",
    0x023744: "FUN_00023744 (slot-clock program -- the fire's fn)",
    0x023B14: "FUN_00023b14 (DOMAIN POWER-UP sequencer)",
    0x02A018: "fn_2a018 (bridge-gate SMN read leaf)",
}

CONTROL_TARGETS = [0x0FE4, 0x0FA8, 0x235C8, 0x23744]
CONTROL_NOTES = {
    0x0FE4: "expect 500+ (project notes: fe4/fa8 idiom at 500+ sites)",
    0x0FA8: "expect 500+ (project notes)",
    0x235C8: "project notes claim 30+ (from the robin_5 analysis)",
    0x23744: "the fire's fn -- the fw's own teardown calls it",
}
HUNT_TARGETS = [0x23B14]
WRAPPER_RANGE = (0x24600, 0x24800)      # the internal power-up wrapper region
FAR_WINDOW = 0x600                      # beyond this, a hit is not in the
                                        # boundary's own function

DEFAULT_LITERALS = [0x0116D054, 0x0116D0F8, 0x0116D17C, 0x0116D184,
                    0x0116D190, 0x010FFE00, 0x0246C3, 0x023B14]


def parse_handlers(data, base, count):
    out = {}
    for m in range(1, count + 1):
        off = base + (m - 1) * STRIDE
        if off + STRIDE > len(data):
            break
        lo, hi = struct.unpack_from("<II", data, off)
        if lo or hi:
            out[m] = (lo, hi)
    return out


def decode_call(data, pos):
    """(kind, target) if the 3 bytes at pos decode as CALL4/8/12, else None.

    Word = (off18 << 6) | (s << 4) | 5, target = ((pc+4)&~3) + off*4.
    Calibrated against Robin1 (enable_vcn.py enc_call8 -- the encoding the
    working Discord sequence uses)."""
    if pos + 3 > len(data):
        return None
    w = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
    if (w & 0xF) != 0x5:
        return None
    s = (w >> 4) & 0x3
    if s == 0:
        return None
    off = (w >> 6) & 0x3FFFF
    if off & 0x20000:
        off -= 0x40000
    target = ((pos + 4) & ~3) + (off << 2)
    return {1: "call4", 2: "call8", 3: "call12"}[s], target


class Attribution:
    """Function-level attribution using handler-table + known-fn boundaries.
    Model: functions are contiguous; a hit belongs to the highest boundary
    at or below it, unless the distance exceeds FAR_WINDOW (then it is in
    an unknown function in between)."""

    def __init__(self, handlers, known):
        self.bounds = {}
        for m, (lo, hi) in handlers.items():
            self.bounds.setdefault(lo, f"msg 0x{m:02x} handler")
        for a, n in known.items():
            self.bounds.setdefault(a, n)
        self.addrs = sorted(self.bounds)

    def owner(self, pc):
        i = bisect.bisect_right(self.addrs, pc) - 1
        if i < 0:
            return "early fw (below all known boundaries)"
        a = self.addrs[i]
        d = pc - a
        label = self.bounds[a]
        if d > FAR_WINDOW:
            return (f"UNKNOWN fn past {label} (+0x{d:x} -- separate "
                    f"function, entry not in our tables)")
        return f"inside {label} 0x{a:05x} (+0x{d:x})"

    def owning_handler(self, pc):
        """(msg_id, handler_addr) if pc is confidently inside a table
        handler's body, else None."""
        i = bisect.bisect_right(self.addrs, pc) - 1
        if i < 0:
            return None
        a = self.addrs[i]
        if pc - a > FAR_WINDOW:
            return None
        label = self.bounds[a]
        if label.startswith("msg ") and "handler" in label:
            try:
                return int(label.split()[1], 16), a
            except ValueError:
                return None
        return None


def hex_ctx(data, pos, before=6, after=9):
    lo = max(0, pos - before)
    hi = min(len(data), pos + after)
    return data[lo:hi].hex()


def main():
    ap = argparse.ArgumentParser(
        description="xref scan of a BC250 SMU SRAM dump (local, read-only)")
    ap.add_argument("dump", help="SRAM dump file (smu.dump_sram() output)")
    ap.add_argument("-t", "--target", type=lambda s: int(s, 0), action="append",
                    help="extra call-xref target address (repeatable)")
    ap.add_argument("--literal", type=lambda s: int(s, 0), action="append",
                    help="extra literal/pointer xref value (repeatable)")
    ap.add_argument("--target-range", nargs=2,
                    type=lambda s: int(s, 0), metavar=("START", "END"),
                    help="scan for calls whose TARGET lies in this range")
    ap.add_argument("--table-base", type=lambda s: int(s, 0),
                    default=HANDLER_TABLE)
    ap.add_argument("--table-count", type=lambda s: int(s, 0),
                    default=HANDLER_COUNT)
    args = ap.parse_args()

    data = open(args.dump, "rb").read()
    print(f"[*] {args.dump}: {len(data)} bytes")

    handlers = parse_handlers(data, args.table_base, args.table_count)
    tm = handlers.get(1, (0, 0))[0]
    if tm == 0x1B3A8:
        print(f"[*] handler table @0x{args.table_base:x}: {len(handlers)} "
              f"entries, msg 0x01 == TestMessage (0x1b3a8) -- table OK")
    else:
        print(f"[!] handler table not found at 0x{args.table_base:x} "
              f"(msg 0x01 -> 0x{tm:05x}); attribution degraded")
        handlers = {}
    attr = Attribution(handlers, KNOWN_FNS)

    # single pass over the image
    calls = {}          # target -> [(pos, kind)]
    rng_hits = []       # [(pos, kind, target)] for the target-range scan
    want = set(CONTROL_TARGETS) | set(HUNT_TARGETS) | set(args.target or ())
    for pos in range(len(data) - 2):
        c = decode_call(data, pos)
        if not c:
            continue
        kind, t = c
        if t in want:
            calls.setdefault(t, []).append((pos, kind))
        if args.target_range and args.target_range[0] <= t <= args.target_range[1]:
            rng_hits.append((pos, kind, t))

    positions = max(0, len(data) - 2)
    noise = positions * (1 / 16) * (3 / 4) / (1 << 18)
    print(f"[*] decode noise expectation: ~{noise:.2f} false hit(s) per "
          f"target in this image size -- a 0 IS a real zero\n")

    # ---- calibration gate ----
    print("== CALIBRATION (controls) -- run before trusting anything ==")
    fe4 = len(calls.get(0x0FE4, []))
    fa8 = len(calls.get(0x0FA8, []))
    validated = (fe4 + fa8) >= 20
    for t in CONTROL_TARGETS:
        n = len(calls.get(t, []))
        print(f"0x{t:05x} {KNOWN_FNS.get(t, '')}: {n} call site(s)"
              f"   [{CONTROL_NOTES[t]}]")
    if validated:
        print(f"-> VALIDATED: direct calls exist ({fe4}+{fa8} fe4/fa8 "
              f"sites) -- direct-call negatives below are meaningful.")
    else:
        print("-> NOT VALIDATED: ~0 fe4/fa8 sites means this fw reaches "
              "functions INDIRECTLY (l32r+callx); every direct-call "
              "negative below is BLIND. Only literal/pointer xrefs remain "
              "trustworthy -- and the 500+-site claim needs revisiting.")

    # ---- the hunt: callers of the domain power-up ----
    print("\n== THE HUNT: direct callers of FUN_00023b14 (domain power-up) ==")
    hunt_msgs = {}
    for t in HUNT_TARGETS + (args.target or []):
        if t in CONTROL_TARGETS:
            continue
        hits = calls.get(t, [])
        name = KNOWN_FNS.get(t, "")
        print(f"\n0x{t:05x} {name}: {len(hits)} call site(s)")
        unknowns = []
        for pos, kind in hits:
            o = attr.owner(pos)
            print(f"    {kind} @0x{pos:05x} ctx[{hex_ctx(data, pos)}]"
                  f"  -- {o}")
            h = attr.owning_handler(pos)
            if h:
                hunt_msgs.setdefault(h[0], []).append(pos)
            if o.startswith("UNKNOWN"):
                unknowns.append(pos)
        if unknowns:
            lo, hi = min(unknowns), max(unknowns)
            print(f"    -> {len(unknowns)} hit(s) cluster in "
                  f"0x{lo:05x}-0x{hi:05x}: one UNKNOWN function -- the "
                  f"internal power-up wrapper (entry not in any table).")
        if t == 0x23B14 and hunt_msgs:
            print(f"    ==> SENDABLE: msg "
                  f"{', '.join(f'0x{m:02x}' for m in sorted(hunt_msgs))} "
                  f"handler(s) call the power-up DIRECTLY.")
        elif t == 0x23B14:
            print("    ==> NO message handler calls it directly "
                  "(internal-only callers).")

    # ---- wrapper-region callers (the second prong) ----
    print(f"\n== WRAPPER CALLERS: direct calls INTO "
          f"0x{WRAPPER_RANGE[0]:05x}..0x{WRAPPER_RANGE[1]:05x} ==")
    print("    (the internal power-up wrapper lives here -- entry address "
          "unknown; whoever calls into this region reaches it)")
    wrap_hits = rng_hits
    if not args.target_range:
        for pos in range(len(data) - 2):
            c = decode_call(data, pos)
            if c and WRAPPER_RANGE[0] <= c[1] <= WRAPPER_RANGE[1]:
                wrap_hits.append((pos, c[0], c[1]))
    if wrap_hits:
        wrap_msgs = {}
        for pos, kind, t in wrap_hits:
            o = attr.owner(pos)
            print(f"    {kind} @0x{pos:05x} -> 0x{t:05x}  -- {o}")
            h = attr.owning_handler(pos)
            if h:
                wrap_msgs.setdefault(h[0], []).append(pos)
        if wrap_msgs:
            print(f"    ==> SENDABLE: msg "
                  f"{', '.join(f'0x{m:02x}' for m in sorted(wrap_msgs))} "
                  f"handler(s) call INTO the wrapper region -- prime "
                  f"vehicle candidates (decode those handlers first).")
        else:
            print("    -> no message handler calls into the wrapper "
                  "region: it is internal-only (a task/ISR).")
    else:
        print("    -> no direct calls into the wrapper region at all "
              "(reached indirectly, or entered by fall-through/branch).")

    # ---- literal xrefs ----
    print("\n== LITERAL xrefs (l32r pools / pointer tables) ==")
    lits = DEFAULT_LITERALS + (args.literal or [])
    tbl_lo = args.table_base
    tbl_hi = args.table_base + args.table_count * STRIDE
    for v in lits:
        hits = [off for off in range(0, len(data) - 3, 4)
                if struct.unpack_from("<I", data, off)[0] == v]
        print(f"\n0x{v:08x}: {len(hits)} dword reference(s)")
        for off in hits:
            where = ("(inside the handler table itself)"
                     if tbl_lo <= off < tbl_hi else attr.owner(off))
            print(f"    dword @0x{off:05x}  -- {where}")
    # any pointer INTO the wrapper region (l32r-loaded entry addresses)
    wrap_ptrs = []
    for off in range(0, len(data) - 3, 4):
        v = struct.unpack_from("<I", data, off)[0]
        if WRAPPER_RANGE[0] <= v <= WRAPPER_RANGE[1] and not (tbl_lo <= off < tbl_hi):
            wrap_ptrs.append((off, v))
    if wrap_ptrs:
        print(f"\npointers into the wrapper region "
              f"0x{WRAPPER_RANGE[0]:05x}..0x{WRAPPER_RANGE[1]:05x}:")
        for off, v in wrap_ptrs:
            print(f"    dword @0x{off:05x} = 0x{v:05x}  -- {attr.owner(off)}"
                  f"   (candidate wrapper entry + its referencer)")
    else:
        print("\n(no dwords point into the wrapper region -- the wrapper "
              "is entered by fall-through/branch or its entry lies outside "
              "the region)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
