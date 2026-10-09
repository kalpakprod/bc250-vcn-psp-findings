#include "adapter_smbus.h"
#include <string.h>
#include <stdio.h>
static adapter_smbus_frame_t q[ADAPTER_SMBUS_TRACE_MAX];static unsigned head,count;static uint32_t dropped;static bool enabled;
bool adapter_smbus_enable(bool v){if(!v)return false;enabled=true;return true;} void adapter_smbus_disable(void){enabled=false;head=count=dropped=0;memset(q,0,sizeof q);}
bool adapter_smbus_push(uint8_t a,const uint8_t*d,unsigned n,bool read,uint32_t t){if(!enabled||(!d&&n)||n>16)return false;if(count==ADAPTER_SMBUS_TRACE_MAX){head=(head+1)%ADAPTER_SMBUS_TRACE_MAX;count--;dropped++;}adapter_smbus_frame_t*f=&q[(head+count)%ADAPTER_SMBUS_TRACE_MAX];f->timestamp_us=t;f->address=a;f->flags=read?1:0;f->length=(uint8_t)n;if(n)memcpy(f->data,d,n);count++;return true;}
unsigned adapter_smbus_read(adapter_smbus_frame_t*out,unsigned cap){unsigned n=0;if(!out)return 0;while(n<cap&&count){out[n++]=q[head];head=(head+1)%ADAPTER_SMBUS_TRACE_MAX;count--;}return n;} void adapter_smbus_status_json(char*out,unsigned cap){snprintf(out,cap,"{\"enabled\":%s,\"mode\":\"passive\",\"available\":%u,\"dropped\":%lu}",enabled?"true":"false",count,(unsigned long)dropped);}
