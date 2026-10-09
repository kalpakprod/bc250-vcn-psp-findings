#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
bool adapter_flash_service_open(bool wiring,bool isolated);
bool adapter_flash_service_open_slot(unsigned slot,bool wiring,bool isolated);
bool adapter_flash_service_read(uint32_t address,unsigned length);
bool adapter_flash_service_approve(uint64_t expected_adapter,uint32_t expected_jedec,uint32_t expected_generation,
 const uint8_t image[32],const uint8_t approved[32],const uint8_t backup1[32],const uint8_t backup2[32],
 bool recovery_confirmed,bool protected_region_preflight);
bool adapter_flash_service_stage(uint32_t sector_address,const uint8_t image[32],const uint8_t sector[4096]);
bool adapter_flash_service_write(bool erase,uint32_t address,const uint8_t image[32],const uint8_t *payload,unsigned length);
bool adapter_flash_service_commit(bool erase,uint32_t address);
void adapter_flash_service_tick(void);
void adapter_flash_service_close(void);
void adapter_flash_service_status(char *out,unsigned capacity);
unsigned adapter_flash_service_data(uint8_t *out,unsigned capacity);
#ifdef __cplusplus
}
#endif
