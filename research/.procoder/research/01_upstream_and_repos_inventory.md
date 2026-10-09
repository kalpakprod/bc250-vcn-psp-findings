# Worker 1: Upstream & Community Repositories Research Inventory

**Date:** 2026-10-01
**Target:** AMD BC-250 (Cyan Skillfish / gfx1013) Ecosystem
**Status:** Verified via GitHub CLI, commit logs, and local source trees.

---

## 1. Upstream & Sibling Repositories

### 1.1 `movacx/bc250-control-center`
- **Owner:** movacx
- **License:** MIT
- **Architecture:** Desktop GTK/Python GUI + root helper (`bc250-helper`) via Polkit / systemd.
- **Key Features:**
  - Monitoring: GPU clock, temperature, busy %, VRAM usage, GDDR6 8-channel temperatures via SMU mailbox.
  - GPU Tuning: `pp_od_clk_voltage` / SMU clock-voltage curves, safe point ceilings, governor service (`cyan`/`oberon`).
  - CPU Tuning: SMU core frequency override, VID table, manual scale.
  - Compute Units: UMR-based routing, live mask switching, systemd boot service (`bc250-cu.service`).
  - Fan Control: PWM direct writes to NCT6687 hwmon (`pwm2`), presets (`quiet`, `balanced`, `boost`), automatic mode.
  - VRAM: UMA frame buffer configuration via CMOS / NVRAM.
  - Game Profiles: AppID-matched launch options and profiles.
- **Limitations:** Primarily desktop-oriented. Decky component was an embedded web-view/quick wrapper, not a native Steam QAM plugin.

### 1.2 `Necrosiak/bc250-toolkit-decky`
- **Owner:** Necrosiak
- **License:** MIT
- **Architecture:** Monolithic Decky Loader plugin (`src/index.tsx`, 83KB) + Python backend (`main.py`, `bios_uma.py`, `updater.py`).
- **Key Features:**
  - 8-core unlock via rw-r-r-0644 SMU queue-3 write integration.
  - UMA Frame Buffer (VRAM) preset management.
  - Per-game fixes database (`games_db.json`) with RADV overrides (`~/.drirc`).
  - Multi-distro compatibility (SteamOS, Bazzite, CachyOS, Arch).
- **Limitations:** Monolithic React frontend; non-standard UI patterns that cause visual clutter in Quick Access Menu.

### 1.3 `xXJSONDeruloXx/decky-lsfg-vk` (Reference for Native UX)
- **Owner:** xXJSONDeruloXx
- **License:** GPL-3.0
- **Architecture:** Highly modular native Decky plugin:
  - `src/components/ConfigurationSection.tsx`
  - `src/components/CollapsibleItemGroup.tsx`
  - `src/components/SettingsTab.tsx`
  - `src/components/BranchSetupModal.tsx`
- **Key Features & UI Standards:**
  - Uses `@decky/ui` standard primitives: `PanelSection`, `PanelSectionRow`, `SliderField`, `ToggleField`, `ButtonItem`, `Field`, `ModalRoot`, `showModal`.
  - Zero custom card containers, zero custom CSS wrappers.
  - 100% controller-navigable focus ring and D-pad event bubbling.
  - Clean separation of UI state from background polling.

### 1.4 `duggasco/bc250-40cu-unlock` & `WinnieLV/bc250-cu-live-manager`
- **Features:** 40 CU unlock via UMR registers and SMN bitmask routing (`[31, 31, 31, 31]` across 4 shader engines).
- **Verification:** Live mask readback vs driver boot map. Driver boot map remains 24 CU unless patched at boot time. Runtime routing delivers extra CUs for compute.

### 1.5 `simpmix/bc250-encoding-decoding-fix` & `DryhoppedIPA/bc250-gfx1013-fix`
- **Features:**
  - VA-API video driver via Vulkan compute shaders for H.264 encode/decode.
  - Kernel + Mesa/RADV async compute queue fixes (~20% FPS uplift).

### 1.6 `MastaG/linux-cachyos-bc250`
- **Features:** CachyOS Linux kernel with BORE scheduler, Zen2 optimizations, Clang/ThinLTO, NCT6687 sensor module, and 15 BC250 cherrypicks.

---

## 2. Licensing & Provenance Verdict
All examined tools use permissive MIT or GPL licenses. Our project is an independent clean-room implementation with native Steam UI, strict command allowlisting, and robust fan arbitration.
