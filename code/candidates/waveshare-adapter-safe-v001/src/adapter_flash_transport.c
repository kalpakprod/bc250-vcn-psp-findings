#include "adapter_flash_transport.h"
#include "adapter_spi_capture.h"
#include "adapter_flash_authority.h"
#include "mode/mode.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"
#include "pico/time.h"
#include <string.h>

#define CS selected_cs
static bool enabled,active;
static unsigned selected_cs=13u,selected_slot;
bool adapter_flash_transport_select_slot(unsigned slot){
 if(enabled || active || slot>1)return false;
 unsigned pin=13u;
 if(slot){
#ifdef ADAPTER_FLASH_SLOT1_CS
  pin=ADAPTER_FLASH_SLOT1_CS;
  if(pin>29 || (pin>=10 && pin<=13))return false;
#else
  return false;
#endif
 }
 selected_slot=slot;selected_cs=pin;return true;
}
unsigned adapter_flash_transport_slot(void){return selected_slot;}
static uint32_t lease_started,started;
static uint8_t frame[260],received_data[128];
static unsigned frame_size,response_size,sent,received;
static uint32_t now_ms(void){return to_ms_since_boot(get_absolute_time());}
void adapter_flash_transport_abort(void *context){
 (void)context;
 if(enabled){gpio_put(CS,true);gpio_init(CS);gpio_set_dir(CS,GPIO_IN);gpio_disable_pulls(CS);spi_deinit(spi1);for(unsigned pin=10;pin<=13;++pin){gpio_init(pin);gpio_set_dir(pin,GPIO_IN);gpio_disable_pulls(pin);}}
 adapter_flash_authority_clear();
 enabled=active=false;frame_size=response_size=sent=received=0;
 memset(frame,0,sizeof(frame));memset(received_data,0,sizeof(received_data));
}
bool adapter_flash_transport_ready(void){return enabled && mode_load()==MODE_FLASH && (uint32_t)(now_ms()-lease_started)<=10000;}
bool adapter_flash_transport_enable(bool wiring,bool isolated){
 if(!wiring || !isolated || mode_load()!=MODE_FLASH || active)return false;
 adapter_flash_transport_abort(NULL);adapter_spi_capture_stop();
 for(unsigned pin=10;pin<=13;++pin){gpio_init(pin);gpio_set_dir(pin,GPIO_IN);gpio_disable_pulls(pin);}
 gpio_put(CS,true);gpio_set_dir(CS,GPIO_OUT);
 spi_init(spi1,100000);spi_set_format(spi1,8,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);
 for(unsigned pin=10;pin<=12;++pin)gpio_set_function(pin,GPIO_FUNC_SPI);
 enabled=true;lease_started=now_ms();return true;
}
void adapter_flash_transport_tick(void){if(enabled && !adapter_flash_transport_ready())adapter_flash_transport_abort(NULL);}
static bool allowed_frame(const uint8_t *tx,unsigned n,unsigned r){
 if(!tx || !n || n>260 || r>128)return false;
 switch(tx[0]){
 case 0x9F:return n==1 && r==3;
 case 0x05:return n==1 && r==1;
 case 0x06:return n==1 && r==0;
 case 0x03:return n==4 && r>0;
 case 0x02:return n>=5 && r==0 && ((unsigned)tx[3]+n-4)<=256;
 case 0x20:return n==4 && r==0 && !(tx[3] || (tx[2]&15));
 default:return false;
 }
}
int adapter_flash_transport_exchange(const uint8_t *tx,unsigned n,uint8_t *rx,unsigned r,void *context){
 (void)context;
 if(!adapter_flash_transport_ready() || (r && !rx) || !allowed_frame(tx,n,r)){adapter_flash_transport_abort(NULL);return -1;}
 if(!active){memcpy(frame,tx,n);frame_size=n;response_size=r;sent=received=0;started=now_ms();active=true;gpio_put(CS,false);}
 else if(n!=frame_size || r!=response_size || memcmp(frame,tx,n)){adapter_flash_transport_abort(NULL);return -1;}
 if((uint32_t)(now_ms()-started)>1000){adapter_flash_transport_abort(NULL);return -1;}
 const unsigned total=frame_size+response_size;
 // Each call has a fixed instruction budget; no blocking SDK transfer API.
 for(unsigned budget=0;budget<64;++budget){
  bool progress=false;
  if(received<sent && spi_is_readable(spi1)){
   uint8_t value=(uint8_t)spi_get_hw(spi1)->dr;
   if(received>=frame_size)received_data[received-frame_size]=value;
   ++received;progress=true;
  }
  if(sent<total && sent-received<8 && spi_is_writable(spi1)){
   spi_get_hw(spi1)->dr=sent<frame_size?frame[sent]:0;
   ++sent;progress=true;
  }
  if(!progress)break;
 }
 if(received==total && !spi_is_busy(spi1)){
  gpio_put(CS,true);if(r)memcpy(rx,received_data,r);active=false;
  memset(frame,0,sizeof(frame));memset(received_data,0,sizeof(received_data));return 1;
 }
 return 0;
}
