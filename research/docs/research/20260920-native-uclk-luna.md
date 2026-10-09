# Exact-clv native UclkDiv1M0 bounded consumer trace

Scope: one offline native path only, from AmdSetup `+0x330` (UclkDiv1M0) to the first callback/record consumer. No firmware or hardware write.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Module: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin`
- Module SHA-256: `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`

## Fresh byte-backed result

1. `CbsBasePei+0x9cc4`: `ba 04 12 00 00` loads literal record ID `0x1204`; the following bytes store it at the output record header.
2. `CbsBasePei+0x9ce4`: `8a 82 30 03 00 00` loads byte `Setup+0x330`; the actual store is at `CbsBasePei+0x9cea`: `88 41 03`, which stores it as the record value. Host-only discriminating reconstruction yields:
   - `Setup+0x330=0x00` -> record bytes `04 12 00 00`;
   - `Setup+0x330=0x01` -> record bytes `04 12 00 01`;
   - `Setup+0x330=0x7f` -> record bytes `04 12 00 7f`.
     This proves the immediate serializer path preserves the selected byte; it does not assign a frequency or clock domain.
3. The first callback table entry at module RVA `0x13e20` contains provider pointer `imagebase+0x13dc0`; provider `+0x10` contains `imagebase+0x36c0`. `0x36c0` calls `0x36f0` at `0x36de` (`e8 0d 00 00 00`). `0x36f0` emits the `$INV` header (`c7 02 24 49 4e 56` at `0x3728`) and version `1` at `0x3731` before emitting the records.
4. Dispatcher bytes at `0x47d..0x499` perform an indirect call through callback entry `+0x10`; the bounded dispatcher window contains no `0x1204` literal or direct clock/register write.

## Bounded missing link

The immediate consumer found is the CbsBasePei INV adapter (`0x36c0 -> 0x36f0`), not a final DF/UCLK actuator. The retained exact-clv 233-module census classifies CbsBasePei's `0x1204` site as an `immediate-candidate` serializer. Its caller matrix lists only AmdFabricAriPei and AmdCcxVhAriDxe as confirmed INV readers; CbsBasePei is omitted by the matrix-generation rule because it has an INV serializer marker but no selected heap-GUID/NVTB reader marker. Therefore the final consumer/override after this callback-list/INV hand-off remains unresolved within the bounded static-analysis coverage of the 233-module x86/TE census. This is not evidence that the consumer lies outside the census and not proof that no indirect/dynamic/DMA consumer exists.

## Reproduction and checks

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`
- Result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-native-uclk-luna/uclk-consumer-trace.json`
- Observed verifier output: `{"status": "PASS", "checks": 22, ...}`
- Existing census evidence reused: `20260919-inv-token-consumers/caller-matrix.md`, `coverage.json`, `verification.json`.

Checks passed: pinned ROM/module hashes, exact serializer load/store bytes (`0x9ce4`/`0x9cea`), callback table pointer arithmetic, `0x36c0 -> 0x36f0` call, INV header/version writes, dispatcher indirect-call window, three synthetic value distinctions, and retained-census classification. Hardware behavior, defaults precedence, domain identity, frequency units, and clock synchronization remain unrun/unresolved.
