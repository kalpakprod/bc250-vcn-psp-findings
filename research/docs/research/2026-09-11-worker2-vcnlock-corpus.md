# BC-250 Worker-2 Historical VCN-lock Corpus Review

- **Date**: 2026-09-11
- **Author**: Worker-2 (BC-250 historical VCN-lock corpus review)
- **Scope**: Systematic extraction and verification of VCN disable mechanisms, evidence classification, historical unlock methods, contradictions, and reuse paths from local historical corpus (`archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md` and `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/`).

---

## 1. Executive Summary & Action First

- **Action**: Review historical VCN-lock research artifacts without mutating local firmware or hardware state; produce a rigorous corpus review structured into Hypotheses (H), Evidence (E), Quirks/Contradictions (Q), Verdicts (V), and Reuse (R).
- **Key Finding**: VCN disablement on AMD BC-250 (Cyan Skillfish 13FE) is multi-layered across Linux kernel (skipped `IP_VERSION(2,0,3)`), PSP SEC_GASKET (`type 0x24`), TOS_SECURITY_POLICY (`type 0x45`), APCB Data Fabric Gating (`DFG`), and SMU/PMFW power policies. Static modification of signed `$PS1` containers (`0x24`/`0x45`) is rejected by the RSA-2048 PSP bootloader verification path, making unsigned APCB DFG modification or runtime mailbox injection the only viable paths.

---

## H. Hypotheses (Stated VCN-Disable Mechanisms)

### H1. Linux Driver Blacklist / Skip Case

- **Description**: The upstream Linux `amdgpu` driver intentionally skips initialization for `cyan_skillfish2` (`IP_VERSION(2, 0, 3)`), leaving VCN blocks unmapped and uninitialized.
- **File Path & Line**: `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md`, lines 47–55; `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/09-vcn-bios-unlock-plan.md`.
- **Quote**: `case IP_VERSION(2, 0, 3): break; /* ← VCN 2.0.3 (cyan_skillfish2) СОЗНАТЕЛЬНО ПРОПУЩЕН */`

### H2. PSP SEC_GASKET Hardware Firewall & Clamping

- **Description**: The PSP firmware applies a cryptographic security gasket (`type 0x24`) during early boot, clamping Data Fabric access, setting NBIF apertures, and explicitly zeroing `0x03E810` (VCN_SEG enable) to lock out VCN MMIO (`0x7800`, `0x7E00`, `0x02403000`).
- **File Path & Line**: `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md`, lines 59–95 (`Слой 3`), and `docs/01-psp-policy-chain.md`.
- **Quote**: `| 0x03E810 (0x210) | 0x00000000 | 0x00000006 | VCN_SEG enable — явный ноль = главный kill |`

### H3. TOS Security Policy Mirror (`type 0x45`)

- **Description**: A secondary mirrored policy container (`type 0x45`, `TOS_SECURITY_POLICY`) reinforces the security gasket configuration to prevent single-blob overrides.
- **File Path & Line**: `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/03-d3-patch-status.md` and `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/roadmap_A_results.md`.
- **Quote**: `D3-B2: D3 плюс зеркало TOS_SECURITY_POLICY по адресу 0x9E4000 со следующими изменениями обоих блобов`

### H4. APCB Data Fabric Gating (DFG) Limitations

- **Description**: The APCB DFG token table restricts DMA routing and memory address windows for IP blocks, limiting VCN memory coherence with GDDR6.
- **File Path & Line**: `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/source-docs/vuln-2-unauthenticated-apcb-dfg.md` and `VCN-LOCK-MECHANISM.md`, §7.
- **Quote**: `DFG@0xab10f4 ... DFG wildcard (0x001FFF00 → 0x007FFF00)`

### H5. SMU Power Domain Gating (Dom6 / Power-Gating)

- **Description**: The PMFW (SMU firmware `88.6.0`) keeps the VCN power domain (dom6) gated off, causing immediate bus wedges (reads returning `0xFFFFFFFF` or hanging the interconnect) if MMIO is accessed while powered down.
- **File Path & Line**: `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md`, §1 & §4; `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/source-docs/VCN-START-SAFE.md`.
- **Quote**: `на 2026-08-29 полный реплей гаскета прочитал VCN-MMIO пока домен был power-gated -> bus wedge, плата мертва до холодного рестарта`

---

## E. Evidence (Provenance, Hashes, and Quotations)

| Item                           | File Path                                                                                  | SHA-256 / Size                                                                | Evidence Class                       | Quote / Description                                                                                                                                                                         |
| ------------------------------ | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **VCN-LOCK-MECHANISM.md**      | `archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/VCN-LOCK-MECHANISM.md`     | `ef3a7bb5234569dfce8240f6fd02ddcebf395ab44f4bc1cd551b969f018e7321` (55,977 B) | `observed-bytes` / `static-analysis` | Complete teardown of PSP directory, gasket groups, differential with Cezanne donor, and verification chains.                                                                                |
| **08-verification-chain.md**   | `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/08-verification-chain.md`   | `2cf3b5ee74f8b17d13994413d867e90267aa40d52857813c9b6acaa23ac198fa`            | `static-analysis`                    | Proves that `$PS1` blobs `0x24` and `0x45` carry an exact `0x100`-byte RSA-2048 signature (`kid 96EA`) verified by PSP supervisor (`fn@0xd1fc`), making static ROM modifications fail boot. |
| **09-vcn-bios-unlock-plan.md** | `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/09-vcn-bios-unlock-plan.md` | `ef12c9b61b68c566527453cf21d80b0bb73abf6822cd257d225e1825a5dc88b3`            | `static-analysis`                    | Architectural plan for DXE runtime mailbox injection (`VcnUnlockDxe.efi`) avoiding static PSP signature breakage.                                                                           |
| **03-d3-patch-status.md**      | `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/03-d3-patch-status.md`      | `cf483c39d6cf2e30c5130cca9c56cb0145a143b338f029caecf28548ed52e074`            | `static-analysis`                    | Analysis of D3, D3-C, and D3-B2 patch sets, risk evaluation, and warning against flashing unsigned `$PS1` blobs.                                                                            |
| **01-psp-policy-chain.md**     | `archives/imported/historical-bios-repo/legacy-bc250-bios/docs/01-psp-policy-chain.md`     | `6b8cc1e1bf5b0ea82226e41df727da0c3b4dd75929c664c61bbf8df8a75b3037`            | `static-analysis`                    | Detailed trace of dispatchers (`fn@0xBA98`), interpreters (`fn@0x2178`, `fn@0xFEAC`), and sequencer (`fn@0x20D4`).                                                                          |

---

## Q. Quirks & Contradictions (Document Discrepancies)

1. **Signature Tail Size & Interpretation**:
   - _Early assumption_: Tail of `$PS1` carriers was considered too small for RSA (`0x100` bytes).
   - _Correction (`08-verification-chain.md`)_: `0x100` bytes (256 bytes) is precisely the length of an RSA-2048 signature. The signature covers the envelope and payload up to the tail.
2. **Relocated `$PS1` Carriers ($PSP type 0x24 / 0x45 at `0x9E0000` / `0x9E4000`)**:
   - _Doc claim (D3-B2)_: Moving SEC_GASKET and TOS policy to unused high regions (`0x9E0000`/`0x9E4000`) and repointing the PSP directory with recalculated Fletcher32 allows loading.
   - _Contradiction_: While the PSP directory Fletcher32 passes and the catalog entry is updated, the PSP bootloader's cryptographic verification (`fn@0xd1fc`) checks the RSA-2048 signature against the trusted root (`kid 96EA`), rejecting any modified payload regardless of its ROM location.
3. **APCB Checksum Location**:
   - _Old imported claim_: Checksum is located at APCB offset `+0x0C`.
   - _Corrected local memory (`firmware-audit.md`)_: APCB v2 instance stamp is at `+0x0C=0x220E`, and the 8-bit/32-bit checksum is at `+0x10` (`0xF2` in stock). Mixing up offset `+0x0C` breaks APCB parsing.

---

## V. Verdicts (Historical Unlock Methods & Outcomes)

| Method                                                                                 | Stated Evidence Class                                   | Stated Mechanism                                                                                                                                              | Boot / Hardware Outcome                                                                                                                              | Reason for Success / Failure                                                                                                                                 |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **D3-B2 / D3-C / D3** (Unsigned Gasket + Policy + APCB)                                | `static-analysis`                                       | Static replacement of SEC_GASKET (`0x24`) and TOS_POLICY (`0x45`) with Cezanne donor values, relocated to `0x9E0000`/`0x9E4000` with repointed PSP directory. | **FAIL (Rejected / Non-bootable / No-display)**                                                                                                      | PSP bootloader (`fn@0xd1fc`) rejects the modified RSA-2048 signature on cold boot. Statically verified in local corpus and hardware-tested.                  |
| **CoreUnlock DXE** (`Bc250CoreUnlockDxe.efi`)                                          | `static-analysis` / `observed-bytes`                    | DXE module checking setup variable guard (`Setup+0x1C4`) and issuing SMN/Q3 message `0x98` for core unlocking / SMU signaling.                                | **INCONCLUSIVE / UNRUN** (Code present in dump `2.bin`, but Setup variable gate `0x157C0` vs `0x11940` prevents execution).                          | Bypasses PSP signature by operating in UEFI DXE phase, but requires correct setup state and SMU cooperation.                                                 |
| **APCB DFG** (APCB-only wildcard `0x001FFF00 → 0x007FFF00`)                            | `observed-bytes` / `hardware-verified` (write/readback) | Modifying unauthenticated APCB DFG token words in SPI ROM (checksum at `+0x10`).                                                                              | **INCONCLUSIVE / NO DISPLAY** (Flashed on hardware; readback verified; produced green/blue indicators + red USB/Ethernet light but no video output). | APCB DFG alone opens Data Fabric DMA windows, but does not un-gate VCN power domain or supply missing firmware/driver support without SMU and kernel action. |
| **SMU Mailbox / Runtime Injection** (`Command 0x100C` / `0x1033`)                      | `static-analysis`                                       | Runtimer-oriented two-step injection of policy blobs via C2P mailbox (`Command 0x10C` session token + `0x1033` apply).                                        | **UNRUN**                                                                                                                                            | Requires host-side execution capability with access to MP0 C2PMSG registers during runtime.                                                                  |
| **Donor-Port / Native Kernel** (`linux-cachyos-vcn-bc250` + `amdgpu.bc250_vcn_mode=1`) | `emulated-or-host-tested` / `observed-bytes`            | Filling the skipped `IP_VERSION(2,0,3)` case in upstream amdgpu driver and passing module parameters.                                                         | **TIMED OUT / UNVERIFIED** (Historical ring tests timed out with `-110` when attempted without prior hardware un-gating).                            | Necessary host-side software component, but insufficient on its own while hardware/PSP domain remains clamped.                                               |

---

## R. Reuse (Actionable Takeaways for Ongoing Work)

1. **Never attempt static modification of signed PSP `$PS1` blobs (`0x24`, `0x45`)**: They are protected by RSA-2048 signatures checked by `fn@0xd1fc`. Any static patch to their bodies or relocation without private keys will be rejected by PSP.
2. **Focus VCN hardware attempts on unauthenticated surfaces**: APCB DFG token modification (checksum at `+0x10`) is structurally sound and unauthenticated, but requires companion SMU power un-gating (Dom6 / power domain) and kernel driver support (`amdgpu.bc250_vcn_mode=1`).
3. **Preserve exact evidence separation**: Maintain strict boundaries between observed bytes, static analysis, emulated results, and hardware-verified readbacks. Do not repeat unverified success claims.

---

_(End of report)_
