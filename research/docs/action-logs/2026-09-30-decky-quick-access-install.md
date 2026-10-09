# BC250 Quick Access installation

## Intent

User explicitly requested Decky plugin installation. Target: steammachine@192.168.1.245.
Install only the Decky runtime and its required protected helpers from release 1.20.3, without desktop GUI, package updates, hardware writes, or service restart.
Source package SHA256: d577d252d568b95d683d80436ea35f2da0cc3aca3446a33827d468fceddf5ed2; matches GitHub asset digest.
Initial state: plugin absent, /usr/libexec absent, Decky v3.2.9 active with hot reload enabled. Existing Decky LSFG-VK must remain untouched. Host rebooted before this operation, uptime 3 minutes at 16:49:42.
Plugin startup _main only logs ready; no hardware action. README says Desktop not fully replaced. Optional external CU/GDDR tools not automatically installed.
Deploy through atomic rename outside plugin scan path. Verify every copied byte and root ownership. Rollback: remove only this newly installed plugin/helper tree after ownership/hash checks, keep all pre-existing state. Do not run rollback against the live installation without an operator request.
Upstream installer located at package/usr/bin/bc250-control-center-decky-install, not package/usr/share/.../scripts. Earlier sed lookup exit 2; corrected path. Installer inspected but not run because it automatically restarts Decky and requires full Desktop helper installation.

## Result

Runtime deployed atomically. Installer not invoked, no service restart or hardware actions. All deployed files compared to verified release bytes:

```
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/plugin.json
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/package.json
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/main.py
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/dist/index.js
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/bc250cc/__init__.py
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/bc250cc/domain/__init__.py
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/bc250cc/domain/gpu/__init__.py
MATCH /home/OWNER/homebrew/plugins/bc250-quick-access/bc250cc/domain/gpu/profiles.py
MATCH /usr/libexec/bc250-control-center/bc250-quick-access-helper
MATCH /usr/libexec/bc250-control-center/bc250-cpu-smu-helper
MATCH /usr/libexec/bc250-control-center/bc250-governor-config-helper
MATCH /usr/libexec/bc250-control-center/bc250-fan-pwm-helper
MATCH /usr/libexec/bc250-control-center/bc250-gddr6-temp-helper
MATCH /usr/libexec/bc250-control-center/bc250-gddr6-temp-reader
MATCH /usr/libexec/bc250-control-center/lib/acpi_payload.py
MATCH /usr/libexec/bc250-control-center/lib/bc250_contract.py
MATCH /usr/libexec/bc250-control-center/lib/bc250_smu_oc_vendor.zip
MATCH /usr/libexec/bc250-control-center/lib/governor_toml.py
MATCH /usr/libexec/bc250-control-center/lib/system_setup_acpi.py
MATCH /usr/libexec/bc250-control-center/lib/system_setup_common.py
MATCH /usr/libexec/bc250-control-center/lib/system_setup_memory.py
MATCH /usr/libexec/bc250-control-center/lib/system_setup_telemetry.py
MATCH /usr/libexec/bc250-control-center/lib/system_setup_vram.py
exit 0
```

Tuning configuration hashes unchanged for governor TOML, fan unit, CPU config. Policy import passed. Decky, fan and GPU governor active. Decky journal has no BC250 load event yet; activation needs operator-approved Decky-only reload. Baseline config backup on target: /home/OWNER/.cache/bc250-decky-install-20260930/baseline-config.tar.

## Approved activation

User explicitly approved Decky-only restart. Executed `sudo -n systemctl restart plugin_loader.service`, exit 0.
Observed new loader PID 11775 at 16:58:56: `Loaded BC250 Quick Access (v1.20.3)`; plugin PID 11796: `BC250 Quick Access plugin ready`.
Existing Decky LSFG-VK also loaded. Decky's startup itself logged `Restarting steamwebhelper`, followed by frontend reinjection. No explicit Steam/GameScope restart was issued; Steam PID 1260 and Gamescope PID 992 retained their earlier start times. Configuration SHA256 checks all remained OK. Decky active. Menu visibility on physical display not directly observed.
