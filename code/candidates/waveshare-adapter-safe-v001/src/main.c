#include "adapter_flash_service.h"
#include "adapter_flash_transport.h"
#include "adapter_network.h"
#include "adapter_spi_capture.h"
#include "adapter_startup.h"
#include "adapter_watchdog.h"
#include "adapter_uart.h"
#include "bridge/bridge.h"
#include "bsp/board_api.h"
#include "cdc_dispatch.h"
#include "pico/cyw43_arch.h"
#include "pico/stdlib.h"
#include "tusb.h"

int main(void) {
  adapter_recorder_t *recorder = adapter_recorder_instance();
  adapter_watchdog_t watchdog;
  adapter_recorder_init(recorder, to_us_since_boot(get_absolute_time()) / 1000);
  adapter_recorder_heartbeat_config(recorder, ADAPTER_RECORDER_HOST_HEARTBEAT, 5000);
  adapter_recorder_record_unknown(recorder, ADAPTER_EVENT_ADAPTER_REBOOT,
                                  to_us_since_boot(get_absolute_time()) / 1000, 0);
  board_init();
  stdio_init_all();
  // Keep USB/CDC alive even when Wi-Fi initialization fails. A transient
  // CYW43 fault must not make the board disappear from the recovery channel.
  tusb_init();
  board_init_after_tusb();
  adapter_startup_set(ADAPTER_STARTUP_USB_READY, 0);
#ifdef USB_ONLY_DIAGNOSTIC
  // Keep the USB path alive without entering CYW43/BT/audio initialization.
  // This separates board/descriptor enumeration from later subsystem faults.
  while (1) {
    tud_task();
    cdc_dispatch_tick();
    sleep_ms(1);
  }
#endif
  // Give the host a bounded USB-only window. Early VERSION/STATUS remain
  // useful even when a later wireless or BT stage fails.
  const uint32_t usb_window = to_ms_since_boot(get_absolute_time()) + 1500;
  while ((int32_t)(to_ms_since_boot(get_absolute_time()) - usb_window) < 0) {
    tud_task();
    cdc_dispatch_tick();
    sleep_ms(1);
  }
  adapter_startup_set(ADAPTER_STARTUP_CYW43_INIT, 0);
  const int wifi_status = cyw43_arch_init();
  if (wifi_status != 0) {
    adapter_startup_set(ADAPTER_STARTUP_FAILED, wifi_status);
  } else {
    adapter_startup_set(ADAPTER_STARTUP_BRIDGE_BOOT, 0);
    bridge_boot_begin();
    while (!bridge_boot_step()) {
      tud_task();
      cdc_dispatch_tick();
      sleep_ms(1);
    }
    adapter_startup_set(ADAPTER_STARTUP_NETWORK_INIT, 0);
    adapter_network_init();
    adapter_startup_set(ADAPTER_STARTUP_READY, 0);
  }
  /* Observe completed service passes, not the external Linux heartbeat.
   * Wireless initialization failure is a degraded USB mode, not a reset loop.
   * Enable only after startup until SDK startup timing is hardware-accepted. */
  uint32_t required = ADAPTER_HEARTBEAT_USB | ADAPTER_HEARTBEAT_RECORDER;
  if (wifi_status == 0)
    required |= ADAPTER_HEARTBEAT_WIFI | ADAPTER_HEARTBEAT_CONTROLLER;
  adapter_watchdog_init(&watchdog, recorder, required, 5000,
                       to_us_since_boot(get_absolute_time()) / 1000);
  while (1) {
    tud_task();
    cdc_dispatch_tick();
    adapter_watchdog_mark(&watchdog, ADAPTER_HEARTBEAT_USB,
                          to_us_since_boot(get_absolute_time()) / 1000);
    if (wifi_status == 0) {
      cyw43_arch_poll();
      bridge_tick();
      adapter_watchdog_mark(&watchdog, ADAPTER_HEARTBEAT_CONTROLLER,
                            to_us_since_boot(get_absolute_time()) / 1000);
      adapter_network_tick();
      adapter_watchdog_mark(&watchdog, ADAPTER_HEARTBEAT_WIFI,
                            to_us_since_boot(get_absolute_time()) / 1000);
    }
    adapter_uart_tick();
    adapter_spi_capture_tick();
    adapter_flash_transport_tick();
    adapter_flash_service_tick();
    if (adapter_flash_transport_ready() && !tud_cdc_ready())
      adapter_flash_transport_abort(NULL);
    const uint64_t now = to_us_since_boot(get_absolute_time()) / 1000;
    adapter_recorder_heartbeat_poll(recorder, now);
    adapter_watchdog_mark(&watchdog, ADAPTER_HEARTBEAT_RECORDER, now);
    adapter_watchdog_tick(&watchdog, now);
  }
}
