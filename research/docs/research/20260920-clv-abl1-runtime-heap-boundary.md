# Exact CLV ABL1 UCLK descriptor runtime-table boundary

## Current

The exact first ordered UCLK descriptor entry `0x20` was followed through the provider selector path and compared against the pinned ROM APCB bytes. Verifier result: `PASS`, `32/32`, exit `0`, stderr empty.

## Fresh result

- Provider case selector: exact `0x0F`.
- Runtime record key constructed for this provider case: exact `0xA04E`, stored into the descriptor passed to `0x6374`.
- Exact `0x6374` lookup uses a runtime table pointer literal `0x00073000` and a `HEAP` sentinel. It compares the input key against linked entries; on match it returns a body pointer and length through the descriptor fields.
- Exact `0x6238` is another runtime HEAP/table allocator/block boundary using the same `0x00073000` pointer literal and `HEAP` sentinel.
- The aligned little-endian scalar `0x0000A04E` is absent from the entire pinned 16 MiB ROM. Therefore no direct flash APCB row can be assigned as the backing record for this runtime key.
- Raw CBSG bytes were recorded without schema decoding. In the pinned CBSG subgroup body, raw rows with second u16 values `0x20/0x21` occur at `0xAB14D8`, `0xAB14E8`, `0xAB1500`, and `0xAB185C`; this is raw contrast only, not a proven token map.

This is a concrete storage-indirection boundary. Runtime population of the HEAP records and conversion from APCB/CBSG raw records to that runtime table remain unresolved. No enum/voltage/frequency/pointer semantics, divider/PLL application, or MCLK=UCLK=FCLK proof follows.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 32,
  "chain": {
    "descriptor": "first ordered UCLK descriptor entry 0x20 -> helper 0x4800",
    "provider_selector": "0x0f",
    "runtime_record_key": "0xa04e",
    "lookup": "0x6374 uses runtime table pointer literal 0x73000 and HEAP sentinel; matches [input] key and returns body pointer/length",
    "heap_helper": "0x6238 uses runtime table pointer literal 0x73000 and HEAP sentinel",
    "apcb_contrast": "CBSG raw rows observed at 0xAB14D8/0xAB14E8/0xAB1500/0xAB185C; schema not decoded",
    "direct_rom_key_match": "0xA04E absent as aligned little-endian scalar"
  },
  "unresolved_edge": "Runtime population of the HEAP records keyed by 0xA04E and the conversion from raw CBSG/APCB records to that runtime table remain unresolved. No frequency/enum/voltage/pointer semantic assignment or MCLK=UCLK=FCLK proof follows."
}
```

Observed stderr: empty. Exit status: `0`.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`
  - SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`
- Prior provider result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json`
  - SHA-256 `3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9`
- Prior APCB parser result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json`
  - SHA-256 `503e4f525f4372903b23ea9320c77f7b0b39250f310d80a1b7565eb98b39f394`

## New artifacts

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1-runtime-heap-boundary-result.json`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-runtime-heap-boundary.md`

No firmware, hardware, settings, shared plan/memory, installation, global config, MCP/Cutter, candidate, source, commits, or subagents changed.
