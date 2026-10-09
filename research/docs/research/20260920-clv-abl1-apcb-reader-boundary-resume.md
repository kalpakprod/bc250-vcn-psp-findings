# Exact CLV ABL1 UCLK/FCLK common-reader boundary — continuation

## Current

The previously completed exact-branch evidence was revalidated first, then the first unfinished edge was executed: exact ABL1 payload `0x1FB4`, called by the UclkDiv1/Fclk policy branches.

## Fresh result

Verifier exit `0`, `42/42 PASS`, stderr empty.

The exact function at payload `0x1FB4` is a descriptor-driven typed configuration/APCB lookup boundary:

- Prologue preserves descriptor pointer `R0 -> R5`, output pointer `R2 -> R6`, and caller type pointer `R3 -> R10`; it reads the first descriptor halfword and rejects a zero descriptor.
- UclkDiv1 descriptors are constructed as exact halfword pairs `[0x20,0x21]`, `[0x20,0x22]`, `[0x20,0x23]`, `[0x20,0x24]`; Fclk constructs `[0x015F,0x0160]`.
- The reader iterates descriptor entries and calls exact helper payload `0x4800` for each entry.
- Caller-supplied type selects output width: type `1` stores a byte at `[R6]`, type `2` a halfword, type `4` a word, and type `8` a doubleword. Success returns `R0=1` at `0x2092`; failure returns `R0=0` at `0x209A`.
- Exact ABL1 strings include APCB/CBS parameter wording (`APCB parameter disabled`, `Config parameter ... mapped to CBS token`, and `Get config parameter ...`).

This proves the UCLK/FCLK branches hand descriptor IDs into a generic typed parameter reader. It does **not** prove a divider/PLL write, MCLK/UCLK/FCLK equality, units, training, synchronous crossing, runtime invocation, physical clocks, or hardware behavior. The first unresolved edge is helper `0x4800` and its external/indirect parameter provider.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1_apcb_reader_boundary_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 42,
  "reader": {
    "payload_offset": "0x1fb4",
    "role": "descriptor-driven typed configuration/APCB lookup boundary",
    "descriptor_pairs": {
      "UclkDiv1M0": ["0x20", "0x21"],
      "UclkDiv1M1": ["0x20", "0x22"],
      "UclkDiv1M2": ["0x20", "0x23"],
      "UclkDiv1M3": ["0x20", "0x24"],
      "Fclk": ["0x15f", "0x160"]
    },
    "helper": "payload+0x4800",
    "typed_outputs": {
      "1": "byte [r6]",
      "2": "halfword [r6]",
      "4": "word [r6]",
      "8": "doubleword [r6]"
    },
    "success": "r0=1 at 0x2092",
    "failure": "r0=0 at 0x209a"
  },
  "unresolved_edge": "payload+0x4800 and its external/indirect parameter provider remain the first consumer edge. No MCLK=UCLK=FCLK, ratio, PLL, training, synchronous-crossing, runtime, physical-clock, or hardware claim follows."
}
```

Observed stderr: empty. Exit status: `0`.

## Inputs and evidence

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Exact Thumb disassembly: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
  - SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`
- Completed prior exact branch result, revalidated:
  - `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json`
  - SHA-256 `d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa`

New role paths:

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1_apcb_reader_boundary_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/20260920-clv-abl1-apcb-reader-boundary-resume.md`
- Report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-apcb-reader-boundary-resume.md`

No firmware, hardware, settings, shared plan, memory, install, MCP/Cutter, candidate, or source input changed.
