# Native read-only APU telemetry slice

Scope: integrate one telemetry component into existing AMDGPU kernel driver. Full BC250 feature scope remains in coverage matrix.
Anchor: amdgpu_pm.c existing amdgpu_get_gpu_metrics(), amdgpu_pm_sysfs_init/fini() in pinned kernel7.2.8 source.
Use case: expose CPU per-core telemetry alongside APU power fields without privileged userspace parsing or new hardware transactions.
Contract: BC250 PCI0x13fe only, bare metal only, read-only sysfs, driver PM get/put balance, canonical gpu_metrics_v2_2 size and revision required. Values named raw; no unproven conversion or fake zero substitution. 0xffff is unavailable; power0xfffe also unavailable. No arbitrary mailbox or register API.
Checklist: modified copy; reconstructing diff; original hash; baseline/modified/rollback parser-hook fixture with literal outputs; malformed/wrong-revision/other-device tests; actual kernel translation-unit compile using original Kbuild flags to new output; original source unchanged; review before kernel rebuild.
Open: actual hardware reads after accepted installation; consumers still need endpoint adaptation; GDDR6 native memory monitor and other control functions are separate unimplemented requirements.
Decision: no firmware payload loading or activation, no OC, no hardware writes. Source compile is not runtime or boot proof.
