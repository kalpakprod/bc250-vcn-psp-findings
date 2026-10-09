#include "adapter_toctou_runtime.h"
#include "adapter_toctou.pio.h"
#include "hardware/dma.h"
#include "hardware/gpio.h"
#include <string.h>

static void input_pin(uint pin) { gpio_init(pin); gpio_set_dir(pin, GPIO_IN); gpio_disable_pulls(pin); }

bool adapter_toctou_runtime_init(adapter_toctou_runtime_t *rt, PIO pio) {
    if (!rt || !pio) return false;
    memset(rt, 0, sizeof(*rt)); rt->pio = pio;
    rt->sm_sniffer = rt->sm_repeater = rt->sm_switcher = -1;
    rt->dma_channel = rt->off_sniffer = rt->off_repeater = rt->off_switcher = -1;
    input_pin(ADAPTER_TOCTOU_MOSI_GPIO); input_pin(ADAPTER_TOCTOU_CLK_GPIO);
    input_pin(ADAPTER_TOCTOU_UPSTREAM_CS_GPIO); input_pin(ADAPTER_TOCTOU_MISO_GPIO);
    /* Downstream CS is deliberately left untouched: no output drive before arm. */
    rt->initialized = true;
    return true;
}

static void release_claims(adapter_toctou_runtime_t *rt) {
    if (rt->dma_channel >= 0) { dma_channel_abort((uint)rt->dma_channel); dma_channel_unclaim((uint)rt->dma_channel); rt->dma_channel = -1; }
    if (rt->sm_sniffer >= 0) pio_sm_unclaim(rt->pio, (uint)rt->sm_sniffer);
    if (rt->sm_repeater >= 0) pio_sm_unclaim(rt->pio, (uint)rt->sm_repeater);
    if (rt->sm_switcher >= 0) pio_sm_unclaim(rt->pio, (uint)rt->sm_switcher);
    if (rt->off_sniffer >= 0) { pio_remove_program(rt->pio, &toctou_spi_sniffer_program, (uint)rt->off_sniffer); rt->off_sniffer=-1; }
    if (rt->off_repeater >= 0) { pio_remove_program(rt->pio, &toctou_cs_repeater_program, (uint)rt->off_repeater); rt->off_repeater=-1; }
    if (rt->off_switcher >= 0) { pio_remove_program(rt->pio, &toctou_cs_switcher_program, (uint)rt->off_switcher); rt->off_switcher=-1; }
    rt->sm_sniffer = rt->sm_repeater = rt->sm_switcher = -1;
}

bool adapter_toctou_runtime_configure_arm(adapter_toctou_runtime_t *rt, const adapter_toctou_runtime_config_t *cfg) {
    if (!rt || !rt->initialized || rt->armed || !cfg || !cfg->window_words) return false;
#ifndef ADAPTER_TOCTOU_WIRING_CONFIRMED
    (void)cfg; return false;
#else
    rt->config = *cfg;
    rt->sm_sniffer = (int)pio_claim_unused_sm(rt->pio, false); rt->sm_repeater = (int)pio_claim_unused_sm(rt->pio, false); rt->sm_switcher = (int)pio_claim_unused_sm(rt->pio, false);
    if (rt->sm_sniffer < 0 || rt->sm_repeater < 0 || rt->sm_switcher < 0) { release_claims(rt); return false; }
    rt->off_sniffer = (int)pio_add_program(rt->pio, &toctou_spi_sniffer_program); rt->off_repeater = (int)pio_add_program(rt->pio, &toctou_cs_repeater_program); rt->off_switcher = (int)pio_add_program(rt->pio, &toctou_cs_switcher_program);
    pio_gpio_init(rt->pio, ADAPTER_TOCTOU_DOWNSTREAM_CS_GPIO);
    gpio_set_dir(ADAPTER_TOCTOU_DOWNSTREAM_CS_GPIO, GPIO_IN);
    pio_sm_config s = toctou_spi_sniffer_program_get_default_config((uint)rt->off_sniffer);
    sm_config_set_in_pins(&s, ADAPTER_TOCTOU_MOSI_GPIO); sm_config_set_in_shift(&s, false, true, 32); pio_sm_init(rt->pio, (uint)rt->sm_sniffer, (uint)rt->off_sniffer, &s);
    pio_sm_config r = toctou_cs_repeater_program_get_default_config((uint)rt->off_repeater); sm_config_set_jmp_pin(&r, ADAPTER_TOCTOU_UPSTREAM_CS_GPIO); sm_config_set_sideset_pins(&r, ADAPTER_TOCTOU_DOWNSTREAM_CS_GPIO); pio_sm_init(rt->pio, (uint)rt->sm_repeater, (uint)rt->off_repeater, &r);
    pio_sm_config w = toctou_cs_switcher_program_get_default_config((uint)rt->off_switcher); sm_config_set_set_pins(&w, ADAPTER_TOCTOU_DOWNSTREAM_CS_GPIO, 1); pio_sm_init(rt->pio, (uint)rt->sm_switcher, (uint)rt->off_switcher, &w);
    rt->dma_channel = (int)dma_claim_unused_channel(false); if (rt->dma_channel < 0) { release_claims(rt); return false; }
    dma_channel_config dc = dma_channel_get_default_config((uint)rt->dma_channel); channel_config_set_transfer_data_size(&dc, DMA_SIZE_32); channel_config_set_dreq(&dc, pio_get_dreq(rt->pio, (uint)rt->sm_sniffer, false)); channel_config_set_read_increment(&dc, false); channel_config_set_write_increment(&dc, false);
    dma_channel_configure((uint)rt->dma_channel, &dc, &rt->pio->txf[rt->sm_switcher], &rt->pio->rxf[rt->sm_sniffer], cfg->window_words, false);
    pio_sm_set_enabled(rt->pio, (uint)rt->sm_sniffer, true); pio_sm_set_enabled(rt->pio, (uint)rt->sm_repeater, true); pio_sm_set_enabled(rt->pio, (uint)rt->sm_switcher, true); rt->armed = true; return true;
#endif
}

void adapter_toctou_runtime_disarm(adapter_toctou_runtime_t *rt) { if (!rt || !rt->initialized) return; if (rt->armed) { pio_sm_set_enabled(rt->pio, rt->sm_sniffer, false); pio_sm_set_enabled(rt->pio, rt->sm_repeater, false); pio_sm_set_enabled(rt->pio, rt->sm_switcher, false); } gpio_set_dir(ADAPTER_TOCTOU_DOWNSTREAM_CS_GPIO, GPIO_IN); release_claims(rt); rt->armed = false; }
void adapter_toctou_runtime_tick(adapter_toctou_runtime_t *rt) { if (rt && rt->armed) rt->observed_words++; }
bool adapter_toctou_runtime_is_armed(const adapter_toctou_runtime_t *rt) { return rt && rt->armed; }
