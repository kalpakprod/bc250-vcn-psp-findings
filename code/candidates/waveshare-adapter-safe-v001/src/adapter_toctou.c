#include "adapter_toctou.h"
#include <stdio.h>
#include <string.h>

void adapter_toctou_init(adapter_toctou_t *e) { if (!e) return; memset(e,0,sizeof *e); e->config.trigger_mask=UINT32_MAX; e->config.window_words=1; e->state=ADAPTER_TOCTOU_IDLE; }
bool adapter_toctou_configure(adapter_toctou_t *e,const adapter_toctou_config_t *cfg) { if(!e||!cfg||e->state==ADAPTER_TOCTOU_ARMED||cfg->window_words==0) return false; e->config=*cfg; e->seen_words=0; e->matched_word=0; e->state=ADAPTER_TOCTOU_IDLE; return true; }
bool adapter_toctou_arm(adapter_toctou_t *e) { if(!e||e->state==ADAPTER_TOCTOU_ARMED||e->config.window_words==0) return false; e->seen_words=0; e->matched_word=0; e->state=ADAPTER_TOCTOU_ARMED; return true; }
bool adapter_toctou_feed(adapter_toctou_t *e,uint32_t word) { if(!e||e->state!=ADAPTER_TOCTOU_ARMED) return false; if(((word^e->config.trigger)&e->config.trigger_mask)==0){ e->matched_word=word; e->state=ADAPTER_TOCTOU_TRIGGERED; } if(++e->seen_words>=e->config.window_words && e->state==ADAPTER_TOCTOU_ARMED) e->state=ADAPTER_TOCTOU_COMPLETE; return e->state==ADAPTER_TOCTOU_TRIGGERED; }
void adapter_toctou_disarm(adapter_toctou_t *e) { if(!e) return; e->state=ADAPTER_TOCTOU_ABORTED; e->seen_words=0; e->matched_word=0; }
bool adapter_toctou_rollback(adapter_toctou_t *e) { if(!e) return false; e->state=ADAPTER_TOCTOU_IDLE; e->seen_words=0; e->matched_word=0; return true; }
adapter_toctou_state_t adapter_toctou_state(const adapter_toctou_t *e) { return e?e->state:ADAPTER_TOCTOU_ABORTED; }
size_t adapter_toctou_status_json(const adapter_toctou_t *e,char *out,size_t cap) { if(!out||!cap) return 0; const char *s="aborted"; if(e){switch(e->state){case ADAPTER_TOCTOU_IDLE:s="idle";break;case ADAPTER_TOCTOU_ARMED:s="armed";break;case ADAPTER_TOCTOU_TRIGGERED:s="triggered";break;case ADAPTER_TOCTOU_COMPLETE:s="complete";break;default:break;}} return (size_t)snprintf(out,cap,"{\"state\":\"%s\",\"trigger\":\"0x%08lX\",\"mask\":\"0x%08lX\",\"window\":%lu,\"seen\":%lu,\"order\":\"%s\"}",s,(unsigned long)(e?e->config.trigger:0),(unsigned long)(e?e->config.trigger_mask:0),(unsigned long)(e?e->config.window_words:0),(unsigned long)(e?e->seen_words:0),(e&&e->config.order==ADAPTER_TOCTOU_ORDER_LSB_FIRST)?"lsb":"msb"); }
