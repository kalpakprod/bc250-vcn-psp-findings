# Habr/PT "Ящик пAMDоры": TOCTOU on BC-250 SPI — the glitch-free PSP bypass (2026-09-23)

> Статус на 2026-09-27: ИСТОРИЧЕСКИЙ ОБЗОР ВНЕШНЕГО ИССЛЕДОВАНИЯ. Чужой результат не подтверждает работу нашего v001. Указанные ниже первоочередные действия, порядок чтений и аппаратные требования не являются актуальным планом или разрешением на подключение.
> Реестр расхождений: `docs/research/2026-09-27-toctou-document-audit.md`.

Source: https://habr.com/ru/companies/pt/articles/979470/ (Positive Technologies, 2026-01-22,
author Алексей Шалпегин), reproducing CCC 2025 talk "Opening pAMDora's box"
(ProjectSomnacin; payload examples: github.com/ProjectSomnacin/SomnacinDumper). Found via
the community guide's EMFI thread (porocyon: "already done before per Habr"). ALL of it
was done ON THE BC-250 BOARD. Nothing here needs EMFI, soldering to the die, or a
parameter sweep.

## 1. The TOCTOU attack (PROVEN on BC-250: Fedora booted)

Facts from the article, all on BC-250:

- The PSP boot ROM reads SPI in Single-IO mode (`03`), 4 bytes per command.
- **The body of EVERY PSP module is read from SPI TWICE.**
- Dual-flash TOCTOU: a Raspberry Pi Pico 2 sits on the SPI bus (its PIO state machines
  sniff every command; a trigger = the first read of the target module's body), and
  switches Chip Select between TWO flash chips: patched data on the first read,
  original on the second (order determined experimentally; "patched first" worked).
- They replaced the BL_PUBLIC_KEY module (body at `0x9DAE00`, 0xAE0 B in their dump;
  public key with id **39BF** = our cross-image anchor `39bfc192…`) with their own
  RSA-2048 key, re-signed TRUSTED_OS and DRIVER_ENTRIES with it (PSPTool crypto:
  **PSS / MGF1-SHA256 / salt 32** — the exact scheme we solved on 2026-09-19), fixed
  SHA-256 in headers.
- Result: **the board booted Linux with the re-signed PSP modules** — PSP code execution
  obtained, no glitch, no fuse, no die work.

Fit with our artifacts: our glitch-signed candidate
`BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin` (`91de01eb…`) IS the patched dump for
this attack — same key-module spoof (t50 slot0 `39bfc192…` -> ours `b36ad5af…`), same
signing scheme, plus the rebuilt `0x24`/`0x45` VCN unlock carriers. The TOCTOU rig
removes the ONE thing the candidate could not pass alone: the on-die ROM hash anchor.

## 2. The rig doubles as the missing observation channel

- The PIO sniffer sees EVERY PSP SPI read: a complete boot-time access log without
  UART — the J5/UART open question becomes non-blocking for the PSP boot phase.
- The same Pico reads/writes BOTH flash chips over USB (their code included): a
  programmer AND an emulator in one, no external programmer needed mid-session.
- A debug channel: PSP code outputs 16-bit words by READING SPI addresses in a watch
  range (`03 Dx…` pattern; 0x27000000-mapped flash as the exfil medium — reads of
  chosen addresses are visible on the bus). Their IPL dump (~40 KB, encrypted) was
  extracted this way.

## 3. Privilege escalation and the PSP ROM dump (both proven)

- IPL syscall backdoor: _*SVC `0xF2` = hardware register write, `0xF3` = read
  (0x3* addresses only)_* — CCP DMA registers are reachable this way.
- Privilege escalation: rewrite the SVC handler pointer in the IPL descriptor table
  (`0x73000`, slot `0x3C`) + queue a CCP descriptor via svc_write → supervisor mode
  (SomnacinDumper `ABL0_C02/start.S` pattern).
- **PSP ROM dump: CCP DMA chain programmed BEFORE a CPU reset; the reset re-exposes
  ROM at `0xFFFF0000`; DMA copies 0x10000 B to RAM; output via the SPI debug channel.**
  Their dump matched the 4700S bootrom byte-for-byte ("полное совпадение").
- Consequence for us: the ROM (hash anchor + verifier code) is READABLE — F4's "only
  unread surfaces" claim is obsolete; V2 (verifier bugs) and V3 (anchor semantics) can
  be answered from the ROM binary itself, and a fresh PSP ROM dump for OUR board is a
  session deliverable.

## 4. Boundaries

- Desktop Ryzen 5600: NOT vulnerable (Quad-mode, 64-byte cached reads, single read).
- Vulnerable: PS5-derived boards — BC-250 and 4700S Kit (exactly our hardware).
- ABLx modules do not verify in stock PSPTool unless signed-over-COMPRESSED bytes are
  checked (their `get_signed_bytes` fix) — matters for any ABL re-signing.
- P4.00/P5.00 community notes ("SMU commands differ on P5.00", rescuemei: SMU fw is
  UNencrypted, signature-checked on load only) — consistent with our robin_5 finding.

## 5. What this changes in the plan

1. NEW PRIMARY lane V7' (SPI TOCTOU, Pico 2 dual-flash): deterministic, proven on this
   exact board, no EMFI sweep, no soldering to the die. A SOIC-8 clip / J4004-rig
   replaces the "glitch" entirely; the board stays stock under the rig.
2. V7 EMFI demoted to fallback (only if the rig hits unexpected ROM-side anti-TOCTOU).
3. The flash session (D1) reframed: with the rig, the PSP spoof needs NO flashing at
   all; the programmer+sniffer+debug roles all live on the Pico.
4. New offline tasks: (a) build the Pico 2 firmware (their PIO programs are printed in
   the article; SomnacinDumper has payloads); (b) produce the dual-image split for
   `91de01eb…` (patched KDB/key reads vs original rest); (c) after code exec: dump OUR
   PSP ROM, decode the anchor check, then decide VCN release from inside the PSP
   (TEE/fTPM machinery) versus our carriers.
5. F1 (signature story) becomes fully demonstrable; F2 (VCN) gets a second, stronger
   road: PSP-side code exec + our rebuilt unlock carriers in the same image.
