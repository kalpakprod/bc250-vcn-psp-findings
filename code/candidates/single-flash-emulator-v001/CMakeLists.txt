cmake_minimum_required(VERSION 3.13)

if(NOT PICO_SDK_PATH)
    message(FATAL_ERROR "Set PICO_SDK_PATH to the locally available Pico SDK")
endif()

include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(bc250_spi_header_capture C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(spi_header_capture src/main.c)
target_link_libraries(spi_header_capture pico_stdlib hardware_pio)
pico_generate_pio_header(
    spi_header_capture
    ${CMAKE_CURRENT_LIST_DIR}/pio/spi_header_capture.pio
)

pico_enable_stdio_usb(spi_header_capture 1)
pico_enable_stdio_uart(spi_header_capture 0)
