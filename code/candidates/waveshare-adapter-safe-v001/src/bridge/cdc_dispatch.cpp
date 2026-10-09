#include "cdc_dispatch.h"
#include "tusb.h"
#include <string.h>

namespace {
volatile bool g_dtr = false;
volatile uint32_t g_commands = 0;
char g_line[128];
size_t g_len = 0;
}

extern "C" __attribute__((weak)) void bridge_cdc_command(char const *line, size_t len) {
    (void)line; (void)len;
}

extern "C" bool cdc_dispatch_dtr(void) { return g_dtr; }
extern "C" uint32_t cdc_dispatch_commands(void) { return g_commands; }
extern "C" void cdc_dispatch_reset(void) { g_len = 0; g_commands = 0; }

#if defined(ENABLE_SERIAL) && ENABLE_SERIAL
extern "C" void tud_cdc_line_state_cb(uint8_t itf, bool dtr, bool rts) {
    (void)itf; (void)rts;
    g_dtr = dtr;
    if (!dtr) g_len = 0;
}

extern "C" void tud_cdc_rx_cb(uint8_t itf) {
    (void)itf;
    if (!g_dtr || !tud_cdc_connected()) return;
    uint8_t buf[64];
    while (tud_cdc_available()) {
        uint32_t n = tud_cdc_read(buf, sizeof(buf));
        for (uint32_t i = 0; i < n; ++i) {
            char c = static_cast<char>(buf[i]);
            if (c == '\r' || c == '\n') {
                if (g_len) {
                    bridge_cdc_command(g_line, g_len);
                    ++g_commands;
                    g_len = 0;
                }
            } else if (g_len + 1 < sizeof(g_line)) {
                g_line[g_len++] = c;
            } else {
                // Oversized command: drop atomically until delimiter.
                g_len = 0;
            }
        }
    }
}
#endif
