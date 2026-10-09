#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void adapter_network_init(void);
void adapter_network_tick(void);
bool adapter_network_stage(const uint8_t *frame, unsigned length);
bool adapter_network_commit(void);
void adapter_network_discard(void);
const char *adapter_network_state(void);
bool adapter_mqtt_connected(void);
unsigned adapter_network_frame_size(void);
#ifdef __cplusplus
}
#endif
