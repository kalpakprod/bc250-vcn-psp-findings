// rig.h — TOCTOU rig control API for the Waveshare RP2350B-Plus-W.
//
// Model: the Waveshare watches the BC-250 SPI flash bus via a SOIC-8
// clip. On a header match, it silences the BC-250 flash (drives /HOLD
// low) and drives substitute bytes onto the shared DO wire for a
// preset window of SPI clocks. See docs/rig-wiring.md and
// docs/rig-topology.md.
//
// Scope. This module is a delivery mechanism: it puts arbitrary bytes
// onto DO at a chosen address window. Generating a modified BIOS image
// whose modules pass PSP signature checks — i.e. the key material and
// module signing — is out of scope and stays with the human researcher.

#pragma once

#include <stdbool.h>
#include <stdint.h>

// Pin assignments. PIO needs MOSI, CS, CLK on consecutive GPIOs
// (MOSI = base, CS = base+1, CLK = base+2). Any change breaks the .pio
// program; keep both in sync.
#define RIG_PIN_MOSI         10  // input  — MOSI from PSP via clip
#define RIG_PIN_CS           11  // input  — CS# from PSP via clip
#define RIG_PIN_CLK          12  // input  — CLK from PSP via clip
#define RIG_PIN_DO_OVERRIDE  16  // output — our data onto the shared DO
                                 //          wire (tristate when idle)
#define RIG_PIN_HOLD_BC250   20  // output — /HOLD to BC-250 flash via
                                 //          clip (LOW silences its DO)
#define RIG_PIN_LED          23  // output — Waveshare user LED (status)

// Runtime state, mirrored for USB console reporting.
typedef struct rig_state {
    bool     armed;
    uint32_t mark;         // 32-bit SPI header (cmd<<24 | addr[23:0]) to match
    uint32_t interval_m1;  // SPI clocks minus 1 during which override is held
    uint32_t hits;         // count of matches observed since last reset
} rig_state_t;

// Experimental initialise: currently returns -3 without hardware changes.
// The dormant backend configures PIO/GPIO/DMA and overclocks to 400 MHz;
// physical acceptance and system integration are required before enabling it.
// Requires `stdio_init_all()` earlier if you want the debug prints.
// Returns 0 on success, non-zero on failure (message printed to stdio).
int rig_init(void);

// Verified staged payloads are bound through rig_payload.h, using the
// existing scratch lease rather than a second 4KiB buffer.

// Arm the rig: on any transaction whose 32-bit header equals `mark`,
// override DO for `interval_m1 + 1` SPI clocks. Mark is
// (0x03 << 24) | addr24 for a single-line READ at addr24. Safe to
// Runtime activation is blocked pending physical acceptance and PIO read-index
// selection. Returns false without GPIO/PIO/DMA changes in the current build.
// timeout_us is an explicit total arming budget (1..1000000 us), not inferred
// from unknown SPI speed. CS rising ends the attempt, including nonmatching reads.
bool rig_arm(uint32_t mark, uint32_t interval_m1, uint32_t timeout_us);

// Disarm. Payload buffer retained, DMA aborted, both output pins go
// back to their safe idles (/HOLD high, DO input).
void rig_disarm(void);

// Snapshot of current state for the USB console.
rig_state_t rig_get_state(void);

// Copy `len` bytes of the current payload buffer starting at `offset`
// into `out`. Clamps to the buffer capacity. Used by the DUMP command
// to verify a LOAD without re-reading the wire.
void rig_get_payload_snapshot(uint32_t offset, uint32_t len, uint8_t *out);

// Self-test: verify PIO program fits, GPIO functions are assignable, and
// a DMA channel can be claimed — all without a clip attached. Writes a
// human-readable multi-line report into `report` (up to `cap` bytes).
// Returns 0 if every subsystem passed, non-zero otherwise. Does not
// disturb the armed/disarmed state.
int rig_selftest(char *report, uint32_t cap);

// Cooperative tick from the unified main loop. Rig itself is IRQ+DMA
// driven, so this is a no-op stub for now — the LED heartbeat could
// live here in a later revision.
void rig_tick(void);

// Shut the rig down before switching to another mode: disable PIO SM,
// abort DMA, tri-state DO override (safe for BC-250 flash) and float
// /HOLD (pull-up on BC-250 board holds it high). Idempotent.
void rig_shutdown(void);
