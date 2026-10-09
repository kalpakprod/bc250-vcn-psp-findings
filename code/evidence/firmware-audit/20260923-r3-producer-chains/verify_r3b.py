#!/usr/bin/env python3
"""R3 producer-chain pass: byte-backed assertions for the ABL1 clock-argument
decode refinement, the APCB-only boot inputs, and the empirical NVRAM-only
nature of the operator's SYNC OC profiles (including both 1:1:1 attempts).

Classes: observed-bytes (image reads, disassembly encodings), corpus census
(re-derived from module bodies), emulation results (cited, not re-run here).
No hardware, no flash, no clock measurement.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FAILS = []


def check(label, cond):
    if not cond:
        FAILS.append(label)
        print("FAIL:", label)


def le16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def le32(b, o):
    return struct.unpack_from("<I", b, o)[0]


# ---------------------------------------------------------------- ABL1 body
abl1 = (ROOT / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin").read_bytes()
ABL1_SHA = "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
check("ABL1 sha", hashlib.sha256(abl1).hexdigest() == ABL1_SHA)

# Dead value-table block 0x5F1E..0x5F9A: every computed value lands in [sp,#4]
# (9001 / 9701 / f8cd9004 stores) and 0x5FA8 overwrites the SAME slot with the
# FCLK default before any read -> the table is dead; only the LSR at 0x5F30 is live.
check("table head movw r1,#0x352", abl1[0x5F1E:0x5F22] == bytes.fromhex("40f25231"))
check("sub r0,r4,#0x352", abl1[0x5F2C:0x5F30] == bytes.fromhex("a4f25230"))
check("unconditional LSR r8,r4,#1", abl1[0x5F30:0x5F34] == bytes.fromhex("4fea5408"))
check("store slot [sp,#4] at 0x5f6c", abl1[0x5F6C:0x5F6E] == bytes.fromhex("0190"))
check("store slot [sp,#4] at 0x5f70", abl1[0x5F70:0x5F74] == bytes.fromhex("cdf80490"))
check("store slot [sp,#4] at 0x5f8e", abl1[0x5F8E:0x5F90] == bytes.fromhex("0190"))
check("store slot [sp,#4] at 0x5f92", abl1[0x5F92:0x5F94] == bytes.fromhex("0197"))
check("same slot overwritten by FCLK default at 0x5fa8", abl1[0x5FA8:0x5FAA] == bytes.fromhex("0190"))
check("FCLK default 1200 (0x4b0)", abl1[0x5FA4:0x5FA8] == bytes.fromhex("40f2b040"))
check("chip-6 default 250 (0xfa) + b back to 0x5fa8", abl1[0x6028:0x602C] == bytes.fromhex("fa20bde7"))
check("SVC28 FCLK selector 0x0e, arg [sp,#4]", abl1[0x5FC2:0x5FC6] == bytes.fromhex("0e200199"))
check("SVC28 UCLK selector 0x0f, arg r8", abl1[0x5FF4:0x5FF8] == bytes.fromhex("0f204146"))
check("SVC #0x28 opcode at both sites", abl1[0x5FC8:0x5FCA] == bytes.fromhex("28df") and abl1[0x5FFA:0x5FFC] == bytes.fromhex("28df"))

# Firmware's own service names (inline strings after the function).
check("GnbSmuInitAblCAR entry string", abl1[0x602C:0x6044] == b"GnbSmuInitAblCAR Entry\n\x00")
check("ConfigSocRail string", abl1[0x6080:0x60A4] == b"Send PSPSMC_MSG_ConfigSocRail 0x%x\n\x00")
check("SetupFclkPll string", abl1[0x60C0:0x60E3] == b"Send PSPSMC_MSG_SetupFclkPll 0x%x\n\x00")
check("SetupUclkPll string", abl1[0x60E4:0x6108] == b"Send PSPSMC_MSG_SetupUclkPll  0x%x\n\x00")

# The provider 0x463C (APCB runtime-cache token read) has exactly ONE call
# site in ABL1 and it is the FCLK override lookup (ID 0x0F).
sites = []
for i in range(0, len(abl1) - 4, 2):
    hw1, hw2 = struct.unpack_from("<HH", abl1, i)
    if (hw1 & 0xF800) == 0xF000 and (hw2 & 0xF800) == 0xF800:
        imm = ((hw1 & 0x7FF) << 12) | ((hw2 & 0x7FF) << 1)
        if imm & 0x400000:
            imm -= 0x800000
        if (i + 4 + imm) & 0xFFFFFFFF == 0x463C:
            sites.append(i)
check("single provider call site at 0x5fae", sites == [0x5FAE])
check("provider arg movs r1,#0xf", abl1[0x5FAA:0x5FAC] == bytes.fromhex("0f21"))
# 0x4800 lookup bounds: valid token IDs 1..0x160.
check("lookup bounds cmp r0,#0x160", abl1[0x480A:0x480E] == bytes.fromhex("b0f5b07f"))
# GnbSmuInitAblCAR is ABL service item 0x17 (service table entry -> handler).
check("service dispatch movs r1,#0x17", abl1[0x7E36:0x7E38] == bytes.fromhex("1721"))

# ------------------------------------------------------------- donor + board
donor = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
DONOR_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
check("donor sha", hashlib.sha256(donor).hexdigest() == DONOR_SHA)
board = (ROOT / "dump/2.bin").read_bytes()
check("board sha", hashlib.sha256(board).hexdigest() == "83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0")

APCB = 0xAB1000
check("donor APCB magic", donor[APCB:APCB + 4] == b"APCB")
check("donor APCB size 2972", le32(donor, APCB + 8) == 2972)
check("donor APCB checksum", sum(donor[APCB:APCB + 2972]) % 256 == 0)
check("donor item7 enum 0x24 (1800) at +0x482", donor[APCB + 0x482] == 0x24)
check("donor token21/UclkDiv bytes at +0x86E..0x872", donor[APCB + 0x86E:APCB + 0x873] == b"\x01\x01\x01\x01\x01")
check("donor DF gate=1 value=1420 tail", donor[APCB + 0xB99:APCB + 0xB9C] == bytes.fromhex("018c05"))
check("board APCB is a different layout (2928)", le32(board, APCB + 8) == 2928)
# 2.bin CBSG tail: same structural override slot, but gate byte 0 and value 1000.
# Tail row = last row of inst15 subgroup (board: 0x488+1768 -> 0xB6C..0xB70;
# donor: 0x48C+1808 -> 0xB98..0xB9C). Row form: (u8_0, gate, u16_le value).
check("donor override row (0,1,1420) at +0xB98", donor[APCB + 0xB98:APCB + 0xB9C] == bytes.fromhex("00018c05"))
check("board override row (0,0,1000) at +0xB6C", board[APCB + 0xB6C:APCB + 0xB70] == bytes.fromhex("0000e803"))
# CBSG subgroup sizes: board inst13 68 B / inst15 1768 B (donor 72/1808, +44 total).
# Subgroup header: gid u16 @+0, instance u16 @+2, size u32 @+4.
check("board CBSG inst13 gid/inst", le16(board, APCB + 0x444) == 0x1707 and le16(board, APCB + 0x444 + 2) == 13)
check("board CBSG inst13 size 68", le32(board, APCB + 0x444 + 4) == 68)
check("board CBSG inst15 size 1768", le32(board, APCB + 0x488 + 4) == 1768)
check("donor CBSG inst13 size 72", le32(donor, APCB + 0x444 + 4) == 72)
check("donor CBSG inst15 size 1808", le32(donor, APCB + 0x48C + 4) == 1808)
# 2.bin is a different firmware BUILD: the donor SMU body (robin_5) region is not
# byte-equal at the same offset and appears nowhere in the board dump.
SMU_OFF, SMU_SIZE = 0x8FEF00, 262400
dsmu = donor[SMU_OFF:SMU_OFF + SMU_SIZE]
check("donor SMU body sha cae8617c", hashlib.sha256(dsmu).hexdigest() == "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37")
check("board SMU region differs from donor", board[SMU_OFF:SMU_OFF + SMU_SIZE] != dsmu)
same = sum(1 for a, b in zip(dsmu, board[SMU_OFF:SMU_OFF + SMU_SIZE]) if a == b)
check("board SMU same-offset agreement 39.3%", abs(same - 103119) <= 20)
for probe in (dsmu[:64], dsmu[SMU_SIZE // 2:SMU_SIZE // 2 + 64], dsmu[-64:]):
    check("donor SMU probe absent from board", probe not in board)

# ROM start = EFI_SYSTEM_NV_DATA FV (the UEFI variable store where Setup persists).
check("SYSTEM_NV_DATA FV GUID at ROM 0x10", donor[0x10:0x20] == bytes.fromhex("78e58c8c3d8a1c4f9935896185c32dd3"))
check("FV signature _FVH", donor[0x28:0x2C] == b"_FVH")
# Donor NVRAM Setup values: MCLK enum 36 (1800), DF override 1420.
check("donor NVRAM MCLK enum 0x24 at 0x7e5", donor[0x7E5] == 0x24)
check("donor NVRAM DfClockOverride 1420 at 0xbd3", donor[0xBD3:0xBD5] == bytes.fromhex("8c05"))
check("donor NVRAM UclkDiv-region bytes 01x6 at 0x716", donor[0x716:0x71C] == b"\x01" * 6)

# ----------------------------------------------- operator SYNC OC profiles
profiles = {
    "01_BC250_SYNC_FclkUclk_1to1_Mclk1750_StockCPU.bin": ("01", 0x23, bytes.fromhex("6b03")),
    "02_BC250_SYNC_Full_1to1to1_1333MHz_StockCPU.bin": ("02", 0x1A, bytes.fromhex("3505")),
    "03_BC250_SYNC_Full_1to1to1_1750MHz_StockCPU.bin": ("03", 0x23, bytes.fromhex("d606")),
    "03_BC250_ULTIMATE_LOW_LATENCY_StockCPU.bin": ("03U", None, None),
}
pbase = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/oc_profiles"
for name, (tag, mclk, df) in profiles.items():
    p = (pbase / name).read_bytes()
    # The whole APCB is untouched by the Setup/mod edits: byte-identical to donor.
    check(f"{tag} APCB byte-identical to donor", p[APCB:APCB + 2972] == donor[APCB:APCB + 2972])
    if mclk is not None:
        check(f"{tag} NVRAM MCLK enum {mclk:#x} at 0x7e5", p[0x7E5] == mclk)
    if df is not None:
        check(f"{tag} NVRAM DfClockOverride {le16(df, 0)} at 0xbd3", p[0xBD3:0xBD5] == df)
p01 = (pbase / "01_BC250_SYNC_FclkUclk_1to1_Mclk1750_StockCPU.bin").read_bytes()
check("profile01 UclkDiv-region bytes 03x6 at 0x716", p01[0x716:0x71C] == b"\x03" * 6)
# The mod author's own arithmetic: 875 = 1750/2 (FclkUclk 1:1 attempt),
# 1750 = MCLK (full 1:1:1 attempt) - both assume UCLK can follow; firmware
# hardcodes UCLK = MCLK/2, so no APCB-untouched edit can reach 1:1:1.
check("profile01 FCLK edit = 1750/2", le16(p01, 0xBD3) * 2 == 1750)
p03 = (pbase / "03_BC250_SYNC_Full_1to1to1_1750MHz_StockCPU.bin").read_bytes()
check("profile03 FCLK edit = MCLK 1750", le16(p03, 0xBD3) == 1750)

# ------------------------------------------------- corpus reader/serializer census
cons = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
V = json.loads((cons / "verification.json").read_text())
readers = {r["token"] for r in V["requests"]}
check("corpus direct NVTB readers are 10ff/1104/1000/1001", readers == {0x10FF, 0x1104, 0x1000, 0x1001})
targets = {0x1364, 0x1363, 0x11ED, 0x1204, 0x1331, 0x1373, 0x1374}
check("no target token among direct readers", not readers & targets)
check("20260919 verification passed 517", V["passed"] == 517)
# Re-derive the 49 serializer write sites and their 7 distinct IDs from module bodies.
C = json.loads((cons / "census.json").read_text())
R = {r.get("ui", r["ffs_guid"]): r for r in C["records"]}


def rawoff(name, rva):
    for s in R[name]["sections"]:
        if s["rva"] <= rva < s["rva"] + s["size"]:
            return rva - s["rva"] + s["raw"]
    raise ValueError(hex(rva))


CV = json.loads((cons / "coverage.json").read_text())
imm = [x for x in CV["target_candidates"] if x["category"] == "immediate-candidate"]
check("49 serializer sites", len(imm) == 49)
ids = {}
for x in imm:
    body = (cons / (R[x["module"]]["stem"] + ".bin")).read_bytes()
    off = rawoff(x["module"], x["rva"])
    check(f"serializer mov edx pattern {x['module']} {x['rva']:#x}", body[off] == 0xBA and body[off + 5:off + 11] == bytes.fromhex("8b45f8668910"))
    ids.setdefault(le32(body, off + 1) & 0xFFFF, set()).add(x["module"])
check("serializer IDs are exactly the 7 targets", set(ids) == targets)
check("each target written by 7 modules", all(len(v) == 7 for v in ids.values()))

# ------------------------------- MemoryPstate 0x123C serializer sites (added)
# 0x123C sat outside the 20260919 census target list, so it is absent from the
# 49 re-derived sites above — a filter artifact, not a different mechanism.
# It uses the SAME serializer pattern in the same 7 modules (1 site each):
# mov edx,0x123c; mov eax,[ebp-0x8]; mov WORD PTR [eax],dx. Clock-token
# serializer total: 56 sites across 8 IDs, all orphaned at the direct-reader level.
memstate_rvas = {
    "AmdFabricAriPei": 0xDD21,
    "AmdNbioBaseARIPei": 0xEB31,
    "AmdNbioGfxARIPei": 0xBEF1,
    "AmdNbioPcieARIPei": 0xF641,
    "AmdNbioSmuV10Pei": 0xC841,
    "AmdSocBl5AriPei": 0xC581,
    "CbsBasePei": 0xA7C1,
}
for name, rva in memstate_rvas.items():
    body = (cons / (R[name]["stem"] + ".bin")).read_bytes()
    off = rawoff(name, rva)
    check(f"0x123c serializer {name} {rva:#x}",
          body[off:off + 5] == bytes.fromhex("ba3c120000")
          and body[off + 5:off + 11] == bytes.fromhex("8b45f8668910"))
check("0x123c absent from direct readers", 0x123C not in readers)

# ------------------------------------------------ writer census (emulation, cited)
wc = json.loads((ROOT / "evidence/firmware-audit/20260923-abl1-apcb-writer-census/writer-census-result.json").read_text())
check("writer census base is donor", wc["base_image_sha256"] == DONOR_SHA)
check("writer census ABL1 pinned", wc["abl1_sha256"] == ABL1_SHA)
pol = [c["final_policy"] for c in wc["cases"]]
check("policy follows APCB item7 (0x24->1800, 0x23->1750)", pol == [1800, 1750, 1800])
check("CMOS word ignored when APCB native", wc["cases"][2]["cmos_clock"] == 1650 and pol[2] == 1800)
check("writer census verdict CLOSED-NEGATIVE", wc["verdict"]["j1_executed_window"].startswith("CLOSED-NEGATIVE"))
check("no foreign writes", wc["verdict"]["foreign_writes"] == [])

# ------------------------------------------------------ APCB emulation (cited)
ap = json.loads((ROOT / "evidence/firmware-audit/20260923-abl95fc-next/emulation-apcb-result.json").read_text())
svc01 = [(s["selector"], s["argument"]) for s in ap["cases"][0]["svc"]]
check("emulated baseline SVC28 (14,1420),(15,900)", svc01 == [(14, 1420), (15, 900)])
check("emulated UCLK arg = memword>>1", ap["cases"][0]["svc"][1]["argument"] == ap["cases"][0]["input_word"] >> 1)
gate_off = [c for c in ap["cases"] if c["case"] == "gate_off"][0]
check("gate off -> FCLK default 1200", [(s["selector"], s["argument"]) for s in gate_off["svc"]] == [(14, 1200), (15, 900)])

# -------------------------------------------- hardware runtime evidence (probe4l/l2)
# Live read-only mailbox queries on the running board (v001), 2026-09-23 night,
# Linux route. Units falsifier (c): the SMU's own answers are real MHz/mV, and the
# DF pstate row values + /2 + k-derivation pattern match the static table.
rt1 = json.loads((ROOT / "evidence/runtime/20260923-234415-probe4l-clockplan.json").read_text())
check("probe4l: SMU alive before and after", rt1["alive_before"] and rt1["alive_after"])
check("probe4l: secure gate already open on v001 boot", rt1["secure_before"] is True)
check("probe4l: core mask 0x0005A870 = 0xFF (8 cores live)",
      int(rt1["reads"]["probe_5a870"]["value"], 16) == 0xFF)
check("probe4l: domain bitmap 0x0000CCB8 = 0x00000000 (VCN bit 6 clear)",
      int(rt1["reads"]["domain_bitmap_ccb8"]["value"], 16) == 0)
check("probe4l: clock-plan words A=B=0x0000000E",
      rt1["clock_plan_words"] == {"A": "0x0000000e", "B": "0x0000000e"})
descv = [v for k, v in rt1["reads"].items() if k.startswith("desc_")]
check("probe4l: VCN descriptor window all zero (20 words, EMPTY)",
      len(descv) == 20 and all(int(v["value"], 16) == 0 for v in descv))
check("probe4l: vcn_domain_bit6 false", rt1["vcn_domain_bit6"] is False)

rt2 = json.loads((ROOT / "evidence/runtime/20260923-234734-probe4l2-clocks-full.json").read_text())
check("probe4l2: SMU alive before and after, no stop",
      rt2["alive_before"] and rt2["alive_after"] and rt2.get("died_at") is None)


def ret(d, k):
    return int(d[k]["ret"], 16)


ladder = [ret(rt2, "pstate_clk_%d" % p) for p in range(8)]
check("probe4l2: CPU pstate ladder 3200..800 (real MHz)",
      ladder == [3200, 2550, 2325, 1960, 1820, 1600, 1271, 800])
rows = [450, 450, 850, 1750, 250]  # static DF pstate rows (verify_r3.py)
c39 = [ret(rt2, "c39_sel_%02d" % s) for s in range(4)]
c3a = [ret(rt2, "c3a_sel_%02d" % s) for s in range(4)]
c38 = [ret(rt2, "c38_sel_%02d" % s) for s in range(4)]
check("probe4l2: 0x39 answers = static DF rows /2 (225/225/425/875)",
      c39 == [r // 2 for r in rows[:4]])
check("probe4l2: 0x3A answers = k-derived fields (112/112/106/109)",
      c3a == [450 // 4, 450 // 4, 850 // 8, 1750 // 16])
check("probe4l2: 0x3A row3 = static 109.375 truncated (109)", c3a[3] == 109)
check("probe4l2: duplicate rows 0/1 answer identically",
      c39[0] == c39[1] and c3a[0] == c3a[1] and c38[0] == c38[1])
check("probe4l2: 0x38 answers (250/250/750/1200; runtime rows, identity unpinned)",
      c38 == [250, 250, 750, 1200])
check("probe4l2: selectors 4..20 cleanly rejected (0xFF, not death)",
      all("Rejected" in rt2["c38_sel_%02d" % s]["exc"] for s in range(4, 21)))
check("probe4l2: GFX clock 2200 from both q0 0x0F and 0x37",
      ret(rt2, "q0_gfxclk") == 2200 and ret(rt2, "q0_gfx_freq_37") == 2200)
check("probe4l2: current DF pstate = 3", ret(rt2, "q0_df_pstate") == 3)
check("probe4l2: SoC DPM ladder (1254/500/762/762)",
      [ret(rt2, "socdpm_%d" % i) for i in range(4)] == [1254, 500, 762, 762])
check("probe4l2: live core freqs in real MHz (idle 1400, active >2000)",
      ret(rt2, "corefreq_1") == 1400 and ret(rt2, "corefreq_0") > 2000)
check("probe4l2: voltages in mV (CPU 724, GPU 1018)",
      ret(rt2, "q3_cpu_volt_36") == 724 and ret(rt2, "q3_gpu_volt_37") == 1018)

print()
if FAILS:
    print(f"FAIL {len(FAILS)}/{len(FAILS)}", *FAILS, sep="\n  ")
    sys.exit(1)
print("PASS all producer-chain + runtime-evidence assertions")
