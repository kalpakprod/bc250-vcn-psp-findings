#ifndef ADAPTER_TOCTOU_STAGE_H
#define ADAPTER_TOCTOU_STAGE_H
#include <stdbool.h>
#include <stdint.h>
#define TOCTOU_STAGE_CAPACITY 4096u
/* RAM staging only. Digest proves transfer integrity, not PSP signatures or
 * membership in an approved image. Full image provenance is checked on host. */
typedef struct {
    uint8_t *data; /* caller leases TOCTOU_STAGE_CAPACITY bytes until clear */
    uint8_t digest[32];
    uint32_t address, length, received;
    bool active, verified;
} adapter_toctou_stage_t;
void adapter_toctou_stage_clear(adapter_toctou_stage_t *s);
bool adapter_toctou_stage_begin(adapter_toctou_stage_t *s, uint32_t address,
                                 uint32_t length, const char *digest, uint8_t *buffer);
bool adapter_toctou_stage_load(adapter_toctou_stage_t *s, uint32_t offset,
                                const char *hex);
bool adapter_toctou_stage_commit(adapter_toctou_stage_t *s,
                                  const uint8_t actual_digest[32]);
#endif
