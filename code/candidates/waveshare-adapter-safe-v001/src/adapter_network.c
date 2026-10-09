#include "adapter_network.h"
#include "adapter_recorder.h"
#include "network_config.h"
#include "network_panel.h"
#include "bridge/bridge.h"
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "pico/flash.h"
#include "hardware/flash.h"
#include "pico/btstack_flash_bank.h"
#include "lwip/tcp.h"
#include "lwip/apps/mqtt.h"
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(sizeof(ADAPTER_PANEL_HTML)>768 && sizeof(ADAPTER_PANEL_HTML)+256<=TCP_SND_BUF,"panel exceeds bounded HTTP send window");
_Static_assert(sizeof(adapter_net_config_t)<=512,"network record exceeds two pages");
_Static_assert(ADAPTER_NET_OFFSET+FLASH_SECTOR_SIZE<=PICO_FLASH_BANK_STORAGE_OFFSET,"network overlaps BT keys");
static adapter_net_config_t active, staged;
static bool provisioned, staged_valid, mqtt_online, mqtt_connecting;
static mqtt_client_t *client;
static uint32_t wifi_retry, mqtt_retry, publish_at;
static char history[60][640];
static uint32_t history_observed[60];
static unsigned history_head,history_count;
/* Do not start the radio until a complete, validated record is present. */
static const char *state="disabled";

const char *adapter_network_state(void) { return state; }
bool adapter_mqtt_connected(void) { return mqtt_online; }
unsigned adapter_network_frame_size(void) { return sizeof(adapter_net_config_t); }

void adapter_network_discard(void) { staged_valid=false;memset(&staged,0,sizeof(staged)); }

bool adapter_network_stage(const uint8_t *frame, unsigned length) {
    staged_valid=false;memset(&staged,0,sizeof(staged));
    adapter_net_config_t candidate;
    if (length != sizeof(candidate)) return false;
    memcpy(&candidate,frame,sizeof(candidate));
    if (!adapter_net_valid(&candidate)) return false;
    ip_addr_t addr;
    if (candidate.broker[0]) {
        if (!ipaddr_aton(candidate.broker,&addr)) return false;
        const unsigned first=ip4_addr1(ip_2_ip4(&addr)),second=ip4_addr2(ip_2_ip4(&addr));
        if (!(first==10 || (first==172 && second>=16 && second<=31) || (first==192 && second==168))) return false;
    }
    memcpy(&staged,&candidate,sizeof(staged));staged_valid=true;
    return true;
}
static void write_config(void *arg) {
    uint8_t bytes[512];memset(bytes,0xff,sizeof(bytes));memcpy(bytes,arg,sizeof(adapter_net_config_t));
    flash_range_erase(ADAPTER_NET_OFFSET,FLASH_SECTOR_SIZE);
    flash_range_program(ADAPTER_NET_OFFSET,bytes,sizeof(bytes));
}
bool adapter_network_commit(void) {
    if (!staged_valid) return false;
    extern char __flash_binary_end;
    if ((uintptr_t)&__flash_binary_end-XIP_BASE>ADAPTER_NET_OFFSET) return false;
    if (flash_safe_execute(write_config,&staged,500)!=PICO_OK) return false;
    const bool equal=memcmp((const void *)(XIP_BASE+ADAPTER_NET_OFFSET),&staged,sizeof(staged))==0;
    staged_valid=false;
    memset(&staged,0,sizeof(staged));
    return equal;
}

// One bounded request/response per connection. Only authenticated read access.
typedef struct { char request[1024];uint16_t used;bool responded; } http_session;
static unsigned http_connections;
static void http_error(void *arg,err_t error) { (void)error;free(arg);if(http_connections)--http_connections; }
static err_t http_free(struct tcp_pcb *pcb,http_session *s) {
    tcp_arg(pcb,NULL);tcp_recv(pcb,NULL);tcp_err(pcb,NULL);tcp_sent(pcb,NULL);tcp_poll(pcb,NULL,0);
    free(s);if(http_connections)--http_connections;
    if (tcp_close(pcb)!=ERR_OK) { tcp_abort(pcb);return ERR_ABRT; }
    return ERR_OK;
}
static bool token_ok(const char *request, size_t received) {
    return adapter_http_token_ok(request, received, active.web_token);
}
static bool request_is(const char *request, const char *prefix) {
    return strncmp(request,prefix,strlen(prefix))==0;
}
static void config_json(char *out, size_t capacity) {
    /* Deliberately expose shape and operational flags only.  Credentials and
       even their lengths are not returned over the network. */
    snprintf(out,capacity,
        "{\"provisioned\":%s,\"wifi_enabled\":%s,\"broker_configured\":%s,\"mqtt_connected\":%s,\"port\":%u}",
        provisioned?"true":"false", provisioned?"true":"false",
        (provisioned && active.broker[0])?"true":"false", mqtt_online?"true":"false",
        provisioned?(unsigned)active.port:0u);
}
static void log_json(char *out, size_t capacity) {
    size_t used=0;
    /* Keep the response within the single bounded HTTP send window. */
    const unsigned count=history_count>2?2:history_count;
    const unsigned first=history_count>count?(history_head+history_count-count)%60:history_head;
    int n=snprintf(out,capacity,"{\"count\":%u,\"entries\":[",count);
    if(n<0 || (size_t)n>=capacity)return;
    used=(size_t)n;
    for(unsigned i=0;i<count;++i) {
        const unsigned index=(first+i)%60;
        const size_t len=strlen(history[index]);
        n=snprintf(out+used,capacity-used,"%s%.*s",i?",":"",(int)len,history[index]);
        if(n<0 || (size_t)n>=capacity-used){ snprintf(out,capacity,"{\"error\":\"log_too_large\"}"); return; }
        used+=(size_t)n;
    }
    snprintf(out+used,capacity-used,"]}");
}
static err_t http_sent(void *arg,struct tcp_pcb *pcb,u16_t length) {
    (void)length;
    if (tcp_sndqueuelen(pcb)==0) return http_free(pcb,arg);
    return ERR_OK;
}
static err_t http_poll(void *arg,struct tcp_pcb *pcb) { return http_free(pcb,arg); }
static err_t http_receive(void *arg,struct tcp_pcb *pcb,struct pbuf *p,err_t error) {
    http_session *s=arg;
    if (error!=ERR_OK) { if(p)pbuf_free(p);return http_free(pcb,s); }
    if (!p) { return http_free(pcb,s); }
    tcp_recved(pcb,p->tot_len);
    if (s->responded || s->used+p->tot_len>=sizeof(s->request)) {pbuf_free(p);return http_free(pcb,s);}
    pbuf_copy_partial(p,s->request+s->used,p->tot_len,0);s->used+=p->tot_len;pbuf_free(p);s->request[s->used]=0;
    if (!strstr(s->request,"\r\n\r\n"))return ERR_OK;
    static char body[sizeof(ADAPTER_PANEL_HTML)],response[sizeof(ADAPTER_PANEL_HTML)+256];const char *code="200 OK",*type="application/json";
    if (request_is(s->request,"GET /api/status HTTP/1.")) {
        if(token_ok(s->request,s->used))bridge_status_json(body,sizeof(body));
        else {code="401 Unauthorized";strcpy(body,"{\"error\":\"authorization_required\"}");}
    } else if (request_is(s->request,"GET /api/recorder HTTP/1.")) {
        if(token_ok(s->request,s->used))
            adapter_recorder_json(adapter_recorder_instance(),body,sizeof(body),
                                  to_us_since_boot(get_absolute_time()) / 1000);
        else {code="401 Unauthorized";strcpy(body,"{\"error\":\"authorization_required\"}");}
    } else if (request_is(s->request,"GET /api/recorder?cursor=")) {
        if(!token_ok(s->request,s->used)) {code="401 Unauthorized";strcpy(body,"{\"error\":\"authorization_required\"}");}
        else {
            const char *value=s->request+25;char *end;errno=0;
            unsigned long cursor=strtoul(value,&end,10);
            if(errno || *value<'0' || *value>'9' || cursor>UINT32_MAX ||
               strncmp(end," HTTP/1.",8)!=0) {
                code="400 Bad Request";strcpy(body,"{\"error\":\"invalid_cursor\"}");
            } else if(!adapter_recorder_events_json(adapter_recorder_instance(),
                                                    (uint32_t)cursor,body,sizeof(body))) {
                code="500 Internal Server Error";strcpy(body,"{\"error\":\"recorder_buffer\"}");
            }
        }
    } else if (request_is(s->request,"GET /api/config HTTP/1.")) {
        if(token_ok(s->request,s->used))config_json(body,sizeof(body));
        else {code="401 Unauthorized";strcpy(body,"{\"error\":\"authorization_required\"}");}
    } else if (request_is(s->request,"GET /api/log HTTP/1.")) {
        if(token_ok(s->request,s->used))log_json(body,sizeof(body));
        else {code="401 Unauthorized";strcpy(body,"{\"error\":\"authorization_required\"}");}
    } else if (request_is(s->request,"GET / HTTP/1.")) {
        type="text/html; charset=utf-8";
        memcpy(body,ADAPTER_PANEL_HTML,sizeof(ADAPTER_PANEL_HTML));
    } else {code="404 Not Found";strcpy(body,"{\"error\":\"not_found\"}");}
    const int length=snprintf(response,sizeof(response),"HTTP/1.1 %s\r\nContent-Type: %s\r\nContent-Length: %u\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n\r\n%s",code,type,(unsigned)strlen(body),body);
    if (length<=0 || (unsigned)length>=sizeof(response) || tcp_write(pcb,response,(u16_t)length,TCP_WRITE_FLAG_COPY)!=ERR_OK) {return http_free(pcb,s);}
    s->responded=true;tcp_sent(pcb,http_sent);tcp_output(pcb);return ERR_OK;
}
static err_t http_accept(void *arg,struct tcp_pcb *pcb,err_t error) {
    (void)arg;
    if (error!=ERR_OK)return error;
    // Reserve the other TCP PCB for MQTT; reject extra web sessions rather than starving it.
    if(http_connections>=1){tcp_abort(pcb);return ERR_ABRT;}
    http_session *s=calloc(1,sizeof(*s));
    if(!s){tcp_abort(pcb);return ERR_ABRT;}
    ++http_connections;tcp_arg(pcb,s);tcp_recv(pcb,http_receive);tcp_err(pcb,http_error);tcp_poll(pcb,http_poll,10);return ERR_OK;
}
static void mqtt_connection(mqtt_client_t *c,void *arg,mqtt_connection_status_t status) {
    (void)c;(void)arg;mqtt_connecting=false;mqtt_online=status==MQTT_CONNECT_ACCEPTED;
}
void adapter_network_init(void) {
    memcpy(&active,(const void *)(XIP_BASE+ADAPTER_NET_OFFSET),sizeof(active));
    provisioned=adapter_net_valid(&active);
    if(!provisioned){memset(&active,0,sizeof(active));state="disabled";return;}
    cyw43_arch_enable_sta_mode();state="connecting";
    struct tcp_pcb *pcb=tcp_new_ip_type(IPADDR_TYPE_V4);
    if(pcb && tcp_bind(pcb,IP_ANY_TYPE,80)==ERR_OK){struct tcp_pcb *listener=tcp_listen_with_backlog(pcb,2);if(listener)tcp_accept(listener,http_accept);else tcp_abort(pcb);}
    else if(pcb)tcp_abort(pcb);
    client=mqtt_client_new();
}
void adapter_network_tick(void) {
    if(!provisioned)return;
    const uint32_t now=to_ms_since_boot(get_absolute_time());
    const int status=cyw43_tcpip_link_status(&cyw43_state,CYW43_ITF_STA);
    if(status!=CYW43_LINK_UP) {
        state="connecting";mqtt_online=false;
        if ((int32_t)(now-wifi_retry)>=0) { wifi_retry=now+30000;cyw43_arch_wifi_connect_async(active.ssid,active.psk,CYW43_AUTH_WPA2_AES_PSK); }
        return;
    }
    state="connected";
    if(!client || !active.broker[0])return;
    if(!mqtt_online && !mqtt_connecting && (int32_t)(now-mqtt_retry)>=0) {
        mqtt_retry=now+10000;ip_addr_t ip;
        if(ipaddr_aton(active.broker,&ip)) {
            struct mqtt_connect_client_info_t info={0};
            info.client_id="bc250-waveshare";info.keep_alive=30;
            info.client_user=active.mqtt_user[0]?active.mqtt_user:NULL;
            info.client_pass=active.mqtt_password[0]?active.mqtt_password:NULL;
            mqtt_connecting=mqtt_client_connect(client,&ip,active.port,mqtt_connection,NULL,&info)==ERR_OK;
        }
    }
    if ((int32_t)(now-publish_at)>=0) {
        publish_at=now+500;
        const unsigned index=(history_head+history_count)%60;
        bridge_status_json(history[index],sizeof(history[index]));
        history_observed[index]=now;
        if(history_count<60)++history_count;else history_head=(history_head+1)%60;
    }
    if(mqtt_online && history_count) {
        // One bounded publish per tick. History preserves original uptime.
        const uint32_t age=(uint32_t)(now-history_observed[history_head]);
        char payload[720];
        const size_t size=strlen(history[history_head]);
        if (!size || history[history_head][size-1]!='}') { history_head=(history_head+1)%60;--history_count;return; }
        const int length=snprintf(payload,sizeof(payload),"%.*s,\"age_ms\":%lu,\"historical\":%s}",
            (int)(size-1),history[history_head],(unsigned long)age,age>1000?"true":"false");
        if(length<=0 || (unsigned)length>=sizeof(payload)) { history_head=(history_head+1)%60;--history_count;return; }
        const err_t result=mqtt_publish(client,"bc250/wv/status",payload,(u16_t)length,0,0,NULL,NULL);
        if(result==ERR_OK){history_head=(history_head+1)%60;--history_count;}
    }
}
