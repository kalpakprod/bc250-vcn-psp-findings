#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
uint8_t *adapter_spi_capture_scratch_take(unsigned capacity);
void adapter_spi_capture_scratch_release(void);
bool adapter_spi_capture_start(bool verified);
void adapter_spi_capture_stop(void);
void adapter_spi_capture_tick(void);
unsigned adapter_spi_capture_read(uint32_t *out,unsigned capacity);
void adapter_spi_capture_status(char *out,unsigned capacity);
#ifdef __cplusplus
}
#endif
/* TOCTOU PIO topology is provided by adapter_toctou.pio; host control lives in adapter_toctou.h. */
