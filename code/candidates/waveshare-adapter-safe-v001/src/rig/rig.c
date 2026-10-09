// rig.c — Implementation of the TOCTOU rig control API. See rig.h.
//
// One PIO state machine does the whole job: sniff header, compare to
// mark, silence BC-250 flash via /HOLD, drive substitute bytes onto
// the shared DO wire. The payload comes from Waveshare RAM via TX FIFO.

#include "rig.h"
#include "rig_payload.h"
#include "rig_abort.h"

#include "spi_toctou.pio.h"

#include <pico/stdlib.h>
#include <hardware/clocks.h>
#include <hardware/dma.h>
#include <hardware/irq.h>
#include <hardware/pio.h>
#include <hardware/structs/qmi.h>
#include <hardware/sync.h>
#include <hardware/vreg.h>

#include <stdio.h>
#include <string.h>

#define TOCTOU_PIO   pio0
#define TOCTOU_SM    0

// Payload is borrowed from the verified stage scratch lease. No duplicate RAM.
// No mechanism to enable this gate exists until bus/timing/read-order acceptance.
static const bool hardware_accepted = false;

static uint g_program_offset = (uint)-1;
static int  g_dma_channel = -1;

static volatile rig_state_t g_state;

// -----------------------------------------------------------------------
// PIO IRQ handler — fires once per rig hit. Kept minimal.
// -----------------------------------------------------------------------
static void __not_in_flash_func(rig_pio_irq_handler)(void) {
    if (pio_interrupt_get(TOCTOU_PIO, 0)) {
        pio_interrupt_clear(TOCTOU_PIO, 0);
        g_state.hits += 1;
    }
}

// -----------------------------------------------------------------------
// Overclock — VREG first, then flash divider, then PLL. Same recipe as
// bc250 toctou-rig-v001 (documented BUILD.md there). At 400 MHz the PIO
// gets 8 sys cycles per SPI bit at 50 MHz SPI, comfortably enough for
// the wait-out-wait-jmp override loop.
// -----------------------------------------------------------------------
static void rig_overclock_400mhz(void) {
    vreg_set_voltage(VREG_VOLTAGE_1_30);
    sleep_ms(10);

    qmi_hw->m[0].timing = (qmi_hw->m[0].timing & ~QMI_M0_TIMING_CLKDIV_BITS)
                          | (4u << QMI_M0_TIMING_CLKDIV_LSB);

    set_sys_clock_khz(400000, true);
}

// -----------------------------------------------------------------------
// PIO / DMA configuration
// -----------------------------------------------------------------------
static void configure_pio(void) {
    pio_sm_config c = spi_toctou_program_get_default_config(g_program_offset);

    // In pins: MOSI at base, CS at base+1, CLK at base+2. The C driver
    // has already asserted `RIG_PIN_MOSI + 1 == RIG_PIN_CS` and
    // `RIG_PIN_MOSI + 2 == RIG_PIN_CLK` — see the compile-time checks
    // in rig_init().
    sm_config_set_in_pins(&c, RIG_PIN_MOSI);
    sm_config_set_jmp_pin(&c, RIG_PIN_CS);

    // Set-pin for pindir toggling of DO.
    sm_config_set_set_pins(&c, RIG_PIN_DO_OVERRIDE, 1);
    // Out-pin for driving payload bits onto DO.
    sm_config_set_out_pins(&c, RIG_PIN_DO_OVERRIDE, 1);
    // Side-set drives /HOLD_BC250.
    sm_config_set_sideset_pins(&c, RIG_PIN_HOLD_BC250);
    sm_config_set_sideset(&c, 1, /*optional=*/false, /*pindirs=*/false);

    // Autopull enables 32-bit refill of OSR from TX FIFO during override.
    sm_config_set_out_shift(&c,
                            /*shift_right=*/false,   // MSB-first over the wire
                            /*autopull=*/true,
                            /*pull_threshold=*/32);
    // In-shift left too (matches SPI wire order).
    sm_config_set_in_shift(&c,
                           /*shift_right=*/false,
                           /*autopush=*/false,
                           /*push_threshold=*/32);

    sm_config_set_clkdiv_int_frac(&c, 1, 0);

    // GPIO ownership hand-off to PIO and starting directions.
    // Inputs — the PSP-driven bus (via clip).
    for (uint pin = RIG_PIN_MOSI; pin <= RIG_PIN_CLK; ++pin) {
        pio_gpio_init(TOCTOU_PIO, pin);
        pio_sm_set_consecutive_pindirs(TOCTOU_PIO, TOCTOU_SM, pin, 1, /*is_out=*/false);
    }
    // Outputs — /HOLD_BC250 (always driven) and DO override (pindir toggled
    // by PIO). Start both at safe idle: /HOLD high, DO input.
    pio_gpio_init(TOCTOU_PIO, RIG_PIN_HOLD_BC250);
    pio_gpio_init(TOCTOU_PIO, RIG_PIN_DO_OVERRIDE);
    pio_sm_set_pins_with_mask(TOCTOU_PIO, TOCTOU_SM,
                              (1u << RIG_PIN_HOLD_BC250),
                              (1u << RIG_PIN_HOLD_BC250) | (1u << RIG_PIN_DO_OVERRIDE));
    pio_sm_set_pindirs_with_mask(TOCTOU_PIO, TOCTOU_SM,
                                 (1u << RIG_PIN_HOLD_BC250),
                                 (1u << RIG_PIN_HOLD_BC250) | (1u << RIG_PIN_DO_OVERRIDE));

    pio_sm_init(TOCTOU_PIO, TOCTOU_SM, g_program_offset, &c);
}

// DMA feeds payload from RAM into the PIO TX FIFO on demand (paced by TX-DREQ).
// The channel is re-armed on each arm() call because the payload buffer and
// length may change.
static void arm_payload_dma(const uint8_t *buf, uint32_t byte_len) {
    // Round up to whole 32-bit words so autopull is happy.
    uint32_t words = (byte_len + 3u) / 4u;
    if (words == 0) return;

    if (g_dma_channel < 0) {
        g_dma_channel = dma_claim_unused_channel(true);
    } else {
        dma_channel_abort(g_dma_channel);
    }

    dma_channel_config c = dma_channel_get_default_config(g_dma_channel);
    channel_config_set_transfer_data_size(&c, DMA_SIZE_32);
    // RAM bytes are little-endian words; the PIO shifts bit 31 first.
    channel_config_set_bswap(&c, true);
    channel_config_set_read_increment(&c, true);
    channel_config_set_write_increment(&c, false);
    channel_config_set_dreq(&c, pio_get_dreq(TOCTOU_PIO, TOCTOU_SM, /*is_tx=*/true));

    dma_channel_configure(g_dma_channel, &c,
                          &TOCTOU_PIO->txf[TOCTOU_SM],  // dest
                          buf,                           // src
                          words,                         // count
                          /*trigger=*/true);
}

// -----------------------------------------------------------------------
// Public API
// -----------------------------------------------------------------------
int rig_init(void) {
    if (!hardware_accepted) return -3; // no clocks, pins or PIO touched
    // Compile-time-ish sanity: PIO expects these to be consecutive.
    if (RIG_PIN_MOSI + 1 != RIG_PIN_CS)   { printf("[rig] MOSI+1 != CS\n"); return -1; }
    if (RIG_PIN_MOSI + 2 != RIG_PIN_CLK)  { printf("[rig] MOSI+2 != CLK\n"); return -1; }

    if (!rig_abort_init()) return -4; // fail closed if no independent timer
    rig_overclock_400mhz();

    // Set the LED as generic GPIO — used for status feedback.
    gpio_init(RIG_PIN_LED);
    gpio_set_dir(RIG_PIN_LED, GPIO_OUT);
    gpio_put(RIG_PIN_LED, 0);

    if (!pio_can_add_program(TOCTOU_PIO, &spi_toctou_program)) {
        printf("[rig] spi_toctou_program does not fit\n");
        rig_abort_shutdown();
        return -2;
    }
    g_program_offset = pio_add_program(TOCTOU_PIO, &spi_toctou_program);
    configure_pio();

    // Hook the PIO's IRQ 0 line to a CPU IRQ so we can count hits without
    // stalling the state machine.
    pio_set_irq0_source_enabled(TOCTOU_PIO, pis_interrupt0, true);
    irq_set_exclusive_handler(PIO0_IRQ_0, rig_pio_irq_handler);
    irq_set_enabled(PIO0_IRQ_0, true);

    // Initialization alone must not run a responder without its abort guard.
    pio_sm_set_enabled(TOCTOU_PIO, TOCTOU_SM, false);
    rig_abort_stop();

    g_state.armed = false;
    g_state.mark = 0xFFFFFFFFu;
    g_state.interval_m1 = 0;
    g_state.hits = 0;

    return 0;
}

// Experimental backend only; binding alone does not authorize activation.
bool rig_arm(uint32_t mark, uint32_t interval_m1, uint32_t timeout_us) {
    const rig_payload_t *payload = rig_payload_current();
    if (!hardware_accepted || g_program_offset == (uint)-1 || !payload ||
        payload->mark != mark || payload->interval_m1 != interval_m1 ||
        payload->read_index != 0 || !timeout_us || timeout_us > 1000000u || g_state.armed) return false;
    uint32_t irq_save = save_and_disable_interrupts();
    pio_sm_set_enabled(TOCTOU_PIO, TOCTOU_SM, false);
    pio_sm_clear_fifos(TOCTOU_PIO, TOCTOU_SM);
    pio_sm_restart(TOCTOU_PIO, TOCTOU_SM);
    configure_pio(); // restore idle directions before removing abort pad overrides
    pio_sm_exec(TOCTOU_PIO, TOCTOU_SM, pio_encode_jmp(g_program_offset));

    // Setup words: MARK, COUNT_M1.
    pio_sm_put_blocking(TOCTOU_PIO, TOCTOU_SM, mark);
    pio_sm_put_blocking(TOCTOU_PIO, TOCTOU_SM, interval_m1);

    // The scratch lease must remain held throughout this DMA transfer.
    arm_payload_dma(payload->data, payload->length);

    if (!rig_abort_start(timeout_us)) {
        rig_disarm();
        restore_interrupts(irq_save);
        return false;
    }
    g_state.armed = true;
    pio_sm_set_enabled(TOCTOU_PIO, TOCTOU_SM, true);

    g_state.mark = mark;
    g_state.interval_m1 = interval_m1;

    gpio_put(RIG_PIN_LED, 1);
    restore_interrupts(irq_save);
    return true;
}

void __not_in_flash_func(rig_disarm)(void) {
    if (g_program_offset == (uint)-1) return;
    uint32_t irq_save = save_and_disable_interrupts();
    rig_abort_stop(); // pad-level release cannot wait for SPI clocks or DMA
    pio_sm_set_enabled(TOCTOU_PIO, TOCTOU_SM, false);
    if (g_dma_channel >= 0) dma_channel_abort(g_dma_channel);
    pio_sm_clear_fifos(TOCTOU_PIO, TOCTOU_SM);
    g_state.armed = false;
    gpio_put(RIG_PIN_LED, 0);
    restore_interrupts(irq_save);
}

rig_state_t rig_get_state(void) {
    // Copy under IRQ disable so a hit mid-read doesn't tear the struct.
    uint32_t save = save_and_disable_interrupts();
    rig_state_t snap = *(rig_state_t *)&g_state;
    restore_interrupts(save);
    return snap;
}

void rig_get_payload_snapshot(uint32_t offset, uint32_t len, uint8_t *out) {
    const rig_payload_t *payload = rig_payload_current();
    if (!payload || offset >= payload->length) return;
    if (len > payload->length - offset) len = payload->length - offset;
    memcpy(out, payload->data + offset, len);
}

// Append a line to the report buffer, tracking remaining capacity.
static void report_line(char **cur, uint32_t *left, const char *line) {
    int n = snprintf(*cur, *left, "%s\n", line);
    if (n > 0 && (uint32_t)n < *left) { *cur += n; *left -= (uint32_t)n; }
}

int rig_selftest(char *report, uint32_t cap) {
    char *cur = report;
    uint32_t left = cap;
    int failures = 0;

    // PIO: rig_init must have loaded the program at a real offset.
    if (g_program_offset != (uint)-1) {
        report_line(&cur, &left, "PIO_OK");
    } else {
        report_line(&cur, &left, "PIO_FAIL program-not-loaded");
        failures++;
    }

    // GPIO: each rig pin must currently be owned by PIO (input trio) or
    // configured as our output pair. We check the function is not the
    // default SIO-with-no-init by reading back the direction mask.
    bool gpio_ok = true;
    for (uint pin = RIG_PIN_MOSI; pin <= RIG_PIN_CLK; ++pin) {
        if (gpio_get_function(pin) != GPIO_FUNC_PIO0) gpio_ok = false;
    }
    if (gpio_get_function(RIG_PIN_HOLD_BC250) != GPIO_FUNC_PIO0) gpio_ok = false;
    if (gpio_get_function(RIG_PIN_DO_OVERRIDE) != GPIO_FUNC_PIO0) gpio_ok = false;
    if (gpio_ok) {
        report_line(&cur, &left, "GPIO_OK");
    } else {
        report_line(&cur, &left, "GPIO_FAIL pin-function");
        failures++;
    }

    // DMA: claim a throwaway channel to prove one is free, then release.
    int ch = dma_claim_unused_channel(false);
    if (ch >= 0) {
        dma_channel_unclaim(ch);
        report_line(&cur, &left, "DMA_OK");
    } else {
        report_line(&cur, &left, "DMA_FAIL no-free-channel");
        failures++;
    }

    return failures;
}

void rig_tick(void) {
    // Rig is IRQ+DMA driven; nothing to poll in the main loop.
}

void rig_shutdown(void) {
    if (g_program_offset == (uint)-1) return;
    // Disarm before dropping the borrowed payload descriptor.
    rig_disarm();
    rig_abort_shutdown();
    rig_payload_clear();

    // Disable the PIO state machine and detach its IRQ.
    if (g_program_offset != (uint)-1) {
        pio_sm_set_enabled(TOCTOU_PIO, TOCTOU_SM, false);
        irq_set_enabled(PIO0_IRQ_0, false);
        pio_set_irq0_source_enabled(TOCTOU_PIO, pis_interrupt0, false);
    }

    // Release the DMA channel we claimed on the first arm.
    if (g_dma_channel >= 0) {
        dma_channel_abort(g_dma_channel);
        dma_channel_unclaim(g_dma_channel);
        g_dma_channel = -1;
    }

    pio_remove_program(TOCTOU_PIO, &spi_toctou_program, g_program_offset);
    g_program_offset = (uint)-1;

    // Return the rig pins to safe idle. DO override → HiZ input so we
    // never drive BC-250's DO line. /HOLD → HiZ input, BC-250's board
    // pull-up holds it high (per docs/rig-wiring.md). Bus-sniff inputs
    // become plain SIO inputs.
    for (uint pin = RIG_PIN_MOSI; pin <= RIG_PIN_CLK; ++pin) {
        gpio_set_function(pin, GPIO_FUNC_SIO);
        gpio_set_dir(pin, GPIO_IN);
    }
    gpio_set_function(RIG_PIN_DO_OVERRIDE, GPIO_FUNC_SIO);
    gpio_set_dir(RIG_PIN_DO_OVERRIDE, GPIO_IN);
    gpio_set_function(RIG_PIN_HOLD_BC250, GPIO_FUNC_SIO);
    gpio_set_dir(RIG_PIN_HOLD_BC250, GPIO_IN);
    gpio_pull_up(RIG_PIN_HOLD_BC250);
    // Restore mux overrides only AFTER both pads have become SIO inputs.
    gpio_set_outover(RIG_PIN_HOLD_BC250, GPIO_OVERRIDE_NORMAL);
    gpio_set_oeover(RIG_PIN_DO_OVERRIDE, GPIO_OVERRIDE_NORMAL);
    gpio_put(RIG_PIN_LED, 0);
}
