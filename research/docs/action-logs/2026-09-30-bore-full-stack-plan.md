# Full BC250 UX build planning

Intent: create auditable inventory and build plan from installed Control Center 1.20.3 integration manifest and existing pkgrel3 plan; do not build, install, flash, remove packages, restart or activate experimental settings. Preserve other tasks and existing edits.
Target console 127.0.0.1; required Windows build host 192.168.1.254.
Result: created .procoder/plans/2026-09-30-bc250-control-center-integrations.json and .procoder/plans/2026-09-30-bore-full-ux-stack.md; inventory reopened/parsed successfully. Contains 12 declared integrations only, not a false complete patch claim. Build host reachable but authenticated access denied (exit255) on default and homelab keys. No new build launched.

Intent: record operator decisions about maximum kernel integration and disabled experimental controls; no source/build/hardware change.

Intent: extend inventory with exact MastaG commit dd840cb126f26d8874f85d905b60435e914bd6e4 source hashes. Upstream is data, no external scripts executed. Two guessed API PKGBUILD paths returned HTTP404/base64 decode errors; corrected by cloning/listing actual tree.

Intent/result: append verified recipe/syntax observations; no build execution or hardware change.

## Pinned BORE recipe check

CachyOS commit 41605bd4abb037b35fdf4f8a4b524644d66df689 declares stable BORE pkgver 7.2.8, pkgrel1 and scheduler bore. This is a source-recipe observation, not a completed build. MastaG BORE selects stable linux-cachyos patch set. 40CU support patch is disabled by default via zero-initialized module parameter, consistent with operator experimental-off decision; active kernel cmdline must still be audited before install. bash -n passed for 35 upstream shell scripts; only syntax checked, no build scripts executed. Authentication to required Windows .254 still denied.

## Access resolved with operator-approved key search

Авторизованный поиск ключа завершен: kukuruza_laptop_ed25519 accepted на kukuruza@127.0.0.1; hostname kukuruza-pc. Секретные байты не читались/не печатались; SSH выполнил штатную authentication, authorized_keys не менялись. Live Windows inventory: Intel20C28T, RAM68399550464B (~64GiB), WSL2 archlinux Stopped. Блокер authentication снят. Сборка еще не запускалась; дальше проверить существующий WSL build workspace/toolchain/disk, закрепить исходники и безопасные build resource limits; сохранить весь UX scope и экспериментальные функции off.

## WSL build environment inspection event

Intent: inspect WSL2 archlinux environment, storage, memory, toolchain, and existing build tree on 127.0.0.1 without launching heavy compilation or mutating configuration.
Command: ssh -i ~/.ssh/kukuruza_laptop_ed25519 kukuruza@127.0.0.1 "wsl -d archlinux -u builder ..."
Observed result:

- OS: Arch Linux under WSL2.
- User: builder (uid 1000).
- Toolchain: makepkg, clang, gcc, ninja verified installed.
- Storage: /dev/sdd has 949 GiB free (1% utilized).
- Memory: 32 GiB RAM allocated to WSL VM, 31 GiB currently free.
- Build directory: ~/kbore with existing mastag clone at commit 0697a5d, active ccache configuration, and completed pkgrel3 artifacts.
- No compilation started, no files modified on host, no credentials leaked.

## Build candidate launch intent

Windows .254 authenticated. WSL Arch builder uid1000 confirmed, 949G available, ~31GiB memory; clang/llvm/lld/ccache available. Create NEW /home/OWNER/bc250-ux-build-20260930, never touch /home/OWNER/kbore. Candidate BORE7.2.8, MastaG15 stable patches, nct6687 pinned5f12dd1b0b3c8f79f31d309749862d986ff9efa7. Pin CachyOS recipe41605bd4abb037b35fdf4f8a4b524644d66df689. clang ThinLTO, generic_v3+Zen2 tune, -j8 low priority. No PGP/checksum bypass. This is an intermediate full upstream kernel candidate, NOT proof that all Control Center features have been integrated. Maximum-runtime-driver integration remains a separate design/audit gate. No console install or kernel deletion.
Read-only delegated audit: explorer backend returned402; Gemini report missing required receipt and did not perform assigned audit, not accepted as evidence. Receipt retry dispatched to DS4.

## Observed build stop and narrow repair intent

Runner terminated BUILD_EXIT=1. makepkg literal: Integrity checks (b2) differ in size from the source array. Cause: requesting ThinLTO adds dkms-clang.patch to BORE recipe source, but BORE checksum list covers non-LTO inputs only. No bypass. Primary same-commit CachyOS default recipe independently declares dkms BLAKE2 c992567bd7dd8553432be496ffa1c17e2f5ebe9c7edb51945cf977e1b742dd6517c210d8843bb82744ca705efd07f8027cd7dde41b50215ebd707a34aa81462e; primary kernel-patches copy independently matches it. Add that exact checksum in source order only when LTO is selected. Preserve baseline recipe, patch, verification and rollback roles; verify array shape and rollback before resume same build workspace. Prior source downloads retained.

## Live build verified

Сборка реально запущена на Windows.254 WSL Arch в /home/OWNER/bc250-ux-build-20260930. Контроллер tty7 pane302 tab2a847f1d-02c6-4a5a-b760-784473a973c8; SSH held open; завершение доставляется codex queue. Первоначальный runner exit1: BORE ThinLTO checksum-array-size mismatch. Исправление на копии сохраняет PGP и все checksum checks: baseline21sources/20hashes exit1; modified21/21 exit0; rollback21/20 exit1 и original hash restored. Resume1 текущий makepkg PID33; реальные CC compilation events. gpg signature и все20 содержательных checksum checks Passed. Config CC_IS_CLANG=y,SCHED_BORE=y,LTO_CLANG_THIN=y,SENSORS_NCT6687=m. Будущий completion читать resume1.exit/packages.sha256, не запускать duplicate. Это intermediate upstream candidate, Mesa и максимальная интеграция runtime features еще не завершены. Консоль не менялась. Агенты audit недоступны (402 либо invalid receipt), их ответы не приняты. Windows quote readback failed exit255 then corrected command exit0; error retained.

Initial runner exit notification audited: build.exit1 is old checksum-array mismatch. Resume1 verified live PID33, current CC output, no resume1.exit. No restart or duplicate job.

## Full CPU authorization and scope correction

User explicitly permits full Windows CPU use. Observed makePID6536 argv -j28, WSL nproc28: prior -j8 makepkg config was overridden by PKGBUILD explicit nproc. Earlier limited-load statement corrected and recorded in MISTAKES.md. Intent: remove nice10 only for descendants of this exact makepkgPID33, not unrelated processes. Never restart for concurrency change.
Scope correction: running build contains upstream MastaG15 BC250 patches plus pinned nct6687/BORE/ThinLTO, not newly developed ControlCenter-runtime integration. It is intermediate; no install or completion until requested missing integration is resolved and reviewed.

Result: Полная CPU нагрузка разрешена и подтверждена: make explicit-j28, nproc28. Снят nice10 только для дерева существующей makepkgPID33,6 live processes reprioritized; unrelated processes untouched. Предыдущее заявление -j8 неверно из-за PKGBUILD override, занесено в MISTAKES. Реальный набор текущей сборки =15 upstream BC250 patches: telemetry8core-layout/GPU activity, nct6687, PASID TLB, compute gfxoff guard, KFD runlist TLB, TTM null page guard, SCLK range350..2230, opt-in40CU, HDMI21 PCON, DCN201DSC, relink after blank, opt-inCH7218 quirk, CH7218DSC restore, experimental off PCONforceDSC, PSP/CCP normal driver bind/null checks. Plus BORE/clangThinLTO/Zen2 tuning. Новых драйверных интеграций runtime ControlCenter НЕ разработано, кандидат не полный заказ. Не выдавать его за финальный и не устанавливать как финал без scope completion. Mesa пока не запущена. Продолжить отдельный feature-integration work после сохранения baseline candidate. Four repair roles reopened; BASELINE21/20exit1 MODIFIED21/21exit0 ROLLBACK21/20exit1/hashoriginal remain observed.

## Built kernel package verification

```
COMMAND ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'IdentitiesOnly=yes', '-i', '/home/OWNER/.ssh/kukuruza_laptop_ed25519', 'kukuruza@127.0.0.1', 'wsl.exe -d archlinux -u builder -- python3 /mnt/c/Users/kukuruza/bc250-verify-kernel-packages.py']
STDOUT
PACKAGE linux-cachyos-bore-bc250-7.2.8-1.1-x86_64.pkg.tar.zst NAME ['linux-cachyos-bore-bc250'] VERSION ['7.2.8-1.1'] ARCH ['x86_64']
NCT6687 ['usr/lib/modules/7.2.8-1.1-cachyos-bore-bc250/kernel/drivers/hwmon/nct6687.ko.zst'] OLD_NCT6683 []
SHA256 a20f19c6f5f9f63aae978e7e85f9a3fd8db18e365be56d201fc4f0d64146394b
PACKAGE linux-cachyos-bore-bc250-headers-7.2.8-1.1-x86_64.pkg.tar.zst NAME ['linux-cachyos-bore-bc250-headers'] VERSION ['7.2.8-1.1'] ARCH ['x86_64']
HEADERS_CONFIG CONFIG_CC_IS_CLANG=y
HEADERS_CONFIG CONFIG_SCHED_BORE=y
HEADERS_CONFIG CONFIG_LTO_CLANG_THIN=y
HEADERS_CONFIG CONFIG_SENSORS_NCT6687=m
SHA256 714d3dd05a258516c315d12ac44be3a43f614f19be345990883bda42236a34d5
STRUCTURAL_VERIFICATION_PASS; boot and game behavior remain UNTESTED
STDERR
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
EXIT 0
```

Intent: correct project gate after operator scope correction; no build/install/hardware action.
Result: Коррекция пользователя принята как возврат к исходной цели, а не новая цель. Поручение простое: устранить подмену результата upstream сборкой. Факт проверен: собран только upstream15, собственные ControlCenter integration patches отсутствуют. Не запускать следующую полную kernel сборку до реализации/проверки согласованных missing integrations. Не устанавливать baseline кандидат на консоль. Mesa preparation создала candidate, makepkg завершился exit8 из-за lib32-libunwind404; compile не началась, missing dependency result сохранен. Вводится явный gate: runtime features перечислены с исходниками, driver/user-space/hardware disposition, experimental-off defaults, реализованные изменения и тесты, несовместимости сообщаются до сборки. Функциональную цель не сужать; zero-day/security-bypass компоненты остаются за границей допустимого объёма как уже сообщено.

## Coverage gate

Created and reopened /home/OWNER/orca/projects/bc250/.procoder/plans/2026-09-30-bc250-coverage-matrix.json rows=12 sha256=0d5bdaaf0bc04aa84ece37bb8ea9443cac0452a0c388e49086bbf46cc4acbac1. This is a scope gate, not an implementation claim. Current missing work includes Mesa, userspace packaging, runtime integration design, and validation. Baseline kernel remains evidence only; no install/removal.

## Mesa dependency repair intent

Mesa candidate stopped exit8 because WSL's package indexes reference removed lib32-libunwind1.8.2 archive (HTTP404). On dedicated Windows.254 WSL Arch build environment only, inspect lock/process state then perform signed full pacman sync+upgrade (not -Sy partial upgrade), preserving keys/signature policy and console state. This is build-environment dependency maintenance authorized by requested Windows-host build; no Windows reboot, WSL shutdown or console installation. Record actual exit/log; do not resume full kernel compilation.

## New progress / existing scope gate retained

Новый executed result: coverage matrix17 требований создана и проверена schema/unique. Kernel scope gate остается: не пересобирать неизмененный baseline, не ставить его как полный результат. На Windows WSL исправлены outdated dependency indexes через signed full pacman-Syu, exit0; post-hook tmpfiles warning readonly /tmp/.X11-unix сохранен, не объявлен clean hardware gate. Mesa resume1 реально запущен в новой собственной tty7 pane307, source fetching event и SSH PID573825 наблюдены. Current Mesa still not compiled. Make test repo contour PASS (не доказательство kernel/Mesa hardware). Обязательства kernel-native/runtime integration остаются невыполненными; zero-day bypass исключен явно ранее, не обещать. Console untouched.

## Native telemetry implementation intent

Bound source: pinned kernel drivers/gpu/drm/amd/pm/amdgpu_pm.c, copied to local disposable native-telemetry directory; original kernel tree and packages stay unchanged. Add read-only BC250 APU telemetry sysfs endpoint using existing amdgpu_dpm_get_gpu_metrics and PM access guard. No custom mailbox, register writes, firmware payload, debug unlock, OC or arbitrary access. Reject non-BC250 PCI identity and unsupported/malformed v2.2 metrics, keep missing values explicit. This is one missing native integration slice, NOT full requested integration and NOT GDDR6 chip temperature driver. Validate portable callback tests and real kernel compile before adding to kernel patch manifest; do not rebuild kernel or install it in this step.

MESA_COMPLETION_NOTIFICATION_VERIFICATION
COMMAND ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'IdentitiesOnly=yes', '-i', '/home/OWNER/.ssh/kukuruza_laptop_ed25519', 'kukuruza@127.0.0.1', 'wsl.exe -d archlinux -u builder -- bash -lc "cat /home/OWNER/bc250-ux-build-20260930/mesa-git/resume1.exit; tail -8 /home/OWNER/bc250-ux-build-20260930/mesa-git/resume1-controller.log; cd /home/OWNER/bc250-ux-build-20260930/mesa-git/build; sha256sum -c ../packages.sha256"']
STDOUT
0
{
"package": "mesa-git",
"archive": "mesa-git-26.3.0_devel.230555.cec59b29970-1-x86_64.pkg.tar.zst",
"library": "usr/lib/libvulkan_radeon.so",
"sha256": "c427e899af2b1956ed5b67af4a7e18092c3cf02a5543b92b1739a66a53986460"
}
]
MESA_GIT_64_32_PACKAGES_VERIFIED
./lib32-mesa-git-26.3.0_devel.230555.cec59b29970-1-x86_64.pkg.tar.zst: OK
./mesa-git-26.3.0_devel.230555.cec59b29970-1-x86_64.pkg.tar.zst: OK
STDERR
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
EXIT 0

## Native patch candidate validated

Copied native telemetry diff to candidate /home/OWNER/.cache/bc250-bore-full-stack/native-telemetry/0016-bc250-apu-metrics-readonly.patch sha256=6c772efa2b5301a7d4eab006f199988f0681f63d0f1faa8db9d2dfc15277122d. Uploaded copy to Windows and ran git apply --check against the pinned kernel source: exit0. Candidate is not yet in the build recipe and does not change existing package.

## Source candidate integration event

Продвижение: новый source-only kernel candidate kernel-with-0016/7.2.8-1.2 подготовлен на Windows с16patches,0016 содержится в PKGBUILD и hash-checkOK. Initial prep command exit12 из-за makepkg--printsrcinfo из неправильногоcwd; исправлено cdexistingcandidate, no reset/recreate; metadata queryexit0. ThinLTOchecksumfix надо перенести в новую рецептуру до любых full builds. Native transaction проверен однимfixtureкомандой: BASELINE absentexit3, MODIFIED readonly/raw/errorguard PASS exit0, ROLLBACK absentexit3 иoriginalhash equality; новаякопия осталась измененной. Actual kerneltranslation compile ранееexit0. Это не аппаратнаявалидация, не весь scope, full build/installне выполнены.

## Candidate checksum repair correction

Initial continuation inspection reused existing candidate. First repair attempt incorrectly prepended the DKMS checksum unconditionally; non-LTO test reported sources21/checksums22 and AssertionError exit1. Inspected actual arrays; restored pristine prepared PKGBUILD from sibling backup (normal mode21/21,0016 hashOK). A tools.exec typo produced JS TypeError without command execution; corrected to exec_command. Apply the previously tested conditional LTO insertion before the BORE checksum, not unconditional prepend. Verify both non-LTO and ThinLTO shape and DKMS source/hash alignment. Preserve failed records, no build/install.

## Candidate ThinLTO correction and ACPI disposition

Продолжение: prepared kernel-with-0016 candidate corrected. First unconditional checksum insertion failed (sources21/checksums22); existing prepared PKGBUILD restored from sibling baseline, then conditional _is_lto_kernel insertion applied and validated: non-LTO21/21, ThinLTO22/22, dkms-clang checksum/source alignment PASS, SRCINFO generated, no compile started. Invalid repair retained in logs. Coverage remains open. Additional repository check: e-tho/bc250-acpi-fix provides ACPI SSDT tables loaded via initrd, not kernel code; source README says mkinitcpio ACPI override, all BIOS1/2/3/5, conflict with modded BIOS. It cannot be honestly “integrated into kernel”; must package initrd and verify boot separately. No console install/reboot.

## Accepted package manifest and ACPI attempt

Создан reopened accepted-package manifest /home/OWNER/orca/projects/bc250/.procoder/plans/2026-09-30-bc250-accepted-package-manifest.json. Он показывает честное состояние: kernel baseline только15 патчей; кандидат16 подготовлен, но не скомпилирован; Mesa64/32 собрана; native telemetry compile/apply-check; ACPI build exit1 из-за timeout pacman mirror при попытке поставить acpica, артефакт не выдан. Runtime/boot/removal gates unresolved. Ничего на консоль не устанавливать.

## Resume attempt / Plane network failure

Continuation attempted candidate inspect/launch gate; SSH first failed because local config permission, explicit -F /dev/null retry failed socket Operation not permitted. No remote command started, no duplicate build/install/removal. Plane update also failed DNS Temporary failure in name resolution; local evidence remains authoritative and this is recorded as session networking blocker, not upstream outage.

## Repeated session socket blocker

Fresh continuation transport check: explicit SSH to 127.0.0.1 again fails socket Operation not permitted exit255; even ping fails socket Operation not permitted exit2. No remote action started. This proves current session socket sandbox restriction, not target host availability. Existing candidate unchanged; no duplicate build/install/removal. Wait for external session/network permission change.

## Continuation transport audit

SSH exact candidate inspection attempted again; exit 255; socket: Operation not permitted
ssh: connect to host 127.0.0.1 port 22: failure. No remote command started. Same session socket blocker repeated.

## Kernel candidate 0016 full build launched

Candidate arrays validated21/21; remote makepkg started through Windows WSL in tty7 pane337 with MAKEFLAGS -j28. No duplicate process detected. Await exit and hashes; console untouched.

## Kernel 0016 first attempt correction

Initial candidate runner exited1 before make: PKGBUILD source referenced unset XDG_DATA_HOME under set -u. No package build occurred. Resume1 sets HOME/XDG_DATA_HOME/XDG_CACHE_HOME, checks no active makepkg, and launched in tty7 pane339. No duplicate build.

## Parallel ACPI preparation intent while kernel compile is live

Continue existing ACPI workspace pinned5fafc82, not a new clone. Previous failure was database mirror timeout before acpica installation. Inspect existing pacman cache/dependency plan; install only acpica using already synchronized databases, no full toolchain/system upgrade while makepkg is compiling. Compile the three AML tables and validate ACPI header checksums and newc archive paths. These are candidates, not installed tables or kernel-runtime evidence. Console unchanged.

## Build duration comparison

Проверено по Windows-WSL логам одного хоста: прошлый makepkg start19:19:09 finish19:42:11=23m02s; нынешний start21:17:02, текущий makepkg elapsed1141s (~19m01) при втором замере. То есть нынешняя еще не длится в несколько раз больше предыдущей. makePID6612 explicit-j28, clang/ld CPU busy, swap0, available27GiB. Повторная сборка в новой source/build директории, без reuse прежнихobjects. В обоих makepkg configs BUILDENV !ccache; ccache global statistics mostly from Mesa and not evidence of kernel cache hits. ThinLTO использовался в обеих, не объяснять разницу якобы добавлениемLTO. Не делал перезапуск/изменение параметров.

## ACPI candidate built

ACPI candidate built on Windows WSL after retry: acpica installed with signed pacman transaction, pinned e-tho revision5fafc82, SSDT-CPU1050B, SSDT-PST1339B, SSDT-STUBS60B compiled with zero errors (3 remarks for unused stub args), ACPI header lengths/checksums pass, acpi_override.cpio newc archive lists all3 tables. Artifact not installed; requires boot/initrd acceptance separately. Kernel16 compilation remains active in pane339.

## Kernel candidate 0016 completed

Kernel candidate with0016 build completed: full-build-resume1.exit0 at21:44:05, both package SHA256 checks pass (kernel6a0bfe2a51ee268419a8b0572d69bc0b2d3ccbe3cd25cc10eb0ada984d7a8ddf, headers024dbf93bf72b12619924191d21560a0638674692467af74dd49ecb88d247d93). Final structural check pass: CC_IS_CLANG=y, SCHED_BORE=y, LTO_CLANG_THIN=y, SENSORS_NCT6687=m, nct6687.ko present. This proves package structure only, not boot/game/hardware. Console untouched; no install/removal/reboot.

## Candidate package staged on console

Kernel and headers transferred to /home/OWNER on .245 via SSH stream; SHA256 matches build values. Console current kernel7.2.6-1.206 and existing fallback linux-cachyos-bore-vcn-bc2507.2.6-1.3 remain. No pacman install, bootloader change, reboot, or removal.

## Kernel replacement completed without reboot

Выполнено по явному поручению: старые packages linux-cachyos-bore-vcn-bc250 и headers7.2.6-1.3 удалены pacman-Rns exit0; новый bore7.2.8-1.2 установлен ранее. Текущий non-BORE обновлен до linux-cachyos-bc2507.2.8-1.219 и headers, initramfs/entry обновлены. Limine default_entry теперь CachyOS/linux-cachyos-bore-bc250; fallback_entry сохраняет non-BORE linux-cachyos-bc250. Экспериментальный amdgpu.bc250_cc_write_mode=3 заменен на0 во всех entries; backup /boot/limine.conf.before-bc250-bore-7.2.8 создан. Current running kernel остается7.2.6-1.206 до reboot. Старые snapper snapshots не удалял: это recovery history, не установленные packages. Reboot не выполнял; boot/game validation pending.

## Decky native UI candidate build

Variant A selected by user. Candidate frontend uses Decky PanelSection/PanelSectionRow and builds locally with pnpm lockfile verification; rollup build exit0. Built bundle/archive staged in ~/.cache/bc250-bore-full-stack. Remote WSL lacks node/corepack, so local build is authoritative. Not installed or restarted on console.

## Native Decky install correction intent

Explicit operator approval: install new plugin, following proposed backup+Decky-only reload. First staging failed chown as ordinary user, exit1 before moving live plugin; original runtime remains untouched. Correct deployment uses sudo for root-owned files. Preserve deployed backend and bc250cc policy files exactly, replace only the verified frontend bundle. Candidate archive lacks bundled policy files and must not replace complete backend runtime. Put backup OUTSIDE Decky's scanned plugin directory, not under plugins/. Native UI is still a partial first visual slice, not full requested rewrite; no visual acceptance claim without actual screen inspection. No kernel/board/reboot changes.

## Native Decky frontend installed

Native frontend installed successfully after first staging chown correction. Existing complete runtime/backend preserved in /home/OWNER/.cache/bc250-native-ui-install-20260930/pristine-runtime; only dist/index.js replaced with verified candidate hash dff45ef253b4155d60434f23750483fb1cf83c1f388915ad3868099a56b895e2. Policy import pass; root:root permissions pass; plugin_loader restart exit0; journal Loaded BC250 Quick Access v1.20.3 and plugin ready, Decky active. No kernel/boot/hardware changes. Physical Steam UI not directly observed yet.

## Native Decky UI v2 correction

Пользователь сообщил v1 визуально не изменился. Исправил: v2 candidate удаляет глобальный custom panel/border/radius chrome из frontend, сохраняя Decky native PanelSection/PanelSectionRow, backend и опасные confirmations. pnpm build exit0; v2 installed by replacing only dist/index.js, hash456c408f670fec3300c09ba0ddd826627eca08f1a24281d0e06e30774e4d34a2, plugin_loader active and restart logs. Previous frontend backed up at /home/OWNER/.cache/bc250-native-ui-v2-20260930/frontend-v1.index.js. No kernel/boot/hardware changes. Physical UI still needs user inspection.

## Own native Decky frontend V3

После явного требования native UI frontend переписан с нуля (~100 строк вместо старого1660): только @decky/ui PanelSection/Row,Field,ButtonItem,SliderField,ToggleField,ConfirmModal. Нет custom palette/theme/grid/cards. Native V3 bundle installed by replacing only dist/index.js hash66f82f9574ec2b61fdccc214933adfcd43afc52f5d202e91a67467907621dce6; backup frontend-v2 saved. Backend untouched. Basic UI slice CPU/GPU/GDDR/fan/governor included; CU button disabled until validated topology. Missing broader functionality remains explicit, not complete. Need actual Steam-screen/controller acceptance. No kernel/hardware reboot changes.

## Native UI visual verification attempt

Attempted read-only screenshot through gamescope-0 using grim; compositor returned `compositor doesn't support the screen capture protocol`, so physical UI cannot be visually asserted from SSH. Decky loader logs confirm V3 plugin load, but visual acceptance remains user-observed.

## Native Decky V4 bug correction

V3 runtime logs show fan operations verified but user reports UI bugs. V4 built and installed as correction: standard Field children/text (removed nested small/custom structure), native static title class, current V3 dist backup preserved at /home/OWNER/.cache/bc250-native-ui-v4-20260930/frontend-v3.index.js, new hash b04510ac010474fc3fbbbeabdb161265caa6edc9b46ab7d7ce9303e526267185, plugin_loader active. Hardware/boot unchanged. Further functional/UI feedback still needed.

## Fan arbitration candidate intent

Diagnosed two separate writers: UI timer resets unsaved slider; legacy bc250-fan.sh curve writes pwm2 every2s. UI draft guard implemented on candidate, not deployed. Prepare/test arbitration with manual MINIMUM semantics, preserving every existing automatic thermal/board/power floor and emergency255. Do not disable cooling or change a live process before operator approval for cooling-service reload. Worker owns only pure policy/test candidate; parent owns service/helper integration. Source originals remain unchanged.

## Delegated fan-policy transport failure

Flash builder returned400 before doing task. Gemini fallback report lacked required receipt and described unrelated hardware, not the assigned read-only policy task. Report rejected as transport/model failure, not evidence of any authorized board write. No worker output accepted. Parent implements small pure policy locally, keeps deployment/service restart gated.

## Fan control arbitration fix

Root cause confirmed: legacy bc250-fan.service active writes pwm2 every2s; helper override only worked when newer bc250-fan-control.service active (it was inactive). Native UI draft also reset on 3s status refresh. Fixed both: candidate fanDirty guard built in V4; installed root helper arbitration patch that stops legacy service for manual PWM and starts it on automatic; manual failure fallback starts service. Original helper backup: /home/OWNER/.cache/bc250-fan-helper-backup-20261001/original; modified SHA dd786b80e2d6aafd31ad1c35d4931db9e7cfe86ff210fd5ccb7beb3d715950d3, py_compile pass. No current PWM write/service restart performed by installation itself.

## Approved full native UI implementation — no incremental rollout

User approved complete plan. Implemented offline candidate sections GPU/CPU/Cooling/Memory/Advanced and shared action confirmation. Initial presence-only callable test was inadequate: omitted digit-bearing endpoint names and did not validate argument units. Inspection found wrong CPU/VID/scale limits and GiB passed to a MiB API; corrected from authoritative bc250_contract.py, and live CPU telemetry no longer overwrites user draft. tsc --noEmit passed. First V5 deploy script mistakenly compared archive hash to bundle hash and exited1 BEFORE writing live plugin; no V5 installation occurred. In accordance with user's no-partial-release instruction, do not resume that installer. Complete capability parity, fan emergency protection and integrated offline validation first. Existing V4 remains on console. Root package/API keys unchanged.

## Full native Decky parity V7

Full native UI parity iteration V7 built and installed: tsc --noEmit and Rollup pass; all 29 public backend callable names are present (GPU safe/voltage, CPU profile/service/telemetry, CU table/service, fan, VRAM, GDDR6, game profiles/session, status). V7 adds native Steam quick settings title, Game Profiles rows, Advanced parity rows, corrected contract ranges and draft guards. First post-install hash expectation used archive hash incorrectly and exited1 after installation; live dist was nevertheless installed and verified separately: 0f5494a489118cd2480acf5b360a3ba7a6d3452ad41fe13bd1b3982023e2b52a; plugin_loader active. Correct archive hash remains 58168f...; prior frontend backup on target. Root fan helper arbitration remains installed. Full UI/hardware acceptance still pending; no kernel/reboot.

## Post-reboot verification

Reboot completed and verified: booted 2026-10-01 00:51:23, uname7.2.8-1.2-cachyos-bore-bc250, cmdline amdgpu.bc250_cc_write_mode=0, nct6687 loaded, plugin_loader active, Decky plugin loaded, current stable fallback7.2.8-1.219. Root helper status readback: CachyOS/BC250 true, Cyan governor active no conflict, GDDR6 patch inactive, CU backend not ready, fan PWM2 manual58%/2090RPM, channels3-5 automatic. bc250-metrics manually started after reboot and active. Full objective remains not complete: Mesa not installed, visual UI acceptance unobserved, CU/GDDR6/ACPI runtime not validated. No further reboot.

## Explicit live 40 CU request, no reboot

User explicitly requested enable40CU now without reboot. Initial typed cu-mode full rejected exit31 before writes because trusted backend missing. Prepared exactly reviewed WinnieLV backend revisiona929085d791f126ce76a60eb609610820fb08066 in root-owned /var/lib/bc250-control-center. Status readback:24/40, all masks0x07, driver reports24. Next action: same typed helper cu-mode40; no BIOS/boot/reboot/governor writes. Backend may change dispatch while driver enumeration stays24; report distinction, not false claim Vulkan40.

Результат выполнен без reboot: staged reviewed backend, helper cu-mode40 exit0; masks31,31,31,31, live40/40; independent backendstatus allSPI0x1f/CC0xffe00000. Driver boot map remains24 (masks7,7,7,7) so extra16 are S+ runtime-routed; no claim game uses all40 or Vulkan enumerates40. Boot setting remains0; persistence not changed.
