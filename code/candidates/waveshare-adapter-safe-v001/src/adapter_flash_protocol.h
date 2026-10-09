#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef enum {FLASH_ID,FLASH_STATUS,FLASH_READ,FLASH_WRITE_ENABLE,FLASH_PROGRAM,FLASH_ERASE_SECTOR} flash_operation;
typedef struct {uint32_t size,jedec;bool exclusive_bus,write_approved;} flash_target;
/* Builds one conventional NOR frame; never sends it. Zero means rejected.
 * The backend must enforce physical bus ownership and consume image-specific
 * approval. Caller booleans are not evidence of either condition. */
unsigned adapter_flash_request(const flash_target *target,flash_operation op,uint32_t address,
                               const uint8_t *payload,unsigned length,uint8_t *out,unsigned capacity);
#ifdef __cplusplus
}
#endif
