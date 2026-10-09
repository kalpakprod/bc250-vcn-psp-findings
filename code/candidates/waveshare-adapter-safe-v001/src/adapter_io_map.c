#include "adapter_io_map.h"
#include <string.h>
#include <stdio.h>
#define MAX_PINS 16
static adapter_pin_info_t pins[MAX_PINS];
void adapter_io_map_reset(void){memset(pins,0,sizeof pins);}
bool adapter_io_map_set_input(const char*n,int p,bool v){if(!n||!v||p<0)return false;for(unsigned i=0;i<MAX_PINS;i++)if(pins[i].name&&!strcmp(pins[i].name,n)){if(pins[i].direction==ADAPTER_PIN_OUTPUT)return false;pins[i]=(adapter_pin_info_t){n,p,ADAPTER_PIN_INPUT,true};return true;}for(unsigned i=0;i<MAX_PINS;i++)if(!pins[i].name){pins[i]=(adapter_pin_info_t){n,p,ADAPTER_PIN_INPUT,true};return true;}return false;}
bool adapter_io_map_get(const char*n,adapter_pin_info_t*out){if(!n||!out)return false;for(unsigned i=0;i<MAX_PINS;i++)if(pins[i].name&&!strcmp(pins[i].name,n)){*out=pins[i];return true;}return false;}
void adapter_io_map_status_json(char*out,unsigned cap){unsigned p=0,n=0;p+=(unsigned)snprintf(out+p,p<cap?cap-p:0,"{\"safe_default\":\"input\",\"pins\":[");for(unsigned i=0;i<MAX_PINS;i++)if(pins[i].name){p+=(unsigned)snprintf(out+p,p<cap?cap-p:0,"%s{\"name\":\"%s\",\"pin\":%d,\"direction\":\"input\",\"verified\":true}",n++?",":"",pins[i].name,pins[i].pin);}snprintf(out+p,p<cap?cap-p:0,"]}");}
