#include "cdc_dispatch.h"
#include "bridge/bridge.h"
#include "adapter_network.h"
#include "adapter_metrics.h"
#include "adapter_recorder.h"
#include "adapter_uart.h"
#include "adapter_spi_capture.h"
#include "adapter_flash_transport.h"
#include "adapter_flash_service.h"
#include "adapter_flash_frames.h"
#include "adapter_flash_engine.h"
#include "adapter_toctou.h"
#include "adapter_toctou_runtime.h"
#include "adapter_toctou_stage.h"
#include "rig/rig_payload.h"
#include "pico/sha256.h"
#include "hardware/pio.h"
#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include "pico/time.h"
#include "mode/mode.h"
#include "tusb.h"
#include <ctype.h>
#include <stdio.h>
#include <string.h>

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif
#ifndef BUILD_DATE
#define BUILD_DATE "unknown"
#endif
static char line[256];
static unsigned used;
static bool overflow;
static uint8_t config_frame[512];
static unsigned config_expected, config_received;
static uint32_t config_started;
static uint8_t *flash_frame;
static unsigned flash_kind,flash_expected,flash_received;
static uint32_t flash_started;
static adapter_toctou_t toctou;
static bool toctou_initialized;
static adapter_toctou_runtime_t toctou_runtime;
static bool toctou_runtime_initialized;
static adapter_toctou_stage_t rig_stage;
static void rig_stage_release(void) {
    rig_payload_clear();
    if (rig_stage.data) adapter_spi_capture_scratch_release();
    adapter_toctou_stage_clear(&rig_stage);
}
static adapter_toctou_t *toctou_state(void) {
    if (!toctou_initialized) { adapter_toctou_init(&toctou); toctou_initialized = true; }
    return &toctou;
}

static char pending[768];
static unsigned pending_size, pending_sent;
static void reply(const char *s) {
    const size_t size = strlen(s);
    if (size >= sizeof(pending)) return;
    memcpy(pending, s, size);
    pending_size = (unsigned)size;
    pending_sent = 0;
}
static void drain(void) {
    if (!pending_size) return;
    if (!tud_cdc_ready()) { pending_size = pending_sent = 0; return; }
    const unsigned sent = tud_cdc_write(pending + pending_sent, pending_size - pending_sent);
    pending_sent += sent;
    tud_cdc_write_flush();
    if (pending_sent == pending_size) pending_size = pending_sent = 0;
}
static void dispatch(void) {
    for (unsigned i = 0; i < used; ++i) line[i] = (char)toupper((unsigned char)line[i]);
    if (!strcmp(line,"UART_RX_ON VERIFIED_3V3")) reply(adapter_uart_enable(true)?"OK uart-rx-enabled\r\n":"ERR uart-unavailable\r\n");
    else if (!strcmp(line,"UART_RX_OFF")) { adapter_uart_disable();reply("OK uart-rx-disabled\r\n"); }
    else if (!strcmp(line,"UART_STATS")) { char data[128],out[160];adapter_uart_status_json(data,sizeof(data));snprintf(out,sizeof(out),"UART_STATE %s\r\nOK\r\n",data);reply(out); }
    else if (!strcmp(line,"UART_LOG")) { uint8_t bytes[128];char out[320];unsigned count=adapter_uart_read(bytes,sizeof(bytes));unsigned pos=(unsigned)snprintf(out,sizeof(out),"UART_DATA %u ",count);for(unsigned i=0;i<count;++i)pos+=(unsigned)snprintf(out+pos,sizeof(out)-pos,"%02X",bytes[i]);snprintf(out+pos,sizeof(out)-pos,"\r\nOK\r\n");reply(out); }
    else if(!strcmp(line,"FLASH_APPROVE") || !strcmp(line,"FLASH_STAGE")){
        if(mode_load()!=MODE_FLASH || adapter_flash_engine_state()==FLASH_ENGINE_RUNNING){reply("ERR flash-busy-or-unavailable\r\n");return;}
        flash_frame=adapter_spi_capture_scratch_take(FLASH_SECTOR_FRAME_SIZE);
        if(!flash_frame){reply("ERR flash-buffer-unavailable\r\n");return;}
        flash_kind=!strcmp(line,"FLASH_APPROVE")?1:2;
        flash_expected=flash_kind==1?FLASH_APPROVAL_FRAME_SIZE:FLASH_SECTOR_FRAME_SIZE;
        flash_received=0;flash_started=to_ms_since_boot(get_absolute_time());
        char out[48];snprintf(out,sizeof(out),"FLASH_READY %u\r\n",flash_expected);reply(out);
    }
    else if(!strncmp(line,"FLASH_ERASE ",12) || !strncmp(line,"FLASH_PROGRAM ",14)){
        bool erase=!strncmp(line,"FLASH_ERASE ",12);char *value=line+(erase?12:14),*end;errno=0;unsigned long address=strtoul(value,&end,16);
        if(errno || !*value || *end || *value=='-' || address>0xFFFFFF){reply("ERR flash-format\r\n");return;}
        reply(adapter_flash_service_commit(erase,(uint32_t)address)?"OK flash-writing\r\n":"ERR flash-unavailable\r\n");
    }
    else if(!strcmp(line,"FLASH_OPEN VERIFIED_3V3 BUS_ISOLATED"))reply(adapter_flash_service_open(true,true)?"OK flash-identifying\r\n":"ERR flash-unavailable\r\n");
    else if(!strcmp(line,"FLASH_CLOSE")){adapter_flash_service_close();reply("OK flash-closed\r\n");}
    else if(!strcmp(line,"FLASH_STATS")){char data[320],out[368];adapter_flash_service_status(data,sizeof(data));snprintf(out,sizeof(out),"FLASH_STATE %s\r\nOK\r\n",data);reply(out);}
    else if(!strncmp(line,"FLASH_READ ",11)){
        char *address=line+11,*sep=strchr(address,' '),*end;unsigned long a,n;
        if(!sep){reply("ERR flash-format\r\n");return;}*sep++=0;errno=0;a=strtoul(address,&end,16);
        if(errno || !*address || *end || *address=='-' || a>0xFFFFFF){reply("ERR flash-format\r\n");return;}
        errno=0;n=strtoul(sep,&end,10);
        if(errno || !*sep || *end || *sep=='-' || !n || n>128){reply("ERR flash-format\r\n");return;}
        reply(adapter_flash_service_read((uint32_t)a,(unsigned)n)?"OK flash-reading\r\n":"ERR flash-unavailable\r\n");
    }
    else if(!strcmp(line,"FLASH_DATA")){uint8_t data[128];char out[300];unsigned n=adapter_flash_service_data(data,sizeof(data));unsigned pos=(unsigned)snprintf(out,sizeof(out),"FLASH_DATA %u ",n);for(unsigned i=0;i<n;++i)pos+=(unsigned)snprintf(out+pos,sizeof(out)-pos,"%02X",data[i]);snprintf(out+pos,sizeof(out)-pos,"\r\nOK\r\n");reply(out);}
    else if(!strcmp(line,"SPI_TRACE_ON VERIFIED_3V3"))reply(adapter_spi_capture_start(true)?"OK spi-trace-started\r\n":"ERR spi-trace-unavailable\r\n");
    else if(!strcmp(line,"SPI_TRACE_OFF")){adapter_spi_capture_stop();reply("OK spi-trace-stopped\r\n");}
    else if(!strcmp(line,"SPI_STATS")){char data[240],out[280];adapter_spi_capture_status(data,sizeof(data));snprintf(out,sizeof(out),"SPI_STATE %s\r\nOK\r\n",data);reply(out);}
    else if(!strcmp(line,"SPI_TRACE_READ")){uint32_t words[32];char out[320];unsigned count=adapter_spi_capture_read(words,32);unsigned pos=(unsigned)snprintf(out,sizeof(out),"SPI_DATA %u ",count);for(unsigned i=0;i<count;++i)pos+=(unsigned)snprintf(out+pos,sizeof(out)-pos,"%08lX",(unsigned long)words[i]);snprintf(out+pos,sizeof(out)-pos,"\r\nOK\r\n");reply(out);}
    else if(!strncmp(line,"TOCTOU_CONFIG ",15)) {
        unsigned long trigger,mask,window; char order[8];
        if (sscanf(line+15,"%lx %lx %lu %7s",&trigger,&mask,&window,order)!=4 || trigger>0xFFFFFFFFUL || mask>0xFFFFFFFFUL || !window || window>0x100000UL) { reply("ERR toctou-format\r\n"); return; }
        adapter_toctou_config_t cfg={(uint32_t)trigger,(uint32_t)mask,(uint32_t)window,
            !strcmp(order,"LSB") ? ADAPTER_TOCTOU_ORDER_LSB_FIRST : ADAPTER_TOCTOU_ORDER_MSB_FIRST};
        reply(mode_load()==MODE_TOCTOU && adapter_toctou_configure(toctou_state(),&cfg) ? "OK toctou-configured\r\n" : "ERR toctou-unavailable\r\n");
    }
    else if(!strcmp(line,"TOCTOU_ARM")) {
        adapter_toctou_t *e=toctou_state();
        if (mode_load()!=MODE_TOCTOU || !adapter_toctou_arm(e)) { reply("ERR toctou-unavailable\r\n"); return; }
        if (!toctou_runtime_initialized) toctou_runtime_initialized=adapter_toctou_runtime_init(&toctou_runtime,pio0);
        adapter_toctou_runtime_config_t cfg={e->config.trigger,e->config.window_words};
        if (!toctou_runtime_initialized || !adapter_toctou_runtime_configure_arm(&toctou_runtime,&cfg)) { adapter_toctou_disarm(e); reply("ERR toctou-wiring-not-confirmed\r\n"); return; }
        reply("OK toctou-armed\r\n");
    }
    else if(!strcmp(line,"TOCTOU_DISARM")) { adapter_toctou_runtime_disarm(&toctou_runtime); adapter_toctou_disarm(toctou_state()); reply("OK toctou-disarmed\r\n"); }
    else if(!strcmp(line,"TOCTOU_STATUS")) { char data[256],out[300]; adapter_toctou_status_json(toctou_state(),data,sizeof(data)); snprintf(out,sizeof(out),"TOCTOU_STATE %s\r\nOK\r\n",data); reply(out); }
    else if (!strncmp(line, "RIG_BEGIN ", 10)) {
        rig_stage_release();
        if (mode_load() != MODE_FLASH) { reply("ERR rig-staging-requires-flash-mode\r\n"); return; }
        char *value = line + 10, *end;
        errno = 0; unsigned long address = strtoul(value, &end, 16);
        if (errno || !isxdigit((unsigned char)*value) || *end != ' ' || address > 0xFFFFFFUL) {
            reply("ERR rig-begin-format\r\n"); return;
        }
        value = end + 1; errno = 0; unsigned long length = strtoul(value, &end, 10);
        if (errno || !isdigit((unsigned char)*value) || *end != ' ' || !length || length > TOCTOU_STAGE_CAPACITY) {
            reply("ERR rig-begin-format\r\n"); return;
        }
        const char *digest = end + 1;
        uint8_t *buffer = adapter_spi_capture_scratch_take(TOCTOU_STAGE_CAPACITY);
        if (!buffer) { reply("ERR rig-buffer-busy\r\n"); return; }
        if (!adapter_toctou_stage_begin(&rig_stage, (uint32_t)address, (uint32_t)length, digest, buffer)) {
            adapter_spi_capture_scratch_release(); reply("ERR rig-begin-format\r\n"); return;
        }
        reply("OK rig-staging\r\n");
    }
    else if (!strncmp(line, "RIG_LOAD ", 9)) {
        char *end; errno = 0; unsigned long offset = strtoul(line + 9, &end, 16);
        bool valid = !errno && end != line + 9 && *end == ' ' && offset <= TOCTOU_STAGE_CAPACITY;
        reply(valid && adapter_toctou_stage_load(&rig_stage, (uint32_t)offset, end + 1) ? "OK rig-loaded\r\n" : "ERR rig-load-format\r\n");
    }
    else if (!strcmp(line, "RIG_COMMIT")) {
        if (!rig_stage.active || rig_stage.received != rig_stage.length) { reply("ERR rig-incomplete\r\n"); return; }
        pico_sha256_state_t hash; sha256_result_t digest;
        if (pico_sha256_try_start(&hash, SHA256_BIG_ENDIAN, false) != PICO_OK) { reply("ERR rig-hash-busy\r\n"); return; }
        pico_sha256_update_blocking(&hash, rig_stage.data, rig_stage.length);
        pico_sha256_finish(&hash, &digest);
        bool verified = adapter_toctou_stage_commit(&rig_stage, digest.bytes);
        if (!verified) rig_stage_release();
        reply(verified ? "OK rig-verified\r\n" : "ERR rig-digest\r\n");
    }
    else if (!strncmp(line, "RIG_PREPARE ", 12)) {
        char *value = line + 12, *end;
        errno = 0; unsigned long index = strtoul(value, &end, 10);
        if (errno || !isdigit((unsigned char)*value) || *end || index > UINT32_MAX) {
            rig_payload_clear(); reply("ERR rig-index-format\r\n"); return;
        }
        reply(rig_payload_prepare(&rig_stage, (uint32_t)index) ? "OK rig-prepared-hardware-blocked\r\n" : "ERR rig-unverified-window\r\n");
    }
    else if (!strcmp(line, "RIG_CLEAR")) { rig_stage_release(); reply("OK rig-cleared\r\n"); }
    else if (!strcmp(line, "RIG_STATUS")) {
        char out[220];
        const rig_payload_t *payload = rig_payload_current();
        snprintf(out, sizeof(out), "RIG_STATE active=%u verified=%u prepared=%u read_index=%lu address=%06lX length=%lu received=%lu hardware=blocked\r\nOK\r\n", rig_stage.active ? 1u : 0u, rig_stage.verified ? 1u : 0u, payload ? 1u : 0u, (unsigned long)(payload ? payload->read_index : 0), (unsigned long)rig_stage.address, (unsigned long)rig_stage.length, (unsigned long)rig_stage.received); reply(out);
    }
    else if (!strcmp(line, "RIG_INIT") || !strncmp(line, "RIG_ARM", 7)) reply("ERR rig-hardware-unverified\r\n");
    else if (!strcmp(line,"RECORDER_STATUS")) {
        char data[320], out[352];
        adapter_recorder_json(adapter_recorder_instance(), data, sizeof(data),
                              to_us_since_boot(get_absolute_time()) / 1000);
        snprintf(out, sizeof(out), "RECORDER_STATE %s\r\nOK\r\n", data);
        reply(out);
    }
    else if (!strncmp(line,"RECORDER_READ ",14)) {
        char *value=line+14, *end; errno=0;
        unsigned long cursor=strtoul(value,&end,10);
        if(errno || !*value || *end || *value=='-' || cursor>UINT32_MAX) {
            reply("ERR recorder-cursor\r\n"); return;
        }
        char data[640], out[672];
        if(!adapter_recorder_events_json(adapter_recorder_instance(),
                                          (uint32_t)cursor,data,sizeof(data))) {
            reply("ERR recorder-buffer\r\n"); return;
        }
        snprintf(out,sizeof(out),"RECORDER_DATA %s\r\nOK\r\n",data);
        reply(out);
    }
    else if (!strcmp(line,"HOST_ALIVE")) {
        adapter_host_alive(to_ms_since_boot(get_absolute_time()));
        adapter_recorder_heartbeat_update(adapter_recorder_instance(),
            ADAPTER_RECORDER_HOST_HEARTBEAT, to_us_since_boot(get_absolute_time()) / 1000);
        reply("OK\r\n");
    }
    else if (!strncmp(line,"METRIC ",7)) {
        char *value=strchr(line+7,' ');
        if(!value){reply("ERR metric-format\r\n");return;}
        *value++=0;errno=0;char *end;long milli=strtol(value,&end,10);
        const char *name=!strcmp(line+7,"CPU_TEMP")?"cpu_temp":!strcmp(line+7,"GPU_TEMP")?"gpu_temp":!strcmp(line+7,"GPU_POWER")?"gpu_power":!strcmp(line+7,"FAN1_RPM")?"fan1_rpm":!strcmp(line+7,"FAN2_RPM")?"fan2_rpm":"unsupported";
        if(errno || !*value || *end || milli<INT32_MIN || milli>INT32_MAX || !adapter_metric_update(name,(int32_t)milli,to_ms_since_boot(get_absolute_time()))) reply("ERR metric-invalid\r\n");
        else reply("OK\r\n");
    }
    else if (!strcmp(line, "NETCFG")) {
        adapter_network_discard();
        config_expected = adapter_network_frame_size(); config_received = 0;
        if (config_expected>sizeof(config_frame)) { config_expected=0;reply("ERR frame-size\r\n");return; }
        config_started = to_ms_since_boot(get_absolute_time());
        char out[64]; snprintf(out,sizeof(out),"READY %u\r\n",config_expected);reply(out);
    } else if (!strcmp(line,"NETCFG_COMMIT")) reply(adapter_network_commit()?"OK saved-reset-required\r\n":"ERR config-not-saved\r\n");
    else if (!strcmp(line, "PING")) reply("OK\r\n");
    else if (!strcmp(line, "VERSION")) {
        char out[160];
        snprintf(out, sizeof(out), "VERSION %s %s MODE %s\r\nOK\r\n", GIT_HASH, BUILD_DATE, mode_name(mode_load()));
        reply(out);
    } else if (!strcmp(line, "STATUS")) {
        static char data[640], out[720];
        bridge_status_json(data, sizeof(data));
        snprintf(out, sizeof(out), "STATE mode=%s\r\nDATA %s\r\nOK\r\n", mode_name(mode_load()), data);
        reply(out);
    } else if (!strcmp(line, "HELP")) reply("Commands: PING VERSION STATUS HELP RECORDER_STATUS RECORDER_READ cursor MODE controller/monitor/flash/diagnostic/recovery UART_STATS UART_LOG UART_RX_OFF; UART_RX_ON requires VERIFIED_3V3 operator confirmation; NETCFG and metrics use host helpers\r\nOK\r\n");
    else if (!strncmp(line, "MODE ", 5)) {
        pico_bc250_mode_t next;
        if (!strcmp(line,"MODE CONTROLLER")) next=MODE_CONTROLLER;
        else if (!strcmp(line,"MODE MONITOR")) next=MODE_MONITOR;
        else if (!strcmp(line,"MODE FLASH")) next=MODE_FLASH;
        else if (!strcmp(line,"MODE DIAGNOSTIC")) next=MODE_DIAGNOSTIC;
        else if (!strcmp(line,"MODE RECOVERY")) next=MODE_RECOVERY;
        else { reply("ERR mode-unavailable\r\n"); return; }
        if (next != mode_load()) { adapter_uart_disable(); adapter_spi_capture_stop(); adapter_flash_service_close(); rig_stage_release(); }
        mode_select(next);
        char out[80];snprintf(out,sizeof(out),"STATE mode=%s\r\nOK\r\n",mode_name(mode_load()));reply(out);
    }
    else reply("ERR unsupported-command\r\n");
}
void cdc_dispatch_tick(void) {
    if (!tud_cdc_ready() || mode_load() != MODE_FLASH) rig_stage_release();
    adapter_toctou_runtime_tick(&toctou_runtime);
    if(flash_expected && (!tud_cdc_ready() || (uint32_t)(to_ms_since_boot(get_absolute_time())-flash_started)>3000)){
        adapter_spi_capture_scratch_release();flash_frame=NULL;flash_kind=flash_expected=flash_received=0;
        adapter_flash_service_close();reply("ERR flash-frame-timeout\r\n");
    }
    if (config_expected && (uint32_t)(to_ms_since_boot(get_absolute_time())-config_started)>3000) {
        adapter_network_discard();
        memset(config_frame,0,sizeof(config_frame)); config_expected=config_received=0;
        reply("ERR config-timeout\r\n");
    }
    drain();
    while (!pending_size && tud_cdc_available()) {
        char ch;
        if (tud_cdc_read(&ch, 1) != 1) break;
        if(flash_expected){
            flash_frame[flash_received++]=(uint8_t)ch;
            if(flash_received==flash_expected){
                bool applied=adapter_flash_frame_apply(flash_kind,flash_frame,flash_expected);
                if(!applied)adapter_flash_service_close();
                reply(applied?"OK flash-frame-accepted\r\n":"ERR flash-frame-invalid\r\n");
                adapter_spi_capture_scratch_release();flash_frame=NULL;flash_kind=flash_expected=flash_received=0;
            }
            continue;
        }
        if (config_expected) {
            config_frame[config_received++] = (uint8_t)ch;
            if (config_received == config_expected) {
                reply(adapter_network_stage(config_frame,config_received)?"OK staged\r\n":"ERR config-invalid\r\n");
                memset(config_frame,0,sizeof(config_frame));config_expected=config_received=0;
            }
            continue;
        }
        if (ch == '\r' || ch == '\n') {
            if (overflow) reply("ERR line-too-long\r\n");
            else if (used) { line[used] = 0; dispatch(); }
            used = 0;
            overflow = false;
        } else if (used < sizeof(line) - 1) line[used++] = ch;
        else overflow = true;
    }
}
