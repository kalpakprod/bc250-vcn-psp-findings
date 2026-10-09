# Concrete BIOS instruction — voltage-unlocked CLV lineage

## Exact image

Use only this candidate for the described BIOS test:

```text
/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/integration-vdd80/BC250_5.00_clv_OC_sync1750_vdd80_MENU_ONLY_v001.bin
SHA-256: ad17650479e40aef6ba409cfc7efb0f3a80f4493fe9e47458b08037d6a1c57da
```

It was built from the user's voltage-unlocked source:

```text
/home/OWNER/orca/projects/bc250/candidates/BC250_5.00_clv_OC_sync1750_vdd80_v001.bin
SHA-256: f2ae4b768f2dd33eacbe06c5c482c5ac9843e434ed81d1d8ff08197d806c4e52
```

The candidate preserves the source's stored requests:

```text
Memory Clock Speed             1750 MHz enum 0x23
UclkDiv1M0                     Enabled 0x01
FCLK_DPM                       Disabled 0x00
DF Clock Override Control      Manual 0x01
DF Clock Override              1750 decimal, LE D6 06
VDDCR_VDD Offset Control       Manual 0x01
VDDCR_VDD Offset               raw 80 decimal
Memory P-state                 Auto 0xFF
Tcl                            16
BankGroupSwap                  0
```

The raw `VDDCR_VDD Offset=80` is preserved exactly. It is not relabelled as 1.15 V because the final consumer and physical rail conversion are not proven.

## What was added

- `CLV Tuning` HII form and five native-form links;
- links to native MCLK, UCLK, FCLK/DF, NBIO and voltage pages;
- corrected two malformed `FALSE` IFR predicates in the voltage form;
- no new voltage writer, no SMU write, no GPIO write, no `$PS1` change, no PSP change and no APCB change.

## BIOS steps after a separately approved flash

1. Enter BIOS Setup and open `Advanced -> CLV Tuning`.
2. Open `Memory clock and timings` and confirm `Memory Clock Speed = 1750 MHz`.
3. Open `Memory controller debug` and confirm `UclkDiv1M0 = Enabled`.
4. Open the memory power page and set `Memory P-state = Disabled` only for the explicit DF-override comparison. This changes the source's `Auto` request and must be recorded as a new test state.
5. Open `Fabric and SMU debug` and set:
   - `FCLK_DPM = Disabled`;
   - `DF Clock Override Control = Manual`;
   - `DF Clock Override = 1750`.
6. Open the voltage page and leave the source's existing VDDCR_VDD manual/offset request unchanged. Do not enter a new numeric voltage and do not exceed the operator limit `1.15 V`.
7. Save and reset.
8. Re-enter BIOS and read every value back. A value that reverted means the test failed at persistence.
9. Before any OS benchmark, record POST, training, display and boot result. Keep the original recovery image ready.

## What this configuration means

This is a controlled BIOS hypothesis matching the user's voltage-unlocked source. It is not yet proof of physical `MCLK:UCLK:FCLK=1:1:1`.

- `UclkDiv1M0=Enabled` is an enum, not a proven numeric `/1` divider.
- `DF Clock Override=1750` is a stored request, not a measured FCLK.
- the BIOS help text says `FCLK > UCLK`, which conflicts with a literal equal-clock interpretation;
- independent physical clocks and latency are still required.

## Acceptance gate

Accept the configuration only if:

- the Setup values survive save/reset;
- the board cold-boots repeatedly;
- no training fallback or corrected error appears;
- independent clock observations are available;
- CPU pointer-chase latency and the same controlled game scene are measured before/after;
- SoC voltage is independently measured and remains at or below `1.15 V`.

No claim of safe, bootable, synchronized or hardware-accepted status follows from this static candidate alone.
