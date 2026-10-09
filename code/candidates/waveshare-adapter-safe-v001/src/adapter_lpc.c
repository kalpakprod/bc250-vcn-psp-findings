#include "adapter_lpc.h"
#include <string.h>
#include <stdio.h>
static adapter_lpc_sample_t q[ADAPTER_LPC_TRACE_MAX]; static unsigned head,count; static uint32_t dropped; static bool enabled;
bool adapter_lpc_enable(bool v){if(!v)return false; enabled=true; return true;}
void adapter_lpc_disable(void){enabled=false;head=count=dropped=0;memset(q,0,sizeof q);}
bool adapter_lpc_push(uint8_t v,uint32_t t){if(!enabled)return false;if(count==ADAPTER_LPC_TRACE_MAX){head=(head+1)%ADAPTER_LPC_TRACE_MAX;count--;dropped++;}q[(head+count)%ADAPTER_LPC_TRACE_MAX]=(adapter_lpc_sample_t){t,v};count++;return true;}
unsigned adapter_lpc_read(adapter_lpc_sample_t*out,unsigned cap){unsigned n=0;if(!out)return 0;while(n<cap&&count){out[n++]=q[head];head=(head+1)%ADAPTER_LPC_TRACE_MAX;count--;}return n;}
void adapter_lpc_status_json(char*out,unsigned cap){snprintf(out,cap,"{\"enabled\":%s,\"mode\":\"passive\",\"available\":%u,\"dropped\":%lu}",enabled?"true":"false",count,(unsigned long)dropped);}
