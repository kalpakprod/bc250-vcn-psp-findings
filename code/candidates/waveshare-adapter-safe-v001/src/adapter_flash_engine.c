#include "adapter_flash_engine.h"
#include <string.h>

static struct {
 flash_target target;
 flash_operation op;
 uint32_t address,started;
 unsigned length,phase,verified;
 uint8_t payload[256],result[128];
 flash_exchange exchange;
 flash_abort abort;
 void *context;
 flash_engine_state state;
 const char *reason;
} job;
static void finish(bool good,const char *reason) {
 if(job.abort)job.abort(job.context);
 job.state=good?FLASH_ENGINE_DONE:FLASH_ENGINE_FAILED;job.reason=reason;
 memset(job.payload,0,sizeof(job.payload));
 if(!good)memset(job.result,0,sizeof(job.result));
}
void adapter_flash_engine_stop(void) {
 if(job.abort)job.abort(job.context);
 memset(&job,0,sizeof(job));job.reason="idle";
}
bool adapter_flash_engine_start(const flash_target *t,flash_operation op,uint32_t address,
 const uint8_t *payload,unsigned length,uint32_t now,flash_exchange exchange,flash_abort abort,void *context) {
 if(job.state==FLASH_ENGINE_RUNNING || !exchange || !abort)return false;
 if(op!=FLASH_ID && op!=FLASH_STATUS && op!=FLASH_READ && op!=FLASH_PROGRAM && op!=FLASH_ERASE_SECTOR)return false;
 uint8_t frame[260];
 if(!adapter_flash_request(t,op,address,payload,length,frame,sizeof(frame)))return false;
 adapter_flash_engine_stop();job.target=*t;job.op=op;job.address=address;job.length=length;
 job.started=now;job.exchange=exchange;job.abort=abort;job.context=context;job.state=FLASH_ENGINE_RUNNING;job.reason="running";
 if(op==FLASH_PROGRAM)memcpy(job.payload,payload,length);
 job.phase=(op==FLASH_PROGRAM || op==FLASH_ERASE_SECTOR)?0:2;
 return true;
}
void adapter_flash_engine_tick(uint32_t now,bool ownership_valid) {
 if(job.state!=FLASH_ENGINE_RUNNING)return;
 if(!ownership_valid){finish(false,"ownership-lost");return;}
 if((uint32_t)(now-job.started)>5000){finish(false,"timeout");return;}
 uint8_t tx[260],rx[128];unsigned size,rxlen=0;
 flash_operation op=job.phase==0?FLASH_WRITE_ENABLE:job.phase==1 || job.phase==3?FLASH_STATUS:job.phase==4?FLASH_READ:job.op;
 uint32_t address=(job.phase==4)?job.address+job.verified:op==FLASH_STATUS || op==FLASH_ID || op==FLASH_WRITE_ENABLE?0:job.address;
 unsigned length=op==FLASH_STATUS || op==FLASH_ID || op==FLASH_WRITE_ENABLE?0:job.phase==4?(job.length-job.verified>128?128:job.length-job.verified):job.length;
 size=adapter_flash_request(&job.target,op,address,op==FLASH_PROGRAM?job.payload:NULL,length,tx,sizeof(tx));
 if(!size){finish(false,"invalid-request");return;}
 if(op==FLASH_ID)rxlen=3;else if(op==FLASH_STATUS)rxlen=1;else if(op==FLASH_READ)rxlen=length;
 int status=job.exchange(tx,size,rx,rxlen,job.context);
 if(status==0)return;
 if(status!=1){finish(false,"transport-failed");return;}
 if(job.phase==0){job.phase=1;return;}
 if(job.phase==1){if(!(rx[0]&2) || (rx[0]&1)){finish(false,"write-enable-rejected");return;}job.phase=2;return;}
 if(job.phase==2){
  if(job.op==FLASH_PROGRAM || job.op==FLASH_ERASE_SECTOR){job.phase=3;return;}
  memcpy(job.result,rx,rxlen);job.verified=rxlen;finish(true,"read-complete");return;
 }
 if(job.phase==3){if(rx[0]&1)return;job.phase=4;return;}
 if(job.phase==4){
  for(unsigned i=0;i<rxlen;++i)if(rx[i]!=(job.op==FLASH_PROGRAM?job.payload[job.verified+i]:0xFF)){finish(false,"readback-mismatch");return;}
  job.verified+=rxlen;
  if(job.verified==job.length)finish(true,"readback-verified");
 }
}
flash_engine_state adapter_flash_engine_state(void){return job.state;}
const char *adapter_flash_engine_result(void){return job.reason?job.reason:"idle";}
unsigned adapter_flash_engine_read(uint8_t *out,unsigned capacity){
 if(!out || job.state!=FLASH_ENGINE_DONE || job.phase!=2 || job.op==FLASH_PROGRAM || job.op==FLASH_ERASE_SECTOR)return 0;
 unsigned count=job.verified;if(count>capacity)count=capacity;memcpy(out,job.result,count);return count;
}
