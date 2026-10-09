# BC-250 VCN evidence reassessment and safe next slice

Status: partially outdated evidence spec. Forward planning and unfinished checklist are superseded by `2026-08-26-bc250-vcn-unlock-master-plan.md`; measured evidence and completed source-validation records remain authoritative.

## Title and scope

Recheck the BC-250 VCN conclusions against preserved boot evidence and the actual AMDGPU control flow, retract claims that exceed the evidence, and define the next fail-closed driver and secure-policy research slice.

## Planning anchor

The anchor is the repeated GFX KIQ failure:

```text
ring kiq_0.2.1.0 test failed (-110)
KCQ enable failed
hw_init of IP block <gfx_v10_0> failed -110
```

The changed assumption is that this failure identified an RC7 kernel regression. Preserved boots show the same failure on the packaged stable kernel when global `amdgpu.fw_load_type=0` was present, while the same stable kernel initializes normally when the parameter is absent. RC7 was never clean-booted with `fw_load_type=-1`, so RC7 itself has not been isolated as the cause.

This is non-local because the evidence crosses Limine boot configuration, AMDGPU global firmware policy, VCN-specific firmware placement, IP-block registration, ring readiness, UEFI execution timing, PSP policy, and hardware recovery.

Related specifications:

| Specification | Status after reassessment | Action |
| --- | --- | --- |
| `2026-08-26-bc250-vcn-vector-a-kernel-patch.md` | partially outdated | Amend its RC7 and runtime-reload conclusions; point to this specification. |
| `2026-08-26-bc250-vcn-path1-verdict-and-next-gate-analysis.md` | partially outdated | Downgrade unproven SEC_GASKET group, IOHC, lock-bit, and DXE-before-lock claims. |
| `2026-08-26-bc250-vcn-path2-dxe-driver-spec.md` | partially outdated | Retain UEFI tooling, but remove the assumption that DXE executes before PSP gasket finalization. |
| `2026-08-25-bc250-vcn-gasket-diff.md` | active evidence | Reuse its cautious differential and runtime-replay result. |
| `2026-08-25-bc250-vcn-trusted-environment-report.md` | partially outdated | Reuse its TEE/debug-token findings; amend its pre-replay and board-state statements. |

## Connected groups or observed existing logic

### 1. Boot evidence and global firmware selection

Purpose: distinguish kernel-version, UEFI, VCN-registration, and firmware-loading effects.

Observed Existing Logic:

- Boot `856553a5` used RC7 with `amdgpu.bc250_vcn=1 amdgpu.fw_load_type=0`; VCN firmware was found, then GFX KIQ failed.
- Boot `a70b5882` used the packaged stable kernel with the same command line. The stock module ignored unknown `bc250_vcn`, yet GFX KIQ still failed.
- Boots `68aa89fc` and `78673ab7` used the same packaged stable kernel without either experimental argument and initialized AMDGPU successfully.
- Therefore global `fw_load_type=0` is the only experimentally isolated input shared by both failed boots and absent from both successful stable boots.
- No clean RC7 boot with `fw_load_type=-1` exists in the preserved evidence.

Validation:

- Evidence file: `tmp_bc250/recon/audit_vcn_boot_evidence_2026-08-26.out`.
- Current board: packaged stable module, `fw_load_type=-1`, `/dev/dri/card1` and `renderD128`, no fatal GFX initialization errors.

### 2. AMDGPU VCN firmware workflow

Purpose: map every VCN-specific branch that must agree on PSP versus direct firmware placement.

Mapped files and functions:

- `drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c#amdgpu_vcn_early_init` requests the firmware selected from UVD IP version.
- `amdgpu_vcn.c#amdgpu_vcn_sw_init` sizes and allocates the VCPU BO. The firmware payload is included only when the VCN path is direct.
- `amdgpu_vcn.c#amdgpu_vcn_resume` copies firmware into the VCPU BO only for the direct path.
- `amdgpu_vcn.c#amdgpu_vcn_setup_ucode` adds VCN firmware to the global PSP table only for the PSP path.
- `vcn_v2_0.c#vcn_v2_0_mc_resume` and `vcn_v2_0_mc_resume_dpg_mode` select PSP TMR addresses or the VCN BO address.
- `vcn_v2_0.c#vcn_v2_0_start_sriov` contains the corresponding SR-IOV branch, although BC-250 is not tested as an SR-IOV VF.

Observed Existing Logic:

```text
requested VCN firmware
  --select global PSP path--> PSP ucode table + PSP TMR cache window
  --select global direct path--> larger VCPU BO + firmware copy + BO cache window
```

The compiled experimental VCN-only patch is incomplete as an implementation contract. It changed setup, copy, and cache-window branches, but did not change the VCPU BO-size condition in `amdgpu_vcn_sw_init`. With global PSP mode and VCN-only direct copy, the BO lacks the firmware payload allocation. A later copy would overlap stack/context/shared regions. Compile success does not validate this path.

Compatibility strategy:

- Keep global AMDGPU firmware policy at its proven default.
- Centralize VCN-specific selection in one helper such as `amdgpu_vcn_fw_is_psp(adev)`.
- Use that helper for BO sizing, PSP registration, firmware copy, normal MC resume, DPG MC resume, and any other VCN firmware-address branch.
- Do not duplicate BC-250 predicates independently in `amdgpu_vcn.c` and `vcn_v2_0.c`.

### 3. VCN registration and hardware initialization

Purpose: separate software proof from any VCN MMIO access.

Mapped files and functions:

- `amdgpu_discovery.c` adds VCN and JPEG IP blocks for BC-250 IP `2.0.3` when opted in.
- `vcn_v2_0.c#vcn_v2_0_sw_init` performs IRQ registration, common VCN software initialization, firmware setup/copy, and ring allocation.
- `vcn_v2_0.c#vcn_v2_0_hw_init` immediately programs the doorbell range and tests decode/encode rings. Ring tests require live VCN MMIO and hardware.
- The normal IP-function table also exposes hardware fini, resume, idle, clock-gating, power-gating, and state-dump callbacks that may access VCN after initialization.

Risk if skipped:

A simple early return from normal `hw_init` is not a complete fail-closed stage. JPEG registration and later PM/debug callbacks can still touch VCN, while initialized rings could become visible without working hardware.

Planned compatibility shape:

- `bc250_vcn_mode=0`: do not add VCN or JPEG IP blocks.
- `bc250_vcn_mode=1`: add a BC-250 probe-only VCN IP block, omit JPEG, run only audited software/firmware steps, force every ring scheduler to not-ready, and use no-op hardware, PM, idle, clock, power, resume, and dump callbacks.
- `bc250_vcn_mode=2`: add the normal VCN/JPEG blocks and permit hardware initialization only in an explicitly selected recovery-capable boot.

### 4. Runtime overlay and reload evidence

Purpose: prevent an invalid control from becoming a platform rule.

Observed Existing Logic:

- A stable-final overlay with matching vermagic was built and installed outside the packaged module.
- After stopping display consumers, unbinding PCI `0000:01:00.0`, and removing the packaged module, loading the experimental overlay with `bc250_vcn=0` reset or hard-hung the board.
- The direct-VCN predicates are false at `bc250_vcn=0`, but the overlay still differs from the packaged module and was built outside the full package pipeline.

Corrected conclusion:

This experiment proves that this overlay/reload control is unusable. It does not prove that every AMDGPU runtime reload on BC-250 is intrinsically unsafe, and it does not identify VCN logic as the reset cause. Future validation must boot a complete co-installable kernel package rather than replace AMDGPU live.

### 5. Power, clocks, fabric policy, and trusted execution

Purpose: distinguish proven prerequisites from the leading secure-policy hypothesis.

Proven observations:

- Native domain-6 OFF/ON and VCN clock-slot restoration work while SMU remains alive.
- Firmware can be staged and verified in VRAM.
- VCN BAR5 reads remain uniformly `0xffffffff` after power/clock restoration.
- A working Cezanne SEC_GASKET contains a 56-write HWID-12 bank covering VCN register ranges; Robin omits it.
- All 56 writes can be replayed through privileged SMU SMN access without opening host VCN MMIO.
- Linux AMD-TEE is unavailable, and no callable VCN secure-world ABI has been identified.
- Modifying SEC_GASKET invalidates its RSA signature and the enlarged candidate does not fit its original slot.

Corrected interpretation:

The missing HWID-12 SEC_GASKET bank is the strongest known platform differential and a leading explanation for the closed bridge. It is not proven to be the sole blocker, to authorize the x86 host specifically, or to become effective through ordinary register stores. Exact claims that group `0x280` is a lock operation, that `0x3e810/0x3e814` is the required IOHC remap path, or that one known bit freezes the table remain hypotheses until the loader/executor is reverse-engineered.

UEFI DXE runs after PSP/ABL early policy initialization on this platform. The existing ProbeApp is valuable for same-session SMU state and chainloading, but it is not currently evidence of execution before SEC_GASKET finalization.

Secure `DEBUG_UNLOCK` support and its RSA public key are proven. Its ability to disable the VCN gasket is not proven, and no signing key or accepted token is available.

### 6. Specifications and validation

Purpose: keep future code and hardware experiments aligned with corrected evidence.

Validation paths:

- Boot evidence must include boot ID, kernel release, complete command line, module source/version, and decisive logs.
- A control boot changes one factor only.
- Experimental kernels are co-installable and preserve the packaged stable kernel and initramfs.
- No runtime AMDGPU replacement is used as acceptance evidence.
- No VCN MMIO read/write occurs in probe-only mode.
- Live secure-policy writes require a recovered loader/executor contract, explicit register ownership, rollback, and cold-power recovery.

## Use cases

### 1. Reproduce a clean firmware-policy control

packaged stable kernel --boot with default global firmware policy--> healthy GFX baseline --boot a complete test kernel with unchanged global policy--> comparable test baseline

Execution Logic:

1. Input: packaged stable kernel, clean Limine entry, packaged initramfs. Outcome: control boot. Logic: verify `fw_load_type=-1`, AMDGPU initialization, KIQ, and `/dev/dri`. External state: boot evidence file. Config parameters: no VCN arguments. Metrics: boot ID and decisive timestamps.
2. Input: co-installable final-7.2 test kernel. Outcome: isolated VCN-mode boot. Logic: preserve global firmware policy and vary only `bc250_vcn_mode`. External state: separate kernel package and boot entry. Config parameters: `bc250_vcn_mode=0|1|2`. Metrics: GFX result, VCN logs, recovery requirement.

Tests:

- description: default stable baseline remains healthy
  input: packaged stable kernel with no experimental arguments
  workflow: boot --initialize AMDGPU--> `/dev/dri` available
  expected outcome: no KIQ/GFX fatal errors
- description: global direct firmware regression remains reproducible only as historical evidence
  input: preserved boot journals
  workflow: compare failed and successful stable boots --isolate command-line difference--> `fw_load_type=0`
  expected outcome: no new live boot is required to reconfirm a known dangerous global setting

### 2. Probe VCN software and firmware without VCN hardware access

test kernel mode 1 --register probe-only VCN workflow--> requested firmware --allocate correctly sized VCPU BO--> copied firmware with rings disabled

Implementation Logic:

- Implement one VCN-specific PSP/direct helper and use it at every VCN firmware-layout branch.
- Define a probe-only IP-function table instead of returning early from the normal hardware table.
- Register VCN but not JPEG in mode 1.
- Reuse audited early/software init only after confirming every called function is free of VCN MMIO.
- Explicitly set decode and encode ring schedulers not-ready.
- Use no-op hardware/PM/resume/idle/dump callbacks in probe mode.
- Emit bounded evidence: firmware name/version, firmware mode, BO size, firmware payload size, GPU address, and probe-only completion. Do not dump firmware contents.

Files And Functions:

- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c` - define read-only mode parameter.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu.h` - declare mode state.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c` - choose off, probe-only VCN, or normal VCN/JPEG registration.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c#amdgpu_vcn_sw_init` - central firmware-layout helper and correct BO sizing.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c#amdgpu_vcn_resume` - direct VCN payload copy.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c#amdgpu_vcn_setup_ucode` - exclude direct VCN from PSP table.
- existing: `drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c` - probe-only IP table and centralized firmware address selection.
- planned: focused source-level test or compile-time assertion for VCPU BO layout.

Input Validation And Contracts:

- Reject mode values outside `0..2` by clamping to `0` and logging once.
- Mode 1 contract: no VCN/JPEG MMIO, no ready VCN/JPEG scheduler, no hardware callback with side effects.
- Mode 2 contract: recovery-capable boot explicitly selected; never default.

### 3. Reverse-engineer the SEC_GASKET loader and executor

Robin and Cezanne PSP/ABL binaries --locate type-0x24 consumer--> group parser --recover requester, commit, and finalization semantics--> evidence-backed secure-policy contract

Detailed Workflow:

1. Locate cross-references from PSP-directory type `0x24`, container body pointers, and group counts into ABL/PSP code.
2. Identify dispatch for group types `0x201`, `0x203`, `0x206`, `0x210`, `0x280`, and `0x281`.
3. Recover the actual write transport: direct SMN, secure service, indexed port, copied policy table, or another mechanism.
4. Determine whether `0x0900c234`, `0x0900cb80`, and descriptor fields are data, commands, commit gates, locks, or a mixture.
5. Binary-diff equivalent Robin and working-sibling handlers before assigning semantic names.
6. Record the boot phase and requester identity required for the HWID-12 bank.

Validation:

- Every assigned semantic name has a decompiled basic block or cross-reference.
- At least one non-VCN bank with known working hardware validates the parser interpretation.
- Static results explain why ordinary SMU writes leave MMIO closed without assuming the conclusion.

Deferred:

- Live PSP exploitation, token forgery, firmware flashing, or signed-container relocation is outside this reassessment slice.

### 4. Preserve UEFI same-session state without claiming secure-policy timing

UEFI ProbeApp --unlock SMU and restore clocks/domain state--> Limine chainload --boot probe-only kernel--> compare preserved control-plane evidence

Observed Existing Logic:

The ProbeApp can unlock SMU debug access, restore VCN clock slots/domain state, and chainload Limine in the same UEFI session. Its 56-write Gasket replay did not open host VCN MMIO.

Validation:

- Use mode 1 only.
- Confirm Linux GFX remains healthy.
- Confirm SMU/clock/domain evidence survives chainload.
- Do not treat this as a bridge-unclamp test and do not perform VCN MMIO.

### 5. Enter VCN hardware initialization only after a stronger bridge proof

evidence-backed secure-policy mechanism --apply reversible preconditions--> recovery-capable boot --select mode 2--> VCPU and ring validation

Execution Logic:

- Mode 2 remains disabled until the SEC_GASKET/bridge mechanism has a recovered contract.
- The first hardware test uses cold-power recovery, serial/netconsole evidence, and one bounded stage at a time.
- Validation order: VCN IP visibility, firmware placement, VCPU status, decode ring, encode rings, media nodes, VAAPI.
- A board reset or uniformly blocked MMIO ends the attempt; no blind retries.

## Implementation checklist

1. [x] Initialize the repository specification lifecycle and planning contract.
2. [x] Preserve and compare boot evidence across RC7/stable and global firmware-policy states.
3. [x] Map the VCN firmware, BO, IP registration, and hardware-init control flow.
4. [x] Reassess SEC_GASKET, UEFI timing, secure debug, and runtime replay claims.
5. [x] Amend or mark partially outdated the affected older specifications listed in the planning anchor.
6. [x] Replace duplicated direct-VCN predicates with one VCN firmware-policy helper and fix every connected BO/address branch.
7. [x] Design and implement the probe-only VCN IP-function table with no JPEG or hardware callbacks.
8. [x] Add focused validation for BO sizing, mode validation, no-MMIO probe behavior, and ring readiness.

Recovered implementation record: three earlier oversized Terra attempts produced only inconsistent partial edits or no safe source changes, so `vcn-probe-new` was reset byte-for-byte to `vcn-probe-base`. Reverse engineering of the Empryo bridge confirms a hard 18-step code-agent ceiling; `maxTurns` cannot raise it. The Terra lane was restored for bounded one- or two-file slices by enabling structural/composed exploration tools, rejecting oversized ownership before broad reads, limiting discovery to four calls, and requiring the first edit by step six. An eight-file deterministic smoke task completed before the width guard was tightened. After the final repair, a three-file task failed immediately with `BLOCKED: TASK_TOO_WIDE`, and a one-file bounded edit completed with `TERRA_BOUNDED_PASS 1`. The lane now fails wide briefs early and completes bounded work. The source patch is accepted for offline packaging: static checker passes `VCN_PROBE_PATCH_PASS files=7 helper_calls=7`, unified patch apply-check passes, and a final-7.2 AMDGPU module compiles with matching vermagic and `bc250_vcn_mode`. No module was installed or loaded.
9. [x] Build and install a complete co-installable final-7.2 probe package with separate mode-0 and mode-1 entries.
10. [ ] Execute mode-0 and mode-1 cold-boot controls; synchronize evidence and specifications.
    - Mode 0 passed as the stock-equivalent control.
    - Mode 1 firmware/BO setup succeeded, but the first implementation violated its contract by reusing normal `vcn_v2_0_sw_init`, registering VCN rings, and allowing global IB tests. The original verifier missed the `IB test failed on vcn_*` log form.
    - Corrective package `7.2.0-1.92-cachyos-vcn-bc250` is rebuilding with dedicated ring-free probe early/sw init and a strict verifier. Mode 1 remains incomplete until a new cold boot has zero VCN/JPEG ring activity.
11. [ ] Reverse-engineer the SEC_GASKET type-0x24 loader/executor and update the hardware hypothesis.
12. [ ] Defer mode 2 until the secure-policy contract and recovery gate pass review.

## Open questions

- Non-blocking: retain `bc250_vcn_mode` as the public parameter name or use a narrower `bc250_vcn_probe_mode` until hardware mode is authorized.
- Non-blocking: package name should remain separate from both stock stable and RC7; proposed `linux-cachyos-vcn-bc250`.
- Blocking before mode 2: which trusted boot-stage function consumes SEC_GASKET group entries, and what requester/lock state does it require?

## Decision log

- Route: evidence audit with a fresh read-only Sol reviewer because live firmware/GPU experiments have hard-reset risk.
- Global `fw_load_type=0` is rejected; it is experimentally associated with pre-VCN GFX KIQ failure on both RC7 and stable.
- RC7 is not declared defective; the existing evidence confounds RC7 with global direct firmware mode.
- Final 7.2 remains the preferred implementation baseline because its clean stock boot is proven healthy, not because RC7 was disproven.
- The runtime overlay/reload experiment is classified as unusable, not as proof that all AMDGPU reloads are inherently unsafe.
- SEC_GASKET HWID 12 remains the leading secure-policy hypothesis, not a proven sole root cause.
- UEFI DXE is treated as post-PSP-policy execution unless reverse engineering proves an earlier or privileged commit path.
- The compiled VCN-only direct patch is not accepted: it omitted VCPU BO firmware space and duplicated policy predicates.
- User authorized implementation of the next dependency-ready slice; mode-2 live hardware initialization remains deferred.
- Selective route escalated to `full` because the change spans AMDGPU firmware layout, IP callbacks, and hard-reset risk. Terra and Sol role templates passed preflight.
- Terra returned partial, partial, then blocked across three bounded source attempts. Per circuit breaker and Sol Advisor fail-closed routing, the implementation lane stopped rather than silently substituting root or another role.
- Terra lane recovery: Empryo's bridge ceiling remains 18 code steps, so `maxTurns` is fixed at 18 and large source changes must be decomposed into dependency-ordered one- or two-file Terra slices. `structural_edit`, `explore_script`, and `genome_query` are enabled; oversized briefs fail early; discovery is capped at four calls; deterministic Windows fallbacks are required. Pre-guard smoke completed eight trivial edits with `TERRA_LANE_SMOKE_PASS 8`; final guard verification returned `BLOCKED: TASK_TOO_WIDE` for three files and `TERRA_BOUNDED_PASS 1` for one file.
- Source slices 6-8 completed and compiled offline. Patch `0011-bc250-vcn-probe-mode.patch` changes seven AMDGPU files, passes static and apply checks, and produced module SHA-256 `08531def0e25791398b0b8391e006905eb9839ab58a2da45f75ec7166561b082` with release `7.2.0-1.1-cachyos-bc250`.
