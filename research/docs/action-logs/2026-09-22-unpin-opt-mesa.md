# Action log: unpin /opt Vulkan driver, switch board to system Mesa 26.2.3

Date: 2026-09-22. Actor: root (this session). Operator order: use the new
system Mesa everywhere instead of the old pinned build.

## Intent (before execution)

Board `steammachine@127.0.0.1`. Today ALL 64-bit Vulkan apps (game
included) load `/opt/bc250-gfx1013/v3.3.0/lib/libvulkan_radeon.so`
(Mesa 26.2.0-rc3, built 2026-08-25) because
`/etc/profile.d/60-bc250-gfx1013.sh` globally exports VK_DRIVER_FILES +
VK_ICD_FILENAMES. System Mesa 3:26.2.3-1.1/2.1 (+9 BC250 patches) is
installed but invisible to the game (except 32-bit ICD, already system).

Target: `/etc/profile.d/60-bc250-gfx1013.sh` -> rename to
`60-bc250-gfx1013.sh.disabled-20260922` (file kept, zero bytes changed).
Command: `sudo mv ...`. Reason: one global arrow redirects everything
to the old build; removing it puts the whole board (game, gamescope,
vulkaninfo) on system Mesa 26.2.3.

Expected effect: NOTHING changes until next login — profile.d is read
at session start. Effect arrives with the already-pending reboot
(kernel 7.2.6-1.2 + cmdline). After reboot: `vulkaninfo | grep
driverVersion` must show 26.2.3, and MangoHud `vulkan_driver` in-game
must agree.

Rollback (1 min, no reboot of firmware): `sudo mv` the file back, then
re-login/reboot. /opt tree untouched. Risk: game could behave worse on
system Mesa — reversible; paired A/B planned.

## Result

Executed 2026-09-22 ~02:0x+05: MOVED_OK, both old files preserved
(.bak-20260902 + .disabled-20260922). /opt tree untouched.
Verified same minute: a FRESH ssh login already reports
`driverVersion = 26.2.3, DRIVER_ID_MESA_RADV` (was pinned to /opt
26.2.0-rc3). The running gamescope/Steam session keeps the old env
until re-login — full effect (game included) arrives with the pending
reboot (kernel 7.2.6-1.2 + cmdline). Post-reboot check: in-game
MangoHud `vulkan_driver` must read 26.2.3.
