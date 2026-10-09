# P1: AmdMemAm4Pei directory lookup, not an SMU command

Exact clean CLV: SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8. Module AmdMemAm4Pei SHA-256 1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8.

## Corrected call roles

- B09 has a variadic, formatting-like call shape. Caller8A0 passes a debug message mentioning APOB to it. That address is not evidence of an APOB service interface. Its complete logging implementation is not needed for the directory edge.
- CD9 calls BFB to locate and validate PSP/BIOS directories. It optionally follows entry70 to a BL2 directory, otherwise scans the BHD table. It matches the first byte of24-byte records against the caller's type argument.
- Caller8D1 requests type61. CD9 copies flags/type, source, size and destination into four caller-provided output locations. It does not issue a SMU frequency command.
- Clean BHD entry at ROM AB0028 has type61, size0, source0 and destination04000000. After return, caller8E8 takes the destination output and at8FC checks for bytes APOB in the pointed memory. This is consumption of an existing buffer, not its producer.

The four-entry directory and instruction ranges were checked against pinned bytes in evidence/firmware-audit/20260923-actuator-first/result.json. No real read of physical04000000 or port I/O occurred. No claim that the buffer is present at runtime follows from the stored address.

## Architecture consequence

Do not search for a clock-setting command in CD9 or infer INV->APOB input delivery from this caller. APOB population and its timing remain open. P1's call-direction correction is complete; the full boot-producer map is not.
