#!/usr/bin/env python3
"""R2 verification: deterministic re-check of every claim in
docs/research/2026-09-23-r2-soc-vddcr-limitation.md.
Inputs (read-only): pinned CLV donor ROM, pinned GenCAD netlist,
census-out.txt + sweep-out.txt produced by SviCensus.java / HandlerSweep.java.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FAILS = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


# --- 1. robin_5 canonical identity -------------------------------------------
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
check("donor CLV ROM sha256", hashlib.sha256(rom).hexdigest() ==
      "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8")
sl = rom[0x8FEF00:0x8FEF00 + 262400]
check("robin_5 len 262400", len(sl) == 262400)
check("robin_5 canonical sha256 (64 hex chars)",
      hashlib.sha256(sl).hexdigest() ==
      "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37")

# --- 2. literal census over the whole image -----------------------------------
def count(pat):
    out, i = [], 0
    while True:
        j = sl.find(pat, i)
        if j < 0:
            return out
        out.append(j)
        i = j + 1

lit_base = count(bytes.fromhex("009e1501"))      # 0x01159E00
check("0x01159E00 literal: exactly 1 @ 0x171a4", lit_base == [0x171a4])
check("slot 0x171a4 stores 0x01159E00", sl[0x171a4:0x171a8] == bytes.fromhex("009e1501"))
check("0x0115A030 direct literal count == 0", count(bytes.fromhex("30a01501")) == [])
check("0x0115A000 direct literal count == 0", count(bytes.fromhex("00a01501")) == [])
lit_sram = count(bytes.fromhex("74340100"))      # 0x00013474
check("0x00013474 stored at 0x15394 and 0x17124 only", lit_sram == [0x15394, 0x17124])
check("slot 0x1714c stores 0x00008b18", sl[0x1714c:0x17150] == bytes.fromhex("188b0000"))

# --- 3. GenCAD netlist ----------------------------------------------------------
gpath = ROOT / "import/from-windows/Users/kukuruza/Downloads/AyuGram Desktop/ASRock AMD BC-250_ISL_X5R r1.00.cad"
gb = gpath.read_bytes()
check("GenCAD sha256", hashlib.sha256(gb).hexdigest() ==
      "decef01f78b7416bb1e51ffc7c9ea03a556a3b7e2443b98fd441ed92959c65d8")
nets, cur = {}, None
for line in gb.decode().splitlines():
    if line.startswith("SIGNAL "):
        cur = line[7:]
        nets[cur] = []
    elif line.startswith("NODE ") and cur:
        _, ref, pin = line.split()
        nets[cur].append((ref, pin))

def m(net):
    return sorted(tuple(x) for x in nets[net])

check("no net name contains SVI (SVI2 bus absent as a named net)",
      not [n for n in nets if "SVI" in n.upper()])
check("CORE_GFX_SVD == {PCA18.1, PRA29.2, PUA1.8}", m("CORE_GFX_SVD") == [("PCA18", "1"), ("PRA29", "2"), ("PUA1", "8")])
check("CORE_GFX_SVT == {PCA19.1, PRA31.2, PUA1.9}", m("CORE_GFX_SVT") == [("PCA19", "1"), ("PRA31", "2"), ("PUA1", "9")])
check("CORE_GFX_SVC == {PCA20.1, PRA32.2, PUA1.10}", m("CORE_GFX_SVC") == [("PCA20", "1"), ("PRA32", "2"), ("PUA1", "10")])
check("APU_SVD carries U25", any(r == "U25" for r, _ in nets["APU_SVD"]))
check("APU_SVT carries U25", any(r == "U25" for r, _ in nets["APU_SVT"]))
check("APU_SVC carries U25", any(r == "U25" for r, _ in nets["APU_SVC"]))
check("PRA29 bridges APU_SVD <-> CORE_GFX_SVD",
      ("PRA29", "1") in nets["APU_SVD"] and ("PRA29", "2") in nets["CORE_GFX_SVD"])
check("PRA34 bridges CORE_GFX_PMSCL <-> SMB0_CL_ISO",
      ("PRA34", "2") in nets["CORE_GFX_PMSCL"] and ("PRA34", "1") in nets["SMB0_CL_ISO"])
check("PRA35 bridges CORE_GFX_PMSDA <-> SMB0_DA_ISO",
      ("PRA35", "2") in nets["CORE_GFX_PMSDA"] and ("PRA35", "1") in nets["SMB0_DA_ISO"])

pus1 = {}
for n, v in nets.items():
    for ref, pin in v:
        if ref == "PUS1":
            pus1[pin] = n
expected_pus1 = {"1": "VDDCR_SOC_RUN_PG", "2": "SOC_OCSET", "3": "SOC_EN", "4": "SOC_FB",
                 "5": "SOC_RF", "6": "SOC_LG", "7": "SOC_VCC", "8": "SOC_PHASE",
                 "9": "SOC_HG", "10": "SOC_BST", "11": "GND"}
check("PUS1 pin set == 11 analog nets (no digital interface)",
      pus1 == expected_pus1)
check("PUS1 nets carry no digital bus names",
      not [n for n in expected_pus1.values() if re.search(r"SMB|I2C|PMB|SVD|SVT|SVC|SVI", n, re.I)])

soc_refs = {ref for ref, _ in nets["+VDDCR_SOC"]}
expected_soc_refs = {"C1873", "C1874", "C1882", "C2081", "C2084", "C2085", "C2086", "C2087",
                     "C2088", "C2097", "C252", "C351", "C63", "C9", "CES2", "CES3", "NSS1",
                     "OR63", "PCS13", "PCS14", "PCS15", "PCS16", "PCS17", "PCS18", "PLS1",
                     "PRS18", "U25", "VTB_SOC"}
check("+VDDCR_SOC member set exact", soc_refs == expected_soc_refs)
check("U25 has 32 pins on +VDDCR_SOC", sum(1 for r, _ in nets["+VDDCR_SOC"] if r == "U25") == 32)
check("SOC_EN members = hardware sequencing only (no EC/SMU endpoint)",
      m("SOC_EN") == [("PCS3", "1"), ("PRS19", "2"), ("PRS20", "2"), ("PRS4", "2"), ("PUS1", "3")])

# --- 4. census-out.txt byte-proven decompile lines ------------------------------
census = (HERE / "census-out.txt").read_text()
for needle, name in [
    ("*(int *)(_DAT_000171a4 + 0x230) = uStack_30;", "FUN_0002bdec writes selector 0 (base+0x230)"),
    ("*(uint *)(_DAT_000171a4 + 0x230) = uStack_30 | 1;", "FUN_0002be40 writes selector 1"),
    ("CONCAT12(*(undefined1 *)(_DAT_0001714c + 1),0x20)", "FUN_0002be18 writes 0x20 calibration"),
    ("func_0x0002bd80(uVar1 & 0xffff);", "q3 0x0F kind 0 -> CPU wrapper 0x2bd80"),
    ("func_0x0002bda4(uVar1 & 0xffff);", "q3 0x0F kind 1 -> GFX wrapper 0x2bda4"),
    ("*(float *)(_DAT_00017124 + 0xc);", "q3 0x30 selector 0 reads domain-0 float (+0x0c)"),
    ("*(float *)(_DAT_00017124 + 0x2c);", "q3 0x30 selector 1 reads domain-1 float (+0x2c)"),
    ("*(int *)(_DAT_000180cc + 0x6c) = iVar1;", "q3 0x49 CPU VID offset -> config +0x6c"),
    ("*(int *)(_DAT_000180cc + 0x9c) = iVar1;", "q3 0x4A GFX VID offset -> config +0x9c"),
    ("*(undefined4 *)(_DAT_00017124 + 0x14) = uVar1;", "q3 0x4D CPU large offset -> state +0x14"),
    ("*(undefined4 *)(_DAT_00017124 + 0x30) = uVar1;", "q3 0x4E GPU large offset -> state +0x30"),
    ("*(bool *)(_DAT_00017124 + 0x66) = (uVar2 & 1) == 1;", "q3 0x9A extra-voltage flags -> state +0x66"),
    ("CENSUS DONE", "census completed"),
]:
    check(name, needle in census)

# --- 5. sweep-out.txt full-handler-surface proof ---------------------------------
sweep = (HERE / "sweep-out.txt").read_text()
check("sweep completed", "SWEEP DONE" in sweep)
check("sweep decompiled >= 110 handlers",
      len(re.findall(r"---- FUNC @ 0x", sweep)) >= 110)
check("no swept handler reads the SVI base slot 0x171a4", "000171a4" not in sweep)
check("no swept handler writes the SVI command register (+ 0x230)",
      "+ 0x230" not in sweep)

func_at_17124, curf = set(), None
func_at_180cc = set()
for line in sweep.splitlines():
    hdr = re.search(r"---- FUNC @ (0x[0-9a-f]+) ----", line)
    if hdr:
        curf = hdr.group(1)
        continue
    if "00017124" in line and curf:
        func_at_17124.add(curf)
    if "000180cc" in line and curf:
        func_at_180cc.add(curf)
check("handlers touching selector state == CPU/GFX set exactly",
      func_at_17124 == {"0x2c0c8", "0x2c0ec", "0x2c340", "0x2c358", "0x2c388",
                        "0x2c44c", "0x2d7a0", "0x2db90"},
      )
check("handlers touching domain config == CPU/GFX droop-cal pair",
      func_at_180cc == {"0x2d7a0", "0x2db90"})
check("q3 0x36 reads domain-0 float (current CPU voltage)",
      "fVar3 = *_DAT_00017124 * fRam0001729c;" in sweep)
check("q3 0x37 reads domain-1 float (current GPU voltage)",
      "fVar3 = *(float *)(_DAT_00017124 + 0x20) * fRam0001729c;" in sweep)
check("q0 0x3B ForceGfxVid calls the GFX wrapper 0x2bda4",
      "func_0x0002bda4();" in sweep)
check("q3 0x4F/0x50 write only DPM-table VID columns (0x171b4+...+0x3b8)",
      "_DAT_000171b4 + ((uVar1 >> 0x12 & 3) * 4 + (uVar1 >> 0x10 & 3)) * 0x3c4 + 0x3b8" in sweep
      and "*(int *)(iVar2 + 0x3b8) = (int)sVar1;" in sweep)
check("q3 0x8E inner writes config float only (0x17aa8+0x70)",
      "*(float *)(iRam00017aa8 + 0x70) = ((float)param_1 / 1.0) * _DAT_000170ac;" in sweep)

# --- 6. result doc ---------------------------------------------------------------
doc = (ROOT / "docs/research/2026-09-23-r2-soc-vddcr-limitation.md").read_text()
check("R2 doc records the limitation verdict", "no BIOS (or firmware) path to +VDDCR_SOC" in doc)
check("R2 doc records the canonical robin_5 hash",
      "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37" in doc)

# --- verdict ---------------------------------------------------------------------
print()
if FAILS:
    print(f"RESULT: FAIL ({len(FAILS)} checks): " + "; ".join(FAILS))
    sys.exit(1)
print("RESULT: PASS (all checks green)")
