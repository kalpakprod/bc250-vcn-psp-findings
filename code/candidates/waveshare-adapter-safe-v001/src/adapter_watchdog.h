#ifndef WAVESHARE_ADAPTER_WATCHDOG_H
#define WAVESHARE_ADAPTER_WATCHDOG_H

#include <stdbool.h>
#include <stdint.h>

#include "adapter_recorder.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
  ADAPTER_HEARTBEAT_USB = 1u << 0,
  ADAPTER_HEARTBEAT_WIFI = 1u << 1,
  ADAPTER_HEARTBEAT_CONTROLLER = 1u << 2,
  ADAPTER_HEARTBEAT_METRICS = 1u << 3,
  ADAPTER_HEARTBEAT_RECORDER = 1u << 4,
};

typedef enum {
  ADAPTER_WATCHDOG_REASON_NONE = 0,
  ADAPTER_WATCHDOG_REASON_TIMEOUT = 1,
  ADAPTER_WATCHDOG_REASON_EXTERNAL = 2,
  ADAPTER_WATCHDOG_REASON_UNKNOWN = 3,
} adapter_watchdog_reason_t;

typedef struct {
  adapter_recorder_t *recorder;
  uint32_t required_bits;
  uint32_t pending_bits;
  uint64_t timeout_ms;
  uint64_t last_feed_ms;
  uint64_t last_progress_ms;
  uint32_t last_sequence;
  adapter_watchdog_reason_t reset_reason;
  bool started;
  bool expired;
} adapter_watchdog_t;

void adapter_watchdog_init(adapter_watchdog_t *watchdog,
                           adapter_recorder_t *recorder,
                           uint32_t required_bits,
                           uint64_t timeout_ms,
                           uint64_t now_ms);
void adapter_watchdog_mark(adapter_watchdog_t *watchdog,
                           uint32_t heartbeat_bits,
                           uint64_t now_ms);
/* Returns true only when all required progress bits arrived in this period. */
bool adapter_watchdog_tick(adapter_watchdog_t *watchdog, uint64_t now_ms);
bool adapter_watchdog_expired(const adapter_watchdog_t *watchdog);
adapter_watchdog_reason_t adapter_watchdog_reset_reason(
    const adapter_watchdog_t *watchdog);
uint32_t adapter_watchdog_last_sequence(const adapter_watchdog_t *watchdog);

#ifdef __cplusplus
}
#endif

#endif
