#ifndef ADAPTER_STARTUP_H
#define ADAPTER_STARTUP_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
  ADAPTER_STARTUP_USB_READY = 0,
  ADAPTER_STARTUP_CYW43_INIT,
  ADAPTER_STARTUP_BRIDGE_BOOT,
  ADAPTER_STARTUP_NETWORK_INIT,
  ADAPTER_STARTUP_READY,
  ADAPTER_STARTUP_FAILED,
} adapter_startup_stage_t;

void adapter_startup_set(adapter_startup_stage_t stage, int error_code);
adapter_startup_stage_t adapter_startup_stage(void);
int adapter_startup_error(void);
const char *adapter_startup_stage_name(void);
uint32_t adapter_startup_uptime_ms(void);

#ifdef __cplusplus
}
#endif

#endif
