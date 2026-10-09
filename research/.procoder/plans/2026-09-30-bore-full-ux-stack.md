# BC250 full UX stack: Windows-host BORE and Mesa builds

## Scope
User requests latest stable CachyOS BORE, every BC250 UX improvement, Mesa Git async compute, installation on console, BORE default, removal of all other kernels except author's non-BORE BC250 fallback. Kernel, userspace, runtime SMU and firmware are separate layers; no silent narrowing to compatibility fixes.

## Anchor and existing work
Required build host Windows 127.0.0.1, console 192.168.1.245.
Prior plan 2026-09-22-kernel-pkgrel3.md documents WSL Arch builds, BORE+clang ThinLTO+Zen2, driver clock range, Wi-Fi/BT/modem modules and recovery gates. Its .74 address is historical and NOT a replacement for requested host.
Current console inventory: nonBORE 7.2.6-1.206, BORE-vcn 7.2.6-1.3, Mesa26.2.3 (32/64 bit), Limine12.5.2. These installed versions do not establish newest upstream stable.
Control Center 1.20.3 declared integration inventory: sibling JSON. Not a complete internet-wide BC250 patch catalog.

## Connected groups / use cases
- Kernel: BORE, BC250 amdgpu/GFX1013, matched metrics/VCN patches, ACPI, sensor modules, Wi-Fi/BT/modem compatibility.
- Userspace: Mesa/RADV async compute; matched lib32 builds; Steam/Proton/FSR4 options.
- Runtime: GPU governors (alternatives, cannot run simultaneously), CPU/CU controls, fan curves, GDDR6 SMU temperatures and VRAM settings.
- Hardware/firmware: VRM I2C requires wiring, BIOS variants/core unlock are not ordinary kernel patches.
- User experience: bootable gaming default, stable fallback, functional monitoring without fabricated readings.

## Checklist
- [x] Resolve authenticated access to .254 without exposing credentials; inspect WSL OS/CPU/RAM/disk and existing builds.
- [ ] Finish interview and have operator confirm plan, including experimental activation.
- [ ] Inspect primary upstream latest stable releases and pinned patch revisions.
- [ ] Build complete catalog including findings outside Control Center; classify every item included/conflict/incompatible/needs hardware/experimental.
- [ ] Derive kernel and Mesa patch compatibility matrix and explicit manifests.
- [ ] Set bounded Windows-host build resources; never build heavily on user's desktop/console inadvertently.
- [ ] Build native Arch packages and lib32 counterparts, verify hashes/config/patch coverage.
- [ ] Snapshot console boot/package state and preserve nonBORE fallback.
- [ ] Install side-by-side; verify initramfs/modules/Limine; approve reboot separately.
- [ ] Observe boot and game smoke with actual async behavior, sensors and stability evidence.
- [ ] Set BORE default; only then remove named redundant kernel packages.

## Open questions
Blocking: authenticated Windows access; default activation of experimental OC/unlocks; operator confirmation of final plan.
Non-blocking facts to research: latest stable version, actual complete patch set and mutual compatibility.

## Decisions
User rejected compatibility-only scope; wants full UX patch set.
Question asked: ship experimental OC/unlock support disabled by default (recommended) or activate? No response yet.
No build/install/removal/reboot performed.

## Operator clarification: maximum integration
Experimental OC/unlocks: include support, DISABLED by default (explicit operator decision). Maximize kernel-driver integration of suitable BC250 features. Investigate safe firmware load/probe/readback paths rather than promise volatile SMU code becomes persistent. For features that architecturally require userspace (Mesa, Proton, game profiles), use a coordinated install/configuration rather than falsely label them kernel code. New native drivers require a bounded specification, conflict/safety analysis and hardware verification. No zero-day exploitation, universal unchecked register-write interface, or bypass of hardware security. Resolve precise supported feature contracts before implementation; do not equate maximum functionality with removing validation.

## Source investigation result
MastaG dd840cb126f26d8874f85d905b60435e914bd6e4 explicitly builds stable, RC and stable-series BORE separately, with nct6687 as an in-tree-built module. Patched Mesa exposes GFX1013 async compute by default; mesa-git optional; directmesh opt-in. New sibling patch inventory contains 15 stable-kernel and 7 Mesa-git patches. This is not proof of compatibility, latest stable kernel version, or board stability; every patch still requires review and comparison with requested disabled experimental defaults. Latest GitHub release API returned unrelated fsr4-payload tag; must inspect repo release assets/fingerprints rather than infer kernel latest from that endpoint. Previous Windows WSL Arch build documented in project action log 2026-09-21, user builder, but current .254 auth remains denied; no remote host identity confirmed.

## Pinned BORE recipe check
CachyOS commit 41605bd4abb037b35fdf4f8a4b524644d66df689 declares stable BORE pkgver 7.2.8, pkgrel1 and scheduler bore. This is a source-recipe observation, not a completed build. MastaG BORE selects stable linux-cachyos patch set. 40CU support patch is disabled by default via zero-initialized module parameter, consistent with operator experimental-off decision; active kernel cmdline must still be audited before install. bash -n passed for 35 upstream shell scripts; only syntax checked, no build scripts executed. Authentication to required Windows .254 still denied.

## Live Windows access confirmed
Авторизованный поиск ключа завершен: kukuruza_laptop_ed25519 accepted на kukuruza@127.0.0.1; hostname kukuruza-pc. Секретные байты не читались/не печатались; SSH выполнил штатную authentication, authorized_keys не менялись. Live Windows inventory: Intel20C28T, RAM68399550464B (~64GiB), WSL2 archlinux Stopped. Блокер authentication снят. Сборка еще не запускалась; дальше проверить существующий WSL build workspace/toolchain/disk, закрепить исходники и безопасные build resource limits; сохранить весь UX scope и экспериментальные функции off.

## WSL build host inspection verified (127.0.0.1)
- Host: Intel 20C/28T, 64GiB RAM total, Windows 11 (hostname kukuruza-pc).
- WSL distribution: archlinux (WSL2), user builder.
- Storage: 949GiB free on /dev/sdd (1% used).
- Memory: 32GiB allocated to WSL VM (31GiB available).
- Toolchain: makepkg, clang, gcc, ninja present.
- Existing tree: ~/kbore with mastag git tree (commit 0697a5d), ccache enabled in .makepkg.conf. Prior pkgrel3 artifacts present in finished-packages/.

## Operator correction gate
No further full kernel compilation or console installation until requested missing driver/integration changes are implemented and verified, with an explicit coverage matrix. Preserve baseline package as evidence only, not final deliverable. Mesa candidate source prepared but build exit8 on dependency404; do not hide error.
