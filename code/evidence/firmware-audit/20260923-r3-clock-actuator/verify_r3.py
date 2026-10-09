#!/usr/bin/env python3
"""R3 verification: deterministic re-check of every claim in
docs/research/2026-09-23-r3-clock-actuator-map.md.
Inputs (read-only): pinned CLV donor ROM, df-census-out.txt (this dir),
smu-pll-handlers.txt + smu-transition-helpers.txt (20260923-abl95fc-next dir).
"""
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PLL = ROOT / "evidence/firmware-audit/20260923-abl95fc-next"
FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
check("donor CLV ROM sha256", hashlib.sha256(rom).hexdigest() ==
      "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8")
sl = rom[0x8FEF00:0x8FEF00 + 262400]
check("robin_5 canonical sha256", hashlib.sha256(sl).hexdigest() ==
      "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37")


def u32(off):
    return struct.unpack("<I", sl[off:off + 4])[0]


def f32(off):
    return struct.unpack("<f", sl[off:off + 4])[0]


# --- 1. base slots ------------------------------------------------------------
for slot, expect, name in [
    (0x1745c, 0x0F568, "slot 0x1745c -> domain table 0xF568"),
    (0x178fc, 0x0F728, "slot 0x178fc -> second table 0xF728"),
    (0x178cc, 0x01D80200, "slot 0x178cc -> 0x01D80200 block"),
    (0x17134, 0x000FFFFF, "slot 0x17134 -> mask 0xFFFFF"),
    (0x17160, 0x010FFE00, "slot 0x17160 -> SMN window 0x010FFE00"),
]:
    check(name, u32(slot) == expect)

# --- 2. domain -> raw -> SMN map ------------------------------------------------
SMN = 0x010FFE00 + 0x200
expect_dom = {
    0x03: 0x5B18C, 0x04: 0x5B1B4, 0x0E: 0x5C0FC, 0x0F: 0x5C8FC, 0x10: 0x5C924,
    0x11: 0x6C0FC, 0x12: 0x6C124, 0x13: 0x6C900, 0x18: 0x6D150,
}
for d, raw in expect_dom.items():
    cell = 0x0F568 + d * 0x1C + 0x254
    got = u32(cell)
    check(f"domain 0x{d:02X} raw == 0x{raw:05X} (SMN 0x{SMN + (raw & 0xFFFFF):08X})",
          got == raw)

# --- 3. DF pstate rows -----------------------------------------------------------
check("row pointer array 0xCEFC..0xCF0B is zero in image",
      sl[0xCEFC:0xCF0C] == b"\x00" * 16)
rows = [0xCF0C, 0xCF34, 0xCF5C, 0xCF84, 0xCFAC]
freqs = [450.0, 450.0, 850.0, 1750.0, 250.0]
for r, f in zip(rows, freqs):
    check(f"row 0x{r:05X} +0x18 == {f} (row+0x10 {f/2} )",
          abs(f32(r + 0x18) - f) < 1e-3 and abs(f32(r + 0x10) - f / 2) < 1e-3)
check("row 0xCF84 +0x14 == 109.375 (1750/16)", abs(f32(0xCF84 + 0x14) - 109.375) < 1e-3)

# --- 4. q3 0x1D selector array ---------------------------------------------------
sel_expect = {1: 0x0D, 2: 0x00, 3: 0x01, 4: 0x02, 5: 0x03, 6: 0x04, 7: 0x05, 8: 0x06,
              9: 0x07, 10: 0x0A, 11: 0x18, 12: 0x13, 13: 0x14, 14: 0x15, 15: 0x16,
              16: 0x17, 17: 0x0B, 18: 0x08, 19: 0x09, 20: 0x0C}
ok = True
for sel, dom in sel_expect.items():
    if u32(0x13EF0 + sel * 4) != dom:
        ok = False
check("q3 0x1D selector->domain array exact (20 entries)", ok)
check("domains 0x0E..0x12 absent from the selector array (OS route closed)",
      not any(dom in (0x0E, 0x0F, 0x10, 0x11, 0x12) for dom in sel_expect.values()))

# --- 5. census content (byte-proven decompile lines) ------------------------------
census = (HERE / "df-census-out.txt").read_text()
for needle, name in [
    ("iVar4 = *(int *)(param_1 * 0x1c + _DAT_0001745c + 0x254);", "0x23890 reads descriptor +0x254 program cell"),
    ("*(undefined4 *)((param_1 & _DAT_00017134) + _DAT_00017160 + 0x200) = param_2;", "0x235c8 SMN window write"),
    ("func_0x0001b514(param_1,param_2);", "0x235c8 IPC transport branch"),
    ("FUN_000235c8(iVar4,param_2);", "0x23890 programs via 0x235c8"),
    ("*(char *)(iVar3 + 0x82) = (char)param_2;", "0x23890 updates current-code cache +0x82"),
    ("FUN_000235c8(puVar1[0xb] + iVar2,param_2);", "0x24410 channel program via 0x235c8"),
    ("*(float *)(*(int *)(uVar3 * 4 + _DAT_000171ec + 0x1c) + 0x18);", "0x1e7d8 query reads row+0x18 via DF+0x1C pointer array"),
    ("*(char *)((int)_DAT_000171ec + 0xe) = (char)param_1;", "0x1e448 selects DF pstate at DF+0x0E"),
    ("CLOSURE DONE, total functions dumped: 49", "22D6C closure ran (49 functions)"),
]:
    check(name, needle in census)

pll = (PLL / "smu-pll-handlers.txt").read_text()
for needle, name in [
    ("func_0x00023890(0xe,uVar1 & 0xff);", "SetupFclkPll (1F218) programs domain 0x0E"),
    ("*pfVar7 = fVar9;", "1F218 stores current FCLK float at DF+0x00"),
    ("func_0x00023890(0xf,uVar7);", "SetupUclkPll (1F2F0) programs domain 0x0F"),
    ("func_0x00023890(0x11,uVar7);", "1F2F0 programs domain 0x11 (UCLK mirror)"),
    ("func_0x00023890(0x10,uVar1);", "1F2F0 programs domain 0x10 (derived)"),
    ("func_0x00023890(0x12,uVar1);", "1F2F0 programs domain 0x12 (derived mirror)"),
]:
    check(name, needle in pll)

tr = (PLL / "smu-transition-helpers.txt").read_text()
for needle, name in [
    ("func_0x00024410(3,uVar5,iVar2);", "1EFB4 syncs channel 3 via 0x24410"),
    ("func_0x00024410(4,uVar5,iVar2);", "1EFB4 syncs channel 4 via 0x24410"),
    ("func_0x0002445c(3);", "1EF90 releases channel 3"),
]:
    check(name, needle in tr)

# --- 6. result doc -------------------------------------------------------------
doc = (ROOT / "docs/research/2026-09-23-r3-clock-actuator-map.md").read_text()
check("R3 doc carries the 1:1:1 structural negative",
      "not reachable through stock firmware" in doc)
check("R3 doc carries the actuator engine chain",
      "FUN_00023890(domain, code)" in doc)

print()
if FAILS:
    print(f"RESULT: FAIL ({len(FAILS)} checks): " + "; ".join(FAILS))
    sys.exit(1)
print("RESULT: PASS (all checks green)")
