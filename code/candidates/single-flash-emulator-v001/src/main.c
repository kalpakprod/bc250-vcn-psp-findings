#include <stdio.h>

#include "hardware/pio.h"
#include "pico/stdlib.h"
#include "spi_header_capture.pio.h"

// Default SPI0 pins from the local Waveshare RP2350B-Plus-W board profile.
// These are capture inputs only; they do not establish BC-250/J4004 wiring.
enum {
  SPI_CS_PIN = 17,
  SPI_CLK_PIN = 18,
  SPI_MOSI_PIN = 19,
};

int main(void) {
  stdio_init_all();

  PIO pio = pio0;
  uint sm = 0;
  uint offset = pio_add_program(pio, &spi_header_capture_program);
  pio_sm_config config = spi_header_capture_program_get_default_config(offset);

  sm_config_set_in_pins(&config, SPI_MOSI_PIN);
  sm_config_set_jmp_pin(&config, SPI_CS_PIN);
  sm_config_set_in_shift(&config, false, false, 32);

  for (uint pin = SPI_CS_PIN; pin <= SPI_MOSI_PIN; ++pin) {
    pio_gpio_init(pio, pin);
  }
  pio_sm_set_consecutive_pindirs(pio, sm, SPI_CS_PIN, 3, false);
  pio_sm_init(pio, sm, offset, &config);
  pio_sm_set_enabled(pio, sm, true);

  while (true) {
    if (!pio_sm_is_rx_fifo_empty(pio, sm)) {
      uint32_t prefix = pio_sm_get(pio, sm);
      printf("SPI_PREFIX_32,%08lx\n", (unsigned long)prefix);
    }
    tight_loop_contents();
  }
}
