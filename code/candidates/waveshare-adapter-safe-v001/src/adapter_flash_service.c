#include "adapter_flash_service.h"
#include "adapter_flash_authority.h"
#include "adapter_flash_engine.h"
#include "adapter_flash_transport.h"
#include "mode/mode.h"
#include "pico/unique_id.h"
#include "pico/time.h"
#include "tusb.h"
#include <stdio.h>
#include <string.h>

__attribute__((weak)) bool adapter_flash_transport_select_slot(unsigned slot){return slot==0;}
__attribute__((weak)) unsigned adapter_flash_transport_slot(void){return 0;}
static bool known,confirmed;
static uint32_t jedec,generation,opened;
static uint64_t adapter_tag;
static flash_operation operation;
static uint8_t data[128];
static unsigned data_size;
static bool approved,staged;
static uint32_t staged_address;
static uint8_t image_hash[32],approved_hash[32],backup_hash[32],sector_copy[4096];
static void clear_write_permit(void){approved=staged=false;memset(image_hash,0,32);memset(approved_hash,0,32);memset(backup_hash,0,32);memset(sector_copy,0,sizeof(sector_copy));}
static uint32_t now_ms(void){return to_ms_since_boot(get_absolute_time());}
static bool context_valid(void){return confirmed && mode_load()==MODE_FLASH && generation==mode_generation() && tud_cdc_ready() && (uint32_t)(now_ms()-opened)<=10000;}
void adapter_flash_service_close(void){
 adapter_flash_engine_stop();adapter_flash_transport_abort(NULL);adapter_flash_authority_clear();
 clear_write_permit();
 known=confirmed=false;jedec=data_size=0;memset(data,0,sizeof(data));
}
bool adapter_flash_service_open(bool wiring,bool isolated){return adapter_flash_service_open_slot(0,wiring,isolated);}
bool adapter_flash_service_open_slot(unsigned slot,bool wiring,bool isolated){
 if(!wiring || !isolated || mode_load()!=MODE_FLASH || !tud_cdc_ready() || adapter_flash_engine_state()==FLASH_ENGINE_RUNNING)return false;
 adapter_flash_service_close();
 if(!adapter_flash_transport_select_slot(slot))return false;
 if(!adapter_flash_transport_enable(wiring,isolated))return false;
 pico_unique_board_id_t id;pico_get_unique_board_id(&id);adapter_tag=0;
 for(unsigned i=0;i<8;++i)adapter_tag=(adapter_tag<<8)|id.id[i];
 generation=mode_generation();opened=now_ms();confirmed=true;operation=FLASH_ID;
 flash_target target={0,0,true,false};
 if(!adapter_flash_engine_start(&target,FLASH_ID,0,NULL,0,opened,adapter_flash_transport_exchange,adapter_flash_transport_abort,NULL)){adapter_flash_service_close();return false;}
 return true;
}
bool adapter_flash_service_read(uint32_t address,unsigned length){
 if(!context_valid() || !known || adapter_flash_engine_state()==FLASH_ENGINE_RUNNING)return false;
 flash_target target={0x1000000,jedec,true,false};uint8_t frame[260];
 if(!adapter_flash_request(&target,FLASH_READ,address,NULL,length,frame,sizeof(frame)))return false;
 adapter_flash_engine_stop();
 if(!adapter_flash_transport_enable(true,true))return false;
 data_size=0;memset(data,0,sizeof(data));operation=FLASH_READ;
 if(!adapter_flash_engine_start(&target,FLASH_READ,address,NULL,length,now_ms(),adapter_flash_transport_exchange,adapter_flash_transport_abort,NULL)){adapter_flash_service_close();return false;}
 return true;
}
bool adapter_flash_service_approve(uint64_t tag,uint32_t chip,uint32_t epoch,const uint8_t image[32],const uint8_t hash[32],const uint8_t b1[32],const uint8_t b2[32],bool recovery,bool protected_regions){
 clear_write_permit();
 if(!context_valid() || !known || adapter_flash_engine_state()==FLASH_ENGINE_RUNNING || tag!=adapter_tag || chip!=jedec || epoch!=generation || !protected_regions)return false;
 if(!adapter_flash_authority_identify(adapter_tag,jedec,generation) || !adapter_flash_authority_approve(adapter_tag,generation,image,hash,b1,b2,recovery))return false;
 memcpy(image_hash,image,32);memcpy(approved_hash,hash,32);memcpy(backup_hash,b1,32);approved=true;return true;
}
bool adapter_flash_service_stage(uint32_t address,const uint8_t image[32],const uint8_t sector[4096]){
 staged=false;memset(sector_copy,0,sizeof(sector_copy));
 if(!context_valid() || !known || !approved || adapter_flash_engine_state()==FLASH_ENGINE_RUNNING || !image || memcmp(image,image_hash,32) || !sector || (address&4095) || address>0x1000000u-4096)return false;
 memcpy(sector_copy,sector,4096);staged_address=address;staged=true;return true;
}
bool adapter_flash_service_write(bool erase,uint32_t address,const uint8_t image[32],const uint8_t *payload,unsigned length){
 if(!context_valid() || !known || !approved || !staged || adapter_flash_engine_state()==FLASH_ENGINE_RUNNING || !image || memcmp(image,image_hash,32))return false;
 if(address<staged_address || address-staged_address>=4096)return false;
 const unsigned off=address-staged_address;
 if(erase){if(address!=staged_address || payload || length!=4096)return false;}
 else if(!payload || !length || length>256 || length>4096-off || (address&255)+length>256 || memcmp(payload,sector_copy+off,length))return false;
 // Check whole request before touching pins. Engine stop/transport enable revoke
 // old low-level authority, then reconstruct only this frozen approved sector.
 adapter_flash_engine_stop();
 if(!adapter_flash_transport_enable(true,true)){clear_write_permit();return false;}
 if(!adapter_flash_authority_identify(adapter_tag,jedec,generation) || !adapter_flash_authority_approve(adapter_tag,generation,image_hash,approved_hash,backup_hash,backup_hash,true) || !adapter_flash_authority_sector(adapter_tag,generation,image_hash,staged_address,sector_copy)){adapter_flash_service_close();return false;}
 const uint8_t *frozen_payload=erase?NULL:sector_copy+off;
 flash_target target;operation=erase?FLASH_ERASE_SECTOR:FLASH_PROGRAM;
 if(!adapter_flash_authority_allows(adapter_tag,generation,image_hash,operation,address,frozen_payload,length,&target)){adapter_flash_service_close();return false;}
 data_size=0;memset(data,0,sizeof(data));
 if(!adapter_flash_engine_start(&target,operation,address,frozen_payload,length,now_ms(),adapter_flash_transport_exchange,adapter_flash_transport_abort,NULL)){adapter_flash_service_close();return false;}
 return true;
}
bool adapter_flash_service_commit(bool erase,uint32_t address){
 if(!staged || address<staged_address || address-staged_address>=4096)return false;
 unsigned off=address-staged_address;
 return adapter_flash_service_write(erase,address,image_hash,erase?NULL:sector_copy+off,erase?4096:256);
}
void adapter_flash_service_tick(void){
 if(confirmed && !context_valid()){adapter_flash_service_close();return;}
 if(adapter_flash_engine_state()!=FLASH_ENGINE_RUNNING)return;
 adapter_flash_engine_tick(now_ms(),context_valid() && adapter_flash_transport_ready());
 if(adapter_flash_engine_state()==FLASH_ENGINE_FAILED){clear_write_permit();return;}
 if(adapter_flash_engine_state()==FLASH_ENGINE_DONE){
  data_size=adapter_flash_engine_read(data,sizeof(data));
  if(operation==FLASH_ID){
   if(data_size==3){jedec=((uint32_t)data[0]<<16)|((uint32_t)data[1]<<8)|data[2];known=adapter_flash_authority_identify(adapter_tag,jedec,generation);}
   if(!known){adapter_flash_service_close();return;}
   data_size=0;memset(data,0,sizeof(data));
  }
 }
}
void adapter_flash_service_status(char *out,unsigned capacity){
 snprintf(out,capacity,"{\"slot\":%u,\"identified\":%s,\"jedec\":\"%06lx\",\"state\":%u,\"result\":\"%s\",\"data_bytes\":%u,\"write_enabled\":%s,\"adapter_tag\":\"%016llx\",\"generation\":%lu}",adapter_flash_transport_slot(),known?"true":"false",(unsigned long)jedec,(unsigned)adapter_flash_engine_state(),adapter_flash_engine_result(),data_size,approved && staged && context_valid()?"true":"false",(unsigned long long)adapter_tag,(unsigned long)generation);
}
unsigned adapter_flash_service_data(uint8_t *out,unsigned capacity){
 if(!out || !context_valid() || operation!=FLASH_READ || adapter_flash_engine_state()!=FLASH_ENGINE_DONE)return 0;
 unsigned n=data_size;if(n>capacity)n=capacity;memcpy(out,data,n);return n;
}
