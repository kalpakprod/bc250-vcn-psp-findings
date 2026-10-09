#include "flash_config.h"

#include <string.h>

#include "hardware/flash.h"
#include "hardware/sync.h"
#include "pico/flash.h"

// Last 4 KiB sector of the Waveshare 16 MiB flash. Firmware image sits
// in the first ~2 MiB; the last sector is a safe island.
#define FLASH_CONFIG_OFFSET 0x00FFF000u
#define FLASH_CONFIG_MAGIC  0xBC250C0Fu

typedef struct {
    uint32_t magic;
    uint32_t mode;
    uint32_t crc;
} flash_config_t;

static uint32_t crc32(const uint8_t *data, size_t len) {
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (int b = 0; b < 8; ++b) {
            crc = (crc >> 1) ^ (0xEDB88320u & -(int32_t)(crc & 1u));
        }
    }
    return ~crc;
}

bool flash_config_read(pico_bc250_mode_t *out) {
    const flash_config_t *fc =
        (const flash_config_t *)(XIP_BASE + FLASH_CONFIG_OFFSET);

    if (fc->magic != FLASH_CONFIG_MAGIC) return false;

    uint32_t payload[2] = { fc->magic, fc->mode };
    if (crc32((const uint8_t *)payload, sizeof(payload)) != fc->crc) return false;

    if (fc->mode > (uint32_t)MODE_VCN_UNBLOCK) return false;

    *out = (pico_bc250_mode_t)fc->mode;
    return true;
}

// Runs under flash_safe_execute so core1 and XIP are parked.
static void flash_config_write_cb(void *param) {
    const flash_config_t *fc = (const flash_config_t *)param;

    uint8_t page[FLASH_PAGE_SIZE];
    memset(page, 0xFF, sizeof(page));
    memcpy(page, fc, sizeof(*fc));

    flash_range_erase(FLASH_CONFIG_OFFSET, FLASH_SECTOR_SIZE);
    flash_range_program(FLASH_CONFIG_OFFSET, page, FLASH_PAGE_SIZE);
}

void flash_config_write(pico_bc250_mode_t m) {
    flash_config_t fc = {
        .magic = FLASH_CONFIG_MAGIC,
        .mode  = (uint32_t)m,
        .crc   = 0,
    };
    uint32_t payload[2] = { fc.magic, fc.mode };
    fc.crc = crc32((const uint8_t *)payload, sizeof(payload));

    // 500 ms is generous; erase+program of a single sector is well under 100 ms.
    (void)flash_safe_execute(flash_config_write_cb, &fc, 500);
}
