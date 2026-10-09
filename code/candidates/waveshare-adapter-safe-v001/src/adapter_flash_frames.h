#pragma once
#include <stdbool.h>
#include <stdint.h>
#define FLASH_APPROVAL_FRAME_SIZE 152u
#define FLASH_SECTOR_FRAME_SIZE 4140u
uint32_t adapter_flash_frame_crc(const uint8_t *data,unsigned length);
bool adapter_flash_frame_apply(unsigned kind,const uint8_t *frame,unsigned length);
