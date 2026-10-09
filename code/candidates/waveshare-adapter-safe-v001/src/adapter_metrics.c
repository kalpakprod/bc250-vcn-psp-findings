#include "adapter_metrics.h"
#include <stdio.h>
#include <string.h>

typedef struct { int32_t value;uint32_t observed;bool valid; } measurement;
static measurement readings[5];
static uint32_t host_seen;
static bool host_observed;
static const char *names[]={"cpu_temp","gpu_temp","gpu_power","fan1_rpm","fan2_rpm"};
bool adapter_metric_update(const char *name,int32_t milli,uint32_t now) {
    for(unsigned i=0;i<5;++i) {
        if(strcmp(name,names[i]))continue;
        if(i<2 && (milli < -273150 || milli>1000000))return false;
        if(i>=2 && milli<0)return false;
        readings[i]=(measurement){milli,now,true};return true;
    }
    return false;
}
void adapter_metrics_json(char *out,unsigned capacity,uint32_t now) {
    char value[5][24];
    for(unsigned i=0;i<5;++i) {
        if(readings[i].valid && (uint32_t)(now-readings[i].observed)<=5000)
            snprintf(value[i],sizeof(value[i]),"%ld",(long)readings[i].value);
        else strcpy(value[i],"null");
    }
    snprintf(out,capacity,"{\"source\":\"linux_hwmon\",\"cpu_temp_milli_c\":%s,\"gpu_temp_milli_c\":%s,\"gpu_power_milli_w\":%s,\"fan1_rpm\":%s,\"fan2_rpm\":%s,\"freshness_limit_ms\":5000}",value[0],value[1],value[2],value[3],value[4]);
}
void adapter_host_alive(uint32_t now) { host_seen=now;host_observed=true; }
const char *adapter_host_power(uint32_t now) { return host_observed && (uint32_t)(now-host_seen)<=5000?"on":"unknown"; }
