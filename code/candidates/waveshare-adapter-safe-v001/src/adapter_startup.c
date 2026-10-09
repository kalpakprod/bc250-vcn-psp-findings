#include "adapter_startup.h"

#include "pico/time.h"

static volatile adapter_startup_stage_t current = ADAPTER_STARTUP_USB_READY;
static volatile int failure;
static uint32_t started;

void adapter_startup_set(adapter_startup_stage_t stage, int error_code) {
  if (!started)
    started = to_ms_since_boot(get_absolute_time());
  current = stage;
  failure = error_code;
}

adapter_startup_stage_t adapter_startup_stage(void) { return current; }
int adapter_startup_error(void) { return failure; }

const char *adapter_startup_stage_name(void) {
  switch (current) {
  case ADAPTER_STARTUP_USB_READY:
    return "usb_ready";
  case ADAPTER_STARTUP_CYW43_INIT:
    return "cyw43_init";
  case ADAPTER_STARTUP_BRIDGE_BOOT:
    return "bridge_boot";
  case ADAPTER_STARTUP_NETWORK_INIT:
    return "network_init";
  case ADAPTER_STARTUP_READY:
    return "ready";
  case ADAPTER_STARTUP_FAILED:
    return "failed";
  default:
    return "unknown";
  }
}

uint32_t adapter_startup_uptime_ms(void) {
  if (!started)
    return 0;
  return to_ms_since_boot(get_absolute_time()) - started;
}
