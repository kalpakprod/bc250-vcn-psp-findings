#ifndef RIG_ABORT_H
#define RIG_ABORT_H
#include <stdbool.h>
#include <stdint.h>
/* Experimental IRQ guard, never initialized by the normal firmware.
 * Requires IRQ delivery on its owning core; latency needs physical measurement.
 * No SPI clock or cooperative main-loop progress is needed for a deadline. */
bool rig_abort_init(void);
bool rig_abort_start(uint32_t timeout_us);
void rig_abort_stop(void);
void rig_abort_shutdown(void);
#endif
