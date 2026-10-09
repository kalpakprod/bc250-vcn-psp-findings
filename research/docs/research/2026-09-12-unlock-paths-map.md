# BC-250 VCN unlock paths — complete map (2026-09-12)

Statuses updated with the 2026-09-12 hardware campaign (S2-A execution, 4 cold cycles,
gasket runtime programming, NBIO probe). Evidence classes per the project contract.
Sources: master plan 2026-08-26, chain report 2026-08-29, synthesis 2026-09-11,
VCN-LOCK-MECHANISM.md, and the 2026-09-12 action log.

## The blocker, stated once

All runtime evidence converges: power (dom6 up-ack), clocks (slots 0x16/0x17/0x18 ON),
firmware staging, driver registration, and the full donor gasket runtime programming
(59/59 writes accepted, bank-12 commit=1) are all PROVEN individually — and the host
VCN register file still reads uniformly all-ones. The missing transition is the
NBIF/Fabric bridge open (chain-report gate G5): PSP applies the gasket at
DRIVER_ENTRIES and hardware-locks the Fabric translation matrices; runtime writes to
the data-plane registers do not re-open it.

## Path inventory

### P1. Runtime SMU/SMN path (chain Path A, VULN-B) — transport PROVEN, transition missing

- P1.1 SMU unlock (Q2 msg 0x23 ring overflow -> debug byte 0x7B3C): PROVEN, repeatable
  (field 2026-08-25/26; re-verified 2026-09-12 twice). Prerequisite for everything.
- P1.2 Q3 SMN proxy writes (msg 0x2C/0x2A): PROVEN transport. Donor gasket runtime
  programming EXECUTED 2026-09-12: 59/59 accepted, `0x0900C234` commit=1. The gasket
  registers LATCH at runtime.
- P1.3 Bridge via programmed gasket: DISPROVEN 2026-09-12 (arbiter all-ones, clean
  reads, fully brought-up state). The write list alone is not the missing transition.
- P1.4 NBIO candidates `0x13b1005c/.60/0x13b00084/.4c`: DISPROVEN as clamp carriers
  (single-reg reads safe; values `0x8000/0xffff/0x108/0x800000`; no PEIM `0x3` pattern).
- P1.5 REMAINING (primary): offline static RE of the trusted executor —
  (a) SEC_GASKET type-0x24 parser/executor in ABL/PSP bodies (`trace_sec_gasket_executor.py`
  per master plan use-case 2): group dispatch, requester/client derivation for HWID 12,
  commit + lock transitions;
  (b) `AmdNbioGfxARIPei` disasm: where Init Config Struct offsets `0x1e0/0x1e1`
  (the `0x3` = clamped writes) serialize in NBIO space — derive TRUE NBIF registers.
  Output must predict an observable internal state change before any host MMIO attempt.

### P2. UEFI same-session activation (chain Path B orchestrator) — implementation EXISTS, same blocker

- `Bc250VcnProbeApp.efi` (historical source `archives/imported/uefi-source/legacy-tmp-bc250-dxe/Bc250VcnUnlockPkg/`; not an accepted safe-run artifact): unlock SMU +
  restore dom6/clocks + 56-write replay + chainload Limine in the SAME UEFI session,
  no reset; the historical `startup_min_probe.nsh` script is preserved at
  `archives/imported/vcn-probes/legacy-tmp-bc250/` but is not a current boot
  instruction. Emprio evidence: dom6 state
  persists across UEFI chainload into Linux.
- Value: pre-OS orchestration (Linux boots with power+clocks+gasket already applied;
  avoids the mode2 first-MMIO wedge). Bound by the same G5 blocker: DXE runs AFTER
  PSP policy finalization, so the missing trusted transition must come from P1.5.
- E4/Bc250CoreUnlockDxe status correction (G7, 2026-09-12): the E1 DXE-only no-boot
  result (2026-09-11T21:25) predates the display-wiring fix and is NON-DISCRIMINATING;
  the boot-safety question of DXE-only edits is REOPENED (low priority — its 0x98
  payload is already known insufficient for the bridge).

### P3. PSP-time firmware ladder (flash) — mostly closed after 2026-09-12

- P3.1 Unsigned policy edits (D3-B2/policy-only): CLOSED — PSP rejection proven with
  correct display wiring (2026-09-12 04:0x).
- P3.2 APCB DFG tokens: BOOT-SAFE, grant present in all D-tests (G7 correction
  2026-09-12: D8-D19 boot to Linux carrying DFG `0x007FFF00`, cksum `0x32`;
  the 2026-09-11 "boot-unsafe" verdict used the pre-wiring-fix non-discriminating
  series and is disproved). The DFG grant did NOT prevent the ReadyToBoot gasket
  wedge — wedge is transport/context, not missing-grant. No further DFG test needed.
- P3.3 D3-C SIGNED relocation (byte-identical signed gasket + directory repoint only):
  NOT BUILT, NOT TESTED. The only clean flash discriminator of
  relocation-vs-signature. Deprioritized: today's runtime result shows the gasket
  VALUES are programmable anyway — the flash path's unique value would be the
  boot-time execution CONTEXT, which a relocation does not create.
- P3.4 S5 in-place single-value $PS1 edit: gated on P3.3 booting.
- P3.5 DEBUG_UNLOCK Type 0x13 token: DEAD (RSA-2048 over `SEC_DBG_PUBLIC_KEY~0x9`,
  kid 6c5f...; requires AMD private key; not fakeable). Master plan defers key
  extraction as out of scope.
- P3.6 Donor/PS5 BIOS flash: NO donor image in the corpus; board-specific NVRAM/APCB
  coupling makes it a rebuild, not a flash. Not a current path.

### P4. Kernel side (chain Path C) — required after the bridge, not an unlock by itself

- Probe kernels PROVEN (mode1: VCN block + fw load hardware-verified 2026-09-12;
  mode2 wedge root-caused = first MMIO with domain gated).
- Staged hardware patch (0012, stages 2-6 in master plan §5): DESIGNED, not built.
  Mandatory for the post-bridge bring-up (VCPU -> decode -> encode -> JPEG).
- `amdgpu.fw_load_type=0`: PROHIBITED (GFX KIQ failure evidence).

### P5. Trusted-environment side — no path

- AMD-TEE unavailable, no VCN TA ABI (master plan). TOS C2P blob loader
  (0x100B/0x100C/0x1033): MEASURED NEGATIVE 2026-09-12 (TOS does not answer direct
  C2P commands on this board; evidence SHA `d6f74e4d...`).

## Ranked next actions

1. **P1.5a offline**: build `trace_sec_gasket_executor.py` (or Cutter/Rizin session) on
   the ABL/PSP bodies + `AmdNbioGfxARIPei` — recover the type-0x24 executor state
   machine (requester identity, commit, lock). No board risk. THE primary path.
2. **P1.5b offline**: same session, derive true NBIF registers from the PEIM/PEI
   config-struct serialization; only then consider one reversible runtime bit-write
   (new runbook + approval).
3. **P2 pre-OS experiment** (after P1.5 yields a transition): extend
   `Bc250VcnProbeApp.efi` with the bounded transition + internal oracle, USB boot,
   same-session chainload, two cold-boot repeats (master plan use-cases 3-4).
4. **P4 staged kernel** (0012): build in parallel — needed the moment the bridge opens.

## What is not claimed

- No bridge-open, VCPU, ring, codec, or stability evidence exists on the target.
- No signature bypass is proven; offline RSA verification never reproduced.
- The fabric-lock model (boot-time-only) is the favored explanation, not proven —
  the executor RE is the test that would prove or replace it.
