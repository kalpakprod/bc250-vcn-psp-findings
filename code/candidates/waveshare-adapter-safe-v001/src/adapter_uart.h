#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define ADAPTER_UART_RX_GPIO 9u
bool adapter_uart_enable(bool operator_verified_3v3);
void adapter_uart_disable(void);
void adapter_uart_tick(void);
unsigned adapter_uart_read(uint8_t *out,unsigned capacity);
void adapter_uart_status_json(char *out,unsigned capacity);
#ifdef __cplusplus
}
#endif
