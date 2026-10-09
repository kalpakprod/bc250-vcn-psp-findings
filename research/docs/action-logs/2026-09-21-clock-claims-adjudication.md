# Clock-claims adjudication — intent

## Intent (written before report)

- Timestamp: 2026-09-21T15:20:00+05:00 (Asia/Almaty)
- Actor: bounded offline adjudication subagent `/root/clock_claims_adjudication`
- Target: owned report `docs/research/2026-09-21-clock-claims-adjudication.md` and this action log only.
- Scope: adjudicate contradictory claims around `AmdFabricAriPei` `0x25D3`/`0x266F`, PEI service slot `0x34`, HOB Type 2 naming, and the inference from a no-immediate scan to global consumer/ABL handoff absence or presence.
- Inputs: exact local CLV disassembly/body and hashes; existing bounded reports and result JSON; pinned local EDK II PI headers and `PeiServicesTablePointerLibIdt` source. No ROM, firmware, hardware, network, candidate, shared report, or memory modification.
- Existing route checked: reuse the existing exact verifier and local PI source; no new analyzer is needed.
- Expected effect: one owned adjudication report that states the corrected claims, evidence boundaries, and unresolved next edge; no modification to the contradictory shared reports.
- Rollback: remove only `docs/research/2026-09-21-clock-claims-adjudication.md` and this action log.

## Observed result

- Timestamp: 2026-09-21T15:31:00+05:00 (Asia/Almaty)
- Exact offline command: a read-only `python3 -B` heredoc checked the hash-pinned `AmdFabricAriPei` body, disassembly markers at `0x25E2`, `0x25E8`, `0x2685`, `0x269C`, `0x26D6`, `0x26D8`, absence of `push 0x1204`, local `PiHob.h` Type 2/3 constants, `PiPeiCis.h` `CreateHob` signature and table order, and `PeiServicesTablePointerLibIdt` source.
- Literal result: `SUMMARY: 14/14 PASS; exit=0`.
- Direct findings: `0x25D3` matches the standard IDT-cached PEI Services pointer pattern; `0x2685 [ECX+0x34]` matches `EFI_PEI_SERVICES.CreateHob`; `0x26D8` supplies Type `0x2` and length `0x30`; PI defines Type `0x2` as `EFI_HOB_TYPE_MEMORY_ALLOCATION` and Type `0x3` as `EFI_HOB_TYPE_RESOURCE_DESCRIPTOR`; the Type-2 fields fit the requested `0x30` bytes; no direct `0x1204` push occurs in the exact module.
- Adjudication: replace “private AGESA dispatch” with standard PI PEI-service wording; replace “Type-2 resource descriptor” with “Type-2 memory allocation”; retain the no-immediate result as a bounded negative only; do not claim global consumer absence or an observed ABL1/APOB/SMU handoff. Treat `0x26D5` `push esi` as register preservation, not a third wrapper argument.
- Report written: `docs/research/2026-09-21-clock-claims-adjudication.md`.
- Final report SHA-256: recorded by the final closeout command below; it is not embedded in this self-referencing log.
- Action-log SHA-256 is reported by the final closeout command; it is not embedded in this self-hashing file.
- Reopened unchanged comparison artifacts: `docs/research/2026-09-21-luna-token1204-provider-object-boundary.md` SHA-256 `5fa10db8417bb05598a0878355f1b5b5129ac37a7529725324622e9216641aa4`; `evidence/firmware-audit/20260921-token1204-provider-boundary/token1204-provider-boundary-result.json` SHA-256 `6f89969ff01801ec1ef77d3aabbf726ae6b948b58f7b4d1ea8a05eddfe4d0bad`. Neither was modified.
- No ROM, candidate, firmware, board, network, shared report, shared memory, or global configuration was modified.
- Remaining uncertainty: runtime PEI dispatch/HOB contents and downstream ABL1/APOB/SMU consumer remain unrun.
