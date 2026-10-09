# BC250 Control Plane Capability & Parity Matrix (2026-10-01)

## 1. Scope & Methodology
This matrix audits all 29 public async callable endpoints of the BC250 Decky plugin and backend, mapping each to its hardware subsystem, access level, verification readback, safety constraints, and implementation status across the three layers:
- **Backend / Daemon (`main.py` / `bc250cc`)**
- **Privileged Helper (`bc250-fan-helper` / sysfs / SMU)**
- **Steam QAM Frontend (`src/index.tsx`)**

## 2. Complete Parity & Capability Ledger

| # | Endpoint Name | Subsystem | Access Tier | Parameter Signature | Readback Verification | Root Helper Action | Frontend Status |
|---|---|---|---|---|---|---|---|
| 1 | `status` | Telemetry | Safe | `()` | sysfs / hwmon | `read-only` | Wired (`getStatus`) |
| 2 | `monitor_snapshot` | Telemetry | Safe | `()` | JSON snapshot dict | `read-only` | Wired (`getSnapshot`) |
| 3 | `cpu_telemetry` | CPU | Safe | `()` | `/proc/cpuinfo`, msr | `read-only` | Wired (`cpuTelemetry`) |
| 4 | `gddr6_sensors` | Memory | Safe | `()` | SMU mailbox query | `read-only` | Wired (`getGddr6`) |
| 5 | `apply_gpu_profile` | GPU | Safe | `(profile: str)` | `pp_dpm_sclk` / `pp_od_clk_voltage` | `gpu-profile <name>` | Wired (`applyGpuProfile`) |
| 6 | `apply_gpu_safe_point` | GPU | Advanced | `(frequency: int)` | sysfs clk readback | `gpu-safe-point <freq>` | Wired (`applyGpuSafePoint`) |
| 7 | `set_gpu_high_frequency_points` | GPU | Lab | `(enabled: bool)` | driver clk table | `gpu-hfp <0/1>` | Wired (`applyGpuPoints`) |
| 8 | `set_gpu_governor_service` | GPU | Safe | `(enabled: bool)` | systemctl is-active | `systemctl <action> <gov>` | Wired (`setGovernor`) |
| 9 | `apply_gpu_voltage_level` | GPU | Advanced | `(level: int)` | sysfs voltage table | `gpu-voltage-level <lvl>` | Wired (`applyGpuVoltageLevel`) |
| 10 | `apply_gpu_voltage_points` | GPU | Lab | `(points: list[dict])` | pp_od table | `gpu-voltage-points <json>` | Wired (`applyGpuVoltagePoints`) |
| 11 | `apply_cu_mode` | Compute Units | Advanced | `(mode: str)` | SPI mask / CC register | `cu-mode <24/40>` | Wired (`applyCuMode`) |
| 12 | `apply_cu_table` | Compute Units | Advanced | `(masks: list[int])` | SPI readback | `cu-table <m1>..<m4>` | Wired (`applyCuTable`) |
| 13 | `save_cu_table` | Compute Units | Advanced | `(masks: list[int])` | saved config JSON | `save-cu-table` | Wired (`saveCuTable`) |
| 14 | `install_cu_service` | Compute Units | Advanced | `()` | systemctl is-enabled | `systemctl enable cu-service` | Wired (`installCu`) |
| 15 | `remove_cu_service` | Compute Units | Advanced | `()` | systemctl is-enabled | `systemctl disable cu-service` | Wired (`removeCu`) |
| 16 | `apply_system_fan_preset` | Cooling | Safe | `(preset: str)` | hwmon pwm readback | `fan-preset <name>` | Wired (`applyFanPreset`) |
| 17 | `apply_fan_channel` | Cooling | Safe | `(channel: int, target: int/str)` | hwmon pwm readback | `fan-channel <ch> <tgt>` | Wired (`applyFan`) |
| 18 | `apply_cpu_tuning` | CPU | Advanced | `(frequency: int, vid: int)` | zenpower / msr | `cpu-tuning <freq> <vid>` | Wired (`applyCpu`) |
| 19 | `apply_cpu_scale` | CPU | Advanced | `(frequency: int, scale: int)` | zenpower / msr | `cpu-scale <freq> <scl>` | Wired (`applyCpuScale`) |
| 20 | `apply_saved_cpu_profile` | CPU | Advanced | `()` | zenpower readback | `apply-cpu-saved` | Wired (`applySavedCpu`) |
| 21 | `install_cpu_service` | CPU | Advanced | `()` | systemctl is-enabled | `systemctl enable cpu-service` | Wired (`installCpu`) |
| 22 | `remove_cpu_service` | CPU | Advanced | `()` | systemctl is-enabled | `systemctl disable cpu-service` | Wired (`removeCpu`) |
| 23 | `apply_vram_size` | Memory | Advanced | `(size_mb: int)` | limine.conf / grub cmdline | `vram-preset <mb>` | Wired (`applyVram`) |
| 24 | `game_profiles` | Profiles | Safe | `()` | config store JSON | `read-only` | Wired (`getGames`) |
| 25 | `save_game_profile` | Profiles | Safe | `(app_id, name, gpu, fan)` | config store JSON | `save-game-profile` | Wired (`saveGame`) |
| 26 | `remove_game_profile` | Profiles | Safe | `(app_id)` | config store JSON | `remove-game-profile` | Wired (`removeGame`) |
| 27 | `set_game_profiles_enabled` | Profiles | Safe | `(enabled: bool)` | config store JSON | `set-game-profiles-enabled` | Wired (`enableGames`) |
| 28 | `game_started` | Profiles | Safe | `(app_id, name, refresh)` | active session status | `hook-game-start` | Wired (`gameStarted`) |
| 29 | `game_stopped` | Profiles | Safe | `(app_id)` | restored session status | `hook-game-stop` | Wired (`gameStopped`) |

## 3. Tiered Access Policy
- **Safe Tier**: Instant execution, no confirmation needed for viewing; single non-destructive confirmation for setting change. No hardware risk.
- **Advanced Tier**: Modal confirmation required. Validates inputs against tight hardware safety bounds. Automatic rollback on failure.
- **Laboratory Tier**: Modal with explicit risk acknowledgment. Confirms current kernel capability before execution. Rollback path must be pre-staged.
