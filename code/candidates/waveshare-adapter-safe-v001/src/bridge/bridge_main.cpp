//
// Ported from DS5Dongle-WoL main.cpp (awalol, 2026/3/4).
// Split into bridge_init / bridge_tick / bridge_shutdown so it can be
// composed with rig code under a shared mode switcher.
//

#include "bridge.h"
#include "usb_identity_gate.h"
#include "adapter_network.h"
#include "adapter_metrics.h"
#include "adapter_uart.h"
#include "../adapter_startup.h"
#include "mode/mode.h"
#include "ps_event_gate.h"
#include "pico/rand.h"

#include <cstdio>
#include <cstring>

#include "bsp/board_api.h"
#include "bt.h"
#include "button_functions.h"
#include "utils.h"
#include "resample.h"
#include "audio.h"
#include "wake.h"
#ifdef ENABLE_WAKE_HID
#include "ps_shortcut.h"
#endif
#include "hardware/clocks.h"
#include "hardware/vreg.h"
#include "hardware/watchdog.h"
#include "pico/cyw43_arch.h"
#include "state_mgr.h"
#include "config.h"
#include "cmd.h"
#include "dse.h"
#if ENABLE_BATT_LED
#include "battery_led.h"
#endif
#ifdef ENABLE_WOL
#include "wol.h"
#endif

#include "pico/critical_section.h"
#include "tusb.h"

int reportSeqCounter = 0;
uint8_t packetCounter = 0;
bool spk_active = false;

uint8_t interrupt_in_data[63] = {
    0x7f, 0x7d, 0x7f, 0x7e, 0x00, 0x00, 0xa7,
    0x08, 0x00, 0x00, 0x00, 0x52, 0x43, 0x30, 0x41,
    0x01, 0x00, 0x0e, 0x00, 0xef, 0xff, 0x03, 0x03,
    0x7b, 0x1b, 0x18, 0xf0, 0xcc, 0x9c, 0x60, 0x00,
    0xfc, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00,
    0x00, 0x00, 0x09, 0x09, 0x00, 0x00, 0x00, 0x00,
    0x00, 0xa7, 0xad, 0x60, 0x00, 0x29, 0x18, 0x00,
    0x53, 0x9f, 0x28, 0x35, 0xa5, 0xa8, 0x0c, 0x8b
};

critical_section_t report_cs;
volatile bool report_dirty = false;
static uint32_t input_generation;

void __not_in_flash_func(interrupt_loop)() {
    if (!mode_controller_active() || input_generation != mode_generation() || !tud_hid_ready()) return;

    if (get_config().polling_rate_mode != 2) {
        if (!tud_hid_report(0x01, interrupt_in_data, 63)) {
            printf("[USBHID] tud_hid_report error\n");
        }
        return;
    }

    bool should_send = false;
    uint8_t safe_report[63];

    critical_section_enter_blocking(&report_cs);
    if (report_dirty) {
        memcpy(safe_report, interrupt_in_data, 63);
        report_dirty = false;
        should_send = true;
    }
    critical_section_exit(&report_cs);

    if (should_send) {
        if (!tud_hid_report(0x01, safe_report, 63)) {
            printf("[USBHID] tud_hid_report error\n");
            critical_section_enter_blocking(&report_cs);
            report_dirty = true;
            critical_section_exit(&report_cs);
        }
    }
}

static PsEventTracker ps_events{};
static uint32_t boot_nonce[2];

void __not_in_flash_func(on_bt_data)(CHANNEL_TYPE channel, uint8_t *data, uint16_t len) {
    if (!mode_controller_active()) return;
    if (channel == INTERRUPT && len > 2 && data[1] == 0x31) {
        if ((data[2] >> 1) & 1) {
            if (len >= 4) {
                mic_add_queue(data + 4, len - 4);
            }
            return;
        }
        if (len < 66) return; // 3-byte BT header + complete 63-byte HID payload.
        if (input_generation != mode_generation()) { ps_events.pressed = (data[12]&1)!=0; ps_events.seen = false; input_generation = mode_generation(); }
        ps_events.update((data[12]&1)!=0,to_ms_since_boot(get_absolute_time()));
        if ((data[56] & 1) != (interrupt_in_data[53] & 1)) {
            set_headset(data[56] & 1);
        }

        wake_on_bt_input(data + 3, len - 3);
        #ifdef ENABLE_WAKE_HID
        ps_shortcut_tick(data + 3, len - 3);
        #endif

        if (get_config().polling_rate_mode != 2) {
            memcpy(interrupt_in_data, data + 3, 63);
#if ENABLE_BATT_LED
            battery_led_note_report();
#endif
            return;
        }

        critical_section_enter_blocking(&report_cs);
        memcpy(interrupt_in_data, data + 3, 63);
        report_dirty = true;
        critical_section_exit(&report_cs);
#if ENABLE_BATT_LED
        battery_led_note_report();
#endif
    }
}

extern "C" uint16_t tud_hid_get_report_cb(uint8_t itf, uint8_t report_id, hid_report_type_t report_type,
                                          uint8_t *buffer, uint16_t reqlen) {
#ifdef ENABLE_WAKE_HID
    if (itf == 1) {
        if (reqlen >= 8) {
            memset(buffer, 0, 8);
            return 8;
        }
        return 0;
    }
#endif
    (void) itf;
    (void) report_id;
    (void) report_type;
    (void) buffer;
    (void) reqlen;

    if (is_pico_cmd(report_id)) {
        return pico_cmd_get(report_id, buffer, reqlen);
    }

    if (dse_is_profile_report(report_id) && !dse_profiles_ready()) {
        get_feature_data(report_id, reqlen);
        return 0;
    }

    std::vector<uint8_t> feature_data = get_feature_data(report_id, reqlen);
    const uint16_t copied = usb_feature_payload_length(feature_data.size(), reqlen);
    if (copied) memcpy(buffer, feature_data.data() + 1, copied);
    return copied;
}

extern "C" bool tud_audio_set_itf_cb(uint8_t rhport, tusb_control_request_t const *p_request) {
    (void) rhport;
    uint8_t const itf = tu_u16_low(p_request->wIndex);
    if (!mode_controller_active()) return true;
    uint8_t const alt = tu_u16_low(p_request->wValue);

    if (itf == 1) {
        printf("[AUDIO] Set interface Speaker to alternate setting %d\n", alt);
        spk_active = alt;
    }
    if (itf == 2) {
        printf("[AUDIO] Set interface Microphone to alternate setting %d\n", alt);
        set_mic_active(alt);
    }

    return true;
}

extern "C" void tud_hid_set_report_cb(uint8_t itf, uint8_t report_id, hid_report_type_t report_type,
                                      uint8_t const *buffer, uint16_t bufsize) {
    if (!mode_controller_active()) return;
#ifdef ENABLE_WAKE_HID
    if (itf == 1) {
        return;
    }
#endif
    (void) itf;
    (void) report_id;
    (void) report_type;
    (void) buffer;
    (void) bufsize;

    if (!usb_set_report_length_ok(report_id, buffer, bufsize, offsetof(SetStateData, reserved))) return;

    if (is_pico_cmd(report_id)) {
#if ENABLE_VERBOSE
        printf("[HID] Receive 0xf6 setting config, funcid:0x%02X\n", buffer[0]);
#endif
        pico_cmd_set(report_id, buffer, bufsize);
        return;
    }

    if (report_id == 0) {
        switch (buffer[0]) {
            case 0x02: {
                state_update(buffer + 1, bufsize - 1);
                bool send_now = ((buffer[1] >> 1) & 1) ||
                                ((buffer[39] >> 3) & 1);
                if (!send_now && spk_active) {
                    break;
                }
                uint8_t outputData[78]{};
                outputData[0] = 0x31;
                outputData[1] = reportSeqCounter << 4;
                if (++reportSeqCounter == 256) {
                    reportSeqCounter = 0;
                }
                outputData[2] = 0x10;
                state_set(outputData + 3, sizeof(SetStateData));
                bt_write(outputData, sizeof(outputData));
                break;
            }
        }
    }
    if (report_id == 0x80 ||
        report_id == 0x60 ||
        report_id == 0x62 ||
        report_id == 0x61) {
        set_feature_data(report_id, const_cast<uint8_t *>(buffer), bufsize);
    }
}

//--------------------------------------------------------------------
// Bridge entry points
//--------------------------------------------------------------------

static unsigned bridge_boot_stage;

extern "C" void bridge_boot_begin(void) {
    if (bridge_boot_stage != 0) return;
    boot_nonce[0]=get_rand_32();boot_nonce[1]=get_rand_32();
    // Board/USB/CYW43 are already initialized by unified main.c.
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, false);

#ifdef CYW43_WL_GPIO_SMPS_PIN
    cyw43_arch_gpio_put(CYW43_WL_GPIO_SMPS_PIN, true);
#endif

#if ENABLE_BATT_LED
    battery_led_init();
#endif

    if (watchdog_caused_reboot()) {
        printf("[bridge] Rebooted by Watchdog!\n");
        // Do not block USB while displaying the watchdog notice.
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, true);
    } else {
        printf("[bridge] Clean boot\n");
    }

    critical_section_init(&report_cs);
    wake_init();

    config_load();

    bridge_boot_stage=1;
}

extern "C" bool bridge_boot_step(void) {
    switch (bridge_boot_stage) {
    case 0:
        bridge_boot_begin();
        return false;
    case 1:
        bt_init();
        bt_register_data_callback(on_bt_data);
        bridge_boot_stage=2;
        return false;
    case 2:
        audio_init();
        bridge_boot_stage=3;
        return false;
    case 3:
        state_init();

#ifdef ENABLE_WOL
        wol_init();
#endif
        bridge_boot_stage=4;
        return true;
    default:
        return true;
    }
}

extern "C" void bridge_init(void) {
    bridge_boot_begin();
    while (!bridge_boot_step()) { }
}

static UsbIdentityGate identity_gate{};
static uint32_t usb_reenumerations = 0;

extern "C" void bridge_status_json(char *buffer, unsigned capacity) {
    const uint32_t now=to_ms_since_boot(get_absolute_time());
    char event_age[16];if(ps_events.seen)snprintf(event_age,sizeof(event_age),"%lu",(unsigned long)ps_events.age(now));else strcpy(event_age,"null");
    char metrics[320],uart[128];adapter_metrics_json(metrics,sizeof(metrics),now);adapter_uart_status_json(uart,sizeof(uart));
    const int length=snprintf(buffer, capacity,
        "{\"startup_stage\":\"%s\",\"startup_error\":%d,\"startup_uptime_ms\":%lu,\"bt_connected\":%s,\"identity_ready\":%s,\"ps_pressed\":%s,\"ps_event\":%lu,\"ps_event_age_ms\":%s,\"boot_id\":\"%08lx%08lx\",\"usb_reenumerations\":%lu,\"uptime_ms\":%lu,"
        "\"monitor\":\"linux_bridge\",\"power\":\"%s\",\"network\":\"%s\",\"mqtt_connected\":%s,\"metrics\":%s,\"uart\":%s}",
        adapter_startup_stage_name(),adapter_startup_error(),(unsigned long)adapter_startup_uptime_ms(),
        bt_is_connected()?"true":"false",bt_usb_identity_ready()?"true":"false",
        mode_controller_active() && input_generation == mode_generation() && bt_is_connected() && (interrupt_in_data[9]&1)?"true":"false",
        (unsigned long)(mode_controller_active() && input_generation == mode_generation() ? ps_events.sequence : 0),event_age,(unsigned long)boot_nonce[0],(unsigned long)boot_nonce[1],
        (unsigned long)usb_reenumerations,(unsigned long)now,
        adapter_host_power(now),adapter_network_state(),adapter_mqtt_connected()?"true":"false",metrics,uart);
    if(length<0 || (unsigned)length>=capacity) {
        if(capacity>=30) snprintf(buffer,capacity,"{\"error\":\"status_too_large\"}");
        else if(capacity)buffer[0]=0;
    }
}

extern "C" void bridge_tick(void) {
    if (!mode_controller_active()) return;
    if(!bt_is_connected())ps_events.update(false,to_ms_since_boot(get_absolute_time()));
    // cyw43_arch_poll() and tud_task() are called by unified main.c.
#if ENABLE_SERIAL
    // CDC can enumerate before Bluetooth identity is cached. Recover the host
    // HID probe once per ready edge; keep all original controller metadata.
    const auto action = identity_gate.step(to_ms_since_boot(get_absolute_time()),
                                           bt_usb_identity_ready(), tud_suspended());
    if (action == UsbIdentityAction::Disconnect) {
        wake_note_usb_reconnect();
        tud_disconnect();
        ++usb_reenumerations;
    } else if (action == UsbIdentityAction::Connect) {
        tud_connect();
    }
#endif
    wake_task();
    audio_loop();
    interrupt_loop();
#if ENABLE_BATT_LED
    battery_led_tick();
#endif
    button_check();
    bt_inquiring_led();
    dse_task();
#ifdef ENABLE_WOL
    wol_tick();
#endif
}

extern "C" void bridge_shutdown(void) {
    // Best-effort cleanup before mode switch. A watchdog_reboot follows,
    // so we do the minimum that keeps the plug/gamepad in a defined state.
    cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, false);
}
