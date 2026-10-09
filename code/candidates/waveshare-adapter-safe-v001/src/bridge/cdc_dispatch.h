#pragma once
#include <stddef.h>
#include <stdint.h>
#ifndef __cplusplus
#include <stdbool.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

bool cdc_dispatch_dtr(void);
uint32_t cdc_dispatch_commands(void);
void cdc_dispatch_reset(void);

#ifdef __cplusplus
}
#endif
