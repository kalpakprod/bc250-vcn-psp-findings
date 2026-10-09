# Worker 10: System Integration Guide, Operational Documentation & Release Gates

**Product:** BC250 Control Plane & Native Steam Quick Access Plugin
**Architecture:** Independent System-Level Control Stack for AMD BC-250

---

## 1. System Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                 Steam Gaming Mode (Gamescope)               │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │        Native BC250 Quick Access Plugin (React)     │   │
│   │   - OverviewSection (Telemetry, GDDR6, BORE status) │   │
│   │   - GpuSection (Profiles, Safe Points, Governor)    │   │
│   │   - CpuSection (Freq, VID, Scale, Service)          │   │
│   │   - CoolingSection (Arbitrated Fan PWM, Presets)    │   │
│   │   - MemoryCuSection (VRAM Presets, 40 CU Routing)   │   │
│   │   - GameProfilesSection (Per-game Auto Apply/Reset) │   │
│   │   - LabSection (Raw Sensors, Voltage Offsets)       │   │
│   └──────────────────────────┬──────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────┘
                               │ Decky RPC (callable)
┌──────────────────────────────▼──────────────────────────────┐
│             Decky Backend Service (main.py)                 │
│   - Operation Lock & Single-Flight Execution                │
│   - Typed Argument Validation & Error Mapping               │
│   - Hardware Readback & Transaction Verifier                │
└──────────────────────────────┬──────────────────────────────┘
                               │ Root Execution / Helpers
┌──────────────────────────────▼──────────────────────────────┐
│           Privileged System Layer (Arch / CachyOS)          │
│   - NCT6687 hwmon (PWM Fan Arbitration vs bc250-fan.service)│
│   - AMDGPU sysfs (pp_od_clk_voltage, power_profile, drm)   │
│   - UMR / SMN Direct Mailbox (40 CU Routing, GDDR6 Sensors) │
│   - UEFI / CMOS NVRAM (UMA Frame Buffer VRAM Size)          │
│   - Systemd Services (bc250-cu.service, governor.service)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Seven Release Gates Audit

| Gate | Title | Requirement | Verification Artifact | Status |
|---|---|---|---|---|
| **Gate 1** | Research Complete | All repos, community chats, and patches mapped | `.procoder/research/01_*.md`, `02_*.md` | **PASSED** |
| **Gate 2** | Contract Complete | Unified data contract, ranges, readback types | `candidates/bc250_control_plane/contract.py` | **PASSED** |
| **Gate 3** | Parity Complete | 100% callable endpoints mapped and implemented | `.procoder/research/03_full_parity_matrix.md` | **PASSED** |
| **Gate 4** | Native UX Complete | Modular `@decky/ui` components, zero custom CSS | `candidates/bc250-quick-access/src/` | **PASSED** |
| **Gate 5** | Safety Complete | Fan arbitration, failsafe floors, safe defaults | `candidates/bc250-fan-arbitration/fan_policy.py` | **PASSED** |
| **Gate 6** | Verification Complete | All tests passing, clean TypeScript/Rollup build | `.procoder/research/08_*.md` | **PASSED** |
| **Gate 7** | Deployment & Rollback | Atomic packaging, checksums, safe rollback runbook | `.procoder/research/09_*.md` | **PASSED** |

---

## 3. Conclusion
The BC250 Control Plane and Native Steam Quick Access Plugin have reached the release candidate stage. All 10 subagent responsibilities have been executed, verified, and documented.
