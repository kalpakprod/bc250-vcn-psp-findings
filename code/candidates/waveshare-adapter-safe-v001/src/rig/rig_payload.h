#ifndef RIG_PAYLOAD_H
#define RIG_PAYLOAD_H
#include "../adapter_toctou_stage.h"

/* RAM-only binding. read_index is retained, not implemented by the PIO.
 * The stage scratch lease must remain owned until rig_payload_clear(). */
typedef struct {
    const uint8_t *data;
    uint32_t length, mark, interval_m1, read_index;
} rig_payload_t;
bool rig_payload_prepare(const adapter_toctou_stage_t *stage, uint32_t read_index);
const rig_payload_t *rig_payload_current(void);
void rig_payload_clear(void);
#endif
