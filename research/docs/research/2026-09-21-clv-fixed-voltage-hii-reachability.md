# Exact-CLV Setup voltage-form reachability audit

Date: 2026-09-21 (Asia/Almaty)  
Target: unmodified pinned CLV BIOS donor only; static HII/IFR source audit. No BIOS/NVRAM edit, unlock, AMIBCP run, or hardware access.

## Result

The raw Setup HII package contains `Advanced` form `0x2712` with a `REF` to voltage form `0x28EA`. That reference is inside a two-byte `SUPPRESS_IF` whose next opcode is the standard `EFI_IFR_FALSE_OP` (`47 02`). Under the standard IFR meaning, the condition is false, so this one scope does not suppress the reference. The pre-existing decoder prints `HIDDEN REF` because it labels any REF inside a suppress scope without evaluating the expression; that label is not a visibility verdict.

Inside form `0x28EA`, VCORE/GFX fixed-voltage numeric fields have valid `EQ_ID_VAL` suppression conditions tied to their own enable questions. The MEMIO voltage selector does **not** have the same well-formed condition: its scope contains `47 06 79 00 00 00`, which is opcode `EFI_IFR_FALSE_OP` with noncanonical length 6, not opcode `EFI_IFR_EQ_ID_VAL_OP`. Do not rewrite this as “MEMIO voltage appears when MEMIO Fix Voltage is Enabled” from the `0x79` payload bytes. The form-level `GRAY_OUT_IF` also has a noncanonical six-byte `FALSE` record; the existing parser's `GRAY` marks scope membership only. Exact AMI Setup-browser treatment of these malformed records and real runtime visibility are not established here.

**AMIBCP visibility alone is insufficient evidence of native Setup reachability or edit/application.** A utility preview or visibility flag does not demonstrate condition evaluation in the firmware's HII browser, successful RouteConfig/NVRAM save, reset behavior, or PEI use. AMIBCP was not run; no binary was found on `PATH` by `command -v`.

## Exact source and method

- Immutable donor: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; size `16,777,216`; SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Existing extracted Setup PE32: `evidence/firmware-audit/20260919-inv-token-consumers/Setup-10cc728ae3f8.bin`; size `169,056`; SHA-256 `10cc728ae3f8abec5bdf206b272eb3806ef4b7f90f2bc3f887b33c02c30da152` (matches its exact-corpus census identity).
- Forms package: package type `2`, offset `0xFB54` within that PE32, declared length `15,398` (`0x3C26`); body SHA-256 `d493853c2c618c7586ad60870f230962dad96ad909a904b92541980b0a054522`.
- Existing read-only IFR output: `evidence/firmware-audit/20260920-df-init-route/menu-Setup.txt`, SHA-256 `18791e3a2a50b89cf8997ec4bebfd944e3abe7a25a9ee03ba3119de0a562c5ed`; package index `menu-Setup-packages.json`, SHA-256 `a9be0a7224c5365abbb678781bda1f632a45b048a063882762c6da3aced814cc`; source parser `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`, SHA-256 `480aa6fc70ed12e8d1dbec2c32dfb45ddadcd7c2f9075ceac6dad6486bc50ebb`.
- Directly inspected the package bytes at the listed IFR offsets; a bounded read-only Python check verified the package coordinates, parent REF bytes, selected scope/question records, and 8 question records (`status=PASS`, exit `0`). Existing output and raw records were cross-checked; no existing evidence file was rewritten.
- Standard-opcode reference only: local imported EDK II revision `04679c85b43cd11bd076a9196b77864fde2091b7`; `UefiInternalFormRepresentation.h` defines `FALSE=0x47`, `EQ_ID_VAL=0x12`, option default bits `0x10/0x20`; its SetupBrowser expression code maps `FALSE` to Boolean false. This is a semantic reference, **not** proof that the exact AMD/AMI Setup browser accepts the noncanonical records in the same way.

## Form path, scopes, and exact field conditions

The Setup forms package names the `Setup` VarStore (`GUID EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9`, size `0x1D3`). The package-local route is `Setup (0x2710) -> Advanced (0x2712) -> Voltage Configuration (0x28EA)`.

| IFR location                    | Raw scope / expression bytes                                                                                          | Direct interpretation                                                                                                              | Reachability conclusion and qualification                                                                                                                                                                                        |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Advanced form's REF to `0x28EA` | `0x7B8: 0A 82` (`SUPPRESS_IF`, scoped); `0x7BA: 47 02` (`EFI_IFR_FALSE_OP`); target REF `0x7E9..0x7F7`, form `0x28EA` | Standard constant-false suppress predicate.                                                                                        | Under standard IFR semantics this REF is not suppressed. Existing `HIDDEN REF` label is lexical scope membership only. Main Setup/AMITSE rendering was not run.                                                                  |
| Voltage form's outer grey scope | `0x2321: 19 82` (`GRAY_OUT_IF`, scoped); `0x2323: 47 06 EC 00 01 00`                                                  | Operand byte is `EFI_IFR_FALSE_OP`; its record length/scope payload is noncanonical for the standard two-byte FALSE record.        | The parser marks all child questions `GRAY`, but does not evaluate it. Treat runtime gray/edit state as **unresolved** until the target browser's behavior is observed; do not treat the lexical tag as proof of a locked field. |
| VCORE voltage QID `0x74`        | `0x234A: SUPPRESS_IF`; expression `0x234C: 12 06 73 00 00 00` (`EQ_ID_VAL`, QID `0x73` equals `0`)                    | QID `0x73` is VCORE Fix Voltage.                                                                                                   | Under standard IFR semantics the 900-mV numeric field is suppressed while VCORE Fix is Disabled; it is exposed by the form logic when that toggle is Enabled (`1`), subject to unresolved outer gray/browser execution.          |
| GFX voltage QID `0x77`          | `0x23CF: SUPPRESS_IF`; expression `0x23D1: 12 06 76 00 00 00` (`EQ_ID_VAL`, QID `0x76` equals `0`)                    | QID `0x76` is GFX Fix Voltage.                                                                                                     | Under standard IFR semantics the 900-mV numeric field is suppressed while GFX Fix is Disabled; it is exposed by the form logic when that toggle is Enabled (`1`), subject to unresolved outer gray/browser execution.            |
| MEMIO voltage QID `0x7A`        | `0x2454: SUPPRESS_IF`; expression `0x2456: 47 06 79 00 00 00`                                                         | This is `EFI_IFR_FALSE_OP` (`0x47`) with an extra payload containing `0x79`, **not** an `EQ_ID_VAL` (`0x12`) comparing QID `0x79`. | The bytes do not support a claimed MEMIO-enable condition. A standard FALSE interpretation would not suppress this selector; exact AMI runtime treatment of the noncanonical length is **unresolved**.                           |

Thus the unmodified donor does **not** provide evidence for a hidden-enabling code or password gate on the voltage form's REF: that exact REF sits under a constant-false suppress expression. The default enable bytes are nevertheless zero, so the VCORE/GFX numeric values are conditionally suppressed under the decoded standard predicates. The MEMIO condition must remain separately qualified rather than copied from the VCORE/GFX pattern.

## IFR defaults versus stored donor bytes

Default flags on ONE_OF options use `EFI_IFR_OPTION_DEFAULT=0x10` and `EFI_IFR_OPTION_DEFAULT_MFG=0x20`. Numeric values are not recommendations or evidence of applied voltage.

| Question / Setup field                       | IFR default and options                                                              | Exact pinned donor bytes (Setup body base `0xD95`) |
| -------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------- |
| QID `0x73`, `Setup+0x1C9`, VCORE Fix Voltage | Disabled `0` option flags `0x30` (standard + manufacturing default); Enabled `1`     | `00` at ROM `0xF5E`                                |
| QID `0x74`, `Setup+0x1CA`, Voltage(mV)       | Numeric `700..1250`, step `1`; IFR DEFAULT id `0`, type `u16`, bytes `84 03` = `900` | `84 03` at ROM `0xF5F`                             |
| QID `0x75`, `Setup+0x1CC`, VCORE Loadline    | 0.3 Ohm option code `2` has flags `0x30` (default)                                   | `02` at ROM `0xF61`                                |
| QID `0x76`, `Setup+0x1CD`, GFX Fix Voltage   | Disabled `0` option flags `0x30`; Enabled `1`                                        | `00` at ROM `0xF62`                                |
| QID `0x77`, `Setup+0x1CE`, Voltage(mV)       | Numeric `700..1250`, step `1`; default `900` (`84 03`)                               | `84 03` at ROM `0xF63`                             |
| QID `0x78`, `Setup+0x1D0`, GFX Loadline      | 0.3 Ohm option code `2` has flags `0x30` (default)                                   | `02` at ROM `0xF65`                                |
| QID `0x79`, `Setup+0x1D1`, MEMIO Fix Voltage | Disabled `0` option flags `0x30`; Enabled `1`                                        | `00` at ROM `0xF66`                                |
| QID `0x7A`, `Setup+0x1D2`, Voltage           | 1.35 V option code `0x1E` has flags `0x30` (default)                                 | `1E` at ROM `0xF67`                                |

These are values in the pinned unmodified donor, not a readback of a live board's mutable `Setup` variable. This audit did not change any value.

## AMIBCP answer and evidence boundary

**No—visibility alone in AMIBCP cannot establish the intended unmodified-CLV Setup behavior.** The exact Setup HII package already contains the form and parent REF; a third-party tool's view of a hidden/gray form is not the firmware browser. Clearing an editor's visibility bit would not prove that a raw IFR condition is satisfied, that the target browser parses the noncanonical `FALSE` records as intended, or that changes are saved to the `Setup` variable and applied. Conversely, the lexical `HIDDEN`/`GRAY` tags do not prove that the REF is hidden or that the conditions evaluate true.

Tool status: the existing AMIBCP inventory says no executable is available locally; this turn's `command -v AMIBCP AMIBCP64 amibcp amibcp64` returned no path. No AMIBCP operation, IFR patch, unlock, NVRAM operation, Setup interaction, PEI/PPI/transport trace, or hardware test was done.

**Static conclusion:** form and question logic are byte-present; VCORE/GFX numeric settings require their corresponding enable QID to be nonzero under the valid `EQ_ID_VAL` predicates. The MEMIO selector has a noncanonical constant-false scope, not a proven enable dependency. **Runtime conclusion:** exact HII browser presentation/editability and persistence are unrun.

## Reproduction and evidence ledger

Read-only commands/checks used:

```sh
sha256sum evidence/donor/retroweb-20260916/BC250_5.00_clv.bin \
  evidence/firmware-audit/20260919-inv-token-consumers/Setup-10cc728ae3f8.bin \
  evidence/firmware-audit/20260920-df-init-route/menu-Setup.txt \
  archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py
sed -n '60,105p' evidence/firmware-audit/20260920-df-init-route/menu-Setup.txt
sed -n '680,724p' evidence/firmware-audit/20260920-df-init-route/menu-Setup.txt
command -v AMIBCP AMIBCP64 amibcp amibcp64
```

A bounded inline Python check read package type `2` at PE32 offset `0xFB54`, checked the exact raw condition/REF/question record ranges shown above, and reported `status=PASS`, `records=30`, `questions=8`, exit `0`; its captured stdout JSON was stored only in `/tmp` (`/tmp/clv_hii_reachability.json`, SHA-256 `233aad0463a88634dcee32885e96e5413068f57be89532855e26ec1674bacbea`). It is not a project artifact and adds no parser/dependency. The exact donor and extracted Setup PE32 hashes matched the current census identity; `menu-Setup.txt` question/default lines matched the raw package fields.

The prior menu report and parser were treated as maps, not semantic verdicts: the existing parser's `HIDDEN` / `GRAY` flags are assigned from an active scope stack (`SUPPRESS_IF` / `GRAY_OUT_IF`) and do not evaluate the expression. For standard opcode names, the imported EDK2 header identifies `0x47` as FALSE and `0x12` as EQ_ID_VAL; its expression handler returns Boolean false for FALSE. This does not substitute for execution of the exact AMI browser.

Checks: donor identity **passed**; exact package/census identity **passed**; form/ref/question/default raw-byte readback **passed**; standard opcode cross-reference **passed**; actual browser visibility/editability/save, AMIBCP behavior, and firmware execution **unrun**. No source or binary was written.
