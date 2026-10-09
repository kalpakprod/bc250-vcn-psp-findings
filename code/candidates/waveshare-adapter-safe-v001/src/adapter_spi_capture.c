#include "adapter_spi_capture.h"
#include "adapter_flash_transport.h"
#include "adapter_spi_capture.pio.h"
#include "mode/mode.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/clocks.h"
#include "pico/time.h"
#include <stdio.h>
#include <string.h>

#define BASE 10u
#define WORDS 2048u
static uint32_t samples[WORDS];
static PIO owned_pio;
static unsigned sm,offset,read_pos;
static int channel=-1;
static unsigned state; /* 0 idle, 1 running, 2 complete, 3 timeout, 4 overrun */
static uint32_t sample_hz,started;
static bool scratch_leased;

void adapter_spi_capture_stop(void) {
    if(owned_pio) {
        pio_sm_set_enabled(owned_pio,sm,false);
        if(channel>=0){dma_channel_abort(channel);dma_channel_unclaim(channel);}
        pio_sm_clear_fifos(owned_pio,sm);
        pio_remove_program_and_unclaim_sm(&adapter_spi_capture_program,owned_pio,sm,offset);
        for(unsigned pin=BASE;pin<BASE+4;++pin){gpio_init(pin);gpio_set_dir(pin,GPIO_IN);gpio_disable_pulls(pin);}
    }
    owned_pio=NULL;channel=-1;state=0;read_pos=sample_hz=0;
    if (!scratch_leased) memset(samples,0,sizeof(samples));
}
bool adapter_spi_capture_start(bool verified) {
    if(!verified || scratch_leased ||
       (mode_load()!=MODE_DIAGNOSTIC && mode_load()!=MODE_MONITOR))return false;
    adapter_flash_transport_tick();
    if(adapter_flash_transport_ready())return false;
    adapter_spi_capture_stop();
    if(!pio_claim_free_sm_and_add_program_for_gpio_range(&adapter_spi_capture_program,&owned_pio,&sm,&offset,BASE,4,true)) {owned_pio=NULL;return false;}
    channel=dma_claim_unused_channel(false);
    if(channel<0){pio_remove_program_and_unclaim_sm(&adapter_spi_capture_program,owned_pio,sm,offset);owned_pio=NULL;return false;}
    pio_sm_config cfg=adapter_spi_capture_program_get_default_config(offset);
    sm_config_set_in_pins(&cfg,BASE);
    sm_config_set_in_shift(&cfg,true,true,32);
    sm_config_set_fifo_join(&cfg,PIO_FIFO_JOIN_NONE);
    sm_config_set_clkdiv(&cfg,1.0f);
    pio_sm_init(owned_pio,sm,offset,&cfg);
    pio_sm_set_consecutive_pindirs(owned_pio,sm,BASE,4,false);
    for(unsigned pin=BASE;pin<BASE+4;++pin){gpio_init(pin);gpio_set_dir(pin,GPIO_IN);gpio_disable_pulls(pin);pio_gpio_init(owned_pio,pin);}
    dma_channel_config dc=dma_channel_get_default_config(channel);
    channel_config_set_transfer_data_size(&dc,DMA_SIZE_32);
    channel_config_set_read_increment(&dc,false);
    channel_config_set_write_increment(&dc,true);
    channel_config_set_dreq(&dc,pio_get_dreq(owned_pio,sm,false));
    dma_channel_configure(channel,&dc,samples,&owned_pio->rxf[sm],WORDS,false);
    pio_sm_put_blocking(owned_pio,sm,WORDS*8-1);
    owned_pio->fdebug=1u<<sm; // W1C: clear only this SM RXSTALL.
    sample_hz=clock_get_hz(clk_sys)/2;started=to_ms_since_boot(get_absolute_time());state=1;
    dma_start_channel_mask(1u<<(unsigned)channel);
    pio_sm_set_enabled(owned_pio,sm,true);
    return true;
}
void adapter_spi_capture_tick(void) {
    if(owned_pio && mode_load()!=MODE_DIAGNOSTIC && mode_load()!=MODE_MONITOR){adapter_spi_capture_stop();return;}
    if(state!=1)return;
    if(owned_pio->fdebug & (1u<<sm)){adapter_spi_capture_stop();state=4;return;}
    if(!dma_channel_is_busy(channel)){pio_sm_set_enabled(owned_pio,sm,false);state=2;}
    else if((uint32_t)(to_ms_since_boot(get_absolute_time())-started)>1000){adapter_spi_capture_stop();state=3;}
}
unsigned adapter_spi_capture_read(uint32_t *out,unsigned capacity) {
    if(state!=2 || (mode_load()!=MODE_DIAGNOSTIC && mode_load()!=MODE_MONITOR))return 0;
    if(capacity>32)capacity=32;
    unsigned left=WORDS-read_pos;if(capacity>left)capacity=left;
    memcpy(out,samples+read_pos,capacity*sizeof(uint32_t));read_pos+=capacity;return capacity;
}
void adapter_spi_capture_status(char *out,unsigned capacity) {
    snprintf(out,capacity,"{\"state\":\"%s\",\"sample_hz\":%lu,\"samples\":%u,\"remaining_words\":%u,\"gpio_base\":10,\"full_rom\":false,\"quad\":false}",state==1?"running":state==2?"complete":state==3?"timeout":state==4?"overrun":"idle",(unsigned long)sample_hz,state==2?WORDS*8:0,state==2?WORDS-read_pos:0);
}

uint8_t *adapter_spi_capture_scratch_take(unsigned capacity){
 if(scratch_leased || capacity>sizeof(samples) || mode_load()!=MODE_FLASH)return NULL;
 adapter_spi_capture_stop();scratch_leased=true;return (uint8_t*)samples;
}
void adapter_spi_capture_scratch_release(void){memset(samples,0,sizeof(samples));scratch_leased=false;}
