#pragma once
#include <stdbool.h>
#include <stdint.h>
#define ADAPTER_SMBUS_TRACE_MAX 64
typedef struct { uint32_t timestamp_us; uint8_t address; uint8_t flags; uint8_t length; uint8_t data[16]; } adapter_smbus_frame_t;
bool adapter_smbus_enable(bool verified); void adapter_smbus_disable(void);
bool adapter_smbus_push(uint8_t address,const uint8_t*data,unsigned length,bool read,uint32_t timestamp_us);
unsigned adapter_smbus_read(adapter_smbus_frame_t*out,unsigned capacity);
void adapter_smbus_status_json(char*out,unsigned capacity);
