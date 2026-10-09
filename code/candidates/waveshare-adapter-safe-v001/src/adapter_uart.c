#include "adapter_uart.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"
#include "hardware/regs/uart.h"
#include "hardware/address_mapped.h"
#include <stdio.h>
#include <string.h>

// Input-only observer. No TX pin, no flow-control outputs, no persisted enable.
static uint8_t ring[8192];
static unsigned head,count;
static uint32_t dropped;
static bool enabled;
bool adapter_uart_enable(bool verified) {
    if(!verified)return false;
    if(enabled)return true;
    uart_init(uart1,115200);
    uart_set_format(uart1,8,1,UART_PARITY_NONE);
    uart_set_hw_flow(uart1,false,false);
    uart_set_irq_enables(uart1,false,false);
    // uart_init normally enables both directions internally; explicitly remove TX.
    hw_clear_bits(&uart_get_hw(uart1)->cr,UART_UARTCR_TXE_BITS);
    gpio_init(ADAPTER_UART_RX_GPIO);
    gpio_set_dir(ADAPTER_UART_RX_GPIO,GPIO_IN);
    gpio_disable_pulls(ADAPTER_UART_RX_GPIO);
    gpio_set_function(ADAPTER_UART_RX_GPIO,GPIO_FUNC_UART);
    enabled=true;
    return true;
}
void adapter_uart_disable(void) {
    if(enabled){uart_deinit(uart1);gpio_init(ADAPTER_UART_RX_GPIO);gpio_set_dir(ADAPTER_UART_RX_GPIO,GPIO_IN);gpio_disable_pulls(ADAPTER_UART_RX_GPIO);}
    enabled=false;memset(ring,0,sizeof(ring));head=count=0;
}
void adapter_uart_tick(void) {
    if(!enabled)return;
    // A fixed per-loop budget prevents UART activity monopolizing audio/BT/USB.
    for(unsigned budget=0;budget<64 && uart_is_readable(uart1);++budget){
        const uint8_t value=(uint8_t)uart_getc(uart1);
        if(count==sizeof(ring)){head=(head+1)%sizeof(ring);--count;++dropped;}
        ring[(head+count)%sizeof(ring)]=value;++count;
    }
}
unsigned adapter_uart_read(uint8_t *out,unsigned capacity) {
    if(capacity>128)capacity=128;
    unsigned copied=0;
    while(copied<capacity && count){out[copied++]=ring[head];head=(head+1)%sizeof(ring);--count;}
    return copied;
}
void adapter_uart_status_json(char *out,unsigned capacity) {
    snprintf(out,capacity,"{\"enabled\":%s,\"rx_only\":true,\"gpio\":9,\"available\":%u,\"dropped\":%lu}",enabled?"true":"false",count,(unsigned long)dropped);
}
