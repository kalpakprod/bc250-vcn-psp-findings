"""Exercise real recorder/watchdog C; never reset or access hardware."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "candidates/waveshare-adapter-safe-v001/src"


class TestRecorder(unittest.TestCase):
    """Native state-machine acceptance, not USB or hardware acceptance."""

    def test_host_loss_is_recorded_without_resetting_live_adapter(self):
        # Missing heartbeat timeout, a blind watchdog feed, or fake zero
        # measurements each violates a separate assertion. CDC wiring is not
        # exercised by this native test.
        source = r'''
#include "adapter_watchdog.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    adapter_recorder_t *r = adapter_recorder_instance();
    adapter_watchdog_t w;
    const uint32_t required = ADAPTER_HEARTBEAT_USB | ADAPTER_HEARTBEAT_RECORDER;
    adapter_recorder_init(r, 0);
    adapter_recorder_heartbeat_config(r, ADAPTER_RECORDER_HOST_HEARTBEAT, 5000);
    adapter_recorder_heartbeat_poll(r, 6000);
    assert(!r->heartbeat_lost && adapter_recorder_count(r) == 0);
    adapter_recorder_heartbeat_update(r, ADAPTER_RECORDER_HOST_HEARTBEAT, 10000);
    adapter_watchdog_init(&w, r, required, 5000, 10000);
    for (uint64_t now = 11000; now <= 15000; now += 1000) {
        adapter_recorder_heartbeat_poll(r, now);
        adapter_watchdog_mark(&w, required, now);
        assert(adapter_watchdog_tick(&w, now));
    }
    assert(r->heartbeat_lost && !adapter_watchdog_expired(&w));
    adapter_recorder_heartbeat_poll(r, 15001);
    assert(adapter_recorder_count(r) == 1);
    adapter_recorder_heartbeat_update(r, ADAPTER_RECORDER_HOST_HEARTBEAT, 15001);
    assert(!r->heartbeat_lost && adapter_recorder_count(r) == 2);
    char data[640];
    assert(adapter_recorder_events_json(r, 0, data, sizeof(data)));
    puts(data);
    assert(!adapter_recorder_events_json(r, 0, data, 8));
    adapter_watchdog_mark(&w, ADAPTER_HEARTBEAT_USB, 16000);
    assert(!adapter_watchdog_tick(&w, 16000));
    assert(!adapter_watchdog_expired(&w));
    adapter_watchdog_mark(&w, ADAPTER_HEARTBEAT_USB, 20000);
    assert(!adapter_watchdog_tick(&w, 20000));
    assert(adapter_watchdog_expired(&w));
    assert(adapter_watchdog_reset_reason(&w) == ADAPTER_WATCHDOG_REASON_TIMEOUT);
    for (uint32_t i = 0; i < 20; ++i)
        assert(adapter_recorder_record_unknown(r, ADAPTER_EVENT_ADAPTER_REBOOT,
                                               0x100000000ULL + i, 0));
    uint32_t cursor = 0;
    adapter_event_t events[16];
    assert(adapter_recorder_read(r, &cursor, events, 16) == 16);
    assert(events[0].sequence == 8 && cursor == 24);
    assert(events[15].monotonic_ms == 0x100000000ULL + 19);
    assert(adapter_recorder_events_json(r, 0, data, sizeof(data)));
    puts(data);
    assert(adapter_recorder_events_json(r, 24, data, sizeof(data)));
    puts(data);
    return 0;
}
'''
        cache = Path.home() / ".cache/waveshare-recorder-integration-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            path = Path(directory)
            (path / "test.c").write_text(source)
            compiled = subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(SRC), str(path / "test.c"),
                 str(SRC / "adapter_recorder.c"), str(SRC / "adapter_watchdog.c"),
                 "-o", str(path / "test")],
                capture_output=True, text=True, timeout=20, check=False,
                env={**os.environ, "TMPDIR": str(cache)},
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            ran = subprocess.run([str(path / "test")], capture_output=True,
                                 text=True, timeout=5, check=False)
            self.assertEqual(ran.returncode, 0, ran.stderr)
            lost, overrun, empty = map(json.loads, ran.stdout.splitlines())
            self.assertEqual([e["type"] for e in lost["events"]], [1, 2])
            self.assertEqual([e["monotonic_ms"] for e in lost["events"]], [15000, 15001])
            self.assertTrue(all(e["value"] is None for e in lost["events"]))
            self.assertEqual(lost["next_cursor"], 3)
            self.assertEqual(overrun["oldest_sequence"], 8)
            self.assertEqual(overrun["next_cursor"], 12)
            self.assertEqual(empty["events"], [])
            self.assertEqual(empty["next_cursor"], 24)


if __name__ == "__main__":
    unittest.main()
