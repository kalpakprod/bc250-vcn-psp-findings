# GDDR6 monitoring / SMU patch preparation

Intent: investigate I2C warning, prepare exact reviewed temperature tool for Decky on 192.168.1.245. No firmware or SMU write in preparation phase.
Baseline: BIOS P3.00, board AMD BC-250, kernel 7.2.6-1.206-cachyos-bc250. Decky helper gddr6-sensors returned ok=true, available=false, reason=REPOSITORY_NOT_READY, empty chip list.
Distinguish separate features: VRM power rails need physical I2C modification; per-chip GDDR6 temperatures need a runtime SMU patch, not I2C wiring.
Reviewed upstream revision from installed helper: b7e6bffcb5d592fc03edde375b7598ddc79aa846. Patch script hash c6c0b17f3f2dad415f7814035a1918331068ab1827269a97254df0ddb554ca6e.
SMU patch is volatile RAM, not SPI BIOS flash. Cold power cycle restores factory handler. It changes a shared firmware mailbox handler and can hang the board; source warns of instability/data corruption. Need communicate risk before execution. Existing metrics service reads kernel gpu_metrics; GPU governor active; no game process observed in latest process check. Do not suppress helper locking, firmware checks, or manually override governor safety.

## Approved application intent

User explicitly confirmed SMU patch after warning. Fresh 17:09:44 check: board accessible, low load, BIOS P3.00, patch inactive. Use installed protected helper with its full repository/hash/firmware/governor/locking checks. Sudo performs authorization; PKEXEC_UID=1000 supplies the requesting desktop identity expected by the helper. No ignore-governor override. No frequency, fan, CPU, BIOS/SPI changes or service restart. Recovery on hang: stop further accesses and ask operator for full power cycle; do not automatically restart.
Command: sudo -n env PKEXEC_UID=1000 /usr/libexec/bc250-control-center/bc250-gddr6-temp-helper --repo /home/OWNER/.local/share/bc250-control-center/ResourceTools/bc250-memory-temperature --action apply

## Application event

```
STDOUT:
gate before: open?
dbg byte 0x00 entry byte 0x00
already unlocked
Successfully patched queue_3_msg_5_handler -> 0x0003AAC4
Runtime SMU patch applied. This lives in volatile SMU RAM only; a full power cycle restores the factory Queue 3 / Message 5 handler.

STDERR:

EXIT: 0
```

## Verified readback

```
{"ok": true, "protocol": 19, "gddr6_available": true, "gddr6_reason": "", "gddr6_chips": [{"chip": 0, "raw": 11051, "code": 43, "temperature_c": 46}, {"chip": 1, "raw": 12336, "code": 48, "temperature_c": 56}, {"chip": 2, "raw": 12850, "code": 50, "temperature_c": 60}, {"chip": 3, "raw": 11565, "code": 45, "temperature_c": 50}, {"chip": 4, "raw": 13364, "code": 52, "temperature_c": 64}, {"chip": 5, "raw": 12593, "code": 49, "temperature_c": 58}, {"chip": 6, "raw": 12079, "code": 47, "temperature_c": 54}, {"chip": 7, "raw": 11051, "code": 43, "temperature_c": 46}], "gddr6_average_c": 54.25, "gddr6_hotspot_c": 64, "gddr6_hotspot_chip": 4, "gddr6_bios_version": "P3.00", "gddr6_firmware_supported": true}
/etc/cyan-skillfish-governor-smu/config.toml: OK
/etc/systemd/system/bc250-fan.service: OK
/etc/bc250-smu-oc.conf: OK
active
active
active
 17:10:25 up 23 min,  2 users,  load average: 0.24, 0.18, 0.24
exit 0
```
