#pragma once
#include "adapter_flash_protocol.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Transport must return promptly: 0 pending, 1 complete, -1 failed.
 * It must consume tx within the call or copy it, and return exactly rxlen bytes.
 * abort must deassert CS and stop transfer. No shared bus proof inferred here. */
typedef int (*flash_exchange)(const uint8_t *tx,unsigned txlen,uint8_t *rx,unsigned rxlen,void *context);
typedef void (*flash_abort)(void *context);
typedef enum {FLASH_ENGINE_IDLE,FLASH_ENGINE_RUNNING,FLASH_ENGINE_DONE,FLASH_ENGINE_FAILED} flash_engine_state;
bool adapter_flash_engine_start(const flash_target *target,flash_operation operation,uint32_t address,
                                const uint8_t *payload,unsigned length,uint32_t now,
                                flash_exchange exchange,flash_abort abort,void *context);
void adapter_flash_engine_tick(uint32_t now,bool ownership_valid);
void adapter_flash_engine_stop(void);
flash_engine_state adapter_flash_engine_state(void);
const char *adapter_flash_engine_result(void);
unsigned adapter_flash_engine_read(uint8_t *out,unsigned capacity);
#ifdef __cplusplus
}
#endif
