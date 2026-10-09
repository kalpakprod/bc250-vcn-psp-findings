# CLV fixed-voltage Setup consumer trace (VCORE / GFX / MEMIO)

Historical static trace: the later [independent decode](2026-09-20-fixed-voltage-independent-decode.md) corrected the VCORE enable-test RVA from `0x30A` to `0x30F`, plus two byte-assertion labels. The [PEI applicability review](2026-09-21-luna-fixed-rail-conditions-current.md) found an unresolved second-PPI dispatch prerequisite. Thus “on every boot” and a physical VR write are not established by this report.

Current: pinned CLV donor / two PEI consumers identified by exact instruction evidence / static only / no voltage recommendation.

## Conclusion

The eight fixed-voltage/loadline controls that live in the separate `Setup` VarStore
(`EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9`, form `0x28EA` "REF Voltage Configuration", offsets
`0x1c9`-`0x1d2`) have **PEI-phase reader and staged-write paths in two vendor VR-controller PEIMs**:

| Consumer   | File GUID                              | PEIM in FV        | ROM offset             | Setup fields read                                                     | Effect                                                                                                |
| ---------- | -------------------------------------- | ----------------- | ---------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `ISL69247` | `6E6D2018-28D0-4AD3-BEB3-B48E4981707D` | PEI FV `0xE02000` | TE image at `0xED2C74` | `0x1c9`, `0x1ca`, `0x1cc` (VCORE) and `0x1cd`, `0x1ce`, `0x1d0` (GFX) | writes VR register index `0x21` (mV) and `0x28` (droop/loadline), plus `0x23`, `0xF0`, `0xC7`, `0xC5` |
| `ISL95712` | `02544BE0-2CB9-4B75-8111-CD8CDC07B837` | PEI FV `0xE02000` | TE image at `0xED3D8C` | `0x1d1`, `0x1d2` (MEMIO)                                              | writes VR register index `0xDF` with the Setup enum code                                              |

Both modules read the **0x1d3-byte `Setup` variable through the PEI Read-Only Variable2 PPI**
(`2AB86EF5-ECB5-4134-B556-3854CA1FE1B4`, `LocatePpi` at `PEI_SERVICES+0x20`, `GetVariable` at
PPI slot `+0x00`), i.e. the code can read the values **before DXE if the PEIMs dispatch**, from the same NVRAM
variable that the hidden BIOS form writes. This is a different route from the CBS offset path
(`AmdSetup+0x6E5/0x6E6` -> `$INV` records `0x1363/0x1364`), which remains producer-only in the
233-module corpus.

Consequence for the OC question: the fixed-voltage controls are not inert form fields. If the
form is made reachable, a value is stored, and the relevant PEIM dispatches, the stored byte can enter
the module's staged register-write path. A next-boot transaction is not established. The physical rail identity, the register semantics, and the
applied voltage remain **unverified** (see Limits).

## Pinned inputs and direct checks

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - size `16,777,216`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Extracted module corpus: `evidence/firmware-audit/20260919-inv-token-consumers/`
  (`census.json`, 233 executable identities, objdump 2.47)
- Setup field inventory (prior, reused): `docs/research/2026-09-20-clv-voltage-control-inventory.md`
- Setup VarStore metadata (prior, reused): `evidence/firmware-audit/20260920-df-init-route/menu-Setup.txt`
  line 2: `VARSTORE id=0x1 name=Setup guid=EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9 size=0x1d3`

Command actually run (single deterministic scanner, read-only):

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py
```

Observed: exit `0`, stderr `0` bytes, machine result `status=PASS`, `350/350` checks passed,
`0` failed. The scanner (a) re-hashes the donor and every module it touches, (b) enumerates all
census modules for the Setup GUID immediately followed by the UTF-16 name `Setup`,
(c) asserts every literal instruction that implements the field consumption, and
(d) re-extracts both consumer TE images **directly from the immutable ROM** (bypassing the
corpus) and re-asserts the same bytes there.

## Module selection (bounded, decisive)

Scanning all 233 extracted images for the `Setup` variable GUID immediately followed by the
UTF-16 string `Setup` - the canonical `GetVariable("Setup", &guid, ...)` argument pair - yields
exactly three modules:

| Module     | Type       | Setup GUID VA | Name VA     | Reads fixed-voltage block?                                    |
| ---------- | ---------- | ------------- | ----------- | ------------------------------------------------------------- |
| `ISL69247` | PEIM (TE)  | `0x9ED36C4`   | `0x9ED36D4` | yes (`0x1c9`-`0x1d0`)                                         |
| `ISL95712` | PEIM (TE)  | `0x9ED455C`   | `0x9ED456C` | yes (`0x1d1`-`0x1d2`)                                         |
| `CpuDxe`   | DXE (PE32) | `0x5E70`      | `0x5E80`    | no - reads `0x1d3` bytes but never touches `+0x1c9`..`+0x1d2` |

20 further modules carry the Setup GUID without the adjacent name pair; they are HII/VarStore
consumers (the `Setup` driver owns the form) and are not `GetVariable("Setup", ...)` call sites.
`Setup-10cc728ae3f8` is the form owner (it holds the `Fix Voltage` / `MEMIO` / `VCORE` /
`Loadline` labels) and is not a voltage consumer.

## Field -> instruction -> action map

`GetVariable` buffer is a stack local; the Setup offsets fold into the frame-pointer
displacements shown below (verified by the literal instructions).

### ISL69247 (buffer base `[ebp-0x178]`, GetVariable DataSize `0x1d3` at RVA `0x2A2`)

| Setup offset |    QID | Field              | Frame slot   | Literal evidence (RVA)                                   | Action                                                |
| ------------ | -----: | ------------------ | ------------ | -------------------------------------------------------- | ----------------------------------------------------- |
| `0x1c9`      | `0x73` | VCORE Fix Voltage  | `[ebp+0x51]` | default `0` @`0x2A9`; `cmp` vs 0 @`0x30A` block          | selects Setup mV vs default 900                       |
| `0x1ca`      | `0x74` | VCORE Voltage (mV) | `[ebp+0x52]` | default `0x384`(900) @`0x28F`; `movzx eax,word` @`0x314` | value staged for register `0x21`                      |
| `0x1cc`      | `0x75` | VCORE Loadline     | `[ebp+0x54]` | default `2` @`0x2AC`; `movzx eax,byte` @`0x36B`          | indexes table `{0,20,30,40,50,60}` -> register `0x28` |
| `0x1cd`      | `0x76` | GFX Fix Voltage    | `[ebp+0x55]` | default `0` @`0x2B0`; `cmp` vs 0 @`0x3AD`                | selects Setup mV vs default 900                       |
| `0x1ce`      | `0x77` | GFX Voltage (mV)   | `[ebp+0x56]` | default `0x384`(900) @`0x293`; `movzx eax,word` @`0x3B2` | value staged for register `0x21`                      |
| `0x1d0`      | `0x78` | GFX Loadline       | `[ebp+0x58]` | default `2` @`0x2B3`; `movzx eax,byte` @`0x403`          | indexes the same table -> register `0x28`             |

Fixed writes around the two blocks (register index staged in mailbox register `0x66`):

- `0x61 <- 0`, `0x62 <- 3` (initialisation, `0x2E1`/`0x2E8`);
- page/rail select: command `0x00` written with `0` then `1` (`[ebp+0x73]` flag, helper `0x5D3`);
- `0x21 <- VCORE/GFX mV`; `0x23 <- 0`; `0x28 <- loadline table value`;
- `0xF0 <- read-modify-write`, bit `0x30` set when the matching `Fix Voltage` is enabled and
  cleared when disabled;
- `0xC7 <- 0xEA0B` (VCORE) / `0xEA8B` (GFX); `0xC5 <- 0x0B` when loadline == 2 else `0x08`.

### ISL95712 (buffer base `[ebp-0x1e0]`, GetVariable DataSize `0x1d3` at RVA `0x266`)

| Setup offset |    QID | Field             | Frame slot  | Literal evidence (RVA)                             | Action                               |
| ------------ | -----: | ----------------- | ----------- | -------------------------------------------------- | ------------------------------------ |
| `0x1d1`      | `0x79` | MEMIO Fix Voltage | `[ebp-0xf]` | default `0` @`0x26D`; `cmp` vs 0 @`0x2B6`          | enable test                          |
| `0x1d2`      | `0x7a` | MEMIO Voltage     | `[ebp-0xe]` | default `0x1e`(1.35 V) @`0x270`; `mov al` @`0x2BC` | enum code written to register `0xDF` |

Enabled path writes the stored enum code to register `0xDF` and then ORs bit 0 into the staged
value; the disabled path writes the default `0x1e` (1.35 V) instead. A follow-up helper stages
`0x65 <- 0x9E`, `0x66 <- 0xDE`, `0x63 <- 0x82`, `0x60 <- 0xC0` (RVA `0x3F3`/`0x401`/`0x419`).

## Transport (observed instructions, inferred protocol)

Both modules do not touch a VR controller directly. They stage a transaction in a mailbox and
then perform x86 port I/O:

- write helper `0x6ED` stages `0x65 <- 0xC0`, `0x66 <- target register`, `0x70/0x71 <- 2-byte
little-endian value`, `0x63 <- 3`, `0x60 <- 0xC0`, then polls status bit `0x40` (max 10
  retries) and writes `0x60 <- 8`;
- the mailbox is reached through x86 ports `0x2E`/`0x2F` and `0xA20`/`0xA21`/`0xA22`
  (Super-I/O/EC configuration + data window), with the usual `0x87,0x87` unlock sequence.

**Inference (not hardware-verified):** the register indices match PMBus-style commands
(`0x00` page select, `0x21` output-voltage command, `0x23` calibration offset, `0x28` droop),
and the two ISL69247 blocks differ by the page flag, which is consistent with a multi-rail
controller. Register semantics, the mailbox chip, and the actual rail voltages are **not**
proven by this evidence.

## Limits and what would settle it

- Evidence class: `static-analysis` over `observed-bytes` (module bytes, hashes, exact
  instruction encodings). No firmware execution, no emulator, no board, no NVRAM write.
- Dispatch is inferred from the FFS state (`F8`, valid), PEIM type, placement in the main PEI
  FV, and the parsed depex (`F894643D-…` = memory-discovered PPI, `01F34D25-…`, AND). Runtime
  dispatch and the resulting VR register traffic are **unrun**.
- Physical rail identity for `VCORE`/`GFX`/`MEMIO`, the mV/enum-to-voltage conversion inside
  the controller, and any safety rating are **unknown**. No voltage value is recommended.
- Decisive next test: a runtime trace of the mailbox ports (`0x2E/0x2F`, `0xA20`-`0xA22`) on a
  board that boots with a modified Setup variable, or an independent readback of the VR
  registers with the field at Enabled versus Disabled, on the existing recovery-capable setup.

## Evidence and rollback

- Scanner: `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py`
- Machine result: `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/fixed-voltage-consumer-result.json`
- Literal stdout/stderr/exit: `verifier.stdout`, `verifier.stderr`, `verifier.exit`
- Manifest: `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/SHA256SUMS.final`
- Action log: `docs/action-logs/2026-09-20-clv-fixed-voltage-consumer.md`

Rollback: delete only these uniquely owned files. The donor, the pinned corpus, and all prior
evidence remain unchanged.
