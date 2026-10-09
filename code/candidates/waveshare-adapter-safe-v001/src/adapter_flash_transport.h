#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Operator-supplied confirmations are NOT electrical/bus-isolation proof.
 * No caller/CDC write endpoint is provided here; default disabled. */
bool adapter_flash_transport_enable(bool wiring_confirmed,bool bus_isolated);
/* Slot 0 is the documented CS13 route. Slot 1 stays disabled unless the
 * board build explicitly supplies ADAPTER_FLASH_SLOT1_CS. */
bool adapter_flash_transport_select_slot(unsigned slot);
unsigned adapter_flash_transport_slot(void);
bool adapter_flash_transport_ready(void);
void adapter_flash_transport_tick(void);
int adapter_flash_transport_exchange(const uint8_t *tx,unsigned txlen,uint8_t *rx,unsigned rxlen,void *context);
void adapter_flash_transport_abort(void *context);
#ifdef __cplusplus
}
#endif
