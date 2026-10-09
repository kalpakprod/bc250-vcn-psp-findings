#include "adapter_flash_frames.h"
#include "adapter_flash_service.h"
static uint32_t be32(const uint8_t*p){return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];}
uint32_t adapter_flash_frame_crc(const uint8_t*p,unsigned length){uint32_t crc=0xFFFFFFFF;for(unsigned i=0;i<length;++i){crc^=p[i];for(unsigned j=0;j<8;++j)crc=(crc>>1)^((0u-(crc&1))&0xEDB88320u);}return ~crc;}
bool adapter_flash_frame_apply(unsigned kind,const uint8_t*f,unsigned length){
 unsigned expected=kind==1?FLASH_APPROVAL_FRAME_SIZE:kind==2?FLASH_SECTOR_FRAME_SIZE:0;
 if(!f || !expected || length!=expected || f[0]!=1 || f[2] || f[3] || be32(f+length-4)!=adapter_flash_frame_crc(f,length-4))return false;
 if(kind==1){
  if(f[1]!=3)return false; // explicit recovery + protected-region attestations.
  uint64_t tag=((uint64_t)be32(f+4)<<32)|be32(f+8);
  return adapter_flash_service_approve(tag,be32(f+12),be32(f+16),f+20,f+52,f+84,f+116,true,true);
 }
 if(f[1])return false;
 return adapter_flash_service_stage(be32(f+4),f+8,f+40);
}
