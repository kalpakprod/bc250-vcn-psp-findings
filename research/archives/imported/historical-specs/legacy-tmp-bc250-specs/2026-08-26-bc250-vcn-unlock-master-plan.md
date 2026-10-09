# BC-250 VCN Unlock Master Plan

> **Execution contract:** apply `writing-plans`, `spec-first-planning-loop`, `brainstorming`, `connected-code-mapping`, `layered-workflow-planning`, and `verification-before-completion`. Implement dependency-ready tasks only, preserve rollback, and record fresh evidence after every live-board transition.

**Goal:** bring BC-250 VCN from the current powered-but-host-inaccessible state to stable hardware decode and encode through the normal Linux DRM/VA-API stack.

**Architecture:** keep the proven stock final-7.2 GPU path as the control, finish the fail-closed AMDGPU probe package, reverse-engineer the signed SEC_GASKET loader/executor to identify the missing trusted transition, prove the VCN bridge internally before any host MMIO access, then enable VCPU, decode, encode, and JPEG in separate cold-boot stages. Do not modify or flash signed PSP firmware, do not use global `amdgpu.fw_load_type=0`, and do not treat compilation or IP-block registration as hardware success.

**Tech stack:** AMD BC-250 Robin P3.00, SMU PMFW 88.6.0, PSP/ABL/SEC_GASKET firmware, EDK2 UEFI application and Limine same-session chainload, Linux 7.2 AMDGPU/VCN 2.0, Python analysis tools, CachyOS package build, DRM render node, Mesa VA-API, FFmpeg.

**Status:** active canonical plan. Forward-planning sections in the older BC-250 VCN plans are superseded by this document; their measured evidence remains reusable unless explicitly corrected here.

## Title and scope

Unlock VCN by resolving the remaining trusted fabric-policy transition, then advance through bounded Linux hardware stages until decode and encode work. The scope includes evidence cleanup, SEC_GASKET executor reverse engineering, reversible pre-OS activation, staged AMDGPU integration, user-space validation, recovery, and synchronization of earlier BC-250 specifications.

## Planning anchor

The concrete hardware anchor is unchanged:

```text
VCN power domain 6 active
+ VCLK/DCLK and slots 0x16-0x18 active
+ firmware staged and verified in VRAM
+ complete 56-write HWID-12 runtime replay performed
+ host VCN BAR5 reads remain uniformly 0xffffffff
```

The changed assumption is that power, clocks, raw register replay, VCN firmware placement, or driver registration alone can unlock the block. Existing evidence rejects each as a sufficient condition. The missing condition is now defined narrowly as a trusted boot-stage transition that makes the VCN fabric route accessible to the host.

This work is non-local because the proof chain crosses PSP signed policy, ABL/SEC_GASKET parsing, requester authorization, lock/commit timing, SMU execution, UEFI same-session state, AMDGPU firmware placement, VCN IP callbacks, cold-boot packaging, DRM initialization, Mesa VA-API, and physical recovery.

Current measured state:

| Layer | Status | Evidence-based conclusion |
| --- | --- | --- |
| Stock GPU/GFX | healthy on final `7.2.0-1.1-cachyos-bc250` | Keep as control; no global firmware-policy override. |
| SMU debug access | available through the existing reversible research path | Useful for measurement and bounded writes; not itself a VCN unlock. |
| Domain 6 | real OFF/ON cycle proven | Power sequencing is no longer the primary blocker. |
| VCN clocks | VCLK/DCLK and slots `0x16-0x18` proven active | Clock programming is no longer the primary blocker. |
| Firmware staging | `navi10_vcn.bin` copied and verified in VRAM | Placement is proven; VCPU execution is not. |
| Host VCN MMIO | uniformly `0xffffffff` | Bridge/requester policy is still closed. |
| SEC_GASKET differential | working siblings contain a 56-write HWID-12 bank; Robin contains none | Leading secure-policy hypothesis, not yet causal proof. |
| Runtime HWID-12 replay | all writes accepted; no MMIO change | Raw stores after boot are insufficient. |
| Linux AMD-TEE | unavailable; no VCN TA ABI identified | Not a current activation path. |
| Unsigned firmware candidate | invalid RSA signature and oversized original slot | Offline research artifact only; never flash. |
| Kernel probe patch | seven files, static checker and module compile passed | Diagnostic infrastructure only; complete package build still running. |
| VCN hardware | not unlocked | No VCPU handshake, ring success, VA-API decode, or encode. |

Impacted specification actions:

| Existing specification | Action | Resulting status |
| --- | --- | --- |
| `2026-08-26-bc250-vcn-evidence-reassessment-and-safe-next-slice.md` | reuse measured evidence; replace its forward checklist | partially outdated evidence spec |
| `2026-08-26-bc250-vcn-vector-a-kernel-patch.md` | retain failed/global-policy evidence; replace forward plan | superseded plan |
| `2026-08-26-bc250-vcn-path1-verdict-and-next-gate-analysis.md` | retain runtime-replay result; replace architecture plan | superseded plan |
| `2026-08-26-bc250-vcn-path2-dxe-driver-spec.md` | retain UEFI application and chainload implementation; replace timing assumptions | partially outdated implementation reference |
| `2026-08-25-bc250-vcn-community-second-gate-plan.md` | retain historical tasks; replace remaining path | superseded plan |
| `2026-08-25-community-second-gate-execution-report.md` | reuse as measured power/clock evidence | active evidence |
| `2026-08-25-bc250-vcn-gasket-diff.md` | reuse as secure-policy differential | active evidence |
| `2026-08-25-bc250-vcn-trusted-environment-report.md` | reuse TEE/debug-token evidence with later replay corrections | partially outdated evidence |
| `2026-08-25-psp-nbio-firmware-extraction-report.md` | reuse extracted PSP/NBIO inventory | active evidence |

## Connected groups or observed existing logic

### 1. Evidence, controls, and recovery

Purpose: ensure every new claim is attributable to one changed input and recoverable by a cold power cycle.

Observed existing logic:

- The clean control is final 7.2 with stock AMDGPU and default global firmware policy.
- Global `amdgpu.fw_load_type=0` is associated with GFX KIQ failure on both RC7 and stable and is prohibited.
- Runtime AMDGPU overlay replacement is not accepted as evidence because it reset or hung the board even with VCN disabled.
- The user authorizes reversible changes and physical power-cycle recovery.

Files and functions:

- existing: `tmp_bc250/recon/audit_vcn_boot_evidence.sh` - capture boot-local kernel and AMDGPU evidence.
- existing: `tmp_bc250/recon/rollback_vcn_test_kernel.sh` - remove experimental kernel configuration.
- existing: `tmp_bc250/recon/rollback_stable_amdgpu_vcn_overlay.sh` - remove the obsolete live overlay.
- planned: `tmp_bc250/recon/collect_vcn_gate_evidence.sh` - produce one manifest per gate with hashes, boot ID, cmdline, kernel, module parameters, MMIO policy, and result.

Invariant: one cold boot changes one gate. A failed gate must leave the stock boot entry usable without the USB path.

### 2. Fail-closed AMDGPU software path

Purpose: validate VCN firmware and software allocation without touching VCN MMIO, doorbells, rings, JPEG, or PM callbacks.

Observed existing logic:

- `0011-bc250-vcn-probe-mode.patch` defines `bc250_vcn_mode=0/1/2`.
- Mode 1 registers a probe-only VCN IP block, omits JPEG, centralizes VCN-specific direct firmware placement, allocates firmware space in the VCPU BO, and forces schedulers not-ready.
- The patch passes `VCN_PROBE_PATCH_PASS files=7 helper_calls=7`, applies cleanly, and produced a matching-vermagic module offline.
- The complete co-installable package build is still active; no package has been installed or booted.

Files and functions:

- existing: `tmp_bc250/recon/0011-bc250-vcn-probe-mode.patch` - current probe implementation.
- existing: `tmp_bc250/recon/check_vcn_probe_patch.py` - source invariants and no-MMIO checks.
- existing: `tmp_bc250/recon/build_verify_vcn_probe_package.sh` - package archive, vermagic, firmware, and stock-package checks.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c#amdgpu_vcn_fw_is_psp` - single VCN firmware-policy helper.
- existing: `drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c#vcn_v2_0_probe_ip_block` - fail-closed software-only block.

Invariant: mode 1 may prove firmware request, BO layout, and software initialization only. It must not be reported as VCN hardware progress.

### 3. Signed SEC_GASKET loader and executor

Purpose: recover the exact trusted transition that consumes type `0x24`, selects group/client semantics, writes HWID-12 policy, commits policy, and locks it.

Observed existing logic:

- Cezanne/Renoir working policies contain an identical 56-write HWID-12 bank at `0x0900c000..0x0900cfff`.
- Robin omits that bank.
- Runtime SMU replay of the same ordered writes does not open host MMIO.
- Therefore the missing mechanism can include execution context, requester identity, group selection, commit sequence, lock timing, or a separate transition not represented by the write list.

Files and functions:

- existing: `tmp_bc250/recon/parse_sec_gasket.py` - parse group/write structure.
- existing: `tmp_bc250/recon/decode_sec_gasket_banks.py` - decode bank descriptors.
- existing: `tmp_bc250/recon/analyze_vcn_gasket_semantics.py` - validate HWID-12 descriptors.
- existing: `tmp_bc250/recon/robin3_psp_bodies/` - Robin signed bodies.
- existing: `tmp_bc250/recon/cezanne_a3mstx_370e/` and `tmp_bc250/recon/v2000a/` - working sibling policies.
- planned: `tmp_bc250/recon/trace_sec_gasket_executor.py` - identify type-0x24 references, parser loops, group dispatch, commit, and lock operations across ABL/PSP binaries.
- planned: `tmp_bc250/recon/compare_sec_gasket_execution_paths.py` - compare Robin and working-sibling executor inputs and branches.
- planned: `tmp_bc250/specs/2026-08-26-bc250-sec-gasket-executor-workflow.md` - reverse-documented trusted workflow.

Invariant: raw address similarity is not enough. The output must identify a callable or reproducible transition and the post-transition state it guarantees.

### 4. UEFI same-session activation

Purpose: execute the proven prerequisites and any newly identified reversible trusted transition before Linux without resetting SMU state.

Observed existing logic:

- `Bc250VcnProbeApp.efi` can unlock SMU, restore VCN clocks/domain state, replay the 56-write profile, and chainload Limine in the same UEFI session.
- Same-session state can survive into Linux.
- DXE execution is currently treated as post-PSP-policy execution; it is not assumed to run before gasket finalization.
- Direct host VCN MMIO reads in UEFI have hard-hung the fabric and are forbidden before a stronger internal proof.

Files and functions:

- existing: `tmp_bc250/dxe/Bc250VcnUnlockPkg/Bc250VcnProbeApp/Bc250VcnProbeApp.c#UefiMain` - pre-OS orchestration.
- existing: `tmp_bc250/dxe/Bc250VcnUnlockPkg/Bc250VcnProbeApp/Bc250VcnProbeApp.c#ChainloadLimine` - same-session handoff.
- planned: `tmp_bc250/dxe/Bc250VcnUnlockPkg/Bc250VcnProbeApp/Bc250VcnProbeApp.c#ApplyTrustedVcnPolicyTransition` - bounded transition only after the executor contract is known.
- planned: `tmp_bc250/recon/vcn_bridge_oracle.py` - read internal policy/route state through a bounded non-host-MMIO path.

Invariant: pre-OS code must fail closed and chainload the stock control when a prerequisite or readback fails.

### 5. Staged VCN hardware initialization

Purpose: replace the current monolithic hardware mode with bounded boot stages that expose the first failing transition.

Planned stages:

| Stage | Allowed behavior | Success signal | Forbidden until success |
| --- | --- | --- | --- |
| 0 | mode off; stock GPU | normal GFX/KIQ and `/dev/dri` | all VCN registration |
| 1 | probe-only software/firmware | BO and firmware evidence, no MMIO | doorbells, VCPU start, rings, JPEG |
| 2 | one bounded VCN identity/status read after internal bridge proof | non-`0xffffffff`, non-hanging stable value | firmware boot and rings |
| 3 | program firmware address and start VCPU | bounded VCPU-ready handshake | ring schedulers and JPEG |
| 4 | initialize and test decode ring only | decode ring fence completes | encode and JPEG |
| 5 | initialize encode rings | encode fence completes | JPEG |
| 6 | initialize JPEG and normal PM callbacks | JPEG smoke and clean suspend/resume | none within VCN scope |

Files and functions:

- planned: `tmp_bc250/recon/0012-bc250-vcn-staged-hardware.patch` - stage parameter and bounded callbacks.
- planned: `tmp_bc250/recon/check_vcn_staged_patch.py` - assert each stage exposes only permitted callbacks/register operations.
- existing: `drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c#vcn_v2_0_hw_init` - decompose into stage-owned functions.
- existing: `drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c#vcn_v2_0_mc_resume` - firmware address programming.
- existing: `drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c#vcn_v2_0_start` - VCPU and ring start sequence.
- existing: `drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c` - BO, firmware, and ring allocation.

Invariant: a stage is promoted only after two cold boots produce the same success signal and no GFX, SMU, PCIe, or filesystem regression.

### 6. User-space media validation

Purpose: prove useful decode and encode through the normal AMDGPU render node.

Corrected success contract:

- AMDGPU VCN normally uses `/dev/dri/renderD128`; `/dev/video*` is not a required success condition.
- `vainfo` must expose expected decode and encode profiles.
- Decode and encode must complete through VA-API with output verification, not just capability enumeration.

Files and functions:

- planned: `tmp_bc250/recon/test_vcn_vaapi.sh` - enumerate profiles and run bounded decode/encode vectors.
- planned: `tmp_bc250/recon/test_vcn_stability.sh` - repeated jobs, idle, suspend/resume, and cold-boot checks.

Invariant: no success claim from `vainfo` alone. Each claimed codec requires a completed job and verified output.

### 7. Specs and community handoff

Purpose: leave one authoritative plan, reproducible evidence, and a minimal patch series the community can review.

Files:

- active: `tmp_bc250/specs/2026-08-26-bc250-vcn-unlock-master-plan.md` - canonical plan.
- planned: `tmp_bc250/specs/2026-08-26-bc250-sec-gasket-executor-workflow.md` - observed secure workflow.
- planned: `tmp_bc250/specs/2026-08-26-bc250-vcn-bringup-results.md` - gate-by-gate results.
- planned: `tmp_bc250/recon/MANIFEST.sha256` - hashes of scripts, patches, firmware input, packages, and evidence outputs.

Invariant: old reports remain evidence; old forward plans must not compete with this plan.

## Use cases

### 1. Establish the reproducible control and probe package

stock final-7.2 boot --finish and verify co-installable package--> mode-0 and mode-1 cold-boot controls

Execution Logic:

1. Input: active package build, `0011` patch, stock installed kernel. Outcome: exactly two package archives in `/tmp/bc250-vcn-probe-packages`. Logic: let the existing build finish; verify package names, release, module vermagic, `bc250_vcn_mode`, `navi10_vcn.bin`, kernel image, headers, hashes, and unchanged stock package. External state: package files only. Config parameters: `pkgbase=linux-cachyos-vcn-bc250`, release `7.2.0-1.91-cachyos-vcn-bc250`. Metrics: build result and archive hashes.
2. Input: verified archives. Outcome: separate Limine entries for mode 0 and mode 1. Logic: install co-installable packages; generate initramfs; add entries without modifying the stock default. External state: new kernel package and boot entries. Config parameters: mode 0, mode 1; global `fw_load_type` absent. Metrics: boot-entry hashes and command lines.
3. Input: recovery-capable boot menu. Outcome: two cold-boot evidence bundles. Logic: boot mode 0, verify stock-equivalent behavior; boot mode 1, verify software/firmware path and no VCN MMIO. External state: evidence files only. Metrics: GFX/KIQ status, `/dev/dri`, firmware request, BO allocation, ring-ready flags, forbidden-access scan.

Tests:

- description: Mode 0 matches stock control.
  input: `amdgpu.bc250_vcn_mode=0`
  workflow: cold boot --initialize AMDGPU--> healthy GFX and DRM without VCN block
  expected outcome: no fatal GPU errors; `card1` and `renderD128`; no VCN/JPEG registration.
- description: Mode 1 remains fail-closed.
  input: `amdgpu.bc250_vcn_mode=1`
  workflow: cold boot --initialize probe VCN--> firmware and BO evidence with schedulers disabled
  expected outcome: no VCN MMIO, doorbell, ring test, JPEG, or PM callback; GFX remains healthy.

### 2. Recover the trusted SEC_GASKET execution contract

signed type-0x24 policy --trace parser, group dispatch, requester state, commit, and lock--> reproducible trusted-transition contract

Detailed Workflow:

```text
| for each Robin and working-sibling firmware body:
  signed entry --locate type-0x24 consumer--> parser entrypoints
  --recover group loop and write primitive--> executor model
  --identify commit and lock transitions--> policy lifecycle |
Robin executor model + working executor model --compare inputs and branches--> VCN-specific missing transition
```

Implementation Logic:

- Build a reference index from parsed group IDs, register addresses, descriptor banks, and binary literal offsets.
- Trace cross-references from type `0x24`, group identifiers `0x201/0x280`, known policy ports, and lock/commit addresses into ABL/PSP functions.
- Recover function boundaries, call order, argument roles, loop termination, requester/client derivation, and post-write synchronization.
- Compare Robin and Cezanne/Renoir control flow. Distinguish missing policy data from a missing caller, disabled feature branch, different requester identity, or earlier lock.
- Produce one state machine with explicit preconditions and one bounded activation hypothesis. If no callable transition is recoverable, stop before live hardware work and record the missing evidence.

Validation:

- Every claimed function has binary offset, input body hash, disassembly/decompilation excerpt, and caller/callee evidence.
- The recovered executor explains all known group types, not only HWID 12.
- The proposed transition predicts an observable internal state change before host MMIO is attempted.

### 3. Prove the bridge internally before host MMIO

known trusted-transition contract --execute bounded pre-OS transition--> internal bridge-open proof --perform one host liveness read--> accessible VCN register file

Input Validation And Contracts:

- Required preconditions: SMU alive, debug access available, domain 6 active, slots `0x16-0x18` enabled, policy transition readback valid, recovery path confirmed.
- Any missing precondition aborts to stock chainload.
- The internal oracle must be bounded and must not depend on a CPU VCN BAR5 read.

Execution Logic:

1. Add only the identified trusted transition and its readback to the UEFI application.
2. Boot from USB, execute prerequisites, evaluate internal policy/route state, and chainload Linux in the same session.
3. In Linux, capture SMU/domain/clock state without touching host VCN MMIO.
4. Only after the internal state matches the recovered contract, boot stage 2 and perform one bounded VCN identity/status read with netconsole/serial capture and cold-power recovery ready.
5. Treat any hang, all-ones read, or unrelated GFX regression as failure; revert to stage 1.

Tests:

- description: Failure before trusted transition remains recoverable.
  workflow: invalid prerequisite --abort activation--> stock chainload
  expected outcome: stock GPU initializes and no VCN access occurs.
- description: Internal bridge oracle is repeatable.
  workflow: two cold boots --apply trusted transition--> same internal open-state evidence
  expected outcome: matching state and hashes before stage 2 is authorized.
- description: First host VCN liveness proof.
  workflow: internally proven open state --read one audited VCN register--> stable non-all-ones value
  expected outcome: no hang; same value class on two cold boots; normal GFX remains alive.

### 4. Start VCPU and validate rings one stage at a time

accessible VCN register file --start VCPU--> firmware-ready VCN --test decode ring--> decode-ready VCN --test encode/JPEG--> complete kernel VCN

Execution Logic:

1. Stage 3 programs the direct firmware cache window and starts VCPU only. Poll one documented ready condition with a fixed timeout; keep every ring scheduler disabled.
2. Stage 4 enables and tests decode only. Do not initialize encode or JPEG.
3. Stage 5 enables encode rings after decode succeeds twice.
4. Stage 6 enables JPEG and replaces probe no-op PM callbacks with audited normal callbacks.
5. At each stage, preserve the previous successful boot entry and create a new entry rather than editing it in place.

Validation:

- Stage 3: firmware address matches the verified BO; VCPU ready arrives before timeout; no ring scheduler is ready.
- Stage 4: decode ring test completes; encode/JPEG remain absent.
- Stage 5: encode ring tests complete; decode remains healthy.
- Stage 6: JPEG smoke, idle, suspend/resume, and reboot do not regress GFX or SMU.

### 5. Prove VA-API decode and encode

complete kernel VCN --expose Mesa VA-API profiles--> verified decode and encode outputs --run stability matrix--> usable VCN

Execution Logic:

1. Install only already-packaged Mesa/VA-API tools unless a missing userspace mapping is proven.
2. Capture `vainfo` against `/dev/dri/renderD128`.
3. Run a small known-good H.264 decode vector and verify decoded frame count/checksum.
4. Run a bounded H.264 encode and verify the output with software decode.
5. Repeat for each claimed codec only after the previous codec passes.
6. Run repeated jobs, idle intervals, cold boot, and suspend/resume with kernel error capture.

Tests:

- description: Hardware decode produces valid frames.
  input: fixed H.264 sample and render node
  workflow: VA-API decode --verify frame count and checksum--> valid decoded output
  expected outcome: hardware path used; no GPU reset or VCN timeout.
- description: Hardware encode produces a valid stream.
  input: deterministic raw frames
  workflow: VA-API encode --software-decode result--> matching frame count
  expected outcome: valid stream and no ring timeout.
- description: Stability gate.
  workflow: repeated decode/encode + idle + suspend/resume --monitor kernel--> stable media stack
  expected outcome: no SMU wedge, PCIe error, GPU reset, filesystem error, or thermal limit violation.

### 6. Package, document, and hand off the unlock

validated VCN stack --minimize patches and publish evidence--> reproducible community implementation with rollback

Execution Logic:

- Separate policy activation, fail-closed probe support, staged hardware bring-up, and final enablement into reviewable patches.
- Preserve stock-off defaults until the full validation matrix passes.
- Produce installation and rollback scripts that never overwrite the stock kernel package.
- Record exact BIOS, firmware, kernel, package, patch, and evidence hashes.
- Update old specifications with final lifecycle states and publish one final results document.

Validation:

- Fresh installation from documented artifacts reproduces mode 0, mode 1, and the final validated stage.
- Removing the experimental package and USB path restores the stock boot without residual module overlays or cmdline parameters.

## Implementation checklist

1. [x] Establish the planning lifecycle, planning contract, and one canonical master plan.
2. [x] Classify earlier reports as evidence versus superseded forward plans.
3. [x] Preserve measured power, clock, firmware-staging, runtime-replay, and boot-policy conclusions.
4. [x] Implement and statically verify `0011-bc250-vcn-probe-mode.patch`.
5. [x] Compile the probe AMDGPU module offline with matching final-7.2 vermagic.
6. [x] Finish and verify the co-installable package build with `build_verify_vcn_probe_package.sh`.
   - Result: `VCN_PROBE_PACKAGE_PASS release=7.2.0-1.91-cachyos-vcn-bc250 packages=2`.
   - Kernel package: `linux-cachyos-vcn-bc250-7.2.0-1.91-x86_64.pkg.tar.zst`, 157451416 bytes, SHA-256 `5b25de8645e94b026d90dc650301ca027f61140f1fd5d835549d9c8117504832`.
   - Headers package: `linux-cachyos-vcn-bc250-headers-7.2.0-1.91-x86_64.pkg.tar.zst`, 39457037 bytes, SHA-256 `fc4d6890f1e289934f229167a9db58a98900189aca10c0287b97887118c6aa12`.
   - External state: verified archives in `/tmp/bc250-vcn-probe-packages`; stock kernel remains installed and active.
7. [x] Install the co-installable probe kernel and headers without changing the stock default entry.
   - Result: `VCN_PROBE_INSTALL_PASS release=7.2.0-1.91-cachyos-vcn-bc250` while the running kernel remained `7.2.0-1.1-cachyos-bc250`.
8. [x] Create immutable Limine entries for mode 0 and mode 1; omit global `fw_load_type`.
   - Entries: `linux-cachyos-vcn-bc250-mode0` with `amdgpu.bc250_vcn_mode=0`, and `linux-cachyos-vcn-bc250-mode1` with `amdgpu.bc250_vcn_mode=1`.
   - Verification: NVMe and both USB Limine config copies share SHA-256 `58e82d7ad82a37d3e626bc8410b0ace80e1e872a8144c12fd5ced03c6de03301`; kernel, initramfs, and module hashes pass.
9. [x] Cold-boot mode 0 and collect the control evidence bundle.
   - Result: `VCN_PROBE_BOOT_PASS mode=0 release=7.2.0-1.91-cachyos-vcn-bc250`; stock-equivalent AMDGPU/DRM initialization, no VCN/JPEG ring activity, evidence boot ID `63ed82c5-c567-4bf4-9ee3-b706777effbd`.
   - Preserved evidence: `tmp_bc250/recon/vcn-probe-mode0_2026-08-26.out`, SHA-256 `0b7c04d489bf0efb1d0105d542da1a0cf3c370f5502d6aaefe40e1db344e6732`.
10. [ ] Cold-boot mode 1 and prove firmware/BO software initialization with no VCN MMIO or ring access.
   - First run disproved the original fail-closed claim: firmware and BO initialization succeeded (`fw_version=0x08118009`, `fw_size=404544`, `vcpu_bo_size=1064960`), but normal `vcn_v2_0_sw_init` registered decode/encode rings and global IB tests executed, failing with `-110`.
   - The verifier had a false-negative regex and incorrectly printed PASS. It now rejects any mode-1 VCN/JPEG ring registration or IB test. Strict replay fails as expected.
   - Root-cause fix in progress: mode 1 now has dedicated early/sw init paths with zero encode rings, no IRQ setup, no `amdgpu_ring_init`, no doorbell setup, and no hardware callbacks. Rebuild target: `7.2.0-1.92-cachyos-vcn-bc250`.
11. [ ] Synchronize the corrected mode-1 rerun into this plan and the reassessment spec.
12. [ ] Implement `trace_sec_gasket_executor.py` with body-hash and offset-backed findings.
13. [ ] Reverse-document the type-0x24 parser/executor in `2026-08-26-bc250-sec-gasket-executor-workflow.md`.
14. [ ] Implement `compare_sec_gasket_execution_paths.py` for Robin versus working siblings.
15. [ ] Identify requester/client derivation, group selection, commit, synchronization, and lock transitions.
16. [ ] Define one bounded internal bridge oracle and its expected before/after states.
17. [ ] Review the trusted-transition contract against all preserved evidence; stop if it cannot predict an internal state change.
18. [ ] Add fail-closed `ApplyTrustedVcnPolicyTransition` and internal readback to the UEFI application; its docstring must name the use-case 3 workflow step `execute bounded pre-OS transition` for code-to-spec traceability.
19. [ ] Build, hash, and deploy the UEFI image to USB while preserving the current known-good image.
20. [ ] Execute two cold-boot internal-oracle runs and compare evidence hashes.
21. [ ] Design `0012-bc250-vcn-staged-hardware.patch` with stages 2-6 and previous-stage boot preservation.
22. [ ] Add `check_vcn_staged_patch.py` to enforce allowed operations per stage.
23. [ ] Build a co-installable staged kernel package; verify archive, module, firmware, initramfs, and boot entries offline.
24. [ ] Execute stage 2: one bounded host VCN liveness read after internal proof.
25. [ ] Execute stage 3: VCPU firmware-address programming and ready handshake only.
26. [ ] Execute stage 4: decode ring only.
27. [ ] Execute stage 5: encode rings.
28. [ ] Execute stage 6: JPEG and audited PM callbacks.
29. [ ] Run `vainfo` against the DRM render node and record profiles.
30. [ ] Implement and run deterministic VA-API decode validation.
31. [ ] Implement and run deterministic VA-API encode validation.
32. [ ] Run repeated-job, idle, cold-boot, and suspend/resume stability gates.
33. [ ] Minimize the final patch series and keep hardware enablement opt-in until all gates pass.
34. [ ] Write `2026-08-26-bc250-vcn-bringup-results.md` with hashes and exact gate outcomes.
35. [ ] Mark older plans superseded or archived and retain measured reports as evidence.
36. [ ] Verify complete rollback to the stock kernel, stock cmdline, and stock USB-independent boot.

Explicitly deferred:

- Flashing unsigned or modified PSP/SEC_GASKET firmware.
- Searching for or extracting AMD private signing keys.
- Global `amdgpu.fw_load_type=0`.
- Live AMDGPU overlay replacement as an acceptance test.
- Brute-force SMN/MMIO scanning.
- Mode-2 or later hardware access before the trusted-transition and internal-oracle gates pass.
- Application integration such as Jellyfin/browser acceleration until VA-API decode and encode are stable.

## Open questions

Blocking before host VCN MMIO:

1. Which signed PSP/ABL function consumes SEC_GASKET type `0x24`, and what exact state transition commits and locks the selected group?
2. How is the requester/client identity for HWID 12 derived, and does the policy authorize x86 host MMIO, an internal PSP/SMU client, or both?
3. Which bounded internal state proves that the VCN route is open without performing a host BAR5 read?

Blocking before VCPU start:

4. Once MMIO is live, which VCN 2.0 register is the safest identity/readiness oracle on Cyan Skillfish, and what reset value is expected?
5. Does BC-250 VCN 2.0.3 execute `navi10_vcn.bin` unchanged after direct placement, or is a different compatible signed payload required? This is tested only after MMIO opens.

Non-blocking:

6. Keep `bc250_vcn_mode` or rename it to `bc250_vcn_stage` when staged hardware implementation begins. Default assumption: keep mode for `0/1`, add a separate experimental stage parameter for `2-6`.
7. Final package naming. Default assumption: retain `linux-cachyos-vcn-bc250` until upstreaming.

## Decision log

- The primary route is trusted SEC_GASKET executor reverse engineering followed by a reversible same-session activation experiment.
- The kernel probe package remains necessary diagnostic infrastructure but is not counted as hardware unlock progress.
- Power, clocks, firmware placement, raw HWID-12 replay, and VCN registration are proven prerequisites or diagnostics, not sufficient unlock conditions.
- The missing HWID-12 bank remains the leading differential, not a proven sole root cause.
- Runtime replay is rejected as the activation mechanism because it produced no host-MMIO change.
- Unsigned BIOS/PSP modification is rejected because signature validation and slot size both fail, and the risk is unnecessary before the loader contract is known.
- Private-key extraction is out of scope and unnecessary for the reversible research route.
- UEFI is retained as a same-session orchestrator, not assumed to execute before PSP policy finalization.
- Host MMIO is forbidden until an internal bridge-open proof is repeatable.
- Hardware bring-up is decomposed into identity, VCPU, decode, encode, and JPEG stages.
- AMDGPU media success is measured through the DRM render node and VA-API; `/dev/video*` is not required.
- Every live stage requires a preserved previous boot entry, cold-power recovery, and two repeatable successful boots before promotion.
- This document supersedes earlier forward plans while preserving their measured evidence.
