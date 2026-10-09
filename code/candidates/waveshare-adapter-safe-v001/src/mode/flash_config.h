#ifndef PICO_BC250_FLASH_CONFIG_H
#define PICO_BC250_FLASH_CONFIG_H

#include "mode.h"

#ifdef __cplusplus
extern "C" {
#endif

bool flash_config_read(pico_bc250_mode_t *out);
void flash_config_write(pico_bc250_mode_t m);

#ifdef __cplusplus
}
#endif

#endif
