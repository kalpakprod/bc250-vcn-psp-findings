# Runbook: making the BC-250 PSP ROM accept a key we control

Purpose: execute the **one** remaining step of the VCN unlock path. Everything upstream of it
is built and verified offline; see
`docs/research/2026-09-19-psp-signature-scheme-solved.md` §7.

Scope and prerequisites

- Board: BC250-01, base `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  (`ea5781049160ab33…`), SPI `W25Q128.V`, CH347T programmer + clip already proven.
- Staged image: `candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin`
  (`91de01eb7cb8e970…`), verified: 14/14 containers PASS, both lock carriers under our kid.
- Skills: `artifact-verification`, `uefi-dxe-validation`. Memory: `memory/firmware-audit.md`
  (the 2026-09-19 SOLVED/delivery entries), `memory/instincts/no-flash-without-recovery.yaml`.

## Route A (preferred — no VRM soldering, and it adds the missing observation channel)

Source: `archives/imported/research-collector/legacy-agent-reach-bc250/repos/SomnacinDumper-CPUCoreMod/`
(SomnacinDumper lineage; GPL-style community project). **Targets BC-250 BIOS 5.0 explicitly.**

| capability                                    | file                                                                                                  | why it matters here                                                                                                                                                                                                                                      |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPI bus injection between mainboard and flash | `PicoModchip/src/spihack.c`, `pio/spi_inject.pio`                                                     | `spihack_inject_payload(addrStart, addrEnd, buf, size)` serves bytes that are **not** in the flash, address-filtered via `spihack_push_filter(addr, doInject)`                                                                                           |
| **LPC POST-code decoder**                     | `PicoModchip/src/postcode.c`, `pio/postcode.pio`, `include/postcode.h` (`LAD[0-3]`, `LFRAME`, `LCLK`) | **the observation channel the 2026-09-17 error audit named as the single deepest missing thing**; works on `TPMS1` (the only populated debug header on this board)                                                                                       |
| Xtensa SMU payload loader                     | `Payloads/smupayload_loader/` (`linkerScript_robin.ld`, `ROBIN=1`)                                    | runs code inside the SMU at boot                                                                                                                                                                                                                         |
| SMU payload, BC-250 branch                    | `Payloads/smupayload_cpayload/main.c` `#ifdef ROBIN`                                                  | writes `0x115A81C = 0x13`, `0x115A870 = 0xFF` — the same two registers this project used for the 8-core unlock                                                                                                                                           |
| measured BC-250 5.0 boot trace                | `sessionlog_bc250.txt`                                                                                | full POST stream from reset through PSP/ABL into x86 (`0xeea6…` → `0xeee00100` → `Done inject!` → `0xea00e0xx` → `0xea000000..0xff` sweep → `0xb000a9xx`/`0xb000acxx` with `SPI:` reads). Their unit stopped at x86 core init — with the codes recorded. |

Hardware: **Raspberry Pi Pico 2** (Pico 1 untested), wired to the SPI bus and, for POST codes,
to `TPMS1` (`LAD0-3`, `LFRAME#`, `LCLK_S4` per `evidence/boardview/bc250-connector-map.json`).
Reset out connects straight to the mainboard reset pin (no MOSFET). No Teensy, no SVI2 tap.

Why this is the cheaper and more informative route than Route B:

1. It needs no soldering to the CPU VRM — only the SPI bus (already exposed via the BIOS
   socket / `J4004`) and an LPC header that is already populated.
2. It gives **POST codes**, converting every future negative from "silent" (the failure mode
   that made the 4700S campaign uninformative) into a localisable code.
3. It already reached the x86 phase on BC-250 5.0 on someone else's unit.

What it does NOT do by itself: change the ROM's stored hash of the AMD public-key entry. Two
sub-hypotheses to test, in order:

- **A1 (read-race / TOCTOU):** if the ROM hashes the key entry on one SPI read and later uses
  a key from a second read, injection can serve different content per read. Test: inject our
  key entry only on the _second_ access to that range; watch the POST stream and then whether
  our carriers validate (a container signed by us that the vendor key would reject).
- **A2 (no race):** the ROM hashes and uses a single read, so injection is equivalent to
  editing flash and fails — then Route A's value is the POST channel, and Route B is required.

## Route B (fallback — voltage glitch)

Source: `archives/imported/research-collector/legacy-agent-reach-bc250/repos/amd-sp-glitch/` (CCS'21,
"One Glitch to Rule Them All"; GPL-3.0; AMD-SB-7044 declares the class unfixed, "Zen 4 and
prior" → Zen 2 in scope permanently).

- Hardware: Teensy 4.0 + LVC07A open-drain drivers on the **SVC/SVD** lines at the CPU VRM,
  reset tap, logic analyser. Not in this project's boardview — the SVI2 test points must be
  located from the VRM datasheet / trace work first.
- Procedure: `attack-code/ParameterDetermination.md` — sweep `waits`/`vid`/`delay`/`duration`
  (paper's own windows: `3108 ≤ delay < 5104`, `920 ≤ duration < 950`), `count=1000` per
  batch in a loop; success = the `hello-world` payload writes to SPI.
- Tools: `attack-code/make_key_entry.py` (key entry), `make_epyc3_pl.py` (install key, re-sign
  firmware), `payloads/{hello-world,dump-sram,get-secret-fuses,decrypt-ikek}`.

## Exact wiring for Route A (from the repo's own sources)

Pico 2 GPIO numbers come from `PicoModchip/src/main.c` (`PIN_*`); board pins from
`evidence/boardview/bc250-connector-map.json` (CAD-derived, verify on the board).

| Pico GPIO  | function                              | board point                                         |
| ---------- | ------------------------------------- | --------------------------------------------------- |
| 4, 5, 6, 7 | `LAD0..LAD3` (`PIN_LPC_BUS_BASE 4`)   | `TPMS1` pins 11, 10, 8, 7                           |
| 8          | `LCLK` (`PIN_LPC_LCLK`)               | `TPMS1` pin 1 (`PCLK_S4`)                           |
| 9          | `LFRAME#` (`PIN_LPC_LFRAME`)          | `TPMS1` pin 3                                       |
| 10         | SPI MOSI                              | SPI bus `SB_SPI_DI` (`J4004` pin 5)                 |
| 12         | SPI CLK                               | `SB_SPI_CLK` (`J4004` pin 4)                        |
| 13         | `CS_MAINBOARD`                        | `SB_RSPI_CS#` (`J4004` pin 3)                       |
| 17         | `CS_CHIP`                             | flash chip CS (lift or cut from the mainboard side) |
| 18         | SPI MISO                              | `SB_SPI_DO` (`J4004` pin 6)                         |
| 16         | target reset (active-high, no MOSFET) | mainboard reset pin                                 |
| 15         | `PROGRAM#` control                    | `J4004` pin 8                                       |
| GND        | ground                                | `TPMS1` pin 2 or `J4004` pin 2                      |

Constraints enforced by the firmware (`_Static_assert` in `main.c`): `CLK+1 == CS_MAINBOARD`
(12+1=13), `MOSI+2 == CLK` (10+2=12). Do not change the Pico GPIO numbers without
changing the asserts.

Build (from the repo root of `SomnacinDumper-CPUCoreMod`):

```
./run_bc250.sh        # builds smupayload_loader + smupayload_cpayload (ROBIN=1),
                      # then the PicoModchip firmware, flashes the Pico, opens the log
```

Expected on the serial log: `Hello from PicoModchip`, `spihack init ok`,
`postcode_init init ok`, `reset mainboard`, then the `POST: 0x…` stream and, after
`Done inject!`, the `SPI:` read lines. The reference trace is `sessionlog_bc250.txt`.

## Verification (same for both routes)

1. Board still boots stock → confirm the device is passive.
2. Inject/glitch; capture the POST stream (`Route A`) or the logic trace (`Route B`).
3. Boot `BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin`; read back the chip and re-run
   `python3 scripts/psp_ps1_verify.py <readback.bin>` → the two lock carriers must PASS under
   kid `b36ad5af630d9ad4`.
4. `bc250_vcn_mode=2`; check `mmUVD_PGFSM_STATUS` is no longer `0xFFFFFFFF` and
   `ring vcn_dec` no longer fails `-110`.
5. Report each check as passed / failed / inconclusive / unrun.

## Rollback

Restore `evidence/programmer/reads/20260911/read-a.bin` (`83c4e420…`) with the proven
CH347T/`flashrom` flow (VERIFIED + independent readback). Remove the device; the ROM-side
state is untouched by Route A, and Route B is power-cycle-reversible.

## Risks and reopening trigger

- Route A: injecting a wrong range corrupts the boot read → no boot, recover by removing the
  device (flash content unchanged). Route B: a failed glitch is a reboot, and a bad parameter
  can hang the SP until power cycle.
- Reopen this runbook when either the POST stream shows a halt before the key check (Route B
  becomes mandatory), or A1's race test succeeds (no glitch needed).
