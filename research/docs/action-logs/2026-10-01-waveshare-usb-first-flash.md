# USB-first controller/diagnostic UF2 flash intent

- Target: Waveshare RP2350B-Plus-W (RP2350 BOOTSEL)
- Image: reports/waveshare-implementation-20260930/guide/Waveshare-RP2350B-Plus-W-USB-first-controller-diagnostic-TEST.uf2
- SHA-256: aba20b1dc0193c6484d93937425b4451df0fbcb9df6ac560fc5040365926bfa3
- Approval: explicit owner approval in chat for this exact SHA-256
- Purpose: install USB-first state-machine candidate after hardware USB-only enumeration proof.
- Recovery: original matching 16 MiB dumps retained at ~/.cache/waveshare-recovery-current-20260930/; recovery UF2 remains available.
- Stop conditions: absent RP2350 BOOTSEL, hash mismatch, copy error, or no reboot event.
- No AMD/SPI/PSP write is performed by this operation.

## Result

- Preflight hash: matched.
- BOOTSEL identity: RP2350 bootloader
- UF2 copy: OK.
- Reboot/unmount: observed.
- Post-write USB listing and device node recorded above in the terminal evidence.
- VERSION/STATUS: pending read-only query after ACL check.

## CDC probe result

- Operator restored ACL on `/dev/ttyACM0`.
- Sent `PING`, `VERSION`, `STATUS`, and `HELP` with CRLF; host writes completed with exit status 0.
- No CDC replies were observed.
- Interpretation: USB enumeration is confirmed, but this run did not reach command acceptance. The likely next discriminator is a fresh reset with a probe sent immediately during the 1.5 s USB-first window; no CYW43 failure is claimed until that timing-controlled test is observed.
