# BC250 graphics stack audit, 2026-09-23

Read-only SSH audit of steammachine@192.168.1.118. No cleanup executed.

## Confirmed

- System vulkan-radeon3:26.2.3-1 and lib32-vulkan-radeon3:26.2.3-2: pacman-Qkk12/12 and7/7 files,0altered.
- Unmanaged /opt/bc250-gfx1013/v3.3.0/lib/libvulkan_radeon.so: sha256538731cb60c2e1ad43be951ed20760d3eab60ad8c683a7bcc34d7757446811c1; embedded build paths mesa-26.2.0-rc3. Whole/opt tree22MiB. Package manager owns neither this library nor routingconf files.
- Active /etc/environment.d/60-bc250-gfx1013.conf and /home/OWNER/.config/environment.d/60-bc250-gfx1013.conf set bothVK_DRIVER_FILES andVK_ICD_FILENAMES to/opt.
- systemctl--user show-environment and liveSteam environment confirm bothvalues. Earlier gamePID81330 maps andcontainerICD confirm/opt64bitdriver actually loaded;32bitICD routes systemlib.
- docs/action-logs/2026-09-22-unpin-opt-mesa.md disabled onlyprofile.d script. System/userenvironment.d remained active. FreshSSH version was not validation ofSteam.
- pacman history: Sep22systemMesa patched1.1/2.1,17:29MastaG1.186/2.186,19:48stock1/2. Switching installedpackages did not override inherited/opt selection.
- MultipleProton tools: packageprotonge-latest-bc25011.7-185,proton-cachyos-slr; userGE-Proton11-3,UMU-Proton-10.0-4,LegacyRuntime. Coexistence alone is notfault or permission todelete.
- protonge-latest-bc250 has1alteredfile: currenttask's scopedwrapperpatch, withpermissions/mtime/size/hash discrepancies. Must migrate intendedbehavior into reproduciblepackage or per-gameconfiguration; update can overwrite patch.
- Twoinstalledkernels:bc2507.2.6-1.206 andexperimentalbore-vcn7.2.6-1.3. Backupkernel notautomaticallytrash.
- lib32-opencl-mesa2.1 remains amidstockMesa2;OpenCL is nottheobservedVulkan route, noFPS attribution.

## Proposed recoverable cleanup

First disable exactlythetwoactiveenvironment.dconf files by descriptive rename,retain/optbaseline. Clear inheriteddriverselection only during agreedfullsessionrestart,notkillplayinggame. Verify newSteam environment andactualgamemaps pointtosystemlib. Only aftersame-scenetest considerarchiving/opt. Do not deleteProtonprefixes,saves,shadercaches,backupkernel,orallVulkanICDs.
No claim thisalonefixes10FPS. PendingruntimeA/B,FOVrestorationandframe-time capture retained.
