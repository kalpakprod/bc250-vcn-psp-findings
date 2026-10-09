# Verdicts for the operator's 6 decode items (2026-09-17)

> Audit 2026-09-27: bounded static synthesis. Negative literal/dataflow searches do not exclude every computed writer. Presence of the flash pointer table and unknown population code are different facts. 0xFFFF0009 is a statically derived return value, not by itself the measured hardware status or rejection location. The unresolved svc handlers prevent treating the closing chain as a complete proven VCN-up path.

Inputs: worker reports `docs/research/2026-09-17-t28-open-questions-workerA.md`,
`docs/research/2026-09-17-t8-smu-msgtable-workerB.md`,
`docs/research/2026-09-17-staged-descriptor-hunt-workerC.md` (all
static-analysis/observed-bytes; G8 workers, read-only, reports reviewed by root).

1. **Table @0x188D8 (OQ-V3a)** — DECODED (partial). Load base t28 = 0x00E00000
   (484 in-range literals; 61 refs to 0x00E01A1C). The 5-entry table is
   consumed by svc #0x7C (write, @0xFCC8) AND svc #0x7B (read, @0x11360);
   it is NOT plausible (SMN addr,value) pairs (3 nonzero 64-bit constants
   - 2 zeros). True semantics live in the svc #0x7B/0x7C handlers outside
     t28. RESIDUAL: handler decode (OQ-V3a kept open, narrowed).
2. **Builder of 0x69D38 (OQ-V3e)** — DECIDED. No code in t28 (old or new)
   writes to 0x69D38-0x69FFF (dataflow scan, 0 hits). t28 stores POINTERS
   into the region, passes the base to svc #0x5E/0x5F, and manages its own
   body copies. The fw_type pointer table IS stored in flash at t28 body
   0x18AAC-0x18D48 (worker C correction of root's earlier "not stored").
   Population of SRAM happens outside t28 (PSP director / svc handlers).
3. **r1 = 0x00185103 (OQ-V3c)** — DECIDED: immediate value, not a pointer;
   fw_type-13 writes 0x00185103 to SMN 0x1F820 (bitfield-looking 0x18/0x51/0x03,
   undecoded).
4. **t8 SMU msg table (V1)** — DECODED (first full pass, pypcode/SLEIGH
   Xtensa): t3 msg table = 8-byte records {handler, flags}, 169 slots,
   128 implemented, 41 NULL, base SRAM 0x746C. **msg 0x8/0x9
   (PowerDown/UpVcn) = NULL in BOTH versions** — community claim confirmed
   byte-level. ID occupancy and flags identical old vs new; all handlers
   recompiled (3 shared thunks unchanged). Addressing convention resolved:
   new body file = SRAM - 0x100 (reconciles all run-1 anchors; root's
   earlier "window base shifted +24 B" was an artifact of this — G7
   correction noted).
5. **Staged descriptor (OQ-V3d)** — DECIDED: no flash-side staging source
   exists (whole-image sweep negative; PSP entries 0x30-0x34/0x44-0x51
   clean; UEFI/ABL clean). Descriptor chain lives in PSP SRAM populated by
   code outside t28. Actual rejection status returned is 0xFFFF0009
   (0xFFFF0006 literal + adds #3) and fw_type 13 IS in the dispatch set —
   so the hardware ITEM_NOT_FOUND must occur upstream (descriptor
   validation or memory reservation 0x11460), still to be pinned.
6. **Runtime layer** — NOT DECODABLE statically (evidence-class boundary).
   PSP acceptance, VCLK rise, amdgpu registration are hardware-verified
   class only; requires R0 restore gate.

## Campaign state after this pass

The C1 chain is now fully mapped at static level:
`[svc #0x5E/5F handler populates SRAM 0x69D38 table] -> t28 dispatch 0xE6A8
-> fw_type-13 handler 0xE7BC (svc write 0x00185103 -> 0x1F820) -> release
block 0xFCC8 (1->0x0900C004, 1->0x1F8A4, 5 table ops) -> VCN up`.
Two residual static targets: svc #0x7B/0x7C/0x5E/0x5F handlers (PSP director,
outside t28) and the upstream rejection site. All flash bytes involved are
byte-identical between native and P5.00.
