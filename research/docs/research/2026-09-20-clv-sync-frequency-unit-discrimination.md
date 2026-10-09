# CLV MCLK/UCLK/FCLK frequency-unit discrimination (offline)

## Conclusion

The strongest demonstrated mapping is **software aliasing**, not physical clock identity:

- In retained `cyan_skillfish_ppt.c`, `METRICS_CURR_UCLK` reads `Current.MemclkFrequency`.
- The `SMU_FCLK` and `SMU_MCLK` cases both select `METRICS_CURR_UCLK`.
- `gpu_metrics` current and average UCLK/FCLK fields also copy `MemclkFrequency`.

Thus equal exported FCLK/MCLK/UCLK values from this source are aliases of one software metric. They cannot establish independent clocks, GDDR6 edge/data-rate conversion, or synchronous operation.

The retained Robin-5 handler evidence separately shows Queue 0 `0x11` returning an internal software committed frequency float indexed through a 20-domain table, while Queue 0 `0x13` returns a P-state index delta/count. Neither is an independent physical clock measurement. Existing static domain/aperture mapping does not identify a physical MCLK/UCLK/FCLK domain; its entries explicitly remain unknown without runtime confirmation.

## Smallest discriminating check executed

The executed check is intentionally host-only and narrow: assert exact source fragments for the driver aliases, then assert the already byte-verified handler/domain classifications. It does not read sysfs, invoke live telemetry, parse new firmware, or claim physical behavior.

Command:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency_unit_verify.py
```

Result: exit `0`, `11/11 PASS`; machine result SHA-256 `6027fd54d8803fbd2a8b22f09c098ec5e9174ddbb143fd2b41f68a5575f7fb0c`.

The check discriminates the available evidence classes as:

| Source              | Demonstrated mapping                                                 | Not demonstrated                                             |
| ------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------ |
| Host driver source  | FCLK/MCLK/UCLK exports alias `MemclkFrequency`                       | Independent physical clock values, units, sync               |
| SMU Queue 0 `0x11`  | Internal committed software frequency float by firmware domain index | PLL/clock-counter sampling; physical MCLK/UCLK/FCLK identity |
| SMU Queue 0 `0x13`  | P-state index delta/count                                            | Frequency in MHz or physical clock                           |
| Fabric domain table | Static group/aperture assignments                                    | Physical domain identity without runtime confirmation        |

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Driver source: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/cyan_skillfish_ppt.c`, SHA-256 `9259ad3ff6f660fe97ca7ea68f9b7e5f5d185982f0d3341180bd880442f030f1`
- Handler verification: `evidence/firmware-audit/20260919-oc-clock-provenance/clock-handlers-verification.json`
- Fabric-domain verification: `evidence/firmware-audit/20260919-oc-clock-provenance/fabric-domains-verification.json`
- Own machine result: `evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency-unit-result.json`

## Minimal remaining offline semantic gate

A truthful experimental default profile still needs one byte-backed static map from the five Setup fields/tokens to the actual consumer/actuator, with:

1. MCLK/FCLK/UCLK units and GDDR6 conversion resolved;
2. UclkDiv1M0 divider semantics resolved;
3. Memory P-state and FCLK/UCLK guidance connected to the training/configuration path;
4. synchronous-crossing selection distinguished from equal software values; and
5. existing-NVRAM/default migration precedence preserved.

Live telemetry is not an offline prerequisite, but hardware acceptance must independently identify actual clocks, training and synchronization. No frequency, voltage, safe-setting, or `1:1:1` claim follows from the executed check.

## Acceptance

- **PASS:** source and retained verification hashes; 11/11 host-only discrimination checks.
- **STATIC ONLY:** driver alias and software-state handler semantics.
- **UNKNOWN/UNRUN:** physical clock mapping, GDDR6 rate conversion, training, synchronization, voltage, hardware.
