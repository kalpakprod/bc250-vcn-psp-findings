# Waveshare final implementation — preflight

## Intent before writes

Implement the approved one-UF2 Waveshare BC250 plan in the existing candidate source. Parallel workers will own disjoint files/worktrees. Preserve the current candidate, recovery dumps, and transaction artifacts. No physical flash is part of this preflight. A root snapshot is created before source changes.

## Target

`candidates/waveshare-adapter-safe-v001/`

## Constraints

- No BC250 BIOS or hardware write during source implementation.
- No deletion or reset of existing uncommitted work.
- Final hardware flash requires exact-image SHA and separate approval.

## Intent before packaging

Package the offline-built UF2, final HTML guide, PSP pipeline note and machine-readable hashes into a new report directory. This is a file copy only; no hardware or BIOS write.

## Packaging result

- UF2 package and guide copied to `reports/waveshare-implementation-20261001/final/`.
- No hardware write performed.

## Offline implementation result

- Target source: `candidates/waveshare-adapter-safe-v001/`.
- Built UF2: `reports/waveshare-implementation-20261001/final/Waveshare-RP2350B-Plus-W-BC250-DS5-TOCTOU-SPI-UART-LPC-FLASH-FINAL.uf2`.
- UF2 SHA-256: `276a170b24ba3c1408ed910f24cf671c85a8bb83e804afcedb326c696929228c`.
- Focused tests: 6 passed.
- `make test`: 7 passed.
- UF2 structural checker: passed.
- RAM relocation gate: passed during build.
- Hardware write: not performed.
- Hardware TOCTOU/PSP cold-boot acceptance: not performed.

## Intent before package refresh

Refresh the packaged UF2 after adding the DTR-aware bridge translation unit to the build. Replace only the packaged UF2 and regenerate its hash list; no hardware write.

## Refreshed package result

- Refreshed UF2 SHA-256: `a72df0bfcc3246bd79e718500d28b9c50de5fdc6fc3fe9be274cdc47b7044c82`.

## Intent before package refresh

Refresh package after integrating the bounded TOCTOU runtime source and CDC ARM/Disarm routing. No hardware write.

## Read-only hardware preflight

- `/dev/ttyACM0` is currently Sony DualSense `054c:0ce6`, not Waveshare.
- No RP2350 BOOTSEL device was present.
- No hardware write or reset was performed.
- Final UF2 remains staged only.

## Intent before correction

Do not flash the user-approved SHA. Correct three preflight defects found before write: build-time `MODE_FLASH` fallback, competing CDC readers, and the empty weak bridge hook. Rebuild a new candidate and issue a new SHA; the prior approval applies only to the old bytes.

## Intent before test correction

Update the existing flash-service host fixtures to select the newly explicit `MODE_FLASH` instead of the retired diagnostic mode. This changes only test setup to match the production mode contract; no production guard is weakened and no hardware access occurs.

## Correction result

- Old approved SHA `37cc50e6e1ab4960e70e480f424722ed41bf17fcccc0eef5fbd959ffd3425bf0` is not current after the preflight correction.
- Current rebuilt UF2 SHA: `5c1d0677070d0dbc32de936957b80243c70b0ffc3749e6f2a6e4ceac62686465`.
- No hardware write performed; old approval does not transfer to the new bytes.
