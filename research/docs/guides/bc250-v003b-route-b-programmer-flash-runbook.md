# BC250 v003b Route-B VCN Unlock — Programmer Flash Runbook

**SUPERSEDED by `docs/guides/bc250-v003c-programmer-flash-runbook.md` —
v003b REJECTED (driver FFS placed after the erased free tail; DxeCore
never dispatches it). Do not flash v003b. Kept for provenance.**

Status: STAGED, NOT flashed. Physical execution requires operator
approval of the exact image name + SHA-256.
Package: `firmware-flash-pkg/20260924-v003b-route-b-vcn/` (`SHA256SUMS`).
Method: **Hardware programmer (CH347 + flashrom) ONLY**. No AFU, no in-OS flash.

Build evidence:
- Base: `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3` (sha256 `606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182`), boot-proven.
- Driver: `candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.efi` (12,288 B, sha256 `ba1cf214…`), FFS wrap sha256 `e8b2a62c…`.
- Candidate: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin` (sha256 `3a7fcf8507c6ea1a366bc8f8c584f7613e0cfac4ce9fcef47c031ed80f853f4d`).
- Build manifest: `candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003b.build.json`.
- Action logs: `docs/action-logs/2026-09-24-v003b-route-b.md`, `docs/action-logs/2026-09-24-plan-consumers.md`.
- Gates: `pytest tests/ -q` 83/83; independent injector verification PASS (193 -> 194 files, byte-identical outside the FV, PSP/APCB untouched).

This runbook inherits the full hardware procedure from
`docs/guides/bc250-v003-community-vcn-programmer-flash-runbook.md`
(same base, same chip `W25Q128.V`, same CH347 method, same
preconditions, same power isolation, same double-read backup, same
rollback structure). Sections below state only what differs.

---

## 1. Package Identity

| File | SHA-256 | Size |
|---|---|---|
| `BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin` | `3a7fcf8507c6ea1a366bc8f8c584f7613e0cfac4ce9fcef47c031ed80f853f4d` | 16,777,216 B |

Same injection geometry as v003 (GUID
`B6250780-7E00-4203-900C-23443B1413FE`, inner FV `0x432000`, size
`0x301c`, state `0xF8`, 193 -> 194 files). The base and every byte
outside the main compressed FV are identical to the v003 lineage;
only the driver payload inside differs (route-B rewrite).

## 2. Driver Behavior Differences vs v003 (why this one is staged)

- v003 sent PSP message `0x1B` early (wedge hazard: empty-args doorbell
  with unchecked response). v003b never sends `0x1B`.
- v003b replays the measured bring-up tail directly
  (`FUN_0002A184` tail steps, cross-referenced to the emu-phase2 trace):
  power-gate windows `0x0115F950/958/964`, PLL table, divider, command
  pulses — with secure read (`0x2A`), RMW+verify, and 250 ms
  timeout-guarded polls. It does NOT run the builder `FUN_00024594`
  (proven destructive: zeroes boot-programmed controller words).
- Abort guards: any protocol mismatch, SMU-alive check failure, or
  verify mismatch -> the driver logs and exits cleanly. It cannot hang
  POST on a poll (bounded timeouts on every wait).
- Policy lock (measured): SMU never runs the VCN tail on this board
  (policy word @`0xCCB8` = 0). The replay in the driver is the only
  in-BIOS route.

## 3. Preconditions

Identical to the v003 runbook: full power isolation, CR2032 out,
CH347 only, `--flash-name` must report `W25Q128.V`, DP display + LAN
attached, P0 LED oracle noted.

## 4. Procedure

Identical to the v003 runbook steps 1-6, with the v003b names:

1. Double read backup: `pre-v003b-read-a.bin` / `pre-v003b-read-b.bin`,
   `cmp` must match, hash recorded.
2. `sha256sum -c SHA256SUMS` in the package dir -> `OK`.
3. Operator approval template (filled):
```text
Подтверждаю запись файла firmware-flash-pkg/20260924-v003b-route-b-vcn/BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin
SHA-256: 3a7fcf8507c6ea1a366bc8f8c584f7613e0cfac4ce9fcef47c031ed80f853f4d
на плату BC-250-01, чип W25Q128.V.
Pre-write дамп: pre-v003b-read-a.bin, SHA-256 [хеш], 16 MiB, два чтения совпали.
Recovery: pre-v003b-read-a.bin + evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3.
Route: programmer re-write + readback.
```
4. `flashrom -p ch347_spi:spispeed=1.875M -w BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin` -> rc 0 + `VERIFIED`.
5. Readback `post-v003b-readback.bin`, `cmp` against the candidate -> `FLASH VERIFIED EXACT` (expect `3a7fcf85…`).
6. Bring-up: clip off, battery in, 12V in, power on, observe P0 LED + DP.

## 5. Hardware Acceptance Gates

| Gate | Check | Pass Criteria |
|---|---|---|
| **H1** | POST & Display | LED green activity, DP video, UEFI visible |
| **H2** | UEFI Stability | Stable in Setup/Shell >= 5 min (driver aborts cleanly if it ran and bailed) |
| **H3** | OS Boot | Linux to login/SSH (the board's current baseline: SSH works) |
| **H4** | VCN discovery | `dmesg`/`lspci` shows the VCN function, `amdgpu` loads without ring timeout |
| **H5** | Codec readiness | `vainfo` lists decode profiles |
| **H6** | Clock controller state | probe4l6-style readback: VCN clock controller now ENABLED (config `0x0E`, enable bit set) vs the pre-flash `not enabled` |
| **H7** | Stability soak | 15 min video decode or `vainfo` + brief playback without crash |

H6 is the direct before/after evidence pair: pre-flash probe
(`evidence/runtime/20260924-012740-probe4l6-vcnctl.json`) measured the
controller ALIVE, boot-programmed, but NOT enabled. The driver's job is
exactly to set that enable.

If H4-H6 fail but H1-H3 pass: the board still boots and is recoverable;
collect `dmesg`, re-run probe4l6 on the new state, and the v2 items
(pump block, `0x01D80814 |= 2`, `0x0220FE00 &= ~4`) become the next
hypotheses — that is the documented v2 path, not a rollback reason by
itself.

## 6. Rollback

Identical structure to the v003 runbook:
- Path A: re-write `pre-v003b-read-a.bin` + readback verify.
- Path B: re-write the donor base
  `evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3` (sha256
  `606a7a7f…`).

## 7. Honest Assessment

- Static + injector verification PASS; no emulator run of the DXE
  driver itself (board library protocols are board-specific).
- The replay steps are cross-referenced to the emu-phase2 trace of the
  real bring-up; the physical effect (VCN ungated, firmware loaded,
  codec answering) is unproven until H4-H7.
- One-variable image: no FCLK/MCLK/UCLK/8-core changes on this base.
