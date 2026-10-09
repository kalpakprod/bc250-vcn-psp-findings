# Bounded passive SPI trace — implementation specification
## Scope and anchor
Full adapter plan F passive BIOS/UART evidence; retain full-ROM acquisition as unproven, do not call a short trace a ROM dump. User requires no intermediate upload and no AMD power interruption.
## Connected logic
Current ordinary clock150MHz, CYW43 dynamically claims a PIO SM. GP9 UART1 separate; candidate PIO/DMA libraries already linked. J4004 shared FCH/flash bus, PROGRAM reset-coupled, only SIO0/SIO1 exposed.
## Use cases
Explicit diagnostic-mode, verified wiring capture of one finite four-input waveform. No master commands, writes, injection, address-specific trigger, reset or output GPIO. Raw trace only local CDC, never network.
## Checklist
- default inactive, explicit diagnostic+scheme confirmation
- dynamically claim PIO/DMA, recover resource failure without GPIO action
- four input GP10-CS,11-clock,12-MOSI,13-MISO; no power/reset wires
- PIO wait CS low then in pins4 only; sample at actual clk_sys
- fixed2048 words=16384 samples, DMA completion/disarm, no interrupt loop
- no claim full capture at133MHz or quad/QPI; clock/coverage status explicit
- clear private trace on new capture/mode change/off; bounded sequential read32words
- test actual PIO assembler/firmware build plus source contract; mocks are not hardware proof
## Open questions
Blocking hardware acceptance: actual chip/clock, orientation and loading. Nonblocking offline implementation: documented chip supports133MHz, exceeding150MHz sampler reliable coverage. Full-ROM acquisition remains open.
## Decision
Finite read-only observation, not substitute for full dump. Controller/audio isolation during explicit diagnostic mode; normal clock unchanged. Rollback via existing four roles; no device write in this phase.
