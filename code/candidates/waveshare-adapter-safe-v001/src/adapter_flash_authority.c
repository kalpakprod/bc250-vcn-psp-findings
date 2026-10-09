#include "adapter_flash_authority.h"
#include <string.h>
static struct {uint64_t tag;uint32_t generation,jedec,sector;bool identified,approved,staged;uint8_t image[32],data[4096];} permit;
static bool digest_valid(const uint8_t *p){if(!p)return false;unsigned any=0;for(unsigned i=0;i<32;++i)any|=p[i];return any!=0;}
void adapter_flash_authority_clear(void){memset(&permit,0,sizeof(permit));}
bool adapter_flash_authority_identify(uint64_t tag,uint32_t jedec,uint32_t generation){
 adapter_flash_authority_clear();
 // Conventional 3-byte addressing profile; other IDs need separate validation.
 if(!tag || (jedec!=0xC22018 && jedec!=0xEF4018))return false;
 permit.tag=tag;permit.jedec=jedec;permit.generation=generation;permit.identified=true;return true;
}
static bool matches(uint64_t tag,uint32_t generation){return permit.identified && permit.tag==tag && permit.generation==generation;}
bool adapter_flash_authority_approve(uint64_t tag,uint32_t generation,const uint8_t image[32],const uint8_t approved[32],const uint8_t backup1[32],const uint8_t backup2[32],bool recovery){
 permit.approved=permit.staged=false;memset(permit.image,0,sizeof(permit.image));memset(permit.data,0,sizeof(permit.data));
 if(!matches(tag,generation) || !recovery || !digest_valid(image) || !digest_valid(approved) || !digest_valid(backup1) || !digest_valid(backup2) || memcmp(image,approved,32) || memcmp(backup1,backup2,32))return false;
 memcpy(permit.image,image,32);permit.approved=true;return true;
}
bool adapter_flash_authority_sector(uint64_t tag,uint32_t generation,const uint8_t image[32],uint32_t address,const uint8_t sector[4096]){
 permit.staged=false;memset(permit.data,0,sizeof(permit.data));
 if(!matches(tag,generation) || !permit.approved || !image || memcmp(image,permit.image,32) || !sector || (address&4095) || address>0x1000000u-4096)return false;
 memcpy(permit.data,sector,4096);permit.sector=address;permit.staged=true;return true;
}
bool adapter_flash_authority_allows(uint64_t tag,uint32_t generation,const uint8_t image[32],flash_operation op,uint32_t address,const uint8_t *payload,unsigned length,flash_target *out){
 if(!out || !matches(tag,generation))return false;
 flash_target target={0x1000000,permit.jedec,true,false};
 if(op==FLASH_PROGRAM || op==FLASH_ERASE_SECTOR){
  if(!permit.approved || !permit.staged || !image || memcmp(image,permit.image,32))return false;
  if(address<permit.sector || address-permit.sector>=4096)return false;
  unsigned off=address-permit.sector;
  if(op==FLASH_PROGRAM && (!payload || !length || length>4096-off || memcmp(payload,permit.data+off,length)))return false;
  if(op==FLASH_ERASE_SECTOR && (address!=permit.sector || length!=4096 || payload))return false;
  target.write_approved=true;
 } else if(op!=FLASH_READ && op!=FLASH_STATUS && op!=FLASH_ID)return false;
 uint8_t frame[260];if(!adapter_flash_request(&target,op,address,payload,length,frame,sizeof(frame)))return false;
 *out=target;return true;
}
