# PSP/TOCTOU implementation result, 2026-10-07

## Software result

Implemented `candidates/single-flash-emulator-v001/toctou_plan.py` around the existing lossless sparse image packer and bounded `SpiNorModel`.

The plan now:

- pins SHA-256 identities of exact stock and candidate images;
- requires explicit `read_index`, address window and image for every substitution;
- rejects overlapping windows, wrong image bytes, wrong capacity and unknown image names;
- keeps unsupported opcodes, short headers and out-of-range reads rejected;
- exports hardware state as disconnected, untested and unauthorized.

Updated `README.md`, added `specs/2026-10-07-psp-toctou-implementation.md`, and added three regression tests.

Verification:

- candidate tests: **24/24 PASS**;
- exact serve-map builder: **PASS**;
- stock SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`;
- candidate SHA-256: `91de01eb7cb8e97014294adc8692eb8be66c3f95ce8481c234805544c0ddd517`;
- serve-map: 6 changed ranges, 14,442 changed bytes;
- anchor-sensitive changed range: `0x9db560..0x9db6a0`.

## Concrete blocker for hardware TOCTOU

The available hardware is Waveshare plus wires. The documented single-flash topology needs the SB_SPI_DO/MISO path to be physically interrupted between the BIOS flash and FCH/PSP, with one side going to the RP2350 input and the other to its MISO output. The local wiring guide states this explicitly and gives two alternatives: interrupt the trace or remove the chip and use a socket/interposer.

J4004 alone is the shared programmer header. Wires there do not isolate the original flash: both the original flash and an RP2350 output would be able to drive the same MISO line. The existing runtime therefore keeps `ADAPTER_TOCTOU_WIRING_CONFIRMED` disabled. Enabling it now would be an unverified electrical change and could cause bus contention or damage.

The current firmware runtime also does not yet implement a single-flash MISO data responder from Waveshare QSPI storage; the old runtime switches/observes CS but is not that responder. The offline pipeline is therefore complete at its honest boundary, while a working physical PSP/TOCTOU run is blocked by the missing MISO isolation/interposer and the missing validated response path.

No BC250 connection, soldering, trace cut, chip removal, reset, BIOS write or firmware flash was performed.
