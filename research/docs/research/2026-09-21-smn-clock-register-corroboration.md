# SMN clock-register corroboration: selector addresses have no local header match

Date: 2026-09-21 (Asia/Almaty, UTC+05:00)  
Owner: `/root/clock_observability`  
Scope: offline corroboration of the completed exact-CLV selector result only; no disassembly rerun.

## Conclusion

The completed SMU-domain selector result identifies two exact calculated SMN addresses for its accepted example: **program `0x0116D150`, poll `0x0116D174`**. The same result maps that example to selector index `11`, array entry `10`, target slot `0x140B0`, domain ID `0x18`, internal Group `6`, raw program offset `0x6D150`.

A bounded verification against the five existing local register/interface headers found **zero literal matches** for either address or its natural base-stripped forms (`0x06D150` / `0x06D174`, `0xD150` / `0xD174`). The headers do not independently name these addresses as MCLK, UCLK, FCLK, DF, UMC, a divider, or a crossing/status register. Thus the address derivation is corroborated only as a static PMFW-selected program/poll target; **register-header evidence does not support any physical-clock identity**.

This does not prove those registers or equivalent computed aliases are absent. It is a bounded no-match over the current local header set, not a hardware map or absence claim.

## Bound evidence and exact addresses

The selector source is the completed result at `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json`. I did not rerun its Ghidra/disassembly path or modify the author’s source/evidence. The accepted example in that result is:

| Field                       | Completed result |
| --------------------------- | ---------------: |
| Selector index              |             `11` |
| Array entry                 |             `10` |
| Target slot                 |        `0x140B0` |
| Dynamic domain ID           |           `0x18` |
| Internal group              |              `6` |
| Raw program offset          |        `0x6D150` |
| Derived SMN program address | **`0x0116D150`** |
| Derived SMN poll address    | **`0x0116D174`** |

The result’s arithmetic/encoding fields remain qualified as model/static: low 16 bits `integer -> ufloat.s`, target scaling `*0.001f`, Group-6 base `U9.16 -> float`, VCO factor `*0.1f*256`, then software float division/encoding. Its `unit_label` remains “not encoded/proven; no MHz claim.” The separate slot-24 qualification records only a historical Robin-3 mapping with `semantic_name=null`; it is not a mapping for these Robin-5 addresses or their physical clock domain.

The bound firmware baseline is `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. The read-only test also reconfirmed `AmdSetup+0x316 = 0x24` at ROM `0x7E5` (IFR label `1800MHz`); no input bytes were changed.

## Local header match check

The bounded set was inventoried from the existing local RE sources:

| Header                                                                         | SHA-256                                                            | What it contains relevant here                                                                                                    |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `archives/imported/recon-evidence/legacy-tmp-bc250-recon/gc_10_1_0_offset.h`   | `a0ad8bffb3c07ec3824d306aff49c77bc40057f8760aec7a76ee58a60cc8e6a2` | GC MMIO offsets, including the separate RLC `GFXCLK:REFCLK` counters; no `0x116D150/174`, `0x6D150/174`, or `0xD150/174` literals |
| `archives/imported/recon-evidence/legacy-tmp-bc250-recon/gc_10_1_0_sh_mask.h`  | `cba20414ecf02e91bafdcfbff7d4ba686326f0bdaf236d1a883364f08410c167` | GC register masks; no selector-address literals                                                                                   |
| `archives/imported/recon-evidence/legacy-tmp-bc250-recon/gmc_10_0_0_offset.h`  | `e45906ce02e79f16fb87a838d86bb4e497e37a9591f97608fa013bbcd8b9cbc2` | 127-byte stub, no register definition                                                                                             |
| `archives/imported/recon-evidence/legacy-tmp-bc250-recon/gmc_10_0_0_sh_mask.h` | `e45906ce02e79f16fb87a838d86bb4e497e37a9591f97608fa013bbcd8b9cbc2` | Same 127-byte stub                                                                                                                |
| `archives/imported/recon-evidence/legacy-tmp-bc250-recon/smu_v11_8_pmfw.h`     | `8893329478e28c2f36b0298b2aeb0fc4b5902a77e76e82db57e2884fe0a82966` | SMU feature bits/levels (mentions `FCLK_DPM` and G6 UCLK/UCLK_DIV SSC), not a register-address table for this SMN window          |

The header set has 31 textual `MCLK/UCLK/FCLK/DF/UMC`-related lines, primarily unrelated RLC counter names and PMFW feature/level fields; **none has an address-literal hit or connects its symbol to `0x0116D150`/`0x0116D174`**. Existing RLC `GFXCLK:REFCLK` definitions at `0x4C30..0x4C35` are not substituted for the Group-6 SMN addresses and do not resolve their semantics.

## One verification command and observed result

Command actually executed:

```text
python3 -B evidence/firmware-audit/20260921-smn-clock-register-corroboration/smn_header_match_test.py
```

Literal stdout:

```text
{"checks": {"failed": 0, "passed": 4, "total": 4}, "domain_id": "0x18", "domain_symbols": 31, "header_count": 5, "literal_matches": 0, "output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smn-clock-register-corroboration/smn-header-match-result.json", "poll": "0x0116D174", "program": "0x0116D150", "status": "PASS", "verdict": "NO_DIRECT_HEADER_MATCH"}
```

- Exit status: `0`.
- Stderr: empty (`0` bytes).
- `PASS` means the bounded comparison and baseline checks executed successfully; the match verdict itself is `NO_DIRECT_HEADER_MATCH`.
- Machine result records hashes, addresses, the five header inputs, matches and the scope limit.

## What would resolve the missing link

A register-meaning artifact for this exact SMN address window is still required: a pinned, address-bearing AMD/AGESA/DF register header or independently decoded exact-board code path that names `0x0116D150`/`0x0116D174`, specifies field semantics/read-vs-program behavior, and ties Group-6/domain `0x18` to one physical clock tree. To establish `MCLK:UCLK:FCLK = 1:1:1`, additionally require independent domain readbacks, units/common-reference conversion, and the UCLK divider/synchronous-crossing status. No hardware procedure is supplied here; the exact meaning is not established by these header matches.

No hardware, network, sysfs, install, ROM/NVRAM, register or firmware action occurred. No GoldenTSC/ATOM analysis or selector disassembly was repeated.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smn-clock-register-corroboration.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-smn-clock-register-corroboration.md`
- Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smn-clock-register-corroboration/`
  - `smn_header_match_test.py`
  - `smn-header-match-result.json`
  - `source-test.stdout`
  - `source-test.stderr`
  - `source-test.exit_status`
  - `SHA256SUMS.final`
