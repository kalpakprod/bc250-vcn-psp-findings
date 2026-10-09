# bridge library: DS5Dongle + HA webhook path.
# Ported from DS5Dongle-WoL, split into bridge_init/tick/shutdown.

add_library(bridge STATIC
    audio.cpp
    battery_led.cpp
    bridge_main.cpp
    bt.cpp
    button_functions.cpp
    cmd.cpp
    config.cpp
    dse.cpp
    ps_shortcut.cpp
    ram_mem.c
    state_mgr.cpp
    usb.cpp
    usb_descriptors.cpp
    wake.cpp
    wol.cpp
)

target_include_directories(bridge PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(bridge PUBLIC
    pico_stdlib
    pico_cyw43_arch_lwip_poll
    tinyusb_device
    tinyusb_board
    pico_btstack_cyw43
    pico_btstack_ble
    pico_btstack_classic
    pico_btstack_hid_host
)
