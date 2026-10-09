# pico-bc250 rig static library: TOCTOU SPI sniff+override over PIO.
# Consumed by src/main.c when MODE_TOCTOU is active.

add_library(rig STATIC
    rig.c
)

pico_generate_pio_header(rig ${CMAKE_CURRENT_SOURCE_DIR}/spi_toctou.pio)

target_include_directories(rig PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(rig PUBLIC
    pico_stdlib
    hardware_pio
    hardware_dma
    hardware_clocks
    hardware_vreg
    hardware_sync
    hardware_irq
)
