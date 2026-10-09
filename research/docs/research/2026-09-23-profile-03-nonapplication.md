# Archived profile 03: direct evidence it did not apply as expected

The original chat timeline is decisive here. Message order:

- `772088`: image initialized and displayed.
- `772089`: asks whether profile 03 was flashed.
- `772090`: latency `142 ns`.
- `772092`–`772096`: retries profile 03; it boots.
- `772097`: operator says it may have booted because nothing changed.
- `772099`: bandwidth rises to 66k, but not a latency result.
- `772100`: proposes checking whether Tcl 16 applied.
- `772107`: CPU-X displays `1800mt`.
- `772109`: explicit conclusion: “выходит, не применилось” (it seems it did not apply).
- `772113`: asks what changed in NVRAM.
- `772115`: BIOS screen is shown. The captured screen (`photo_9`) displays Tcl and the surrounding timing controls as Auto.
- `772126`–`772130`: operator says settings already available in BIOS do not work and asks for changes below user settings. They hypothesize the board ignores NVRAM values and obtains clocks from other sources.

This is participant evidence, not a hardware measurement. It does not validate the assumption that a raw AmdSetup/NVRAM edit alone reproduces the requested operating state. The exact flashed hash and reset history are absent, so a universal nonapplication claim is not justified. The profile-03 image contains the intended request bytes, but the screenshot and participant interpretation suggest nonapplication in that reported trial, without identifying its cause.

## Decision impact

- Do not treat profile 03, the 1333 hypothesis, or the low-latency hypothesis as successful configurations.
- Do not spend further effort cloning raw NVRAM values.
- The remaining alternatives include variable retrieval/default fallback and later producer/consumer policy. No specific override or ignored-value mechanism has yet been demonstrated. This directly matches the user's original instruction to go “below user settings”.
- The native HII menu bridge is still only an access mechanism. Adding a menu does not solve the ignored-value path.

Evidence: `evidence/firmware-audit/20260923-chat-case/chronology-772088-772130.json`, source export `result.json`, and `photo_9@04-09-2026_04-56-25.jpg`.
