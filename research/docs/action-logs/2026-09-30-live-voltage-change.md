# Live voltage change: CPU scale -35 -> -34

## Intent before write

Target: BC-250 at 192.168.1.245. User explicitly requested: set CPU FVID curve scale to -34 and measure before/after. Current service is `bc250-smu-oc.service`; CPU frequency must remain 3900 MHz. GPU setting is not changed by this operation. Planned rollback: restore `/etc/bc250-smu-oc.conf` from captured baseline (`scale=-35`) and rerun the same service apply command. No BIOS/SPI write.

## Baseline capture pending

## Observed baseline

Remote command on 127.0.0.1 before write:

- config: frequency=3900, scale=-35, max_temperature=100
- sensors: CPU 62.0 C, vddgfx 1.01 V, vddnb 1.16 V, CPU Vcore 0.00 V (invalid/unavailable)
- `bc250-smu-oc.service`: active

## Write and observed result

- Backup: `/etc/bc250-smu-oc.conf.pre-scale-minus35-20260930T2027`
- Applied config: frequency=3900, scale=-34, max_temperature=100
- Service restart exit: 0; `ExecMainStatus=0`; active
- Journal: `Applying 3900 MHz @ Scale -34, 100°C`

## Observed after

- sensors: CPU 62.0 C, vddgfx 1.01 V, vddnb 1.10 V, CPU Vcore 0.00 V (invalid/unavailable)
- CPU voltage delta: not measurable from available hwmon sensor.
- GPU voltage was not changed by this operation.

## GPU +10 mV requested and applied

User requested GPU +10 mV. Baseline SetTestMode argument 1015 mV, driver readout 1006 mV. Backup on board: /etc/systemd/system/cyan-skillfish-governor-smu.service.d/20-fixed-2200.conf.pre-1025-20260930.
First sed failed: `sed: -e expression #1, char 6: unterminated 's' command`; shell continued and restarted governor with unchanged 1015 mV, driver readout 999 mV. Corrected quoting with set -e; changed drop-in 1015 -> 1025, daemon-reload and D-Bus SetTestMode 2200 1025 completed exit0. Journal: Test mode enabled with fixed frequency 2200 MHz and voltage 1025 mV. Driver readout: 1018 mV, 2200 MHz. CPU config unchanged at scale -34, frequency3900. Telemetry is not an independent rail measurement. Rollback baseline saved but not executed. Requested setpoint increment +10mV confirmed; observed readout difference baseline1006 ->1018 (+12mV), not exactly10mV. No stress test.
