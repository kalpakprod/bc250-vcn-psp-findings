# BC250 v003c Route-B VCN Unlock — Programmer Flash Runbook

Status: STAGED, NOT flashed. Physical execution requires operator
approval of the exact image name + SHA-256.
Package: `firmware-flash-pkg/20260924-v003c-route-b-vcn/` (`SHA256SUMS`).
Method: **Hardware programmer (CH347 + flashrom) ONLY**. No AFU, no in-OS flash.

This runbook supersedes
`docs/guides/bc250-v003b-route-b-programmer-flash-runbook.md` (v003b
REJECTED: its driver FFS was placed after the erased free tail at inner-FV
`0x432000`, where the real DxeCore FV walker stops — the driver would
never dispatch. See the v003c package README and the appended v003b action
log). Everything else about the design is unchanged from v003b.

Build evidence:
- Base: `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3` (sha256 `606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`), the community 3.00 the board's P3-family lineage matches.
- Driver: `candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.efi` (12,288 B, sha256 `ba1cf214…`), FFS blob sha256 `e8b2a62c…` (state normalized to `0xF8` in-image).
- Candidate: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin` (sha256 `dafb323a5d701f29b9c1b74f0a6bc728572590ced54a8389c01b20c0a4f828b0`).
- Builder: `scripts/build_v003c_bds_prefix.py`; manifest: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003c.build.json`.
- Injection geometry: driver FFS at inner-FV `0x12940`, BEFORE `Bds.ffs` (which shifts to `0x15960`), contiguous after the previous file (D6A2CB7F…), 8-byte aligned, size `0x301C`, state `0xF8`, 193 -> 194 files. This is the W9-proven placement class (hardware-dispatched injected driver).
- Pre-flight: `scripts/verify_candidate_preflight.py` 9/9 gates PASS, VERDICT GO (`evidence/firmware-audit/20260924-v003c-preflight/result.json`), including G9 (erased gap before the new file = 0 = dispatch reachable) and the capsule FFS header checksum.

This runbook inherits the full hardware procedure from
`docs/guides/bc250-v003-community-vcn-programmer-flash-runbook.md`
(same base, same chip `W25Q128.V`, same CH347 method, same
preconditions, same power isolation, same double-read backup, same
rollback structure). Sections below state only what differs.

---

## 1. Package Identity

| File | SHA-256 | Size |
|---|---|---|
| `BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin` | `dafb323a5d701f29b9c1b74f0a6bc728572590ced54a8389c01b20c0a4f828b0` | 16,777,216 B |

## 2. Driver Behavior (unchanged from v003b design)

- Route-B: no `0x1B` doorbell; direct replay of the measured
  `FUN_0002A184` bring-up tail (24 steps) with secure read (`0x2A`),
  RMW+readback verify, 250 ms timeout-guarded polls, abort guards;
  skips the destructive builder `FUN_00024594`.
- Policy lock (measured): SMU never runs the VCN tail on this board
  (policy word @`0xCCB8` = 0). The driver performs the tail itself
  after DXE dispatch.
- One variable per flash: no FCLK/MCLK/UCLK/8-core changes; v2 items
  (pump block, `0x01D80814 |= 2`, `0x0220FE00 &= ~4`) deferred.

## 3. Preconditions

Identical to the v003 runbook: full power isolation, CR2032 out,
CH347 only, `--flash-name` must report `W25Q128.V`, DP display + LAN
attached, P0 LED oracle noted.

## 4. Procedure

Identical to the v003 runbook steps 1-6, with the v003c names:

1. Double read backup: `pre-v003c-read-a.bin` / `pre-v003c-read-b.bin`,
   `cmp` must match, hash recorded.
2. `sha256sum -c SHA256SUMS` in the package dir -> `OK`.
3. Operator approval template (filled):
```text
Подтверждаю запись файла firmware-flash-pkg/20260924-v003c-route-b-vcn/BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin
SHA-256: dafb323a5d701f29b9c1b74f0a6bc728572590ced54a8389c01b20c0a4f828b0
на плату BC-250-01, чип W25Q128.V.
Pre-write дамп: pre-v003c-read-a.bin, SHA-256 [хеш], 16 MiB, два чтения совпали.
Recovery: pre-v003c-read-a.bin + evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3.
Route: programmer re-write + readback.
```
4. `flashrom -p ch347_spi:spispeed=1.875M -w BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin` -> rc 0 + `VERIFIED`.
5. Readback `post-v003c-readback.bin`, `cmp` against the candidate -> `FLASH VERIFIED EXACT` (expect `dafb323a…`).
6. Bring-up: clip off, battery in, 12V in, power on, observe P0 LED + DP.

## 5. Hardware Acceptance Gates

| Gate | Check | Pass Criteria |
|---|---|---|
| **H1** | POST & Display | LED green activity, DP video, UEFI visible |
| **H2** | UEFI Stability | Stable in Setup/Shell >= 5 min (driver aborts cleanly if it ran and bailed) |
| **H3** | OS Boot | Linux to login/SSH (the board's current baseline: SSH works) |
| **H4** | VCN discovery | `dmesg`/`lspci` shows the VCN function, `amdgpu` loads without ring timeout |
| **H5** | Codec readiness | `vainfo` lists decode profiles |
| **H6** | Clock controller state | probe4l6-style readback: VCN clock controller now ENABLED vs the pre-flash `not enabled` |
| **H7** | Stability soak | 15 min video decode or `vainfo` + brief playback without crash |

H6 is the direct before/after evidence pair: pre-flash probe
(`evidence/runtime/20260924-012740-probe4l6-vcnctl.json`) measured the
controller ALIVE, boot-programmed, but NOT enabled.

If H4-H6 fail but H1-H3 pass: the board still boots and is recoverable;
collect `dmesg`, re-run probe4l6, and the v2 items (pump block,
`0x01D80814 |= 2`, `0x0220FE00 &= ~4`) become the next hypotheses — the
documented v2 path, not a rollback reason by itself.

## 6. Rollback

- Path A: re-write `pre-v003c-read-a.bin` + readback verify.
- Path B: re-write the donor base
  `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3` (sha256
  `606a7a7f…`).

## 7. Honest Assessment

- Pre-flight 9/9 PASS with DxeCore-semantics dispatch reachability
  (the exact defect class that killed v003b is now a named gate, G9).
- No emulator run of the DXE driver itself (board library protocols are
  board-specific); the replay steps are cross-referenced to the
  emu-phase2 trace of the real bring-up.
- Boot confidence ceiling, stated honestly: the base class runs on this
  board right now (P3-family provenance doc); the change class (one DXE
  driver added inside the compressed FV, before Bds) is the W9-proven
  class; the af531026 boot failure was a DIFFERENT class (whole 3.00 DXE
  FV grafted onto a 5.00 PSP/SMU/ABL lineage). No static check can
  guarantee a boot; recovery is proven by deed (the board was restored
  from the af531026 brick via this same programmer path).
- The physical effect (VCN ungated, firmware loaded, codec answering)
  is unproven until H4-H7.
