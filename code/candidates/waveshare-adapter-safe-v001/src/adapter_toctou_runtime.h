#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "hardware/pio.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Fixed interposer wiring.  Do not silently substitute board GPIOs. */
#define ADAPTER_TOCTOU_MOSI_GPIO 10u
#define ADAPTER_TOCTOU_CLK_GPIO 12u
#define ADAPTER_TOCTOU_UPSTREAM_CS_GPIO 13u
#define ADAPTER_TOCTOU_DOWNSTREAM_CS_GPIO 17u
#define ADAPTER_TOCTOU_MISO_GPIO 18u

typedef struct {
    uint32_t trigger_word;
    uint32_t window_words;
} adapter_toctou_runtime_config_t;

typedef struct {
    PIO pio;
    int sm_sniffer, sm_repeater, sm_switcher;
    int dma_channel;
    int off_sniffer, off_repeater, off_switcher;
    adapter_toctou_runtime_config_t config;
    uint32_t observed_words;
    bool initialized, armed;
} adapter_toctou_runtime_t;

bool adapter_toctou_runtime_init(adapter_toctou_runtime_t *rt, PIO pio);
bool adapter_toctou_runtime_configure_arm(adapter_toctou_runtime_t *rt,
                                           const adapter_toctou_runtime_config_t *cfg);
void adapter_toctou_runtime_disarm(adapter_toctou_runtime_t *rt);
void adapter_toctou_runtime_tick(adapter_toctou_runtime_t *rt);
bool adapter_toctou_runtime_is_armed(const adapter_toctou_runtime_t *rt);

#ifdef __cplusplus
}
#endif
