#ifndef TOCTOU_ENGINE_H
#define TOCTOU_ENGINE_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TOCTOU_PIN_MOSI 10
#define TOCTOU_PIN_SCK  12
#define TOCTOU_PIN_CS   13
#define TOCTOU_PIN_MISO 16
#define TOCTOU_PIN_CS0  17
#define TOCTOU_PIN_CS1  18

// Default anchor/trigger for AMD PSP BL_PUBLIC_KEY reading
// Trigger on command: 0x03 (read) + 0x9DB8DC
#define TOCTOU_DEFAULT_TRIGGER ((0x03u << 24) | 0x9DB8DCu)
// Switch length: 0x338 commands
#define TOCTOU_DEFAULT_COUNT   (0x338u - 1u)

void toctou_engine_init(void);
bool toctou_engine_configure(uint32_t trigger, uint32_t count);
bool toctou_engine_arm(void);
void toctou_engine_disarm(void);
bool toctou_engine_is_armed(void);
void toctou_engine_status_json(char *out, size_t capacity);
size_t toctou_engine_read_debug(uint16_t *out, size_t max_words);

#ifdef __cplusplus
}
#endif

#endif // TOCTOU_ENGINE_H
