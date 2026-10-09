# Read-only Waveshare host inspection

The approved full-adapter plan is `.procoder/plans/20260930-waveshare-full-adapter.md`.
This helper implements host evidence collection for its first acceptance stages,
not firmware flashing, Bluetooth pairing, feedback generation or power control.

```sh
python3 scripts/waveshare_probe.py --device /dev/ttyACM0 --timeout 1.5
python3 scripts/waveshare_probe.py --fixture reports/waveshare-implementation-20260930/cdc-baseline-fixture.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_waveshare_probe.py -v
make test
```

Prefer the observed `/dev/serial/by-id/` link if the CDC number changes. Device-node
access must already be authorized. The helper does not call sudo/pkexec, reset,
change modes or flash anything. In Omarchy, use sudo only in an interactive terminal;
an agent without an interactive authentication channel must use the system's
pkexec dialog for approved privileged actions, not request passwords in chat.

## JSON evidence

- `evidence_class` distinguishes actual device queries from offline fixtures.
- `hardware_acceptance` is always false: a protocol reply is not gameplay proof.
- `replies.VERSION` includes only recognized revision, UTC build time and mode.
- `replies.STATUS` recognizes legacy `MODE controller` and modern
  `STATE mode=controller`; a bare `OK` is `acknowledged_unknown`, not a state.
- `consistent_mode_reply` means the two recognized modes agree. A revision label
  does not prove that installed flash bytes equal a Git commit or a preserved UF2.
- `usb` inventories only the CDC USB ancestor and associated gamepad event nodes.
  USB IDs do not prove a physical board identity; event nodes do not prove input.
- Exit 0 means the recognized mode replies agree. No reply, conflict, access error
  or malformed fixture exits 1. An invalid CLI argument exits 2.

Reads are limited by time and byte count. Only VERSION and STATUS are sent. Terminal
settings are restored on exit. An advisory lock detects other users of this helper,
not every possible serial program. Unrecognized logs, MACs, credentials and serial
numbers are never stored. The helper does not capture keyboard or microphone data.

## Observed 2026-09-30 boundary

The installed firmware replied `c1e7627`, build UTC `2026-09-28T21:32:39Z`,
mode `controller`. Legacy STATUS also returned `MODE controller`.
The user reports the DualSense is still blinking. The current USB HID kernel probe
failed with expected feature response length 20, received 1, error -22; there is
no registered gamepad input node. This host initialization failure is distinct
from the unconfirmed Bluetooth pairing. Passive CDC observation supplied no logs.

Preserved source/build artifacts are not an installed-flash readback. Recovery,
powered-hub behavior, pairing, input, audio and feedback remain unaccepted.
No subagents are permitted by the latest user instruction. Independent cross-family
review has not been performed and is not replaced with a claimed self-review.

## Expanded offline candidate (not final, no upload authorization)

The candidate copy under `candidates/waveshare-adapter-safe-v001` now includes
asynchronous Wi-Fi, token-authenticated read-only HTTP, telemetry-only MQTT and
three allowlisted Linux-origin measurements. Network configuration is a CRC-protected
local CDC frame; its sector `0xFFC000` is separate from Bluetooth keys and the
controller config. No real credentials have been provisioned. Authentication token
and MQTT credentials belong in a private, owner-only JSON file, never the repo.

`waveshare_provision_network.py --dry-run --config PRIVATE_FILE` validates shape
without accessing a device or printing values. Actual provisioning is explicitly
requested with a verified CDC device; `--commit` writes settings, not firmware,
and does not reboot. This helper must not be used on the old installed firmware.
Only a future approved full adapter build with the matching protocol may receive it.

The host measurement bridge verifies BC250 DMI before sending `HOST_ALIVE` and
fixed `METRIC` commands. A lost heartbeat gives unknown power, never off. Measurements
become null after five seconds. The collector is not installed on AMD or as a service.
The default HTTP endpoint listens only on loopback. Firmware HTTP is LAN-only and
read-only, with a token for status; local HTTP/MQTT are not encrypted transport.

The generated HTML is a draft. It uses actual CAD connector coordinates, contains
no private dumps or credentials and disables intermediate UF2 downloads. The user
requires the final full image before any upload. Physical power control, external
GPIO connections, Decky integration and full hardware acceptance remain unfinished.

## Additional staged integration checks

Read-only Decky frontend/backend now typecheck and build locally. They use the same
loopback collector, reject stale/wrong-source/nonfinite values, request no root and
perform no install/migration actions. `@decky/api` and `@decky/ui` are LGPL-2.1;
license texts are included in the plugin, package lock is retained, and the published
sources are identified in its README. Live Steam/Decky installation is still pending.

The optional power-on host helper is not installed or enabled. It reads the fixed
owned relay state and fixed HA switch, requires agreement on OFF plus confirmed
exclusive BC250 supply, and defaults to dry-run. It has no power-off/reset command.
`--on-ps` reads one fresh nonretained status from the exact adapter MQTT topic before
considering the same gate. Missing/foreign/retained/unknown input never actuates.
HA credentials are owner-only file values; they are never sent to the relay endpoint.
Tests use fake APIs; no actual relay or Home Assistant call has been made.

## Goal continuation: passive diagnostics and freshness closure

UART is now implemented as a default-disabled, explicitly confirmed RX-only observer
on UART1 GP9. It maps no TX pin and clears the TX-enable bit; default UART stdout is
removed to avoid accidentally driving GP0. A native mocked test verifies no GPIO
calls before confirmation, fixed 64-byte per-loop service budget and bounded 8 KiB
history. `UART_LOG` transfers only bounded USB-local chunks; it is not exposed over
HTTP or MQTT. The capture helper verifies the exact installed source fingerprint,
requires operator level/ground/connector checks, saves to a new mode-600 file and
prints only byte count/hash. This is code acceptance, not a wiring authorization.

The BIOS helper is offline integrity comparison only. It does not flash, modify,
map injection offsets, emit key material or assert preservation of signed regions.

Power-on consumption now uses a genuine recent PS rising-edge sequence, boot ID,
queue age and owner-only event deduplication. Held button state, old queue samples,
retained messages, unknown age and stale events cannot trigger it. The actual lwIP
MQTT default output buffer was only 256 bytes; the candidate now reserves 1024 bytes
for its bounded status publication. No actual MQTT/HA actuation test was performed.

HTTP callback scratch buffers are static in NO_SYS polling mode, not nested on the
measured 2 KiB main stack; all tcp_abort paths return ERR_ABRT. Failed/new/timed-out
private config frames invalidate the prior staged credential record.

## Preconnection readiness and graceful shutdown

The full, unshrunk requirement audit is in
`reports/waveshare-implementation-20260930/readiness-matrix.json` and `READINESS.md`.
It distinguishes code/build proof, electrical evidence, installation and runtime
acceptance. No passing host gate is used to prove the whole adapter ready.

Official vendor pinout asset was inspected and hashed: component side, USB-C up,
UART1 RX GP9 is physical left header pin 12, adjacent GND is pin 13. The draft guide
now embeds that manufacturer drawing and illustrates the two conditional receive-only
wires from CAD J5 pin3 U_TX and pin2 GND. Actual board voltage/ground/connector checks
are still required before connecting or enabling UART; no TX/power wire is added.

`scripts/waveshare_shutdown.py` adds only explicit graceful shutdown of the local
DMI-identified BC250. Default dry-run and all non-BC hosts are nonmutating. The fixed
command `systemctl poweroff` is invoked only with explicit execution; no sudo bypass,
relay-off, restart or arbitrary command interface exists. Tests use a fake executor.
A successful request is not reported as verified power removal or successful boot.
No real shutdown has been executed during development.

## Controlled protocol integration (not live acceptance)

`test_waveshare_mqtt_transport.py` exercises the actual MQTT client byte protocol
through a socketpair fake broker: credential flags, topic subscription, retained and
historical rejection, fresh event acceptance, packet deadline and disconnect. It never
connects to the real broker. `test_waveshare_ha_transport.py` uses controlled urllib
responses to prove that HA Authorization is not forwarded to the relay target, the
service/target is fixed, redirects and oversized responses are refused.

The native network harness includes the exact staged `adapter_network.c` behind
mocked SDK/lwIP functions. It tests authorization, read-only exact route selection,
copy-before-free response handling, abort callback result and HTTP session accounting.
One web connection is bounded so it cannot consume both TCP PCBs and starve MQTT.
Mock flash callbacks assert if reached. This is not an evaluator of board timing.

The firmware's embedded Russian panel now renders named metrics instead of an
English placeholder. Its UTF-8 bytes and header are checked against the existing
2920-byte TCP send window without increasing that window; malformed/failed replies
clear the old displayed values. Browser fixture tests on desktop/mobile verify units,
null data, failure state clearing, no JS errors/external requests/overflow. Real tokens,
WiFi and controller state are not used in those tests.

BC250 community source reports actual SuperIO hwmon name `nct6686` under both kernel
module variants. Collector and Decky now preserve that source; no assumption of PWM
control follows from the hwmon name. Installing or operating a fan-control driver is
not performed by these read-only telemetry tools.

## Portable preconnection bundle and credential staging boundary

The explicit packaging helper ships offline HTML, image/sidecar, readiness/setup docs,
selected standard-library helpers including the existing firmware parser, built Decky
frontend/backend and retained dependency/license metadata. It excludes private recovery
reads, real profiles, env files, tokens and dependency caches. New archives are exclusive
and every packaged file is reopened and hash-checked; validators were also run from an
independently extracted cache folder. This remains a draft, not full hardware acceptance.

The profile helper reads only documented owner-only env assignment files, never sources
or evaluates a shell, writes only new owner-only profiles and leaves supply/MQTT ACL
confirmations false. It has been exercised on synthetic inputs only. Real assignment
names/permissions were inspected without emitting values; actual private values were not
copied or provisioned. Credential transmission now requires the exact expected compiled
source fingerprint before NETCFG: a controlled serial test proves a wrong/old device gets
VERSION only, never the credential frame. An intermediate upload is still not authorized.

The SDK default diagnostic USB output timeout was 500000us. The candidate now explicitly
sets zero stdout/connect-wait/mutex-blocking timeouts, preserving host-independent startup
and command replies through its separate bounded pending buffer. Actual compile flags are
checked rather than relying on source text alone. The legacy WoL switch's contradictory
CYW43_LWIP=0 definition was removed; networking is defined once by the selected SDK target.

### UART correction, 2026-09-30

Earlier J5 pin3-to-GP9 draft is superseded: CAD U_TX/J5.3 leads via R9557 to UIO1.33 SINA (input). J5.4 U_RX leads via R9558 to UIO1.34 SOUTA (output). Official Nuvoton NCT6686D v0.5 section4.4 confirms direction; output type O12p3 means3.3V in legend. UIO1 supplies CAD pins1 SIO+3V and46/85 +3VSB_A. Design documentation is not measured specimen acceptance. See uart-net-trace.json for exact source/hash and conflicting table heading. User is not asked to use a multimeter. Existing draft packages are not instructions to wire during gameplay.

### Passive diagnostic mode

MODE diagnostic is explicit RAM-only selection, numeric ID5 preserves0-4. USB/BT controller output, audio processing and wake/button actions gated while diagnostics selected; CDC/network/RX observer polling continues. Leaving diagnostic requires fresh BT input for HID forwarding; heldPS is rebaselined without an artificial rising event. UART capture now selects diagnostic after version check and restores original mode; no legacy rig/TOCTOU activation, mode flash write or reboot. Native/fixture checks do not establish hardware behaviour.

### Bounded passive waveform observer

PIO/DMA input-only GP10-CS,11-clock,12-MOSI,13-MISO, explicit diagnostic mode + selected3.3V scheme confirmation. Finite2048words/16384samples at unchanged clk_sys (default150MHz), 1s no-trigger timeout; no master SPI commands/PROGRAM# drive/flash writes. Local CDC chunks32words, raw trace not network-published. This is NOT a full ROM dump or proof of133MHz/quad/QPI capture. Mock-SDK test uses actual sampler C source to exercise resource failure/bounds/timeout/disarm; physical acquisition remains unperformed. Host private capture helper is still pending.

### Private host SPI waveform capture

`waveshare_spi_capture.py` uses the existing fixed-command CDC exchange, exact expected sourceID VERSION and explicit selected-scheme confirmation before capture. Reserves a new mode600 file, selects diagnostic, checks finite completed metadata then fetches64 fixed32word chunks (8192bytes); always attempts disarm and original-mode restoration, records acknowledgements. Format: one JSON header line plus little-endian32bit PIO words, eight4bit samples perword (CS/CLK/MOSI/MISO). Header records sampleHz/hash and full_rom=false/quad=false. No command/address decoding, external master requests, reset, raw network output or fullROM claim. PTY/file mocks are protocol tests, not hardware observations.

### SPI waveform timing correction

The finite PIO now consumes a sample counter then samples via IN+JMP, so sampleHz=clk_sys/2 (75MHz at150MHz sys), not150MHz. It stops issuing IN after16384 samples instead of filling/stalling after DMA completion. RXSTALL during acquisition invalidates the trace as overrun and clears it; no silently stretched timeline. Mock SDK regression first failed overrun assertion exit134, then passes after change. Hardware overrun sensitivity/actual capture still untested.

### Conventional NOR operation core (owner optionA)

Pure frame+engine modules support bounded normal memory requests, WREN/WEL checking, busy polling and readback verification of page/sector.5s operation deadline and ownershiploss abort. Transport contract is a nonblocking callback, tested only with an emulated NOR. Physical SPI/GPIO transport and caller-bound exact chip/image approval are not implemented here; do not treat supplied approval booleans as hardware evidence. No PSP race, substitution, raw arbitrary opcode or network write path. All actual image/recovery/readback gates remain required.

### SPI transport and common wiring profile

New transport source uses hardwareSPI1 fixedGP10SCK/11MOSI/12MISO/13CS; passive PIO updated to those same wires with input orderCLK/MOSI/MISO/CS, wait pin3. Earlier passive orderingCS/CLK/MOSI/MISO is superseded before physical SPI instructions. Transport is disabled until diagnostic+explicit wiring/isolation confirmation, polling64iterations, transfer timeout1s/sessionlease10s, cleanup resets pins toinputs. No active CDC endpoint exists yet; exact image permission/chip authority must be bound in later integration. Native mockSDK tests are not real GPIO or bus-isolation acceptance. Do not connect/drive shared bus based on these source tests.

### Defensive preservation preflight

Host write-plan now reuses firmware_audit PSP parser, bounds64directory graph/1024entries, checks directory checksum and in-image references; candidate must preserve whole conservative boot/PSP prefix and every referenced blob/directory. Unknown/unmapped PS1 markers fail closed, no guessed envelope. This is unchanged-byte coverage, not signature authentication or complete proof of all firmware signed regions. Physical execution remains unauthorized by generated plan. Native synthetic corrupted PSP first passed erroneously (testfailed), now rejects; owned dump/2.bin unchanged self-check passes current parser scope without exposing body/key data.

### Bound destructive service API

Approval checks current adapter UIDtag (not unique flash-chip UID), observedsupportedJEDEC and modegeneration, approvedimage digest/matchingbackup digests, hostrecovery+protected-region attestation. Stage copies one4096sector immutably; pagepayload must match its exactbytes and stay in authorizedsector. On SPItransaction rearm low-levelauthority reconstructed only from cached approved sector; verify mismatch revokespermit. No cryptographic owner authentication or firmware full-image digest computation claimed; trustedhost preflight/actual owner image approval and physicalisolation remain separate. USB erase/program commands not yet exposed.

### Final RAM closure for framed localUSB writer

Audio stack restored32KiB. CDC framed receiver leases inactive passive8KiB sampler scratch instead of dedicated4140bytes. Lease is exclusive; sampler start rejects while leased; release wipes payload. No immutable sector cache removed. ARMbuild/sourceID 4a057d873ab5 verified, native samplermock tests confirm lease/start rejection/zeroing, exactCDC→NORemu writes/readback pass. Full hardware/runtime acceptance and remaining project interfaces still pending, image remainsNOT_FINAL.
