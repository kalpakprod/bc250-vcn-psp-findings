#ifndef BRIDGE_H
#define BRIDGE_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Bridge module: DS5Dongle + HA webhook path.
// Assumes unified main.c has already called board_init(), tusb_init(),
// and cyw43_arch_init() before invoking the boot functions.
void bridge_boot_begin(void);
// Perform one bounded initialization step. Returns true when complete.
bool bridge_boot_step(void);
void bridge_init(void);

// Main-loop body for MODE_CONTROLLER. Call every iteration.
// unified main.c is responsible for cyw43_arch_poll() and tud_task().
void bridge_tick(void);

// Called before switching to another mode (typically followed by
// watchdog_reboot). Best-effort cleanup only.
void bridge_shutdown(void);

// Read-only status; unavailable subsystems are explicit, never fabricated.
void bridge_status_json(char *buffer, unsigned capacity);

#ifdef __cplusplus
}
#endif

#endif // BRIDGE_H
