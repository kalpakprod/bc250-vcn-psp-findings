# CH347T programmer MCP and CLI evaluation

> Status clarification 2026-09-27: the final section "Runtime trial result" supersedes the earlier TRIAL/unrun statements for the recorded 2026-09-11 read-only capture. It does not establish current hardware state or authorize another capture/write.

## Question and scope

The operator referred to `AmsProc`/`AmsProg`; no such name was found in the local BC-250 corpus or local IMSProg source. The provided screenshot and host device identify the likely intended program as **IMSProg**. This note evaluates whether an MCP server exists for that programmer and whether a CLI path is better for read-only chip identification and full reads.

Date: 2026-09-11T06:03:31.927652+00:00
Project: `/home/OWNER/orca/projects/bc250`

## Findings

### IMSProg

- Installed package: `imsprog 1.9.1-1`, license `GPL-3.0-only`; package metadata was read with `pacman -Qi`, no package was installed by this evaluation.
- Local source root: `/home/OWNER/src/imsprog-1.9.1-native/src/IMSProg-1.9.1`; README SHA-256 `6c5c1327082f3ad087a9000058490f38d7394075bd13f7135824a0286a4689b9`.
- Manual: `/usr/share/man/man1/IMSProg.1.gz`, IMSProg 1.9.1; SHA-256 `6b1ff18271a175c16371dc1253875e22045b6e352489bed8f094e465ecb0bfec`. Its synopsis is only `IMSProg`; it describes a Qt GUI.
- Source `IMSProg_programmer/main.cpp` creates `QApplication`, `MainWindow`, and enters the GUI event loop. `mainwindow.cpp` accepts an optional `.bin` argument to preselect/open a file buffer, but no documented CLI Detect/Read/Verify/Erase/Write operation or JSON/MCP endpoint was found.
- IMSProg supports CH347T and W25Q128BV in its GUI/database. It remains a GUI fallback, not an MCP/CLI automation backend.

### MCP-server search

- Local search found no `AmsProc`, `AmsProg`, or IMSProg MCP implementation.
- GitHub repository search was attempted for `IMSProg MCP`, `AmsProc MCP`, `AmsProg MCP`, `CH347T MCP`, `mcp-server flashrom`, `mcp flashrom programmer`, `mcp spi programmer`, and related terms. The first searches returned no relevant implementation. One `CH341 MCP` result was an unrelated Android/software-SPI repository without evidence of IMSProg/CH347T support. Later GitHub API requests reached the unauthenticated rate limit (HTTP 403).
- General web search is unavailable because the Serper API key is not configured. Therefore the conclusion is bounded: **no dedicated maintained IMSProg/CH347T MCP server was found in the inspected local corpus and GitHub repository-search scope**, not a universal proof that none exists.

### flashrom CLI

- Arch repository metadata exposes `flashrom 1.8.0-1`, GPL-2.0-or-later, package URL `https://www.flashrom.org/`; the package is available but was not installed or run in this evaluation.
- Release page `https://github.com/flashrom/flashrom/releases/tag/v1.8.0` resolved to commit `90b6b4376c7480a223e7bb5642e7116315ac6d09`.
- Pinned source `https://raw.githubusercontent.com/flashrom/flashrom/90b6b4376c7480a223e7bb5642e7116315ac6d09/programmers/ch347_spi.c`, retrieved 2026-09-11, SHA-256 `dd9f0863e4b8e79d3b6f115f0b98dedbe1f1481047ef511096195650bdd74efe`, contains the native `ch347_spi` backend.
- The backend explicitly registers `VID:PID 0x1A86:0x55DB` as `CH347T`, uses SPI interface 2 and endpoints `0x06/0x86`, supports 4-byte SPI, and offers `60M`, `30M`, `15M`, `7.5M`, `3.75M`, `1.875M`, `937.5K`, and `468.75K` speeds. Default is 15 MHz.
- Pinned Winbond source `https://raw.githubusercontent.com/flashrom/flashrom/90b6b4376c7480a223e7bb5642e7116315ac6d09/flashchips/winbond.c`, SHA-256 `5f964a9e70ccfff15e96948638a7f8ab980a24fb629fb1d5ab996fafdfeffa6a`, has a 16 MiB/256-byte-page `W25Q128.V` entry with 2.7–3.6 V range and RDID probe. It is the database family match for the operator-selected W25Q128BV; exact JEDEC ID must still be read from the chip.

## Operator-provided hardware configuration

- Programmer: `CH347T` (operator supplied).
- Chip selector screenshot: `SPI_FLASH / WINBOND / W25Q128BV / 16 M / page 256 / block 64 K / 3.3 V / 4byte No`.
- Host USB: `1a86:55db`, WCH/QinHeng `USB To UART+SPI+I2C`, `/dev/ttyACM0`.
- Evidence: `evidence/programmer/imsprog-preflight.json` and `evidence/programmer/imsprog-chip-selection.png`.
- Board-view maps `J4004` to SPI and names BIOS_A1 as an MXIC 16 MiB 3 V device. This conflicts with the operator's current Winbond marking, so physical marking/orientation and the selected target chip take precedence and must be verified. The CAD remains a wiring lead, not live identity.

## Decision

- **IMSProg: `KEEP` as GUI fallback.** It can operate CH347T manually, but its documented interface is GUI-only and it has no MCP server in the inspected source.
- **flashrom: `TRIAL` as the preferred CLI read-only route.** Native CH347T support and explicit `-r` operation make it easier to automate, hash, compare, and feed into the existing firmware audit than GUI screenshots. Runtime compatibility with this exact CH347T/clip/chip is not yet verified.
- **No custom MCP wrapper yet.** A wrapper would add another untrusted layer. First test flashrom directly with a read-only command; a narrowly whitelisted wrapper can be considered later if repeated CLI orchestration is needed.

## Planned read-only trial (not executed)

After the operator confirms the board is fully unpowered and the clip/chip orientation is checked:

1. Install or otherwise obtain the pinned Arch `flashrom 1.8.0-1` binary. Record the package hash and `flashrom --version`; do not silently use another version.
2. Probe without write flags, preferably at a conservative speed for an in-circuit clip:
   ```text
   flashrom -p ch347_spi:spispeed=1.875M
   ```
   The exact detected JEDEC/manufacturer/model must be recorded. Stop on a mismatch or ambiguous ID.
3. Take two complete reads to distinct new files using only `-r`:
   ```text
   flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-a.bin
   flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-b.bin
   ```
4. Hash and compare the two files byte-for-byte. Stop if they differ.
5. Run `scripts/firmware_audit.py` independently on each read and compare each with `dump/2.bin`. Preserve all hashes and changed ranges.
6. Only after two matching reads and metadata review, decide whether to build a new APCB-only candidate from `read-a.bin`. No flash approval is implied.

The command examples are a plan only. No command above was executed in this evaluation. Never use `flashrom -w`, erase options, status-register write options, or `Auto` in the first trial.

## JTAG separation

The J2 CAD mapping is a separate read-only debug path. It must not be mixed with SPI identification. Before JTAG attach, verify J2 population, +1.8 V, pin 1, adapter/protocol, reset behavior, and debug state. `J4004` remains the SPI header.

## Open coverage

- GitHub API rate limit prevented exhaustive repository search; no direct web search was available.
- `flashrom` package was not installed/run, so exact local binary support and chip detection remain unverified.
- Board power isolation, chip marking/orientation, clip contact, JEDEC ID, two fresh reads, and SPI signal integrity remain unverified.

## Runtime trial result

The operator confirmed the board was fully unpowered, the BIOS battery was removed, and only the CH347T was connected. The Arch package was downloaded to a temporary user-owned directory and verified with `gpgv` against the local Arch keyring. Package SHA-256: `b3804df8cf3a44461deb03bd0ac2edc37d616edc28eb95a9a0d3b3c16cc48316`; package signature key fingerprint: `05C7775A9E8B977407FE08E69D4C5AA15426DA0A`; extracted binary SHA-256: `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`.

Read-only runtime results:

- `flashrom v1.8.0 (git:v1.8.0)` executed through `ch347_spi` at `1.875M`.
- Probe found `Winbond W25Q128.V` (`16384 kB`).
- Two complete `-r` captures completed with exit 0. Both are byte-identical to each other and to `dump/2.bin`; common SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Full parser, NVAR, IPDS, and executable extraction checks pass on the fresh reads.
- No `-w`, erase, write-protection change, status-register write, register mutation, JTAG target-memory write, or flash occurred.

Runtime decision: **`ADOPT` for this bounded read-only CH347T capture route**, with the exact pinned binary and low-speed command. This does not imply flash safety or candidate bootability. IMSProg remains **`KEEP` GUI fallback**.

Evidence:

- Probe log: `evidence/programmer/probe-20260911.txt`, SHA-256 `c89588ff0a4889bf03d9ab2f7b12e0c56eb891c5f8746b5793f0664944c7cd1e`.
- Read manifest: `evidence/programmer/reads/20260911/manifest.json`, SHA-256 `80b34cb2be1706abeac499d95cc4ae1d0c55b05183add75b015ad85780cccb60`.
- Action log: `docs/action-logs/2026-09-10-programmer-preflight.md`.
