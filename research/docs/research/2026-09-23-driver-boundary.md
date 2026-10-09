# Menu bridge DXE boundary audit

The existing host mock was rerun, not recompiled. It exited `0`, stderr empty, with literal output:

```text
PASS: registration, three error paths, failed removal retained, successful removal, idempotent unload (host mock only)
```

The packaged DEPEX was independently decoded from `menu.depex`: `PUSH EFI_HII_DATABASE_PROTOCOL_GUID; END`. The driver only registers HII packages through `EFI_HII_DATABASE_PROTOCOL`, assigns an unload handler, and does not contain a voltage, SMU, GPIO, NVRAM or clock writer. Evidence: `evidence/firmware-audit/20260923-driver-boundary/result.json`.

This closes the driver's intended mutation scope statically. It does not prove DXE dispatch on BC-250, AMI Setup visibility, or any hardware result.
