# Exact ABL1 payload-relative address and loop-semantics review

## Result

Independent header/entry/Thumb checks establish only a payload-relative code model:

- ABL1 container: PSP type `0x31`, SPI `0x99FD00`, container SHA-256 `95ae7826a69ea56b8c52ac703b85f181d45bdc309de334c2b7f9f4130376d515`.
- `$PS1` header: `load_address=0`, `rom_size=0xC020`; decompressed payload length `94624` (`0x171A0`). The zero load-address field is observed metadata, not a proof of physical runtime base.
- ARM entry bytes at payload offset `0x0`: `e92d4010 e59f2004 e12fff32 e8bd8010`; literal at `0x10` is `0x0005E02D`, outside the decompressed payload. This is an ARM entry trampoline with an external/unknown target, not a proven in-payload call to `0x95FC`.
- Exact function cluster starts at payload `0x95FC`, continues through `0x98AB`, and reaches a code-to-data boundary at `0x98AC`, where raw data begins `\nAGESA MEM - Multi-Die - DRAM Speed Sync`. The previous worker disassembly window ending at `0x9870` was partial.

## Loop and calling/dataflow observations

- `R0` is dereferenced at `0x9600` into `R4`, establishing a context-pointer input.
- `R5` is a caller-supplied outer structure; the function reads `[R5+0x0C]`, `[R5+0x4B]`, and callback `[R5+0x52C]`.
- First indexed loop: callback `[R5+0x52C] (R5,index)` runs before reading `[R5+0x0C]+0x20`; the byte `[R5+0x4B]` controls its bound. `R1=R4+(index<<2)` and the result is stored at `R1+0x278`.
- Reduction/writeback loops use `[[R4+0x3C4]+0x74]` as a later bound and write selected values at `[R4+0x2BC]` and `[R0+0x20]`.
- Exact payload strings mention `Channel`, `MEMCLK`, and `Memory P-state`, but strings do not prove that `[R5+0x4B]` or `[[R4+0x3C4]+0x74]` are channels, P-states, dies, or a physical memory domain. The semantic names remain unresolved.

## Boundary

The review does not infer a runtime relocation base, loader contract beyond observed `$PS1` fields, caller/provider identity, MHz units, UCLK/FCLK relationship, or `1:1:1`. A flat Thumb scan has no complete xref authority over mixed code/data. The exact `AmdSetup+0x316/$INV 0x11ED` population edge remains open.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1_address_loop_verify.py
```

Observed status: `25/25 PASS`.

Owned evidence:

- `evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1-address-loop-result.json` — SHA-256 `04a1086be29f6297461d90ecaa9865d5d74747371ccd2860510967dc94e87227`
- `evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1-entry-arm.txt` — SHA-256 `b494f9e3d59855eaa7a39ea8e1623bebe7d1419b05b1d7b0f29a67b56f9cc223`
- `evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1-function-95fc-98b0.txt` — SHA-256 `569981be14760be76e4a5e8f3fc6f46307d2299017db834fca29eb6e98b05898`
