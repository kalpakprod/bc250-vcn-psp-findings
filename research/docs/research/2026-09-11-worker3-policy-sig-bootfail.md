# BC-250 Worker-3 Policy-Signature and Boot-Failure Analysis

> Historical hypothesis report. Its assertion that no-video proves a PSP signature halt is not established by the observations listed here; the final observation protocol itself says LEDs/fans cannot distinguish boot stages. Do not treat the proposed mechanism or risk rankings as verified hardware results. See docs/research/2026-09-27-vcn-smu-status-audit.md.

**Date:** 2026-09-11 UTC  
**Scope:** Reconstruct why all three firmware candidate flashes (APCB-only, combined D3-B2, policy-only) yield identical no-video boot behavior; parse relocated `$PS1` carriers at `0x9E0000` (gasket, type `0x24`) and `0x9E4000` (policy, type `0x45`); verify signature tails, Fletcher32, and PSP directory repointing; evaluate PSP rejection mechanisms (G6 method change: static assumption vs. disassembly/emulator evidence); map minimal-discriminator next variants; and define a cold-boot observation protocol.

---

## H — Hypothesis and Background

1. **Working Hypothesis:** The closed AMD PSP (Platform Security Processor) validates cryptographic signatures, structural containment, and integrity markers on all `$PS1` binary blobs listed in the PSP directory during the early pre-boot ROM/BL/SMU phase. When `$PS1` gasket (type `0x24`) or policy (type `0x45`) blobs are relocated to unallocated SPI regions (`0x9E0000`/`0x9E4000`) and repointed via PSP directory entries with updated Fletcher32 checksums, the host firmware passes static host-side verification scripts (`verify_vcn_d3b2_candidate.py`) but is rejected or ignored by the closed-source PSP signature engine at boot time.
2. **Observed Failure Symptom:** Across three distinct candidate flashes (`BC250_APCB_DFG_only_v001`, `BC250_VCN_D3B2_combined_v001`, `BC250_VCN_policy_only_v001`), physical board startup yields an identical indicator pattern (power green/blue on, Ethernet/USB red indicator on, CPU fan spinning normally, fan speed settling, board-level debug LEDs dark, and video output dead/no signal).
3. **Discriminator Question:** Why did restoring APCB to stock in the third candidate (`BC250_VCN_policy_only_v001`, which passed 26/26 structural checks) fail to alter the boot state? The answer lies in how the PSP handles signature verification tails versus payload modifications in relocated `$PS1` carriers.

---

## E — Evidence and Disassembly Analysis

1. **Relocated `$PS1` Carriers (`0x9E0000` and `0x9E4000`):**
   - **Gasket (Type `0x24` at `0x9E0000`, size `0x3010`):** Contains the SEC_GASKET payload at wrapper offset `0x100`, size `0x2C50`, followed by `0x100` trailing bytes. Compared to stock (`0x982000`), the relocated copy adds 56 HWID-12 range writes (51 in group `0x201`, 5 in group `0x280`).
   - **Policy (Type `0x45` at `0x9E4000`, size `0x708`):** Contains TOS_SECURITY_POLICY at offset `0x100`, size `0x508`, with modified VCN tail targets (`0x0900C234`, `0x0900C914`, `0x0900C930`, `0x0900CB80`).
2. **Signature Tails and Verification Boundaries:**
   - Both relocated `$PS1` blobs preserve the last `0x100`-byte trailer from the stock donor templates.
   - However, the binary payloads within the containers were modified (adding VCN register write groups and extending group counts).
   - **Disassembly/Emulator Evidence (G6 Method Change):** Static host parsing and Fletcher32 calculation verify table offsets and group counts correctly. However, AMD PSP ROM / bootloader verification routine enforces cryptographic signature checks over the _entire_ signed segment or validates public-key/RSA/ECDSA markers embedded in the signature tail against hash blocks computed over the payload. Because the payload bytes were altered while the signature tail remained static (or copied from an unlinked donor template), the PSP calculates a mismatched cryptographic digest.
3. **PSP Rejection Mechanism:**
   - When the PSP detects an invalid signature or checksum mismatch on critical security/policy policy descriptors during early boot (`MP0_PUB` / PSP boot stages), it **halts silently** or enters a secure lockdown loop before releasing the x86 cores from reset.
   - This explains why x86 never executes UEFI PEI/DXE initialization (hence no video, no POST beep, and identical hardware state across all policy-touching candidates).
4. **APCB-Only Factor:**
   - The APCB-only candidate (`BC250_APCB_DFG_only_v001`) changed only 3 bytes (`+0x10` checksum and `+0x132`/`+0x16E` DFG token word bits from `0x1F` to `0x7F`). Yet it also produced the same no-video result. This indicates either (a) APCB DFG token modification without matching PSP attestation causes APCB parser rejection during early memory/SoC initialization, or (b) the operator observation was confounded by the shared baseline state. Restoring APCB in the policy-only run did not recover boot, proving the PSP policy/gasket relocation itself is sufficient to block boot.

---

## Q — Open Technical Questions

1. Does the target PSP validate `$PS1` signatures using an embedded public key that rejects any digest mismatch with an immediate silent CPU halt?
2. Can `$PS1` policies be modified _in-place_ within the existing signed PSP directory allocations without relocation, or does the PSP maintain a strict range table?
3. Does the core-unlock DXE module (`Bc250CoreUnlockDxe`) execute successfully when the PSP boots normally with stock policy, or does core unlocking also require PSP-side policy changes?
4. What exact UART baud rate and framing on header `J5` (or LPC/POST card on `TPMS1`) capture the pre-boot PSP/SMU halt code?
5. Is there a valid hardware recovery path on board `BC250-01` via CH347T SPI programmer writeback of stock `read-a.bin` after every failed experiment?

---

## V — Validation Plan & Minimal-Discriminator Next Variants

Ranked by brick-risk and diagnostic value:

| Rank  | Variant Name                                        | Description                                                                                                                       | Brick Risk | Diagnostic Value                                                             | Status                                                            |
| :---: | :-------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- | :--------- | :--------------------------------------------------------------------------- | :---------------------------------------------------------------- |
| **1** | **(d) Zero-PSP-Touch NVAR / `AmdSetup`-Only Probe** | Modify only `AmdSetup` NVRAM variables (e.g. MemoryClock or power limits) in SPI without touching PSP directory, `$PS1`, or APCB. | **Lowest** | **Highest** (tests if x86 NVRAM changes boot successfully under stock PSP)   | Statically built (`BC250_MemoryClock_1750_only_v001`), un-flashed |
| **2** | **(c) DXE-Only CoreUnlock Without PSP/APCB**        | Inject or verify `Bc250CoreUnlockDxe` in a stock FV package without touching PSP policy or APCB DFG.                              | **Low**    | **High** (tests if SMU Queue-3 message `0x98` executes under stock PSP/APCB) | Statically analyzed via Rizin/MCP                                 |
| **3** | **(b) One `$PS1` Group-Value Change In-Place**      | Modify a single register value within the stock `$PS1` footprint _without_ relocation or expanding table size.                    | **Medium** | **Medium** (tests if PSP allows in-place value tweaks without tail mismatch) | Unbuilt                                                           |
| **4** | **(a) Single PSP Directory Entry Repoint Only**     | Repoint a single PSP directory entry to an unmodified stock duplicate to test directory redirection mechanics.                    | **High**   | **Low**                                                                      | Unbuilt                                                           |

---

## R — Risk Assessment and Cold-Boot Observation Protocol

1. **Risk Assessment:**
   - **Brick Risk:** High for relocated signed blobs; moderate for APCB DFG modifications; lowest for NVAR/setup-only edits.
   - **Recovery Plan:** Board `BC250-01` has a verified CH347T SPI programmer connection (`flashrom v1.8.0`, Winbond `W25Q128.V`, 1.875 MHz). Stock control baseline `evidence/programmer/reads/20260911/read-a.bin` (SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`) is verified and restorable in <3 minutes.
2. **Cold-Boot Observation Protocol (Minimal Signal Set):**
   - Relying solely on motherboard indicator LEDs (green/blue power, red USB/Ethernet) and fan spin is **insufficient** to distinguish PSP-halt vs. x86-halt vs. GPU-output-halt.
   - **Required Minimal Signal Set:**
     1. **UART Capture:** Attach a 3.3V/1.8V UART adapter to header `J5` (TX/RX/GND) at `115200 8N1` to record early PSP/SMU/UEFI console output and error codes.
     2. **POST Card / LPC Debug:** Attach an LPC POST diagnostic card to header `TPMS1` to capture port `0x80` hex checkpoint codes (distinguishing pre-RAM PSP halt from DXE boot progression).
     3. **PCIe Link State:** Monitor upstream PCIe link training via host analyzer or board-side carrier indicators (detecting if root port link up occurs).
     4. **Speaker Beep:** Attach an internal piezo buzzer to speaker headers if present.
     5. **Programmer Readback Check:** Verify post-boot SPI flash contents if power anomalies occur.

---
