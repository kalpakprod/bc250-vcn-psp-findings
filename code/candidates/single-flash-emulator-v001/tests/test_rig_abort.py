"""Actual C timer/CS abort guard with fake SDK peripherals, not fake guard logic."""
import ctypes as c
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rig_override_model import OverrideTrace
SRC = ROOT.parent / "waveshare-adapter-safe-v001/src/rig"

HEADER = r'''
#ifndef FAKE_SDK_H
#define FAKE_SDK_H
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
typedef unsigned uint;
typedef uint64_t absolute_time_t;
#define __not_in_flash_func(f) f
#define GPIO_OVERRIDE_NORMAL 0
#define GPIO_OVERRIDE_LOW 2
#define GPIO_OVERRIDE_HIGH 3
#define GPIO_IRQ_EDGE_RISE 8
#define IO_IRQ_BANK0 0
static inline absolute_time_t get_absolute_time(void) { return 1000; }
static inline absolute_time_t delayed_by_us(absolute_time_t t, uint64_t us) { return t + us; }
void gpio_set_oeover(uint, uint);
void gpio_set_outover(uint, uint);
void gpio_set_irq_enabled(uint, uint32_t, bool);
void gpio_acknowledge_irq(uint, uint32_t);
uint32_t gpio_get_irq_event_mask(uint);
bool gpio_get(uint);
void gpio_add_raw_irq_handler(uint, void (*)(void));
void gpio_remove_raw_irq_handler(uint, void (*)(void));
void irq_set_enabled(uint, bool);
int hardware_alarm_claim_unused(bool);
void hardware_alarm_set_callback(uint, void (*)(uint));
bool hardware_alarm_set_target(uint, absolute_time_t);
void hardware_alarm_cancel(uint);
void hardware_alarm_unclaim(uint);
#endif
'''
SHIM = r'''
#include "fake_sdk.h"
#include "rig.h"
#include "rig_abort.h"
static void (*timer_cb)(uint);
static void (*gpio_cb)(void);
static bool timer_pending, cs_enabled, missed, unavailable;
static uint oe, out, events, disarms, ordered, order_error;
static absolute_time_t target;
static bool cs = true;
void fake_failure(int flag) { missed = flag == 1; unavailable = flag == 2; }
void fake_reset_trace(void) { ordered = order_error = disarms = 0; }
int fake_driving(void) { return oe != GPIO_OVERRIDE_LOW; }
int fake_hold(void) { return out == GPIO_OVERRIDE_HIGH; }
unsigned fake_disarms(void) { return disarms; }
unsigned fake_order_error(void) { return order_error; }
unsigned fake_pending(void) { return timer_pending; }
unsigned fake_target(void) { return (unsigned)target; }
void gpio_set_oeover(uint pin, uint value) {
 if (pin != RIG_PIN_DO_OVERRIDE) order_error++;
 oe = value; if (value == GPIO_OVERRIDE_LOW) ordered = 1;
}
void gpio_set_outover(uint pin, uint value) {
 if (pin != RIG_PIN_HOLD_BC250) order_error++;
 if (value == GPIO_OVERRIDE_HIGH && ordered != 1) order_error++;
 out = value;
}
void gpio_set_irq_enabled(uint pin, uint32_t mask, bool enabled) { (void)pin; (void)mask; cs_enabled = enabled; }
void gpio_acknowledge_irq(uint pin, uint32_t mask) { (void)pin; events &= ~mask; }
uint32_t gpio_get_irq_event_mask(uint pin) { (void)pin; return events; }
bool gpio_get(uint pin) { (void)pin; return cs; }
void gpio_add_raw_irq_handler(uint pin, void (*f)(void)) { (void)pin; gpio_cb = f; }
void gpio_remove_raw_irq_handler(uint pin, void (*f)(void)) { (void)pin; if (gpio_cb == f) gpio_cb = NULL; }
void irq_set_enabled(uint irq, bool enabled) { (void)irq; (void)enabled; }
int hardware_alarm_claim_unused(bool required) { (void)required; return unavailable ? -1 : 2; }
void hardware_alarm_set_callback(uint alarm, void (*f)(uint)) { (void)alarm; timer_cb = f; }
bool hardware_alarm_set_target(uint alarm, absolute_time_t t) { (void)alarm; target = t; timer_pending = !missed; return missed; }
void hardware_alarm_cancel(uint alarm) { (void)alarm; timer_pending = false; }
void hardware_alarm_unclaim(uint alarm) { (void)alarm; }
// Backend boundary: the real guard must release the pads before DMA cleanup.
void rig_disarm(void) {
 rig_abort_stop();
 if (fake_driving() || !fake_hold()) order_error++;
 disarms++;
}
void fake_cs(int high) {
 bool previous = cs; cs = high;
 if (!previous && cs && cs_enabled) { events |= GPIO_IRQ_EDGE_RISE; if (gpio_cb) gpio_cb(); }
}
void fake_deadline(void) {
 if (timer_pending && timer_cb) { timer_pending = false; timer_cb(2); }
}
'''

class AbortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache = Path.home() / ".cache/waveshare-rig-abort-20261007"
        cache.mkdir(parents=True, exist_ok=True)
        cls.work = tempfile.TemporaryDirectory(dir=cache)
        root = Path(cls.work.name)
        (root / "fake_sdk.h").write_text(HEADER)
        for name in ("pico/stdlib.h", "hardware/gpio.h", "hardware/irq.h", "hardware/timer.h"):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('#include "fake_sdk.h"\n')
        (root / "shim.c").write_text(SHIM)
        library = root / "abort.so"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-shared", "-fPIC", "-I", str(root), "-I", str(SRC),
                        str(SRC / "rig_abort.c"), str(root / "shim.c"), "-o", str(library)],
                       check=True, capture_output=True)
        cls.lib = c.CDLL(str(library))
        cls.lib.rig_abort_init.restype = c.c_bool
        cls.lib.rig_abort_start.argtypes = [c.c_uint32]
        cls.lib.rig_abort_start.restype = c.c_bool

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def tearDown(self):
        self.lib.rig_abort_shutdown()
        self.lib.fake_cs(1)
        self.lib.fake_failure(0)

    def test_early_cs_or_deadline_releases_stalled_override_without_spi_progress(self):
        for cause in ("cs", "deadline"):
            with self.subTest(cause=cause):
                self.assertTrue(self.lib.rig_abort_init())
                self.lib.fake_reset_trace()
                self.assertTrue(self.lib.rig_abort_start(100))
                self.assertEqual(self.lib.fake_target(), 1100)
                trace = OverrideTrace(b"\xa5")
                trace.levels(cs=0, clk=0)
                self.assertEqual((trace.driving, trace.hold), (True, 0))
                self.lib.fake_cs(0)
                if cause == "cs":
                    self.lib.fake_cs(1)
                else:
                    self.lib.fake_deadline()
                self.assertEqual((self.lib.fake_driving(), self.lib.fake_hold()), (0, 1))
                self.assertEqual(self.lib.fake_order_error(), 0)
                self.assertEqual(self.lib.fake_pending(), 0)
                self.assertEqual(self.lib.fake_disarms(), 1)
                # No PIO clock progress or trace "repair" was needed to override pads.
                self.assertFalse(trace.finished)
                self.lib.fake_deadline()
                self.assertEqual(self.lib.fake_disarms(), 1)
                self.lib.rig_abort_shutdown()
                self.lib.fake_cs(1)

    def test_resource_or_missed_deadline_fails_closed_and_rearm_requires_new_budget(self):
        self.lib.fake_failure(2)
        self.assertFalse(self.lib.rig_abort_init())
        self.assertFalse(self.lib.rig_abort_start(100))
        self.lib.fake_failure(0)
        self.assertTrue(self.lib.rig_abort_init())
        self.assertFalse(self.lib.rig_abort_start(0))
        self.lib.fake_failure(1)
        self.assertFalse(self.lib.rig_abort_start(100))
        self.assertEqual((self.lib.fake_driving(), self.lib.fake_hold()), (0, 1))
        self.assertEqual(self.lib.fake_pending(), 0)
        self.lib.fake_failure(0)
        self.assertTrue(self.lib.rig_abort_start(100))
        self.assertFalse(self.lib.rig_abort_start(200))
        self.lib.fake_deadline()
        self.assertEqual((self.lib.fake_driving(), self.lib.fake_hold()), (0, 1))
        self.lib.fake_deadline()
        self.assertTrue(self.lib.rig_abort_start(200))
        self.assertEqual(self.lib.fake_target(), 1200)

if __name__ == "__main__":
    unittest.main()
