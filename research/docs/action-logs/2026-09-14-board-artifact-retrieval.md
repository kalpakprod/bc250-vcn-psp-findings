# BC-250 board artifact retrieval

## Intent

- Timestamp: 2026-09-14T16:41+05:00.
- Actor: root Codex agent; no delegation. Root keeps exact-board collection and offline reconciliation because the files are small and directly gate current conclusions.
- Operator powered `BC250-01`; initial SSH returned `No route to host`, then ICMP became reachable and SSH succeeded.
- Live identity: host `cachyos`, boot ID `1bb84c62-17f7-4e08-af55-0b61ec8c8c37`, kernel `7.2.0-1.92-cachyos-vcn-bc250`, cmdline includes `amdgpu.bc250_vcn_mode=1`, system state `running`, GPU `1002:13fe`.
- Scope: retrieve only the seven previously named September-12 stage2b/stage4/stage5 source/output files and the exact running compressed `amdgpu.ko.zst`; no command execution from retrieved files, no hardware register access, no mailbox call, no reboot, and no firmware write.
- Secret preflight: remote name-only sensitive-pattern scan over the seven files returned no matches. Do not copy SSH configuration, credentials, private keys, shell histories, unrelated exports, or broad directories.
- Remote source files and SHA-256 values were enumerated before transfer. Expected stage4 source hash `821635e2c0f80a34f03a2a82902d1f3b65c5ec451110ec602c01b1da0d883227` matches the contemporaneous journal.
- Exact running module: `/lib/modules/7.2.0-1.92-cachyos-vcn-bc250/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko.zst`, size 5,862,198 bytes, SHA-256 `7424913c4864079865e8f792a54edc9c3d6a1bb1997ca0a916072e988d7dea40`.
- Destination: new directory `evidence/runtime/20260914-board-retrieval/`. Preserve remote basenames, source paths, sizes and hashes in a manifest. Inspect and sanitize outputs before citing them; originals on the board remain untouched.
- Expected effect: close the evidence-retrieval blocker and permit offline verification of the exact observer addresses, stage sequencing, and installed module provenance.
- Rollback: generated local copies can be quarantined if validation fails; never delete or modify the remote originals. Retain this append-only record.

## Result

- PASS: mode1 became reachable after the initial transient `No route to host`. Live identity: host `cachyos`, boot ID `1bb84c62-17f7-4e08-af55-0b61ec8c8c37`, kernel `7.2.0-1.92-cachyos-vcn-bc250`, cmdline `amdgpu.bc250_vcn_mode=1`, system `running`, GPU `1002:13fe`.
- PASS: retrieved exactly the seven requested September-12 files and the running compressed `amdgpu.ko.zst`; local sizes and SHA-256 values match the remote pre-transfer inventory. Manifest: `evidence/runtime/20260914-board-retrieval/manifest.json`.
- PASS: stage4 source SHA-256 equals the contemporaneously expected `821635e2c0f80a34f03a2a82902d1f3b65c5ec451110ec602c01b1da0d883227`.
- Source/output reconciliation: both stage2b results record all 59 writes accepted, bank control readback `0x0900C234=1`, and `alive_final=true`. Stage5 records all 15 writes accepted, commit readback `1`, and ten bounded configuration reads. These are historical hardware outputs now source-verifiable; they do not prove VCN visibility.
- G7 carryover confirmed: `stage4_arbiter.py` uses the obsolete base0 `0x7800` plus `0xBC/BD/C9/CA` labels. Its five all-ones results remain measurements at numeric byte offsets `0x1E2F0/0x1E2F4/0x1E004/0x1E324/0x1E328`, not proof of the printed VCN2 register names.
- Exact module provenance: compressed SHA-256 `7424913c4864079865e8f792a54edc9c3d6a1bb1997ca0a916072e988d7dea40`; decompressed SHA-256 `7d6606ba80be79e49bb703f29b79a22fcc4b96d8c51b7799bf694f4d417d1ebf`; build ID `ca6bb73e0c93d32f1c80552e5093e7a766a3c924`; vermagic matches the running kernel. Static strings confirm custom `bc250_vcn_mode`, `vcn_v2_0_probe`, and `green_sardine_vcn`/`renoir_vcn` declarations.
- No retrieved code was executed. No mailbox, SMN, DF, MMIO, firmware, boot configuration, or hardware state was modified. Remote originals remain untouched.

## Exact-module function audit intent

- Use only the locally copied/decompressed exact module. Preserve bounded `llvm-objdump` disassembly for `amdgpu_vcn_fw_is_psp`, `vcn_v2_0_probe_hw_init`, `vcn_v2_0_hw_init`, `vcn_v2_0_start`, and `amdgpu_discovery_set_mm_ip_blocks` under the retrieval evidence directory.
- Compare observable control flow/constants/strings against retained `0011-bc250-vcn-probe-mode.patch`; do not assume full source equivalence from strings or symbol names.
- Acceptance: exact module SHA/build ID retained; bounded functions decode; mode-selection and probe no-MMIO behavior directly visible; identify the first real VCN initializer call chain as far as static binary permits. No board operation or module execution.

## Exact-module function audit result

- Preserved bounded disassembly artifacts for discovery selection, `amdgpu_vcn_fw_is_psp`, probe `hw_init`, real `hw_init`, and `vcn_v2_0_start`. No module code was loaded or executed by this audit.
- Exact discovery code matches the retained 0011 behavior at the binary level: device `0x13FE`; mode `1` selects `vcn_v2_0_probe_ip_block`; mode `2` selects `vcn_v2_0_ip_block` and the JPEG branch; out-of-range mode follows the warning/disable path.
- Exact `amdgpu_vcn_fw_is_psp` tests Cyan Skillfish2 flag, device `0x13FE`, packed IP version `0x02000300`, and mode in `{1,2}` before returning false; otherwise it tests global firmware load type. This corroborates direct VCN firmware placement in the installed modes.
- Probe `hw_init` is only a log call followed by return zero. It contains no VCN MMIO access, matching the successful mode1 behavior.
- G7 refinement: real `vcn_v2_0_hw_init` itself starts with the NBIO `vcn_doorbell_range` callback and later ring tests; it does not call `vcn_v2_0_start`. `vcn_v2_0_start` is a separate path reached via the power-gating state callback and begins with `amdgpu_dpm_enable_vcn`, then PGFSM/static-power-gating register work in the non-DPG branch. Therefore the old statement that the controlled mode2 wedge was proven at the first VCN MMIO instruction inside `vcn_v2_0_hw_init` is too specific. The last log only bounds the hang to the real VCN initialization phase; without instruction tracing it may be in power-gating/start, doorbell setup, or the first ring access.
- The exact installed module is consistent with retained patch 0011 for the audited custom behavior, but full source equivalence is not claimed. First failing instruction remains INCONCLUSIVE.
- Manifest validation PASS: eight retrieved files exist with exact sizes/hashes; manifest SHA-256 `88fac765ad8a49b0f31bc77220cb3c70473143949fc8a45f123240f7e1aaecba`. `git diff --check` PASS.
