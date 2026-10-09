#include "rig_abort.h"
#include "rig.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/irq.h"
#include "hardware/timer.h"

static int alarm_num = -1;
static volatile bool active;

void __not_in_flash_func(rig_abort_stop)(void) {
    if (alarm_num < 0) return;
    active = false;
    /* Pad overrides bypass even a stalled PIO WAIT or forced instruction.
     * Release DO first, then HOLD, BEFORE any potentially blocking DMA abort. */
    gpio_set_oeover(RIG_PIN_DO_OVERRIDE, GPIO_OVERRIDE_LOW);
    gpio_set_outover(RIG_PIN_HOLD_BC250, GPIO_OVERRIDE_HIGH);
    gpio_set_irq_enabled(RIG_PIN_CS, GPIO_IRQ_EDGE_RISE, false);
    gpio_acknowledge_irq(RIG_PIN_CS, GPIO_IRQ_EDGE_RISE);
    hardware_alarm_cancel((unsigned)alarm_num);
}

static void __not_in_flash_func(deadline_irq)(unsigned alarm) {
    if (alarm_num >= 0 && alarm == (unsigned)alarm_num && active) rig_disarm();
}

static void __not_in_flash_func(cs_irq)(void) {
    if (gpio_get_irq_event_mask(RIG_PIN_CS) & GPIO_IRQ_EDGE_RISE) {
        gpio_acknowledge_irq(RIG_PIN_CS, GPIO_IRQ_EDGE_RISE);
        if (active) rig_disarm();
    }
}

bool rig_abort_init(void) {
    if (alarm_num >= 0) return true;
    alarm_num = hardware_alarm_claim_unused(false);
    if (alarm_num < 0) return false;
    hardware_alarm_set_callback((unsigned)alarm_num, deadline_irq);
    gpio_add_raw_irq_handler(RIG_PIN_CS, cs_irq);
    irq_set_enabled(IO_IRQ_BANK0, true);
    return true;
}

bool rig_abort_start(uint32_t timeout_us) {
    if (alarm_num < 0 || !timeout_us || timeout_us > 1000000u || active || !gpio_get(RIG_PIN_CS)) return false;
    // Caller has disabled IRQs and configured a disabled SM with DO input/HOLD high.
    gpio_acknowledge_irq(RIG_PIN_CS, GPIO_IRQ_EDGE_RISE);
    active = true;
    gpio_set_irq_enabled(RIG_PIN_CS, GPIO_IRQ_EDGE_RISE, true);
    if (hardware_alarm_set_target((unsigned)alarm_num, delayed_by_us(get_absolute_time(), timeout_us))) {
        rig_abort_stop();
        return false;
    }
    gpio_set_outover(RIG_PIN_HOLD_BC250, GPIO_OVERRIDE_NORMAL);
    gpio_set_oeover(RIG_PIN_DO_OVERRIDE, GPIO_OVERRIDE_NORMAL);
    return true;
}

void rig_abort_shutdown(void) {
    if (alarm_num < 0) return;
    rig_abort_stop();
    gpio_remove_raw_irq_handler(RIG_PIN_CS, cs_irq);
    hardware_alarm_set_callback((unsigned)alarm_num, NULL);
    hardware_alarm_unclaim((unsigned)alarm_num);
    alarm_num = -1;
}
