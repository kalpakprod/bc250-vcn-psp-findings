# Status and evidence boundary

Snapshot: 2026-07-30

## Confirmed

- The owner-controlled research console runs system software 9.00.
- pOOBs4 source was pinned to `886f4a07d0793ea6ee945ba064c6056e3af0231c` and its exploit image was inspected read-only.
- The malicious exFAT Upcase entry declares `FirstCluster = 3` and `DataLength = 0x00ff000000001000`, while the stored table data is only a few KiB.
- The JavaScript exploit sprays `kqueue`/`knote` objects, maps fake structures at low addresses and obtains control during cleanup of a corrupted `knote`.
- Official PS4 firmware 13.52 was acquired from Sony HTTPS and identified as system version `13.520.000`, SDK `13.520.001`.
- The outer `SLB2` container was parsed read-only into two bounded inner entries; both remain protected/encrypted.
- A bounds-hardened OpenOrbis decryptor package was built and locally package-validated, but was not transferred, installed or executed on a PS4.
- Dropbear upstream `2026.91` at commit `ee65bff1567576a223febcdd5ae552326a4da4b1`, PS4 app v1.07/internal Build 57, completed reboot-surviving live tests on the owner-controlled 9.00 console.

## Plausible models

- `/dev/pup_update0` is an operational interface into a privileged PUP-processing path rather than a readable key file.
- The path likely crosses kernel/PUP-manager and secure-processor trust boundaries before returning verified or decrypted data.
- Successful PUP decryption can be implemented as an oracle while all key material remains inside SAMU or a non-exportable key slot.
- A LilyGO T-Embed CC1101 is useful to PS4 research mainly through its ESP32-S3 WiFi, USB-OTG and GPIO capabilities, not its CC1101 sub-GHz radio.

## Unverified

- Exact ownership and lifetime of ciphertext, plaintext, DMA and mailbox buffers in the PUP pipeline.
- Whether any temporary or reusable PUP key becomes visible to the x86 kernel.
- Any mailbox command that exports SAMU key material.
- Sony exFAT implementation details in 9.00, the exact 9.03 fix and later changes through 13.52.
- Survival of the documented sibling exFAT candidates on 13.52.
- Any complete, reproducible public kernel exploit chain for 13.52.

## Explicit non-claims

- PUP decryption does not imply key export.
- A symmetric PUP key is not Sony's private signing key.
- Kernel control does not automatically expose SAMU-internal secrets.
- A structurally valid custom PUP is not accepted by unchanged retail secure boot without valid Sony authorization or a separate verification bypass.
- Local OpenOrbis PKG validation is not Sony retail signing.

## Excluded operations during this snapshot

No 13.52 firmware update, PUP decryption run, malformed-media write, kernel race, hardware probing, glitching, NOR/Syscon modification or deployment of the prepared decryptor occurred during the documented 13.52 preparation phase.
