# Decky on BC-250: what it is and which repositories matter

Date: 2026-09-22
Scope: research only. No plugin installation or board change.

## Short answer

Decky Loader is a plugin framework for Steam Gaming Mode. The Home/Quick Access button opens Steam's side panel; the plug icon opens Decky and its plugins. Decky is not a governor and does not change BIOS by itself.

The BC-250-specific governor/tuning front end is **BC250 Tune** from `lethevimlet/lethe-bc250`. It exposes existing services from the controller panel. It can select GPU governor limits, UMA split, CU count, core unlock, fan curve, HUD and resolution. It does not provide physical MCLK/UCLK/FCLK control and does not provide a proven SoC-voltage setter.

The LSFG plugin is a separate component. **Decky LSFG-VK** from `xXJSONDeruloXx/decky-lsfg-vk` installs and configures the `lsfg-vk` Vulkan layer, per-game profiles and launch options. It is frame generation, not a governor and not a memory/BIOS tool.

## Repositories found

### 1. Decky Loader

URL: https://github.com/SteamDeckHomebrew/decky-loader

Official plugin loader. It adds a plug icon to Gaming Mode and provides the Quick Access UI, plugin backend and TypeScript/Python bridge. This is the base, not BC-250-specific.

### 2. BC250 Tune — recommended BC-250 control panel

URL: https://github.com/lethevimlet/lethe-bc250

Commit: `7cddcd185722b4972791193de9e2f63afb979f35`

Relevant paths:

- `decky-bc250-tune/decky-plugin/`
- `decky-bc250-tune/bc250-tune`
- `docs/tuning.md`

What the panel controls:

- GPU governor floor and ceiling, live;
- UMA/VRAM split, next reboot through CMOS;
- CU count, live;
- 6/8-core unlock, warm reboot;
- software fan curve;
- MangoHud HUD;
- Gaming Mode resolution.

The plugin is a front end for `bc250-tune`. It does not replace `cyan-skillfish-governor-smu`; it writes the governor range and calls the existing BC-250 tools.

Important limits:

- 40 CU and 8 cores are silicon-lottery features;
- 40 CU can add roughly 30 W according to the repository's own documentation;
- power must use EPS12V to 2× Micro-Fit, not one PCIe 8-pin cable;
- the project documents GPU clock readout corruption after 8-core unlock;
- the code does not expose MCLK/UCLK/FCLK or a verified SoC-voltage path.

### 3. BC250 Toolkit Decky — broader alternative

URL: https://github.com/Necrosiak/bc250-toolkit-decky

Commit: `10188021a6a9d55f2b7da7962b640633b9c8f5f8`

This plugin adds:

- game-specific launch-option database;
- Proton/GE-Proton selection;
- CU and UMA controls;
- core unlock;
- system/hardware status;
- optional BC250 Control Center integration;
- per-game recommendations.

Its UMA path writes EFI/NVRAM only on a whitelisted P3.00 layout and uses a root helper. That is a write path, not something to enable blindly on the current CachyOS/CLV BIOS. It is useful as a later Game Mode UI, not as the first governor component.

### 4. Decky LSFG-VK — frame generation

URL: https://github.com/xXJSONDeruloXx/decky-lsfg-vk

Commit: `e744826869cdf8711373a9a655e423fd8e79e654`

Plugin version: `0.14.4`.

It does the following:

1. installs the `lsfg-vk` Vulkan layer;
2. configures Lossless Scaling profiles;
3. adds per-game launch options;
4. supports Steam games and managed Flatpak targets;
5. exposes multiplier, flow scale, performance mode, FP16 and pacing options from Quick Access.

Requirements from its README:

- install Lossless Scaling from Steam;
- switch the application to its `lsfg-vk` beta branch;
- install the layer through the plugin;
- assign a profile to the game AppID.

The repo bundles a remote `lsfg-vk-2.0.0.tar.xz` with declared SHA-256 `08bdbdf373a111022df87dac7aa87e3b564bb841f961552e3ca85fea12b5aa74`. The plugin is unofficial community software.

Repository tests:

- TypeScript tests: 23/23 passed;
- Python tests: 52/52 passed with available `python3`;
- package script's `python3.12` phase did not run because `python3.12` is not installed in the research environment.

### 5. Decky Lossless Scaling legacy plugin

URL: https://github.com/xXJSONDeruloXx/decky-lossless-scaling

This is the older/smaller predecessor. Use `decky-lsfg-vk`, not this one, unless the current plugin cannot work with the installed Decky version.

## What “Decky Governor” means here

There is no separate magic “Decky governor” that replaces the BC-250 SMU governor. The useful chain is:

```text
Decky Loader
  -> BC250 Tune panel
      -> bc250-tune / cyan-skillfish-governor-smu / CU tools
```

For frame generation the chain is separate:

```text
Decky Loader
  -> Decky LSFG-VK
      -> per-game launch options
          -> lsfg-vk Vulkan layer
```

The two plugins can coexist. They solve different problems.

## Recommendation for this project

1. **Use `lethe-bc250` as the BC-250 control-panel reference.** It is the cleanest explanation of the Quick Access workflow and the existing governor boundary.
2. **Use `decky-lsfg-vk` for Spider-Man only after the base game works without frame generation.** Test native FPS and frametime first, then enable LSFG with a per-game profile.
3. **Do not install `Necrosiak/bc250-toolkit-decky` yet.** It has more features but also an EFI/NVRAM UMA helper and external BC250 Control Center dependency. Evaluate its exact OS/BIOS guards first.
4. **Do not treat Decky as the MCLK/UCLK/FCLK solution.** None of the three BC-250 plugins exposes a proven BIOS clock-domain actuator.
5. **Do not enable 40 CU, 8 cores, high GPU ceiling, LSFG and a new game profile simultaneously.** That would destroy causality and overload the board's power/thermal margin.

## Suggested staged test for the target game

- Stage D0: current board, no Decky changes, game at a fixed 60-FPS cap, record frametime and GPU/CPU clocks.
- Stage D1: install only Decky Loader + BC250 Tune, no OC change, verify read-only status panel.
- Stage D2: set only a conservative governor ceiling already proven on the board, then record the same scene.
- Stage D3: install Decky LSFG-VK and enable only a 2× profile for Spider-Man. Start with Performance Mode, FP16 only if the runtime exposes it correctly, no HDR, and no extra frame-generation multiplier until the base game is stable.
- Stage D4: compare native 30/40/60 FPS against generated output. Treat generated frames as smoothness, not as a latency reduction.

## Current decision

- Decky Loader: useful framework.
- BC250 Tune: best first BC-250 panel reference.
- Decky LSFG-VK: correct plugin for Lossless Scaling frame generation.
- Necrosiak Toolkit: powerful but later and more invasive.
- BIOS/SoC/MCLK/UCLK/FCLK: separate track, not solved by Decky.

No packages, services, plugins, BIOS images, NVRAM variables or board state were changed during this research.
