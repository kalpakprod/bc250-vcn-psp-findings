#include "mode.h"

// RAM-only selection. Never read legacy mode storage or share config flash.
static pico_bc250_mode_t current = MODE_CONTROLLER;
static uint32_t generation;
pico_bc250_mode_t mode_load(void) { return current; }
bool mode_controller_active(void) { return current == MODE_CONTROLLER; }
uint32_t mode_generation(void) { return generation; }
bool mode_select(pico_bc250_mode_t m) {
    if (m != MODE_CONTROLLER && m != MODE_DIAGNOSTIC &&
        m != MODE_MONITOR && m != MODE_TOCTOU && m != MODE_FLASH &&
        m != MODE_RECOVERY) return false;
    if (m != current) { current = m; ++generation; }
    return true;
}
const char *mode_name(pico_bc250_mode_t m) {
    switch (m) {
    case MODE_CONTROLLER: return "controller";
    case MODE_TOCTOU: return "toctou";
    case MODE_MONITOR: return "monitor";
    case MODE_DIAGNOSTIC: return "diagnostic";
    case MODE_FLASH: return "flash";
    case MODE_RECOVERY: return "recovery";
    default: return "unsupported";
    }
}
