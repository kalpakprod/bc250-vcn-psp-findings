#include "adapter_flash_protocol.h"
#include <string.h>

unsigned adapter_flash_request(const flash_target *t,flash_operation op,uint32_t address,
                               const uint8_t *payload,unsigned length,uint8_t *out,unsigned capacity) {
    if(!t || !out || !capacity || !t->exclusive_bus)return 0;
    if(op==FLASH_ID || op==FLASH_STATUS) {
        if(address || length || payload)return 0;
        out[0]=op==FLASH_ID?0x9F:0x05;return 1;
    }
    if(!t->jedec || t->jedec>0xFFFFFF || !t->size || t->size>0x1000000)return 0;
    if(op==FLASH_WRITE_ENABLE) {
        if(!t->write_approved || address || length || payload)return 0;
        out[0]=0x06;return 1;
    }
    uint8_t opcode;
    unsigned frame_size=4;
    if(op==FLASH_READ) {
        if(payload || !length || length>128)return 0;
        opcode=0x03;
    } else if(op==FLASH_PROGRAM) {
        if(!t->write_approved || !payload || !length || length>256 || (address&255)+length>256)return 0;
        frame_size+=length;opcode=0x02;
    } else if(op==FLASH_ERASE_SECTOR) {
        if(!t->write_approved || payload || length!=4096 || (address&4095))return 0;
        opcode=0x20;
    } else return 0;
    if(address>=t->size || length>t->size-address || capacity<frame_size)return 0;
    out[0]=opcode;out[1]=(uint8_t)(address>>16);out[2]=(uint8_t)(address>>8);out[3]=(uint8_t)address;
    if(op==FLASH_PROGRAM)memcpy(out+4,payload,length);
    return frame_size;
}
