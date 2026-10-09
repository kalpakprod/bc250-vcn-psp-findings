# Authorized UF2 upload

Owner authorized exact e822a65145dbe23cef60a22cf098223707cccef2db9f7ef2bcdbd62a9444ecaa image. Hash matched. Both recovery copies matched recorded hash. Attempted picotool load -v; exit 249, no accessible BOOTSEL device. No write observed. Retain authorization, await physical BOOTSEL connection.

Ledger update intent: append this observed failed execution without changing prior results.

## Dispatcher execution

- Exact authorized UF2 hash matched e822a65145dbe23cef60a22cf098223707cccef2db9f7ef2bcdbd62a9444ecaa.
- Dynamic USB discovery found no RP2350 BOOTSEL device. `picotool info` and `picotool load -v` both exited 249; no write occurred.

## Approved image loaded

- BOOTSEL appeared as 2e8a:000f. `picotool info` identified RP2350 ARM Secure.
- Exact approved UF2 loaded; independent picotool verify reached 100% OK; reboot exited 0.
- After 3 seconds application USB did not enumerate and no ttyACM existed. Hardware acceptance and readback remain incomplete.

## Independent readback

- BOOTSEL returned as 2e8a:000f. `picotool save` read 820,784 program bytes; SHA-256 `8690c616c9dfff6ede00b2e7b337515d3cbe69740acae2aa6c5354486662da75`.
- `picotool verify` against the exact approved UF2 returned `OK` through 100%. The programmed image matches the candidate. Application USB enumeration remains unverified/absent.
