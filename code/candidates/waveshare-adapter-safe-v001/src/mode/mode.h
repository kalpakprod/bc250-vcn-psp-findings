#ifndef PICO_BC250_MODE_H
#define PICO_BC250_MODE_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    MODE_CONTROLLER  = 0,
    MODE_TOCTOU      = 1,
    MODE_OVERCLOCK   = 2,  // reserved for Phase 3
    MODE_MONITOR     = 3,  // reserved for Phase 4
    MODE_VCN_UNBLOCK = 4,  // reserved for Phase 2
    MODE_DIAGNOSTIC  = 5,  // passive local diagnostics; never persisted
    MODE_FLASH       = 6,  // guarded external SPI flash service; never persisted
    MODE_RECOVERY    = 7,  // recovery/re-enumeration; never persisted
} pico_bc250_mode_t;

pico_bc250_mode_t mode_load(void);
bool mode_select(pico_bc250_mode_t m);
bool mode_controller_active(void);
uint32_t mode_generation(void);
void              mode_save(pico_bc250_mode_t m);
void              mode_switch_and_reboot(pico_bc250_mode_t m);
bool              mode_check_boot_long_press(void);
const char       *mode_name(pico_bc250_mode_t m);

#ifdef __cplusplus
}
#endif

#endif
