#ifndef WAVESHARE_ADAPTER_RECORDER_H
#define WAVESHARE_ADAPTER_RECORDER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* A fixed-size ring keeps the recorder usable while USB or networking is
 * unavailable.  The oldest entries are overwritten once it is full. */
#define ADAPTER_RECORDER_EVENT_CAPACITY 16u
#define ADAPTER_RECORDER_HOST_HEARTBEAT 1u

typedef enum {
  ADAPTER_VALUE_UNKNOWN = 0,
  ADAPTER_VALUE_VALID = 1,
} adapter_value_state_t;

typedef enum {
  ADAPTER_EVENT_HEARTBEAT_LOST = 1,
  ADAPTER_EVENT_HEARTBEAT_RECOVERED = 2,
  ADAPTER_EVENT_POWER_DROP = 3,
  ADAPTER_EVENT_ADAPTER_REBOOT = 4,
  ADAPTER_EVENT_WATCHDOG_RESET = 5,
} adapter_event_type_t;

typedef struct {
  uint32_t sequence;
  uint64_t monotonic_ms;
  adapter_event_type_t type;
  uint32_t heartbeat_bits;
  int32_t value;
  adapter_value_state_t value_state;
} adapter_event_t;

typedef struct {
  adapter_event_t events[ADAPTER_RECORDER_EVENT_CAPACITY];
  uint32_t next;
  uint32_t count;
  uint32_t sequence;
  uint32_t heartbeat_required;
  uint32_t heartbeat_seen;
  uint64_t heartbeat_timeout_ms;
  uint64_t heartbeat_last_ms;
  bool heartbeat_started;
  bool heartbeat_lost;
} adapter_recorder_t;

/* One instance shared by the foreground loop and its CDC/HTTP callbacks. */
adapter_recorder_t *adapter_recorder_instance(void);
void adapter_recorder_init(adapter_recorder_t *rec, uint64_t now_ms);
void adapter_recorder_heartbeat_config(adapter_recorder_t *rec,
                                        uint32_t required_bits,
                                        uint64_t timeout_ms);
void adapter_recorder_heartbeat_update(adapter_recorder_t *rec,
                                       uint32_t bits,
                                       uint64_t now_ms);
void adapter_recorder_heartbeat_poll(adapter_recorder_t *rec,
                                     uint64_t now_ms);

bool adapter_recorder_record(adapter_recorder_t *rec,
                             adapter_event_type_t type,
                             uint64_t now_ms,
                             uint32_t heartbeat_bits,
                             int32_t value,
                             adapter_value_state_t value_state);
bool adapter_recorder_record_unknown(adapter_recorder_t *rec,
                                     adapter_event_type_t type,
                                     uint64_t now_ms,
                                     uint32_t heartbeat_bits);

/* Copy the oldest available entries without exposing ring storage. */
size_t adapter_recorder_read(const adapter_recorder_t *rec,
                             uint32_t *cursor,
                             adapter_event_t *out,
                             size_t capacity);
uint32_t adapter_recorder_last_sequence(const adapter_recorder_t *rec);
uint32_t adapter_recorder_count(const adapter_recorder_t *rec);

/* Stable bounded status representation for CDC/HTTP adapters. */
size_t adapter_recorder_json(const adapter_recorder_t *rec,
                             char *out,
                             size_t capacity,
                             uint64_t now_ms);

/* At most four events per response. Zero means insufficient output capacity. */
size_t adapter_recorder_events_json(const adapter_recorder_t *rec,
                                    uint32_t cursor, char *out, size_t capacity);

#ifdef __cplusplus
}
#endif

#endif
