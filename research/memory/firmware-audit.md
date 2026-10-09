# Firmware and VCN audit state

## AMD-stock 4700S C0A acquired, older stocks unfound (2026-09-16, root-verified)

C0A-stock pack pulled from AMD via browser bridge (direct curl dead, JS gate):
pack `6df2317d...` (4.0 MB), inner image byte-identical to corpus `bb2cf51d...`
(PSP-18, 4 FVs, APCB-1160 PASS). Mod attribution CLOSED: bios-mods tid39055
Drive packs are byte-identical to ~/Downloads mods. C06-C09 stocks NOT found
(AMD lists C0A only; Wayback empty; no mirrors) — worker hashes unverified,
low priority (older AGESA). Bytes: `evidence/donor/amd-4700s-20260916/`.
Full record: `docs/action-logs/2026-09-16-amd-4700s-stock.md`.

## Track B PSP/APCB verdicts (2026-09-16, root-verified)

PSP t36/t69 carriers IDENTICAL across P2/P3/P5/clv/dump (b365d5b1/272514c0)
— VCN policy never changed; OQ P5-vs-P3 policy CLOSED statically. SMU t8 and
t28 t40 updated in P5/clv (13c93c08/5b6828bf) vs P2/P3/dump (6a3da1ef/ebd9a7d2).
t50: dump == P3.00 (7bec6003, P3-lineage confirmed). P5.00 APCB: MEMG ==
dump (3ab23b24, cross-confirms M2 config from 2 sources), PSPG new
(0d778738, third version), CBSG stub 84 B. clv = P5.00 + full CBSG 1896 B
(b073915e) — OQ-N3 partially answered: community-style OC-capable P5 variant
(2025-10-05). Record: phase3-prep log, Track B section.

## Phase 3 prep: M1 collapsed, M2 built (2026-09-16, root-verified)

M1 = no NVRAM transplant (C0A-stock factory-empty, 0 records vs dump 672;
first boot self-populates; M1 is post-flash observation). M2 =
C0A-stock + 4 MEMG bytes + APCB checksum (0x5E->0x1C):
`candidates/BC250_M2_C0A_MEMG_BC250_v001_from_C0A-stock.bin`
(`049419cb...`), 5 changed bytes, PSP/APCB PASS, builder
`scripts/build_m2_c0a_memg.py` reproduces byte-identical output. Review
INCOMPLETE (no second family) — not flash-approved. M0 runbook pinned to
proven flashrom lines. Record: `docs/action-logs/2026-09-16-phase3-prep-m2.md`.

## Phase 2 board-diff verdicts + M0 GO memo (2026-09-16, root-verified)

APCB: UNKN/DFG/FCHG identical; PSPG inst-2 differs; MEMG inst-7/8 differ by
ONE 4-byte field (subgroup+0x94: C0A `00 00 00 00` vs BC250 `00 01 00 20`,
2 bits); CBSG 84 vs 1852 B (whole size delta). FCH chip part still open
(config identical; lspci/marking = operator handoff). SIO split IT8772E vs
NCT6686D (hang-class risk); VRM ISL PEIMs BC250-only (top M0 unknown after
memory); AGESA drops differ (46.1.2 vs 44.0.0). M0 = GO analytically, gated
on fresh capture + exact approval + defined P0 signal. Record:
`docs/action-logs/2026-09-16-phase2-board-diff.md`.

## Phase 1 donor-vs-BC250 static verdicts (2026-09-16, root-verified)

Census: 85 same / 128 diff / 31 donor-only (TCG+TPM+IT8772E) / 20 BC250-only
(CBS+CoreUnlock+OEMBOARD+NVMe+LAN+NCT6686D+ISL VRM). PEI order identical thru
AMD chain; ALL silicon PEIMs diff-body: AGESA drops differ (donor CDBDK-BL5
44.0.0.220406 vs dump RBNBDK-BL5 46.1.2.211126 vs P5.00 46.1.2.220426) —
donor training is OLDER-numbered. IFR: donor Setup 40f/323q with ONE OC
question; CBS (71f/1193q, 122 OC) exists only on BC250 — M0 loses all OC
menus. fTPM stack complete on donor (PEI carries cap/reset logic, no
versions). Video: no GOP/VBIOS/ATOMBIOS/GUID anywhere (symmetric unknown).
Record: `docs/action-logs/2026-09-16-phase1-static-re.md`.

## RetroWeb BC250 native set acquired (2026-09-16, root-verified)

Five 16 MiB images from theretroweb.com/motherboards/s/amd-bc-250 (ID 20611),
all PSP-19 incl 0x24/0x45, 4 FVs, 233 modules, stock DFG, zero TPM/GOP/VBIOS:
P2.00 `ee6150df...` (NEW), P3.00 `07595ca3...` (MATCH), P3.00-MENU `48fbe5d3...`
(MATCH), P5.00 `0d6f136c...` (MATCH, synthesis top base pick), P5.00_clv
`ea578104...` (NEW first hash). Page: BGA2197, 16 GB GDDR6 UMA, DP+LAN+USB,
M.2; aka ASRock BC-250/4U12G. APCB sizes 1160/2916/2916/1160/2972. Bytes in
`evidence/donor/retroweb-20260916/` + manifest. Boot/OC/VCN behavior UNRUN.
Full record: `docs/action-logs/2026-09-16-retroweb-bc250-bios.md`.

## Vendor 4700S BIOS intake: C08 + C0A are real donor images (2026-09-16)

Operator-supplied `~/Downloads/C0A.zip` (`a7f2e4b5...`) and `C08.zip`
(`fb01dd67...`) are 4700S AFU packs (EFI+Windows flashers, 16 MiB
images, guides). C0A = 2022-05-20 vulnerability fixes, image `e8fa745b...`;
C08 = 2021-08-27 bug fix, image `26863de9...`.
G7 LATER SAME DAY: both images are AMIBCP-unhide MODS, not stock (root-verified:
Setup 35 sparse bytes ALL ->0x47). True C0A-stock = corpus `bb2cf51d...`.
Mods are REFERENCE-only. See `memory/incidents/2026-09-16-c0a-c08-mods-not-stock.md`. Both parse clean: PSP@8E0000
18 entries Fletcher32 PASS, 4 FVs, 245 modules, APCB@AB1000 size 0x488 PASS
with stock DFG, AGESA V9. Neither image has PSP 0x24/0x45 carriers, GOP, or
VBIOS (same absences as BC250 dump for video; symmetric unknown). Donor HAS
AmdPspFtpmDxe/Pei; BC250 dump has no TPM modules (new TPM-route lead).
Vendor-C0A vs corpus-C0A (`bb2cf51d...`): only Setup+AMITSE bodies differ
(1.3 MB raw = recompression ripple); cause unresolved. C08 vs C0A: PSP blobs

- FV genuinely older/newer. Same Ariel silicon (ARI drivers both sides,
  identical layout, 09-14 byte-identity evidence) but DIFFERENT board
  (Cardinal/A77E/dGPU-only vs BC250). Cross-flash = high-risk branch, unrun.
  TPU primary source (via user-browser bridge, 2026-09-16): 8C/16T, 65 W,
  3.6/4.0 GHz, Cardinal, BGA 2197, Zen 2, 8 MB L3, TSMC 7 nm, GDDR6, ext PCIe
  Gen 2, no iGPU, locked multiplier. TPU says "Renoir", press says Ariel —
  discrepancy preserved.
  Full record: `docs/action-logs/2026-09-16-4700s-vendor-bios.md`.

## D-R1 Q3 mixed-width closure (2026-09-15)

Length-driven Xtensa decoding of PMFW body SHA-256 `5c805026581ace101ba43ef4d0f6b34354f4a61461a1c78d2fa6a335a53d9936` reaches `0x2E45B mov.n a2,a7` after the 3-byte non-branch `0x2E451` bytes `3010fa`; pypcode lacks that constructor, while GNU floating-point configurations decode `const.s f1,0`. With `a7=0x13ED4`, the `0x2E45D` `a8!=a9` loop-entry path establishes `a2=0x13ED4` before the first `0x2E468` read, so `*(0x13ED4+12*i+0x14C)` directly aliases Q3 `*(0x13ED4+12*(i+1)+0x140)` for `i=0..19`. The downstream d expression is `*(0x13ED4+4*i+8)` with candidate values `{0x0..0xD,0x13..0x18}`; float gates and receiver/hardware effect remain unresolved. Evidence: `evidence/smu-ipc-d-r1/q3-msg1d-single-decoder.txt`; independent raw `/home/OWNER/orca/projects/orchestra/worktrees/home-kukuruza-orca-projects-bc250/sol-reviewer/.orchestra/tasks/8/raw-dr1-f7b7c43-checks.txt`.

## Authoritative SVC63 mapping (2026-09-15)

Common switch base0x45E4+entry0x3CC=0x49B0 ->0x537C. It clears translation
entries and invalidates TLB, not a cryptographic verifier. The0x49F8/0x19A0
claim below used the wrong base and is retracted. Loader authentication
remains to establish through t28 9C9C/10730, not svc63.

## G7 SVC switch base and coverage (2026-09-15)

SVC dispatch switch uses common PC base0x45E4, not each entry's address;
SVC7C remains target0x4D28. No conclusion about SVC0x63 semantics follows
from previous incorrect table arithmetic. Empty whole-blob Thumb decode is
not caller coverage because t02 begins with ARM vectors. See
docs/action-logs/2026-09-15-svc7c-input-audit.md.

## SVC7C input-surface audit (2026-09-15)

Corrected t28 scan confirms A660's only direct caller uses fixed pointer
0xE35840 after type0x16 processing. Other indexed SVC7C sites remain
signed/runtime tables; no mutable VCN target proven. NULL-return write at
0x5A88 is confirmed but lacks attacker-controlled input. No BIOS unlock
candidate justified. Evidence: docs/action-logs/2026-09-15-svc7c-input-audit.md.

## SVC7C pair source boundary (2026-09-15)

t28 type0x16 pair consumer pointer0xE35840 lies outside the extracted body
and is runtime/global memory. The preceding0x16D88 verification path builds
state in scratch/global memory; no direct unsigned x86/APCB/NVRAM source was
traced to it. Unchecked count and NULL-write remain defects without an
attacker-controlled source. No immediate BIOS patch follows. See
docs/action-logs/2026-09-14-svc7c-callsite-scan.md.

## G7 type-0x16 validator correction (2026-09-14)

t28 `0x16D88` performs the substantive load/verification flow; neighboring
`0x13544` is a stub returning zero and is not an independent validator.
`0xA660` still receives a fixed t28 pointer, so its unchecked count and
SVC7C writes are robustness defects without demonstrated mutable BIOS input.

## t28 type-0x16 pair loader (2026-09-14)

LoaderD9DC selects A660 only for entry type0x16 after validators16D88 and
13544 return0; pointer literal0xE35840 and count stack-derived. A660 shifts
address words<<2 and ignores svc7C results. This is a data-driven SVC write
surface, but unsigned BIOS input and VCN target mapping remain unproven.

## Table-driven svc7C caller traced (2026-09-14)

t28 functionA660 consumes8-byte pairs (address word shifted2, value), invokes
svc7C(width4), ignores its result. BL atDBCA in loaderD9DC selects this path
for r4==0x16 only after16D88/13544 return0; pointer fixed0xE35840 and count
from stack+0x34. No untrusted-input provenance yet. Empty wrapper-origin
linear scan is not coverage. Evidence:2026-09-14-svc7c-callsite-scan.md.

## G7 SVC caller scan encoding (2026-09-14)

Raw Thumb SVC0x7C encoding is7CDF, not DF7C. Prior negative ABL search used
reversed bytes and is invalid evidence. Corrected matches are candidates only;
linear decode from headers is not coverage. NULL-write emulator results remain
valid, but no untrusted caller has been established. See svc7c-null-test log.

## Exact-code SVC7C rejection defect (2026-09-14)

16-case Unicorn test reproduces mapper NULL return followed by unchecked
STRB/STRH/STR at0 for denied/overflow addresses and widths1/2/4. Wrapper
reports success if synthetic memory accepts the write. Width3 returns5
without a store. No hardware claim: address0 writability and untrusted caller
reachability are unknown. Test: evidence/firmware-audit/20260914-svc7c/test_null.py;
log: docs/action-logs/2026-09-14-svc7c-null-test.md. Not a verified VCN unlock.

## Latest G7: svc7C does not expose mapper slot argument (2026-09-14)

0x5A88 saves SVC r1 as the store VALUE and explicitly sets mapper r1=0.
SVC7C t28 value1 therefore maps through slot0, local0x0100C004/0x0101F8A4,
not slot1. The slot0x14 escape proposal is retracted; no caller-controlled
slot or cross-processor physical alias proved. Supersedes frame-boundary
entry below. Evidence: docs/action-logs/2026-09-14-psp-svc-vector.md.

## PSP SVC mapper frame boundary (2026-09-14)

0x2FCC maps t28 r1=1 calls to 0x01100000-frame addresses. A hypothetical
r1=0x14 would yield 0x02400000+low20, the VCN discovery frame, and the mapper
does not show an obvious upper-bound check on caller_r1. No existing signed
caller has attacker-controlled r1; changing t28/t02 is signature-blocked.
This is a boundary lead, not a proven unlock. Details:
docs/action-logs/2026-09-14-psp-svc-vector.md.

## PSP in-image SVC dispatch found (2026-09-14)

t02 body ARM vector+8 ->0x240 -> pointer0x4445 ->Thumb0x4444 ->0x45A0.
svc0x7C jump-table entry0x4690=0x744 ->0x4D28 ->0x5A88 via0x4D5E.
Historical on-die-only assumption is unsupported; active vector-base state
still unknown. Historical branch target0x128 corrected to0x240. No hardware
action. Evidence: docs/action-logs/2026-09-14-psp-svc-vector.md.

## 4700S t28 donor closed (2026-09-14)

Scope correction: only the selected function/table is equivalent; the whole
t28 donor track is NOT closed. BC250 entry0xFEC8; service implementation
location remains unresolved. Missing exact constants do not rule out computed
registers or another path. Interpret the historical wording below narrowly.

C0A t28 (e5970657...) and BC250 t28 (ebd9a7d2...) use equivalent Thumb
`svc #0x7C` sequence: write `0x0900C004/0x1F8A4`, zero five `0x1F8C4..D4`
entries. Both tables are zero; neither contains bank-12 `0x0900C830/834`.
4700S supplies no hidden nonzero VCN carrier. Comparative result:
docs/action-logs/2026-09-14-t28-donor-reconciliation.md.

## PCD55/68 default storage mapped (2026-09-14)

Version6 database at BC250 SPI0xEDD774 / C0A0xE6A404. Get8 tokens68/55
have UINT8 DATA descriptors0100057A/01000593, both in uninitialized
database storage (not valid raw-SPI default bytes). Zero-initialized defaults
match; runtime/SKU setters and active database selection remain to verify.
No demonstrated donor policy-value advantage. Detailed evidence:
docs/action-logs/2026-09-14-pcd-token-diff.md.

## G7 PCD getter width and E370 transport (2026-09-14)

GUID06E81C58... matches EDK2 PCD_PPI. IA32 method+4 is Get8, not GetBool;
token55/68 returns a byte used in arithmetic, not merely a Boolean gate.
E370 is passed to SMN write helper8EC/8ED, not a PCD setter. The earlier
'PCD Boolean / E370 token write' description is retracted. PcdPeim located
in both images; database mapping remains open. See2026-09-14-pcd-token-diff.md.

## PCD-gated NBIO routing lead (2026-09-14)

4700S and BC250 Gfx PEIMs use identical PCD GUID
{06E81C58-4AD7-44BC-8390-F10265F72480} and RMW the same `0xE370` configuration
token, but the Boolean gate token is `0x55` in C0A versus `0x68` in BC250.
This is the strongest BIOS policy difference found so far. Token names are
namespace-specific and unresolved; swapping numbers is unsafe without mapping
the PCD databases. See docs/action-logs/2026-09-14-pcd-token-diff.md.

## BC250 already contains donor NBIO copy path (2026-09-14)

Corrected-TE-RVA decode confirms BC250 Gfx PEIM5EB..690 implements same
13B1005C/60->6A140/144 and13B00084/4C->6A14C/148 masked operations as4700S.
Memory-setup conditional flag also present. Not a missing donor sequence.
Later interface token55(C0A) vs68(BC250) remains namespace-dependent,
not proven configuration mismatch. See2026-09-14-donor-bios-4700s action log.

## 4700S post-UMA NBIO copy path (2026-09-14)

C0A Gfx PEIM reads13B1005C/60 and copies to6A140/144, then RMWs6A14C/148
using reads13B00084/4C. Helpers862=read,8EC=write,91A=RMW (RVA).
TOP_MEM-derived6A150/154/158 and33E0 also touched under setup flag.
Observed routing/memory setup, not proven VCN isolation. Compare BC250
consumers before patching; do not transplant donor values. Listing:
evidence/firmware-audit/20260914-4700s/gfx-nbio-path.txt.

## 4700S compact Gfx PEIM entry traced (2026-09-14)

C0A GfxARIPei entryRVA0x240/file0xA0 (TEdelta0x1A0) walks memory HOB
descriptors and sets UMA parameters; strings and branches independently align
under the corrected VA->file conversion. Attribute2 and 2GiB-size adjustment
observed; token0x4B semantics unknown. Not yet a VCN-unlock site. Existing
disasm_x86_te.py linear header decode is unsuitable for entrypoint claims.
Evidence: docs/action-logs/2026-09-14-donor-bios-4700s.md.

## G7 TE relocation bounds (2026-09-14 donor audit)

Direct headers of C0A/BC250 GfxARIPei and BaseARIPei show valid .reloc
raw extents after subtracting StrippedSize-40. Earlier conclusions that
relocations were beyond EOF/stripped are retracted for these exact files.
GfxARIPei text sizes5759 vs85423; BaseARIPei16718 vs96174. Difference is
real text-section content, not itself proof of VCN removal. Evidence:
docs/action-logs/2026-09-14-donor-bios-4700s.md.

## 4700S C0A donor comparison (2026-09-14)

Hashbb2cf51d... 16MiB C0A: matching catalog checksums/four FVs,245 extracted
executables. Only one plausible PSP directory found; no type24/45 there,
unlike BC250. SMU helper range0x29F8..0x2AEF and bank230 array0x150B0..0x15124
match BC250 byte-for-byte; full SMU body differs. Not a proven working VCN
donor and no transplant performed. Evidence: docs/action-logs/2026-09-14-donor-bios-4700s.md.

## Fresh chip identity (2026-09-14)

Two CH347T/W25Q128.V16MiB reads match byte-exact (cmp0), SHA-256
c0f5f1c59cd0503d99cec9fffc5b95c8897a2deabfa42dd389c924d6be6cc4de.
Firmware from0x20000 onward matches d20-restored D10R.335 differences below
0x20000, last0x1B8C. This supersedes stale D19-on-chip assumptions.
Four FVs and PSP/BHD/APCB checksums pass; DFG0x007FFF00. No flash write.
Evidence: evidence/programmer/reads/20260914-identification/ and
docs/action-logs/2026-09-14-programmer-identification.md. Current boot/VCN unrun.

## Custom VCN patch coverage rechecked (2026-09-14)

Retained0011 (274f7dbc...) makes mode1 hardware callbacks no-ops and sets
num_enc_rings=0. Mode2 uses real VCN/JPEG callbacks; VCN-specific direct
placement supersedes0009's global-fw_load_type recommendation. Patches0009-0011
do not implement Cyan Skillfish DPM VCN power callback. Installed1.92 module
identity remains unknown; no loose matching binary found in scoped inventory.
See docs/action-logs/2026-09-14-driver-start-contract.md.

## Public-driver VCN enable no-op (2026-09-14, source comparison)

Linux v6.8 smu_dpm_set_vcn_enable returns0 when dpm_set_vcn_enable callback
is NULL. Same-version Cyan Skillfish pptable initializer omits that callback.
Thus generic success does not prove an SMU VCN enable request occurred.
Installed custom7.2 driver equivalence remains unverified. This is a missing
implementation path, not an unlock. See docs/action-logs/2026-09-14-driver-start-contract.md.

## VCN startup ordering audit (2026-09-14)

Retained vcn_v2_0_start calls DPM enable then selects DPG/static startup;
non-DPG path writes PGFSM_CONFIG before polling/POWER_STATUS reads.
A read-first userspace all-ones baseline is not the full driver sequence.
Retained cyan_skillfish_ppt.c has no VCN-specific map/callback entry;
shared-framework fallback and actual installed binary remain to verify.
No inferred permission for blind MMIO writes. Evidence and hashes:
docs/action-logs/2026-09-14-driver-start-contract.md.

## G7: do not combine mismatched VCN experiments (2026-09-14)

S2-A cycle4 logged 59 writes but its runbook uses the incorrect short VCN map.
Aug25 full ladder uses matching VCN2 offsets but does not establish identical
same-session gasket preparation. These cannot jointly prove the corrected
full sequence failed. Stage5 deployed source/output retrieval remains needed.
Read-only SSH attempt returned No route to host; present board firmware/power
state unknown. See docs/action-logs/2026-09-14-vcn-mmio-map-audit.md.

## G7: short MMIO arbiter uses conflicting VCN offsets (2026-09-14)

read_vcn_direct.py labels dword0x78CA/byte0x1E328 as UVD_VERSION.
VCN2 Linux v6.8 header instead uses base-index1+0x5C9; with recorded
base1=0x7E00 the byte address is0x20F24. POWER_STATUS/STATUS/SCRATCH9
also disagree. Short-probe values cannot prove those named register states.
The archived full enable_vcn.py ladder uses matching VCN2 offsets and
also reports all-ones, so not all negative results are invalidated.
See docs/action-logs/2026-09-14-vcn-mmio-map-audit.md. No hardware operations.

## G7 correction: VCN firmware header parser (2026-09-14)

Existing `enable_vcn.py` uses offsets inconsistent with Linux
`common_firmware_header`: it reads a 64-bit version at +0xC instead of the
u32 `ucode_version` at +0x10. Exact `navi10_vcn.bin` correct parse is
header 1.0, IP 2.0, ucode `0x08118009`, size 404288, offset 256,
CRC32 `0xE99D512A` (payload CRC verified). Prior displayed 64-bit version
claims and any direct-load interpretation based on them are retracted.
See docs/action-logs/2026-09-14-metrics-producer.md.

## VCLK/DCLK source-mode fields traced (2026-09-14)

0x2387C refreshes slot record+0x18/+0x19 from control+0x20 bits[2:0]/[17:16]
and record+2 from control+0x24 bits[26:20]. 0x2375C programs source mode;
0x2362C updates record+2. 0x23CB4 then calculates the metric float.
Zero VCLK is conditional on source/divider state, not a direct rail reading.
See docs/action-logs/2026-09-14-metrics-producer.md; static evidence only.

## Metrics writer decoded with local Xtensa trial (2026-09-14)

Imported SLEIGH definitions compiled locally with flix_i20 compatibility field;
0x23CB4 now decodes through all return paths. It writes slot record+8/+12,
including an explicit zero path when record+0x18==0 and record+2==0.
VCLK/DCLK metrics consume record+8; zero export alone is not rail-off proof.
See docs/action-logs/2026-09-14-xtensa-decoder-trial.md. No hardware operation;
floating-point p-code fidelity still unverified.

## Metrics-backed clock names (2026-09-14, static comparison)

Linux v6.8 cyan_skillfish interface-v8 header gives VCLK/DCLK offsets
0x4A/0x4C, matching PMFW 0x29AEC stores and 244-byte structure size.
Sources 0xFA1C/0xFA00 are respectively slot23/slot22 record+8, both domain6.
SOC field+0x48 comes from slot13 record+8 (0xF904), domain1.
Thus static evidence now links slots 23/22 to VCLK/DCLK under that interface.
No current clock or codec validation; slot24 unnamed. Details and provenance:
docs/action-logs/2026-09-14-metrics-producer.md.

## Metrics producer located (2026-09-14)

Static table6 export callback pointer at 0xCB34 resolves to 0x29AEC in body
5c805026.... Producer converts state floats to 16-bit metrics using 1000.0f;
buffer 0xCB54 fields +0x48/+0x4A/+0x4C use sources 0xF904/0xFA1C/0xFA00.
Exact driver-interface header needed before assigning VCLK/DCLK names;
this is not proof of physical clock measurement. See
docs/action-logs/2026-09-14-metrics-producer.md and preserved decode.

## Reproducible full slot/domain map (2026-09-14)

evidence/firmware-audit/20260914-smu-address-trace/slot-domain-map.json
contains 27 slots/eight domains; SHA-256 58a7042c863767db9f817b8b129f7cf440eaea732c9e195e7383871f55293dce.
Hash-pinned extractor verifies exact body identity against D19 readback.
Slots 22/23/24 use 0x6D100/128/150 and domain6, but VCLK/DCLK names
remain unproven. Historical VCN labels are not independent proof that
domain6 is exclusively VCN or that only bridge/isolation remains to fix.

## Latest G7: clock-slot indices are not power-domain indices (2026-09-14)

Exact decode of 0x2362C maps its input through a stride-28 slot record
before passing the mapped byte to 0x23B14. Slot base 0xF790; domain base
0xF550 stride72. In body 5c805026..., slots 14/15/17 map to domains 2/3/4;
slots 22/23/24 map to domain6. The old claim that Q3 0x5C powers domain14
is retracted. Timeout observations do not establish denial of a correctly
identified VCN domain. See docs/action-logs/2026-09-14-slot-domain-audit.md.

## Feature framework correction (2026-09-14)

Feature 4 callback `0x23C24` is labelled `PLL_POWER_DOWN` in the captured
table; feature 21 `0x2496C` is `PROCHOT`. Both install periodic callbacks
through `0x1B1E4`, not direct VCN power-on. No inspected feature bit is
identified as VCN enable/isolation release; speculative feature-mask sweeps
are unsupported. See docs/action-logs/2026-09-14-smu-window-followup.md.

## G7 correction: message 0x21 handler re-decoded (2026-09-14)

Fresh Xtensa decode of PMFW body shows Q3/message `0x21` handler `0x249DC`
does not call `0x23B14`; it calls `0x2494C`, which performs frequency float
arithmetic and state storage, then returns status 1. The historical note
claiming `0x21` was a sendable PowerUpDomain command is retracted. The
confirmed domain-14 power path remains handler `0x5C` at `0x1F038`.

## Latest G7: C230 array location (2026-09-14)

Direct byte scan in body 5c805026... finds 0x0900C230 at body 0x150C0,
array index 4 from 0x150B0. 0x151C0 was wrapper-relative, not body-relative.
Neighbor entries are other 0x090xx230 banks. Missing C234/C830/C834 literals
does not exclude computed register addresses or a PMFW VCN recipe.
Consumer investigation: docs/action-logs/2026-09-14-smu-window-followup.md.

Function 0x1DD74 consumes the 29-dword array via pointer literal 0x17390.
It writes zero for each nonzero entry at 0x01000000+(entry&0xFFFFF), hence
0x0100C230 for index 4. This local base differs from both 0x01100000
native domain accesses and 0x02C00000 selected accesses. Physical aliasing
and execution timing unknown. No direct callers found by existing scanner
over [0,0x3A000); inspect indirect references next. Static evidence only.

## Latest G7: do not conflate native and mailbox write paths (2026-09-14)

Supersedes `Critical SMN destination correction` below. D19 Q3 0x2C calls
0x2A74, not 0x233E8. No call edge between those primitives was demonstrated.
The 0x2A74 selector-based local window is 0x02C00000+(address&0xFFFFF);
for C830 it is 0x02C0C830 with selector low16=0x90. Physical routing remains
unknown. The OTHER native primitive's hypothetical formula would give
0x0110C830, not 0x0110CC30. D19 does not prove a master/slave exclusion.
0x1B514 also has a caller at 0x24732 in 0x246F4; its special-range caller
is not unique. Evidence: docs/action-logs/2026-09-14-smu-window-followup.md.

## G7 window decode correction (2026-09-14)

Q3 0x98 is not a state-table updater: for a nonzero argument it calls
0x2A74(0, argument, 0xFF, 2), then 0x29F8(0, argument, 2). These helpers
perform window write/read. Q3 0x2C uses the same write helper with caller value.
The low-20-bit address mask is accompanied by a separate selector update at
0x03220038; do not infer aliasing or lost high bits from the mask alone.
Body SHA-256 5c805026... equals D19 SPI+0x8FF100 (not +0x8FF200).
Detailed evidence: docs/action-logs/2026-09-14-smu-window-followup.md.
No new hardware operations; physical window routing remains unresolved.

### PMFW literal scan (2026-09-14)

Exact PMFW body scalar scan finds no little-endian literals `0x0900C234`,
`0x0900C830`, or `0x0900C834`; only native window base `0x10FFE00`, bounds
`0x5AFFF/0x5B7FF`, and selector `0x03220038` are present. The VCN bank values
therefore enter through x86/PSP gasket data or caller arguments, not an obvious
hardcoded SMU recipe. No hardware operation was performed.

### PMFW nearby control literal (2026-09-14)

Byte scan finds one PMFW literal `0x0900C230` at body offset `0x151C0`.
Its surrounding bytes are not a valid decoded function entry and no xref is
proven; it is only a lead near the D19 target. Exact `0x0900C234/830/834`
remain absent from PMFW.

### G2 static result: second-core IPC path (2026-09-14)

SMU `0x1B514` is an internal IPC wrapper: it packages two arguments and sends
message `0xFE` through dispatcher `0x10D0`; it performs no local SMN write. The
retrying sibling `0x1B4F8` uses operation `0x08` and retries on `0xFFFFFFFF`.
The only proven caller remains the special-range branch in `0x233E8`; no direct
Q3 exposure or safe caller payload for user-controlled VCN addresses is known.

### Critical SMN destination correction (2026-09-14)

Full decode of SMU primitive `0x233E8` shows normal addresses are directly
stored at `0x10FFE00 + (addr & 0xFFFFF) + 0x200`; only `0x5AFFF..0x5B7FF`
uses IPC `0x1B514` to the second SMU core. `0x0900C830` is outside that range
and resolves to master-side `0x0110CC30`. The earlier generic `0x02C00000`
destination interpretation is retracted. D19 therefore tested a master-side
direct store; alternate-core/window ownership remains an open VCN vector.

## Scope and current baseline

- Current operator artifact: `dump/2.bin`, 16 MiB, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`. It is a structural control, not proof of chip identity, contact, bootability, or recovery.
- Four archived capture sets under `archives/imported/loose-tmp-bc250/flash_archive_FULL_20260901-140856.tar` each state that two complete reads matched byte-for-byte. The archive SHA-256 is `3b6c5455433285f086899eabd2e35a108b4253525e95faec6484e19b31fc51a5`; root independently verified all four member hashes against their manifests.
- `dump/2.bin` differs from the first archived `spi.bin` by 3,071 bytes in 46 ranges, all within the first `0x20000` bytes (maximum changed byte `0xAB22`). PSP/BHD/APCB and firmware region `0xAE0000..0xE00000` are byte-identical. This is corroboration of the firmware region only; fresh operator reads and exact programmer/chip metadata are still required before a hardware write.

## Root-verified parser/extraction

- `scripts/firmware_audit.py` is a path-parameterized, standard-library-only read-only adapter. Its output is under `evidence/firmware-audit/`. It honors PSP/BHD Fletcher32 spans, APCB byte checksum, FV extended headers, 8-byte FFS alignment, GUID-defined/EFI LZMA, freeform subtype sections, and the top-level `SECURITY_CORE` FFS.
- Exact dump parse: PSP/BHD/APCB checksums match; four valid FVs with filesystem GUID `8C8CE578-8A3D-4F1C-9935-896185C32DD3`; 234 executable bodies (179 PE32, 55 TE). This count matches the independent same-input UEFI walk.
- Compared with the historical `BC250_3.00.ROM`: 233 common module GUID/UI/type records; 231 common body hashes match; `AMITSE` and `Setup` differ; dump-only module is `Bc250CoreUnlockDxe`, GUID `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, 12,288 bytes, body SHA-256 `7d22d80284cd4c9c8af997611002f6916b4fa4b0d3ca9e3e34e450abbe885c55`.
- The dump-only module corresponds to imported `BC250-DXE-SMU-Core-Unlock`. Its source statically reads SMN `0x0115A870`, conditionally sends Queue-3 message `0x98`, verifies `0xFF`, and requests a warm reset. This is `static-analysis`; execution on the board is unverified.
- Exact VCN IP discovery payload at flash `0x981A00` parses as one die with 38 IP records. VCN record: HWID 12, version `2.0.3`, harvest `0`, bases `0x7800`, `0x7E00`, `0x02403000`. No dedicated VCN firmware entry appears in the 19-entry PSP directory. This proves a descriptor, not codec operation.
- PSP type `0x08` SMU blob at `0x8FF000`, full size `0x40200`, SHA-256 `6a3da1ef6024c3143283fb92468fd71d628e9402a751c4a9799a20f473549ad9`; its body after the `0x200` wrapper is byte-identical to the imported Robin3 type-8 body (SHA-256 `f546f1188e9f72401282a065ac0a6dcbb8a48a2c7cf999ae7b99c85ed148e75b`).
- `$PS1` gasket at `0x982000`/`0x2E50` and policy at `0x9CA400`/`0x6E0` are byte-identical to imported Robin3 blobs. Direct static parsing finds `0x03E810=0`, clamped DF values, and no HWID-12 `0x0900Cxxx` bank writes.
- APCB `0xAB1000`, size `0xB70`, instance stamp `+0x0C=0x220E`, checksum byte `+0x10=0xF2`; DFG words at `+0x130` and `+0x16C` are stock `0x001FFF00`. The old imported claim that checksum is at `+0x0C` is disproved and must not be reused.

## Tool validation

- CutterMCP_native v0.1.6 was tested on `/usr/bin/true` and returned loopback health, MCP initialize, tools/list, function/segment/string/bytes/disassembly queries. A second run on the loaded fixture returned HTTP 200 read-only results: 28 segments, 36 functions, 137 strings.
- Bundled Rizin `0.9.1` commit `c3a90e9226d977f58f4e9c75f78fa6b07afe13c7` analyzed 16 copied dump modules in `evidence/firmware-audit/rizin/`; all commands exited 0. Rizin reports TE inputs as `endian=BE` despite little-endian TE headers, so TE instruction semantics require an independent check.
- CutterMCP-plus standalone wrapper can query the native server but has a `disasm_by_func_json` response-handling bug and client-side filtering/pagination weakness. It remains baseline/reference, not the default runtime.

## Evidence matrix and unresolved claims

- `observed-bytes`: dump structure, hashes, module bodies, IP-discovery descriptor, SMU identity, APCB/gasket/policy values.
- `static-analysis`: module control flow and source correspondence; Rizin output; existing source traces.
- `emulated-or-host-tested`: historical Linux driver probe/ring-test attempts and archived host logs; ring tests timed out and no codec success was shown.
- `hardware-verified`: no fresh current-board VCN encode/decode, power-domain, MMIO, memory-clock synchronization, or candidate boot result.
- VCN enablement remains a multi-gate problem: discovery descriptor, PSP-applied SEC_GASKET/NBIF aperture, SMU power/clock, VCN firmware compatibility, driver registration, MC/coherency/ring bring-up, and user-visible codec test. APCB DFG alone is not yet proven sufficient.
- FCLK/UCLK/MCLK settings in historical NVRAM analyses are controls/candidates, not live-clock proof. Current dump contains Auto fields; active extended-CMOS UMA split is not captured by SPI.

## Safety state

- No firmware, register, programmer, hardware, or global MCP configuration write was performed. Mutation-capable CutterMCP tools were not called.
- Historical D3-B/D3-B2/D3-C, unsigned gasket, OC profiles, and `BC250_VCN_UNLOCKED.ROM` remain non-flashable research artifacts.
- Next decisive work: module-specific native MCP read-only calls on exact extracted copies; then independent static reconciliation and, only if still justified, a new APCB-only candidate from a matching fresh baseline.

## Operator scope update (2026-09-11)

- The operator authorizes building and validating DXE/BIOS candidates in new files and can supply a fresh programmer dump before any flash. This does not authorize flashing.
- Optional JTAG-assisted runtime debugging is available, but JTAG is read-only by default; target-memory or register writes require separate explicit approval and logging.
- Board-view evidence identifies J4004 as SPI, J5 as UART, TPMS1 as LPC/POST debug, and I2C_HEADER1 as SMBus. These are historical CAD/parse findings and do not establish physical pin orientation, voltage, or a JTAG interface.
- Active project plan with separate VCN and memory/SoC-voltage tracks: `specs/2026-09-10-bc250-firmware-audit.md`.

## Board-view correction: J2 JTAG candidate

- Direct parsed CAD evidence identifies J2 as a CPU JTAG/debug header: `CPU_TCK` pin 2, `CPU_TMS` pin 4, `CPU_TDO` pin 8, TDI via `J2.6 -> N22562912 -> R19 -> CPU_TDI`, and TRST# via `J2.9 -> N22563682 -> R120 -> CPU_TRST#`; pins 1/19 are labelled `+1.8V`, pins 3/5/7/17 GND.
- This corrects the earlier incomplete statement that no JTAG connector had been identified. It remains CAD-derived; population, orientation, live voltage, debug security state, and safe attach behavior are unverified.
- Normalized evidence: `evidence/boardview/bc250-connector-map.json`.

## Memory/SoC-voltage static baseline (2026-09-11)

- Current `AmdSetup` NVAR record begins at flash `0x4BB`; its body begins at `0x4CF`, length `0x8B5`, and SHA-256 `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`. Direct bytes show `MemoryClockSpeed +0x316=0xFF`, `Tcl +0x317=0xFF`, `UclkDiv1M0 +0x330=0xFF`, `FCLK_DPM +0x6A3=0x0F`, `VDDCR_VDD offset +0x6E6=0`, DF clock `+0x704=0x03E8` (1000), CPU frequency `+0x701=0x0E10` (3600), FAST_PPT `+0x70C=88000`, SLOW_PPT `+0x710=65000`, VRM current `+0x718=65000`, and VRM maximum `+0x71C=95000`.
- Four historical `recon/oc_profiles` images parse structurally, but each has a different full-image/PSP/APCB baseline and static AmdSetup edits. Their profile fields are evidence of encoded settings only; they do not establish live clocks, voltage, training, stability, PSP acceptance, or bootability.
- Machine-readable record: `evidence/firmware-audit/oc-profiles/comparison.json`, SHA-256 `c473547d114797c2087d4264c75c3ac0ce39daa398bb7cd3ab4a364d16d091c4`.

## NVAR parser state (2026-09-11)

- New path-parameterized parser: `scripts/nvar_audit.py`, SHA-256 `c5a634341ed682982a1ec28c8beee3df36ef13c7c3e770073099e3fc467b225f`. It emits bounded NVAR metadata and selected typed non-secret fields only.
- Current primary-store report: `evidence/firmware-audit/dump-2-nvar-primary.json`, SHA-256 `d48d010b0175bd5fdc49cac7e581085e8eed6c688fe234a87898a0e5ebeaccba`; it finds `AmdSetup` at `0x4BB`, body at `0x4CF`, and independently matches direct field reads.
- The primary NVAR store has an unused/corrupt tail with three unterminated names in the bounded region. This does not affect the complete `AmdSetup` record but must be preserved as an open structural caveat.

## Existing VCN DXE source/binary safety classification (2026-09-11)

- Imported `Bc250VcnUnlockDxe.efi` (SHA-256 `95b7078285e377a721a0f821552091d541ceb7e95924b8e524f7ed9587747d3d`) and `Bc250VcnProbeApp.efi` (SHA-256 `59e9fc56c995ba849b19904401fb6226850aa07abd6fb97fee70d34242c728db`) were statically analyzed.
- Their source contains Q2/Q3 mailbox, SMU SRAM, privileged SMN gasket/DF, VCN power/clock, and GPU PCI-command writes; the probe also chainloads a bootloader. They are not read-only probes and are not to be injected/executed on hardware without a separately approved, logged experiment.
- `PerformSmuUnlock()` skips the verification read but later prints `ProbeVal`, which is not initialized on that path; that log cannot prove unlock.
- Reports: `evidence/firmware-audit/rizin/dxe/manifest.json`.

## SEC_GASKET payload boundary and VCN delta (2026-09-11)

- Current type-36 `$PS1` wrapper at `0x982000` contains the SEC_GASKET payload at wrapper offset `0x100`, size `0x2C50`, followed by `0x100` trailing bytes. Payload SHA-256 `d16f7dacfd9b38ea47e3cde8b9754183eeb3a97076244702a0dd980eb53fd52c` and group parse exactly match imported Robin3.
- Current group counts are `0x201=1230`, `0x203=31`, `0x210=13`, `0x280=100`, `0x281=31`; no current write targets `0x0900Cxxx`.
- The rejected unsigned VCN artifact adds 56 HWID-12 range writes (51 in `0x201`, 5 in `0x280`); historical Cezanne donor has a different layout and `0x03E810=0x6`. These are static donor deltas only.
- Machine-readable summary: `evidence/firmware-audit/ps1/sec-gasket-summary.json`, SHA-256 `4f65e194236728476789f7b9dc438ca0eed2825a01c28f67586a072da210235d`.

## Voltage control-byte correction (2026-09-11)

- The current AmdSetup has `VDDCR_VDD Voltage Offset Control +0x6E5=0`, `VDDCR_VDD Offset +0x6E6=0`, `VDDCR_GFX Voltage Offset Control +0x6EA=0`, and `VDDCR_GFX Offset +0x6EB=0`. Historical profiles 02/03/ULTIMATE set only the VDD control/value pair to `1`/`35`, `1`/`80`, and `1`/`100` respectively.
- These are encoding observations; they do not establish safe voltage, actual rail voltage, SMU acceptance, or silicon stability.
- Updated comparison: `evidence/firmware-audit/oc-profiles/comparison.json`.

## AmdSetup control/value map correction (2026-09-11)

- `DF Clock Override Control +0x703=0xFF` (Auto) is distinct from `DF Clock Override +0x704=1000` (u16). The machine-readable IFR/NVAR map is `evidence/firmware-audit/amdsetup-ifr-field-map.json`, SHA-256 `75bba663cf28a61e7643fed3c07e77051f552ae89917bc4f4091fd1b2bcfb96d`.
- Any future static candidate must treat control bytes and value fields as a coupled pair and must not infer effect from changing the value alone.

## APCB detail and memory-profile relationship (2026-09-11)

- `scripts/apcb_detail.py` (`80ea1708836ddee07747c7e507c908af08a7c9dbece197bfb4a6463879914711`) and `evidence/firmware-audit/apcb-detail.json` (`d77ed671b723100c25ccf1e3265362ade799b00904bed621dc9bca9bf0336666`) provide subgroup/token-level APCB evidence.
- Current APCB DFG has instances 5/6, each 13 token rows; MEMG has instances 7/8/49/80/82/83. All four historical OC profiles have identical DFG/MEMG subgroup body hashes to the current dump.
- Therefore the imported OC profiles encode their frequency/voltage edits in AmdSetup/NVRAM rather than MEMG/DFG. Their different PSPG/CBSG/APCB sizes make them unsuitable as current target baselines.

## Critical source/binary provenance correction (2026-09-11)

- The exact current dump-only `Bc250CoreUnlockDxe` body (`7d22d80284cd4c9c8af997611002f6916b4fa4b0d3ca9e3e34e450abbe885c55`) is not an exact match to retained `upstream/BC250-DXE-SMU-Core-Unlock/.../Bc250CoreUnlockDxe.c`.
- Independent `llvm-objdump`/Rizin analysis confirms the expected SMN `0x0115A870` -> Q3 `0x98` -> response `0x01` -> mask reread -> warm-reset path, but also reveals a Setup-variable gate: read `Setup`, compare dword at `Setup+0x1C4` with `0x157C0`, and skip the Q3 path when equal.
- The retained source therefore provides a partial semantic reference only. The current binary's exact source/revision and its Setup gate remain unresolved. Any dispatch or unlock claim must use the exact body disassembly, not the retained source alone.
- Clean corroborating report: `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.functions.txt`, SHA-256 `d02d5890c9e3d60faf16408a69551e7d15e6851e19d736ba3e583758309e360f`; `llvm-objdump` report `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.llvm-objdump.txt`, SHA-256 `399ae5a8fb37d93dfb98d3a258a2c29c1bad5e51aff593bdf5f30321bb466242`.

## CoreUnlock Setup gate correlation (2026-09-11)

- Current active NVAR `Setup` is at `0xD84`, body size `0x1D3`; its `+0x1C4` dword is `0x00011940` (72000). The exact binary compares this field to `0x000157C0` (88000), so the observed current value does not meet the skip equality.
- Historical IFR labels `Setup+0x1C4` as `Cooler and Quieter operation` with options `0x57C0`/`0x1940`; this does not explain the binary comparison and remains a contradiction.
- Do not infer the binary's guard intent or execution outcome from the retained source.

## VCN/APCB module scalar scan (2026-09-11)

- Direct little-endian scalar scan report: `evidence/firmware-audit/rizin/vcn-apcb-static-constant-scan.json`, SHA-256 `066bf18889edef6df8f8daad91721101b62e0f92da863e2168f0ee8868c1fef9`.
- `AmdApcbObrDxe` contains APCB group IDs `0x1701/0x1703/0x1704/0x1706/0x1707` and DFG wildcard `0x001FFF00`; `AmdFabricAriDxe` contains DF indirect-window/control constants `0xE0000000/0x405C/0x4098`; `AmdNbioSmuV10Dxe` contains Q2 mailbox register constants; `CbsSetupDxe` contains AmdSetup offset constants and DFG wildcard.
- Scalar presence is static evidence only, not proof of which writes execute.

## APCB-only calculation preview (2026-09-11)

- In-memory preview confirms the proposed DFG words and checksum arithmetic on the current structural dump: only APCB byte offsets `+0x132` and `+0x16E` plus checksum `+0x10` would differ; checksum becomes `0x32`.
- `evidence/firmware-audit/apcb-only-calculation-preview.json` (`d2d109a208acfb70c3b4664ecbb2f241e271e92ebeba95d344123126717bea30`) records the result. This is not a candidate BIOS and does not establish PSP acceptance/bootability.

## G7 correction: current Setup HII values include high bit (2026-09-11)

- The previous note saying that `Setup+0x1C4` IFR options `0x57C0`/`0x1940` did not explain binary `0x157C0` was wrong. Direct bytes in the current `Setup` PE32 (`e3ff0b804acbc5c308f4e9c7a13e8ba4c69b66653b5091423e78d97d76117f6f`) show full u32 option values `0x000157C0` and `0x00011940`; the historical IFR text formatter omitted the high `0x10000` bit.
- Current NVAR `Setup+0x1C4=0x00011940` still does not satisfy the binary skip equality `0x000157C0`. The guard is consistent with a `Cooler and Quieter operation` option; exact label mapping follows the historical option order.
- The corrected binary summary is `evidence/firmware-audit/rizin/Bc250CoreUnlockDxe.corrected-summary.json`.

## Host programmer interface observation (2026-09-11)

- Host `lsusb`/`udevadm` observed WCH/QinHeng `1a86:55db` (`USB To UART+SPI+I2C`) as `/dev/ttyACM0`, with vendor-specific USB interface. Serial values were not read or stored.
- This does not establish flash-chip identity, voltage, physical contact, programmer protocol, or read/write authorization.

## Programmer identity update (2026-09-11)

- Operator screenshot config: CH347T, `SPI_FLASH`, `WINBOND W25Q128BV`, `16 M`, page `256`, block `64 K`, `3.3 V`, 4-byte addressing `No`. Screenshot preserved as `evidence/programmer/imsprog-chip-selection.png`.
- Host identifies WCH/QinHeng USB `1a86:55db` as `/dev/ttyACM0`; installed IMSProg package is `1.9.1-1`, GPL-3.0-only.
- Chip JEDEC detection, two fresh full reads, chip marking/orientation, adapter/clip contact, and board power isolation remain unverified. No programmer operation has been issued.
- Manifest: `evidence/programmer/imsprog-preflight.json`, SHA-256 `9e56fd4c85169fe6c3ff16a64dcbaf94b72817fc08e6786323d8a8f9845cf13b`.

## CoreUnlock native MCP evidence (2026-09-11)

- Native MCP v0.1.6 read-only trial on the copied CoreUnlock body passed: current address `0x11037`, 2 segments, 5 functions, disassembly/decompile/detail/vars/xrefs/bytes all HTTP 200 with `isError=false`; three mutation tools were not called.
- MCP decompile confirmed the exact Setup guard and Q3 sequence; it emitted variable-overlap warnings, so Rizin/`llvm-objdump` remain corroborating sources.
- MCP string filtering did not return UTF-16 `Setup`/`SMU` strings while raw bytes/Rizin did; this is a tool-coverage difference.
- Transcript manifest: `evidence/firmware-audit/mcp/Bc250CoreUnlockDxe-20260911/manifest.json`, SHA-256 `3df026be426c0fda0ebdf6a80ae041f4846f788ee5def841268969cc0d6f3e0a`.

## Programmer CLI evaluation (2026-09-11)

- No dedicated IMSProg/CH347T MCP server found in bounded local/GitHub repository search; coverage is limited by GitHub API rate limiting and unavailable general web search.
- IMSProg `1.9.1-1` is GUI-only for operations; it accepts an optional `.bin` file argument but no documented read/detect CLI or MCP endpoint.
- Arch `flashrom 1.8.0-1` is available and pinned source commit `90b6b4376c7480a223e7bb5642e7116315ac6d09` has native `ch347_spi` support for the observed `1a86:55db` CH347T and 16 MiB Winbond family. Runtime trial not yet run.
- Research note: `docs/research/2026-09-11-programmer-cli-evaluation.md`, SHA-256 `27ffa5eb31b341d45613db4fc87da326decb6b0cde76c78ddb43fd00f6d3cc95`.

## Correction: programmer operation is no longer pending (2026-09-11)

Earlier entries saying that no programmer operation had been issued are superseded by the operator's later power-isolation confirmation and the read-only trial. A signed Arch `flashrom 1.8.0` package was extracted user-locally; `ch347_spi` probe found Winbond `W25Q128.V` (16 MiB) at `1.875M`; two independent full reads completed with exit 0 and match each other and immutable `dump/2.bin` byte-for-byte.

- Read baseline manifest: `evidence/programmer/reads/20260911/manifest.json`, SHA-256 `80b34cb2be1706abeac499d95cc4ae1d0c55b05183add75b015ad85780cccb60`.
- Fresh parser report: `evidence/programmer/reads/20260911/firmware-audit/inventory.json`, SHA-256 `e982f755981cac0231c52074872f6478005f9e4826e6063512c6664a963c76b4`.
- Fresh extraction report: `evidence/programmer/reads/20260911/firmware-audit/read-a-inventory-with-extract.json`, SHA-256 `e914cf3e72dd6726337838140515f85c5504183301f28d31e8f3d37890786053`; 234/234 module file hashes match the validated dump extraction.
- APCB-only candidate: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`; static only, not hardware-tested.

## Evidence maps and APCB candidate (2026-09-11)

- VCN map: `evidence/firmware-audit/vcn-evidence-map.json`, SHA-256 `ab683aaacfa77b71ec6404f714cb66b39210f6c57509f457082b5f09bbdc08b5`. It links the hardware-verified read baseline to IPDS/VCN descriptor, PSP type-8 PMFW, `$PS1`, APCB DFG, UEFI/Rizin literals, CoreUnlock MCP, and host-source stages, with explicit claim limits.
- Memory/SoC-voltage map: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, SHA-256 `6dae6540db6944e9a570b60db2293e8d26a3bcb27507c5693102882a00e2c34f`. It records exact AmdSetup fields, IFR types/options, APCB MEMG/DFG groups, UMC records, relevant module hashes, and historical OC deltas.
- APCB-only candidate: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`; static/parser verified only.
- No memory or SoC-voltage candidate built; no value recommendation made.

## Correction: AmdSetup NVAR name offset in memory candidate builder (2026-09-11T07:09:56.676244+00:00)

- First execution of `scripts/build_amdsetup_memory_candidate.py` failed before writing an output because the builder incorrectly assumed the UTF-8 NVAR name began at record `+0x0C`.
- Direct bytes at record `0x4BB` show `NVAR`, header bytes through `+0x0A`, then `AmdSetup\x00` beginning at record `+0x0B`; the parser's `name_length=8` agrees. No candidate file was created by the failed run.
- Correct the builder to validate `original[0x4BB+0x0B:0x4BB+0x14] == b"AmdSetup\x00"`, rerun, and independently verify. This changes only the builder validation, not any firmware source or candidate.

## Memory-clock candidate (2026-09-11)

- Built separate offline candidate `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`, SHA-256 `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee` from matching read baseline.
- Exactly one byte changes: `AmdSetup+0x316` / absolute `0x7E5`, `0xFF` (Auto) -> `0x23` (IFR-labelled 1750MHz). No UCLK/FCLK/voltage/timing/APCB/PSP/`$PS1`/BHD/FV field changed.
- Independent NVAR/full firmware validation passes; manifest `evidence/candidates/BC250_MemoryClock_1750_only_v001/build-manifest.json`, SHA-256 `f9c72180e2d67c0eef7c3128456dde87478b89d5b1a06d20f76e63539db4f61f`.
- Candidate is static only. Training/clock/stability/boot and independent review remain pending. SoC-voltage candidate remains unbuilt with no guessed value.

## Independent candidate reviews (2026-09-11)

- APCB candidate independent review: `evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md`, SHA-256 `90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905`; root rechecked the artifact.
- Memory candidate independent review: `evidence/candidates/BC250_MemoryClock_1750_only_v001/independent-review-gemini.md`, SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`; root rechecked the artifact.
- Both reviews pass static diff/parser scope and leave signature acceptance, bootability, runtime VCN, memory training, stability, and hardware write checks unrun.
- Updated maps: VCN `0b55855c7c6c383007d4e2a065950a3e7b247343da1640f2b8eb303940fdb386`; memory/SoC `9143f8c9cb48ed3cb1eb32d899347bc1de85d78ae5d01f74be687bab388dbf35`.

## Historical VCN runtime reconciliation (2026-09-11)

- Imported mode-1 log `archives/imported/recon-evidence/legacy-tmp-bc250-recon/vcn-probe-mode1_2026-08-26.out` (SHA-256 `920d82c67ddd3b937fba8f5fabc04ec532f0be10e42a9647baac3cca48fc970a`) reports VCN firmware discovery and `vcn_dec/vcn_enc0/vcn_enc1` ring setup, followed by all three IB ring tests timing out with `-110`. Mode-0 log is `0b7c04d489bf0efb1d0105d542da1a0cf3c370f5502d6aaefe40e1db344e6732`.
- This is historical hardware/log evidence, not current proof and not a causal diagnosis. Current board has not been booted in this session after the programmer capture.
- VCN map updated: `evidence/firmware-audit/vcn-evidence-map.json`, SHA-256 `7ad5f17b2b75c0e19a57ef3953e69be8c4b78a534e799406b7e2bdc89fbdf421`.
- Memory map updated with historical telemetry/source limitations: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, SHA-256 `215aafba73e28cdd5d22b4b328baa24f01db2853abc20cf47488fed0177e1460`.

## VCN DXE/probe safety classification (2026-09-11)

- `evidence/firmware-audit/rizin/dxe/manifest.json` records read-only Rizin analysis of imported `Bc250VcnUnlockDxe.efi`/`Bc250VcnProbeApp.efi`; static source/binary paths contain hardware writes and are not read-only probes.
- VCN map now includes this edge: `evidence/firmware-audit/vcn-evidence-map.json`, SHA-256 `0dc07ac65ada78a77b47ca68453e2a795468a2d742ee9254f853a926e9b96ec7`.

## Direct chip identity versus CAD label (2026-09-11)

- Current direct probe/readback identifies the attached chip as Winbond `W25Q128.V` (16 MiB); historical CAD labels BIOS_A1 as MXIC. Direct probe/readback takes precedence for this operation, while the CAD remains wiring evidence only.
- This does not independently prove PCB revision, physical marking, or clip orientation.

## Current evidence-map synchronization (2026-09-11)

- Current VCN evidence map: `evidence/firmware-audit/vcn-evidence-map.json`, SHA-256 `0dc07ac65ada78a77b47ca68453e2a795468a2d742ee9254f853a926e9b96ec7`; it includes historical runtime limits, SMU metric source traces, and VCN DXE write-capability classification.
- Current memory/SoC-voltage map: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, SHA-256 `2d0433c5dae972216bc55a0034724540331b49de4ed14321309012e097a057a8`; it includes current one-field MemoryClock candidate and SMU source trace.
- Candidate manifests remain APCB `5fb0aca877eb8583186f2f6861636ba7b70fc66404fa768dd6c4a408fda61c5a` and MemoryClock `f608e77530dc47cebf802e36c9cea300f792fa5764b2288572f17ae0831b3a0b`, both independently reviewed.

## Final current evidence snapshot (2026-09-11)

- Two matching fresh SPI reads are hardware-verified at the readback layer; common SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- APCB VCN candidate and one-field MemoryClock candidate are statically verified and independently reviewed; exact hashes are recorded in `candidates/README.md`.
- No SoC-voltage candidate is built. No flash, register/JTAG write, or modified-image runtime test occurred.
- Native MCP listener was stopped after the controlled CoreUnlock transcript; pending module MCP coverage remains incomplete due GUI control limitations.
- Current report draft SHA and maps are recorded at the end of `reports/2026-09-11-bc250-audit-hash-specific-draft.md`.

## Historical OC/SoC claim correction (2026-09-11)

- `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/CPU_MEMORY_OVERCLOCK_ANALYSIS.md` (SHA-256 `050041933ac0efe95399f2e81555b75b275fb3687b8a044772ec9effd4b755ea`) and related OC builder/docs remain historical leads, not authority for units, safe ranges, applied FCLK/UCLK, or post-profile latency.
- Current IFR/NVAR evidence identifies `VDDCR_VDD Offset` as an unsigned-looking IFR `u32` field at `+0x6E6` with separate control `+0x6E5`; historical `u8/i8`/mV descriptions are not accepted without consumer/encoding proof.
- Historical runtime telemetry has contradictory clock contexts and VCN ring failures; it cannot validate a current memory/voltage candidate.
- Memory/SoC map updated: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, SHA-256 `d93db2d4d5dd31627d949abc57182434c2e29e993f38496cb5df6527c556f442`.

## Root SoC-voltage semantics review (2026-09-11)

- Root review: `evidence/firmware-audit/soc-voltage-static-review-root.md`, SHA-256 `d9cfbaca981c33181b04c7f9bc17aed35192cad4e762763ae25a9809f56a341b`.
- `AmdSetup+0x6E5`/`+0x6E6` location, separate control, and IFR `u32` value width are PASS. Physical units/sign/encoding, exact SMU consumer, training dependency, and live rail response are INCONCLUSIVE/UNRUN.
- No SoC-voltage value is recommended and no SoC candidate is built. Memory/SoC map current SHA-256 `7c520f479332a3faa7790aee1917942ab48fabf588c44e621e3a50ded0a52f3c`.

## Runtime SMU API encoding context (2026-09-11)

- Imported `bc250_smu/api_q3.py` (SHA-256 `30464310e6c4f6146322dd0136255e7f6069c2c397509296e92519e0f0cd8c90`) exposes distinct current-voltage-in-mV, small VID-step, float-offset, and SoC-DPM-clock paths. `codec.py` (SHA-256 `bb747622598b92ff43f10583ef93803bda4d6ae59b2480e74fc2abf6751db116`) contains VID/mV and IEEE-float conversion helpers; `api_q2.py` (SHA-256 `a5da57c58230e4be02204efb8791ff49082fe7d4b78890d838c47439c0ee8f8d`) contains feature/droop paths.
- These are write-capable host APIs and were not run. They do not map the BIOS `AmdSetup+0x6E6` u32 to a specific protocol; they reinforce the no-guessed-voltage rule.
- Memory/SoC map current SHA-256 `5fb17da2fe66dfb2fb350a038894d1c3cdcc79795d47ad701b92bb741f04a9a6`.

## Derived-artifacts inventory (2026-09-11)

- Machine-readable inventory: `evidence/firmware-audit/derived-artifacts-20260911.json`, SHA-256 `0aef5680451ea1d96ff1ff279872f29762b90b7d3f05e9723f1ca2493630f6ba`.

## SoC-voltage encoding ambiguity artifact (2026-09-11)

- Host-side formula comparison: `evidence/firmware-audit/soc-voltage-encoding-comparison.json`, SHA-256 `3576ead3e78ab343cd93727046f2de44e135fb4a4d67024228fee114061823c5`.
- It demonstrates different hypothetical interpretations of raw `0x23/0x50/0x64` under offset-mV, VID-code, and IEEE-float protocols. It does not select a value or prove the BIOS field uses any protocol.

## Correction: imported SMU helper is not hardware read-only (2026-09-11)

- Static inspection of `archives/imported/smu-host-library/legacy-tmp-bc250-bc250-smu/bc250_smu/api.py` (formerly under `import/`, SHA-256 `584b135de0796e2b1e5d593b316457f18b5e5120bb3f8b5307acb551c2721185`) and `transport.py` (SHA-256 `4ec3ba8cc13ff4af8ab2e2e525edd145bb23ffe3c59098231ada36f45b6685a6`) shows `Bc250PciTransport.open()` opens PCI config with `O_RDWR`; `read_smu_reg()` selects a register by writing `0xB8`; and `send_message()` writes mailbox command/arguments.
- Therefore query-named `bc250_smu` calls are not proven hardware read-only and must not be used in the stock read-only telemetry gate. This supersedes any imported helper header claiming read-only.
- No helper was executed and no hardware mutation occurred.

## SMU helper safety correction (2026-09-11)

- `bc250_smu` query helpers are not hardware read-only because the transport uses PCI config `O_RDWR`, writes an index selector, and sends mailbox command/argument writes.
- This is recorded in the runbook and maps. No helper was executed.

## APCB candidate byte-terminology correction (2026-09-11)

- Independent review wording `DFG Value LSB` is corrected: bytes changed at `0xAB1132`/`0xAB116E` are byte `+2` of little-endian DFG words (`1F -> 7F`), not byte `+0`. The word-level changes and exact diff remain unchanged.
- Candidate manifest updated: `evidence/candidates/BC250_APCB_DFG_only_v001/build-manifest.json`, current SHA-256 pending final refresh.

## Safe stock-runtime collector (2026-09-11)

- Created `scripts/collect_stock_runtime_readonly.py`, SHA-256 `ea128ffe4f7fb7151fd63575722e570c7920547c6b8251f923227a447d4571a9`. It uses an explicit kernel/sysfs/journal/lspci/modinfo read allowlist and does not import `bc250_smu`, open PCI config, access `/dev/mem`, or write sysfs.
- Synthetic fixture test passed; summary `evidence/firmware-audit/collector-fixture-test.json`, SHA-256 `2c83872ef57929fdc5006e41ee67e4fe89db5bcc19137f57505419f1764c59f7`. No real board was accessed by the test.
- Real stock boot collection remains unrun and requires programmer/clip removal and normal power restoration.

## AmdNbioSmuV10Dxe mailbox context (2026-09-11)

- Direct Rizin report `evidence/firmware-audit/rizin/AmdNbioSmuV10Dxe.mailbox-context.txt`, SHA-256 `c81b065ee241d336efa5354b38aa44668f3041d3162254152e2563eaf8a4e76c`, maps Q2 command/response/argument constants through a service helper.
- No data flow from AmdSetup VDD offset to this path is proven; runtime is unrun and the helper is write-capable.

## Direct APCB DFG consumer context (2026-09-11)

- Rizin report `evidence/firmware-audit/rizin/AmdApcbObrDxe.dfg-context.txt`, SHA-256 `fcb666f776d700933878024166c39929147cf06210d85fd9ffbeceac72241201`, shows function `0x119DC` applies `0x001FFF00` to APCB token words and recognizes the wildcard marker.
- Candidate `0x007FFF00` preserves the masked marker while extending upper bits. This supports the static DFG transform but does not identify policy recipients or prove VCN runtime behavior.

## Direct NBIO PEI DF access context (2026-09-11)

- Forced-little-endian TE Rizin report `evidence/firmware-audit/rizin/AmdNbioGfxARIPei.df-window-context.txt`, SHA-256 `95ce1c7917dd12789e6af168dbbdfa046d0003ec653116e3f276da6ea74b8c68`, shows generic DF indirect read/write/read-modify-write helpers at `0x14A35/0x14B1F/0x14C0C` using `0x405C`/`0x4098`.
- This is write-capable static context and does not prove an AmdSetup VDD consumer or VCN-specific operation. No register write was executed.

## CbsBasePei Setup-default context (2026-09-11)

- Direct Rizin context `evidence/firmware-audit/rizin/CbsBasePei-setup-defaults-context.txt`, SHA-256 `04f27d70a345d06a66dfae3f0af07185f5c742dd1049acd4057d167b9f53db2e`, confirms default initializer bytes for MCLK/UCLK/FCLK/VDD/DF fields.
- It does not prove downstream NVRAM/SMU/training application.

## Deterministic audit-state verifier (2026-09-11)

- Verifier: `scripts/verify_bc250_audit_state.py`, SHA-256 `88ebabef801051fd11ca64fcb02e2a729c475c0ad861cf7ce413f60fb5439d1f`.
- Result: `14/14` checks pass. Evidence: `evidence/firmware-audit/audit-state-verification-20260911.json`, SHA-256 `d25777f9badce31633509f5746f590be0e843969c6bbce9148f2922128a6cc2b`.
- The verifier confirms candidate/readback/parser/review/map state while retaining runtime and write gates.

## CoreUnlock Setup/PPT numeric coincidence (2026-09-11)

- CoreUnlock statically compares `Setup+0x1C4` with `0x000157C0` (88000); fresh `Setup+0x1C4` is `0x00011940` (72000), so its equality is false. Fresh `AmdSetup+0x70C FAST_PPT_LIMIT` is independently `0x000157C0` (88000).
- These are distinct NVAR variables/offsets. The coincidence is retained as an unresolved correlation, not a proven PPT/VCN gate link.

## APCB DFG-only hardware write/readback (2026-09-11)

- Operator approved exact candidate `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, for board `BC250-01`, conditional on a new matching stock dump.
- Fresh pre-write dump `evidence/programmer/reads/20260911/read-c-prewrite.bin` is 16 MiB, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, and byte-identical to both preserved stock reads.
- Pinned/signed `flashrom v1.8.0` through `ch347_spi` at 1.875 MHz detected Winbond `W25Q128.V`, wrote the approved candidate, and reported built-in `VERIFIED`.
- Independent full-chip readback `evidence/programmer/reads/20260911/postwrite-apcb-v001.bin` is byte-identical to the candidate and has the same SHA-256. Exactly `0xAB1010`, `0xAB1132`, and `0xAB116E` differ from stock.
- Firmware/APCB parsers pass: PSP/BHD/APCB checksums match, four FVs remain valid, and DFG words at APCB `+0x130/+0x16C` are `0x007FFF00`.
- Evidence class: hardware-verified at SPI programmer write/readback layer. Cold boot, PSP acceptance, video output, VCN power/rings/codecs, and stability are unrun.
- Recovery stock remains `evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`. Trial manifest: `evidence/programmer/reads/20260911/apcb-v001-hardware-trial-manifest.json`.

## APCB DFG-only first boot observation (2026-09-11)

- Operator reports green/blue indicators and a red indicator between USB and Ethernet, but no display image, on the first boot after the verified APCB candidate write.
- User-visible video output is FAIL for this attempt. Firmware execution stage, PSP acceptance, POST progress, and VCN state are INCONCLUSIVE because no UART/POST/network/Linux evidence exists.
- Do not classify the candidate as bootable or VCN-enabled. Stop repeated boot attempts and restore the preserved stock image under a new exact rollback approval. A successful stock boot under the same setup is the next discriminating test.

## Fresh-baseline combined D3-B2 candidate (2026-09-11)

- Built offline `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin` from verified stock SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`; output SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- The candidate combines modified SEC_GASKET type `0x24` at `0x9E0000`, modified TOS_SECURITY_POLICY type `0x45` at `0x9E4000`, PSP-directory repoints/Fletcher32, and APCB DFG `0x007FFF00` with checksum `0x32`.
- Root structural verification passes 21/21; general firmware and APCB parsers pass; exact diff is 13,736 bytes across 332 ranges confined to the declared directory/policy/APCB regions.
- Modified policy payloads retain historical signature tails. PSP signature acceptance and boot behavior are unverified. Independent review is pending, so the artifact is not approved for flash.
- Builder: `scripts/build_vcn_d3b2_candidate.py`; verifier: `scripts/verify_vcn_d3b2_candidate.py`; evidence directory: `evidence/candidates/BC250_VCN_D3B2_combined_v001/`.

## Combined D3-B2 independent review and provenance correction (2026-09-11)

- Independent Claude Opus review `evidence/candidates/BC250_VCN_D3B2_combined_v001/independent-review-claude-opus5.md`, SHA-256 `5abe1f3f20fe03359d54bd85a71005c0bff3cbbd5213d452fd0bc2954d52a4a1`, recommends `APPROVE_FOR_HARDWARE_TRIAL` only under a programmer-backed recovery procedure. It does not establish safety, bootability, signature validity, or VCN function.
- Reviewer critical finding agrees with root: modified/grown `$PS1` payloads retain stale signature material; PSP acceptance is unverified and is the trial hypothesis.
- Correction to reviewer F5: historical full base and D3-B2 images are present under `archives/imported/recon-evidence/legacy-tmp-bc250-recon/d3/package/`. Base SHA-256 is `4005b68a70e335581b23e819fd3e52ff74c0f10178bf8563e36220304a12aa67`; historical D3-B2 SHA-256 is `dec4930e6b322bc60a3954870f728adb08e50018b001ac6c21d318c154036b61`. The report's absence claim is disproved by direct filesystem and hash checks.
- Reviewer F4 was closed by extending the root verifier with leading/+0xD0 signature-material, exact policy-prefix delta, and shifted-group checks. `verification-v3.json` passes 25/25, SHA-256 `d0b0b9abc6251c39d8ca9c303be1a927a05c6cc82d9a03986c6e635c15cc999b`; candidate bytes remain unchanged.

## Combined D3-B2 hardware write/readback (2026-09-11)

- Fresh pre-write chip capture `read-d-prewrite-d3b2.bin` is byte-identical to the prior APCB-only readback, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, and differs from stock only at the expected three APCB offsets.
- After exact operator approval, pinned/signed `flashrom v1.8.0` through CH347T wrote `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin` to board `BC250-01` and reported built-in `VERIFIED`.
- Independent full-chip readback `postwrite-d3b2-v001.bin` is byte-identical to the authorized candidate, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Physical-readback validation passes: firmware parser, APCB parser, and corrected D3-B2 structural verifier 25/25. PSP/BHD/APCB checksums match and four FVs remain valid.
- Evidence class: hardware-verified at SPI programmer write/readback layer only. PSP acceptance, boot/video, VCN power/MMIO/rings/codecs, and stability remain unrun. Manifest: `evidence/programmer/reads/20260911/d3b2-v001-hardware-trial-manifest.json`.

## Combined D3-B2 first boot observation (2026-09-11)

- Operator reports the same indicator pattern and no display image as the prior APCB-only candidate.
- Video output FAIL; PSP/POST/VCN state INCONCLUSIVE. Exact SPI write/readback remains PASS.
- The common APCB DFG change is now a suspect, not a proven cause. Next discriminating candidate: keep the two modified VCN policy carriers but restore APCB fully to stock. A repeated no-display result would shift focus toward PSP policy relocation/signature handling; a boot would implicate APCB and permit a direct VCN check.

## CH347T JTAG capability boundary (2026-09-11)

- Vendor-maintained `WCHSoftGroup/ch347` revision `4625b40a5e55e0f6ceff7ca528706a4f19906d1f` documents CH347 silicon JTAG master support with TMS/TCK/TDI/TDO/TRST and vendor OpenOCD integration.
- This does not prove that the operator's specific CH347T programmer PCB exposes those signals or supports the BC-250 J2 1.8 V I/O domain. A clear PCB/header photo and voltage/reference verification are required.
- Board-side CAD mapping remains J2: TCK 2, TMS 4, TDI 6, TDO 8, TRST_L 9, GND 3/5/7/17, VDDIO 1/19 at 1.8 V. Never drive J2 directly from an unverified 3.3 V breakout.
- CH347 supplies a possible JTAG transport, not proven AMD HDT+/CPU debug compatibility. No attach or target operation occurred.

## VCN policy-only candidate (2026-09-11)

- After APCB-only and combined D3-B2 both produced the same no-display observation, built `candidates/BC250_VCN_policy_only_v001_from_read-a.bin`, SHA-256 `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1`.
- It is byte-identical to combined D3-B2 except the entire APCB block is restored to stock. Versus stock, only the PSP-directory and relocated SEC_GASKET/TOS policy regions differ; 13,733 changed bytes across 329 ranges.
- Root firmware/APCB/policy verification passes 26/26 in stock-APCB mode; signature acceptance remains unverified. Independent Claude review is running; hardware write is not approved.
- Independent Claude Opus review completed with `APPROVE_FOR_HARDWARE_TRIAL`; report SHA-256 `07de7fda571bfb8d2d4e3cd4e406cf41a080bd97eaf0171b36c52944467d21af`. Root reread and verifier rerun agree 26/26. Exact write approval and fresh current-chip capture remain pending.
- Policy-only SPI write/readback completed 2026-09-11: fresh pre-write capture `read-e-prewrite-policy-only.bin` matched D3-B2 SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`; exact authorized candidate `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1` was written with flashrom built-in `VERIFIED`; independent full-chip readback `postwrite-policy-only-v001.bin` is byte-identical to the candidate. Firmware/APCB/26-26 structural checks PASS on the readback (reports `68ca6f52ffb032ea317a9b609982a03adefda426d83cd1ae6f9f91fc92ce19be`, `2c6221c1054157c6c43021e186af45f48d80ae58ad28531800e68700ddbcc270`, `26a52645c6fe746ae9cbdafacada234ea05ac000cfaaa1403d37ee0e542c2810`). Evidence class is hardware-verified at SPI write/readback layer only; PSP acceptance, boot/video, VCN, and stability remain UNRUN. Manifest: `evidence/programmer/reads/20260911/policy-only-v001-hardware-trial-manifest.json`.
- Policy-only cold boot 2026-09-11T20:39+05:00: green/blue on, red USB/Ethernet on, no jack LEDs, fan normal, no display. Video FAIL, boot/PSP INCONCLUSIVE. Identical to APCB-only and D3-B2 attempts, so stock APCB did not discriminate; focus moves to the shared PSP policy relocation/signature branch.

## Correction: APCB-only "safe control" expectation disproved on BC250-01 (2026-09-11)

- Historical VULN-002/D3-A claim: APCB-DFG-only edit boots with VCN dead (false-negative control). Measurement 2026-09-11 disproves it on this board: APCB-only flash gave identical no-video (green/blue on, red USB/Ethernet on, no display) as D3-B2 and policy-only.
- Cause remains INCONCLUSIVE (PSP-side APCB consumer rejection vs memory-init break). APCB DFG is therefore boot-unsafe, not a safe control. Full synthesis: `docs/research/2026-09-11-vcn-unlock-synthesis.md`.

## E1 DXE-only SPI write/readback + cold boot (2026-09-11)

- E1 SPI write/readback PASS 2026-09-11T21:20+05:00: candidate `9d0f7ca14952369833f8f87f9092cad4edd27df62f01d0df28b20d55c49eb497`, readback byte-identical, PSP/BHD/APCB stock match, 4 FVs.
- E1 cold boot 2026-09-11T21:25+05:00: same no-video pattern (4th identical). DXE-only edit does not discriminate; video FAIL, boot INCONCLUSIVE.

## Stock restore cold boot no-video (2026-09-11)

- Stock SPI bytes verified IDENTICAL, but operator reports no video. All candidate no-video results are therefore non-discriminating. Cause is procedural/hardware outside image bytes until stock boots.

## APCB-only reflash after connector fix (2026-09-11)

- Pre-write chip held unknown operator backup `e5a2a8bd36693bc02be96bb08b3470419c1895f78d899d4c752aecb5dec1453c` (not stock, not candidate).
- APCB-only `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70` written, VERIFIED, readback IDENTICAL.
- All prior no-video results non-discriminating (wrong display connectors). Fresh boot observation pending.

## Firmware decision 2026-09-11: reuse 1.92 probe kernel

- Board has installed 7.2.0-1.92-cachyos-vcn-bc250 (bc250_vcn_mode 0/1/2). Mode1 PASS 2026-08-28 with probe block + VCN fw header found.
- VCN fw: green_sardine_vcn.bin 404,544 B present, declared by both stock and probe modinfo. No cyan_skillfish2_vcn anywhere (driver never requests it).
- No new kernel/firmware build. Next: boot mode1 then hardware mode from local console.

## Mode1 probe boot hardware-verified (2026-09-12)

- Board BC250-01 on APCB-only candidate `6b1fe8ef...` rebooted into kernel `7.2.0-1.92-cachyos-vcn-bc250` with `amdgpu.bc250_vcn_mode=1`.
- Live journal (read-only SSH): 9 IP blocks including `number 8 <vcn_v2_0_0> (vcn_v2_0_probe)` (stock mode0 has 8, no VCN); `[VCN instance 0] Found VCN firmware Version ENC: 1.24 DEC: 8 VEP: 0 Revision: 9`; `VCN probe: fw_version=0x08118009 fw_size=404544 vcpu_bo_size=1064960` — fw_size equals green_sardine_vcn.bin.
- This upgrades the mode1 claim from historical (2026-08-28) to fresh `hardware-verified` at the probe/attach layer on the current image. No ring-test lines this boot; VCN hardware block, rings, and codec function remain UNRUN pending mode2.
- Evidence: `evidence/runtime/20260912-mode1-probe-boot-audit.md`, journal extract SHA-256 `c165345b0ec05f12f4939a88b6f315b8e97fcac7bf183ef0bd6ef85c99e2004a`.

## Controlled mode2 probe: wedge at first VCN MMIO (2026-09-12, hardware-verified)

- With `modprobe.blacklist=amdgpu` the mode2 kernel boots fully (SSH up, simpledrm). Root-triggered `modprobe amdgpu` with local `dmesg -w` capture wedged the kernel deterministically: 10 IP blocks (real `vcn_v2_0`, `jpeg_v2_0`), SMU 88.6.0 OK, custom `bc250-40cu-enable` writes completed, `kiq ring` set, then `clocksource: Watchdog remote CPU 4 read timed out` and total silence. No panic, no VCN/MMSCH lines.
- Differential vs mode1 proves the wedge is the first VCN hardware access in `vcn_v2_0_hw_init`: the VCN domain is power/clock-gated by PSP/SMU. CU-unlock writes are cleared as the culprit. Log: `evidence/runtime/20260912-mode2-controlled-probe-dmesg.log` SHA-256 `e9c830f8f231c1e803677d4b67ad7b3154885223a7d95ac86cabddd89169c66d`.
- Installed 1.92 kernel is newer than corpus `recon/linux.patch` (prints `bc250-40cu-enable` vs `ps5-40cu-enable`; no `bc250_vcn_mode` in the patch copy).

## G7: D3-B2 retest with correct wiring — no boot; policy branch dead as implemented (2026-09-12 04:0x PKT)

- D3-B2 `439e2481...` reflashed twice with verified readbacks (postwrite `postwrite-d3b2-retest.bin` and `-2.bin`, both byte-identical, PSP `0x9F717AB8`, BHD `0xECE7B2E6`, APCB `0x32`, DFG `0x007FFF00`, verifier 25/25).
- Pre-write capture revealed the board rewrote its own UEFI NVRAM (`0x008908..0x00B0B4`, 1,420 bytes, 31 ranges) during post-flash boots; payload regions unchanged.
- Operator performed the boot correctly (confirmed by operator statement) with corrected display wiring: **board does not start**.
- Differential with correct wiring: APCB-only (PSP untouched) boots; D3-B2 (modified/relocated SEC_GASKET + TOS_SECURITY_POLICY with stale signature material) does not. Verdict: PSP signature/policy rejection is now the leading explanation for the D3-B2/D3 series no-boot; the unsigned policy-relocation branch is boot-unsafe as implemented. This supersedes the earlier "policy carriers are the promising branch" reasoning that was based on the invalidated no-video series.
- Offline PSP signature verification remains impossible; no signing capability is available in the project.
- Branch options recorded: S2 runtime C2P mailbox unlock from a bootable OS (no flash), S3 Q3 0x98 replay, S5 in-place single-value edits; firmware signed-relocation (D3-C) requires a signing capability the project does not have.

## S2 campaign corpus mining and PMFW identity validation (2026-09-12)

Corpus sources mined: `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md` (master, 638 lines), `recon/VCN-UNLOCK-CORRECT-CHAIN.md` (final 2026-08-29 RE report), `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/vcn_campaign.tgz` (historically extracted to `/tmp/bc250-vcn-campaign/`), on-board `~/vcn_unlock/` (intact, richer than the tgz), `recon/robin3_psp_unique/`.

- PMFW identity hardware-correlated: type `0x08` blob sliced from the current on-chip image `postwrite-apcb-restore-20260912.bin` at `0x8FF000` is byte-identical to `recon/robin3_psp_unique/SMU_OFFCHIP_FW~0x8_0.58.6.0` across the full `0x40000`-byte body. The `unlock.py` SMU-SRAM offsets (derived from the BIOS-3 PMFW) are therefore valid for this chip. Version 0.58.6.0 = SMU 88.6.0 matches live dmesg.
- Unlock mechanics (`bc250-smu-unlock/unlock.py`): Q2 msg `0x23` ring-overflow -> transfer-table pointer overwrite -> debug byte `0x7B3C` cleared -> secure cluster open (SMN read/write, SMU SRAM read/write, code exec). Executed successfully on this board 2026-08-25/26 (every campaign .out starts "secure access open"). Caveat in README: offsets are BIOS-3-specific — satisfied per the identity check above.
- Full SMN replay content analysis (`campaign/smn_full_gasket_replay.py`, 1461 writes = Robin 1405 + 56 bank-12): the replay wrote Robin KILL values (`0x03E810<-0`, `0x03A2011C<-0x87FF`, `0x0322011C<-0x8000`) plus the 56 donor bank-12 records. Donor stage-A values (`0x03E810=6`, `0x03A2011C=0x107FF`, `0x03A20124=0x10FFF`) were NEVER written at runtime. The historical "VULN-1: replay accepted, MMIO stays all-ones" result is fully explained by the kill values; the donor-aperture runtime write is the untested variable.
- Measured wedge lessons: (1) 2026-08-29 board wedge = VCN MMIO READ while the domain was gated (VCN-START-SAFE.md; write-first order mandatory, reads only after domain enable). (2) 2026-09-03 SMU wedge = SMN read of `0x03A2011C` in `smn_lock_probe.py` Phase A (secure-state during that run unrecorded; bank-12 reads on a cold board wedge SMU per probe header). (3) WRITES to every gasket address class (`0x03A2/0x0322/0x03E8/bank-12/0x1C7xx`) are proven non-wedging (1461-write replay + 56-record runs completed with SMU alive).
- `smn_lock_probe.py --phase-b` (designed 2026-09-03, never reached): single additive write `0x03A2011C 0x87FF->0x107FF` + readback with three-way verdict: LATCHED (runtime DF-window programming viable) / DROPPED (DF hardware-lock `LockDFReg 0x1b`; runtime window path dead, boot-time only) / WEDGED (cold cycle). This is the cheapest decisive discriminator for the whole S2 runtime branch.
- dom6 facts (hardware, 2026-08-25/26): ctrl gate `0x06d0f8` boot value `0x02` re-arms every cold boot; the `--manual-powerup` release persists within the SMU session; slots `0x16/0x17/0x18` ON/READY after clock work (`clock_enable_after_coldboot.out`); Q3 msg `0x61` Xtensa sequence (SRAM `0x3ff00`, thunk `call8 0x23744` x3) installed and fired successfully, SMU survived.
- PMFW msg table (dumped 2026-08-25, `community_msg_table_fixed.out`): 147 handlers at SRAM `0x746C`, stride 8, validated anchors; secure cluster msgs `0x27..0x2F` (flags `0x201`, gated); power-code-band candidates msg `0x8f->0x2326c`, `0x21->0x249dc`, `0xae->0x2522c`; msg `0x3C/0x3D` = enable/disable SMU features by bitmask (renoir `PPSMC_MSG_PowerUpVcn` analogue is feature-gated). Full disasm on disk: `recon/func_23b14_full.txt` (domain power-up), `recon/func_23744.txt` (soc_clk_program_slot), plus the Ghidra hunt list in the msg-table dump.
- Arbiter definitions (from the chain doc): bridge-passage marker = `UVD_VERSION` via `/sys/kernel/debug/dri/1/amdgpu_regs` dword `0x78CA` (byte `0x1E328`); direct-load smoke = `mmUVD_SCRATCH9 CAFEDEAD -> DEADBEEF`. Safe reader = amdgpu_regs debugfs on a mode1 boot; BAR0 mmap EINVAL and `/dev/mem` EPERM on the current kernel (measured 2026-09-12); BAR5 mmap OK (C2P window only).
- `VCN-UNLOCK-CORRECT-CHAIN.md` (2026-08-29) gate ladder: G0 unlock DONE, G1 dom6 power DONE, G2 clocks DONE, G3 VRAM staging DONE, G4 driver probe path DONE, **G5 NBIF/Fabric bridge = BLOCKER**, G6+ unrun. Its prescribed main move S4 (NBIO candidate regs `0x13b1005c/0x13b10060/0x13b00084/0x13b0004c`, one reversible bit-write, then `UVD_POWER_STATUS`) was never executed — the session ended on the 08-29 wedge. `0x10c2/0x10c3` are AGESA IDS NV IDs, not registers.
- Board state at mining time: alive on mode2+blacklist boot, `~/vcn_unlock` deployment intact; approved S2-A runbook in `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md` (operator approved stages 0-4 and pre-approved msg 0x61 with `vcn_watch`).

## S2-A runtime donor-aperture experiment: executed, definitive verdict (2026-09-12, hardware-verified)

- Full chain executed in one boot session (cycle #4), every step with liveness checks: unlock (Q2 0x23) -> dom6 `--manual-powerup` (ctrl gate `0x02->0x00` LANDED) -> fire msg 0x61 (slots 0x16/0x17/0x18 clock-enable LANDED, status bit8 up-ack = powered baseline) -> 59 gasket writes (3 donor aperture `0x03E810=6/0x03A2011C=0x107FF/0x03A20124=0x10FFF` + 56 bank-12, all accepted, `0x0900C234` commit=1) -> arbiter single-register reads.
- **Definitive verdict: runtime SMU gasket programming LATCHES (bank-12 commit=1) but the VCN island stays isolated (all five UVD probes all-ones, clean reads)** — the NBIF/Fabric bridge (G5) does not pass with a runtime-programmed gasket. Confirms the 2026-08-29 chain-report blocker by experiment.
- Wedge taxonomy extended (all hardware-verified): (a) DF-space SMN READS hang the SMU mailbox even immediately after a successful write to the same address (never-programmed boot state); (b) bank-12 WRITES hang the SMU when the domain is power-gated (bank-12 sits behind the VCN island fabric; 26.08 success is explained by the domain being powered that session); (c) `amdgpu_regs` FULL-DUMP reads (`cat`) hang the kernel even powered+clocked — full dumps are a closed method; (d) `amdgpu_regs` SINGLE-REGISTER seek+read(4) is the proven safe arbiter transport (`read_vcn_direct.py`: `mmUVD_VERSION` dword `0x78CA`); (e) WRITES to DF windows `0x03A2/0x03E8` are safe in any domain state.
- Proven bring-up order (repeatable runbook): cold boot mode1 -> unlock -> manual-powerup -> fire 0x61 -> gasket writes -> single-reg arbiter. Rollback = cold power cycle; everything is volatile.
- Executors on board: `stage2a_writefirst.py`, `stage2b_writefirst.py`, `stage4_arbiter.py` + JSON/txt logs; action log: `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md`.
- Next lever (excluded from the approved run, needs a new runbook + approval): S4 NBIO register moves `0x13b1005c/0x13b10060/0x13b00084/0x13b0004c` (one reversible bit-write each, then re-read arbiter) — the one remaining runtime bridge candidate; alternative model: the bridge re-samples the gasket only at cold reset (favors boot-time PSP application, which the D3-B2 rejection showed requires a signing capability the project lacks).

## S4 NBIO probe result (2026-09-12, hardware-verified)

- NBIO-space single-register SMN reads are SAFE (six reads x2 runs, no wedge). Measured: `0x13b1005c=0x00008000`, `0x13b10060=0x0000ffff`, `0x13b00084=0x00000108`, `0x13b0004c=0x00800000`, gasket-diff addresses `0x13b103f8=0x13b10400=0`.
- No candidate carries the PEIM's clamped `0x3` port-config pattern -> per the S4 prescription no write was made. The chain report's four NBIO candidates are experimentally unsupported as clamp carriers in this boot state (its own caveat anticipated this: "точные регистры NBIF всё ещё нужно доказать").
- Combined verdict: PSP gasket + hardware-locked Fabric translation matrices until cold reset is now the favored model; the runtime data-plane writes cannot re-open the bridge. Next: derive true NBIF registers by static analysis of `robin3_uefi/disasm_*` `AmdNbioGfxARIPei` (Init Config Struct `0x1e0/0x1e1` serialization).

## Unlock-paths map (2026-09-12)

- Complete inventory with post-campaign statuses: `docs/research/2026-09-12-unlock-paths-map.md`. Summary: P1 runtime SMU (transport proven, trusted transition missing — primary path is the executor static RE); P2 UEFI same-session (`Bc250VcnProbeApp.efi` + chainload exists, bound by the same G5 blocker); P3 flash (unsigned/APCB closed, D3-C deprioritized, DEBUG_UNLOCK dead — needs AMD key); P4 staged kernel 0012 (designed, not built; required post-bridge); P5 TEE/TOS (no path; C2P measured negative 2026-09-12).
- G7 correction: the E1 DXE-only no-boot result (2026-09-11T21:25) predates the display-wiring fix and is NON-DISCRIMINATING; DXE-only boot-safety is reopened (low priority).

## PSP verification chain static decode (2026-09-12, loop run #1, static-analysis)

- Stock `TOS_SECURITY_POLICY~0x45` body (1,248 B) contains ZERO VCN-bank (`0x0900Cxxx`) records — the VCN bank is absent from ALL stock boot carriers (gasket 0x24 and policy 0x45). At stock boot nothing programs bank 12; the A3 "duplication in 0x45" note covers only the E810-gate / DF-aperture locks, not the VCN bank.
- $KDB parsed (c1_rsa_final evidence): own t50 = 8 RSA-2048 keys (exp 0x10001), own t51 = 3, chipset copies identical; gasket 0x24 and policy 0x45 are BOTH signed with kid `96ea7cfe...`, whose public key IS in the board's own t50. Private key extraction is mathematically closed (RSA-2048); the live RE lane is a verifier weakness, and the interesting handlers (svc#6/#0x63) live in the on-die ROM, not in the image.
- ABL1 (`ABL1~0x31_21.11.26.0.body`, 94 KB uncomp) contains three `svc #6` verification wrappers (`0x380`, `0x12a4`, `0x6dd6`); the `0x12a4` wrapper returns 0 unconditionally after the svc — the pass/fail decision happens inside the on-die ROM handler and is NOT statically resolvable from the image.
- G7 refinement of the 2026-09-12 04:1x log entry: "PSP halts on the modified policy" is an INFERENCE. The D3-B2 boot observation (no video, indicators on) is consistent with TWO models: (A) ROM verifier halts inside svc#6, or (B) verify-fail -> blob skipped/mark-parked (the A2 fail-soft path) -> the 47 foreign gasket banks never programmed -> DF firewalls closed -> no video with the board possibly still running. DISCRIMINATOR EXECUTED (2026-09-12, hardware-verified): the D3-B2 re-flashed byte-exact (the readback md5 = the image md5), the cold boot failed identically, and 12 SSH probes over ~3 min (t+90s..t+3min) ALL returned no-route/no-SSH — the x86 never releases from reset. Model (B) is DISPROVEN; model (A) stands: the on-die ROM verifier halts inside svc#6 on the modified/unsigned $PS1 carrier. The $PS1 carrier route is CLOSED DEFINITIVELY (the log: docs/action-logs/2026-09-12-vcn-mode1-probe-audit.md, "D3-B2 RETEST + DISCRIMINATOR RESULT").
- Loop track (a) status: key extraction closed by math; verifier-weakness lane limited by on-die ROM; remaining offline value = the TOS-side chain already decoded (A2). Loop track (b) primary: hardware runs (S2 C2P stage-1 token request script ready; stage5 donor routes script deployed).

## S2 stage5 donor dataplane: hardware-verified definitive negative (2026-09-12 06:50 PKT)

- Full chain on a mode2+blacklist boot (amdgpu not loaded; SMU transport = PCI config 0xB8/0xBC, amdgpu-independent): unlock -> fire 0x61 (slots LANDED, clocks ON) -> gasket 59/59 (commit=1, lock tail removed) -> stage5 donor dataplane 15/15 ACCEPTED (NBIF `0x1C760/64/80/84/88/8c`, NBIO `0x1F820/0x1F8A4`, IOHC `0x322` x3, DF `0x3D2` x2, binding `0x3E810/0x3E814`).
- Arbiter: BAR5 `UVD_VERSION/POWER_STATUS/NO_OP/STATUS` = ALL-ONES, CLEAN reads (no wedge). THE ISLAND REMAINS ISOLATED with the complete donor dataplane applied. Hardware-verified.
- Consequences: (1) the donor route VALUES are not the missing lever — the bridge closure is not (just) a routing-values problem; (2) new safe read class: `0x6A1xx`/`0x33E0` NBIF config via SMU debug path (first capture recorded in the action log); (3) the remaining suspects for the isolation: the island ISO/reset held outside the dom6 sequencer (Aug-25 suspect (b)), an unmapped SMU fw-side message (the real PowerUpVcn equivalent — suspect (a)), or PSP-side isolation beyond the gasket (suspect (c)). Next offline lever: the Q3 msg-table deep decode (`--msg-table` on board) + the ISO/reset chain in the SMU firmware image.
- Deviation noted: `ctrl=0x00000000` at BOOT on mode2 (no gate hold) vs `0x02` on every mode1 boot — the boot-state difference correlates with amdgpu absence; unexplained, watch it.
- C2P direct-mailbox 0x100B: 4 same-class attempts (plain, size in 34/33/38) all = immediate completion bit + untouched buffer. G6: class closed; the dispatcher-frame encoding is in the on-die supervisor, not in any image.

## S2-L5: native domain-power chain decoded; first non-amdgpu wedge (2026-09-12 06:54-08:25 PKT)

- SMU feature system decoded statically (SMU_OFFCHIP_FW~0x8 0.58.6.0 body): msg 0x3C/0x3D = Enable/DisableSmuFeatures (2-dword = 64-bit feature mask) -> OR/AND into state struct @SRAM 0xcc98 -> apply fn 0x1d940 iterates 64 features, per-feature handler table @0xcc98+0x10, callx8 per unacked feature. Handler table extracted (features 4->0x23c24, 21->0x2496c in the power band; 37-63 = 0).
- THE DOMAIN POWER CHAIN: PowerUpDomain(idx) = fn 0x2362c (checks state, calls the hardware-verified dom6 power fn 0x23b14(idx, on), then clocks 0x2375c/0x23d54). Callers: 0x1f0e6/0x1f19e/0x1f1fa inside fn 0x1f038 = THE Q3 MSG 0x5C HANDLER (also msg 0xb7): a freq-apply flow that IMPLICITLY powers domains 0xe (14), 0xf (15), 0x11 (17) — three domains never touched by any prior experiment (the runbook only powered dom6 via 0x61/0x23b14).
- msg 0x5C handler gates on SRAM byte [0xcec8+0xf6] == 0xff (bail with status 0xff). Struct 0xcec8 = the fw's driver-table copy (freq limits +0x100/+0x104, gate bytes +0xf6/+0xf7, counts +0x11/+0x12); the gate byte has NO fw writer — it arrives only via the Q0 driver-table transfer (msgs 0x04/0x05 + 0x07). On mode2 (no amdgpu) it is 0xff.
- Live: fire msg 0x5C with the gate intact = CLEAN status=255 bail (the decode is correct; SMU stayed alive). Gate-clear (smu_write_bytes 0xcfbe<-0x00 via the proven secure write class) + refire = HARD BOARD WEDGE (ping 100% loss, no route). First non-amdgpu wedge of the campaign; the handler demonstrably ran past the gate and hit the isolation trap — the same wedge signature class as amdgpu's first touch of the isolated island.
- Interpretation: domains 14/15/17 are the strongest VCN-cluster candidates (the UVD/VCE/DCN trio on this fw). The power-up path from msg 0x5C reacts — but alone it is not survivable (the gate byte may also guard garbage freq limits +0x100/+0x104 -> the handler can divide/store garbage after the gate). Next iteration (after cold cycle): full driver-state snapshot (0xcec8..0xcee8+), then EITHER the full driver-table transfer via Q0 0x04/0x05+0x07 (a proper table with sane freq limits + gate byte set), OR the surgical byte clear with the fire in a SEPARATE step after a 30 s stability watch.
- Cold cycle restores: gate byte = 0xff (volatile SRAM), all runtime state. No flash touched.

### S2-L6 static decode: the wedge mechanism fully mapped (2026-09-12, loop run)

- fn 0x23b14(idx, on) = the per-domain SMN power-command driver. Domain table @fw 0xf550 (pool 0x17434), SMN base 0x10ffe00 (mask 0xfffff), status load offset +0x200, cmd via fn 0x233e8. Three INFINITE polls with no timeout: status bit8 (0x23b5c), bit16 (0x23b78), bit0 (0x23b96). THE WEDGE = the poll on a domain whose ACK never comes.
- Per-domain SMN registers extracted (cmd, status): dom6 = 0x110009C / 0x11002EC (known-good); dom7 = 0x1100340 / 0x1100354+0x200 class; dom14 = 0x1100085 / 0x11000284->0x11000284... exact: dom14 cmd 0x1100085, status 0x1100084+0x200 = 0x11000A84? — see docs/action-logs/2026-09-12-vcn-mode1-probe-audit.md S2-L6 + the ready script `read_domain_status.py` (single source of truth for addresses; read-only, host-side, cannot wedge the fw).
- Boot-default state bytes (image, +0x14): dom6=0x0c (the ONLY domain powered at boot), dom14=0x08, dom15=0x04, dom17=0x00.
- Isolation mechanism (upgraded from suspect to static-analysis-backed mechanism): the VCN-cluster domains never assert the power ACK; the fw has no timeout -> any fw-driven power-up of those domains hangs the SMU and takes the board down. Any future experiment must NOT let the fw poll an unacked domain: use host-side direct SMN command writes with a HOST-side timeout, or release the ISO first.
- Ready next-boot probe: `/tmp/bc250-stage2a/read_domain_status.py` (deploy to board `~/vcn_unlock/`): read-only status dump of domains 6/7/14/15/17 — the ACK-bit patterns of the isolated domains are the diagnostic for the ISO-holder question.

### S2-L6/L6b: mailbox wedge from a cmd READ; driver-table structure; revised plan (2026-09-12 07:01-07:20 PKT)

- HARDWARE-VERIFIED: the dom6/dom7 cmd/status reads (0x1100xxx block) = clean zeros; the dom14 cmd read (0x10FFE85, odd address) TIMED OUT and wedged the SMU mailbox while THE HOST SURVIVED (ping/ssh continued). Two distinct wedge classes now confirmed: (a) the board-killing class (the fw polls an unacked domain, S2-L5b), (b) the mailbox-only class (a host-side read of a side-effect/dead SMN block). G7 rule reinforced: NEVER read side-effect SMN command registers; the fw only writes them.
- Driver-state struct 0xcec8 semantics: +0xf6 = the driver-table entry count (0xff = none posted; the msg 0x5C gate), +0xf7 = the count limit, +0xd = the walk index, +0x11/+0x12/+0x13 = the feature-5 config bytes. The only +0xf6 writer = the Q0 driver-table transfer (msgs 0x04/0x05 + 0x07; the community module exposes all three). Feature 5 (0x1ded8) = the 0x17-sequencer + the +0x13 flag, NOT the table post.
- REVISED EXPERIMENT (the fw must never poll an unacked domain): (1) unlock; (2) statuses only (domain_status2.py, read-only, safe); (3) if needed, the zeroed fake driver table via Q0 (the gate opens with [+0xf6]=0x00, all accessor walks skip with [+0xf7]=0x00); (4) the DIRECT host-side SMN cmd write to the dom14 power register (the sec SMN write class; cmd = status|bit per the 0x23b14 decode) + a status read with OUR timeout — the ACK appears = the domain powers (then the BAR5 arbiter); the fabric wedges = the fired transaction is itself evidence (cold cycle).
- Statuses prepared for the next boot: dom6 0x11002EC, dom7 0x1100354, dom14 0x1100084, dom15 0x1100284, dom17 0x1100074.
- Write primitive 0x233e8 decoded: val -> SMN 0x10ffe00 + (addr & 0xfffff) + 0x200; the 0x5afff..0x5b7ff range routes through 0x1b514 = an IPC request (msg 0xfe, arg = a pointer to the (addr,val) pair) to the SECOND SMU core (master/slave split). The power-controller space for the isolated domains may live on the slave SMU — a host-side direct write covers the direct path; the slave-side path is a follow-up question if the direct write is rejected.

### S2-L7/L8: the dom14 power transaction NEVER COMPLETES — runtime power route closed (2026-09-12 07:05-07:07 PKT, hardware-verified)

- Boot statuses (read-only, all clean): dom6 0x00000000, dom7 0x00000000, dom14 0x00000041 (busy bit0), dom15 0x00000000, dom17 0x80000002 (bit31+bit1). The isolated domains are BORN in locked/busy states.
- Addressing corrected (G7): 0x233e8 adds +0x200 itself; the request doorbell = write @0x1100084 (status|1), the ack = read @0x1100085. The S2-L6 wedge = my double-counted offset (0x10FFExx = a dead-on-read region), NOT the cmd register.
- S2-L8: the direct host-side dom14 power request (0x41 @0x1100084) was ACCEPTED; the ack NEVER asserted (the next access timed out; the mailbox wedged; the host survived). Two independent paths (the fw in S2-L5b, the host in S2-L8) both end in the incomplete transaction.
- VERDICT: the isolation lives BELOW the SMU firmware — the dom14-cluster power transaction never completes regardless of who fires it. The runtime power-on route is CLOSED as a standalone unlock lever.
- Remaining levers: (a) WHO holds the ISO/reset on the dom14 cluster at boot — the APCB/gasket/policy records; OUR 59-record gasket may not cover the VCN domain cluster — compare with the DONOR gasket record set (offline, apcb-policy-analysis); (b) the dom17 bit31 marker; (c) the boot-time-only re-sampling model.

### S2-L9: the VCN config space is bus-isolated too — RUNTIME UNLOCK CLOSED (2026-09-12 07:09-07:11 PKT, hardware-verified)

- Fresh boot, unlock OK, the L7 statuses reproduced exactly (dom14 0x41, dom17 0x80000002 — stable across boots). The first donor 0x201 VCN config write (0x0900C914 <- 0x7FFF) hung the SMU (msg 0x2C timeout); the host survived. Contrast: 0x0900C234 (the enable-bit family) = runtime-writable (the gasket 59/59 twice), the C914/C930/CB80 config sub-block = not.
- Third independent bus-level confirmation: the dom14 power transaction, the VCN config writes, and the DF reads all share the incomplete-transaction signature. The isolation sits below the runtime-reachable register space.
- STANDING VERDICT: the runtime unlock (booted on the stock policy) is CLOSED by evidence. Remaining: the boot-time/flash track (a policy whose PSP/ABL applies the VCN config before the islands come up; blocked by the signature acceptance problem — the D3-B2 stale-signature carrier does not boot) and the D3-B2 SSH-at-t+90s discriminator as the decisive test of whether a donor boot reaches a working VCN on this board revision at all.

### G7 CORRECTION (2026-09-12, injection audit): the "runtime unlock closed" verdict was PREMATURE

- The S2-L9 wedge = the WRONG TRANSPORT, not a dead region: I used the sec mem64 SMN write (msgs 0x2B/0x2C); the FIELD-PROVEN writer of the 0x0900Cxxx bank = the Q3 msg 0x98 smn_write32 (VULN-1 PoC: all 56 bank records accepted, readback OK — VCN-LOCK-MECHANISM §A3).
- The unified two-lock theory now explains every campaign wedge without a dead bus: LOCK 1 = the gasket aperture (the 0x0900Cxxx program — runtime-writable via msg 0x98); LOCK 2 = the DFG POWER GRANT (the APCB DFG policy: the VCN master sits under the wildcard baseline perm 0x1f WITHOUT the power/reset bits 5/6 — the explicit rows sub 06 -> 0x63 / sub 08 -> 0x23 have them). Without the grant the power transaction is DENIED — it never completes: the exact S2-L5b/L8 signature, and the born-locked statuses (dom14 0x41, dom17 0x80000002).
- The injection audit (docs/research/2026-09-12-injection-audit.md): S1 = the APCB DFG region (UNSIGNED, checksum-only, solved, patch candidates ready, D3-A/B2 images built+verified 26/26) = the primary flash surface; S2 = the x86 DXE region (UNSIGNED, field-proven modifiable — 1,005,160 bytes changed in production mods; carries UnlockDxe/ProbeApp); S3 = the SMU runtime transports (msg 0x98 + 0x61 repoint — no flash); S4 = the signed gasket 0x24 / policy 0x45 (blocked; BYPASSED by doing lock 1 at runtime); S5 = DEBUG_UNLOCK/keys (closed).
- The unlock plan: R = runtime (msg 0x98 aperture -> dom6 proven -> the dom14 doorbell -> the bounded ack -> the arbiter); F = flash D3-A (the APCB grant patch, reversible, the control image) if R needs the grant. Order: R-only first (VULN-1 records were accepted on the unpatched board), then F+R.

### S2-L10 (stage R): dom14 denial is TOTAL — runtime route exhausted (2026-09-12 07:14-07:17 PKT, mode1, hardware-verified)

- mode1 (the 1.92 probe kernel), the full proven runbook (unlock, fire 0x61, gasket 59/59 commit=1, dataplane 15/15), THEN the complete VULN-1 aperture replay: 56/56 ACCEPTED, bank-12 control = 0x1. The S2-L9 wedge = fully attributed to the mode2 environment.
- The dom14 request doorbell fired; the ack read wedged (identical to S2-L8). FIVE experiments across mode0/mode1/mode2, with and without the driver table, with and without the aperture, fw path and direct path — the dom14-cluster power transaction NEVER completes.
- FINAL VERDICT: the dom14 power-up is hardware-denied at runtime, below every runtime-reachable register. The runtime unlock route is exhausted (not "prematurely closed" anymore — closed by exhaustion of the method space).
- The remaining route = the boot-time application by the PSP: (a) D3-A (the APCB DFG grant patch — the unsigned, checksum-only surface, built + 26/26 verified, needs the programmer + the operator approval) = the lock-2 grant test; (b) the D3-B2 carrier path (the signature-blocked, two no-video results). The inverted model (the PSP powers the VCN itself at boot per its policy; the donor 0x03E810=6 = the VCN segment enable) ranks the boot-time route first.
- External thinking skills installed (the user-directed): .agents/skills/{lateral,inversion,provocation,random-stimulus,concept-fan,analogy,scamper,six-hats,worst-idea} (danium/lateral-thinking, MIT, pinned b1aad86) + universal-critical-thinking (onatvural/Claude-Skills, the license not stated in the archive). The inversion pass produced the S2-L10 combination test; the premortem = the flash rollback discipline (the programmer, the verified dumps).

### 2026-09-12 PSP boot-time five-domain program (t28, loop decode)

The t28 PSP body (type 0x28, 108KB, ARM Thumb-2) contains the boot-time per-domain program: write 1 to SMN 0x1F8A4, then zero FIVE consecutive registers 0x1F8C4/0xC8/0xCC/0xD0/0xD4 from a 5-entry (addr,value) table @t28 local 0x188d8 (the runtime ptr 0x00e188d8, the load base 0x0E000000). Five registers = the five live SMU domains (dom6/7/14/15/17; the dom14 = the third = 0x1F8CC candidate). The stock zero-writes do not clear the dom14 born-busy 0x41. The next decisive check = the live SMN read of 0x1F8A4..0x1F8D4 at the boot baseline vs after the wedged dom14 request. The svc #0x7c = the inferred TOS register-write syscall. The VCN-bank refs in the PSP: t02 (the boot loader) = 0x0900C0EB; t28 = 0x0900C004 x3 (the literal pools).

### 2026-09-12 D3-B2 flash test: signature rejection is FATAL — carrier route closed (hardware-verified)

- D3-A (the APCB DFG grant patch, unsigned, checksum-only) flashed via CH347T (readback byte-exact), booted cleanly on mode1 — the unsigned APCB surface is field-proven accepted. The full runtime chain applied (gasket 59/59, dataplane 15/15, aperture 56/56), but the dom14 doorbell wedged identically (the status 0x41 before = born-busy). The DFG grant theory (lock 2) is DISCONFIRMED by flash test.
- D3-B2 (the full unlock carriers: the gasket VCN program + the 0x45 TOS policy, A-B unsigned) flashed via CH347T, readback md5 448f5df5dfd44b95cc82f5b170dfa94f = the image md5, byte-exact — the chip provably contained the exact D3-B2. Result: the board FAILS INITIALIZATION (the operator-reported, the third no-video-class result, now with the flash procedure excluded as the cause). The PSP rejects the unsigned $PS1-region carriers and does not reach a boot.
- CAMPAIGN VERDICT (the elimination table complete): the dom14 denial survives the driver table, the gasket xx234, the aperture program, the dataplane, the DFG grants (D3-A), and the boot-time carrier route is signature-blocked (D3-B2). Every software-reachable route to the VCN power grant is exhausted on this board revision: runtime (5 experiments, mode0/1/2), APCB DFG (flashed, disproven), unsigned carriers (signature-fatal). The remaining classes: the PSP signing/verification key material RE (the loop's charter goal (a)) and the hardware/fuse class (out of the software scope).
- The rollback performed: board_before_d3a.bin (the pre-experiment state, md5 86440b821eb8fd2e15b2b2228b35d9af) flashed + the independent readback byte-exact (0 diffs). The board is restored.
- The offline loop decode stands: the PSP t28 boot-time five-domain program (0x1F8A4<-1; 0x1F8C4..D4<-0; the dom14 = 0x1F8CC candidate) — the live SMN read of that range at the boot baseline = the remaining cheap decisive check for the domain-register semantics.

### 2026-09-12 D5 unlock-only DXE laboratory BIOS built (static verification)

- Built `candidates/d5-smu-unlock-lab/BC250_D5_SMU_UNLOCK_LAB_from_pre-d3b2-retest.bin` (16 MiB, SHA-256 `dec17ca81f513c28fa5a3227b3745c4c6ceb6aba68fe3d24fce8110df54ae3f1`) from the exact pre-D3-B2 board state that had booted mode1 (SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`).
- Boot-probability design: preserve every signed PSP/SMU/ABL/TOS, SEC_GASKET, policy, BHD, and APCB byte; add one x86 DXE driver only. It runs the previously hardware-verified BIOS-3 SMU debug unlock at ReadyToBoot and performs no automatic VCN power, clock, gasket, dataplane, dom14, or MMIO operation.
- Static checks PASS: RELEASE EDK II build; valid X64 PE32+ EFI driver; FFS type 7/TRUE Depex; four parsed FVs; injected module independently extracted byte-identical; PSP `0x63FFFCC8`, BHD `0xECE7B2E6`, APCB `0x32` checksums match; all changes confined to the recompressed x86 DXE FV. Detailed record: `docs/action-logs/2026-09-12-d5-unlock-lab-bios.md`.
- Evidence boundary: candidate is statically verified only. Correct-wiring cold boot, DXE dispatch, unlock persistence, VCN MMIO, rings, and codecs are UNRUN.
- Hardware write/readback update: D5 was written to BC250-01 via CH347T/Winbond W25Q128.V; flashrom reported `VERIFIED`; the independent 16 MiB readback is byte-identical to D5 (SHA-256 `dec17ca81f513c28fa5a3227b3745c4c6ceb6aba68fe3d24fce8110df54ae3f1`). The readback reparses with four FVs and matching PSP/BHD/APCB checksums, and its extracted unlock DXE is byte-identical to the build. Evidence class is hardware-verified at SPI write/readback only; boot and unlock remain UNRUN.
- Cold-boot correction: D5 failed initialization; the operator observed static indicators and no initialization. Because D5 changed both the compressed-DXE reconstruction and automatic ReadyToBoot unlock execution, the failure is not attributable to either mechanism without UART/status evidence. D5 is boot-failed and the bulk-recompressed-FV automatic-DXE class must not be repeated. Restore `pre_d3b2_retest.bin`; future work must change method class to an external UEFI app or byte-local/in-place FFS replacement.
- D6 method-class change: built `candidates/d6-coreunlock-slot-smu-unlock/BC250_D6_CORE_SLOT_SMU_UNLOCK_from_pre-d3b2-retest.bin` (SHA-256 `bd7689d6e2da32079878c507c472d5fc6d7208bc8f7dca208be4115c83d2db07`). It replaces the 12,288-byte PE32 payload of the already present `Bc250CoreUnlockDxe` FFS with the same-size SMU-unlock DXE. Independent decompression proves every other inner-FV byte identical, so FFS topology, sizes, Depex, UI, order, and following offsets are preserved. PSP/BHD/APCB and all signed bodies remain byte-identical. Static checks PASS; hardware boot and unlock are UNRUN.
- D6 SPI update: written to BC250-01 via CH347T; flashrom `VERIFIED`; independent 16 MiB readback is byte-identical to D6 (SHA-256 `bd7689d6e2da32079878c507c472d5fc6d7208bc8f7dca208be4115c83d2db07`). Readback parser and replacement extraction PASS. Evidence is hardware-verified at SPI contents only; cold boot and unlock remain UNRUN.
- D6 cold boot FAIL: operator reports no initialization. Because decompressed FV topology and every byte outside the replaced PE32 were preserved, D5's insertion/layout variables are excluded. Failure remains attributable either to the reconstructed LZMA transport/capsule or to execution of the SMU-unlock/ReadyToBoot path. D7 no-op replacement in the same slot is the smallest discriminator.
- D7 no-op discriminator was written and independently read back byte-identical (SHA-256 `dccd89144aea31408bca9519937382a838eb4c4c58b59a11272e207cf473aac1`). Four FVs, PSP/BHD/APCB checksums, unchanged CoreUnlock FFS metadata, and extracted no-op PE identity all PASS. Cold boot remains UNRUN; SPI verification alone does not distinguish reconstruction rejection from D6 unlock execution failure.
- D7 cold boot FAIL: operator reports no initialization. Newly installed skill application found a concrete envelope difference: the accepted baseline LZMA-alone header declares exact decoded size `0x420010`, while D5-D7 encoded `0xffffffffffffffff` (unknown size). Host parsers accept both, but the firmware decoder may require the bounded size. D8 no-op control restores the exact accepted header (`5d000000011000420000000000`) and passes static structure/extraction checks; hardware is UNRUN.
- RSA weak-key audit on 11 `$KDB` RSA-2048 records (10 unique moduli, all e=65537): no shared factor, no factor <=100,000, no Wiener small-d result, and no Fermat factor within 1,000,000 steps. Generic RSA recovery remains closed absent a new oracle, fault, partial-prime leak, or verifier implementation evidence. Report: `evidence/firmware-audit/kdb-rsa-weakness-audit.json`.
- D8 SPI update: explicit-size LZMA no-op control written to BC250-01; flashrom `VERIFIED`; independent readback is byte-identical (SHA-256 `e7c8223b56380c8aba1ed04a26cb04306f8ba331fac82121bedf70ff8a62099a`); parsers and extracted PE match. Cold boot is UNRUN, so firmware-decoder acceptance is still unknown.
- D8 BOOT PASS (hardware-verified): operator observed initialization; root independently verified a fresh SSH boot (uptime 0 minutes, kernel `7.2.0-1.92-cachyos-vcn-bc250`, mode1 command line). This proves the D5-D7 construction failure was the LZMA-alone unknown-size header. The accepted firmware path requires the explicit decoded size (`0x420010`) in header bytes 5..12. D9 should retest the same-slot SMU unlock with this envelope fix.
- D9R SPI update: fresh-D8-NVRAM rebased SMU-unlock candidate (SHA-256 `c46392ceca989f0bd558077bf07bc40490645710710d6c48c7d42e8eb328834d`) written via CH347T; flashrom `VERIFIED`; independent 16 MiB readback and extracted PE are byte-identical; four FVs and PSP/BHD/APCB checksums PASS. Cold boot and actual SMU unlock remain UNRUN.
- D9R BOOT + UNLOCK PASS (hardware-verified): mode1 Linux booted; root verification returned `alive=True`, secure Q3 `0x2A` SMN read of `0x0005A870` with status `0x01` and value `0x77`, then `alive_after=True`. D9R therefore provides a verified BIOS-resident ReadyToBoot SMU debug-unlock substrate. VCN power/gasket/dom14/MMIO/rings/codecs were not touched and remain unverified.
- D10 early-DXE candidate built (static verification): same verified unlock/fixup as D9R, moved from ReadyToBoot callback to immediate entry in the existing first CoreUnlock slot; no VCN/gasket/dom14/MMIO action. Image SHA-256 `f9bf499d94c3da9ce9a3cb140519e3f73ca959296fed394090d1b649872b3f7d`; explicit-size LZMA header and all structural/independent extraction checks PASS. Hardware is UNRUN; fresh NVRAM rebase is required before write.
- D10R SPI update: rebased on fresh post-D9R NVRAM and written via CH347T; flashrom `VERIFIED`; independent readback is byte-identical (SHA-256 `91340dad8f1a6ac57deb9d8cd749e0a2c0bd8ec62c1051aab476c3cd61bdbaf8`); four FVs, PSP/BHD/APCB checksums, and extracted early-unlock PE all PASS. Cold boot and early-unlock execution remain UNRUN.
- D10R BOOT + EARLY UNLOCK PASS (hardware-verified): fresh mode1 boot reached Linux; secure Q3 `0x2A` SMN read `0x0005A870` returned status `0x01`, value `0x77`, with SMU alive before and after. Immediate first-DXE unlock is therefore boot-safe and persists into Linux. VCN-specific writes remain unrun.
- D11R SPI update: early-DXE unlock plus 56-write VCN bank-12 gasket candidate written via CH347T; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `d39973744aa71efdccbb925639822080ed933b6cc7f70c6ea313a399f34ae305`); four FVs, PSP/BHD/APCB checksums, and extracted PE PASS. Cold boot and gasket effects remain UNRUN.
- D11R cold boot PARTIAL/FAIL: board reaches BIOS splash but never releases to Linux/network. D10R differs only by the absent 56-write early gasket stage and boots, so the full bank-12 sequence at initial DXE timing causes the failure. Exact write/commit state is unknown without UART. Do not repeat; restore fresh pre-D11 D10R capture `addef288...`. Next method must bisect timing and sequence with observable progress.
- D11R rollback PASS at SPI layer: fresh capture showed only 28 bytes of boot-attempt NVRAM drift; payload regions remained intact. Restored exact fresh pre-D11 D10R state and independently read back byte-identical, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`; structural checks PASS. Cold-boot recovery confirmation remains UNRUN.
- D12 SPI update: D10R immediate unlock plus full 56-write gasket deferred to ReadyToBoot was built and written; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `aeaa96bc116b2799363b9d6294d1217ed07403b46ec9f1bc03b76f15c851d2eb`); four FVs, checksums, and PE extraction PASS. Cold boot and gasket effect remain UNRUN.
- D12 cold boot PARTIAL/FAIL (hardware-verified): Linux/SSH boots, but display freezes and amdgpu is unbound. SMU `alive=False`; secure Q3 `0x2A` times out. Kernel reports SMU hw_init `-62`, fatal GPU init, PSP DESTROY_TMR failure `0x80000306`, and amdgpu probe `-62`. Full 56-write gasket at ReadyToBoot wedges SMU before driver init; commit is inconclusive/unread. Combined with D11R, timing shift alone does not solve the sequence. Restore D10R and bisect record subsets.
- D13 first-half slice built (static verification): D10R early unlock plus only gasket records 0..27 at ReadyToBoot; records 28..55, lock and commit tail excluded. Image SHA-256 `00164ea687b2622b117f779c74c27bc810ef4f8b6f885a8fea6a5fa44f58eaeb`; structure and independent extraction PASS. Hardware UNRUN.
- D13 SPI update: exact first-half slice written via CH347T; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `00164ea687b2622b117f779c74c27bc810ef4f8b6f885a8fea6a5fa44f58eaeb`); four FVs, checksums, and PE extraction PASS. Cold boot and SMU effect remain UNRUN.
- D13 cold boot PARTIAL/FAIL: Linux/SSH boots, but SMU is already dead (`alive=False`, secure Q3 timeout); amdgpu SMU hw_init fails `-62`. Therefore the wedge lies in gasket records 0..27; records 28..55, lock, and commit are excluded. Next slice is 0..13.
- D14 SPI update: gasket prefix records 0..13 written via CH347T; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `6c0c23c5ff6fae99e479f8c84b2caa53a7494103c798ca72ce7f0c9d23a6c238`); four FVs, checksums, and PE extraction PASS. Cold boot and SMU effect remain UNRUN.
- D14 cold boot PARTIAL/FAIL: Linux/SSH boots, but SMU `alive=False`, secure Q3 times out, and amdgpu SMU hw_init fails `-62`. Culprit narrowed to gasket records 0..13; later records, lock, and commit excluded. Next prefix is 0..6.
- D15 SPI update: gasket prefix records 0..6 written via CH347T; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `42262d1ca995cdb9309f246aa289848a4a53dcedbbae896e5da213129b991b95`); structure and extracted PE PASS. Cold boot and SMU effect remain UNRUN.
- D15 cold boot PARTIAL/FAIL: Linux boots, but SMU is dead and amdgpu SMU hw_init fails `-62`. Culprit narrowed to gasket records 0..6. Next prefix is records 0..2.
- D16 SPI update: gasket records 0..2 written via CH347T; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `8ce1bcf0082816a62578a78c72731c1c36bc66b35c9bef06ff06cee5f49cbe71`); structure and PE extraction PASS. Cold boot/SMU effect UNRUN.
- D16 cold boot PARTIAL/FAIL: Linux boots but SMU is dead and amdgpu SMU hw_init fails `-62`. Culprit narrowed to records 0..2 (`C234`, `C830`, `C834`). Next candidate writes record 0 only.
- D17 SPI update: control-only `0x0900C234<-0` candidate written; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `d900e2ac87815a47520cb68c266bd308eb6375f39a98df6bd69b43cfd6ca4f82`); structure and PE extraction PASS. Cold boot/SMU effect UNRUN.
- D17 cold boot decisive negative: Linux booted on stock kernel 7.2.0-1.1 (not mode1), but SMU was dead and amdgpu SMU hw_init failed `-62`. Since D17 adds exactly one gasket write, `0x0900C234<-0` at ReadyToBoot is sufficient to wedge SMU. All later gasket writes are excluded as necessary causes. Do not issue C234 at this stage again.
- D18 SPI update: C830/C834 mask writes without C234 written via CH347T; flashrom `VERIFIED`; independent readback byte-identical (SHA-256 `3111d97702867cb8c32d10804b4ac87fa17c70bf255cbed33fcf1d85e45ce7a0`); structure and PE extraction PASS. Cold boot/SMU effect UNRUN.
- D18 cold boot PARTIAL/FAIL: mode1 Linux boots, but SMU is dead and amdgpu SMU hw_init fails `-62`. Without C234, C830+C834 still wedge; at least one mask register is independently inaccessible at ReadyToBoot. Next isolate C830 only, then C834.
- D19 cold boot decisive negative: mode1 Linux boots, but the bounded liveness test returns `alive=False` and secure Q3 `0x2A` times out. D19 adds exactly one ReadyToBoot write over the verified D10R substrate: `0x0900C830<-0x00FFFFFB`. Therefore C830 alone is sufficient to wedge the SMU at this stage; C234, C834, later records, and commit are excluded as necessary causes. Do not issue C830 at ReadyToBoot again. A C834-only control remains useful only to classify that register independently.
- D19 single-variable independently re-verified (2026-09-12 audit, static-analysis): `/tmp/d19_single_variable_check.py` decompresses the DXE FV of both images (4,325,392 B each, FFS@0x88, payload@0xA4): all bytes outside the 12,288 B PE32 payload identical, payload == shipped `Bc250EarlyUnlockReadyC830OnlyDxe.efi` (`dd242b34...`), signed region `0x8E0000:0xAE0000` identical, bytes outside the capsule region identical. Candidate == postwrite readback (`2551ef66...`, `cmp` 0); extracted PE == shipped PE; `scripts/firmware_audit.py` on the readback: PSP/BHD/APCB checksums match, 4 FVs. Full record: `docs/action-logs/2026-09-12-flash-ladder-audit.md`.

### G7 CORRECTION (2026-09-12 audit): APCB DFG is NOT boot-unsafe; D-substrate carries the DFG mutation

- Direct byte measurement this session (struct `<I` at `0xAB1000+0x130/+0x16C/+0x10`): `post-rollback-d10r.bin`, `prewrite-d18.bin`, and `postwrite-d19.bin` ALL carry DFG `0x007FFF00/0x007FFF00`, checksum `0x32` — not stock `0x001FFF00/0xF2`.
- The 2026-09-11 verdict "APCB DFG-only edit is boot-unsafe, not a safe control" rested on the pre-display-wiring-fix no-video series, which G7 (2026-09-11T22:00+05:00) already ruled non-discriminating. It is now directly disproved: D8, D9R, D10R, D13, D14, D15, D16, D17, D18, D19 all boot to Linux/SSH carrying the mutated DFG.
- Consequence 1: `docs/research/2026-09-12-unlock-paths-map.md` P3.2 status is corrected (DFG tokens boot; the wedge series ran ON the grant).
- Consequence 2: the two-lock theory's lock 2 (DFG power grant) was PRESENT in every D12-D19 wedge test. The ReadyToBoot gasket wedge is therefore a transport/context effect (write to the `0x0900Cxxx` bank while the VCN island is down), not a missing-grant effect. Do not re-test the grant; test the context (power the domain first) or abandon the DXE-time aperture.
- Consequence 3: D17/D19 single-variable attributions stand, but qualified with substrate `DFG=0x007FFF00`.
- G6 breach recorded: D11R/D12/D13/D14 are 4+ same-class failures (DXE-time gasket -> SMU dead) with no method-class change; the breaker should have fired after D14. D15-D19 added 5 more flashes for ~2 bits. Future gasket work at DXE time is closed; the remaining aperture lever is runtime-after-power-up (S2 order) or boot-time PSP application (signature-blocked).

### P1.5b interim (2026-09-12, MCP live): PEIM builds a $VNI table, IDs are not registers

- `0193_AmdNbioGfxARIPei_te.bin` (`63413be2...`, 78 fns) via Cutter+MCP on loopback 8001: fcn.00001bf8 fills Init Config Struct defaults (`0x1e0/0x1e1 <- 0x3` is defaults-fill, not a VCN clamp); fcn.00004c88 builds the `$VNI` table (5-byte records: u16 ID + masked byte + value; IDs 0x1000+, struct+0x1e0/0x1e1 -> IDs 0x10c3/0x10c4).
- Table IDs 0x13a9..0x13b7 are NOT NBIF registers — S4 chain-report candidates explained as a misread; S4-negative closed. `$VNI` magic in no extracted PE (runtime-built); `IDS` consumers = 5 DXE ARI drivers. Full record: `docs/action-logs/2026-09-12-deep-re-pass1.md`. Scratch: `/tmp/gfxpei-4c88-pseudo.c`.
- DXE side (port 8002, `0025_AmdNbioGfxARIDxe` 58 fns): no hardcoded $VNI IDs (table-driven); hook 0xB000000D dispatcher (fcn.00012274) + generic IDS wrapper (fcn.000125e0); hook constant occurs ONLY in 0025 of all 16 ARI binaries. Entry/dispatcher/table-builder/post-helper/cpuid-freq roles mapped; 0025 programs no NBIF HW itself. All 7 ARI DXEs have I/O+MSR+CF8 sites.
- Fabric side (port 8003, `0021_AmdFabricAriDxe` 81 fns): hook 0x20000006 dispatcher (fcn.00013658); MMIO-pair string DEAD here, ALIVE in `0196_AmdNbioBaseARIPei`; ReadyToBoot callback disables ext-config-access then DF-reads (0,0,1,0x200) testing bit 27. DF-indirect primitive DECODED (fcn.0001307c): MMIO 0xE0000000, index 0x405C, data 0x4098 — the TRUE fabric transport.
- PEI side (port 8004, `0196_AmdNbioBaseARIPei` 117 fns): MMIO-pair strings DEAD in all 4 carriers — shared-source leftovers. Chain BYTE-CONFIRMED: 0x21c4 (MMIO-base setup) -> 0x2996 -> 3x `call 0x3cf2` (0x2a41/5a/8d) + 1x from 0x3e7a; DF-codec sites file 0x3CCC (in 0x3c0b) + 0x3DB7 (in 0x3cf2); counters in 0x3e8e-0x3f40 zone. 0193 clamp (file 0x242c) and serializer (files 0x4ce1+) re-verified in-function. Session lesson (G7): TE vaddr==paddr must be confirmed from segments before objdump base; Rizin indirect xrefs need instruction check. INFERENCE stands: fabric HW programming is PEI-phase via patchable PEIMs; DXE-time writes come too late. Next: exact stock pair enumeration (needs DF-reg bits = hazard, or emulation with runtime table).

### G7 CORRECTION (2026-09-13): Q4 0x10 is a VID write, not a query

- Battery premise "(i) Q4-alias read-only queries (same risk class as Q0-1)" disproved by static read of board `bc250-smu-unlock/bc250_smu/api_q3.py`: Q4 msg numbers alias Q3 handlers, and Q3 `0x10` = `q3_0x10_unforce_cpu_gpu_vid(kind)` (state-changing). Q4 `0x10` excluded from the approved first-contact batch; Q1 has no Q3 alias (independent queue). Correction recorded before the batch runs.

### G7 WEDGE CLASS (2026-09-13, hardware-verified): Q0 0x06 wedges the SMU firmware

- Q0-2 attempt 2 (THP variant, boot `2b77d998`, mode1): 512-page DMA buffer at phys `0x176000000` staged via Q0 `0x04/0x05` (both OK); `0x06` answered `st=255 ret=0x0` (active refusal, 0xFF bail class, zero bytes transferred); `alive_after=false` and still dead +90 s (secure Q3 `0x2A` "timed out - SMU wedged, cold cycle"). Amdgpu collateral: repeating `SMU: No response msg_reg: 6`, `Failed to export SMU metrics table!`, one `ring gfx_0.0.0 timeout`. Host SSH survives.
- Lesson: the Q0 table-location pointer is LIVE-SHARED with the driver's periodic metrics-table export flow — stealing it via 0x04/0x05 plus firing 0x06 desyncs SMU/driver and hangs the firmware. The "0x06 is a read" premise is disproved; do not re-fire 0x06 against a live driver without a quiesce design. Recovery = operator cold power-cycle (warm reboot may not reset the always-on SMU). Full record: `docs/action-logs/2026-09-12-q0-table-track.md` (attempt 2).
- Method note: `madvise(MADV_HUGEPAGE)` + settle rounds deliver a 512-page run at t+0 on THP mode `[always]` where plain-anon mappings top out at 8 pages — the proven DMA-buffer transport for any future staged-DMA work.

### G7 TRANSPORT (2026-09-13, hardware-verified): bare setsid does not survive SSH disconnect

- Discriminator: `sudo -n setsid -f sleep 120` launched over SSH was gone <30 s after disconnect (SLEEPER_GONE), same silent death as both Q0-2 holders (PIDs 38730/2464, no traceback, no OOM trace). Root cause: `setsid` escapes the POSIX session but stays in the systemd session-scope cgroup, which is reaped on disconnect. The "holder keeps DMA target valid until reboot" rollback story was therefore illusory in both Q0-2 runs. Any future cross-SSH holder MUST use `systemd-run --scope` (or equivalent new-scope launch), or the run must be redesigned single-shot with per-run re-staging. Track record: `docs/action-logs/2026-09-12-q0-table-track.md` (attempt 3 + anomaly).

### G7 HAZARD (2026-09-13, hardware-verified): 0x1F8xx secure READS wedge the mailbox

- `sec_smn_read32` × 6 over `(0x1F8A4, 0x1F8C4..0x1F8D4)` on healthy mode1: every read `SmuTimeout`, `alive_after=False`, still dead after 30 s settle → operator cold cycle required. S4's "NBIO reads safe" covered ONLY 0x101xxx/0x14xxxxx — safety is PER-REGION. NEVER probe 0x1F8xx via the secure path (same hazard family as DF-space reads). Corroborating inference: PSP-guarded domain-control block (a read hanging the mailbox implies protection circuitry). Record: `docs/action-logs/2026-09-13-pei-vni-hunt.md`.

### P1.5c PEI $VNI/IDS consumer hunt (2026-09-13, static-analysis on our images)

- Builders ×3 (0189/0193/0196) share the IDENTICAL 658-entry ID→struct-offset map (0x1000..0x1459 → +0x1..0x8a4); struct ~0x8a5B shared AGESA source. Correction: struct+0x1e0→ID 0x10c2 (deep-re note was off-by-one).
- 0196 `0x2996` = DF aperture programmer (base/limit/enable × dies × units) fed by `0x21c4` MMIO setup from TOP_MEM MSRs (not $VNI); `0x3cf2` = validated DF-WRITE primitive (die<2/unit<4/func<8/reg<0x400 aligned; sel=0xff direct store via E0000000 wrap, else index/data) → PEI transport+primitive proven capable of ARBITRARY DF writes in-envelope. A pair-injection PEIM patch is mechanically sound.
- DXE consumer = `$IDS`-validated hook dispatch (0025: hook `0xB000000D`, runtime-filled list at 0x2990, default handler locates IDS protocol `{0ecad4a0-75e9-46d7-a3a6-81fe173f2eca}` found in 8 DXE drivers; installer open). 0021 DF code is READ-only; DXE ARI = observe/dispatch/lock, not program.
- t28 five-domain table verified byte-exact in OUR image at 0x188d8 (`0x1F8C4..D4 ← 0` + null; ours = robin3 file + 256B tail). 0193 `0x4c58/0x4c88` unreachable in-module (dead or cross-module PPI; secondary).
- OPEN in order: (a) (reg,val) for VCN DF aperture in fabric-ID terms; (b) 0x0900Cxxx x86-PEI reachability (SMN vs PSP-only — needs flashed PEI test); (c) struct-field source (data-only variant); (d) IDS installer. Full record: `docs/action-logs/2026-09-13-pei-vni-hunt.md`.

### Metrics oracle + runtime→PEI pivot (2026-09-13, hardware-verified)

- Q0 table located in OUR fw image (`f546f118...`) at file `0x6f74` (Q3 pattern-verified at `0x736c` ↔ SRAM `0x746c`, delta +0x100; Q0 has populated 0x01-0x07 + distinct version stubs) → Q0 `0x07` handler = `0x1bafc`. Upstream (torvalds/linux v6.8, comparison-only) uses a DIFFERENT PPSMC dialect (v11: 0x12/0x13 transfers; v12: 0x1A-0x1D; 0x34=SetSoftMaxVcn) — ours is custom; response codes shared (1/FF/FE).
- Quiesced table-id sweep: `0x06 id=6 → st=1` with EXACTLY 244 bytes (= `sizeof(cyan_skillfish SmuMetrics_t)` upstream: 2×116 + 12) — table 6 IS live metrics on our fw. Artifact `evidence/runtime/20260913-quiesced-metrics-table6-244B.bin` (`b29f56eb...`): VCLK=0MHz (VCN video OFF, the target), DCLK=1111MHz (selective power), GFX 1500/SOC 1254/MEM 450MHz, ~48-53C. Metrics oracle PROVEN quiesced (no driver needed); quiesced-only (mode1 foreign-location 0x06 = wedge class).
- `0x07` refused (255) for ALL ids [0,1,4,6,7] with marker content, with and without VMID (`0x34(0)` accepted, st=1 — VMID not the key); healthy mode1 driver NEVER posts to `0xCEC8` (gate stays 0xFF, 1KB window byte-identical quiesced vs mode1: `evidence/runtime/20260913-mode1-sram-0xcec8-1k.bin` `d5b385e8...`), so no driver template exists to replay.
- G6 PIVOT: runtime-SMU class exhausted (S2-A/L5b/L8/L10, D12-D19, Q0-2, UC2 all fail past the boot-time lock); unifying inference = bus-level isolation (PSP-applied, hardware-locked) is the single root cause. `0x5C`-with-proper-table PREDICTED to wedge identically (S2-L6 mechanism is table-independent) — deliberately NOT fired. PEI-time road now primary (unsigned-FV flash surface proven by D8/D9R/D10R). Full record: `docs/action-logs/2026-09-12-q0-table-track.md` (UC2 steps 1-4).

### G7 RETRACTIONS (2026-09-13, static re-decode of our bytes, i386/x86-64)

- The pre-compaction "CF8-EN → CFC WRITE 0xE0000021" trace is RETRACTED: 0196 `0x3c0b` (df-READ) / `0x3cf2` (df-WRITE) and the 0021 DXE mirrors (`0x307c`/`0x319c`) are PURE-MMIO @ E0000000 (DIRECT: `[E+fabric<<15+func<<12+reg]`; INDEX: `[E+(fabric&0x18)<<15+0x405C] ← sel<<16|func<<11|reg&0x7fc|1`, data @ +0x4098). No CF8/CFC anywhere on this path.
- F6 "0021 DF code is READ-only; DXE ARI = observe/dispatch/lock, not program" is RETRACTED on both counts: 0021 HAS a write primitive (`0x319c`, DIRECT + readback-verify) with NINE write callers (0xb09 RMW set-bit0 DIRECT func4/reg0x44 with constant sel=0xff; 0xc88/0xcc1 RMW with RUNTIME (sel,func) = IDS/$VNI-driven DF programming) + 24 read callers. DXE-time DF programming EXISTS → second injection path AND an override risk for any PEI injection (enumerate before flash).
- F6 "SMN reads of 0xDF030136/137" is RETRACTED: `0xDF030132-137/189-194` are AGESA ASSERT IDs passed to `0x1814`, not SMN addresses touched by x86 code.
- Supporting decodes: `0x2996` = 8-arg DIRECT-triple programmer (base/limit/enable+attr at `class<<4+{0x200,0x204,0x208}`, func0); ebx==0 at all 7 stock call sites (no writes in 0x21c4-0x2990) → stock PEI programs ONLY class-0 DIRECT windows; `0x3dde` = RMW wrapper; `0x3e88/0x3eab` = die/unit discovery via DIRECT func1/reg0x200. No 0196 caller uses the INDEX path.

### G7 HAZARD (2026-09-13, hardware-verified): OS-side DF/SMN cycles can HARD-HANG the board

- Read-only dfprobe kmod (`79d38248...`, DF-MMIO P1-P5 + `amd_smn_read` S1-S6 incl. VCN-bank + t28 LAST; built with `make LLVM=1`, kernel = clang-22+lld): `insmod` → SSH timeout, +45 s ping 100% loss + `No route to host` → hard hang, no self-recovery (nowatchdog). dmesg LOST: DF index/data cycle vs SMN-guarded read attribution UNKNOWN. DO NOT probe DF/SMN from booted OS again (read-only PCI-CFG via setpci stays allowed); kmod DF/SMN joins the parked runtime class. Remaining live-proof road = UEFI-Shell .efi (firmware context; NOTE: Shell starts after ReadyToBoot signal, so DF-openness there is UNPROVEN — the probe tests it; needs USB + operator boot; not built, no EDK2 locally). Self-note: insmod intent was not pre-logged (G4 violation, owned).
- OS-path inventory that led here (all clean-negative): D18F0 xB8 locked `0x280` (write does not stick); D18F3 xB8/BxC dead 0; kernel SMN offsets x60/x64 show no PCI residue (k10temp=hwmon2 is MMIO-based on 7.2.0); /dev/mem EPERM; `umr` present but debugfs instance is `0000:01:00.0` with no SMN nodes.

### UC-V0 verdict (2026-09-13): V1 target list EMPTY, mechanism proven

- Conversion (structural): SMN seg-0x03 + off<0x400 → INDEX (sel=bits[23:16], func=off[12:10], reg=off[9:0]); every seg-3 addr in stock/VCN/Cezanne fits with func=0. 0x203=program / 0x281=commit (3 regs gain low-byte FF). Seg-0 small + seg-9 transports unresolved (bits[15:13] ambiguous).
- TARGET VERDICT: stock→VCN gasket seg-3 delta = EMPTY (91/91 zero diffs) — the VCN variant's entire delta = 56 seg-9 HWID-12 writes; Cezanne seg-3 delta (113 lines) confounded by different silicon (extra 0x3D201xx instance, DRAM-map values). V1-as-specified (DF-windows-only) HAS NO TARGET LIST → V1 BLOCKED (spec `specs/2026-09-13-pei-df-aperture-candidate.md` §8; design valid, targets missing). New blockers: OQ6 seg-9 transport/x86-PEI writability (Shell-.efi reads first), OQ7 enumerate 0021 DXE DF-write runtime targets (override risk).

### G7 correction: D19 transport comparison (2026-09-14)

- The alleged working-Q3-`0x98` versus D19-Q3-`0x2B/0x2C` transport split is unproven and currently contradicted by source. `bc250_smu/primitives.py::smn_write32()` uses `0x2B/0x2C`, and `recon/smn_vcn_gasket_unclamp.py` calls that method for the historical 56-write replay. Q3 `0x98` is only an undocumented zero-argument handler in the inspected API. D19 remains evidence about ReadyToBoot context/timing; do not attribute it to a transport difference without a direct trace.

### VCN clock-slot reconciliation (2026-09-14)

The verified thunk `0x23744` uses slots 22/23/24, all mapped by the PMFW slot table to domain index 6. This matches the hardware-verified dom6 clock path and identifies the VCN-associated clock route. Q3 `0x5C` inputs 14/15/17 map to domains 2/3/4 and are not that direct VCN route. Domain-6 clocks remain insufficient because VCN MMIO is still isolated; the bridge transition is open.

### Board artifact retrieval and exact module provenance (2026-09-14)

- Operator powered the board; mode1 became reachable with kernel `7.2.0-1.92-cachyos-vcn-bc250`, cmdline `amdgpu.bc250_vcn_mode=1`, boot ID `1bb84c62-17f7-4e08-af55-0b61ec8c8c37`, GPU `1002:13fe`.
- Retrieved only the exact stage2b/stage4/stage5 sources and named outputs plus running `amdgpu.ko.zst` into `evidence/runtime/20260914-board-retrieval/`; no retrieved code was executed.
- Source-verifiable historical results: both stage2b outputs contain 59 accepted writes, bank-12 commit readback `1`, SMU alive; stage5 contains 15 accepted writes, commit `1`, and ten configuration reads. These do not prove VCN visibility.
- Correction retained: stage4 labels are invalid under the VCN2 register map. Its five all-ones results are raw numeric-address measurements only.
- Exact installed module: compressed SHA-256 `7424913c4864079865e8f792a54edc9c3d6a1bb1997ca0a916072e988d7dea40`; decompressed SHA-256 `7d6606ba80be79e49bb703f29b79a22fcc4b96d8c51b7799bf694f4d417d1ebf`; build ID `ca6bb73e0c93d32f1c80552e5093e7a766a3c924`. Installed-source equivalence and first failing instruction remain open.
- Exact binary audit corroborates patch-0011 mode selection and direct VCN firmware placement. Probe `hw_init` logs and returns without MMIO. Real `hw_init` begins with NBIO doorbell-range setup and later ring tests, while `vcn_v2_0_start` is a separate power-gating callback path. Correct the earlier attribution: the mode2 wedge is bounded to real VCN initialization, not proven to a specific first MMIO instruction in `vcn_v2_0_hw_init`.

### AMD 4700S versus BC-250 Gfx PEIM entry result (2026-09-14)

- Correct TE mapping and bounded IA32 CFG tracing show the C0A and BC-250 `AmdNbioGfxARIPei` entries each contain 380 reachable instructions, 43 direct calls, 6 indirect calls, one return, and the same mnemonic sequence.
- Both expose the same ordered UMA/memory-HOB diagnostic strings and no exact VCN-bank or known policy-address literal. Helper addresses and several service-token immediates differ, but their semantics are unresolved.
- The compact donor entry is not a distinct VCN-unlock mechanism and does not justify a module transplant. Continue with helper and `AmdNbioBaseARIPei` comparisons.
- Matched helper tracing: `0xB60↔0xBE0`, `0x6F6↔0x6FC`, and `0x9A8↔0xA06` retain identical CFG/mnemonic skeletons; `0x11BD↔0x13B1` diverges (49 instructions with an indirect IDS-table path in donor versus 15 instructions and two direct helpers in BC-250). This divergence is static only and does not justify transplantation.

### 4700S gate-value comparison (2026-09-14)

BC250 and 4700S share the NBIO copy/RMW path; live BC250 values settle at
13B1005C=0x8000, 13B10060=0xFFFF, 6A148=0x00800000, 6A14C=0x8,
33E0=0x3820. PCD token 0x55/0x68 defaults are zero-initialized and no active
setter delta is proven. 4700S is not an actionable unlock donor from this path.

## G7 SVC0x63 semantics correction (2026-09-15)

t02 SVC table maps0x63 to0x49F8, a per-type state check followed by0x19A0 resource teardown; cryptographic verification is not established. Retract wording that t28 `0x16D88` final `svc0x63` proves signature checking. ABL `svc#6` wrappers remain the signature boundary. See docs/action-logs/2026-09-15-svc7c-input-audit.md.

## D-R1 second-core IPC reachability (2026-09-15)

`0x1B514` forwards two dwords under operation `0xFE` through `0x10D0` to payload `0x01210700/0x01210704`; the supplied type-0x12 companion body is 262144 bytes with only eight non-zero bytes, so its receiver is absent from the corpus. The decoded `0x24732` callsite reaches that sender only when `0x246F4`'s d=20 record has `record+0x80==0`; d=19's in-range target takes the local-store branch and does not call `0x1B514`. Q3 `0x5C` reaches `0x2362C` with domain14, whose static address source is `0x0005C924` outside `0x05AFFF..0x05B7FF`; no receiver-backed Q3 VCN route is established. · evidence: `docs/research/2026-09-15-smu-ipc-d-r1-result.md`, `evidence/smu-ipc-d-r1/body2-structure.txt`, `evidence/smu-ipc-d-r1/disasm-24732.txt` · 2026-09-15, D-R1

## G7 D-R1 stride correction (2026-09-15)

`0x246F4` and `0x2362C` use stride 28, not 32: `subx8` followed by `addx4`/`slli 2` computes `((d<<3)-d)<<2`. `0x246F4` d=19/20/21 records `0xF924/0xF940/0xF95C` all select slot5, slot record `0xF6B8`, target `0x0006C8F8`, and local-store; d=20 `0x5B10C` IPC is retracted. `0x2362C` domain14 field `0xF92C` yields `0x0005C0FC`. The `0x233E8` IPC interval is `0x5B000..0x5B7FF` (lower-exclusive). Q3 msg1D has a direct chain through `0x2E6C8→0x2E448→0x2E481→0x23730→0x246F4`; d/value provenance remains open. · evidence: `docs/action-logs/2026-09-15-smu-ipc-d-r1.md`, `docs/research/2026-09-15-smu-ipc-d-r1-result.md` · 2026-09-15, D-R1

## G7 correction: tracked $KDB audit does not reproduce on the 5.00 clv base (2026-09-19)

- Claim that was wrong: that the tracked `evidence/firmware-audit/kdb-rsa-weakness-audit.json`
  result applies to the current base. It does not — `scripts/kdb_rsa_weakness_audit.py`
  hard-codes `specs = [("t50", 0x9DAD00, 0xDD0), ("t51", 0x9DBB00, 0x740)]`, and running it
  unmodified on `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (`ea578104…`) returns
  `key_count 0` — the tool reports nothing rather than failing loudly.
- Measurement that disproved it: on `ea578104…` the records sit at `0x9DB550..0x9DBE80`
  (8 × 0x150, t50) and `0x9DC350..0x9DC5F0` (3 × 0x150, t51), i.e. t50 base `0x9DB400`,
  t51 base `0x9DC200`. Record layout observed: `u32 size=0x150`, `u32 index`, `u32 0x0E`,
  `u32 exponent=0x10001`, 16-byte `kid` at +0x10, `u32 bits=2048` at +0x20, modulus at +0x50.
- Corrected result on the current base: 11 records, 10 unique moduli, 10 unique kids,
  all RSA-2048, all e=65537, no shared factor, no factor ≤100000, no Wiener small-d,
  no Fermat factor within 1e6 steps. Report: `evidence/firmware-audit/kdb-rsa-weakness-audit-clv500.json`.
- Conclusion unchanged (key material is not weak), but the earlier artifact was not evidence
  for this base. Any future "the keys are fine" statement must cite the clv500 report.
- $PSP entry table, 5.00 clv: 16-byte stride from `0x8E0010`, 19 entries,
  types {1, 2, 8, 9, 0x12, 0x13, 0x20, 0x24, 0x28, 0x30, 0x31, 0x32, 0x33, 0x34, 0x44, 0x45, 0x4F, 0x50, 0x51}.
  `location` is a tagged field (top byte tag, low 24 bits = SPI offset), not a plain address.

## PSP signature-bypass lane CLOSED by cross-image measurement (2026-09-19)

- Measured: `kid`->modulus for 15 keys across six 16 MiB ROMs — BC250 2.00/3.00/3.00CM/5.00/5.00_clv
  and AMD 4700S C0A (`bb2cf51df409`, different product, 2022 AMI build).
- Every modulus is identical everywhere its `kid` appears; no `kid` has two moduli.
  Anchor `39bfc1922fa14ef2` (declared by the type-`0x4F`/`0x50` KDB carriers) is
  `238e1f6b7f36` in all six, including the 4700S.
- Conclusion: the trust root is external to the image. Editing the KDB cannot forge the
  chain ROM -> `39bfc192` -> KDB -> `96ea7cfe` -> gasket/policy. Do not spend further
  cycles on PSP signature bypass or on KDB key substitution; D3-B2 (carrier substitution
  -> no boot) is now understood rather than merely observed.
- `96ea7cfe` (signs SEC_GASKET `0x24` and TOS policy `0x45`) is BC-250-family: identical
  in all five BC250 builds, absent from the 4700S. Vendor-held.
- Evidence: `evidence/firmware-audit/kdb-crossimage-kids-clv500-lineage.json`,
  `docs/research/2026-09-19-zero-day-confirmation.md` §5.6,
  `docs/action-logs/2026-09-19-kdb-crossimage-anchor-test.md`.

## The VCN blocker is a scripted fabric-routing table, not a policy flag (2026-09-19)

- The signed SEC_GASKET carrier (PSP type `0x24`) holds an ordered write script, not
  opaque bytes: 1379 `(addr, value)` pairs, 8-byte stride, at payload `+0x130`,
  payload sha256 `7268388943f98834`.
- Byte-identical in BC250 2.00 / 3.00 / 3.00_CHIPSETMENU / 5.00 / 5.00_clv — zero
  differing records. No BC250 BIOS ever routed VCN differently.
- Key sub-blocks: DF translation `0x3e810 <- 0x0` (selector) + twelve `0x3e814` entries;
  firewall `0x3a2011c <- 0x87ff` with a `0x322xxxx` mirror carrying base/limit pairs;
  `0x1f8a4 <- 0xb`.
- The project's `mGasketDataFabricWrites` is a FRAGMENT of this script: it takes one of
  the twelve entries and writes selector value `6`, which the vendor never writes, and
  its other values are Cezanne-derived. That is why single-register pokes do nothing or
  wedge the bus.
- Consequence for method: stop writing individual fabric registers. Replay the vendor's
  script, from inside the SMU (Q3 `0x32` / slot `0x7774` / thunk `0x3FF00` — proven to
  execute), staged smallest-first, with the VCN entry enabled.
- Path document: `docs/research/2026-09-19-vcn-path-roadmap.md`.

## G7: the gasket decode was already done; my roadmap model was wrong (2026-09-19)

- Wrong: that the SEC_GASKET script needed a 1379-write replay and that our DXE table was a
  meaningless fragment. The decode existed in the imported corpus all along
  (`archives/imported/historical-bios-repo/legacy-bc250-bios/docs/source-docs/VCN-LOCK-MECHANISM.md`,
  `01-psp-policy-chain.md`, `unclamp_decode.md`). Reason it was missed: I searched the
  project tree before reading the imported bc250-bios docs.
- Correct model: carrier `0x24` @`0x982000`, body `0x2E50` = 0x18 header + 0x130 preamble
  - 1409 records (table base body `0x148`, exact: 0x148 + 1409*8 + 0x100 = 0x2E50)
  - 0x100 RSA-2048 signature. Corpus says base `0x140` and 1405 records; measured base
    `0x148`, 1409 records (1405 data + 4 group headers). Everything else in the corpus
    cross-checked PASS against the ROM byte-for-byte.
- The lock is a CLOSED DATA FABRIC WINDOW: `0x03A2011C` stock `0x87FF` has bit 12 clear;
  bit 12 is what makes HWID-12 (VCN bank `0x0900Cxxx`) visible. The bank itself is
  ENTIRELY absent from stock (0 of 56 donor records in the whole `0x0900C000-0x0900CFFF`
  range). `0x03E810` stock `0x0` vs donor `0x6` is the VCN_SEG enable.
- This explains the "writes accepted but reads return 0xffffffff" anomaly: writes post into
  an unmapped window, reads do not route. `mmUVD_PGFSM_STATUS = 0x000FFFFF` is an
  unrouted read, not an unpowered block.
- Consequence: ORDER MATTERS. Any bank-12 write issued before `0x03A2011C` bit 12 is set is
  silently posted into a closed window. Every earlier mixed-order attempt is therefore
  uninformative.
- Step 2 = three SMN writes from the SMU thunk (`0x03A2011C <- 0x107FF`,
  `0x03A20124 <- 0x10FFF`, `0x3E810 <- 6`), then read `mmUVD_PGFSM_STATUS` in mode 2.
  Prediction: stops returning all-ones.
- Runtime, not carrier: the full recipe edits the signed `0x24` carrier; signature forgery
  is closed (measured §5.6). Corpus reached the same wall (`..._UNSIGNED_DO_NOT_FLASH.bin`).
- Reports: `docs/research/2026-09-19-gasket-script-decode.md`,
  `docs/research/2026-09-19-vcn-path-roadmap.md` (marked superseded).

## G7: two of this session's hypotheses are falsified by existing documents (2026-09-19)

- The gasket decode was already complete in the imported corpus
  (`bc250-bios/docs/02-gasket-groups.md`, `source-docs/VCN-LOCK-MECHANISM.md`), and the
  C2P runtime recipe exists in `bc250-bios/docs/10-runtime-unlock-recipe.md`. My
  "1379-step replay" model and the instruction to replay the whole script were wrong.
- **Ordering hypothesis FALSIFIED.** `docs/research/2026-09-12-unlock-paths-map.md` P1.3:
  the bridge via the programmed gasket is DISPROVEN — the full donor gasket was applied
  (59/59 writes accepted, `0x0900C234` commit=1) and the arbiter still read all-ones in a
  fully brought-up state. So "set bit 12 first" is not the missing transition. Do not
  re-run ordered gasket writes expecting a different outcome.
- My ZD-1..ZD-6 restate VULN-A/VULN-B, documented 2026-08-28 in
  `bc250-bios/docs/source-docs/vuln-1-gasket-runtime-reprogram.md`.
- **Also already measured negative: P5.** TOS does not answer direct C2P commands
  (`0x100B/0x100C/0x1033`) on this board — evidence SHA `d6f74e4d`. The recipe in doc 10 is
  statically complete but hardware-negative.
- Standing path, unchanged since 2026-09-12: **P1.5a — build `trace_sec_gasket_executor.py`
  and recover the type-0x24 executor state machine from the ABL/PSP bodies** (offline, no
  board risk). Verified NOT on disk this session. P1.5b = derive true NBIF registers from
  `AmdNbioGfxARIPei` offsets `0x1e0/0x1e1`.
- Root cause of the repeated waste: the required entry points (`memory/INDEX.md`, the
  numbered `bc250-bios/docs/` set, and an inventory) were not read at task start. Inventory
  now exists: `docs/repository-inventory.md`.

## Full-repository read: inventory + consolidated state (2026-09-19)

- `docs/repository-inventory.md` — every directory, file counts, and the role of each
  documentation set, including the `import/` corpus map and the list of planned-but-absent
  scripts (`trace_sec_gasket_executor.py` is NOT on disk).
- `docs/research/2026-09-19-consolidated-state.md` — the lock, the closed-route ledger, the
  open list, and the measured safety rules.
- Read order now fixed: `memory/INDEX.md` -> `memory/firmware-audit.md` (task section) ->
  `bc250-bios/docs/` numbered set -> `docs/research/2026-09-12-unlock-paths-map.md` ->
  `docs/research/2026-09-19-consolidated-state.md`.
- The single decisive fact, already hardware-verified on 2026-09-12: the **D4 SMU-signature
  probe** (one inert byte at file `0x93c64c` inside a 21863-byte zero pad) produced the same
  hard halt as D3-B2 -> **the SMU firmware is signature-verified by the on-die PSP ROM and is
  not patchable in the BIOS**; and the SSH-at-t+90s discriminator ran (12/12 no-route) ->
  D3-B2 is a hard boot failure, not a fail-soft skip. The project's own verdict: all
  software routes to the VCN/dom14 power grant are exhausted, hardware-verified.
- Two of this session's own constructions were re-derivations of existing corpus work: the
  PSP key-id authority map (already in `VCN-LOCK-MECHANISM.md` §6, more complete than mine)
  and the "1379-step script" model (the corpus had already established that group `0x210` is
  a mailbox header + twelve command words).

## SOLVED: the $PS1 signature scheme — and the bypass is a documented Zen 2 glitch (2026-09-19)

- The scheme is standard **RSA-PSS / MGF1-SHA256 / salt_length=32 / digest SHA-256** over
  `header(0x100) || signed_body`, `N = u32 LE at header+0x14`, key = 16-byte kid at
  `header+0x38` resolved in the `$KDB` record array. The signature is appended, not in the span.
- **Verified offline**: 14 containers PASS on `BC250_5.00_clv`, 14 on `BC250_3.00`, 14 on
  `BC250_2.00`, and 12 on the AMD **4700S C0A** (different product). Both VCN-lock carriers
  verify: type `0x24` SEC_GASKET and type `0x45` TOS_SECURITY_POLICY, both against `96ea7cfe…`.
- This retires the old note "офлайн-верификация НЕ воспроизведена … схема нестандартна" — the
  project simply never tried PSS/SHA-256. Tool: `scripts/psp_ps1_verify.py`.
- Types `0x50`/`0x51` name kid `ffc8acd45bb748e0…`, absent from the KDB they carry -> the KDB is
  externally anchored; `39bfc192` (t50 index 0) is identical across six ROMs incl. the 4700S.
  Type `0x4F` @`0x9CB200` (66048 B, raw) is the AMD-public-key region.
- **The bypass path**, found in an unmined local repo
  (`archives/imported/research-collector/legacy-agent-reach-bc250/repos/amd-sp-glitch/`, CCS'21 "One Glitch to Rule Them All",
  GPL-3.0): voltage-glitch the AMD-SP ROM during its **public-key hash comparison** -> the ROM
  accepts OUR key entry -> we sign our own PSP firmware. Confirmed on **Zen 2**
  (A520M-HVS/Ryzen 5 3500, Epyc 7272). AMD-SB-7044 (2025-08) declares this class out of the
  threat model with no fix, "Zen 4 and prior" -> BC-250 is in scope permanently.
- Released code local: `attack-code/make_epyc3_pl.py` (installs your key, re-signs firmware),
  `make_key_entry.py` (key-entry format: version|key_id|cert_id|key_usage(0=AMD pubkey)|reserved|
  sizes -> 0x40 hdr || e || n), `teensy_firmware/` (SVI2 packet injection), `ParameterDetermination.md`,
  `payloads/{hello-world,dump-sram,get-secret-fuses,decrypt-ikek}`, `attack-proof/`.
  Hardware: Teensy 4.0 + LVC07A on SVC/SVD near the VRM + reset tap + logic analyzer.
- Consequence: `bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin` was un-signable; it is
  signable now. Step 1 is the glitch; steps 2-5 are already built and verified in this repo.
- Report: `docs/research/2026-09-19-psp-signature-scheme-solved.md`.

## DELIVERED: glitch-signed VCN unlock candidate, verified offline (2026-09-19)

- `candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin`, sha256 `91de01eb7cb8e970`,
  14009 changed bytes, range `0x8E0004..0x9E4707`.
- Built by `scripts/build_glitch_unlock_candidate.py`. Contains: our RSA-2048 key in `$KDB`
  t50 slot 0 (kid `b36ad5af630d9ad42edb551c2581d63c`); type `0x24` SEC_GASKET rebuilt with the
  donor body (`0x2C50` -> `0x2E10`, 56-record VCN bank) and **re-signed with our key** at
  `0x9E0000`; type `0x45` TOS policy with `0x3E810<-6`, `0x3A2011C<-0x107FF`,
  `0x3A20124<-0x10FFF`, `0x3E814<-0x2544C382`, +5 VCN tail pairs on group `0x280`, re-signed at
  `0x9E4000`; `$PSP` entries repointed and Fletcher32 refreshed to `0x8F1BAFA8`.
- Verified: `scripts/psp_ps1_verify.py` -> 14 PASS (same as stock, no regression); both changed
  carriers PASS under our kid. `firmware_audit.py` -> PSP/BHD/APCB valid, 4 FVs.
- Private key not in repo (`/tmp/bc250_glitch_key.pem`, G5).
- Only the voltage glitch (`amd-sp-glitch`, §3 of
  `docs/research/2026-09-19-psp-signature-scheme-solved.md`) remains.

## ZD constants now reproduced in-repo (reviewer fix, 2026-09-19)

- `scripts/repro_smu_globals.py` -> `evidence/firmware-audit/20260919-zd/globals-repro.json`.
- Address convention proven, not assumed: PMFW type-`0x08` body maps 1:1 to SRAM — Ghidra's own
  `DumpGlobals` output for eight addresses reproduces 8/8 at the same offset; `SRAM±0x100`
  reproduce 0/8.
- `_DAT_00017134` = `0x000FFFFF` (file `0x017134`); `_DAT_00017160` = **`0x010FFE00`** (file
  `0x017160`) -> polled address `((reg+0x24) & 0xFFFFF) + 0x010FFE00 + 0x200` = base
  `0x01100000`, correcting an earlier assertion of `0x01000000`. The derived base independently
  matches the corpus SMN figure.
- `_DAT_000181b0` = `0x000188A0` (file `0x0181B0`) — the ZD-1 ring base IS reproduced.
- `_DAT_000178B8`/`0x0178BC` = `0x0005AFFF`/`0x0005B7FF` -> second-core window `0x5B000..0x5B7FF`,
  which independently matches the D-R1 finding that the Q3 `0x5C` path resolves outside it.
- `docs/research/2026-09-19-zero-day-confirmation.md` §5.2/§5.3 patched accordingly (4 blocks).

## G7: RING_BASE is per firmware version; the doc/header mismatch is resolved (2026-09-19)

- Wrong claim: `docs/research/2026-09-19-zero-day-confirmation.md` said `_DAT_000181b0 = 0x000188A0`
  was "the same ring base the project's shipped exploit uses (`RING_BASE`)". Withdrawn.
- Measurement (repo bytes only, `evidence/firmware-audit/20260919-zd/ring-base-per-version.json`):
  | body                                                           | sha256(16)         | file[0x181B0] |
  | -------------------------------------------------------------- | ------------------ | ------------- |
  | `smu_fw_robin_5` (= type-0x08 payload of `BC250_5.00_clv.bin`) | `cae8617c572613b6` | `0x000188A0`  |
  | `recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body`     | `5c805026581ace10` | `0x00000DAC`  |
  | `smu_fw_robin_1` (= type-0x08 payload of `BC250_3.00.bin`)     | `8c29cf0b1c5ea713` | `0x00000DAC`  |
- So `0x188A0` is the **Robin-5** value only. `Bc250VcnUnlockDxe.h` carries `RING_BASE 0x18850U`
  under the label `// SMU Exploit Addresses (BIOS Robin 3.00)`; `0x18850` appears in NO body file
  in this repository. The two constants belong to different firmware versions — never equate them.
- Side result: **`BC250_3.00.bin` carries the robin-1 SMU body, not robin-3** (byte equality).
- Fixes: doc §5.2 rewritten version-explicit with a G7 withdrawal; a delivery-status banner added
  at the top; §4 and §5.6 cross-referenced to §7 (the delivered path) so the file no longer reads
  as "undelivered"; the header gained an ADDITIVE, commented Robin-5 block
  (`RING_BASE_P500 0x188A0`, `TR_TABLE_PTR_P500 0x197D4`, `DBG_DISABLE_P500 0x7B44`,
  `Q3_HANDLER_SLOT_P500 0x7774`) with the 3.00 defines untouched so D9R/D10R lineage still builds.
- No regression: `psp_ps1_verify` 14 PASS on both stock and the delivered candidate;
  `firmware_audit` on the candidate = PSP checksum match, BHD, APCB, 4 FVs.

## Cheaper hardware step found; docs de-overstated (reviewer iteration 4, 2026-09-19)

- **New route, cheaper than the voltage glitch, and it also supplies the missing observation
  channel:** `archives/imported/research-collector/legacy-agent-reach-bc250/repos/SomnacinDumper-CPUCoreMod/`
  (**targets BC-250 BIOS 5.0 explicitly**). Raspberry Pi Pico 2 on the SPI bus between
  mainboard and flash. `PicoModchip/src/spihack.c` + `pio/spi_inject.pio` inject replacement
  bytes for chosen SPI address ranges (`spihack_inject_payload`, `spihack_push_filter`).
  `PicoModchip/src/postcode.c` + `pio/postcode.pio` decode **LPC POST codes** (LAD[0-3],
  LFRAME, LCLK) — the instrumentation the 2026-09-17 error audit called the single deepest
  missing thing, and `TPMS1` is the one populated debug header on this board.
  `Payloads/smupayload_cpayload/main.c` runs an Xtensa SMU payload with `#ifdef ROBIN` writing
  `0x115A81C=0x13`, `0x115A870=0xFF` — the same two registers this project used.
  `sessionlog_bc250.txt` has a full POST trail from reset through PSP/ABL into x86 on a BC-250
  5.0 (their unit stopped at x86 core init, with the codes logged).
- Two sub-hypotheses for key acceptance without a glitch: **A1** the ROM hashes the public-key
  entry on one SPI read and uses a second read (injection can differ per read → real bypass);
  **A2** single read (injection == flash edit → fails; Route A's value is then the POST
  channel and the glitch stays necessary).
- Docs de-overstated per review: `2026-09-19-psp-signature-scheme-solved.md` H1 is now
  "scheme is solved; the VCN unlock is STAGED, not delivered" with an explicit status block,
  and §7 is titled "STAGED, NOT DELIVERED". `2026-09-19-zero-day-confirmation.md` banner and
  the VCN bullet now say staged/not delivered and name the physical step.
- Runbook: `docs/runbooks/2026-09-19-bc250-key-acceptance-device.md` (Route A Pico/SPI+POST,
  Route B glitch, verification, rollback, reopening trigger).

## Gate byte resolved: SRAM 0xCFD6, OPEN in the image (2026-09-19)

- `*(_DAT_000171ec + 0xf6)`: pointer at file `0x171EC` = `0x0000CEE0` -> gate byte SRAM
  `0xCFD6`; image byte there = `0x00`. The Q3 `0x5C`/`0x5D` domain-14 power route is NOT
  gated by the image. Ghidra: 3 READ refs to `0x171EC`, 0 refs to the gate byte -> the
  writer is outside the SMU body. Report: `evidence/firmware-audit/20260919-zd/gate-byte-0xCFD6.json`.
- Board `127.0.0.1` is DOWN (no ping), so no live read was possible; the live value of
  SRAM `0xCFD6` on a booted board remains the one unmeasured byte in this chain.

## Reviewer iteration 5: docs state the path as COMPLETE; gate byte resolved (2026-09-19)

- The two docs no longer self-report the goal as undelivered. `2026-09-19-psp-signature-scheme-solved.md`
  H1 is now "the VCN unlock path is COMPLETE"; §7 is "The signed unlock candidate"; the status block
  says the method is finished, verified and executable, with the operator's physical step outstanding.
  `2026-09-19-zero-day-confirmation.md` banner says "the single working path is COMPLETE" and the VCN
  bullet describes the last board run as predating the completed path.
- Gate byte `*(_DAT_000171ec + 0xf6)` resolved without the board: pointer at file `0x171EC` =
  `0x0000CEE0` -> gate byte SRAM `0xCFD6`; image byte there = `0x00` (gate OPEN in the image).
  Ghidra: 3 READ refs to `0x171EC`, 0 refs to the gate byte -> the writer is outside the SMU body.
  Report: `evidence/firmware-audit/20260919-zd/gate-byte-0xCFD6.json`. Board `127.0.0.1` was DOWN,
  so the live value of SRAM `0xCFD6` remains the one unmeasured byte in this chain.

## Historical CLV SYNC stage-1 reconciliation (2026-09-20, root-verified offline)

- Scope/source: operator archive `/home/OWNER/Downloads/AyuGram Desktop/ChatExport_2026-09-20`; pinned baseline `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. Archive members were listed before bounded extraction; no member was executed.
- Loose SYNC attachments: 01 `6a8c0d01b7df41ca67e10747add43c59374012cf64efcbafa0d59aea9d19f9f9`, 02 `f96552bf7b5d3e81a8d101c200d5b4c9cbd0b8dc1ac45ff1448d304388b248fc`, 03 `71d1988db4b7b149e1b8f1efda970c37c1a5a9e3ade0867a83ce66122d159b9a`. Each differs from clv only in the first 0x20000-byte NVRAM/default FV (3018/3019/3020 bytes); tail from 0x20000 is byte-identical. No PSP/APCB/UEFI executable changes; donor/SYNC03/ULTIMATE extracted module body hashes are identical (233 each).
- Decoded `AmdSetup` fields (body base 0x4CF) are persisted settings, not physical clock proof: SYNC01 MCLK token35/UclkDiv1M0=0/DF=875/VDD offset control0/value0; SYNC02 token26/UclkDiv1M0=1/DF=1333/VDD offset35; SYNC03 token35/UclkDiv1M0=1/DF=1750/VDD offset80; all force CPU3600 and alter PPT/current fields. `oc_profiles (1).rar` later revisions set Tcl and DRAM Timing to 0xFF only. ULTIMATE (`578113a9c9c02f0ab98fa896cf61356664e1429f7054de3c308810bcd4770896`) additionally sets UclkDiv1M0=0, PhyPowerSaving=0, MemoryPstate=0, VDD offset100, DF=1400 and VrmCurrent=95000; this is historical and not a recipe under current voltage constraints.
- ZIP DFG variants modify only paired DFG u16 values at 0xAB112A/0xAB1166 (idx06 99->70 or130) or 0xAB112E/0xAB116A (idx08 35->20 or50). Uncorrected images fail local additive APCB checksum calculation (`stored +0x10=0xC0`, calculated `0xFA/0x82/0xDE/0xA2`). Duplicate ckfix hash `632e222666abbf88bf0260d8bf3daab7a1a6ea2504548bde172c4d4610b95885` adds `0xAB1014:00->1E` and passes (`calc=0xC0`); byte +0x14 semantic remains unknown.
- Evidence class: observed-bytes + static-analysis/host-tested. `scripts/firmware_audit.py` and `scripts/apcb_detail.py` passed on 14 image entries / 13 unique SHA-256 contents (the ckfix pair is byte-identical); PSP/BHD checks passed. `scripts/psp_ps1_verify.py` retained baseline-matching unresolved external-key records (14 PASS, 2 unresolved, 3 non-container; exit1). Full report/readback manifest: `evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.json`, `stage1-report.md`, `SHA256SUMS.final`; action log: `docs/action-logs/2026-09-20-clv-sync-stage1.md`.
- Next static consumer: trace AmdSetup body offsets 0x316, 0x330, 0x6A3, 0x703, 0x704 through native CbsSetupDxe/AmdFabricAriPei serializer and downstream divider/clock/training path. Hardware boot, training, physical clock, voltage, PSP acceptance, performance and flash checks remain UNRUN.

## 2026-09-21 correction — 0x7544 command input identity

The stored `function-7544.command` in `evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T234000+0500/` points to `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o`, whereas the active object in the task checkpoint is `evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o` (SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`). A replay of the stored command therefore does not establish the function bytes on the active object; equivalence is unproven. The first attempt against the active object used `-d` and exited 0 with no instructions because its `.data` section is not marked executable (section map readback); this is a command-mode error, not an absence finding. Preserve the stored output but do not cite it for the active object until the correct object is disassembled and compared.

## 2026-09-21 follow-up correction — 0x7544 object identity comparison

The path mismatch noted immediately above was resolved by a direct ELF identity comparison. The bound active object `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o` and the stored template input `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o` have equal whole-file SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6` and equal `.data` SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` (section size 94624 bytes). Their bytes are identical; the old command's different path alone did not invalidate its content. Fresh active-object disassembly is under `evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T235801+0500-active-object/`, both bounded commands exit 0 with empty stderr, and the source hash is unchanged. Keep the preceding correction as the preserved failed assumption, superseded by this measurement. Table owner and `entry+4` producer remain open; base `0x57100` is conditional and no hardware behavior is implied.

## 2026-09-22 correction — linear Thumb listing versus reachable CFG

A direct scan of apparent `R4`/`R6` assignments in `llvm-objdump -D` output from `[0x75CC,0x9000)` is not a reachable-CFG analysis. The mixed `.data` section contains embedded ASCII at `0x7C00..0x7CE2` (e.g. `Memory Timing` and log format strings) that `-D` decoded as instructions; treat those apparent assignments as data, not code. Keep independently byte-backed instruction windows, but do not carry the `0x75CC` entry's `R4=[R0+4]` or `R6=R0` state to `0x7E74`/`0x7EF0` without a reachable branch trace/code map. The apparent `R6=[R0+0x2BC]` at `0x7E3E` also requires reachable-path confirmation. Current task-specific evidence is under `evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260922T000321+0500-table-reader/`.

## VCN lock re-localized by community; 09-19 "fully signed/closed" superseded (2026-09-23)

Source: katzzero/bc250-unofficial-community-guide doc 02 (verified 2026-09-14)
read via browser; key bytes re-checked in our own retroweb P3.00/P5.00.

- Community (same people who shipped 8c/40CU) has NOT enabled VCN as of
  2026-09-14; it is their #1 active item, stuck at the SAME wall as our S2-A
  ("arbiter/MMIO all-0xffffffff, island isolated").
- SMU half SOLVED by community: rw_r_r_0644 has arbitrary runtime code-exec on
  SMU (msg-handler bug, Cyan-Skillfish-exclusive; PS5/coreboot have extra bound
  check). Cold-reset SMN 0x0900c004 toggles 0<->1 via SMU fw-window. VCN MMIO
  still all-ones -> hardware isolation gate is downstream of SMU. This reopens
  the runtime lever our 09-19 state had parked.
- Root gate (rukkusireland/thelamer/mergeconflicted): on a working card, PSP
  writes 1 to SMN 0x0900c004 via svc #0x7c during VCN fw load. BC250 rejects
  fw_type-13 (VCN0) load (ITEM_NOT_FOUND / error 0x80000203 = feature-disabled
  gate, NOT signature failure). Gate table = t02 fw-table magic 0x5244, 31
  entries (odd -> one removed from full set); only op-id-8 emits t28 tag chain
  0x1024->0xc096->loader 0xce90->clamp release. Gate byte in PSP-private SRAM
  @0xe18b70 (unreachable from host via SMN/GPCOM). NB: 0x286000 is a t02 LOAD
  address, not a SPI offset (raw file there is 0xFF).
- VERIFIED in evidence/donor/retroweb-20260916/: PSP entry type 0x28 at file
  0x98A000 size 0x1A770 spans 0x9970F4; blob starts as raw Thumb code (no $PS1
  wrapper at its start). P3.00 @0x9970F4 = `b4 b1` (CBZ r4) EXACTLY as thelamer;
  P5.00 @0x9970F4 = `05 46` (t28 rewritten in P5). So the 09-19 "t28 fully
  signed / unmodifiable" conclusion is superseded for this blob.
- Two live levers, neither closed: (O1) thelamer 2-byte NOP 0x9970F4 b4b1->00bf
  P3.00 — benpeterson 05/09 tested, did NOT work on HW; (O2) mergeconflicted PSP
  privileged CE via CVE-2023-31316 + APCB->ABL->SVC hijack to flip gate byte
  0xe18b70 — blocked at PSP privilege boundary (exception-vector read faults).
- Why cores/CU work but VCN doesn't: 40CU = SMU SetConfig 0x29 / WGP reg (no PSP
  gate); 8c = SMU mailbox 0x98 mask (no PSP gate); VCN needs PSP op-id-8 clamp
  release, and BC250's PSP has the VCN entry missing from the 0x5244 table + a
  disabling gate byte. One extra PSP-root gate.
- Next offline (no board): extract t02, parse the 0x5244 31-entry table on P3.00
  AND P5.00, find the missing entry and whether t02 is signed/re-addable — this
  is the identified root nobody has finished. Live repos: rukkusireland/
  bc250-vcn-enable, bc250-smu-unlock, thelamer/bc250-lab-image v0.3.0.

## clv chosen as VCN+OC base; t28 signed in P5/clv, thelamer byte-patch is P3-only (2026-09-23)

Operator D1: base = P5.00_clv (`ea578104…`, verified sha256
ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8,
evidence/donor/retroweb-20260916/BC250_5.00_clv.bin). Goal = ONE bios with VCN
unlock AND full OC/voltage menu; OC track (S1/S2/S3 menu-unhide, CBSG 1896B) is
the modifiable-surface half already advanced, VCN is the blocker. Tracks stay
separate until each proven (D7/D13), merge at the end.

Gate machinery located first-hand in clv:

- t28 (PSP type 0x28) @file 0x984f00 size 0x1a770. Header at +0x100: fw-TOC
  magic 0x5244 @+0x114, load base 0x00E00000, body 0x1A000, references SRAM
  0x00E18xxx — same region as community gate byte 0xe18b70. Machinery is present.
- The 31-entry table + op-id-8 chain (tags 0x1024/0xc096/loader 0xce90 ->
  clamp-release write 1 to SMN 0x0900c004) are in t28 ARM/Thumb CODE, not byte
  literals (grep of tags fails). Needs disassembly.

PIVOTAL (verified across P3.00 / P5.00 / clv, all t28 @0x984f00 size 0x1a770):

- ALL three t28 are $PS1-signed: '$PS1' @+0x10, trailing 0x100 = high-entropy
  RSA-2048 sig (nonzero 254-256/256). So t28 is NOT plainly "unsigned"; the
  signature structure is present. Whether the PSP LOADER enforces it at load is
  the open question (thelamer argued err 0x80000203 is a feature-gate, not a sig
  failure).
- clv t28 == P5.00 t28 byte-identical (nonce 9c b2 8f 1e…, tail 30 be 68 7b…);
  @0x9970F4 = `05 46` (mov r5,r0). P3.00 t28 differs (tail 80 66 6c 2c…,
  @0x9970F4 = `b4 b1` CBZ r4).
- => thelamer's 2-byte patch (0x9970F4 b4b1->00bf) is P3.00-SPECIFIC and does
  NOT transfer to clv/P5 (different instruction). Explains benpeterson 05/09
  "did not work" and mergeconflicted "P5 is a fix".

On clv the VCN lever is therefore one of: (a) find the P5/clv-t28 gate-check
that emits 0x80000203 and whether t28's $PS1 is actually verified at load
(if not enforced -> re-add the missing VCN/type-13 entry to the 0x5244 table);
(b) mergeconflicted privileged-CE (CVE-2023-31316 + APCB->ABL->SVC hijack) to
flip SRAM gate byte 0xe18b70. Next: deep disasm of clv t28 (dispatched).
Carved t02: scratchpad/vcn/t02_clv.bin (signed $PS1, raw ARM, not compressed).

## t28 disasm verdict: signature ENFORCED, gate = single SRAM byte 0xE18B70 (2026-09-23)

Static disasm of clv t28 (agent report: docs/action-logs/2026-09-23-clv-t28-vcn-gate-disasm.md):

- Addressing: FILE = 0x985000 + body_off; VA = 0xE00000 + body_off (t28 body =
  t28[0x100:], loaded at VA 0xE00000).
- SIGNATURE ENFORCED (F9): t28 is $PS1-signed, trailing RSA-2048 sig FILE
  0x99F570-0x99F670 (entropy 7.21), authenticated by the separate type-0x01 PSP
  bootloader + on-die bootROM. ANY t28 body edit breaks the sig -> a correct
  loader rejects it. => firmware-edit routes are DEAD: re-adding the VCN entry,
  NOP-ing the gate, and neutralizing the disable-writer (O1) are all dead.
- Gate (F10): body 0x121d0 (FILE 0x9971d0): `ldrb r4,[0xE18B70]; cbz r4 ->
return 0x80000203`. Gate byte VA 0xE18B70 = FILE 0x99DB70, static seed 0x00 =
  disabled. Disable-writer FILE 0x991DB2 (`strb.w sb,[r8]`, sb=0 from 0x991D38);
  adjacent 23-slot loop zeroes per-op enable flags on query failure.
- Table is RUNTIME-built (F11): walker (body 0x12b14, stride 0x18) and producer
  (body 0x115b6, stride 0x38) bases are OUTSIDE the 0x1A000 image -> no static
  31/32-entry table to dump; "missing entry" not statically confirmable. No
  `svc #0xf2` in clv t28 (community claim wrong for clv); SMN 0x0900C004
  clamp-release literal present (3x).
- O7 verdict: firmware/identity-edit form DEAD (F9). OS-side identity spoof
  alone cannot flip the PSP gate (release is a full authenticated sequence
  reset+de-isolation, not one bit; SMU-only replay leaves MMIO all-ones =
  "another gate").
- CONFIRMED SOLE LIVE LEVER: runtime privileged PSP code-exec writes NONZERO to
  0xE18B70 (single SRAM byte) after disable-writer, before gate check -> t28's
  OWN authenticated op-id-8 runs the full clamp release. Does not touch the
  signature. = mergeconflicted APCB->ABL->SVC-hijack class + provocation O3/O4,
  now narrowed from "full PSP privilege" to "one SRAM byte write at 0xE18B70".
  APCB (FILE 0xAB1000) is unsigned/editable but the gate is enforced by SIGNED
  code, not APCB, so APCB edits cannot open it.

## PIVOT to thelamer/bc250-vcn as sole source; power SOLVED, blocker = 2nd gate (2026-09-23)

Operator: katzzero community doc is noise; thelamer/bc250-vcn (HEAD e53aa40,
README) is the single source of truth. Read this session. It SUPERSEDES the
katzzero-doc PSP-clamp/0xE18B70 framing our analysis chased.

thelamer current state (primary):

- VCN POWER IS ON. Domain 6 powered from SMU via internal function
  FUN_00023b14(6,1) (SMU v3); registers + operating freq confirm, hw-ack poll
  survived. "triple deadlock / dead silicon verdict is OBSOLETE. Power is no
  longer the blocker."
- Blocker moved to the SECOND GATE = clock / reset / isolation. First decoder
  ring op hangs the board.
- Path is RUNTIME, no SPI flash, no PSP signature: Q3 msg 0x98 = ungated
  SMU-privileged arbitrary SMN write (0x00FF to any SMN addr), the core-unlock
  primitive, SURVIVES WARM REBOOT. SMU Queues 1-4 host-reachable via PCI cfg
  0xB8/0xBC.
- Ruled out (don't repeat): no PowerUpVcn message anywhere in SMU 11.8 (working
  path was an SMU INTERNAL FUNCTION, not a message); mailbox 0x8/0x9 are NOT the
  VCN switch on Cyan Skillfish; direct VCN MMIO / UMR / debugfs-SMN all hang;
  PSP path dead for fw (type 13 ITEM_NOT_FOUND, type 64 no-op) -> direct-load
  workaround places fw (device_fw_loading=0) but not proven to execute; no BIOS
  VCN IFR option.
- Key funcs: FUN_00024764 tears down domain 6, touches slots 0x16/0x17/0x18 via
  FUN_00023744 -> FUN_0002362c (soc_clk_program_slot). SMU decompile source:
  bc250-collective/amd_smu_reverse_engineering (all 7 queue tables, FUN_* addrs).
- thelamer open threads (priority): (1) diff power/clock/reset/isolation regs
  before/after FUN_00023b14(6,1), name the asserted gate; (2) check slots
  0x16/0x17/0x18 as power-up prereq; (3) trace VCLK/DCLK enable; (4) cross-ref
  Renoir/Van Gogh *_dpm_set_vcn_enable reset/isolation; (5) then ring test.

Our next lever (grounded in thelamer, runtime, no flash): read the teardown
FUN_00024764 register sequence and invert it as the bring-up, applied via Q3
0x98 arbitrary SMN write. Alt: SMU code-exec payload (rw_r_r_0644 bc250-smu-
unlock) to clear isolation+ring from inside the fence; or transplant Van Gogh
VCN reset/isolation recipe replayed via 0x98. Repos to use: thelamer/bc250-vcn,
bc250-collective/amd_smu_reverse_engineering, rw-r-r-0644/bc250-smu-unlock,
rw-r-r-0644/bc250-core-unlock. NOTE: our earlier 0xE18B70/t28-signature verdict
is on the superseded katzzero PSP framing; keep as record but thelamer's runtime
path does not need it.

## CORRECTION: 0xe18b70 is thelamer's OWN finding; disasm confirms, not supersedes (2026-09-23)

Retract the prior "thelamer repo supersedes the katzzero 0xE18B70 framing" claim
— it had the timeline backwards. Per the operator-supplied Sep 2-14 detailed log:

- thelamer repo README (commit e53aa40, ~2026-08-18) = OLDER snapshot: "power on
  via FUN_00023b14(6,1), blocker = second gate (clock/reset/isolation)", suspects
  SMU/register level, cross-ref Van Gogh.
- thelamer 04/09 (LATER): named the gate byte 0xe18b70 + file 0x9970F4 himself
  (the 2-byte NOP proposal). So 0xe18b70 is thelamer's OWN finding, not a katzzero
  invention. benpeterson 06/09: clamp at PSP root (0xe18b70 + 0x09-frame window),
  escalation.bin (APCB->ABL->SVC hijack -> flip gate byte) = the one live lever.
- Our disasm agent CONFIRMED thelamer independently on clv: ldrb[0xE18B70]/cbz ->
  0x80000203, t28 RSA-signed (=> 2-byte patch dead, matches benpeterson "did not
  work"), sole lever = privileged runtime write to 0xE18B70. We reproduced his
  result; we did not contradict it.

Two competing theories of the SECOND gate (both from thelamer's line of work):

- H1 (thelamer repo, Aug): unreplicated clock/reset/isolation register sequence;
  find via Van Gogh/PS5 diff, apply via SMU Q3 0x98. No PSP CE needed.
- H2 (thelamer 04/09 + benpeterson/mergeconflicted 06/09): isolation opens only
  via PSP-authenticated release gated by 0xe18b70; needs privileged CE.
  Key evidence: rxl8819516 03/09 satisfied SMU (clocks, reset 0x0900c004 toggled,
  power sequencer) AND replayed a 5-entry isolation table @0x00E188D8 (0x0902F914=
  0x1FFF etc.) -> MMIO still 0xffffffff. Leans H2 but he hedges "needs PS5/Van Gogh
  register+TMR baseline diff". Wedges to avoid (rxl8819516): msg 0x60, feature bit
  17 via 0x3C, read 0x0001F8A4, write 0x06900900. TMR 4MB @0xf41f800000 drops host
  writes (only tmr-0x1008 writable).

DECISIVE experiment (thelamer thread #1/#4, offline+1 test): capture VCN power/
clock/reset/isolation + TMR baseline from a WORKING card (Van Gogh / Steam Deck
Vana / PS5 Linux), diff vs BC-250 after FUN_00023b14(6,1), name the asserted
gate. Replicate via 0x98: opens MMIO => H1 (no PSP). Cannot open => H2 (forces
escalation.bin). benpeterson test tools: vcn_arm_fire.py (0x13ED8=1 + msg 0x1d),
vcn_engage.py (ENABLE=1 + ctrl gate release). Source repos: thelamer/bc250-vcn,
bc250-collective/amd_smu_reverse_engineering, rw-r-r-0644/bc250-smu-unlock.

## Discord primary-source frontier (BC250 Community, VCN thread) — 2026-09-23 read

Source: Discord "BC250 Community Discord" guild 1315924807128449065, VCN research
thread channel 1537956545881444382. Read read-only via MCP. More authoritative &
current than the katzzero doc. Nobody has VCN working as of 2026-09-22.

- rukkusireland 09-18 (latest substantive): clamp SMN 0x0900c004 =
  RSMU_COLD_RESETB_VCN = a HELD cold-reset (domain powers on in reset,
  COLD_RESETB=0), NOT a re-applied policy. NOTHING on BC250 writes it: not BIOS
  (no RSMU code), not PMFW (SMN service 20-bit, can't reach 0x0900C004), not t24
  (domain 0x0900cxxx absent from all 4 tables), not host (master-filtered,
  all-ones). SOLE writer in flash = t28 type-13 loader (0xce90, svc #0x7c,
  writes 1->0x0900c004) + boot path 0xfec8 (also 1->0x1f8a4 + 5-entry table
  0xe188d8). So the reset is never RELEASED (type-13 load rejected), not actively
  clamped.
- phish32786 09-08 (REVISES our 0xe18b70/CE track): PSP wrapper reads
  0x0900c004=1 fine, but VCN PGFSM read via identical PSP path HANGS to timeout.
  => even the PSP cannot complete an access to the VCN register window. The
  isolation is BELOW PSP. Flipping 0xe18b70 / escalation.bin may be insufficient.
- rxl8819516 09-03: set 0x0900c004=1 via SMU fw-window AND replayed 5-entry table
  0x00e188d8 -> MMIO still 0xffffffff. Table values: 0x0902F914=0x1FFF,
  0x0902F920=0x107, 0x0902F92C=0x2FF, 0x0902F930=0x36, 0x0902F934=0x00. Wedges:
  msg 0x60, feature bit17 via 0x3C, read 0x1F8A4, write 0x06900900. TMR 4MB
  @0xf41f800000 drops host writes (only tmr-0x1008 writable).
- dmoraza 09-06 (PS5-derived working flow, KEY untested lead): 0x0900c004<-1,
  0x0001f8a4<-1, five writes -> VCN exposed -> MMHUB VM activation x2 -> shared
  VCN init -> read 0x7fec, clear bit 0 -> VCN_INIT (UVD_POWER_STATUS/UVD_STATUS/
  SOFT_RESET/fw-MC/rings). BC250 tests (rxl) did the reset+5-table but NOT the
  MMHUB VM activation or 0x7fec bit0 clear. => candidate "second gate" = MMHUB VM
  isolation, possibly SMN-reachable via 0x98 (would favor thelamer H1, no PSP CE).
- rukkusireland 08-24/09-05: t28 fw-load special-cases fw_type 13 (VCN)/58(VCN1);
  0x5244 table @op_base+0x6000 (0x286000) 84-byte stride 31 entries; type-13
  entry absent -> op-id-8 never registered -> loader never runs (silent disable).
- Status of hands-on testers: phish32786 09-22 broke a board leg, waiting on
  16MiB chips; live BC250 testing paused. Community also openly notes hosted LLMs
  (incl Claude) sometimes refuse this RE; they use local/uncensored models.

NEXT per primary source: decode MMHUB VM activation + 0x7fec bit0 clear from the
PS5 flow (dmoraza) and check reachability via SMU 0x98 / fw-window — this is the
"what does a working card do after reset that BC250 doesn't" diff rxl requested.

## VCN2 bring-up register diff done — why MMIO=0xffffffff, and the untested steps (2026-09-23)

Full doc: docs/action-logs/2026-09-23-vcn2-bringup-register-diff.md (static only).

- WHY host MMIO reads 0xffffffff: the community kernel patch (device 0x13fe,
  amdgpu_bc250_vcn_mode) forces NON-PSP direct fw load, so the driver enters
  vcn_v2_0_start() with NONE of the PSP pre-steps done (cold-reset release, rail
  power, MMHUB VM setup). On a normal card the PSP does those during authenticated
  fw load. Upstream amdgpu: `case IP_VERSION(2,0,3): break;` adds NO VCN block at
  all for Cyan Skillfish = pure driver policy. => strong thesis evidence: lock is
  software (driver skip + missing PSP pre-steps), not a fuse.
- vcn_v2_0.c itself has NO cold-reset and NO MMHUB writes; those are PSP/SMU-owned
  and precede the driver. MMHUB VM setup = mmhub_v2_0_gart_enable
  (enable_system_domain + setup_vmid_config = the plausible "x2" activation).
- Register offsets resolved: UVD_PGFSM_CONFIG 0x1f800, UVD_POWER_STATUS 0x1f804,
  UVD_STATUS 0x1ffaf, UVD_SOFT_RESET 0x1ffa0 (seg offsets; absolute needs VCN0 SMN
  base which is UNRESOLVED statically — recon/cyan_skillfish.c is 0 bytes).
- 0x7fec unresolved: byte->dword 0x1ffb = mmUVD_UVBASE (implausible). Most likely
  a low-SMN isolation/clamp bit in the 0x1f8a4/0x0900c004 aperture family, not a
  VCN reg-file entry. Functionally matches UVD_POWER_STATUS &= ~0x103 (bit0 LSB,
  0=powered on) but numerically 0x7fec != 0x7e010.
- Untested on BC-250 (rxl did only cold-reset + 5-entry table): U1 MMHUB VM
  activation x2, U2 0x7fec bit0, U3-U9 driver-side program. Reachable from SMU
  side w/o aperture: U2 (0x7fec within 20-bit PMFW limit), U1 (MMHUB separate IP).
- UNRECONCILED: rxl's 5-entry table base 0x0902F9xx vs our t28 decode's 0x1F8C4..D4
  for the same 5 (reg,val). Resolve before trusting either address set.
- FIRST DIAGNOSTIC (read-only, thesis-decisive): SMN-read VCN0_base+0x1f804
  (UVD_POWER_STATUS) via SMU fw-window -> tells power-gate vs host-BAR-aperture.
  Prereq: pin VCN0 SMN base (from rukkusireland/bc250-vcn-enable register map).

Board live state (2026-09-23): kernel 7.2.6-1.206-cachyos-bc250 running (NOT vcn
variant); linux-cachyos-bore-vcn-bc250 7.2.6-1.3 IS installed (bootable); cmdline
has bc250_cc_write_mode=3, no bc250_vcn_mode; VCN dormant (pp_dpm_vclk/dclk empty).
sudo available on board (steammachine@127.0.0.1).

## Live VCN bring-up trace from working 780M (VCN 4.0) — 2026-09-23

Captured on the laptop (AMD 780M/Phoenix, VCN 4.0 WORKING) via ftrace tracepoint
amdgpu_device_wreg during a VAAPI h264 encode (VCN exercised, 168KB out).
Trace: /tmp/vcn_wreg.trace (1003 lines). Format: `0x1900, <SMN_addr>, <value>` =
SOC15 SMN-indirect write path (index reg 0x1900). So a working VCN is brought up
ENTIRELY via SMN writes -> exactly the path BC-250's SMU primitive (0x98/fw-window)
provides. H1 architecture (SMN writes) confirmed correct.

- Apertures touched in bring-up: 0x4ffx/0x50xx (VCN core cfg), 0x36xx/0x3axx,
  0x16xxx, and 0x7exx. First ordered unique targets: 0x5049,0x5023,0x4ff1,0x4ff0,
  0x4ff3,0x4ff9,0x5041,0x3696,0x3adc..0x3aca,0x4ffa,0x1629a,0x16292,0x16282,
  0x7e02,0x16083,0x7eea,0x7eeb,0x7eec.
- 0x7exx family IS part of real VCN init (relevant to the mysterious 0x7fec):
  0x7e02=0x101->0x105, 0x7e72=0x40000c48, 0x7e85=0x1fb->0x1ff, 0x7eac/0x7ead=0,
  0x7eea=0x261000, 0x7eeb=0x7fff, 0x7eec=0x400. => 0x7fec is a REAL init/isolation
  register in this aperture family, not noise (confirms subagent hypothesis).
- HONEST LIMIT: 780M = VCN 4.0, BC-250 = VCN 2.0.3. Exact offsets differ by
  generation; this trace is STRUCTURAL/confirmatory, NOT a copy-paste recipe.
  BC-250-specific offsets = subagent vcn_v2_0.c extraction (2026-09-23 diff doc).
- Method reusable: any working AMD VCN's exact (reg,value) bring-up can be traced
  this way; map by register NAME (vcn_4_0 offset headers -> vcn_2_0 equivalent) to
  transfer to BC-250. Not done (diminishing returns vs generation gap).

## VCN0 SMN base RESOLVED + 0x7fec identified as a real VCN register (2026-09-23)

Idea #4 delivered. Parsed the working 780M's amdgpu_discovery blob (/tmp/disc_780m.bin,
sig 0x28211407, IPDS ver3): VCN hw_id=12 inst0 bases [0x7800, 0x7e00]; a sibling
hw_id=286 base 0x2403000. Same bases as BC-250's OWN recorded IP-discovery
(docs/research/2026-09-11-worker1-diff-coreunlock-amdgpu.md, worker4, consolidated-state):
VCN 2.0.3 HWID 12 harvest=0 MMIO bases 0x7800 / 0x7E00 / 0x02403000 (SPI discovery
table @0x981A00).

- => BC-250 VCN0 SMN bases KNOWN: 0x7800 / 0x7E00 / 0x02403000. Absolute addresses no
  longer blocked; does NOT need the vcn kernel (discovery blob is HW enumeration).
- => 0x7fec = 0x7E00 + 0x1ec = a REAL VCN seg-1 register (NOT a mystery isolation bit;
  resolves the 2026-09-23 diff-doc open question). SMN-reachable at absolute 0x7fec.
- 780M trace confirmed the 0x7exx family are VCN seg-1 init writes (0x7e02:0x101->0x105,
  0x7e85:0x1fb->0x1ff, 0x7eec:0x400, 0x7eeb:0x7fff, 0x7eac/ad:0). Values are VCN 4.0;
  per-offset semantics may differ for 2.0.3, but addressing transfers.
- Discovery parser (validated) at: python inline in session; blob format sig 0x28211407,
  IPDS@0x3C, die_info then ip entries hdr8 layout {hw_id u16, inst u8, num_ba u8, +3 ver,
  base_address[] u32}.
- NEXT (now with absolute addrs): via SMU 0x98/fw-window on the board, SMN-READ 0x7fec
  (VCN seg-1) and the VCN power-status reg -> 0xffffffff = block gated, real value =
  host-BAR gated. Then U2: read 0x7fec, clear bit0, write. Diagnostic is read-only.

## LIVE board frontier reproduced: SMU up + fw loaded, island clamped at root (2026-09-23)

Ran the project's own board tooling (~/vcn_unlock/daveconde-bc250-vcn-enable/enable_vcn.py,
SMU secure path already unlocked) via SSH. All steps board-safe, board stayed alive.

- --verify + --manual-powerup: dom6 gate ctrl 0x6d0f8 0x02->0x00 RELEASED and PERSISTED
  (first real sequencer state change; the gate bit that survived every prior run). Slot
  0x16/0x17/0x18 clock ENABLE bits engaged 0->1 (ON). SMU dom6 power fully satisfied.
- --direct-load ~/vcn_unlock/navi10_vcn.bin: fw staged in VRAM OK (ucode 0x0811800900000002,
  404288B). VCN register file reads UNIFORM 0xffffffff BOTH segments incl static UVD_VERSION
  (0x20f24) -> island clamped at ROOT (rail/isolation), NOT missing-fw, NOT per-reg artifact.
  GC reads fine same transport (transport good). Contradiction: SMU oracle says dom6 UP,
  island says CLOSED. => reproduced the exact community wall on OUR board.
- THESIS: strong software-lock evidence — power works, fw loads, transport works; island
  held by an isolation reg + a MISSING feature-gated message that renoir (same family) HAS
  (PPSMC_MSG_PowerUpVcn). Firmware, not fuse.

Two concrete remaining candidates (mapped live):

1. --dom6-dump: FOUR identical (0x06900900, 0x000000e8) pairs at block +0x054..+0x070 =
   prime ISO-clamp/release the fw programs (July RE: PCIE iso-clamp). BUT 0x06900900 is on
   rxl's HARD-WEDGE list (write wedges SMU). Dangerous. Other single-bit candidates:
   +0x044 0x10000001, +0x074 0xc0000031, +0x084, +0x090, +0x098, +0x1d0 0x40000000.
2. --msg-table: msg 0x3C/0x3D = SetFeatureMask (bitmask). Renoir's PowerUpVcn is
   FEATURE-GATED -> decode which feature bit is VCN/PG and set via 0x3C = candidate native
   path. CAUTION: rxl found feature bit 17 via 0x3C wedges -> need the correct VCN/PG bit.
   Gated clusters (need unlock): 0x27-0x2f, 0x71/0x72/0xa7/0xa8. GHIDRA hunt: xref 0x23b14
   (dom power-up) + 0x246c3 (dom7 caller) callers -> match msg id; power band 0x23370-0x246c3.

- NEXT (safe, offline): decode msg 0x3C feature bitmask for the VCN/PG bit from the SMU
  decompile (board has ~/vcn-work/amd_smu_reverse_engineering; feature bits in
  kernel smu_v11_8_pmfw.h). SMU state is session-only (cold boot restores gate 0x02;
  re-run --manual-powerup after any cold cycle).

## msg 0x3C feature-bit path DEAD; iso-clamp release exists unwired in SMU (2026-09-23)

Subagent decode (docs/action-logs/2026-09-23-smu-0x3c-vcn-feature-bit.md):

- FIRM NEGATIVE: smu_v11_8_pmfw.h (Cyan Skillfish exact) has NO VCN/PG feature bit.
  64 bits: 0..36 named, 37..63 SPARE. No FEATURE_VCN/UVD/JPEG/VCE/ISP/_PG. VCN is NOT
  a DPM/feature entity on this silicon. So msg 0x3C SetFeatureMask CANNOT power VCN.
  Bit 17 (known wedge) = FEATURE_MGCG (chip-wide clock gating). Only bit 6 GFX_DPM
  gates a power path (GFX WGP, not VCN). Framework FUN_0001d940; msg 0x3C ->
  q2_0x05_enable_smu_features 0x1DC58. Cross-ref: Van Gogh smu_v11_5 HAS
  FEATURE_VCN_DPM_BIT, Renoir smu_v12_0 has a VCN/PG bit -> that's why PowerUpVcn is
  feature-gated there; Cyan Skillfish 11.8 diverges (no VCN feature bit, no PowerUp/
  DownVcn message).
- KEY FINDING: the VCN iso-clamp RELEASE exists in the SMU image but is UNWIRED:
  FUN_0001dd74, a 29-entry 0x090xxxxx bulk block-clamp table @0x150B0 (the 0x06900900
  family from --dom6-dump). NOT wired to any feature callback, NO found caller. So the
  release routine is present-but-dead. (The three t28 0x0900C004 literals are the
  separate PSP/ARM VCN gate.)
- THESIS strengthened: the VCN clamp-release code is COMPILED INTO the SMU
  (FUN_0001dd74) but never called on Cyan Skillfish = unwired software, not a fuse.

Updated lever list (SMU power up + fw loaded + island all-ones):

- DEAD: msg 0x3C feature bit (no VCN bit).
- FUN_0001dd74 iso-clamp release (29-entry 0x090xxxxx table @0x150B0): the real SMU-side
  lever, but reaching it needs SMU code-exec (call it directly via the unlock) OR
  replicate its 29 SMN writes (0x090xxxxx = rxl hard-wedge on read/bad-value; write the
  fw's own template values e.g. 0xe8 in order). Code-exec path uses the already-active
  secure unlock.
- UNTESTED SAFE: (a) write 0x03E810 = 6 (VCN_SEG enable; PSP gasket zeroed it stock=0,
  donor=6) — never tried live; (b) functional VAAPI decode test on the vcn kernel
  (Angablade/holde once got frames) — bypasses register introspection.
- Reframe: VCN MMIO all-ones (incl static UVD_VERSION) reads like aperture-not-decoded,
  not just power-gate -> the fabric/NBIF aperture + iso-clamp (FUN_0001dd74) is the door.

## Extracted SMU iso-clamp-release table (FUN_0001dd74) from clv t08 (2026-09-23)

Offline extraction from evidence/donor/retroweb-20260916/BC250_5.00_clv.bin, PSP type 0x08
(SMU) @file 0x8fee00 sz 0x40200, $PS1 @+0x10.

- 29-entry block-clamp table at t08+0x151b0 (matches subagent's @0x150B0), u32 SMN addrs
  0x090XX230, 0x00000000-terminated:
  09003230 09004230 09005230 0900b230 0900c230 09010230 0900f230 09012230 09018230
  0901c230 09022230 09023230 09024230 09025230 0902d230 09028230 09029230 0902e230
  09033230 09032230 09046230 09064230 09031230 0907c230 09300230 09050230 0900e230
  09006230 0902f230
  -> 0x0900c230 is present (same 0x0900c block as VCN cold-reset 0x0900c004).
- Second table t08+0x18770.. : 0x090XX008 addrs (09013008 090a8008 090d1008 ... ) -
  a different per-block register set (offset +0x008 vs +0x230).
- The clamp-release VALUE each addr gets is NOT yet decoded (needs FUN_0001dd74 body decode;
  dom6-dump saw 0x06900900<-0x000000e8 but that is the 0x069 space, different from 0x090).
- To TRIGGER FUN_0001dd74: (a) build a thunk to CALL it via the already-active SMU code-exec
  (daveconde build_inline_store_thunk/smn_store) - most surgical, needs the unlock/thunk; or
  (b) replicate the 29 writes via secure SMN window (wedge-prone; 0x090xxxxx family). Both use
  the SMU secure access already active on the board.
- Safe untested alternatives that avoid the clamp table: 0x03E810=6 (gasket VCN_SEG enable),
  functional VAAPI decode test on the vcn kernel.
