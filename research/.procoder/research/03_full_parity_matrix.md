# Worker 3: Full Feature Parity & Capability Matrix

**Status:** 30 Public Callables Mapped & Verified
**Architecture:** Decky API (`callable`) <-> Python Plugin Backend (`main.py`) <-> Privileged System Helper / sysfs / SMU / UMR

---

## 1. Feature Parity Matrix

| # | Endpoint Name | Category | Safety Tier | Args | Return Type | UI Component | Description |
|---|---|---|---|---|---|---|---|
| 1 | `status` | Telemetry | Safe | `()` | `State` | `OverviewSection` | Complete board status (clocks, temps, governor, fan, VRAM, CU) |
| 2 | `monitor_snapshot` | Telemetry | Safe | `()` | `Result` | `OverviewSection` | Instantaneous telemetry snapshot |
| 3 | `gddr6_sensors` | Telemetry | Safe | `()` | `Result` | `OverviewSection` | Reads 8-channel GDDR6 temperatures via SMU mailbox |
| 4 | `cpu_telemetry` | Telemetry | Safe | `()` | `Result` | `CpuSection` | Realtime CPU cores, frequency, VID readback |
| 5 | `apply_gpu_profile` | GPU | Safe | `(profile_key: str)` | `Result` | `GpuSection` | Sets validated GPU clock profiles (e.g., quiet, default, oc) |
| 6 | `set_gpu_governor_service` | GPU | Safe | `(enabled: bool)` | `Result` | `GpuSection` | Toggles cyan/oberon GPU governor systemd service |
| 7 | `set_gpu_high_frequency_points` | GPU | Extended | `(enabled: bool)` | `Result` | `GpuSection` | Enables >2000MHz GPU points (disabled by default) |
| 8 | `apply_gpu_safe_point` | GPU | Extended | `(freq: int)` | `Result` | `LabSection` | Applies validated single GPU frequency ceiling |
| 9 | `apply_gpu_voltage_level` | GPU | Lab | `(level: int)` | `Result` | `LabSection` | Sets GPU voltage level offset |
| 10 | `apply_gpu_voltage_points` | GPU | Lab | `(points: list)` | `Result` | `LabSection` | Uploads full custom frequency-voltage curve |
| 11 | `apply_cpu_tuning` | CPU | Extended | `(freq: int, vid: int)` | `Result` | `CpuSection` | Sets CPU target frequency and VID |
| 12 | `apply_cpu_scale` | CPU | Extended | `(freq: int, scale: int)` | `Result` | `CpuSection` | Applies manual CPU scaling ratio |
| 13 | `apply_saved_cpu_profile` | CPU | Safe | `()` | `Result` | `CpuSection` | Restores stored CPU profile |
| 14 | `install_cpu_service` | CPU | Safe | `()` | `Result` | `CpuSection` | Installs systemd boot unit for CPU profile |
| 15 | `remove_cpu_service` | CPU | Safe | `()` | `Result` | `CpuSection` | Removes systemd boot unit for CPU profile |
| 16 | `apply_fan_channel` | Cooling | Safe | `(channel: int, value: int \| "automatic")` | `Result` | `CoolingSection` | Sets manual PWM % (20-100) or returns to automatic with arbitration |
| 17 | `apply_system_fan_preset` | Cooling | Safe | `(preset: str)` | `Result` | `CoolingSection` | Applies fan preset (`quiet`, `balanced`, `boost`) |
| 18 | `apply_cu_mode` | Compute Units | Extended | `(mode: str)` | `Result` | `MemoryCuSection` | Toggles 24 vs 40 CU runtime routing |
| 19 | `apply_cu_table` | Compute Units | Extended | `(masks: int[4])` | `Result` | `MemoryCuSection` | Sets custom CU bitmasks across 4 shader engines |
| 20 | `save_cu_table` | Compute Units | Extended | `(masks: int[4])` | `Result` | `MemoryCuSection` | Persists validated CU bitmasks to config |
| 21 | `install_cu_service` | Compute Units | Safe | `()` | `Result` | `MemoryCuSection` | Enables `bc250-cu.service` for boot-time CU persistence |
| 22 | `remove_cu_service` | Compute Units | Safe | `()` | `Result` | `MemoryCuSection` | Disables `bc250-cu.service` |
| 23 | `apply_vram_size` | Memory | Extended | `(size_mib: int)` | `Result` | `MemoryCuSection` | Sets UMA Frame Buffer (2G-8G, reboot required) |
| 24 | `game_profiles` | Game Profiles | Safe | `()` | `GameStore` | `GameProfilesSection` | Lists stored per-game configurations |
| 25 | `set_game_profiles_enabled` | Game Profiles | Safe | `(enabled: bool)` | `GameStore` | `GameProfilesSection` | Master switch for auto-applying game profiles |
| 26 | `save_game_profile` | Game Profiles | Safe | `(app_id, name, gpu, fan)` | `GameStore` | `GameProfilesSection` | Saves profile for specific Steam game |
| 27 | `remove_game_profile` | Game Profiles | Safe | `(app_id: str)` | `GameStore` | `GameProfilesSection` | Deletes profile for specific Steam game |
| 28 | `game_started` | Game Profiles | Safe | `(app_id, name, auto)` | `Result` | `GameProfilesSection` | Applies per-game settings on launch |
| 29 | `game_stopped` | Game Profiles | Safe | `(app_id: str)` | `Result` | `GameProfilesSection` | Restores default settings on game exit |
| 30 | `sample` | Diagnostics | Safe | `()` | `Result` | `LabSection` | Collects raw diagnostic log for troubleshooting |

---

## 2. Parity Status
100% of public endpoints in `main.py` are mapped into the native Steam Quick Access architecture.
