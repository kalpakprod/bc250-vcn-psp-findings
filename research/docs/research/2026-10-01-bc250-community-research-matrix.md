# BC250 Community Research & Requirements Matrix (2026-10-01)

## 1. Executive Summary & Purpose

This document consolidates findings from community channels (Telegram chat "AMD BC-250 community", Discord guild 1315924807128449065, GitHub repositories, and local reverse engineering data) to define the exact feature set, architectural constraints, and UX expectations for the new independent BC250 Control Plane and native Steam Quick Access plugin.

## 2. Community Repositories & Lineage

| Repository / Project                                           | Author / Maintainer     | Role & Capabilities                                                                                | Status in Control Plane                                                                     |
| -------------------------------------------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `movacx/bc250-control-center`                                  | movacx                  | Desktop GUI (PySide6) + Decky Quick Access wrapper. GPU/CPU/Fan/CU/VRAM management, game profiles. | Reference baseline; architectural split into independent daemon/helper + native QAM plugin. |
| `WinnieLV/bc250-cu-live-manager`                               | WinnieLV                | Live CU routing (24 <-> 40 CU) via SPI register masks and CC registers without reboot.             | Integrated via typed privileged helper (`cu-mode 40`, `cu-mode 24`).                        |
| `rw-r-r-0644/bc250-core-unlock`                                | rw-r-r-0644 / rescuemei | SMU protected register writes, core unlocking lineage.                                             | Historical research; arbitrary writes restricted to laboratory mode.                        |
| `Forbidden-Darkness/AMD-BC-250-UEFI-v2.2-Firmware-Menu-Script` | Forbidden-Darkness      | UEFI menu unlocks, DXE driver injection for persistent settings.                                   | Firmware layer; independent of userspace plugin.                                            |
| `CachyOS/linux-cachyos` (BORE)                                 | CachyOS / ptr1337       | Linux kernel with BORE scheduler, Clang ThinLTO, Zen2 optimizations, NCT6687 sensor driver.        | Verified running kernel on console (`7.2.8-1.2-cachyos-bore-bc250`).                        |
| `MastaG/linux-bc250`                                           | MastaG                  | 15 BC250 kernel patches: audio, PCIe, D3cold, display engine, memory mapping.                      | Built and integrated into the active BORE kernel.                                           |
| `e-tho/bc250-acpi-fix`                                         | e-tho                   | ACPI DSDT/SSDT overrides for CPU p-states and power management.                                    | Built archive available; not required for runtime Decky plugin.                             |
| `xXJSONDeruloXx/Decky-Framegen`                                | xXJSONDeruloXx          | FSR 3.1 / OptiScaler frame generation replacement for DLSS in Game Mode.                           | Complementary Decky plugin; reference for native Steam Decky UI standards.                  |
| `hexdumb/turing-smart-screen-python-bc250`                     | hexdumb                 | USB external display dashboard for BC250 telemetry.                                                | Reads telemetry from governor/sysfs; compatible with our daemon metrics.                    |

## 3. Community Desires & Critical Pain Points

### 3.1. Native Steam Quick Access Menu (QAM) Design

- **Problem**: Existing BC250 Quick Access iterations were dismissed by users as "вайп-кодинг" and "чужеродные квадратики". Web-dashboards, custom HTML cards, and desktop-styled forms inside Steam's side panel break immersion and navigation.
- **Requirement**: Use exclusively `@decky/ui` standard components: `PanelSection`, `PanelSectionRow`, `Field`, `ButtonItem`, `SliderField`, `ToggleField`, and standard Steam focus rings. The plugin must navigate flawlessly using only the gamepad D-pad and A/B buttons.

### 3.2. Fan Control Arbitration Conflict

- **Problem**: Setting manual fan PWM causes the background `bc250-fan.service` (or legacy daemon) to immediately overwrite the PWM register back to automatic, causing erratic oscillation ("слетает и возвращается").
- **Requirement**: The privileged helper must pause `bc250-fan.service` when manual PWM is engaged, and automatically resume `bc250-fan.service` when returning to automatic mode, when the plugin unloads, or on failure.

### 3.3. 40 Compute Units (CU) Live Management

- **Problem**: Enabling 40 CUs live via SPI mask `0x1f` routes the 16 extra CUs, but the driver boot-time map remains `[7,7,7,7]` (24 CU). Users need clear distinction between live-routed CUs and persistent boot-time CUs, and a safe way to test without bricking the boot chain.
- **Requirement**: Distinct readouts for `Live Active CUs` (e.g. 40) vs `Driver Boot Map CUs` (24). Safe mode toggle requiring confirmation, persistent boot setting disabled by default.

### 3.4. GPU Frequency & Governor Stability

- **Problem**: Conflicting governors (`cyan_skillfish` vs `oberon`) can cause GPU clock clamping, black screens, or game crashes.
- **Requirement**: Mutually exclusive governor service management, clear safe points (e.g. 1500–2200 MHz), and readback validation after profile application.

### 3.5. CPU Tuning & P-States

- **Problem**: Over-aggressive voltage or frequency scaling causes instant kernel panic.
- **Requirement**: Clamped safe limits (Frequency: 3100–4200 MHz, VID: 950–1325 mV, Scale: -50 to 0). Real-time telemetry monitoring.

### 3.6. Memory & GDDR6 Telemetry

- **Problem**: GDDR6 temperatures on BC250 require specific SMU mailbox queries; without the driver patch, sensors report stale or empty data.
- **Requirement**: Read-only query path with status indicator ("Active" vs "Not available"). VRAM preset changes (2–8 GiB) must clearly indicate that a reboot is required.

### 3.7. Game Profiles Automation

- **Problem**: Games require different thermal and power budgets (e.g. AAA titles need boost fan and max GPU; light emulators need quiet fan and clamped clocks).
- **Requirement**: Automatic detection of running game (`app_id`), application of bound profile on launch, and reliable restoration of default state on game exit.

## 4. Synthesis & Directives for Implementation

1. **Zero Unconfirmed Actions**: Never claim hardware state without readback verification.
2. **Tri-State Architecture**: Safe Mode (default), Advanced Mode (unlocked with confirmation), Laboratory Mode (hidden by default, strict safeguards).
3. **Atomic Deployment**: Deployments must verify hashes, preserve previous working runtime, and support immediate single-command rollback.
