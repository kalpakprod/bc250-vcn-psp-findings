#include "rig_payload.h"
#include <string.h>

static rig_payload_t payload;

void rig_payload_clear(void) {
    memset(&payload, 0, sizeof(payload));
}

bool rig_payload_prepare(const adapter_toctou_stage_t *s, uint32_t read_index) {
    rig_payload_clear();
    if (!s || !s->active || !s->verified || !s->data ||
        ((uintptr_t)s->data & 3u) || !s->length ||
        s->length > TOCTOU_STAGE_CAPACITY || s->received != s->length ||
        s->address >= 0x1000000u || s->length > 0x1000000u - s->address) return false;
    /* DMA reads whole words; pad outside the hashed bytes within the lease. */
    unsigned pad = (4u - (s->length & 3u)) & 3u;
    memset(s->data + s->length, 0, pad);
    payload.data = s->data;
    payload.length = s->length;
    payload.mark = 0x03000000u | s->address;
    payload.interval_m1 = s->length * 8u - 1u;
    payload.read_index = read_index;
    return true;
}

const rig_payload_t *rig_payload_current(void) {
    return payload.data ? &payload : NULL;
}
