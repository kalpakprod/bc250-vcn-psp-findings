# Programmer and flash preflight

## Intent

- Date: 2026-09-10T16:22:16.492853+00:00
- Actor: root agent following the user's request for a safe programmer-backed BIOS workflow.
- Scope: read-only inspection of the operator-provided programmer dump and the existing project scripts/docs. No programmer command, chip write, firmware write, or board power operation was performed.
- Target artifact: `dump/2.bin`.
- Expected effect: establish whether the dump is structurally usable as a stock control and define the gates for a first candidate.
- Rollback: none required for read-only inspection; `dump/2.bin` remains unchanged.

## Observed bytes and structure

- Size: 16777216 bytes (16 MiB).
- SHA-256: `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- `$PSP` at `0x008E0000`, 19 entries; Fletcher32 stored `0x63FFFCC8` matched the independent calculation.
- `$BHD` at `0x00AB0000`, 4 entries; Fletcher32 stored `0xECE7B2E6` matched the independent calculation.
- APCB at `0x00AB1000`, size `0xB70`; byte checksum stored at `+0x10` was `0xF2` and matched the independent calculation.
- `$PS1` gasket metadata at `0x00982000`: total `0x2E50`; `$PS1` policy metadata at `0x009CA400`: total `0x6E0`. Their group layouts parsed as 5 groups (`0x201/0x203/0x210/0x280/0x281`) and 4 groups (`0x210/0x211/0x280/0x281`).
- APCB DFG words at `APCB+0x130` and `APCB+0x16C` are the stock-looking `00 ff 1f 00` values. An in-memory simulation of changing both to `00 ff 7f 00` would require the byte checksum at `APCB+0x10` to become `0x32`; no output file was written.
- The dump hash did not match any of the 105 nearby imported 16 MiB firmware candidates. Treat its provenance as a fresh operator-provided board read until repeated reads are compared.

## Safety decision

- `dump/2.bin` is a usable structural control at the `observed-bytes` layer, not proof of correct chip identity, clip contact, bootability, or recoverability.
- Historical D3-B/D3-C/D3-B2 artifacts and the unsigned gasket builders remain prohibited from flashing. Historical scripts use hard-coded Windows paths and older assumptions and must not be run unchanged against this dump.
- The first contemplated VCN candidate is APCB-only, preserving the signed PSP region and changing no `$PS1` gasket/policy bytes. It remains unbuilt and unapproved.
- Before any write, record the exact programmer, software, chip marking, voltage/adapter, board identity, in-circuit versus removed-chip setup, two matching fresh reads, candidate hash, and explicit approval for that exact hash.

## Next decisive check

Perform two independent full-chip reads with the programmer to new files and compare them byte-for-byte with each other and, separately, with `dump/2.bin`. If the two fresh reads differ, stop and fix contact/voltage/selection before any write.

## Correction (2026-09-10T16:23:35.414835+00:00)

- Post-install contour validation initially failed on `tools/cutter/.venv/.../certifi/cacert.pem`. This is the public CA bundle installed as a dependency, not a project credential or firmware key. The validator did not previously skip generated environments.
- Corrective action: update only the validator's canonical-file scan to skip the explicitly generated Cutter installation directories already covered by `.gitignore`; keep the tracked project contour and secret-like checks unchanged.

## Documentation verification

- `python3 scripts/validate-contour.py`: passed (`contract_copies=4`, `skills=11`, `instincts=6`).
- `git diff --check`: passed.
- No firmware, hardware, programmer, or board state was changed.

## Host-side programmer interface observation (2026-09-11T05:35:46.576793+00:00)

- `lsusb` observed Bus 005 Device 003 `1a86:55db` (`QinHeng Electronics USB To UART+SPI+I2C`), USB bcdDevice `5.44`, three interfaces including a vendor-specific interface. `udevadm` maps it to `/dev/ttyACM0`, vendor `wch.cn`, model ID `55db`; no serial value was read or stored.
- This is a host-side interface observation only. It does not identify the attached flash chip, prove SPI wiring/contact, establish voltage, or authorize a read/write. The exact programmer software/protocol still needs operator confirmation.
- No programmer command, SPI transaction, board power operation, register access, firmware write, or flash occurred.

## Programmer tool availability check (2026-09-11T05:37:06.736483+00:00)

- Host PATH has no `flashrom`, `ch341a_spi`, `ch347`, `minipro`, `openocd`, or `pyocd` executable. The WCH USB interface is present as `/dev/ttyACM0`, but no native read route is selected or invoked.
- Operator must identify the actual programmer application/protocol before any SPI read. No package was installed and no USB/SPI transaction was attempted.

## Programmer identity evidence intent (2026-09-11T05:46:06.063759+00:00)

- Operator provided a GUI screenshot showing programmer chip selection: `SPI_FLASH`, manufacturer `WINBOND`, device `W25Q128BV`, capacity `16 M`, page `256`, block `64 K`, supply `3.3 V`, and `4byte address=No`.
- Host read-only checks observed USB `1a86:55db` (`QinHeng Electronics USB To UART+SPI+I2C`) as `/dev/ttyACM0`; package metadata reports IMSProg `1.9.1-1`, GPL-3.0-only.
- Planned output: preserve a copy of the user-provided screenshot and a redacted metadata manifest. No serial, credential, or access-bearing value will be stored.
- Expected effect: provenance evidence only; no SPI read/write, erase, board power, or firmware mutation.

## Programmer identity evidence result (2026-09-11T05:47:34.676555+00:00)

- User screenshot confirms selected profile `SPI_FLASH / WINBOND / W25Q128BV / 16 M / page 256 / block 64 K / 3.3 V / 4byte No`; preserved copy SHA-256 `cd4a135c9cd1e8f9030f98de21a5a06c31deef5c20569c964c2041b804a4639c`.
- Host confirms CH347T-compatible WCH USB interface `1a86:55db` at `/dev/ttyACM0`; IMSProg package `1.9.1-1`, binary SHA-256 `ab5e02458b4d4567a50cf31f70e9ceee8177c48cae2fead61694c93d591a6368`; no native programmer command was run.
- Machine-readable manifest: `evidence/programmer/imsprog-preflight.json`, SHA-256 `9e56fd4c85169fe6c3ff16a64dcbaf94b72817fc08e6786323d8a8f9845cf13b`.
- Remaining preflight: confirm board is fully unpowered (no `+3.3V_SB`), verify physical chip marking and pin 1, run read-only Detect/JEDEC, and obtain two matching complete reads.

## Programmer MCP/CLI evaluation intent (2026-09-11T06:02:18.381613+00:00)

- Question: whether a dedicated MCP server exists for the user's `AmsProc`/`AmsProg` term (likely `IMSProg`), and whether a command-line route is preferable for CH347T Detect/read.
- Scope: local IMSProg source/package/man page, host USB metadata, and public flashrom v1.8.0 source/release metadata. No programmer command, SPI transaction, package install, or hardware operation will be performed in this evaluation.
- Expected effect: a sanitized research note and plan for a read-only CH347T CLI trial.
- Safety boundary: no `-w`, erase, status-register write, register mutation, or firmware flash.

## Programmer MCP/CLI evaluation result (2026-09-11T06:03:55.775183+00:00)

- No dedicated maintained MCP server for IMSProg/CH347T was found in the bounded local/GitHub repository search; global absence is not claimed because GitHub API rate limiting and unavailable Serper search limit coverage.
- IMSProg 1.9.1 is a Qt GUI. Its source accepts an optional `.bin` file argument but exposes no documented CLI read/detect/JSON/MCP operation.
- `flashrom 1.8.0` is available in Arch metadata and its pinned source has native `ch347_spi` support for VID/PID `1a86:55db` (CH347T), 4-byte SPI, configurable speeds, and a Winbond 16 MiB/256-byte-page family entry.
- Decision: keep IMSProg as GUI fallback; use `flashrom 1.8.0` as a `TRIAL` preferred CLI read-only route, after board-power/orientation confirmation. No flashrom package install or programmer command was executed.
- Research note: `docs/research/2026-09-11-programmer-cli-evaluation.md` SHA-256 `27ffa5eb31b341d45613db4fc87da326decb6b0cde76c78ddb43fd00f6d3cc95`.

## Read-only CH347T CLI trial and flashrom preparation intent (2026-09-11T06:16:26.049553+00:00)

- Operator confirmation received: BC-250 is fully unpowered, BIOS battery removed, and only the programmer is connected. This authorizes the bounded read-only Detect/Read trial, not any write, erase, register mutation, or flash.
- Target: the physically connected SPI flash selected by the operator as `Winbond W25Q128BV`, nominal 16 MiB, 3.3 V. Physical marking and clip orientation are operator-confirmed by statement but the JEDEC ID remains to be measured.
- Existing capability check: `/usr/bin/flashrom` is not installed; Arch metadata offers `flashrom 1.8.0-1`. IMSProg 1.9.1 remains GUI-only for chip operations.
- Install intent: use the repository-native package interface `sudo -n pacman -S --needed flashrom` if non-interactive authorization is available; otherwise stop and request the operator to install the pinned package. This changes only the host package environment, not the target.
- Hardware procedure intent after package verification: run `flashrom -p ch347_spi:spispeed=1.875M` (probe only), then two separate full reads with `-r` into new files under `evidence/programmer/reads/`. No `-w`, erase, status-register write, or automatic write action is permitted.
- Expected result: JEDEC `EF 40 18` / Winbond W25Q128 family and two byte-identical 16 MiB images. A mismatch, unstable ID, USB/clip error, or differing reads is a stop condition.
- Rollback: no target rollback is needed for read-only operations; remove only any failed/incomplete derived capture and restore no firmware. Host package rollback is `sudo pacman -R flashrom` only if explicitly required.

## User-local flashrom preparation fallback intent (2026-09-11T06:17:29.477655+00:00)

- `sudo -n -v` failed, so system installation is not available without an interactive operator password. Do not prompt for or capture credentials.
- Fallback: download the Arch repository `flashrom 1.8.0-1` package to a temporary user-owned directory, verify its package metadata/hash as far as available, extract only the `flashrom` executable and required non-secret files to a temporary user-local prefix, and run `--version`/help before any hardware command. Do not modify `/usr`, `/var`, or global configuration.
- Package URL observed from `pacman -Sp`: `https://stable-mirror.omarchy.org/extra/os/x86_64/flashrom-1.8.0-1-x86_64.pkg.tar.zst`.
- If extraction lacks a runtime dependency or verification is insufficient, stop rather than substitute an unpinned binary.

## Flashrom package verification and USB permission result (2026-09-11T06:21:12.665632+00:00)

- Downloaded Arch package to `/tmp/bc250-flashrom-trial-20260911/flashrom-1.8.0-1-x86_64.pkg.tar.zst`; package size `5,250,510` bytes; SHA-256 `b3804df8cf3a44461deb03bd0ac2edc37d616edc28eb95a9a0d3b3c16cc48316`.
- Downloaded detached signature; `gpgv` with `/etc/pacman.d/gnupg/pubring.gpg` reported a good signature from Arch packager Frederik Schwan, key fingerprint `05C7775A9E8B977407FE08E69D4C5AA15426DA0A`. No secret material was accessed or recorded.
- Extracted package only under `/tmp/bc250-flashrom-trial-20260911/prefix`; executable SHA-256 `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`. `flashrom --version` returned `v1.8.0 (git:v1.8.0)`; help lists `ch347_spi` and read-only `-r`.
- Host USB descriptor read-only observation: bus `005`, device `003`, `1a86:55db`, firmware descriptor `bcdDevice 5.44`, USB interface 2 vendor-specific, bulk endpoints `0x06/0x86`, bus-powered 100 mA. This matches the pinned backend.
- Current user is not in `uucp`; `/dev/ttyACM0` is `root:uucp` mode `660`, and the USB node is `root:root` mode `664`. A libusb transaction may therefore require an operator-approved privileged invocation or a temporary udev permission change. `sudo -n` is unavailable; no privilege prompt or password was captured.
- No SPI transaction, chip Detect, read, write, erase, or flash occurred.

## Privileged read-only probe intent (2026-09-11T06:21:50.494582+00:00)

- Because the current USB node permissions deny the unprivileged account and `sudo -n` is unavailable, use one operator-visible `pkexec` authorization for the exact probe only. The password, if entered by the operator in the system dialog, must not be sent to this agent or stored.
- Exact command: `pkexec /tmp/bc250-flashrom-trial-20260911/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M --flash-name`
- Effect: configure the CH347T SPI interface and issue flashrom's read-only JEDEC probe/name query. It must not write, erase, or alter status registers.
- Expected signal: `Winbond W25Q128.V` or a clear mismatch/error. Expected ID from pinned database: `EF 40 18`.
- Stop conditions: authorization failure, USB permission/claim error, unstable/unknown ID, any suggestion of a write/erase operation, or mismatch with physical target. Full reads remain a separate step.

## Probe result and full-read capture intent (2026-09-11T06:22:46.669941+00:00)

- Probe command completed with exit code 0. Observed output: `CH347 SPI clock set to 1.875MHz`; `Found Winbond flash chip "W25Q128.V" (16384 kB, SPI)`; vendor `Winbond`, name `W25Q128.V`.
- Evidence output will be preserved at `evidence/programmer/probe-20260911.txt` with SHA-256 recorded after write.
- Next exact commands, after this intent record: `pkexec /tmp/bc250-flashrom-trial-20260911/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-a.bin` and the same command with `read-b.bin`.
- Expected effect: two independent complete 16 MiB reads only. Each invocation may probe/identify and read; it must not erase, write, unprotect, or modify the target.
- Stop conditions: any nonzero exit, read error, chip identity change, output size other than 16 MiB, or any mismatch between the two reads.
- Rollback: remove only incomplete derived files; no target rollback operation.

## First full read result (2026-09-11T06:26:50.108571+00:00)

- Exact command completed with exit code 0: `pkexec /tmp/bc250-flashrom-trial-20260911/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-a.bin`.
- Observed flashrom output: `CH347 SPI clock set to 1.875MHz`; `Found Winbond flash chip "W25Q128.V" (16384 kB, SPI)`; `Reading flash... done.`
- Output: `evidence/programmer/reads/20260911/read-a.bin`, size `16,777,216` bytes, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, owner `root:root`, mode `0644`.
- `cmp` against immutable `dump/2.bin` returned exit `0`; both SHA-256 values are `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`. This is a fresh read matching the selected prior dump, not yet a second fresh read.
- Flashrom stdout will be preserved at `evidence/programmer/reads/20260911/read-a.flashrom.log`.
- No write, erase, status-register write, register mutation, or flash occurred.

## Second full read start intent (2026-09-11T06:27:03.465459+00:00)

- Exact command: `pkexec /tmp/bc250-flashrom-trial-20260911/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-b.bin`
- Target remains physically isolated and powered only by CH347T as confirmed by operator.
- Expected effect: one independent complete 16 MiB read, no target mutation. Compare byte-for-byte with `read-a.bin` and `dump/2.bin` only after completion.

## Second full read result and matching baseline (2026-09-11T06:28:51.817972+00:00)

- Exact command completed with exit code 0: `pkexec /tmp/bc250-flashrom-trial-20260911/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r evidence/programmer/reads/20260911/read-b.bin`.
- Observed output: `CH347 SPI clock set to 1.875MHz`; `Found Winbond flash chip "W25Q128.V" (16384 kB, SPI)`; `Reading flash... done.`
- Output: `evidence/programmer/reads/20260911/read-b.bin`, size `16,777,216` bytes, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, owner `root:root`, mode `0644`.
- `cmp` returned `0` for `read-a.bin` versus `read-b.bin`, and `0` for `read-b.bin` versus immutable `dump/2.bin`. All three SHA-256 values are `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Flashrom stdout will be preserved at `evidence/programmer/reads/20260911/read-b.flashrom.log`.
- Two matching fresh full reads are now present. This establishes a matching read baseline; it does not establish bootability, PSP acceptance, VCN enablement, or hardware stability under a modified image.
- No write, erase, status-register write, register mutation, or flash occurred.

## Readback manifest capture intent (2026-09-11T06:28:51.817981+00:00)

- Preserve commands, package/binary hashes, USB identity, file sizes/hashes, comparisons, and evidence classification in `evidence/programmer/reads/20260911/manifest.json`.
- Expected effect: machine-readable provenance only; no target operation.

## Fresh-read independent parser intent (2026-09-11T06:29:43.433094+00:00)

- Target inputs: `evidence/programmer/reads/20260911/read-a.bin` and `read-b.bin`, both already verified 16 MiB and byte-identical.
- Exact command: `python3 scripts/firmware_audit.py evidence/programmer/reads/20260911/read-a.bin evidence/programmer/reads/20260911/read-b.bin --output evidence/programmer/reads/20260911/firmware-audit/inventory.json`
- Expected effect: read-only parse of SPI/PSP/BHD/APCB/UEFI FV/FFS structure into a new JSON report; no input writes or hardware access.
- Independent checks: outer format, PSP/BHD/APCB checksums, FV/FFS boundaries, executable count, and report hash.

## Fresh-read executable extraction intent (2026-09-11T06:30:33.828228+00:00)

- Exact command: `python3 scripts/firmware_audit.py evidence/programmer/reads/20260911/read-a.bin --output evidence/programmer/reads/20260911/firmware-audit/read-a-inventory-with-extract.json --extract-image evidence/programmer/reads/20260911/read-a.bin --extract-dir evidence/programmer/reads/20260911/firmware-audit/read-a-extract`
- Expected effect: copy executable PE32/TE bodies from the fresh read to a new evidence directory and emit a machine-readable extraction record; source read remains untouched.
- Acceptance: executable count and per-body SHA-256s must match the already validated `dump-2-extract`; any mismatch is a stop condition.

## Fresh-read parser and extraction result (2026-09-11T06:31:12.400291+00:00)

- `scripts/firmware_audit.py` completed with exit code 0 on both fresh reads. Report: `evidence/programmer/reads/20260911/firmware-audit/inventory.json`, SHA-256 `e982f755981cac0231c52074872f6478005f9e4826e6063512c6664a963c76b4`.
- Both inputs were parsed as 16 MiB images with PSP `19` entries/checksum match, BHD `4` entries/checksum match, APCB size `0xB70`/checksum match, and `4` firmware volumes. Both retained DFG words `0x001FFF00` at APCB relative `0x130` and `0x16C`.
- Fresh read-a executable extraction completed with `234` modules. Report: `evidence/programmer/reads/20260911/firmware-audit/read-a-inventory-with-extract.json`, SHA-256 `e914cf3e72dd6726337838140515f85c5504183301f28d31e8f3d37890786053`.
- Independent byte-level comparison of all `234` extracted module files against `evidence/firmware-audit/dump-2-extract/modules` found `234/234` names and hashes equal, with zero differences.
- This confirms the fresh baseline at observed-bytes/static-analysis layers. It does not prove modified-image boot, PSP signature acceptance, VCN runtime enablement, or memory/voltage behavior.

## APCB-only candidate build intent (2026-09-11T06:31:49.370015+00:00)

- G3 check: no canonical project candidate builder exists; the imported unsigned gasket builder is rejected and cannot be reused as a safe route. Add the smallest deterministic builder plus one new candidate.
- Source: `evidence/programmer/reads/20260911/read-a.bin`, independently matched by `read-b.bin` and immutable `dump/2.bin`; source SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- New script: `scripts/build_apcb_dfg_candidate.py`; new output: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`. Output must be created only if absent and must never overwrite the source.
- Exact transform: at APCB base `0xAB1000`, size `0xB70`, change relative words `+0x130` and `+0x16C` from little-endian `0x001FFF00` (`00 FF 1F 00`) to `0x007FFF00` (`00 FF 7F 00`); recalculate only APCB checksum byte at `+0x10` from `0xF2` to `0x32`.
- Expected changed offsets: absolute `0xAB1132`, `0xAB116E`, and `0xAB1010` only; total changed bytes `6`. PSP, `$PS1`, BHD, FV/FFS, NVRAM, and all other bytes must remain identical.
- This is an offline candidate, not a release or flash image. Preserve signed regions; do not invoke a programmer after building it.
- Rollback: delete only the new candidate/script if the independent checks fail; original reads and `dump/2.bin` remain untouched.

## APCB-only candidate build result and validation intent (2026-09-11T06:33:24.031049+00:00)

- Builder completed with exit code 0. Script SHA-256: `9235d0137abbfa17c49de3323cf82f4d65d5ded9fcbbe1dad246bcad9248ea2f`.
- Candidate: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, size `16777216`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`.
- Builder reported only absolute offsets `0xAB1010`, `0xAB1132`, `0xAB116E` changed; DFG words `0x001FFF00 -> 0x007FFF00`; APCB checksum `0xF2 -> 0x32`; no signed regions touched.
- Before relying on the candidate, run independent byte-diff and existing `scripts/apcb_detail.py` and `scripts/firmware_audit.py` reports into new evidence files.
- Acceptance: exactly three changed bytes, APCB checksum match, DFG values `0x007FFF00`, unchanged PSP/BHD/FV/FFS/NVAR/other bytes, and no parser failures.
- Candidate remains offline/static only; no programmer operation is authorized by this build.

## APCB-only candidate validation result (2026-09-11T06:34:33.444936+00:00)

- Independent byte comparison (separate from builder) found exactly `3` changed byte offsets: `0xAB1010: F2 -> 32`, `0xAB1132: 1F -> 7F`, and `0xAB116E: 1F -> 7F`; image sizes remain `0x1000000`.
- `scripts/apcb_detail.py` completed exit `0`: report `evidence/candidates/BC250_APCB_DFG_only_v001/apcb-detail.json`, SHA-256 `01feebf8bb82ea17d6ef12138445573128eae94d171ee8180608ec0cb72abf9e`. Source APCB checksum `F2/F2`, candidate `32/32`; source DFG words `0x001FFF00`, candidate `0x007FFF00`; both group count `6`, no parser errors.
- `scripts/firmware_audit.py` completed exit `0`: report `evidence/candidates/BC250_APCB_DFG_only_v001/firmware-audit.json`, SHA-256 `0b1b273dd233e3e102cc9df333221eee68b593ac80736e9e38bfb5ee4cb26fac`. Candidate PSP/BHD/APCB checksums match and `4` firmware volumes were found.
- Candidate output remains `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`.
- Static verification passed for byte-level minimality and parser structure. Hardware acceptance, PSP signature acceptance, bootability, VCN runtime effect, and memory/voltage behavior remain unrun.
- No programmer write, erase, register mutation, or flash occurred.

## Candidate provenance manifest capture intent (2026-09-11T06:34:45.685555+00:00)

- Preserve machine-readable candidate source/output hashes, exact transformation, builder hash, independent parser report hashes, and unrun checks at `evidence/candidates/BC250_APCB_DFG_only_v001/build-manifest.json`.
- This metadata write does not touch firmware or hardware.

## Audit state and plan update intent (2026-09-11T06:35:19.033876+00:00)

- Update the canonical spec, firmware-audit memory, and hash-specific draft with the verified two-read baseline and the statically verified APCB-only candidate.
- Preserve current open gates: independent review, PSP/signature behavior, bootability, VCN runtime, memory training, SoC-voltage units/rails, and exact per-image/per-board approval remain incomplete.
- These documentation writes do not modify firmware or hardware.

## Audit state update result (2026-09-11T06:36:50.820784+00:00)

- Updated canonical spec with the matching fresh-baseline and APCB-only candidate status. Spec hash: `a22fb0fa54eb7cd3a676d935a009b913b2cc42a76a2145a090641c3567ea3557`.
- Corrected firmware-audit memory: prior no-programmer-operation wording is superseded by the observed read-only probe/reads.
- Updated hash-specific draft with F12/Q2. Draft SHA-256: `d8b24c0319a6e72fc8009459b2f196559c26b6815ad57bcca46c05b6a7fee6cd`.
- Remaining evidence gaps are explicitly retained: native MCP on pending modules, VCN runtime/codec, memory training and voltage semantics/telemetry, independent candidate review, and any hardware write approval.
- No firmware or hardware mutation occurred.

## Post-candidate repository validation result (2026-09-11T06:39:29.755157+00:00)

- Command `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-contour.py && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check` completed exit `0`.
- Contour: `OK contract_copies=4 skills=11 instincts=6`.
- Unit tests: `4` NVAR tests passed.
- `git diff --check`: passed.
- Candidate and readback evidence remain offline/read-only artifacts; no programmer write or hardware mutation occurred.

## Fresh-read IP discovery extraction intent (2026-09-11T06:44:47.930665+00:00)

- Source: `evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Extract exactly `0x450` bytes at SPI offset `0x981A00` to `evidence/firmware-audit/ip-discovery/read-a-hardware-ip-config.bin`; parse with the existing imported `parse_hw_ip_config.py` into `read-a-hardware-ip-config.json`.
- Expected effect: new read-only evidence for the IPDS descriptor; source image is untouched.
- Acceptance: binary declared size `0x44C`, IPDS version `2`, one die, 38 IP records, and VCN HWID 12 version `2.0.3`/harvest 0 with bases `0x7800`, `0x7E00`, `0x02403000`.

## Fresh-read IP discovery result (2026-09-11T06:45:50.818228+00:00)

- Extracted `0x450` bytes at `0x981A00`: `evidence/firmware-audit/ip-discovery/read-a-hardware-ip-config.bin`, SHA-256 `1b5b798a93abac86f0f25ef188627ee9a86fcfc27d68af0a444bc8cfdc896bc5`.
- Existing `parse_hw_ip_config.py` completed exit `0`; report `evidence/firmware-audit/ip-discovery/read-a-hardware-ip-config.json`, SHA-256 `c327fb0ae3dbe276329e76a8b296c05c59449338361afef8e6491ac4fa516ecc`.
- Observed binary header version `0.0`, declared size `1100` (`0x44C`); IPDS version `2`, one die, 38 IP records. VCN row: HWID `12`, instance `0`, version `2.0.3`, harvest `0`, bases `0x00007800`, `0x00007E00`, `0x02403000`.
- Fresh parsed report is JSON-equal to imported Robin3 reference `import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_hw_ip_config_parsed.json`, SHA-256 `b314a8e3c7d1a7036bfc0837b97200bea6c276fa0492a2de881c9bb626a02cb5`.
- This remains descriptor-only evidence; it does not prove VCN power, firmware loading, MC/coherency/rings, codec, or user-visible operation.

## VCN evidence-map capture intent (2026-09-11T06:46:10.576180+00:00)

- Build a machine-readable VCN path map from already verified current-read parser outputs, `$PS1`/PSP/APCB reports, Rizin static scans, CoreUnlock corrected summary, and imported host-source references.
- New output: `evidence/firmware-audit/vcn-evidence-map.json`. This is derived metadata only; no firmware or hardware write.
- Each edge must state evidence class, exact source/hash, observed or inferred status, and the next discriminating test.

## VCN evidence-map result (2026-09-11T06:50:04.941815+00:00)

- Created `evidence/firmware-audit/vcn-evidence-map.json`, SHA-256 `ab683aaacfa77b71ec6404f714cb66b39210f6c57509f457082b5f09bbdc08b5`.
- Map links the matching read baseline, IPDS/VCN descriptor, PSP type-8 PMFW, `$PS1` groups, APCB candidate, Rizin literal scan, CoreUnlock MCP/static path, and imported amdgpu source.
- It separates descriptor-only, static-analysis, hardware-readback, and runtime-unknown claims and records discriminating next tests.
- No firmware or hardware mutation occurred.

## Memory/SoC-voltage evidence-map capture intent (2026-09-11T06:53:23.072410+00:00)

- Build a machine-readable map of AmdSetup/NVAR, IFR fields, APCB MEMG/DFG groups, UMC/IPDS records, memory/SMU/DF consumers, and historical OC deltas.
- New output: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`; derived metadata only.
- Preserve the no-guessed-voltage rule: historical numeric offsets are recorded as unverified claims until units, control semantics, consumers, training dependencies, and live telemetry are established.

## Fresh-read NVAR/AmdSetup audit intent (2026-09-11T06:54:01.669588+00:00)

- Exact command: `python3 scripts/nvar_audit.py evidence/programmer/reads/20260911/read-a.bin --output evidence/programmer/reads/20260911/firmware-audit/read-a-nvar-primary.json --store-offset 0x0 --store-length 0x10000 --variable AmdSetup`.
- Expected effect: parse the same bounded NVAR store and selected `AmdSetup` body directly from the fresh read; no input or hardware writes.
- Acceptance: one AmdSetup record at relative `0x4BB`, body length `0x8B5`, same body hash and selected field values as the validated dump report.

## Fresh-read NVAR/AmdSetup audit result (2026-09-11T06:54:59.869759+00:00)

- `scripts/nvar_audit.py` completed exit `0`; report `evidence/programmer/reads/20260911/firmware-audit/read-a-nvar-primary.json`, SHA-256 `d3e769533368d0fcbfad476e6c2b75f510d1b4f80d356c4b8ff72bdfd3673b65`.
- Observed `683` records, one `AmdSetup` at `0x4BB`, body length `0x8B5`, body SHA-256 `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`; three existing tail `unterminated NVAR name` warnings are reproduced.
- Selected field values are equal to the validated dump report, including MCLK `0xFF`, UCLK divider `0xFF`, FCLK_DPM `0x0F`, VDD control/value `0/0`, DF control/value `0xFF/1000`, CPU `3600`, PPT `88000/65000`, and VRM `65000/95000`.
- Fresh-read NVAR result confirms the current field baseline at observed-bytes/static-analysis layers; units, consumer behavior, training dependence, and live voltage remain unresolved.

## Memory/SoC-voltage evidence-map result (2026-09-11T06:57:08.677013+00:00)

- Created `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, SHA-256 `6dae6540db6944e9a570b60db2293e8d26a3bcb27507c5693102882a00e2c34f`.
- Map records current AmdSetup/NVAR values from the fresh read, IFR types/options, APCB MEMG/DFG groups, IPDS UMC instances, relevant PEI/DXE module hashes and static literal hits, and historical OC deltas.
- It explicitly leaves memory and SoC-voltage candidates unbuilt because field consumers, units, training behavior, and live rails are not proven.
- No voltage value was guessed and no firmware/hardware mutation occurred.

## Evidence-map documentation result (2026-09-11T06:58:06.448202+00:00)

- Firmware-audit memory updated with fresh baseline, candidate, VCN map, and memory/SoC map hashes.
- Hash-specific draft appended with F13. Current SHA-256 `a6acce840566e598995544960867ce432d5baae3d2ba944d2d6f0836c4caea4b`.
- Documentation reflects that only the APCB-only VCN candidate exists; memory/SoC-voltage candidate remains unbuilt.

## Memory/SoC candidate specification intent (2026-09-11T07:01:47.856917+00:00)

- Create a bounded active specification for separate memory-clock and SoC-voltage candidate tracks.
- The specification must permit offline candidate generation only after evidence gates; it must explicitly forbid guessed voltage values and combined first tests.
- New output: `specs/2026-09-11-memory-soc-candidate.md`; no firmware/hardware mutation.

## Memory/SoC candidate specification result (2026-09-11T07:03:33.227408+00:00)

- Created `specs/2026-09-11-memory-soc-candidate.md`, SHA-256 `5c28191a261aaa128d1f4b2a1bf77d91436e02235b24f90c3c456926e87c33a1`.
- Specification keeps memory and SoC-voltage tracks separate, records exact current fields and gates, and explicitly forbids guessed voltage values.
- Current status: no memory or SoC-voltage binary; only APCB-only VCN candidate exists.

## Independent candidate review dispatch intent (2026-09-11T07:05:59.702229+00:00)

- Bounded worker task: independently review only `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin` and its source/reports; inspect actual bytes, hashes, parser outputs, failure/recovery path, and unrun hardware/signature checks.
- Worker model family: Gemini via selector `omniroute/agy/gemini-3.1-pro-low`; effort: medium reasoning. Astra is prohibited and will not be used.
- Permissions: read-only repository/evidence access; worker may write only its unique review artifact `evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md`; no candidate edits, no package/programmer commands, no hardware, no register/JTAG writes, no secrets.
- Acceptance: review states checked scope, exact source/output hashes, changed offsets, parser/checksum results, recovery/failure gates, findings, and unrun checks; it must not call the candidate safe, bootable, signed, or flash-ready.
- Root will recheck the returned artifact and hash before relying on it.

## Independent candidate review dispatch receipt (2026-09-11T07:07:09.177169+00:00)

- Worker: `candidate-review-gemini`; child id `sub-f24777ec`; effective model `omniroute/agy/gemini-3.1-pro-low`; unique artifact `evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md`.
- Dispatch is a review input only. Root verification is pending.

## Memory-clock-only candidate build intent (2026-09-11T07:08:09.845747+00:00)

- Rationale: IFR provides a concrete `MemoryClockSpeed` option `0x23 = 1750MHz`, and historical profiles independently use this value; this permits a one-field offline hypothesis without guessing a voltage.
- Source: `evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`; AmdSetup NVAR body begins at `0x4CF`.
- New script: `scripts/build_amdsetup_memory_candidate.py`; output: `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`; refuse in-place/overwrite.
- Exact transform: change only `AmdSetup+0x316` / absolute `0x7E5` from `FF` (Auto) to `23` (IFR 1750MHz). Do not change UCLK, FCLK, DF override, voltage, timing, power, APCB, PSP, `$PS1`, BHD, or any other NVAR bytes.
- Expected changed range: one byte at absolute `0x7E5`; no checksum field is altered by this NVAR byte change.
- Candidate is a static test hypothesis, not a stability/boot claim.
- Rollback: delete only the new candidate/script/reports if checks fail; preserve all source reads and controls.

## Memory candidate builder correction intent (2026-09-11T07:10:10.810305+00:00)

- Failure observed: builder exited `1` with `AmdSetup NVAR name mismatch` before output creation.
- Correction: change only the NVAR name slice from record `+0x0C` to `+0x0B`, confirmed by direct observed bytes and parser metadata.
- No target or source image was modified; output path remains absent and protected by overwrite refusal.

## Memory-clock-only candidate build result and validation intent (2026-09-11T07:11:16.089629+00:00)

- Corrected builder completed exit `0`; script SHA-256 `3d015676c4e2d8bc5fbee235aaea18802fb93332d1b4bab0610ab4f20dd0ea36`.
- Candidate: `candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin`, size `16777216`, SHA-256 `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`.
- Builder reports one changed byte: AmdSetup `+0x316`, absolute `0x7E5`, `FF` (Auto) -> `23` (IFR 1750MHz). No UCLK/FCLK/voltage/timing/APCB/PSP/`$PS1`/BHD/FV fields are intentionally changed.
- Validate with independent byte diff, fresh `nvar_audit.py`, and `firmware_audit.py` into `evidence/candidates/BC250_MemoryClock_1750_only_v001/`.
- Acceptance: exactly one changed offset, selected MemoryClockSpeed `0x23`, all outer checksums/volumes valid, and no other selected field changes.
- Candidate remains static hypothesis only; no programmer operation is permitted by this build.

## Memory-clock-only candidate validation result and manifest intent (2026-09-11T07:13:17.622793+00:00)

- Independent byte diff: exactly one changed byte `0x7E5: FF -> 23`; image size remains `0x1000000`.
- Fresh candidate NVAR parse completed exit `0`: `evidence/candidates/BC250_MemoryClock_1750_only_v001/nvar-primary.json`, pending report SHA-256 after write; 683 records, one AmdSetup, three reproduced tail warnings, selected MemoryClockSpeed `35` (`0x23`).
- Full firmware parse completed exit `0`: `evidence/candidates/BC250_MemoryClock_1750_only_v001/firmware-audit.json`, pending report SHA-256 after write; PSP/BHD/APCB checksums match and 4 FVs found.
- No other selected AmdSetup field differs from the fresh baseline. No voltage/APCB/PSP/`$PS1`/BHD/FV change occurred.
- Preserve machine-readable provenance at `evidence/candidates/BC250_MemoryClock_1750_only_v001/build-manifest.json`.
- Candidate remains untested static hypothesis; no programmer write or hardware mutation.

## Memory-clock-only candidate manifest result (2026-09-11T07:14:41.712742+00:00)

- Build manifest: `evidence/candidates/BC250_MemoryClock_1750_only_v001/build-manifest.json`, SHA-256 `f9c72180e2d67c0eef7c3128456dde87478b89d5b1a06d20f76e63539db4f61f`.
- NVAR report SHA-256 `06710664aa71770881221401da74c1fa1ce224e8eaf1e5940176490a69a927f5`; firmware report SHA-256 `83b82cd738bc7d668ac90f568066ef451ffc2075af36d2b2fde5bc4e951dcae8`.
- Static verification passed: one changed byte, selected field `MemoryClockSpeed=0x23`, all outer checksums/4 FVs valid, no other selected field changed.
- Candidate remains not hardware-tested and not flash-approved.

## Memory candidate state documentation intent (2026-09-11T07:14:52.012946+00:00)

- Update memory/SoC evidence map, active memory candidate specification, firmware-audit memory, and hash-specific report with the new one-field memory-clock candidate.
- Preserve SoC-voltage no-go: no voltage candidate or value will be created until units/consumer/training/telemetry are proven.
- Documentation and metadata only; no firmware or hardware mutation.

## Memory candidate state documentation result (2026-09-11T07:16:37.229835+00:00)

- Updated `evidence/firmware-audit/memory-soc-voltage-evidence-map.json` SHA-256 `e0b13fe380740b011aca216bc268117827210ed5a296c74203c62b198a28735b` with the one-field candidate.
- Updated `specs/2026-09-11-memory-soc-candidate.md` SHA-256 `7b62f4d1e773d8f59cebbf3a78e5c0472885e312d32527070d3c5a7870055de9`.
- Updated firmware-audit memory and hash-specific report; report SHA-256 `84bc5a70f9d5e0114f54179bdad7b93f74f944a05d198faaaf75f3a1bfcbd0cb`.
- SoC-voltage candidate remains unbuilt, with the no-guessed-value rule intact.

## Candidate catalog intent (2026-09-11T07:18:13.624386+00:00)

- Create `candidates/README.md` to prevent confusion between the APCB VCN candidate, one-field memory candidate, and the intentionally unbuilt SoC-voltage track.
- Include exact hashes, static status, hardware/recovery restrictions, and explicit no-go for historical unsigned candidates.
- Documentation only; no firmware or hardware mutation.

## Candidate catalog result (2026-09-11T07:18:59.400559+00:00)

- Created `candidates/README.md`, SHA-256 `6252ecbe3fd82f57e5922bff13cddaeee420083e347c07899a39f51285bd17b8`.
- Catalog lists exact source/candidate hashes and keeps the SoC-voltage track explicitly unbuilt; it rejects historical unsigned/OC artifacts as flash sources.

## Independent candidate review result and metadata update intent (2026-09-11T07:20:54.912049+00:00)

- Gemini reviewer completed bounded read-only review. Root independently rechecked both actual artifacts and hashes.
- APCB review: `evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md`, SHA-256 `90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905`.
- Memory review: `evidence/candidates/BC250_MemoryClock_1750_only_v001/independent-review-gemini.md`, SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`.
- Both reviews pass exact hash/size/diff/parser scope and explicitly leave signature, boot, runtime, training, stability, and hardware checks unrun.
- Update both build manifests with the independent-review paths/hashes and update the evidence maps/catalog/docs. These are metadata/documentation writes only.

## Independent review integration result (2026-09-11T07:23:00.130946+00:00)

- Root rechecked the actual APCB review file: SHA-256 `90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905`; review scope and PASS/UNRUN statements are present.
- Root rechecked the actual memory review file: SHA-256 `47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb`; review scope and PASS/UNRUN statements are present.
- Updated candidate manifests: APCB `5fb0aca877eb8583186f2f6861636ba7b70fc66404fa768dd6c4a408fda61c5a`; memory `f608e77530dc47cebf802e36c9cea300f792fa5764b2288572f17ae0831b3a0b`.
- Updated catalog SHA-256 `6a05eaac7d794cfb27d584a4b2c65bf30f9abb3e1191db3e8360633a7db57d5b`, memory spec SHA-256 `994090808ae4d2d2527a36dd2872ef15ef2f7c51bd97ff0d8fac394f4598b9d3`, VCN map SHA-256 `0b55855c7c6c383007d4e2a065950a3e7b247343da1640f2b8eb303940fdb386`, memory map SHA-256 `9143f8c9cb48ed3cb1eb32d899347bc1de85d78ae5d01f74be687bab388dbf35`, and draft report SHA-256 `d1d8b46400cf112899ed2bb1bf7ccedd2700d3c4f6b91a6b1074303f548e4436`.
- Independent review is complete for both offline candidates. Hardware/signature/runtime/training/boot checks remain unrun; no flash approval exists.

## Final candidate/static validation intent (2026-09-11T07:23:28.173614+00:00)

- Run repository contour, unit tests, syntax checks for both new builders using a temporary pycache prefix, and `git diff --check`.
- Recompute candidate/source/review hashes and verify candidate outputs remain exact.
- No hardware/programmer command and no firmware write.

## Final candidate/static validation result (2026-09-11T07:24:33.207366+00:00)

- Command completed exit `0`: contour validation, 4 unit tests, py_compile for both new builders with temporary pycache, and `git diff --check`.
- Contour: `OK contract_copies=4 skills=11 instincts=6`; all 4 NVAR tests passed.
- Candidate hashes remain APCB `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70` and MemoryClock `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`.
- No firmware/hardware mutation occurred.

## Historical VCN runtime evidence reconciliation intent (2026-09-11T07:26:48.761839+00:00)

- Add bounded historical runtime observations to the VCN evidence map and report without promoting them to current hardware proof.
- Sources: imported `vcn-probe-mode0_2026-08-26.out`, `vcn-probe-mode1_2026-08-26.out`, and `a1_vcn_readonly.out`; preserve exact hashes and labels.
- Expected result: mode-1 historical log shows VCN firmware/ring enumeration followed by IB ring test `-110` timeouts; mode-0/readonly limitations remain explicit.
- No board access or hardware command will be run; documentation/metadata only.

## Historical VCN runtime reconciliation result (2026-09-11T07:28:29.709406+00:00)

- Added the imported historical mode-0/mode-1 and read-only limitations to the VCN/memory maps with exact hashes.
- Mode-1 observation is recorded as VCN firmware/ring setup followed by `-110` IB timeouts; it is explicitly not promoted to current hardware proof.
- No board boot or hardware command occurred in this reconciliation.

## SMU metrics/source trace map update intent (2026-09-11T07:30:03.437030+00:00)

- Add static source traces for Cyan Skillfish SMU metrics and PMFW feature-bit definitions to the VCN and memory maps.
- Record that the host source labels metrics as MHz/mV in the metrics interface but does not prove the AmdSetup NVRAM offset encoding or exact running driver.
- Documentation/metadata only; no hardware or firmware mutation.

## SMU metrics/source trace map result (2026-09-11T07:31:37.790785+00:00)

- Added static Cyan Skillfish SMU metric and PMFW feature-bit traces to VCN/memory maps.
- Source artifacts: `cyan_skillfish_ppt.c` SHA-256 `9259ad3ff6f660fe97ca7ea68f9b7e5f5d185982f0d3341180bd880442f030f1`, `smu_v11_8_pmfw.h` SHA-256 `8893329478e28c2f36b0298b2aeb0fc4b5902a77e76e82db57e2884fe0a82966`, feature callback map SHA-256 `fab4157a57a1d73ae35402d1d35c06adc7bf64a509c108a2eb32f63cc5e499d4`.
- Updated VCN map SHA-256 `996643d78b5176c6746a0f200901cc9afc36a7a3e977b8ecd5ca7901a64f8ee4` and memory map SHA-256 `2d0433c5dae972216bc55a0034724540331b49de4ed14321309012e097a057a8`.
- Source traces remain static/imported; no NVRAM unit or runtime claim was promoted.

## Programmer/candidate recovery-gate runbook intent (2026-09-11T07:32:31.746451+00:00)

- Create a concise repeatable runbook for future read-only SPI capture and any separately approved candidate write.
- Include exact baseline hashes, package/protocol, stop conditions, rollback, explicit approval string, and post-write readback requirements.
- Documentation only; no hardware or firmware operation.

## Programmer/candidate recovery-gate runbook result (2026-09-11T07:34:32.344111+00:00)

- Created `docs/runbooks/2026-09-11-bc250-programmer-and-candidate-gates.md`, SHA-256 `66352fe691122df1d98a8df49dfdec7bdba0ecef810304e7e00a8f3209b9e149`.
- Runbook documents read-only prerequisites, exact commands, candidate review gates, explicit per-image/per-board approval, post-write readback, rollback, and JTAG separation.
- Write gate remains not passed; no firmware/hardware mutation occurred.

## VCN DXE write-capability edge update intent (2026-09-11T07:35:13.284954+00:00)

- Add the imported VCN DXE/probe binary static findings to the VCN map, explicitly separating their hardware-write behavior from read-only probes.
- Source manifest: `evidence/firmware-audit/rizin/dxe/manifest.json`; no binary will be run.
- Expected result: record that these artifacts are static write-capable references and are not safe read-only probes.

## VCN DXE write-capability edge update result (2026-09-11T07:36:41.516623+00:00)

- VCN map updated with `VCN-E11` and Dxe static manifest; map SHA-256 `0dc07ac65ada78a77b47ca68453e2a795468a2d742ee9254f853a926e9b96ec7`.
- Imported VCN DXE/probe binaries remain static write-capable references and were not executed.

## VCN DXE/probe documentation result (2026-09-11T07:37:38.659113+00:00)

- Updated firmware-audit memory and report with the write-capable static classification. Current report SHA-256 `184bd0c53510712f6e59435c2cb1724bb75813bbb6421cc8d2db67e68c80c1ce`.
- No imported DXE/probe binary was run and no hardware mutation occurred.

## Durable decision update intent (2026-09-11T07:42:07.475819+00:00)

- Append decisions for the fresh matching CH347T baseline, separate offline candidates, and explicit SoC-voltage no-go to `memory/decisions.md`.
- Preserve prior decisions and do not mark either candidate flash-ready.

## Durable decision update result (2026-09-11T07:42:53.501310+00:00)

- Appended D12 (fresh read baseline) and D13 (separate candidate/no-guessed-voltage status) to `memory/decisions.md`, SHA-256 `af3389200cf9814a3ce2bd00b37881d09b2af7a6ae49b626095689ed8cb8c739`.

## Project-state status update intent (2026-09-11T07:55:26.740271+00:00)

- Append current phase/results to `memory/project-state.md`: two matching hardware readbacks, verified offline VCN and memory candidates, and remaining runtime/SoC/MCP gaps.
- Preserve historical statements; no write/flash claim.

## Project-state status update result (2026-09-11T07:56:44.674261+00:00)

- Appended current readback/candidate/runtime status to `memory/project-state.md`, SHA-256 `73e6d367ccf7a3dd82c6a2fb4be8fccb329d0c3e1421667dff1a851fac029779`.

## Repository hygiene check result (2026-09-11T07:58:18.349966+00:00)

- `git diff --check` passed after all current updates.
- No new builder bytecode was written under project paths; existing imported/project `__pycache__` artifacts were preserved as provenance and not modified by the final py_compile run (temporary pycache prefix used).

## Final current-state verification intent (2026-09-11T08:01:08.625716+00:00)

- Re-read and verify current candidate manifests, review hashes, evidence-map artifact references, readback equality, candidate diff offsets, parser checks, and repository hygiene.
- Report PASS/UNRUN status without claiming hardware behavior or flash approval.

## Final current-state verification result (2026-09-11T08:03:21.670104+00:00)

- Root checks all passed: two reads size/hash/equality; APCB candidate exact three-byte diff and parser reports; MemoryClock candidate exact one-byte diff and NVAR/full parser reports; independent reviews present; map artifact references resolve and hashes match.
- Repository command completed exit `0`: contour validation, 4 unit tests, and `git diff --check`.
- Current artifact classes: fresh SPI readback `hardware-verified` for the read operation; candidates `statically-verified-offline-candidate` with independent review.
- Explicitly unrun: PSP cryptographic acceptance, modified-image boot, VCN runtime/codec, memory training/stability/live clocks, SoC-voltage rails, JTAG, and all firmware/register/programmer writes.
- No firmware write, erase, flash, register mutation, or JTAG target-memory write occurred.

## Programmer CLI research runtime amendment intent (2026-09-11T08:19:41.254557+00:00)

- Append the verified package signature, actual `flashrom v1.8.0` probe, two matching reads, and bounded adoption state to `docs/research/2026-09-11-programmer-cli-evaluation.md`.
- Keep read-only scope and unrun write/boot/runtime claims explicit.

## Programmer CLI research runtime amendment result (2026-09-11T08:23:26.671655+00:00)

- Research note updated with package signature/binary hashes and the successful read-only runtime trial; SHA-256 `3e082b56514be95a94011f183b23ccda1dca8a6d4fbd6e7e72ce92030b193d57`.
- flashrom route promoted from `TRIAL` to `ADOPT` for read-only Detect/read/hash/parse only.
- D14 appended to `memory/decisions.md` SHA-256 `20ffb1d355c3ad3f26ef1064edcd5ad9949511dac378e48738858e91e0dcafbc`.

## Programmer status correction result (2026-09-11T08:26:20.402072+00:00)

- Updated report with F18 clarifying that the earlier no-read statement is historical and superseded by the verified read-only trial. Current report SHA-256 `90ddc28f9d09fc397ed71d7ef9176a2a4c5a3de23f04d9cfe33e0fafee359848`.
- Updated research note/D14: `flashrom v1.8.0` is adopted only for read-only CH347T operations.

## Direct chip identity correction/update intent (2026-09-11T08:31:47.487694+00:00)

- Record that direct read-only `flashrom` probe found Winbond W25Q128.V, while historical CAD labels BIOS_A1 as MXIC. Preserve the conflict and give direct JEDEC/probe evidence precedence for this attached chip; do not infer PCB revision or population from either label alone.
- Append the correction to `memory/decisions.md` and firmware-audit memory. Documentation only.

## Direct chip identity correction/update result (2026-09-11T08:34:32.981010+00:00)

- D15 appended to `memory/decisions.md`, SHA-256 `d85035d938d366d9a844c036ba6aa73dfe8e6454f5800d7f1732891fe6f38abe`; firmware-audit memory appended with same distinction.
- Direct Winbond readback identity and historical CAD MXIC label are preserved as separate evidence; no firmware/hardware mutation.

## Candidate catalog review-link result (2026-09-11T08:36:06.746922+00:00)

- Added both independent review paths/hashes to `candidates/README.md`, SHA-256 `7ad1fbccf77c21e948cab9fbbfe915f06e82452d11dbb9f507ce02c09bf8dd99`.

## Final map/hash synchronization intent (2026-09-11T08:37:02.931340+00:00)

- Append current VCN/memory map hashes and candidate/review statuses to firmware-audit memory and the hash-specific report after all map updates.
- Documentation only; no firmware/hardware operation.

## Final map/hash synchronization result (2026-09-11T08:38:12.791382+00:00)

- Firmware-audit memory and report now point to current map hashes; report SHA-256 `6fbd4bf852b02ae3bb0b585060d0447f6be628e982f63fc522352754ddebe716`.
- No firmware/hardware mutation occurred.

## IPDS checksum corroboration intent (2026-09-11T08:43:50.387863+00:00)

- Add an independent 16-bit additive checksum check for the three nonempty IPDS tables to the VCN map.
- Expected: stored sums `0x48DC`, `0x023F`, and `0x0131` match calculated sums. Metadata only; no hardware/firmware mutation.

## IPDS checksum corroboration result (2026-09-11T08:44:55.142698+00:00)

- Independent additive checksums pass for nonempty IPDS tables 0/1/2: `0x48DC`, `0x023F`, `0x0131`.
- Updated VCN map SHA-256 `cd5161981c161a060b6ff0a4c30bf05e5b91aa05b11f8c7268744e2eace99bb2`. Binary header checksum field remains uninterpreted and is not used for a runtime claim.

## Final documentation/MCP cleanup validation result (2026-09-11T09:02:34.932158+00:00)

- Contour validation, 4 unit tests, and `git diff --check` completed with exit `0` after all current map/spec/catalog updates.
- Native MCP server cleanup verified: no listener remains on port 8000; saved transcript remains on disk.

## Independent review worker cleanup (2026-09-11T09:11:14.673830+00:00)

- Direct child `candidate-review-gemini` was deleted after root verified both review artifacts. Its review outputs remain in `evidence/candidates/`.

## Final evidence-status snapshot intent (2026-09-11T09:14:09.898802+00:00)

- Append a final current snapshot to the hash-specific report and firmware-audit memory after all map/candidate/review updates.
- Include exact hashes, evidence classes, MCP cleanup, and all remaining unrun checks. Documentation only.

## Final evidence-status snapshot result (2026-09-11T09:16:31.648450+00:00)

- Appended F20 current status and synchronized firmware-audit memory. Current report SHA-256 `16b24757fc71553d8d0488f10d13cfadfce1353fd7275b3bf8e5ef775d1fbf1f`.
- Current VCN map SHA-256 `cd5161981c161a060b6ff0a4c30bf05e5b91aa05b11f8c7268744e2eace99bb2`; memory/SoC map SHA-256 `2d0433c5dae972216bc55a0034724540331b49de4ed14321309012e097a057a8`.
- Goal remains active because runtime/signature/training/voltage/MCP pending checks are not complete.

## Closing validation intent (2026-09-11T09:17:40.474649+00:00)

- Re-run contour/tests/diff checks after final snapshot writes and verify MCP port remains closed.

## Closing validation result (2026-09-11T09:21:07.710087+00:00)

- Contour validation passed (`contract_copies=4 skills=11 instincts=6`), all 4 unit tests passed, `git diff --check` passed, and no listener remains on port 8000.
- Current action log SHA-256 after this append: `6c560972c1774e65016f92b587d790f6ded6ada45cd0675aa98024ae1dcf865f`.

## SoC-voltage static semantics review dispatch intent (2026-09-11T09:27:36.726233+00:00)

- Bounded worker task: inspect only local/imported source and current evidence for `AmdSetup+0x6E5/+0x6E6` VDDCR_VDD control/value semantics, units, sign/encoding, SMU/PMFW consumers, and memory-training dependencies.
- Model family: Gemini via selector `omniroute/agy/gemini-3.1-pro-low`; effort: medium reasoning. Astra is prohibited and will not be used.
- Permissions: read-only repository/evidence access; write only unique artifact `evidence/firmware-audit/soc-voltage-static-review-gemini.md`; no binary edits, package/programmer/hardware commands, register/JTAG writes, or secrets.
- Source paths: `evidence/firmware-audit/memory-soc-voltage-evidence-map.json`, `evidence/firmware-audit/amdsetup-ifr-field-map.json`, `evidence/firmware-audit/dump-2-nvar-primary.json`, current fresh-read NVAR report, imported `tmp_bc250/recon` and `bc250-bios` source/docs, and Rizin reports.
- Acceptance: report exact hashes/paths, observed versus inferred claims, contradictions, unit/consumer evidence, no-go recommendation where proof is absent, and one next discriminating read-only test. No candidate or voltage value may be recommended from speculation.
- Root will independently recheck the artifact and hash.

## SoC-voltage static semantics review dispatch receipt (2026-09-11T09:29:13.228500+00:00)

- Worker: `soc-voltage-static-review-gemini`; child id `sub-48e6e7d2`; effective model `omniroute/agy/gemini-3.1-pro-low`; unique artifact `evidence/firmware-audit/soc-voltage-static-review-gemini.md`.
- Dispatch is a review input only; root verification is pending.

## Historical OC/SoC claim reconciliation intent (2026-09-11T09:31:09.342543+00:00)

- Add explicit contradiction/rejection records for imported OC/SoC claims, preserving their hashes and distinguishing IFR/byte evidence from unverified historical comments and telemetry.
- Document that current `VDDCR_VDD` value is IFR type `u32` with separate control, while historical documents model it as `u8/i8` and call values mV; do not promote those claims.
- Update memory/SoC map, firmware-audit memory, and hash-specific report. Documentation only; no candidate/hardware mutation.

## Historical OC/SoC claim reconciliation result (2026-09-11T09:33:15.836847+00:00)

- Added explicit historical/unverified/contradicted classification to the memory/SoC map and report. Current map SHA-256 `d93db2d4d5dd31627d949abc57182434c2e29e993f38496cb5df6527c556f442`; report SHA-256 `01527393aa34d0951433136518d7c6633d34f62f960506156f85957100c677c2`.
- No voltage was selected and no firmware/hardware mutation occurred.

## SoC-voltage static review worker result (2026-09-11T09:35:39.443374+00:00)

- Worker `soc-voltage-static-review-gemini` did not produce the requested artifact and stopped after an unsupported safety refusal. This is a worker result only, not a project finding.
- Root will continue the authorized static review directly using local evidence and will not use worker refusal as an authority. No hardware/programmer/register/JTAG operation occurred.

## Root SoC-voltage static review intent (2026-09-11T09:36:13.406477+00:00)

- After the worker did not produce an artifact, root will write a bounded static review from current evidence and imported source, explicitly preserving observed/inferred/unknown layers.
- Output: `evidence/firmware-audit/soc-voltage-static-review-root.md`. No firmware/hardware mutation and no voltage selection.

## Root SoC-voltage static review result (2026-09-11T09:39:17.568950+00:00)

- Created `evidence/firmware-audit/soc-voltage-static-review-root.md`, SHA-256 `d9cfbaca981c33181b04c7f9bc17aed35192cad4e762763ae25a9809f56a341b`.
- Review confirms: control/value fields and types are statically located; physical unit/sign/encoding, exact SMU consumer, training dependency, and live rail response remain inconclusive/unrun.
- Historical mV/safety comments are retained as contradicted/unverified references; no voltage value is recommended and no SoC candidate is built.
- Worker refusal was not used as evidence; root review is the project finding.

## SoC review integration intent (2026-09-11T09:40:07.883907+00:00)

- Add root SoC static review path/hash to the memory/SoC evidence map, firmware-audit memory, candidate spec, and hash-specific report.
- Preserve no-go for voltage candidate. Documentation only.

## SoC review integration result (2026-09-11T09:43:04.824371+00:00)

- Added root SoC review to map/memory/spec/report. Current memory-map SHA-256 `7c520f479332a3faa7790aee1917942ab48fabf588c44e621e3a50ded0a52f3c`; report SHA-256 `0e5fcf921c0b760bb5bc4ae7d5a30000a933d47f08161b11154d5ec4c1ff8876`.
- Evidence-based outcome remains no-go for a voltage candidate; no value was selected and no hardware action occurred.

## Rizin entry-call-graph metadata intent (2026-09-11T10:06:17.027460+00:00)

- Add parsed entry function/call-reference summaries from existing bundled Rizin reports to the memory/SoC map.
- This is context only; do not promote entry callrefs to field-consumer proof. Documentation/metadata only.

## Rizin entry-call-graph metadata result (2026-09-11T10:08:45.966520+00:00)

- Added entry call-reference summaries for 9 relevant modules to the memory/SoC map; current map SHA-256 `c444df533ed94c2701c3cfe6d2dc656651d86cb158245bb6045aa90b589b73e9`.
- These are static context only and are not treated as field-consumer proof.

## Runtime SMU API source-context update intent (2026-09-11T10:14:31.623170+00:00)

- Add static references to imported `bc250_smu` Queue-3/Queue-2/Queue-0 API and codec conversion code.
- Record separately that these files expose write-capable runtime methods and must not be executed; their voltage/mV and VID conversions do not prove the BIOS NVRAM field encoding.
- Update root SoC review, memory/SoC map, firmware memory, and report. Documentation only; no source execution or hardware access.

## Runtime SMU API source-context update result (2026-09-11T10:17:24.896846+00:00)

- Added imported Queue-0/2/3 and codec source references to root SoC review, memory map, firmware memory, and report.
- Current root review SHA-256 `8de13ee8606f0c8ae9f29d874015fa45000fd26c9956e6c4fcdc82cb80b263a9`; memory map SHA-256 `5fb17da2fe66dfb2fb350a038894d1c3cdcc79795d47ad701b92bb741f04a9a6`; report SHA-256 `4a914d5f018599700affa2d6776bde99a146f83a71eec16c31c4dc073a89602b`.
- No imported write-capable API was executed and no voltage was selected.

## Derived-artifacts manifest intent (2026-09-11T10:20:17.492828+00:00)

- Create a concise machine-readable inventory of the fresh readback, candidate binaries, parser reports, evidence maps, reviews, specs, and recovery runbook created/updated in this work.
- Record paths, SHA-256, size, evidence class, and status without copying raw secret/security material.
- Metadata only; no firmware/hardware mutation.

## Derived-artifacts manifest result (2026-09-11T10:21:52.870029+00:00)

- Created `evidence/firmware-audit/derived-artifacts-20260911.json`, SHA-256 `5275f96c3e1333bf543f8d2929bdecd1c0cfd6f584536771c366de3ed25c1219`.
- It inventories current readback, candidates, reports, maps, reviews, specs, and runbooks without copying raw secret/security material.
- Open runtime/signature/unit/MCP/JTAG gates remain explicit.

## Derived-artifacts manifest correction (2026-09-11T10:23:39.681010+00:00)

- Removed append-only action logs from the derived manifest hash snapshot to avoid stale self-referential entries. Current manifest SHA-256 `0aef5680451ea1d96ff1ff279872f29762b90b7d3f05e9723f1ca2493630f6ba`.

## Derived-artifacts inventory documentation result (2026-09-11T10:25:15.034809+00:00)

- Added F24 and firmware-audit memory link to the current derived-artifacts manifest.

## Stock-boot read-only telemetry runbook extension intent (2026-09-11T10:26:18.710596+00:00)

- Extend the recovery runbook with the next non-mutation stock-boot telemetry procedure needed for VCN/memory/SoC evidence.
- Prerequisite: remove programmer/clip and restore normal board power; no candidate flash.
- Documentation only; no current power-cycle or boot action.

## Stock-boot read-only telemetry runbook extension result (2026-09-11T10:27:23.940524+00:00)

- Runbook updated with a non-flashing stock-boot telemetry gate and stop conditions; SHA-256 `0d68e587e3525274c8eb9ac9a1174b87a1946febcc704d7022c161ab11229e79`.
- No power-cycle or boot action was performed in this session.

## SoC review hash-reference correction intent (2026-09-11T10:28:39.418251+00:00)

- Root SoC review was extended with runtime SMU API context after the memory map recorded its prior hash. Update only the map artifact hash reference, then re-run root map integrity checks.

## SoC review hash-reference correction result (2026-09-11T10:29:44.425048+00:00)

- Updated memory map root-review hash to `8de13ee8606f0c8ae9f29d874015fa45000fd26c9956e6c4fcdc82cb80b263a9`; current memory map SHA-256 `3b4a57c4cb978f2f004196312f3eadc6acd5e0f194e551986cb88b7381c58287`.
- Refreshed derived-artifacts entry hashes; current manifest SHA-256 `d660f10a675180bdc11131d918806b6a7b86decd80dd4ea7a3505332f1485f74`.

## Final static-review/manifest validation result (2026-09-11T10:31:56.075196+00:00)

- Map refs resolve with matching hashes; contour validation, 4 unit tests, and `git diff --check` pass.
- Native MCP port 8000 remains closed.
- Root SoC review is current SHA-256 `8de13ee8606f0c8ae9f29d874015fa45000fd26c9956e6c4fcdc82cb80b263a9`; memory map current SHA-256 `3b4a57c4cb978f2f004196312f3eadc6acd5e0f194e551986cb88b7381c58287`.

## JTAG readiness inventory intent (2026-09-11T10:34:36.233526+00:00)

- Record current read-only JTAG preparation state: CAD-derived J2 nets, host tool availability, physical/debug prerequisites, and explicit no-attach status.
- New output: `evidence/boardview/jtag-readiness-20260911.json`; no adapter attach, target reset, register access, or target-memory write.

## JTAG readiness inventory result (2026-09-11T10:35:56.475353+00:00)

- Created `evidence/boardview/jtag-readiness-20260911.json`, SHA-256 `8a4e35a2d5d34761b4275754e439e8af9374f60cc2c6d8ef6599efd15be738c7`.
- CAD-derived J2 mapping is preserved; no host JTAG tool is installed and all physical/debug prerequisites remain UNRUN.
- No JTAG attach, target read, register access, or target-memory write occurred.

## JTAG runbook link result (2026-09-11T10:37:00.992385+00:00)

- Linked the JTAG readiness inventory from the recovery-gate runbook; current runbook SHA-256 `95ab2bef6d8e28be158ec514a7178c100a3495aaa49c26db91ee4ab29c8cc610`.

## Completion matrix intent (2026-09-11T10:37:29.170749+00:00)

- Create a machine-readable objective audit matrix with PASS/INCONCLUSIVE/UNRUN/NO-GO statuses, exact evidence links, and next tests.
- New output: `evidence/firmware-audit/completion-matrix-20260911.json`; metadata only.

## Completion matrix result (2026-09-11T10:39:09.127197+00:00)

- Created `evidence/firmware-audit/completion-matrix-20260911.json`, SHA-256 `eaded6410497075f04a438f771fa068ef417bc44e8c06f1ae6ce14c51021c8e9`.
- Matrix audits each objective layer and explicitly records remaining runtime/MCP/JTAG/SoC gates; it does not mark the goal complete.

## Derived-artifacts manifest refresh result (2026-09-11T10:40:38.699456+00:00)

- Added current root SoC review, JTAG readiness, and completion matrix entries; manifest SHA-256 `a26076c63c85678a137ca005fe4e854d9da7f06da73a9f23d3433e031dff5f7f`.

## Continuation validation result (2026-09-11T10:43:54.078387+00:00)

- Map artifact references resolve with matching hashes; contour validation, 4 unit tests, and `git diff --check` pass.
- Native MCP port 8000 remains closed.
- Completion matrix remains `ACTIVE_INCOMPLETE`; no goal completion call was made.

## SoC-voltage encoding ambiguity artifact intent (2026-09-11T10:45:08.107044+00:00)

- Create a host-side comparison showing why raw AmdSetup values `0x23`, `0x50`, and `0x64` cannot be promoted to mV/VID/float encodings without a consumer trace.
- Reproduce formulas documented in imported `bc250_smu/codec.py` without importing or executing the write-capable API.
- New output: `evidence/firmware-audit/soc-voltage-encoding-comparison.json`; no voltage candidate/value selection and no hardware access.

## SoC-voltage encoding ambiguity artifact result (2026-09-11T10:46:30.740397+00:00)

- Created and integrated host-side formula comparison; artifact SHA-256 `3576ead3e78ab343cd93727046f2de44e135fb4a4d67024228fee114061823c5`.
- Current memory/SoC map SHA-256 `8d5acc1f3e68493f6536d80950f00ae6b8403ad6973def3d9e4c8bd64537ce9c`; root review/report updated.
- No voltage selected, no write-capable API executed, and no hardware accessed.

## Derived manifest encoding-artifact refresh result (2026-09-11T10:47:09.456151+00:00)

- Added `soc-voltage-encoding-comparison.json` to the derived-artifacts manifest; current manifest SHA-256 `5378bb4ec4f7f51fdf26583c37006c5e90ef890ad05e87e4e14ff36e2ea4fce5`.

## Root SoC review hash refresh intent (2026-09-11T10:48:26.463948+00:00)

- Root SoC review was extended with the encoding ambiguity artifact; refresh the memory map's root-review hash and rerun map integrity.

## Root SoC review hash refresh result (2026-09-11T10:48:57.771712+00:00)

- Refreshed memory map root-review hash `8916ecc37dd00e5f3d39c3fe2e4a6dffca44bb0f519cf7fc3e20f8e33c67b47d`; current memory map SHA-256 `d953eb7acbda967ee3f2db3a2392e8dcc6821597fbf5b21b781a88f68a962691`.

## Completion matrix refresh intent (2026-09-11T10:51:44.080247+00:00)

- Refresh the current completion matrix with root SoC review/encoding evidence and latest candidate/recovery statuses after the continuing static work.
- Metadata only; no hardware/firmware mutation.

## Completion matrix refresh result (2026-09-11T10:52:49.070314+00:00)

- Completion matrix now references root SoC review/encoding evidence and current map/candidate/recovery artifacts; SHA-256 `ffb21db9b1aa5db0b473dd097c91cf39be0692c4d276d298e14b311512812fa0`.

## Completion/derived manifest synchronization result (2026-09-11T10:53:23.391032+00:00)

- Refreshed derived-artifacts hashes after completion-matrix update; current manifest SHA-256 `b753cfba76d765bf3344498bcbdd39abfb21e9fddf3ae011c8738bfd43fc3428`.

## Continuation closing validation result (2026-09-11T10:54:19.958854+00:00)

- Completion matrix/map references pass; contour validation, 4 unit tests, `git diff --check`, and MCP port-closed check pass.
- Goal remains active; stock boot/runtime and remaining MCP context are not complete.

## Stock telemetry route safety clarification intent (2026-09-11T10:56:16.667720+00:00)

- Record that imported `a1_readonly.sh` includes an SMU Python section and `sudo` paths; despite its read-only label, the transport/constructor is not independently proven side-effect-free.
- Mark it as deferred and make sysfs/kernel read-only collection the first stock-boot route. No script execution or board access.

## Stock telemetry route safety clarification result (2026-09-11T10:57:53.163851+00:00)

- Recovery runbook marks imported `a1_readonly.sh` deferred until its SMU transport is independently reviewed.
- Direct sysfs/kernel/journal reads remain the first stock-boot route; runbook SHA-256 `4e783199fc88a158722755380ddb8c65810494a0a0e81079cd9e858db59a9b84`.

## Imported SMU helper read-only classification correction intent (2026-09-11T10:58:51.009357+00:00)

- Static inspection of `bc250_smu/api.py` and `transport.py` found that `Bc250Smu.__init__` opens PCI config with `O_RDWR`; `read_smu_reg` calls `write_config32(0xB8, reg)` to select an index, and `send_message` writes mailbox command/arguments. Even query-named APIs therefore are not proven hardware read-only.
- Correct the runbook/memory/maps/report to prohibit executing this helper in a read-only session. Direct sysfs/kernel/journal collection remains the only first stock telemetry route.
- No helper was imported/executed against hardware and no hardware mutation occurred.

## Imported SMU helper read-only classification correction result (2026-09-11T11:01:48.070867+00:00)

- Updated firmware memory, root SoC review, memory map, report F26, and runbook with the `O_RDWR`/selector/mailbox write finding.
- Current map SHA-256 `a24f66ddb114e2c37c6ca2c5eedcafd4fa71c69d959743fa370fe17b0d497bd1`; runbook SHA-256 `34cb8ac0245b9cd0851f4d8feddc9a348dd5a91d2b560acab23353003c32408a`; root review SHA-256 `85073a35337989a62e13a0c599076b9031c2852cd91788f815292962aab45565`.
- No imported helper was executed and no hardware mutation occurred.

## VCN map SMU-helper safety update result (2026-09-11T11:02:49.317819+00:00)

- VCN map now links `bc250_smu/api.py` and `transport.py` as write-capable source context; SHA-256 `6e4edaf7389ad1032a7b0d7131fc3bf9055606f76f6f2ccced770acda377970e`.
- Read-only runtime route remains direct sysfs/kernel/journal only.

## SMU helper safety map synchronization result (2026-09-11T11:03:53.303705+00:00)

- Updated VCN/memory/completion maps and derived-artifacts manifest with the write-capable helper classification.
- Current VCN map SHA-256 `6e4edaf7389ad1032a7b0d7131fc3bf9055606f76f6f2ccced770acda377970e`; memory map `a24f66ddb114e2c37c6ca2c5eedcafd4fa71c69d959743fa370fe17b0d497bd1`; completion matrix `4b610b8e9539721407103128a38ff5f604fee8f5a6543302a9fd10fb268d22df`; derived manifest `bcc98fcb9e6267421456997ac07c30cd94a13b6592005e585546012ee3768947`.

## SMU-helper correction closing test intent (2026-09-11T11:04:22.969081+00:00)

- Re-run map-reference verification, contour/unit/diff checks after the helper classification update.

## Root SoC review hash refresh intent 2 (2026-09-11T11:05:36.837954+00:00)

- Root SoC review was extended with helper safety correction; refresh the memory map's root-review hash and derived manifest entry.

## Root SoC review hash refresh result 2 (2026-09-11T11:06:22.954122+00:00)

- Updated map and derived manifest root-review hash to `85073a35337989a62e13a0c599076b9031c2852cd91788f815292962aab45565`. Current memory map SHA-256 `198e5b32c1bf1d5b0f518ee0128bd26907839fe9018b677c84e90116e3add270`; derived manifest `2c112694996f4d91b918054d7f5c4a3b92a5a125cac76cc11af9494dcd9fa82a`.

## Candidate review terminology correction intent (2026-09-11T11:07:27.289380+00:00)

- Independent APCB review calls bytes `0xAB1132`/`0xAB116E` the DFG value LSB. Direct little-endian bytes show the changed byte is word byte `+2` (`0x1F -> 0x7F`), not the least-significant byte (`+0`).
- Record this terminology correction in the root evidence/memory/report without changing the candidate or reviewer artifact; word values and exact offsets remain correct.

## Candidate review terminology correction result (2026-09-11T11:08:59.181818+00:00)

- Corrected root metadata/report wording: DFG bytes at `+2`, not LSB; candidate bytes unchanged.
- Updated APCB manifest SHA-256 `191b74eda51288e65e04aefa176109aa1096f4e861227437310423b5f6b40f30`, VCN map SHA-256 `e290d5233e8fdec331ea1a272b5de1bb46ff37baedac2f423266c7a07beaac84`, and derived manifest SHA-256 `df555ee7c686a4f3e29b82a5b25af015ac623244174de66296298c54ccca19ca`.

## Candidate terminology correction validation result (2026-09-11T11:09:48.335195+00:00)

- Map refs, contour, 4 tests, diff check, and closed MCP port pass after the metadata correction.

## Safe stock-runtime collector intent (2026-09-11T11:10:56.873203+00:00)

- Existing imported `a1_readonly.sh` is deferred because its `bc250_smu` transport writes PCI selectors/mailbox state. Create a separate collector that only reads allowlisted kernel/sysfs/journal/lspci/modinfo data and never opens PCI config or SMU transport.
- New script: `scripts/collect_stock_runtime_readonly.py`; no current board boot or collector execution.
- Acceptance: explicit allowlist, no SMU/mailbox imports, redacted sensitive-looking identifiers, dated output manifest, and safe `--help`/syntax validation.

## Safe stock-runtime collector fixture test intent (2026-09-11T11:14:01.338012+00:00)

- Create a synthetic sysfs fixture and run `collect_stock_runtime_readonly.py` with `--skip-journal`; no `/sys` target files or hardware are accessed.
- Exact test command: `python3 scripts/collect_stock_runtime_readonly.py /tmp/bc250-stock-collector-fixture-20260911/out --sysfs-drm /tmp/bc250-stock-collector-fixture-20260911/sys/class/drm --proc-cmdline /tmp/bc250-stock-collector-fixture-20260911/proc_cmdline --skip-journal`.
- Acceptance: one AMD card is collected, sensitive-looking UUID/serial text is redacted in sanitized output, fixture binary is hashed, manifest reports `hardware_mutation=false`, and no forbidden SMU/PCI paths are opened.
- Rollback: delete only the temporary fixture/output directory.

## Safe collector fixture result capture intent (2026-09-11T11:17:16.453880+00:00)

- Preserve sanitized host-fixture test outcome at `evidence/firmware-audit/collector-fixture-test.json` after deleting temporary fixture files.
- Include script hash, command, one synthetic AMD card, UUID/serial redaction checks, and mutation=false. No raw desktop or credential data.

## Safe stock-runtime collector fixture test result (2026-09-11T11:19:20.706304+00:00)

- `collect_stock_runtime_readonly.py` passed synthetic fixture test: one AMD card, 7 outputs, sanitized UUID/serial, fixture binary hash, `hardware_mutation=false`; process exited `0`.
- Temporary fixture/output was deleted. Evidence summary: `evidence/firmware-audit/collector-fixture-test.json`, SHA-256 `2c83872ef57929fdc5006e41ee67e4fe89db5bcc19137f57505419f1764c59f7`.
- Collector script SHA-256 `ea128ffe4f7fb7151fd63575722e570c7920547c6b8251f923227a447d4571a9`. No real board or SMU helper was accessed.

## Safe stock-runtime collector integration result (2026-09-11T11:22:57.730635+00:00)

- Runbook, completion matrix, firmware memory, and report now link the safe collector and fixture evidence.
- Real stock boot remains unrun; no board/programmer/register/JTAG operation occurred.

## Safe collector closing validation result (2026-09-11T11:24:39.174805+00:00)

- VCN/memory map references pass; contour validation, 4 unit tests, collector syntax, and `git diff --check` pass.
- Port 8000 remains closed.
- Real stock boot collector remains unrun and no hardware mutation occurred.

## AmdNbioSmuV10Dxe mailbox-context report intent (2026-09-11T11:28:33.357120+00:00)

- Preserve direct bundled Rizin disassembly around the observed Q2 command/response/argument constants and service helper functions.
- Input: `evidence/firmware-audit/dump-2-extract/modules/0031_AmdNbioSmuV10Dxe_pe32.bin`, SHA-256 `546a0689e607a3a87b8c437c7fe7191e55757f56b35792fb8d84f539844b500e`; Rizin `/tmp/.mount_CutterNJDkHb/usr/bin/rizin` v0.9.1 commit `c3a90e9226d977f58f4e9c75f78fa6b07afe13c7`.
- New report: `evidence/firmware-audit/rizin/AmdNbioSmuV10Dxe.mailbox-context.txt`; static output only, no input/hardware mutation.

## AmdNbioSmuV10Dxe mailbox-context report result (2026-09-11T11:29:03.640811+00:00)

- Report written: `evidence/firmware-audit/rizin/AmdNbioSmuV10Dxe.mailbox-context.txt`, SHA-256 `c81b065ee241d336efa5354b38aa44668f3041d3162254152e2563eaf8a4e76c`.
- Direct disassembly shows Q2 RSP `0x03B10564`, Q2 ARG `0x03B10998`, and Q2 CMD `0x03B10528` passed through `fcn.00012f34`/`fcn.00015090` service paths; it does not identify AmdSetup+0x6E6 consumption.
- Static-analysis only; no code/hardware execution.

## AmdNbioSmuV10Dxe mailbox-context integration result (2026-09-11T11:30:37.476744+00:00)

- Added direct Rizin mailbox report and linked it to memory/SoC review/maps.
- Current map SHA-256 `3a33d5b068fc45e0140b951c972c4e8ca67cfbdc2fe007dca6244be02a10f625`; root SoC review SHA-256 `6961bd0785d33fc88537870602796f48680bccc37efed82d53c02506600a1bf2`; report SHA-256 `39e93fcd6ac0f9cd0c45af52db5d90c41c94d785abf657a0bee6443c0a04bdd4`.
- No hardware or write-capable helper execution occurred.

## AmdApcbObrDxe DFG-context report intent (2026-09-11T11:32:09.149653+00:00)

- Preserve direct bundled Rizin disassembly around the APCB DFG wildcard handling function.
- Input: `evidence/firmware-audit/dump-2-extract/modules/0033_AmdApcbObrDxe_pe32.bin`, SHA-256 `e0bc6cb786469818ac6af66d7c2d06ffd5d9026ad550b651911e45334746604c`; Rizin v0.9.1 commit `c3a90e9226d977f58f4e9c75f78fa6b07afe13c7`.
- New report: `evidence/firmware-audit/rizin/AmdApcbObrDxe.dfg-context.txt`; static output only.

## AmdApcbObrDxe DFG-context report result (2026-09-11T11:32:45.489030+00:00)

- Report written: `evidence/firmware-audit/rizin/AmdApcbObrDxe.dfg-context.txt`, SHA-256 `fcb666f776d700933878024166c39929147cf06210d85fd9ffbeceac72241201`.
- Direct code context at function `0x119DC` checks APCB token words using mask `0x001FFF00` and compares to the wildcard marker; it loops token records and reports token offsets. The candidate word `0x007FFF00` preserves the lower masked wildcard (`0x007FFF00 & 0x001FFF00 == 0x001FFF00`) while extending upper bits. This is static semantic support for the APCB hypothesis, not PSP/runtime proof.

## APCB DFG static-context integration intent (2026-09-11T11:33:55.609471+00:00)

- Add the direct AmdApcbObrDxe DFG wildcard context report to the APCB candidate manifest and candidate catalog/report.
- Preserve the distinction: static semantic support only; no PSP, hardware, or VCN runtime claim.
- Metadata/documentation writes only.

## AmdApcbObrDxe DFG static-context integration result (2026-09-11T11:35:48.548834+00:00)

- Candidate manifest/catalog/report now link direct DFG consumer context. Current APCB manifest SHA-256 `8ad078ec33a164e08e79523496acc9b81dfa76f48d294540b47819854ec6639a`; VCN map SHA-256 `d1ad9c77de57113a954ecd7636ae0ca8d4d9295d2f7422f3951072ed8d581842`.
- Static support is recorded without promoting policy/runtime claims.

## AmdNbioGfxARIPei DF-window context intent (2026-09-11T11:38:35.925994+00:00)

- Preserve direct little-endian x86 Rizin disassembly of the TE module's DF indirect-window accessors.
- Input: `evidence/firmware-audit/dump-2-extract/modules/0193_AmdNbioGfxARIPei_te.bin`, SHA-256 `63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8`; force `bin.endian=little` because Rizin TE metadata otherwise reports a misleading endian.
- New report: `evidence/firmware-audit/rizin/AmdNbioGfxARIPei.df-window-context.txt`; static output only, no hardware operation.

## AmdNbioGfxARIPei DF-window context report result (2026-09-11T11:41:49.438253+00:00)

- Report written: `evidence/firmware-audit/rizin/AmdNbioGfxARIPei.df-window-context.txt`, SHA-256 `95ce1c7917dd12789e6af168dbbdfa046d0003ec653116e3f276da6ea74b8c68`.
- Direct forced-little-endian TE disassembly maps read/write helpers: `fcn.00014a35` forms DF indirect addresses using `0x405C`/`0x4098`; `fcn.00014b1f` writes a value through the DF window; `fcn.00014c0c` performs read-modify-write.
- This is static write-capable DF context, not proof of VCN or AmdSetup field use; no hardware/register operation occurred.

## CbsBasePei Setup-defaults context intent (2026-09-11T11:45:21.743631+00:00)

- Preserve direct forced-little-endian TE Rizin context around the function that writes default AmdSetup field bytes, including MCLK/UCLK/FCLK and VDDCR_VDD control/value.
- Input: `evidence/firmware-audit/dump-2-extract/modules/0204_CbsBasePei_te.bin`, SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`; Rizin v0.9.1 commit `c3a90e9226d977f58f4e9c75f78fa6b07afe13c7`.
- New report: `evidence/firmware-audit/rizin/CbsBasePei-setup-defaults-context.txt`; static output only, no hardware operation.

## CbsBasePei Setup-defaults static integration intent (2026-09-11T11:48:29.935829+00:00)

- Add direct CbsBasePei disassembly showing initialization writes for MCLK/UCLK/FCLK, voltage control/value, DF override, and power fields to the memory/SoC map and report.
- Classify it as static default-structure evidence, not proof of NVRAM read/SMU application/training.

## CbsBasePei Setup-defaults static integration result (2026-09-11T11:51:13.878785+00:00)

- Added direct CbsBasePei initializer context to memory map, root review, firmware memory, and report.
- Current memory map SHA-256 `5245ebbdd38673ff06a7fb622d751df7dc92f2451fd702fa0704da24829cfc92`; root review SHA-256 `fa6a69fb287901d56d5ec27ed7c553b03f2d61f59d58c519734041e885733281`.
- Static default corroboration only; no hardware/register writes.

## Root SoC review hash refresh after CbsBasePei integration (2026-09-11T11:53:18.089140+00:00)

- Refreshed root review hash `fa6a69fb287901d56d5ec27ed7c553b03f2d61f59d58c519734041e885733281` in memory map; current map SHA-256 `6e5530223f267f871d86f8b3129f1fa3da54d43f810f6291b035307af98fb38f`.

## Final static-context manifest synchronization intent (2026-09-11T11:54:20.072250+00:00)

- Refresh evidence-map artifact hashes and derived-artifacts entries after direct AmdNbio/CbsBase/AmdApcb Rizin context reports and root SoC updates.
- Re-run all non-hardware checks and confirm MCP port remains closed.

## Final static-context manifest synchronization result (2026-09-11T11:56:23.945088+00:00)

- Current VCN map SHA-256 `6b1ca1ee755983c298f4b1e44824c968b80666bad7cd1a3e251269c7bc834058`; memory/SoC map `6e5530223f267f871d86f8b3129f1fa3da54d43f810f6291b035307af98fb38f`; derived-artifacts manifest `33c1ea33efc8026b3db614b41c00f3803c18dc1ee070a57b1f8557b0d73ff24d`.
- Direct Rizin context reports and collector/encoding/JTAG artifacts are included; no firmware/hardware mutation.

## Static-context closing validation result (2026-09-11T11:57:44.621251+00:00)

- Map refs, contour validation, 4 unit tests, `git diff --check`, and MCP port-closed check all pass.
- Direct Rizin reports for APCB DFG, Gfx PEI DF window, CbsBase Setup defaults, and SMU mailbox are preserved.
- Runtime boot/telemetry and all hardware writes remain unrun.

## Candidate builder negative-test intent (2026-09-11T12:00:36.439991+00:00)

- Run both new builders against temporary corrupted baselines.
- APCB test corrupts one DFG byte; memory test pre-sets `MemoryClockSpeed` to `0x23`.
- Expected: both builders reject the unexpected baseline before writing output. Temporary files will be deleted after inspection; project inputs/candidates remain untouched.

## Candidate builder negative-test result (2026-09-11T12:03:03.582850+00:00)

- APCB builder rejected corrupted checksum (`stored=0xF2 calculated=0xF3`), returned internal `rc=1`, and created no output.
- Memory builder rejected pre-set field (`MemoryClockSpeed baseline: 0x23`), returned internal `rc=1`, and created no output.
- Temporary negative-test directory was deleted. Both candidate source/output files remain unchanged.

## Candidate negative-test metadata intent (2026-09-11T12:03:38.244362+00:00)

- Add the completed builder negative-test results to both candidate manifests and derived inventory.
- Metadata only; candidate bytes remain unchanged.

## Candidate negative-test metadata result (2026-09-11T12:05:12.420969+00:00)

- APCB manifest current SHA-256 `8aa0e639d91e2e937c1c561f9a0c205552a68801725d7c545ffa7d7c2bfacda3`; memory manifest `ec3e7772d6271c8eff70b4931ae2b7bd759e24282e16af4ba3021c46bfc12759`.
- VCN map `7070e9b19f8115a5ae40e47bf053fd851b782719361de813818dc893620b0b9e`; memory map `3c70d6b1cf39956bc7e45a9da70c43d660b1fdbc02e6fa0eaa62c67411921803`; derived manifest `0e12a3c50d74278d1549fd21fc0609e3ee78c51674baa9ad0ffbe5770d4f5a48`.
- Candidate bytes unchanged; safety rejection tests are recorded.

## Candidate negative-test closing validation (2026-09-11T12:06:10.237282+00:00)

- Map references, candidate hashes, contour validation, 4 unit tests, `git diff --check`, and closed MCP port all pass.
- Candidate bytes remain unchanged after negative tests and metadata updates.

## Deterministic audit-state verifier intent (2026-09-11T12:07:36.694180+00:00)

- Existing parsers/builders/reviews are complete but distributed; add a small verifier that checks their current hashes, exact candidate diffs, parser statuses, map references, and explicit incomplete gates.
- New script: `scripts/verify_bc250_audit_state.py`; new output: `evidence/firmware-audit/audit-state-verification-20260911.json`.
- Read-only operation over project artifacts; no firmware/hardware mutation.

## Deterministic audit-state verifier result (2026-09-11T12:10:22.642535+00:00)

- `scripts/verify_bc250_audit_state.py` completed exit `0`: `14/14` exercised checks passed; evidence `evidence/firmware-audit/audit-state-verification-20260911.json`, SHA-256 `d25777f9badce31633509f5746f590be0e843969c6bbce9148f2922128a6cc2b`.
- Verifier confirms baseline equality, exact candidate diffs/hashes, fresh parser results, review hashes, map references, and `hardware_mutation=false`.
- It retains open runtime/MCP/SoC/JTAG/write gates and does not mark the goal complete.

## Deterministic verifier integration result (2026-09-11T12:12:07.593923+00:00)

- Added verifier to completion matrix, derived manifest, firmware memory, and report. Completion matrix SHA-256 `7b4257bcd34a5a022bb423e36f518af3db708d4a9a0863f22845a8593353772c`; derived manifest `5c115349864018377af9b4e2f57900c67c32fe9e0c5a26d0ffd28fda1d5e0db2`.

## Current programmer attachment observation (2026-09-11T12:12:57.598498+00:00)

- Host read-only check still sees CH347T `1a86:55db` at `/dev/ttyACM0`; this confirms the programmer USB is still connected.
- No claim is made about clip contact or board power. Stock boot gate remains blocked until the operator removes the clip/programmer connection and restores normal board power.

## CoreUnlock Setup/PPT numeric coincidence analysis intent (2026-09-11T12:15:22.220084+00:00)

- Record the observed numeric coincidence between CoreUnlock's `Setup+0x1C4 == 0x000157C0` guard, current `Setup+0x1C4=0x00011940`, and `AmdSetup+0x70C=0x000157C0`, while keeping the two NVAR variables separate.
- This is static correlation only; do not infer that the guard is the PPT field without a source/data-flow proof.
- Update VCN map, root review/report, and firmware memory; no hardware/firmware mutation.

## CoreUnlock Setup/PPT correlation result (2026-09-11T12:16:40.930448+00:00)

- Added unresolved numeric coincidence to VCN map/report/memory; current VCN map SHA-256 `c05dc39e37420174c234d60f1bc64f048b734f220be0f075ec6ecbc429f2410e`.
- No semantic link or hardware claim was promoted.
