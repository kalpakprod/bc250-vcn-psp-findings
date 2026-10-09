# NBIF VCN clamp mechanism — reverse-engineered structure (2026-09-12)

> Historical model, not a demonstrated end-to-end mechanism. The token consumer is explicitly TBD below; naming byte defaults as a physical clamp and deriving a live write procedure requires evidence beyond the shown serialization. Not a current probe authorization.

Evidence: `recon/disasm_AmdNbioGfxARIPei.txt` (25,318 lines), `recon/disasm_AmdNbioPcieARIPei.txt`
(30,380 lines), APCB token scan of the current chip image (`6b1fe8ef...`). All claims
`static-analysis` unless marked otherwise.

## The clamp chain, end to end

1. **Hardcoded defaults** (`disasm_AmdNbioGfxARIPei.txt` `0x22a3..0x24f8+`): the PEIM's
   Init Config Struct initializer fills hundreds of byte fields unconditionally. The
   VCN-relevant fields get **`0x3` = Port-Disconnected/Clamped** (`+0x1e0` at `0x2404`,
   `+0x1e1` at `0x240e`), while several neighboring ports get **`0x7` = Full-Enabled**
   (`+0x1e2/+0x1e4/+0x1e5/+0x1e6/+0x1ea`). The clamp is a DEFAULT, not a measurement.
2. **Serializer** (Gfx `0x7322/0x7342`, `0x7354/0x7374`; Pcie `0x0a986..0x0aaf0+`): emits
   APCB token records into a RAM token list: `word token_id` + type/size byte
   (`AND 0xfc`, `OR 0x2`) + payload byte(s) copied from the struct
   (token `0x10c2` <- `struct+0x1e0`, `0x10c3` <- `struct+0x1e1`, tokens `0x1090-0x1094` <- `0x1a2/0x1a3/0x1a7/0x1ab/0x1ac`, ...).
3. **APCB merge at boot**: the flash APCB (`0xAB1000`, checksum-only gate) is the
   TEMPLATE; the PEI token stream is merged in RAM. Token scan of the flash image
   proves tokens `0x10c2/0x10c3` are ABSENT from flash — Robin omits the VCN NBIF
   tokens; the clamp is injected at runtime by the PEIM defaults (fail-closed).
4. **Token engine** (consumer, location TBD — likely the shared AGESA token engine or
   PSP/ABL side): parses the merged stream and programs the NBIF registers via the
   SMN-window primitives.
5. **SMN access primitives** (`0x6a3` = read, `0x72d` = write, `0x75b` = RMW
   `(reg & and) | or`): PCI `0xB8` index + memory window `0xe0000000` (sizes byte/word/
   dword; `0x81+` = bulk via `0x846`); instance base from `[state+0xe]`, stride `0x83/0x103`.
   Token arguments are REAL SMN addresses (`0x6A1xx` class) — same mechanism as the
   live-proven `0x13b1005c` reads.
6. **PSP SEC_GASKET** (type `0x24`, separate path): programs the firewall banks
   (VCN bank 12 `0x0900Cxxx` — absent in Robin) and hardware-locks the Fabric
   translation matrices until cold reset (chain report §3.1; runtime values are
   programmable — proven 2026-09-12 — but the translation lock is not understood yet).

## Consequences for the unlock

- Two independent clamps: (a) NBIF port config via runtime-injected tokens (defaults
  `0x3`), (b) fabric firewall values + translation lock (PSP gasket).
- (b)'s VALUES are runtime-writable (proven: 59/59 accepted, commit=1). The open
  question is whether the ROUTING registers (`0x6A1xx`/`0x1C7xx`/`0x1F8xx`) are
  writable at runtime — if the translation lock guards only the firewall target
  registers, a full donor-route write opens the bridge.
- The ready live experiments (scripts deployed on board):
  1. `stage4b_nbif_config_capture.py` — read-only capture of `0x6A1xx/0x33e0`.
  2. `stage5_full_dataplane.py` — donor routes/windows/binding writes + capture.
  3. `stage4_arbiter.py` — the `mmUVD_VERSION` verdict.
- The deeper RE targets: the token ENGINE (consumer loop), and the PSP/ABL gasket
  executor (ARM blobs in `recon/robin3_psp_bodies/`, `disasm_arm_binary.py` available)
  — the "trusted transition contract" per master plan use-case 2.

## Ruled out by this decode

- P3.3b "in-place APCB token flip" — tokens absent from flash; nothing to flip.
- The four NBIO candidates as clamp carriers — they are PEI read-captures of hardware state.
- Any belief that the gasket write list alone (P1.2/1.3) is the full donor state —
  the routes/binding/`0x6A1xx` layer is separate and was never runtime-written.
