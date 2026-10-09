# BC250 Control Plane & Native Steam Quick Access Plugin — User Guide

## 1. Introduction

The BC250 Control Plane is an independent, native system management suite designed specifically for the AMD BC250 console running Linux (CachyOS BORE, SteamOS, Bazzite). It integrates seamlessly into Steam Game Mode's Quick Access Menu (QAM), adhering strictly to Steam's native design system and controller navigation standards.

## 2. Navigating the Quick Access Menu

To open the BC250 plugin:

1. Press the Quick Access button (`...` or `Home + A` on gamepad).
2. Navigate to the Decky Loader plug icon.
3. Select **BC250**.

All controls are fully navigable via gamepad D-pad (`Up/Down` to move, `Left/Right` for sliders, `A` to activate or toggle, `B` to cancel).

---

## 3. Sections & Features

### 3.1. Быстрые настройки (Quick Settings)

- **Kernel**: Displays current active kernel (e.g. `BORE 7.2.8-1.2-cachyos-bore-bc250`).
- **GPU Status**: Live GPU temperature in °C and utilization percentage.
- **CPU Status**: Live CPU temperature and clock frequency in MHz.
- **GDDR6 Memory**: Shows average and hotspot memory temperatures when sensors are active.
- **Refresh status**: Queries a fresh hardware snapshot.

### 3.2. GPU Management

- **GPU Profiles**: Select validated clock profiles:
  - _Battery_: Lower frequencies for low-power 2D/indie gaming.
  - _Balanced_: Default everyday gaming profile.
  - _Performance_: Sustained high clock frequency.
  - _Maximum_: Full uncapped clocks for heavy titles.
- **Governor service**: Toggles the background GPU governor service (`cyan_skillfish`).
- **High frequency points**: Toggles experimental upper frequency points (requires confirmation).

### 3.3. CPU Management

- **Frequency**: Clamped slider from 3100 MHz to 4200 MHz (step 50 MHz).
- **VID**: Clamped slider from 950 mV to 1325 mV (step 5 mV).
- **Apply CPU profile**: Programs selected frequency and voltage.
- **Scale**: Clamped slider from -50 to 0 for temporary clock scaling.
- **Apply temporary scale**: Applies quick scaling adjustment.

### 3.4. Cooling (Охлаждение)

- **PWM Slider**: Set manual fan percentage (20% to 100%, step 5%).
- **Apply manual speed**: Engages manual PWM. The fan arbitration engine automatically pauses conflicting background fan services so the setting holds firm.
- **Return to automatic**: Hands control back to the system fan service.
- **System Presets**: Instant one-click presets:
  - _Quiet Preset_: Low noise ceiling for desktop or media.
  - _Balanced Preset_: Standard fan curve.
  - _Boost Preset_: Aggressive curve for demanding 3D games.

### 3.5. Game Profiles (Игровые профили)

- Automatically detects the active running game (`app_id` and game title).
- Allows assigning a dedicated GPU profile and fan preset per game.
- Automatically applies settings when the game starts.
- Restores prior hardware states immediately when the game closes.

### 3.6. Memory (Память)

- **VRAM Status**: Real-time display of used and total video memory in MiB.
- **VRAM Preset**: Slider from 2 GiB to 8 GiB (step 1 GiB).
- **Apply VRAM preset**: Stages the memory reservation in boot configuration; clearly notifies that a reboot is required.

### 3.7. Advanced & Laboratory Settings

- **Compute Units (CU)**:
  - Live readout of active compute units (e.g. `40 CU`).
  - _Enable 40 CU mode_: Live-routes 40 CUs via SPI register mask without rebooting.
  - _Apply validated CU table_: Direct application of verified topology mask.
  - _Save validated CU table_: Persists the current live topology.
  - _Install / Remove CU service_: Manages boot-time CU persistence.
- **Voltage Controls**: Apply validated GPU safe points and voltage levels.
- **CPU Services**: Install or remove persistent CPU clock service.
- **GDDR6 Sensors**: Manual SMU query for memory temperature readout.

---

## 4. Safety & Recovery

- All dangerous actions are protected by modal confirmation dialogs.
- Background services are gracefully arbitrated to prevent race conditions.
- Fallback kernel (`linux-cachyos-bc250`) is always preserved in bootloader.
