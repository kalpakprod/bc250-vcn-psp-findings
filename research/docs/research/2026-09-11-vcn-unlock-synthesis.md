# BC-250 VCN unlock synthesis (2026-09-11)

## 0. Action first

- Goal: unlock VCN 2.0.3 on operator-owned BC250-01. Stock restore is NOT requested by operator.
- Fact: 3 flashes give identical no-video (APCB-only, D3-B2 combined, policy-only stock-APCB).
- Next discriminating flash: D3-C signed-relocation mechanics test (valid signature, only directory repoint).
- Parallel no-flash path: TOS C2P runtime blob (0x100B/0x100C/0x1033) on stock OS + patched amdgpu kernel.

## 1. Sources reread (G1)

- `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md` (55,977 B; 5 lock layers; stage A/B/C recipe; signature scheme; D3 ladder).
- `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/10-runtime-unlock-recipe.md` (14,404 B; C2P channel, commands, blob recipe).
- `archives/imported/recon-evidence/legacy-tmp-bc250-recon/VCN-UNLOCK-CORRECT-CHAIN.md` (12,164 B; gates G0-G9, G5 NBIF/Fabric clamp = blocker).
- `archives/imported/recon-evidence/legacy-tmp-bc250-recon/VCN-EXPLOIT-SPEC.md` (3,310 B; Q3 0x98 ungated SMN write; dom6; FF reads).
- `archives/imported/recon-evidence/legacy-tmp-bc250-recon/vuln-1-gasket-runtime-reprogram.md` (4,755 B; SMU replay accepted, MMIO still FF).
- `archives/imported/recon-evidence/legacy-tmp-bc250-recon/vuln-2-unauthenticated-apcb-dfg.md` (3,328 B; APCB checksum-only gate).
- Worker reports: worker1 (diff/CoreUnlock/amdgpu), worker2 (corpus), worker3 (policy-sig bootfail), worker4 (runtime design).
- Fresh evidence: policy-only write/readback PASS 26/26; cold boot 2026-09-11T20:39+05:00 = no-video, same LEDs/fan.

## 2. Where VCN is killed (5 layers, observed vs inferred)

| Layer                  | State                                                               | Evidence class                                                                 |
| ---------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| L1 discovery/HW        | PRESENT, harvest=0 (VCN 2.0.3, bases 0x7800/0x7E00/0x02403000)      | observed-bytes (SPI @0x981A00 + live TMR blob)                                 |
| L2 amdgpu driver       | EMPTY case: `IP_VERSION(2,0,3)` -> break, no vcn block              | static-analysis (upstream source); patched kernel 1.92 installed, never booted |
| L3 PSP SEC_GASKET 0x24 | kill values: 0x03E810=0 (donor 6), DF windows shut, VCN bank absent | observed-bytes (Robin vs Cezanne diff, 158 differ)                             |
| L4 SMU dom6 power      | enable=0 off; no PowerUpVcn msg in SMU 11.8/PMFW 88.6.0             | static-analysis + prior live reads                                             |
| L5 VCN firmware        | absent; donor renoir_vcn.bin 405,952 B on host                      | observed-bytes (file present, never loaded on target)                          |

## 3. Why all 3 flashes give the same no-video

- H1 (main): PSP validates RSA-2048 tails over $PS1 payload. Relocated/modified carriers keep stale 0x100 tails -> digest mismatch -> silent PSP halt before x86 release. Explains identical LEDs/fan/no-video across D3-B2 and policy-only. Class: static-analysis + hardware behavior; PSP transform itself UNRESOLVED (offline verify never reproduced).
- H2 (APCB surprise): APCB-only 3-byte change also killed video, against historical "false-negative" expectation (boot OK, VCN dead). Either PSP-side APCB consumer rejects DFG without attestation, or DFG tokens break memory init. Class: hardware-observed, cause INCONCLUSIVE.
- Skipped discriminator: historical ladder prescribed 01 D3-C (SIGNED relocation, valid sig) -> 02 D3-B2 -> 03 D3-A. We flashed equivalents of 03 and 02 but never 01. D3-C isolates directory/relocation mechanics from the signature variable.

## 4. Holes / exploits inventory (honest status)

1. E1 SMU Q3 msg 0x98 smn_write32 (VULN-1/EXPLOIT-SPEC): ungated privileged SMN write, field-proven PoC (56 Bank-12 writes accepted in readback) BUT x86 MMIO stayed 0xFFFFFFFF. Status: replay works, unclamp FAILED at aperture layer.
2. E2 APCB DFG checksum-only gate (VULN-002, no signature): attractive (additive checksum, recalculable) BUT our APCB-only flash produced no-video, so "safe control" claim is DISPROVED on current board. Status: boot-unsafe, cause open.
3. E3 TOS C2P runtime blob (doc 10): x86 -> C2P/SOS mailbox -> TOS dispatcher fn@0xBA98; 0x100B token (per-boot, read at buf+0x100), 0x100C blob load via DMA descriptor, 0x1033 apply via svc 0x7c. Blob binds by TOKEN (0x40 header), never touches SPI, RSA tail not involved. Tool `tools/psp-policy/c2_blob_builder.py` exists. Status: statically mapped, NEVER executed on target. Best no-flash hole.
4. E4 Bc250CoreUnlockDxe (GUID 2F3D426D-...): reads SMN 0x0115A870, Setup guard, sends Q3 0x98, warm reset. Present in dump (12,288 B). Status: static only, execution UNRUN.
5. E5 amdgpu kernel patch (mode1/probe kernels, vcn_v2_0.c, `amdgpu.bc250_vcn_mode=1`): fills empty case. Status: built, installed, never booted on target. Required even after hardware unclamp.

## 5. Sequence forward (ranked, one variable each)

1. S1 D3-C signed relocation (FLASH): original signed gasket byte-identical at 0x9E0000 + repoint 0x24 + Fletcher32. Valid sig. Boots -> relocation OK, signature is the killer. No-video -> even directory touch halts PSP; stop PSP-touch path entirely.
2. S2 C2P runtime probe (NO FLASH, stock OS): 0x100B token -> build blob (groups 0x201/0x210 per doc 10) -> 0x100C -> 0x1033 -> read mmUVD_VERSION 0x78CA. PASS signal != 0xFFFFFFFF. Abort on SMU wedge (never send msg 0x2A).
3. S3 Q3 0x98 ordered unclamp replay (RUNTIME, no flash): single reversible SMN store, readback, then 56-write Bank-12 only if step 1 readback accepts. Signal: aperture read change.
4. S4 Patched kernel boot (NO FLASH): boot 1.92 with `amdgpu.bc250_vcn_mode=1` + renoir_vcn.bin staged. Needed for V2 (UVD_VERSION) and beyond.
5. S5 In-place single-value $PS1 edit (FLASH, only if S1 boots): one u32 in stock footprint, no relocation/size change. Tests whether PSP tolerates any payload delta at all.

## 6. What is NOT claimed

- No "safe flash" claim for any PSP/APCB variant after 3 no-video results.
- No signature bypass proven. Offline RSA verify never reproduced (11 keys x transforms x spans x hashes = empty).
- No VCN ON, no ring, no codec, no stability evidence exists on target.

## 7. Evidence produced by this synthesis

- 4 worker reports in `docs/research/2026-09-11-worker*.md` (w1 6,325 B; w2 10,497 B; w3 8,241 B; w4 9,662 B).
- No firmware built, no hardware touched by this report.
