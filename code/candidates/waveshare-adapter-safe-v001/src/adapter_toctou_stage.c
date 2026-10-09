#include "adapter_toctou_stage.h"
#include <string.h>

static int nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

void adapter_toctou_stage_clear(adapter_toctou_stage_t *s) {
    memset(s, 0, sizeof(*s));
}

bool adapter_toctou_stage_begin(adapter_toctou_stage_t *s, uint32_t address,
                                 uint32_t length, const char *digest, uint8_t *buffer) {
    adapter_toctou_stage_clear(s);
    if (!buffer || !length || length > TOCTOU_STAGE_CAPACITY || address >= 0x1000000u ||
        length > 0x1000000u - address || strlen(digest) != 64) return false;
    for (unsigned i = 0; i < 64; ++i) if (nibble(digest[i]) < 0) return false;
    for (unsigned i = 0; i < 32; ++i)
        s->digest[i] = (uint8_t)((nibble(digest[2*i]) << 4) | nibble(digest[2*i+1]));
    s->data = buffer;
    s->address = address;
    s->length = length;
    s->active = true;
    return true;
}

bool adapter_toctou_stage_load(adapter_toctou_stage_t *s, uint32_t offset,
                                const char *hex) {
    size_t n = strlen(hex);
    if (!s->active || s->verified || offset != s->received || !n || (n & 1u) ||
        n / 2 > s->length - s->received) return false;
    /* Validate the whole chunk before touching staged bytes. */
    for (size_t i = 0; i < n; ++i) if (nibble(hex[i]) < 0) return false;
    for (size_t i = 0; i < n / 2; ++i)
        s->data[offset+i] = (uint8_t)((nibble(hex[2*i]) << 4) | nibble(hex[2*i+1]));
    s->received += (uint32_t)(n / 2);
    return true;
}

bool adapter_toctou_stage_commit(adapter_toctou_stage_t *s,
                                  const uint8_t actual_digest[32]) {
    if (!s->active || s->received != s->length) return false;
    s->verified = memcmp(s->digest, actual_digest, 32) == 0;
    if (!s->verified) s->active = false; /* caller releases the lease */
    return s->verified;
}
