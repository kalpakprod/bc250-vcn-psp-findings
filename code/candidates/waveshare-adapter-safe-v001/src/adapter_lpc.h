#pragma once
#include <stdbool.h>
#include <stdint.h>
#define ADAPTER_LPC_TRACE_MAX 128
typedef struct { uint32_t timestamp_us; uint8_t value; } adapter_lpc_sample_t;
bool adapter_lpc_enable(bool verified); void adapter_lpc_disable(void);
bool adapter_lpc_push(uint8_t value,uint32_t timestamp_us);
unsigned adapter_lpc_read(adapter_lpc_sample_t*out,unsigned capacity);
void adapter_lpc_status_json(char*out,unsigned capacity);
