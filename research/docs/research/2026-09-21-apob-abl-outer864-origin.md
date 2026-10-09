# G7 correction — ABL1 outer+0x864 is not proven as the HEAP source

## Correction

The previous owned report `docs/research/2026-09-21-apob-abl-heap-populator.md` incorrectly described the ABL1 `0x6B78` call as copying payload bytes from `R10` / `outer+0x864`. Reopened bytes show that the checked call is **zero-filling**, and the exact FCLK call chain gives provider stack argument two as zero. The same numeric local offset `SP+0xA4` in constructor `0xC00` and provider `0x49CC` denotes different frames; it does not join the pointer field to the HEAP call.

The prior verifier's `34/34 PASS` only asserted literal bytes and callsite presence; it did not decode the `0x6B78` signature or reconcile stack arguments across FCLK → reader → helper → provider. Its PASS is not a semantic source-dataflow proof. The original report/evidence remain unchanged; this G7 report supersedes only that source-copy interpretation.

## Exact target and load-map result

- CLV donor: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- ABL1 container: SPI `0x99FD00`, 49,184 bytes, SHA-256 `95ae7826a69ea56b8c52ac703b85f181d45bdc309de334c2b7f9f4130376d515`.
- Exact decompressed ABL1: 94,624 bytes (`0x171A0`), SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact `$PS1` `load_address` field: `0x00000000`; this metadata does not provide a physical runtime base. A prior code-address fit under `0x57100` is explicitly conditional, not loader proof.
- Constructor literal `0x006CD4D0` occurs at payload `0xC4B4` (`D0 D4 6C 00`). It is outside payload-relative coordinates with load address zero; under conditional base `0x57100`, it maps to payload offset `0x6763D0`, also outside `0x171A0`. Thus it is not mapped into the exact ABL1 payload by either available mapping. Its actual target region remains unknown because the loader/runtime map is unresolved. An alternative base is not inferred to force an in-image mapping.

## Constructor caller and field writes

Fresh disassembly and byte reconciliation of the exact payload show:

- Constructor caller `0xB84` sets `R4=R0`, `R5=R1` at `0xB88/0xB8A`; its path at `0xBCA/0xBD0/0xBD2` sets `R1=R5`, `R0=R4`, then calls `0xC00`.
- Four inspected direct callsites (`0xA6C`, `0xA8A`, `0xAB6`, `0xAE4`) set `R1=R4` before calling `0xB84`.
- In the containing ABL1 code, `R4` is derived from runtime/global structure data: load a pointer through the literal cell `0x6E134`, read `[R0+0x0C]`, then OR `0xFC000000` into `R4` at `0xA30`. This is not a byte-backed APOB or `$INV` field join.
- Constructor `0xC00` retains its input outer object in `R8`; it computes `R1+0x864` at `0xC29E`, saves that pointer in **the constructor's** `[SP+0xA4]` at `0xC2A8`, then stores `0x006CD4D0` to `[R1+0x864]` at `0xC2AE`.
- The exact full Thumb listing contains only direct `#0x864` references at `0xC29E` (address computation) and `0xC2AE` (store); the direct store encoding `C1 F8 64 28` occurs once. No alias/indirect write exclusion is claimed.

## FCLK call-frame argument into HEAP key 0xA04E

Raw Thumb bytes and reconciled disassembly establish this separate call chain:

```text
FCLK 0x463C:
  0x464C: MOVS R2,#0
  0x4664/0x4666: STR R2,[SP] / STR R2,[SP+4]
  0x466A: BL 0x1FB4

reader 0x1FB4:
  push mask 0x47FF saves 12 registers = 48 bytes
  0x1FC0: LDRD R7,R9,[SP,#48]   ; caller stack words, R9 is second word = 0
  0x1FD2: STR R9,[SP]           ; forwards that zero as helper arg0
  0x1FE0: BL 0x4800

helper 0x4800:
  push {R2,R3,R4,R5,R6,LR} = 24 bytes
  0x4808: LDR R1,[SP,#0x18]     ; helper entry SP arg0 = forwarded zero
  0x4812: STRD R3,R1,[SP]       ; provider stack args = R3, then zero
  0x481C: BL 0x49CC

provider 0x49CC:
  push mask 0x4FFF saves 13 registers = 52 bytes
  0x49D2: SUB SP,#0x6C = 108 bytes
  frame delta = 52 + 108 = 160 bytes
  provider [SP+0xA4] = entry SP +4 = second provider stack arg = 0
  0x4B54 loads that value into R1; 0x4B5C calls 0x6238 on the 0xA04E miss path
```

For this FCLK invocation the second `0x6238` argument is zero. It is an **auxiliary caller value/context**, not proven to be a payload source pointer. Other direct `0x6238` callsites (e.g. `0x46DC`, `0x4774`) pass `R1=R6`, copied from the respective caller's input `R0`; the second parameter therefore cannot be given a universal “source pointer” type from the selected call alone.

## 0x6238 / 0x6B78 signature discrimination

The `0x6238` producer saves its second argument `R1` into `R10` (`0x6242`). It later sets:

```text
0x6316: MOVS R1,#0
0x6318: LDR R2,[R5,#4]      ; node length
0x631A: ADD R0,R5,#0x10     ; node payload destination
0x631E: MOV R3,R10          ; auxiliary arg is R3
0x6320: BL 0x6B78
```

Fresh Thumb disassembly of `0x6B78..0x6B84` decodes:

```text
0x6B78: B 0x6B7E
0x6B7A: STRB R1,[R0],#1
0x6B7E: SUBS R2,#1
0x6B80: BHS 0x6B7A
0x6B82: BX LR
```

The helper consumes `R0` (destination), `R1` (fill byte), and `R2` (length); it does not read `R3`. In this call `R1=0`, so the operation is a zero-fill/memset-like loop, not memcpy from `R10`. The prior description of `0x6B78` as a byte-copy helper was incorrect.

## Boundary

The native `AmdSetup+0x316=0x24` `$INV 0x11ED` producer and APOB service `0x9E3B14C` / message `0x61` / argument `0xFF` remain separate existing static routes. This correction finds no byte-backed join from either route to the constructor outer object, `[SP+0xA4]` in the provider frame, the FCLK stack argument, or the A04E HEAP miss path.

The HEAP node's newly allocated payload is zero-filled in the inspected creation call. Later provider population paths, whether they use the external field pointer in other callers, and actual runtime contents remain outside this correction's scope. No firmware, ABL1, APOB service, SMU, hardware, training, clock, or synchronization execution was performed.

## Reproduction and owned evidence

A fresh-window verifier was started in `evidence/firmware-audit/20260921-apob-abl-outer864-origin/outer864_origin_verify.py`. Each requested LLVM Thumb window exited `0` and was byte-reconciled to the hash-pinned decompressed payload. The verifier reached final result assembly but then exited `1` with `NameError: name 'toolver' is not defined`; therefore no machine PASS JSON is claimed for that orchestration script. The captured disassembly windows and raw-byte checks remain the evidence for this G7 correction; the orchestration bug is retained in the action log.

- Fresh disassembly tool: LLVM 22.1.8.
- Input object: `evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Existing ABL1 full listing: `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Relevant owned windows: `fclk-463c.stdout`, `reader-1fb4.stdout`, `helper-4800.stdout`, `provider-49cc.stdout`, `heap-6238.stdout`, `fill-6b78.stdout`, `constructor-caller-b84.stdout`, `constructor-c00.stdout`, `context-callers.stdout`; every captured `.exit` is `0` and every `.stderr` is empty.
- Exact target and neighboring boundary lines remain in the machine-readable windows; no old report/evidence was modified.

Current check status: **PASS** for byte-reconciled disassembly windows and the specific stack/fill semantics above; **INCONCLUSIVE** for actual runtime load base and source-region identity; **UNRUN** for ABL1/HEAP execution and every hardware result.

## G7 transmission and ownership note

The prior heap-source statement is withdrawn exactly as described above. Root should propagate this correction to the `read_current_goal` and `clock_independent_review` tracks before either reuses the old copy narrative. This subagent could not directly message those tracks because no collaboration/send tool was exposed.

The nominal evidence directory already contained root-created files timestamped 16:46 before this executor wrote its 16:50/16:58 artifacts. No root-created file was edited, but the `SHA256SUMS.final` in that shared directory was generated over both sets and is a mixed-owner manifest, not a single-owner verification artifact. Root should reconcile it or treat the fresh window files as unintegrated until reviewed.

## Isolated verifier correction rerun — completed (2026-09-21T17:18:00+05:00)

The prior failed verifier copy was left unchanged. A fresh uniquely owned directory was used:
`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/`.

The copied source changed only these verifier mechanics: (1) `OUT` was retargeted to the isolated directory; (2) `toolver` was initialized from `llvm-objdump --version`; and (3) the existing byte-valued check records were given a bytes-to-hex JSON default so result assembly is parseable. No instruction expectation, input path, firmware fact, or semantic check was changed. Exact diff: `.../DIFF_FILE.patch`, SHA-256 `b14a93d48cee3ce12a86a37cba26d3356331fc6147415e83dda59bc6f9eee89d`.

- Corrected verifier command: `PYTHONDONTWRITEBYTECODE=1 python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/outer864_origin_verify.py`
- Observed stdout: `{"status":"PASS","checks_passed":102,"checks_failed":0,"pointer":"0x006CD4D0 not mapped into ABL1 by exact header or conditional 0x57100 base; runtime map unresolved","fclk_provider_aux":"zero","fill_semantics":"0x6B78 repeats R1 byte; FCLK call sets R1=0; not memcpy","first_unresolved":"upstream/runtime map of outer object and any bridge to APOB/INV"}`
- Exit status: `0`; stderr: empty. Machine result: `PASS`, 102/102 checks. LLVM version recorded in result: `22.1.8`.
- Independent single-case command: `llvm-objdump -D --section=.data --triple=thumbv7 --start-address=0x6b78 --stop-address=0x6b84 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`; exit `0`, stderr empty. It decodes `0x6B78: B`, `0x6B7A: STRB R1,[R0],#1`, `0x6B7E: SUBS R2,#1`, `0x6B80: BHS`, `0x6B82: BX LR`. Independent raw bytes at payload `0x6B78` are `01 e0 00 f8 01 1b 52 1e fb d2 70 47`.
- Rollback role: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/ROLLBACK.sh`; separate disposable target restored with exit `0`, and its SHA-256 `9e3ae148c72c333a0816e7b90ba70d359691eef297e537d89a2be655fec05241` equals the sibling baseline.
- Four roles reopened: modified verifier `outer864_origin_verify.py` (SHA-256 `16fb872d550a5f09d482c56f78375e447e77f91de382feef91a3550c3640bb3f`), `DIFF_FILE.patch`, `VERIFICATION.txt`, executable `ROLLBACK.sh`; final manifest `SHA256SUMS.final` validates all 68 listed entries with exit `0`.

The first isolated rerun after the requested `toolver` fix exposed and preserved a separate JSON serialization error (`TypeError: Object of type bytes is not JSON serializable`); the bytes-to-hex compatibility change above was the smallest output-only correction needed to reach result emission. The original mixed-owner failure remains preserved as `NameError: name 'toolver' is not defined`.

The static conclusion is unchanged: FCLK provider second stack argument is zero; `0x6238` sets `R1=0`, `R0=node+0x10`, `R2=node length`, and passes `R10` only in `R3`; `0x6B78` does not read `R3` and zero-fills. This is observed-bytes/static-analysis evidence only. Runtime load/relocation mapping, aliases/DMA writes, ABL1/HEAP execution, APOB/INV join, firmware writes, and hardware clock/training behavior remain unresolved/unrun.
