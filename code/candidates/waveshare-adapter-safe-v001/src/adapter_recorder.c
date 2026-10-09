#include "adapter_recorder.h"

#include <stdio.h>
#include <string.h>

static adapter_recorder_t shared_recorder;
adapter_recorder_t *adapter_recorder_instance(void) { return &shared_recorder; }

static bool elapsed(uint64_t now, uint64_t then, uint64_t limit) {
  return now >= then && now - then >= limit;
}

void adapter_recorder_init(adapter_recorder_t *rec, uint64_t now_ms) {
  if (!rec)
    return;
  memset(rec, 0, sizeof(*rec));
  rec->heartbeat_last_ms = now_ms;
}

void adapter_recorder_heartbeat_config(adapter_recorder_t *rec,
                                        uint32_t required_bits,
                                        uint64_t timeout_ms) {
  if (!rec)
    return;
  rec->heartbeat_required = required_bits;
  rec->heartbeat_timeout_ms = timeout_ms;
  rec->heartbeat_seen = 0;
  rec->heartbeat_started = false;
  rec->heartbeat_lost = false;
}

void adapter_recorder_heartbeat_update(adapter_recorder_t *rec,
                                       uint32_t bits,
                                       uint64_t now_ms) {
  if (!rec)
    return;
  rec->heartbeat_seen |= bits;
  rec->heartbeat_last_ms = now_ms;
  rec->heartbeat_started = true;
  if (rec->heartbeat_lost &&
      (rec->heartbeat_seen & rec->heartbeat_required) ==
          rec->heartbeat_required) {
    rec->heartbeat_lost = false;
    (void)adapter_recorder_record_unknown(rec, ADAPTER_EVENT_HEARTBEAT_RECOVERED,
                                          now_ms, rec->heartbeat_seen);
  }
}

void adapter_recorder_heartbeat_poll(adapter_recorder_t *rec,
                                     uint64_t now_ms) {
  if (!rec || !rec->heartbeat_started || !rec->heartbeat_required ||
      !rec->heartbeat_timeout_ms)
    return;
  const bool complete = (rec->heartbeat_seen & rec->heartbeat_required) ==
                        rec->heartbeat_required;
  if (elapsed(now_ms, rec->heartbeat_last_ms, rec->heartbeat_timeout_ms) &&
      !rec->heartbeat_lost) {
    rec->heartbeat_lost = true;
    (void)adapter_recorder_record(rec, ADAPTER_EVENT_HEARTBEAT_LOST, now_ms,
                                  rec->heartbeat_seen, 0,
                                  ADAPTER_VALUE_UNKNOWN);
  }
  if (complete && !rec->heartbeat_lost)
    rec->heartbeat_seen = 0;
}

bool adapter_recorder_record(adapter_recorder_t *rec,
                             adapter_event_type_t type,
                             uint64_t now_ms,
                             uint32_t heartbeat_bits,
                             int32_t value,
                             adapter_value_state_t value_state) {
  if (!rec || type == 0)
    return false;
  if (rec->sequence == UINT32_MAX) {
    /* Keep sequence arithmetic unambiguous for readers rather than allowing
     * a wrapped sequence to make a full ring look empty or overrun. */
    rec->sequence = 0;
    rec->next = 0;
    rec->count = 0;
  }
  adapter_event_t *event = &rec->events[rec->next];
  rec->sequence++;
  if (!rec->sequence)
    rec->sequence++;
  *event = (adapter_event_t){rec->sequence, now_ms, type, heartbeat_bits,
                             value, value_state};
  rec->next = (rec->next + 1u) % ADAPTER_RECORDER_EVENT_CAPACITY;
  if (rec->count < ADAPTER_RECORDER_EVENT_CAPACITY)
    rec->count++;
  return true;
}

bool adapter_recorder_record_unknown(adapter_recorder_t *rec,
                                     adapter_event_type_t type,
                                     uint64_t now_ms,
                                     uint32_t heartbeat_bits) {
  return adapter_recorder_record(rec, type, now_ms, heartbeat_bits, 0,
                                  ADAPTER_VALUE_UNKNOWN);
}

size_t adapter_recorder_read(const adapter_recorder_t *rec,
                             uint32_t *cursor,
                             adapter_event_t *out,
                             size_t capacity) {
  if (!rec || !cursor || !out || !capacity)
    return 0;
  uint32_t oldest = rec->next + ADAPTER_RECORDER_EVENT_CAPACITY - rec->count;
  oldest %= ADAPTER_RECORDER_EVENT_CAPACITY;
  uint32_t wanted = *cursor;
  if (wanted < rec->sequence - rec->count + 1u)
    wanted = rec->sequence - rec->count + 1u;
  size_t copied = 0;
  while (copied < capacity && wanted && wanted <= rec->sequence) {
    uint32_t offset = wanted - (rec->sequence - rec->count + 1u);
    if (offset >= rec->count)
      break;
    uint32_t slot = (oldest + offset) % ADAPTER_RECORDER_EVENT_CAPACITY;
    out[copied++] = rec->events[slot];
    wanted++;
  }
  *cursor = wanted;
  return copied;
}

uint32_t adapter_recorder_last_sequence(const adapter_recorder_t *rec) {
  return rec ? rec->sequence : 0;
}

uint32_t adapter_recorder_count(const adapter_recorder_t *rec) {
  return rec ? rec->count : 0;
}

size_t adapter_recorder_json(const adapter_recorder_t *rec,
                             char *out,
                             size_t capacity,
                             uint64_t now_ms) {
  if (!out || !capacity)
    return 0;
  if (!rec)
    return (size_t)snprintf(out, capacity, "{\"valid\":false}");
  const unsigned long long age =
      rec->heartbeat_started && now_ms >= rec->heartbeat_last_ms
          ? (unsigned long long)(now_ms - rec->heartbeat_last_ms)
          : 0ull;
  const bool valid = rec->heartbeat_started && !rec->heartbeat_lost;
  const int n = snprintf(
      out, capacity,
      "{\"valid\":%s,\"heartbeat_bits\":%lu,\"heartbeat_age_ms\":%llu,"
      "\"event_sequence\":%lu,\"event_count\":%lu,\"freshness_limit_ms\":%llu}",
      valid ? "true" : "false", (unsigned long)rec->heartbeat_seen, age,
      (unsigned long)rec->sequence, (unsigned long)rec->count,
      (unsigned long long)rec->heartbeat_timeout_ms);
  if (n < 0)
    return 0;
  return (size_t)n < capacity ? (size_t)n : capacity - 1u;
}

size_t adapter_recorder_events_json(const adapter_recorder_t *rec,
                                    uint32_t cursor, char *out, size_t capacity) {
  if (!rec || !out || !capacity)
    return 0;
  adapter_event_t events[4];
  const size_t count = adapter_recorder_read(rec, &cursor, events, 4);
  const uint32_t oldest = rec->sequence - rec->count + 1u;
  int n = snprintf(out, capacity,
                   "{\"next_cursor\":%lu,\"oldest_sequence\":%lu,\"events\":[",
                   (unsigned long)cursor, (unsigned long)oldest);
  if (n < 0 || (size_t)n >= capacity)
    return 0;
  size_t used = (size_t)n;
  for (size_t i = 0; i < count; ++i) {
    const adapter_event_t *e = &events[i];
    char value[16];
    if (e->value_state == ADAPTER_VALUE_VALID)
      snprintf(value, sizeof(value), "%ld", (long)e->value);
    else
      strcpy(value, "null");
    n = snprintf(out + used, capacity - used,
                 "%s{\"sequence\":%lu,\"monotonic_ms\":%llu,\"type\":%u,"
                 "\"heartbeat_bits\":%lu,\"value\":%s}",
                 i ? "," : "", (unsigned long)e->sequence,
                 (unsigned long long)e->monotonic_ms, (unsigned)e->type,
                 (unsigned long)e->heartbeat_bits, value);
    if (n < 0 || (size_t)n >= capacity - used)
      return 0;
    used += (size_t)n;
  }
  n = snprintf(out + used, capacity - used, "]}");
  if (n < 0 || (size_t)n >= capacity - used)
    return 0;
  return used + (size_t)n;
}
