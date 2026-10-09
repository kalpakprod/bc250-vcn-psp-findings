#pragma once
#include <stdbool.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
bool adapter_metric_update(const char *name,int32_t milli,uint32_t now);
void adapter_metrics_json(char *out,unsigned capacity,uint32_t now);
void adapter_host_alive(uint32_t now);
const char *adapter_host_power(uint32_t now);
#ifdef __cplusplus
}
#endif
