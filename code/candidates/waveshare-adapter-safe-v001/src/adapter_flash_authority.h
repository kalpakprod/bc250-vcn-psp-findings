#pragma once
#include "adapter_flash_protocol.h"
#ifdef __cplusplus
extern "C" {
#endif
void adapter_flash_authority_clear(void);
bool adapter_flash_authority_identify(uint64_t target_tag,uint32_t observed_jedec,uint32_t generation);
bool adapter_flash_authority_approve(uint64_t target_tag,uint32_t generation,const uint8_t image_digest[32],
 const uint8_t approved_digest[32],const uint8_t backup1_digest[32],const uint8_t backup2_digest[32],bool recovery_confirmed);
bool adapter_flash_authority_sector(uint64_t target_tag,uint32_t generation,const uint8_t image_digest[32],
 uint32_t address,const uint8_t sector[4096]);
bool adapter_flash_authority_allows(uint64_t target_tag,uint32_t generation,const uint8_t image_digest[32],
 flash_operation operation,uint32_t address,const uint8_t *payload,unsigned length,flash_target *out);
/* This layer checks binding/bytes. It is not a signature/PSP verifier, hardware
 * isolation sensor, or cryptographic authorizer. Trusted host preflight and
 * actual image-specific owner approval must precede approve()/sector(). */
#ifdef __cplusplus
}
#endif
