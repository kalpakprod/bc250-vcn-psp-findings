//
// HA webhook over WiFi. Based on DS5Dongle-WoL.
//
// When the controller connects, WiFi is brought up briefly, an HTTP POST is
// sent to the Home Assistant webhook (which turns on the BC-250 power plug),
// then WiFi is torn down.  Everything is non-blocking (state machine from the
// main loop) so the controller's Bluetooth is not affected.
//
// Port to the 0.7.2 base: unlike the 0.6.0 version, we do NOT define
// tud_mount_cb/tud_umount_cb (wake.cpp already defines them with ENABLE_WAKE_HID).
// To tell whether the PC is on we query tud_mounted() during the observation
// window.
//

#include "wol.h"

#include <cstdio>
#include <cstring>

#if __has_include("secrets.h")
#include "secrets.h"
#else
#warning "secrets.h not found: building with placeholder credentials. Copy src/secrets.h.example to src/secrets.h and fill it in."
#define WIFI_SSID        "YOUR_SSID"
#define WIFI_PASS        "YOUR_WIFI_PASSWORD"
#define WEBHOOK_IP_A     192
#define WEBHOOK_IP_B     168
#define WEBHOOK_IP_C     1
#define WEBHOOK_IP_D     22
#define WEBHOOK_PORT     80
#define WEBHOOK_PATH     "/api/webhook/placeholder"
#endif

#include "pico/cyw43_arch.h"
#include "pico/time.h"
#include "tusb.h"
#include "wake.h"
#include "lwip/tcp.h"
#include "lwip/ip_addr.h"

namespace {

enum class State {
    Idle,
    Observe,
    Connecting,
    Backoff,
    Sending,
    Cleanup
};

State           state              = State::Idle;
absolute_time_t state_since;
absolute_time_t last_attempt;
absolute_time_t observe_since;
absolute_time_t host_active_since;
absolute_time_t backoff_since;
int             retries            = 0;
bool            badauth_seen       = false;
bool            wol_ready          = false;

// TCP webhook state
tcp_pcb        *webhook_pcb        = nullptr;
bool            webhook_sent       = false;
bool            webhook_done       = false;

constexpr int64_t HOST_OBSERVE_US       = 3'000'000;
constexpr int64_t HOST_ACTIVE_SUSTAIN_US = 300'000;
constexpr int64_t CONNECT_TIMEOUT_US    = 20'000'000;
constexpr int64_t DEBOUNCE_US           = 90'000'000;
constexpr int64_t BACKOFF_US            = 1'500'000;
constexpr int     MAX_RETRIES           = 2;
constexpr int64_t CLEANUP_LINGER_US     = 500'000;
constexpr int64_t POWEROFF_SUPPRESS_US  = 180'000'000;
constexpr int64_t TCP_TIMEOUT_US        = 10'000'000;

void enter_cleanup() {
    state_since = get_absolute_time();
    state = State::Cleanup;
}

err_t webhook_recv_cb(void *arg, tcp_pcb *tpcb, pbuf *p, err_t err) {
    if (p != nullptr) {
        tcp_recved(tpcb, p->tot_len);
        pbuf_free(p);
    } else {
        // Server closed the connection
        tcp_close(tpcb);
        if (tpcb == webhook_pcb) webhook_pcb = nullptr;
    }
    return ERR_OK;
}

err_t webhook_connected_cb(void *arg, tcp_pcb *tpcb, err_t err) {
    if (err != ERR_OK) {
        printf("[webhook] TCP connect error: %d\n", err);
        webhook_done = true;
        return ERR_OK;
    }

    char request[256];
    const int len = snprintf(request, sizeof(request),
        "POST %s HTTP/1.1\r\n"
        "Host: %d.%d.%d.%d\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n\r\n",
        WEBHOOK_PATH,
        WEBHOOK_IP_A, WEBHOOK_IP_B, WEBHOOK_IP_C, WEBHOOK_IP_D);

    const err_t we = tcp_write(tpcb, request, len, TCP_WRITE_FLAG_COPY);
    if (we == ERR_OK) {
        tcp_output(tpcb);
        webhook_sent = true;
        printf("[webhook] POST sent to %d.%d.%d.%d:%d%s\n",
               WEBHOOK_IP_A, WEBHOOK_IP_B, WEBHOOK_IP_C, WEBHOOK_IP_D,
               WEBHOOK_PORT, WEBHOOK_PATH);
    } else {
        printf("[webhook] tcp_write error: %d\n", we);
    }

    webhook_done = true;
    return ERR_OK;
}

void webhook_error_cb(void *arg, err_t err) {
    printf("[webhook] TCP error: %d\n", err);
    webhook_pcb = nullptr;
    webhook_done = true;
}

void start_connect() {
    cyw43_arch_enable_sta_mode();
    if (cyw43_arch_wifi_connect_async(WIFI_SSID, WIFI_PASS, CYW43_AUTH_WPA2_AES_PSK) != 0) {
        printf("[webhook] connect_async could not be started\n");
        cyw43_arch_disable_sta_mode();
        wake_cancel_poweroff_suppress();
        state = State::Idle;
        return;
    }
    state_since = get_absolute_time();
    state = State::Connecting;
}

}  // namespace

void wol_init() {
    state = State::Idle;
    last_attempt = nil_time;
    retries = 0;
    if (strcmp(WIFI_SSID, "YOUR_SSID") == 0 ||
        strcmp(WEBHOOK_PATH, "/api/webhook/placeholder") == 0) {
        printf("[webhook] secrets.h not configured (placeholders); webhook disabled\n");
        wol_ready = false;
        return;
    }
    wol_ready = true;
    printf("[webhook] Ready: %d.%d.%d.%d:%d%s\n",
           WEBHOOK_IP_A, WEBHOOK_IP_B, WEBHOOK_IP_C, WEBHOOK_IP_D,
           WEBHOOK_PORT, WEBHOOK_PATH);
}

void wol_request() {
    if (!wol_ready) return;
    if (state != State::Idle) return;
    if (!is_nil_time(last_attempt) &&
        absolute_time_diff_us(last_attempt, get_absolute_time()) < DEBOUNCE_US) {
        return;
    }
    retries = 0;
    badauth_seen = false;
    webhook_sent = false;
    webhook_done = false;
    observe_since = get_absolute_time();
    host_active_since = nil_time;
    state = State::Observe;
    wake_suppress_poweroff(POWEROFF_SUPPRESS_US);
    printf("[webhook] Controller connected; observing host (%lld ms)\n",
           static_cast<long long>(HOST_OBSERVE_US / 1000));
}

void wol_tick() {
    switch (state) {
        case State::Idle:
            return;

        case State::Observe:
#if defined(WOL_FORCE_TEST)
            printf("[webhook] (TEST) forcing: ignoring PC gate\n");
            start_connect();
            return;
#elif defined(WOL_ALWAYS)
            printf("[webhook] WOL_ALWAYS: skipping PC-on gate\n");
            start_connect();
            return;
#else
        {
            const bool host_active = tud_mounted() && !tud_suspended();
            if (!host_active) {
                host_active_since = nil_time;
            } else if (is_nil_time(host_active_since)) {
                host_active_since = get_absolute_time();
            } else if (absolute_time_diff_us(host_active_since, get_absolute_time()) >
                       HOST_ACTIVE_SUSTAIN_US) {
                printf("[webhook] USB host active (PC on): webhook aborted\n");
                wake_cancel_poweroff_suppress();
                state = State::Idle;
                return;
            }
            if (absolute_time_diff_us(observe_since, get_absolute_time()) > HOST_OBSERVE_US) {
                printf("[webhook] Host seems off; bringing up WiFi for webhook\n");
                start_connect();
            }
            return;
        }
#endif

        case State::Connecting: {
            const int link = cyw43_tcpip_link_status(&cyw43_state, CYW43_ITF_STA);
            if (link == CYW43_LINK_UP) {
                printf("[webhook] WiFi has IP; starting TCP to HA\n");
                webhook_sent = false;
                webhook_done = false;
                state_since = get_absolute_time();
                state = State::Sending;
                return;
            }
            if (link == CYW43_LINK_BADAUTH) {
                if (!badauth_seen && retries < MAX_RETRIES) {
                    badauth_seen = true;
                    retries++;
                    printf("[webhook] BADAUTH (may be transient); retrying\n");
                    backoff_since = get_absolute_time();
                    state = State::Backoff;
                } else {
                    printf("[webhook] BADAUTH; aborting\n");
                    enter_cleanup();
                }
                return;
            }
            const bool failed = (link < 0);
            const bool timed_out =
                absolute_time_diff_us(state_since, get_absolute_time()) > CONNECT_TIMEOUT_US;
            if (failed || timed_out) {
                printf("[webhook] WiFi failed/timeout (link=%d, retry=%d)\n", link, retries);
                if (retries < MAX_RETRIES) {
                    retries++;
                    backoff_since = get_absolute_time();
                    state = State::Backoff;
                } else {
                    enter_cleanup();
                }
            }
            return;
        }

        case State::Backoff:
            if (absolute_time_diff_us(backoff_since, get_absolute_time()) > BACKOFF_US) {
                start_connect();
            }
            return;

        case State::Sending: {
            if (webhook_pcb == nullptr && !webhook_done) {
                webhook_pcb = tcp_new();
                if (webhook_pcb == nullptr) {
                    printf("[webhook] tcp_new failed\n");
                    enter_cleanup();
                    return;
                }
                tcp_err(webhook_pcb, webhook_error_cb);
                tcp_recv(webhook_pcb, webhook_recv_cb);

                ip_addr_t dest;
                IP4_ADDR(&dest, WEBHOOK_IP_A, WEBHOOK_IP_B, WEBHOOK_IP_C, WEBHOOK_IP_D);

                const err_t ce = tcp_connect(webhook_pcb, &dest, WEBHOOK_PORT,
                                             webhook_connected_cb);
                if (ce != ERR_OK) {
                    printf("[webhook] tcp_connect error: %d\n", ce);
                    tcp_abort(webhook_pcb);
                    webhook_pcb = nullptr;
                    enter_cleanup();
                }
                return;
            }

            if (webhook_done) {
                if (webhook_sent) {
                    last_attempt = get_absolute_time();
                    printf("[webhook] Delivered; cleanup\n");
                }
                if (webhook_pcb != nullptr) {
                    tcp_close(webhook_pcb);
                    webhook_pcb = nullptr;
                }
                enter_cleanup();
                return;
            }

            if (absolute_time_diff_us(state_since, get_absolute_time()) > TCP_TIMEOUT_US) {
                printf("[webhook] TCP timeout\n");
                if (webhook_pcb != nullptr) {
                    tcp_abort(webhook_pcb);
                    webhook_pcb = nullptr;
                }
                enter_cleanup();
            }
            return;
        }

        case State::Cleanup:
            if (absolute_time_diff_us(state_since, get_absolute_time()) < CLEANUP_LINGER_US) {
                return;
            }
            printf("[webhook] WiFi down\n");
            cyw43_arch_disable_sta_mode();
            if (!webhook_sent) {
                wake_cancel_poweroff_suppress();
            }
            state = State::Idle;
            return;
    }
}
