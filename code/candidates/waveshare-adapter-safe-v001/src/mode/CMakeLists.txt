add_library(mode STATIC
    mode.c
    flash_config.c
)

target_include_directories(mode PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(mode PUBLIC
    pico_stdlib
    pico_flash
    hardware_flash
    hardware_sync
    hardware_gpio
)
