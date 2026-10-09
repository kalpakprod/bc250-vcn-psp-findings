# Waveshare upstream research: falsification and corrections

Target: existing waveshare-adapter-safe-v001; no source patch or hardware write.
Research objective: reuse existing software without promoting upstream comments or issue reports into local hardware conclusions.

## New evidence

1. Official TinyUSB has examples/device/cdc_uac2. README explicitly documents composite CDC+UAC2 on Pico. CFG_TUD_CDC=1 and CFG_TUD_AUDIO=1. This disproves the broad inference that CDC+audio is inherently unsupported. It does not establish this project's DualSense/UAC1/HID/CDC layout on RP2350.
2. Preprocessing the actual compile_commands.json commands for pico_stdio_usb/stdio_usb.c succeeded (exit 0): PICO_STDIO_USB_ENABLE_TINYUSB_INIT=0 and PICO_STDIO_USB_ENABLE_IRQ_BACKGROUND_TASK=0. Consequently previous claims of automatic double initialization or competing IRQ task ownership are not established for this build.
3. Main ELF disassembly confirms stdio_init_all precedes explicit tusb_rhport_init. This is a real ordering difference from upstream. With NDEBUG, the SDK tud_inited assertion is compiled out; its absence alone does not establish a hang or broken enumeration.
4. The SDK flash.c can return PICO_ERROR_NOT_PERMITTED when lockout is not ready. btstack_flash_bank.c ignores that return in erase and write. Current compiled settings are NDEBUG=1, PICO_FLASH_ASSUME_CORE1_SAFE=0 and multicore-lockout support=1. This supports a persistence defect under the stated prerequisites, not the previous claim that it causes the observed silent CDC.
5. BTstack TLV initializer's missing-bank path erases/formats and returns the TLV implementation; an unsuccessful write alone is not shown to terminate main or stop CDC.
6. main's CYW43 failure branch still enters a loop calling cyw43_arch_poll and bridge_tick despite no successful bridge initialization. This is a separate source-level defect to test, not a proven observed cause.

## Decisions retained / corrected

- Retain DS5Dongle as controller base and Linux Bridge as source/issue reference.
- Do not remove CDC, remove Wi-Fi, replace the approved all-in-one scope with separate products, or require extra UART hardware solely from upstream anecdotes.
- Isolation build profiles can diagnose features; they do not redefine the final deliverable.
- Preserve one current target, recovery, hashes and exact-image approvals.
- No claim that PSP/VCN is unlocked; no active PSP experiment is performed.
- GPL reuse requires compliance; rewriting GPL code after reading it is not automatically a licensing workaround.

## Reproducible evidence

SDK: 079c6f39023649b154152db30f1d781e884879bc
TinyUSB: 3af1bec1a9161ee8dec29487831f7ac7ade9e189
Compiled macros: /home/OWNER/.cache/bc250-upstream-research-20261001/compiled-macro-evidence.json
ELF: /home/OWNER/.cache/waveshare-adapter-safe-v001-build/unified.elf
Sources: pico_stdio_usb/stdio_usb.c, pico_stdio_usb/include/pico/stdio_usb.h, pico_flash/flash.c, pico_btstack/btstack_flash_bank.c, BTstack/platform/embedded/btstack_tlv_flash_bank.c.

Next unanswered checks: current CDC byte transport, exact composite descriptor integrity, measured startup stage, and resource budgets. No further firmware choice follows from this audit alone.

## Hardware discriminator after the audit (2026-10-01)

Current flashed image was inspected read-only while enumerated as 054c:0ce6:

- negotiated USB Full Speed 12 Mbps;
- `bcdDevice=1.00`;
- device class Misc/IAD;
- 6 interfaces;
- CDC IAD interfaces 4/5 present;
- CDC ACM/Data descriptors and endpoints present (notification EP 0x85, data OUT 0x06, data IN 0x86);
- configuration `wTotalLength=0x012d`.

A host probe set DTR/RTS, sent `PING`, `VERSION`, and `STATUS`, and received zero bytes for each. Therefore enumeration and descriptor presence are hardware-observed, while command acceptance is not. This narrows the fault to runtime startup/CDC service or transport state; it does not justify blaming malformed descriptors or DTR alone.

## Official TinyUSB composite cross-check

The installed SDK includes `examples/device/cdc_uac2`, a documented CDC+UAC2 composite example. Its descriptor source explicitly warns that the same VID/PID with different interfaces can produce a host error. The example uses one static descriptor, a class-map PID, IAD, fixed endpoints and compile-time total-length macros. This is positive evidence that CDC+audio is supported in principle, but it reinforces the requirement not to change a Sony VID/PID composite layout dynamically without a descriptor/version strategy.

## UART build contradiction (2026-10-01)

- Current CMake explicitly contains `pico_enable_stdio_uart(unified 0)`.
- Current ELF contains `uart_init` as a hardware API symbol but no `stdio_uart` driver symbols.
- Official `awalol/DS5Dongle` CMake uses `pico_enable_stdio_uart(ds5-bridge 1)`.
- `kungaa/DS5-Linux-Bridge` CMake explicitly documents diagnostics on UART0 GP0 at 115200 8N1 and sets `pico_enable_stdio_uart(ds5-bridge 1)`, `pico_enable_stdio_usb(ds5-bridge 0)`.
- Therefore the current flashed image cannot produce upstream-style `printf` diagnostics on GP0; the existing guide's proposed UART debug path is not enabled by that image.

## Host probe compatibility finding

Official TinyUSB `cdc_uac2` callback checks `tud_cdc_connected()` (DTR) before reading/echoing CDC data. Existing `scripts/waveshare_probe.py` opens the tty and sends commands but never asserts DTR/RTS via TIOCMBIS/serial API. Therefore that probe is not a valid compatibility test for upstream-style CDC callbacks. The manual discriminator asserted DTR/RTS and still received zero bytes from the flashed image; the probe script should be extended before using it as a universal CDC verdict.

## Existing SDK runtime recovery path

Pico SDK `pico_usb_reset/usb_reset.c` already provides a CDC line-coding reset: when `PICO_ENABLE_USB_RESET_VIA_BAUD_RATE=1`, setting CDC baud to `PICO_USB_RESET_MAGIC_BAUD_RATE` (default 1200) calls `rom_reset_usb_boot_extra()`. The current CMake explicitly sets `PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0` and `PICO_STDIO_USB_ENABLE_RESET_VIA_VENDOR_INTERFACE=0`. Thus the current firmware has no software BOOTSEL/recovery reset path, even though the existing SDK can provide one without a separate Debug Probe. Vendor-interface reset would alter the composite descriptor; baud reset is the lower-impact candidate for a debug build, pending descriptor/callback compatibility review.
