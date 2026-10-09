#pragma once
#include <stdbool.h>
#include <stdint.h>
typedef enum { ADAPTER_PIN_UNKNOWN=0, ADAPTER_PIN_INPUT=1, ADAPTER_PIN_OUTPUT=2 } adapter_pin_dir_t;
typedef struct { const char *name; int pin; adapter_pin_dir_t direction; bool verified; } adapter_pin_info_t;
void adapter_io_map_reset(void); bool adapter_io_map_set_input(const char*,int,bool); bool adapter_io_map_get(const char*,adapter_pin_info_t*); void adapter_io_map_status_json(char*,unsigned);
