#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef enum { ADAPTER_TOCTOU_IDLE=0, ADAPTER_TOCTOU_ARMED, ADAPTER_TOCTOU_TRIGGERED, ADAPTER_TOCTOU_COMPLETE, ADAPTER_TOCTOU_ABORTED } adapter_toctou_state_t;
typedef enum { ADAPTER_TOCTOU_ORDER_MSB_FIRST=0, ADAPTER_TOCTOU_ORDER_LSB_FIRST=1 } adapter_toctou_order_t;
typedef struct { uint32_t trigger; uint32_t trigger_mask; uint32_t window_words; adapter_toctou_order_t order; } adapter_toctou_config_t;
typedef struct { adapter_toctou_config_t config; adapter_toctou_state_t state; uint32_t seen_words; uint32_t matched_word; } adapter_toctou_t;
void adapter_toctou_init(adapter_toctou_t *e);
bool adapter_toctou_configure(adapter_toctou_t *e, const adapter_toctou_config_t *cfg);
bool adapter_toctou_arm(adapter_toctou_t *e);
bool adapter_toctou_feed(adapter_toctou_t *e, uint32_t word);
void adapter_toctou_disarm(adapter_toctou_t *e);
bool adapter_toctou_rollback(adapter_toctou_t *e);
adapter_toctou_state_t adapter_toctou_state(const adapter_toctou_t *e);
size_t adapter_toctou_status_json(const adapter_toctou_t *e, char *out, size_t capacity);
#ifdef __cplusplus
}
#endif
