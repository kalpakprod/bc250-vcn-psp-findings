# Preconnection setup — draft, not final-image upload permission

This package preserves the full plan. It is not a substitute for electrical/runtime
acceptance and must not be described as an all-functions hardware-ready release.
No installation, configuration write, power command or firmware upload has been run.
The user requires the final complete image before uploading; that restriction remains.

## Files and offline inspection

Open `CONNECT.html` without internet. Drawings, vendor pinout and diagram behavior are
embedded. The UF2 download control remains disabled. `PACKAGE-MANIFEST.json` lists exact
per-file hashes; private backups, profiles and credentials are excluded.

From the unpacked folder, run read-only checks with the existing Python 3:

```sh
python3 scripts/check_waveshare_uf2.py Waveshare-RP2350B-Plus-W-DualSense-WiFi-MQTT-LinuxMetrics-TEST.uf2
python3 scripts/waveshare_bios_audit.py SOURCE_ROM --baseline PRISTINE_ROM --structure
```

The BIOS helper uses the packaged existing project parser. It does not write a ROM,
extract or print security material, or establish signature/PSP/hardware acceptance.

## Private network profiles (only after operator elects preparation)

The documented related env sources are `~/.config/eltex/wifi.env`, `mqtt.env` and
`ha.env`. Their names/permissions/assignment names were checked without emitting values.
The helper supports their observed names. It does not execute shell input, contact HA,
set supply/ACL approval true, modify source config or access a serial device.

```sh
python3 scripts/waveshare_private_profiles.py --destination ~/.cache/waveshare-private-profiles
python3 scripts/waveshare_provision_network.py --config ~/.cache/waveshare-private-profiles/network.json --dry-run
```

Destination profiles are owner-only and never overwritten. Do not upload them into
this public package or send token/password values in chat. HA power profile starts
with exclusive-supply and MQTT ACL confirmations false. Those are hardware/security
facts to verify, not fields for the agent to turn true merely to make a check pass.

After an independently approved final image is installed and its VERSION reply matches
its manifest, settings provisioning requires the exact expected source fingerprint:

```sh
python3 scripts/waveshare_provision_network.py --config PRIVATE_NETWORK_JSON --device VERIFIED_CDC --expected-version EXPECTED_SOURCE_ID --commit
```

This is not a command to run on the old controller or the current BOOTSEL drive.
It verifies VERSION before sending credentials, writes only the network config slot,
does not reboot and does not upload firmware. Actual execution remains unperformed.

## BC250 Linux integration (installation pending)

Copying scripts or a built plugin is not proof they are installed or running. A service
or system config change requires operator approval; no installer silently modifies it.

Read-only endpoint on the DMI-identified AMD:

```sh
python3 scripts/waveshare_host_metrics.py --serve
```

It binds `127.0.0.1:8766`. Decky uses that one collector, not another hardware reader.
For the verified Waveshare CDC, explicitly start the foreground bridge:

```sh
python3 scripts/waveshare_host_metrics.py --device VERIFIED_CDC --watch
```

A different laptop is refused by DMI. CPU/GPU temperature/power are measurements,
not invented zeroes; absent/stale values remain unavailable.

The compiled `decky-plugin/` requests no root and has no install/migration hooks. Place
it only through the operator-approved Decky installation process. Live Steam UI,
installed APIs and host version compatibility remain untested.

## Power and diagnostics (never automatic by package extraction)

The HA helper defaults to dry-run; actual power-on requires explicit execution plus
private supply confirmation and agreement of direct physical relay/HA OFF replies.
PS watching additionally requires authenticated MQTT and confirmed owned-topic ACL.
It never powers off the relay or resets a board. Graceful local shutdown is a separate
explicit command, requires local BC250 DMI and never invokes a generic shell or sudo.

UART capture requires physical level/ground/connector acceptance and the installed
source fingerprint. It remains disabled by default, configures no TX pin and prints no
raw logs. Use only the conditional drawing after actual measurements; no JTAG, PMBus
write, SPI override, PSP bypass or arbitrary hardware control is authorized here.

## Final acceptance still required

Verify exact image/source/guide association; approved upload; powered-hub behavior;
actual controller input/audio/microphone/feedback; networking/HA/Decky and fresh values;
electrical checks before any GPIO; restoration; reconnect/cold-start cycles; ordinary
gameplay and observation. Keep unresolved items open in the requirement matrix.
