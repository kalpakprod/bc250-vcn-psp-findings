# Driver startup contract audit

## Intent

Root traces the retained VCN startup sequence and Cyan Skillfish callbacks,
offline only, to identify a missing prerequisite before the first VCN access.
This source audit does not modify Linux, firmware or board registers.

## Observed source

`recon/vcn-source-context/drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c`
SHA-256 b25b189db07741f786c4918ba1e407ae8cc9ab3290ed8feefc771028f43064d0:
vcn_v2_0_start invokes amdgpu_dpm_enable_vcn when dpm_enabled, chooses DPG
when flagged, otherwise disables static power gating. The non-DPG helper
writes PGFSM_CONFIG before polling PGFSM_STATUS and later reading POWER_STATUS.
Thus a userspace baseline requiring all named MMIO reads to succeed before
any PGFSM write does not reproduce the standard driver ordering.
This is not authorization to blindly write an inaccessible register.

`recon/cyan_skillfish_ppt.c`
SHA-256 9259ad3ff6f660fe97ca7ea68f9b7e5f5d185982f0d3341180bd880442f030f1:
the message map includes no VCN power command, and the local pptable_funcs
initializer has no VCN-specific power callback. The shared framework's exact
fallback and installed custom module behavior remain unknown.

## Consequence

Two checks remain distinct: restore a valid precondition for MMIO access,
and execute the driver's actual tile-power/clock/reset/start sequence.
All-ones before the initial PGFSM write does not alone prove failure of
that full startup sequence; conversely driver hangs are not dismissed by
this observation. Identify the installed module's first failing instruction
and actual DPG/static path before designing a new hardware test.
Linux source files here are retained comparison inputs, not proof of the
currently installed binary. Board remains unavailable from the last SSH check.

## Shared fallback resolved for public v6.8 source

Read-only source comparison retrieved from torvalds/linux tag v6.8,
drivers/gpu/drm/amd/pm/swsmu/amdgpu_smu.c and
drivers/gpu/drm/amd/pm/swsmu/smu11/cyan_skillfish_ppt.c.
The initially tried swsmu/ppt/cyan_skillfish_ppt.c URL returned404;
the smu11 path returned the actual source. No external code executed.

smu_dpm_set_power_gate routes UVD/VCN requests to smu_dpm_set_vcn_enable.
That function returns zero immediately if ppt_funcs->dpm_set_vcn_enable
is NULL, before issuing hardware commands or updating vcn_gated.
The same-version Cyan Skillfish initializer contains no such callback.
Therefore that public driver path can report success without performing
a VCN enable transaction. It is a missing implementation/fallback behavior,
not a discovered PSP bypass or proof of the installed custom driver's behavior.

Practical consequence: future validation must observe actual clock/power
state or a traced command; a successful generic DPM return is insufficient.
The installed 7.2.0-1.92 code may differ and needs exact binary/source audit.

## Imported custom patch coverage

Read-only audit of retained patches0009/0010/0011; no application or build.
0011 SHA-256274f7dbc060e5b36e17843e35e1ef457efb4d4ed509f0a6ad735a8ce833b074b:
mode1 registers probe-only callbacks, num_enc_rings=0, and no-op hardware,
clock/power callbacks. Mode2 registers actual VCN/JPEG IP blocks. Its helper
amdgpu_vcn_fw_is_psp returns false for the scoped Cyan Skillfish2/13fe/2.0.3
case in modes1/2, covering software allocation, copy, PSP setup and MC windows.
None of these three patches adds a Cyan Skillfish DPM VCN power callback.
0009 selected navi10_vcn and originally documented global fw_load_type=0;
0011 supersedes that with VCN-specific placement. Do not prescribe global
fw_load_type=0 from the obsolete0009 instructions.

Consequences: mode1 boot is intentionally not a functional codec test;
source patch coverage suggests a missing DPM implementation but does not
prove installed module identity. A focused filename scan found no loose
amdgpu.ko[.zst/.xz/.gz] or matching1.92 package in project/import outputs.
The board's actual binary/build provenance remains a required retrieval.

## Goal checkpoint: blocked on target evidence

Repeated read-only SSH identification again returned No route to host.
The same missing input has persisted across more than three continuation
turns: current board state and access to its actual module and September12
experiment artifacts. Loose-file and three relevant archive checks did not
recover those artifacts. Public-source fallback and retained-patch auditing
are complete within their stated comparison scope and cannot validate the
installed kernel or prove a hardware unlock.

Mark the goal blocked, not complete. The objective remains working VCN with
verified operation; no claim of impossibility or exhaustive firmware analysis.
Resume after operator supplies present power/programmer/BIOS state and a
reachable Linux session or an offline copy of the specified target evidence.
No blind boot, flash, MMIO read, or mailbox replay is requested by this entry.

## Target evidence retrieval correction

The target-evidence blocker above is superseded. After operator power-on, mode1 became reachable and the exact running module was copied read-only to `evidence/runtime/20260914-board-retrieval/amdgpu-7.2.0-1.92.ko.zst`.

Direct module facts: compressed SHA-256 `7424913c4864079865e8f792a54edc9c3d6a1bb1997ca0a916072e988d7dea40`; decompressed SHA-256 `7d6606ba80be79e49bb703f29b79a22fcc4b96d8c51b7799bf694f4d417d1ebf`; build ID `ca6bb73e0c93d32f1c80552e5093e7a766a3c924`; vermagic `7.2.0-1.92-cachyos-vcn-bc250 SMP preempt mod_unload`. Static strings confirm the custom mode parameter, probe functions, and VCN firmware declarations.

This closes binary provenance, not source provenance or first-failing-instruction attribution. Next offline step is function-level comparison of the exact module against retained patch 0011/public source. No live mode2 or hardware probe is authorized by this retrieval.
