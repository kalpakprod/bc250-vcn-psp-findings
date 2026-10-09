# Public-source follow-up: no address-to-clock mapping for SMN 0x0116D150/174

Date: 2026-09-21 (Asia/Almaty, UTC+05:00)  
Owner: /root/clock_observability  
Scope: maximum three primary source files; exact SMN/address-block and clock-generator semantics only.

## Conclusion

**Bounded source gap; no exact semantic match found.** The newest completed exact-Robin-5 report maps dynamic domain ID 0x18, internal Group 6 to SMN program 0x0116D150 and poll 0x0116D174, but says physical identity is unresolved. I checked three public AMD/Linux/coreboot source files across two independent source families. None names either address (or 0x6D150/0x6D174 / low-offset forms) as an MCLK/UCLK/FCLK/DF/UMC/clock-generator register, and none binds domain 0x18 to a physical clock tree.

This is not proof that a proprietary, computed, or undocumented register dictionary does not exist. It is a bounded negative limited to the cited sources. The next missing source is an address-bearing AMD/AGESA/SMN register/domain reference for this exact Cezanne/Ariel/Skillfish SMU generation that defines these two addresses, their field/read-program semantics, and the Group-6/domain-ID mapping.

## Bound target and newest completed SMU result

- CLV: /home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin, 16,777,216 bytes, SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- Latest report: /home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smu-domain18-identity.md.
- Latest machine result: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smu-domain18-identity/domain18-identity-result.json, SHA-256 f4a005400dba428ff8ba8f782d67bfa608c9e5fc714c5771075c48d6467e5cbe.
- The completed result says Queue 3 message 0x1D, selector 11, dynamic ID 0x18, internal Group 6; descriptor 0xFA48, program pointer cell 0xFA5C, raw program offset 0x6D150, SMN program 0x0116D150, poll 0x0116D174. Its verdict is INTERNAL_GROUP6_ONLY; PHYSICAL_CLOCK_IDENTITY_UNRESOLVED.
- The operator’s CLV request remains AmdSetup+0x316=0x24 at ROM 0x7E5 (IFR label 1800MHz), stored request only. No ROM or configuration bytes were written.

I did not rerun the selector’s Ghidra slice, firmware disassembly, or the earlier local-header test. The result above is read as already-completed input.

## Agent Reach routing and bounded search status

agent-reach doctor --json ran before public-source search. Sanitized routing facts: Jina Reader is active for general web reads; Exa search is unconfigured; GitHub CLI is detected but has active_backend=null because Doctor did not live-probe it. I did not run gh auth status, use an authenticated GitHub session, install/configure a backend, or inspect credential values. Jina Reader was the only retrieval route used.

Exact-address search results (retrieval date 2026-09-21):

| Public index/page                       | Request                 | Observed result                                             |
| --------------------------------------- | ----------------------- | ----------------------------------------------------------- |
| grep.app API via Jina Reader            | 116D150                 | HTTP 429, Vercel Security Checkpoint                        |
| DuckDuckGo HTML via Jina Reader         | "0x116D150" AMD SMN     | No results found                                            |
| DuckDuckGo HTML via Jina Reader         | "6D150" "SMN" AMD clock | No results found                                            |
| GitHub code search page via Jina Reader | 0x116D150               | Sign-in required to view code results; no sign-in attempted |

These are retrieval/index outcomes, not evidence that the address is absent from all public code.

## Primary source files checked

### 1. coreboot Cezanne Data Fabric header — pinned source, no clock mapping

- Repository: coreboot/coreboot, local imported .git HEAD b7931d1afacdc6666b4812305a14ed3deb431201, origin https://github.com/coreboot/coreboot.git.
- Public URL read with Agent Reach Jina Reader: https://raw.githubusercontent.com/coreboot/coreboot/b7931d1afacdc6666b4812305a14ed3deb431201/src/soc/amd/cezanne/include/soc/data_fabric.h.
- License: file declares SPDX-License-Identifier: GPL-2.0-only.
- Local file hash: bd438484a85441daf8eb4bfd1a89b102c3638e16317e766dd826384f46689af3.
- Jina response hash: fdf8b9a6a6b45e75fd4dd8b2031708ad8baffdec96005f9885c923d830afc460; normalized body hash 5d4600e473e5c6007df06b239925a2c9856f82e3d41f9ac3a15415ef59e7430a. The returned body equals the local commit-pinned file after newline normalization.
- Relevant definitions are generic DF configuration access identifiers such as DF_PCI_CFG_MAP0=DF_REG_ID(0,0xA0), DF_IO_BASE0=DF_REG_ID(0,0xC0), DF_MMIO_BASE0=DF_REG_ID(0,0x200), and DF_FICAA_BIOS/DF_FICAD_LO/DF_FICAD_HI. It contains no 0x0116D150/0x0116D174 address, no MCLK/UCLK/FCLK/UMC clock label, and no mapping from Group 6/domain 0x18 to a clock tree. These are DF configuration-register identifiers, not a semantic match for the PMFW-derived SMN pair.

### 2–3. upstream Linux v6.8 AMD source — exact-address checks only

Two version-pinned raw source files were read via Jina Reader (same Linux repository/version, one independent source family):

1. https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/gpu/drm/amd/include/asic_reg/gc/gc_10_1_0_offset.h  
   Jina response: 1,198,521 bytes, SHA-256 0834a1a258b52935e37d56fea479fa62ce2c845c7a76a93c8efad5c3b886e8d2; normalized-body hash 59b5ae6dad3f457ef7492ae8d9d773ca72db7b940149ae35ecad4f2e114b0593. Exact and base-stripped target-address match count: 0. The local imported header has hash a0ad8bffb3c07ec3824d306aff49c77bc40057f8760aec7a76ee58a60cc8e6a2 and does not normalize byte-for-byte to this v6.8 retrieval; the two artifacts are kept distinct.
2. https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/gpu/drm/amd/amdgpu/gfx_v10_0.c  
   Jina response: 438,169 bytes, SHA-256 4bd9bb4a4738817158d0a907d304bd9ac955a6631b54746a0b93d3ec904c42fb. Exact target-address match count: 0. No other clock/telemetry semantics from this file are repeated or adopted in this task.

The GC header is a GC MMIO-offset definition source; it does not name the PMFW-derived Group-6 SMN pair. The Linux files contain AMD’s permissive license notice. No external source file was installed, copied into project source, or modified.

## Verification and bounded result

The local verification consumes the completed smu-domain18-identity JSON, validates its exact address/group identity, checks the pinned coreboot source commit/hash and the cached Jina bodies, then tests the specified exact address forms in the three source bodies. It is not a full public-code census and does not reinterpret the PMFW disassembly.

Command actually executed:

    python3 -B evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/verify_public_source_gap.py

Observed literal stdout:

    {"checks": {"failed": 0, "passed": 16, "total": 16}, "latest_result": "domain18-identity-result.json", "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/public-source-gap-result.json", "physical_clock_identity": "unresolved", "poll": "0x0116D174", "program": "0x0116D150", "source_families": 2, "source_files": 3, "source_literal_hits": 0, "status": "PASS", "verdict": "bounded-public-source-gap"}

- Exit status: 0; stderr: empty (0 bytes).
- 16/16 checks passed. This validates the provenance/address lookup, not any hardware behavior.
- No exact semantics found. No other source family was searched after the two independent code families and the bounded address-index attempts.
- No hardware, network write, credentials, install, sysfs, mailbox, register, ROM, firmware, or NVRAM operation occurred.

## Exact missing source

An address-specific public AMD/AGESA source remains missing: the Cezanne/Ariel/Skillfish SMN/PMFW domain or register dictionary that defines 0x0116D150 and 0x0116D174, maps descriptor Group 6/domain ID 0x18 to a physical clock tree, and names the programmable field/status bits and units. For a 1:1:1 claim, that source must additionally identify UCLK-divider/crossing status and a common-reference conversion; the current source lookup does not.

## Artifacts

- Report: /home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smn-clock-register-public-source-followup.md
- Action log: /home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-smn-clock-register-public-source-followup.md
- Evidence directory: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/
  - public-source-retrieval-ledger.json
  - verify_public_source_gap.py
  - public-source-gap-result.json
  - stdout/stderr/exit captures
  - SHA256SUMS.final

The Agent Reach raw web responses remain only in /tmp; the project evidence stores sanitized source URLs, hashes, claim summaries, and the offline verifier result.
