#include "adapter_watchdog.h"

#include <string.h>

#if defined(PICO_ON_DEVICE) || defined(PICO_RP2040) || defined(PICO_RP2350)
#include "hardware/watchdog.h"
#include "hardware/structs/watchdog.h"
#define ADAPTER_WATCHDOG_HW 1
#endif

#define ADAPTER_WATCHDOG_MAGIC 0x57444700u

static bool elapsed(uint64_t now, uint64_t then, uint64_t limit) {
  return now >= then && now - then >= limit;
}

static void persist_progress(const adapter_watchdog_t *watchdog,
                             uint32_t reason) {
#if ADAPTER_WATCHDOG_HW
  watchdog_hw->scratch[0] = ADAPTER_WATCHDOG_MAGIC | (reason & 0xffu);
  watchdog_hw->scratch[1] = watchdog->pending_bits;
  watchdog_hw->scratch[2] = watchdog->last_sequence;
  watchdog_hw->scratch[3] = (uint32_t)watchdog->last_progress_ms;
#else
  (void)watchdog;
  (void)reason;
#endif
}

void adapter_watchdog_init(adapter_watchdog_t *watchdog,
                           adapter_recorder_t *recorder,
                           uint32_t required_bits,
                           uint64_t timeout_ms,
                           uint64_t now_ms) {
  if (!watchdog)
    return;
  memset(watchdog, 0, sizeof(*watchdog));
  watchdog->recorder = recorder;
  watchdog->required_bits = required_bits;
  watchdog->timeout_ms = timeout_ms;
  watchdog->last_feed_ms = now_ms;
  watchdog->last_progress_ms = now_ms;
#if ADAPTER_WATCHDOG_HW
  /* Read the boot cause before watchdog_enable overwrites SDK scratch[4]. */
  if (watchdog_enable_caused_reboot()) {
    uint32_t marker = watchdog_hw->scratch[0];
    if ((marker & 0xffffff00u) == ADAPTER_WATCHDOG_MAGIC &&
        (marker & 0xffu) != ADAPTER_WATCHDOG_REASON_NONE)
      watchdog->reset_reason =
          (adapter_watchdog_reason_t)(marker & 0xffu);
    else
      /* A hard stall can reset before the foreground tick stores an explicit
       * reason. A watchdog-caused reboot is therefore conservatively timeout. */
      watchdog->reset_reason = ADAPTER_WATCHDOG_REASON_TIMEOUT;
    if (recorder)
      (void)adapter_recorder_record_unknown(recorder,
                                            ADAPTER_EVENT_WATCHDOG_RESET,
                                            now_ms, 0);
  }
  /* This is the only reset mechanism exposed here: the RP watchdog resets the
   * adapter MCU, never BC250 power rails. It remains unfed until progress is
   * observed for every required service. */
  if (timeout_ms)
    watchdog_enable((uint32_t)timeout_ms, false);
#else
  watchdog->reset_reason = ADAPTER_WATCHDOG_REASON_NONE;
#endif
  watchdog->started = true;
}

void adapter_watchdog_mark(adapter_watchdog_t *watchdog,
                           uint32_t heartbeat_bits,
                           uint64_t now_ms) {
  if (!watchdog || !watchdog->started || watchdog->expired)
    return;
  watchdog->pending_bits |= heartbeat_bits;
  watchdog->last_progress_ms = now_ms;
  if (watchdog->recorder)
    watchdog->last_sequence =
        adapter_recorder_last_sequence(watchdog->recorder);
  persist_progress(watchdog, ADAPTER_WATCHDOG_REASON_NONE);
}

bool adapter_watchdog_tick(adapter_watchdog_t *watchdog, uint64_t now_ms) {
  if (!watchdog || !watchdog->started || !watchdog->required_bits ||
      !watchdog->timeout_ms)
    return false;
  const bool complete =
      (watchdog->pending_bits & watchdog->required_bits) ==
      watchdog->required_bits;
  if (elapsed(now_ms, watchdog->last_feed_ms, watchdog->timeout_ms)) {
    /* A completed set of bits that arrived after the deadline is still a
     * missed watchdog period. Never feed late and silently hide the stall. */
    watchdog->expired = true;
    watchdog->reset_reason = ADAPTER_WATCHDOG_REASON_TIMEOUT;
    persist_progress(watchdog, ADAPTER_WATCHDOG_REASON_TIMEOUT);
    if (watchdog->recorder)
      (void)adapter_recorder_record_unknown(
          watchdog->recorder, ADAPTER_EVENT_WATCHDOG_RESET, now_ms,
          watchdog->pending_bits);
    return false;
  }
  if (complete && !watchdog->expired) {
    watchdog->pending_bits = 0;
    watchdog->last_feed_ms = now_ms;
    persist_progress(watchdog, ADAPTER_WATCHDOG_REASON_NONE);
#if ADAPTER_WATCHDOG_HW
    watchdog_update();
#endif
    return true;
  }
  return false;
}

bool adapter_watchdog_expired(const adapter_watchdog_t *watchdog) {
  return watchdog && watchdog->expired;
}

adapter_watchdog_reason_t adapter_watchdog_reset_reason(
    const adapter_watchdog_t *watchdog) {
  return watchdog ? watchdog->reset_reason : ADAPTER_WATCHDOG_REASON_UNKNOWN;
}

uint32_t adapter_watchdog_last_sequence(const adapter_watchdog_t *watchdog) {
  return watchdog ? watchdog->last_sequence : 0;
}
