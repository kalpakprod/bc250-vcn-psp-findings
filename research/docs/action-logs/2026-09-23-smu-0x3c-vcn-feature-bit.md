# SMU msg 0x3C (SetFeatureMask) — is there a VCN/PG feature bit?

Date: 2026-09-23. Read-only static analysis. No image or hardware modified.

## Lead (answer first)

**There is NO VCN/UVD/JPEG/VCE/PG feature bit in this PMFW's feature framework.**
The SMU 11.8 (`smu_v11_8_pmfw.h`) 64-bit feature enum for Cyan Skillfish / BC-250
defines bits 0..36 (named) and 37..63 (all `SPARE`). **None** names VCN, UVD, JPEG,
VCE, a VCN-DPM, or a power-gating (PG) domain. The multimedia/VCN block is simply
not represented in the SMU DPM/feature framework on this silicon.

Consequently **no feature bit's callback reaches the VCN power/iso path.** Setting
any feature bit via msg 0x3C (SetFeatureMask) will not run a VCN power-up. This is a
**negative result**: the "native PowerUpVcn via SetFeatureMask" hypothesis does not
hold for the SMU 11.8 PMFW. The VCN gate lives elsewhere (PSP t28 gate byte @
VA 0xE18B70; dedicated SMU domain messages Q3 0x5C / 0x61), not in the feature mask.

**Bit 17 (the known wedge) = `FEATURE_MGCG_BIT`** — Medium-Grain Clock Gating, a
chip-wide clock-gating reconcile, not VCN. Wedging on enable is consistent with MGCG
forcing clock-gating across all domains.

---

## 1. The full 64-bit SMU 11.8 feature list

Source: `smu_v11_8_pmfw.h` (Cyan Skillfish / BC-250's exact PMFW major, SMU 11.8),
local copy `import/from-windows/Users/kukuruza/tmp_bc250/recon/smu_v11_8_pmfw.h`.

| bit    | name                                 |     | bit | name                       |
| ------ | ------------------------------------ | --- | --- | -------------------------- |
| 0      | FEATURE_CCLK_CONTROLLER              |     | 32  | FEATURE_MEAS_DRAM_BLACKOUT |
| 1      | FEATURE_GFXCLK_EFFT_FREQ             |     | 33  | FEATURE_CC1                |
| 2      | FEATURE_DATA_CALCULATION             |     | 34  | FEATURE_PPT                |
| 3      | FEATURE_THERMAL                      |     | 35  | FEATURE_STAPM              |
| 4      | FEATURE_PLL_POWER_DOWN               |     | 36  | FEATURE_CSTATE_BOOST       |
| 5      | FEATURE_FCLK_DPM                     |     | 37  | FEATURE_SPARE_37           |
| 6      | FEATURE_GFX_DPM                      |     | 38  | FEATURE_SPARE_38           |
| 7      | FEATURE_DS_GFXCLK                    |     | 39  | FEATURE_SPARE_39           |
| 8      | FEATURE_DS_SOCCLK                    |     | 40  | FEATURE_SPARE_40           |
| 9      | FEATURE_DS_LCLK                      |     | 41  | FEATURE_SPARE_41           |
| 10     | FEATURE_CORE_CSTATES                 |     | 42  | FEATURE_SPARE_42           |
| 11     | FEATURE_G6_SSC (G6 UCLK/UCLK_DIV SS) |     | 43  | FEATURE_SPARE_43           |
| 12     | FEATURE_RM                           |     | 44  | FEATURE_SPARE_44           |
| 13     | FEATURE_SOC_DPM                      |     | 45  | FEATURE_SPARE_45           |
| 14     | FEATURE_DS_SMNCLK                    |     | 46  | FEATURE_SPARE_46           |
| 15     | FEATURE_DS_MP1CLK                    |     | 47  | FEATURE_SPARE_47           |
| 16     | FEATURE_DS_MP0CLK                    |     | 48  | FEATURE_SPARE_48           |
| **17** | **FEATURE_MGCG ← known wedge**       |     | 49  | FEATURE_SPARE_49           |
| 18     | FEATURE_DS_FUSE_SRAM                 |     | 50  | FEATURE_SPARE_50           |
| 19     | FEATURE_GFX_CKS                      |     | 51  | FEATURE_SPARE_51           |
| 20     | FEATURE_FP_THROTTLING                |     | 52  | FEATURE_SPARE_52           |
| 21     | FEATURE_PROCHOT                      |     | 53  | FEATURE_SPARE_53           |
| 22     | FEATURE_CPUOFF                       |     | 54  | FEATURE_SPARE_54           |
| 23     | FEATURE_UMC_THROTTLE                 |     | 55  | FEATURE_SPARE_55           |
| 24     | FEATURE_DF_THROTTLE                  |     | 56  | FEATURE_SPARE_56           |
| 25     | FEATURE_DS_MP3CLK                    |     | 57  | FEATURE_SPARE_57           |
| 26     | FEATURE_DS_SHUBCLK                   |     | 58  | FEATURE_SPARE_58           |
| 27     | FEATURE_TDC (legacy APM)             |     | 59  | FEATURE_SPARE_59           |
| 28     | FEATURE_UMC_CAL_SHARING              |     | 60  | FEATURE_SPARE_60           |
| 29     | FEATURE_DFLL_BTC_CALIBRATION         |     | 61  | FEATURE_SPARE_61           |
| 30     | FEATURE_EDC                          |     | 62  | FEATURE_SPARE_62           |
| 31     | FEATURE_DLDO                         |     | 63  | FEATURE_SPARE_63           |

`NUM_FEATURES 64`. No FEATURE_VCN*, FEATURE_UVD*, FEATURE_JPEG*, FEATURE_VCE*,
FEATURE_ISP*, FEATURE__*PG anywhere. The named bits are all CPU/GFX/SOC clock-DPM,
deep-sleep (DS*_), throttle, and CPU/thermal/voltage policy.

## 2. VCN/PG-gating feature bit: NONE — with the decompile cross-ref

- **The feature framework is `FUN_0001d940` (`0x1D940`).** It reconciles the 64
  requested/current bits and invokes each bit's **enable callback at table+0x10**
  or **disable callback at table+0x110**. `q2_0x05_enable_smu_features` (`0x1DC58`,
  reachable as **msg 0x3C** on the Q2/Q3 mailbox and as Q2 0x05) does
  `feature_mask |= mask` at `0x17374` then calls `FUN_0001d940` to walk callbacks.
  `FUN_0001db54(n)` tests whether feature n is enabled.
  (Sources: `import/.../recon/SMU-HANDLERS.md`, `docs/action-logs/2026-09-14-smu-window-followup.md`.)
- **The callbacks physically nearest the power code are NOT VCN:**
  - feature **4** → `0x23C24` = `PLL_POWER_DOWN` (matches header bit 4). Installs a
    periodic callback via `0x1B1E4`, returns 1.
  - feature **21** → `0x2496C` = `PROCHOT` (matches header bit 21). Same shape.
  - These matches confirm the callback table is keyed by the header's bit numbering,
    so "no VCN bit in the header" ⇒ "no VCN callback in the table."
- **No feature callback calls the domain power-up `FUN_00023b14`.** The historic
  "PowerUpDomain message 0x21 → `0x249DC` → `0x23B14`" lead was **retracted**:
  `0x249DC` only reads the arg via `0x0FFC`, calls `0x2494C` (float/frequency
  arithmetic + state store), returns 1 — **no call to `0x23B14`**
  (`2026-09-14-smu-window-followup.md`, "G7 correction"). `FUN_00023b14` itself
  (decompile `evidence/firmware-audit/20260919-zd/window_decomp.txt:360`) reads a
  status word, masks 3/2-bit fields into a per-domain struct (+0x98/+0x99), and
  loops a 27-entry table (stride 0x1C) updating a `+0x7e` byte — a domain
  status/level applier, reached only by the dedicated domain-power path
  (`0x2362C`/`0x23B14` band), **not** by the feature mask.
- **Bit 6 (`FEATURE_GFX_DPM`) is the only feature that gates a power path** — it
  gates `RequestActiveWgp` (WGP/compute-unit gating) and the `q1_0x08` state action
  via `FUN_0001db54(6)`. That is GFX WGP gating, **not VCN**.

**Explicit bit-17 identity:** bit 17 = `FEATURE_MGCG_BIT` (Medium-Grain Clock
Gating). Not VCN. This matches the observed hard wedge (rxl8819516).

## 3. The candidate action, evaluated

- Hypothetical "set feature bit N via msg 0x3C" for VCN: **no valid N exists.**
  Every named bit (0..36) is CPU/GFX/SOC/DS/throttle policy; 37..63 are `SPARE`
  (undefined — enabling a spare walks a null/undefined callback slot, an
  unbounded-risk no-op at best, and is not a VCN lever).
- Mask value would be `1 << N`; there is no N whose callback runs `FUN_00023b14(6,1)`
  (dom6/VCN) or releases the iso-clamp. **So there is no bitmask to recommend.**
- The decompile does **not** show any feature callback reaching the VCN power-up.
  Negative result confirmed statically.

## 4. Feature bit whose callback writes 0x0900c004 (cold-reset) / 0x06900900 iso-clamp: NONE FOUND

- The SMN `0x0900xxxx` block-clamp path exists in the SMU image but is **not wired to
  a feature callback.** Function `0x1DD74` iterates a 29-entry table (pointer literal
  `0x17390` → `0x150B0`) of `0x090xxxxx230` values, masks each to a 20-bit offset and
  clears the matching `0x01000000`-window dword — a bulk per-block reset/clamp. The
  every-byte direct-call scanner over `[0,0x3A000)` found **no direct caller** of
  `0x1DD74`; its registration/timing is unknown and it is **not** a feature-bit
  callback (`2026-09-14-smu-window-followup.md`, "Array consumer" sections).
- `0x0900C004`/`0x0900C230`/`0x0900C234` appear as literals but on the SMU (Xtensa)
  side they are consumed by the domain/clamp routines above, not by the 64-bit
  feature framework. (The PSP-side `0x0900C004` clamp-release literals — ×3 at FILE
  0x9922BC/0x994D4C/0x994ECC in t28 — are the ARM PSP VCN gate, a separate blob;
  see `2026-09-23-clv-t28-vcn-gate-disasm.md`.) **No feature bit drives either.**

## 5. Cross-ref: what the NAME would be on Renoir / Van Gogh

On the sibling SoCs the VCN block _is_ in the feature framework, which is exactly why
PowerUpVcn is feature-gated there — and why looking for the same on 11.8 was worth
ruling out:

- **Van Gogh** `smu_v11_5_pmfw.h`: has a `FEATURE_VCN_DPM_BIT`; `smu_v11_5_ppt.c`
  `vangogh_set_vcn_enable` gates on it and sends PowerUp/PowerDownVcn.
- **Renoir** `smu_v12_0_pmfw.h`: has a VCN feature bit (`FEATURE_VCN`/PG-class);
  `renoir_ppt.c` uses the PowerUpVcn message with it.

(Exact Van Gogh/Renoir bit numbers recalled, not locally verified — no local copies of
those headers exist. The load-bearing point is the _symbol name_ `FEATURE_VCN*`, which
is **absent** from 11.8.) Cyan Skillfish (11.8) diverges: its multimedia block is not a
DPM/feature entity, so there is no feature bit to set and no SMU message
(PowerUpVcn/PowerDownVcn are also absent from the 11.8 message set — SMU-FINDINGS.md).

## Honest limits

- Static only; no hardware exercised. Static analysis is not proof of runtime behavior.
- The named-feature conclusion is **certain** (definitive header enumerates all 64).
- The "no feature callback reaches VCN" conclusion rests on: (a) the header having no
  VCN bit, (b) the two power-adjacent callbacks decoding as PLL_POWER_DOWN / PROCHOT,
  (c) the retraction of the 0x21→0x23B14 edge. The full 64-entry callback table was
  **not** exhaustively re-disassembled slot-by-slot in this pass; bits 37..63 are
  `SPARE` (no defined callback). If a spare slot held an undocumented VCN callback it
  would still not be nameable/derivable statically — but the header marking them SPARE
  and the message set lacking PowerUpVcn make that highly unlikely.
- The SMN clamp routine `0x1DD74` has no found caller; whether it is dead code or
  indirectly registered is unresolved (stated, not assumed).

## Key file/line citations

- 64-bit list: `import/from-windows/Users/kukuruza/tmp_bc250/recon/smu_v11_8_pmfw.h`
  (FEATURE_*_BIT 0..63; bit 17 = FEATURE_MGCG_BIT).
- Feature framework + callbacks: `docs/action-logs/2026-09-14-smu-window-followup.md`
  (§"Feature framework assessment": `0x1D940`, table+0x10/+0x110, feat4=`0x23C24`
  PLL_POWER_DOWN, feat21=`0x2496C` PROCHOT; §"G7 correction": 0x21→0x249DC no
  `0x23B14`; §"Array consumer": `0x1DD74` / `0x150B0`, 0x090xxxxx230, no caller).
- msg 0x3C→enable_smu_features (`0x1DC58`), feature-6 gate: `import/.../recon/SMU-HANDLERS.md`;
  `scratch/amd_smu_reverse_engineering/tables/known_messages_smu_fw_robin_5.txt`.
- `FUN_00023b14` body: `evidence/firmware-audit/20260919-zd/window_decomp.txt:360`.
- PSP t28 VCN gate (separate blob): `docs/action-logs/2026-09-23-clv-t28-vcn-gate-disasm.md`.
