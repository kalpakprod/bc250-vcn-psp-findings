# Action log — community profile matrix

## Intent before write

Create a report-only, static comparison of the exact CLV AmdSetup clock fields against current community evidence from Discord, Telegram exports and public GitHub repositories. Produce three native BIOS comparison states plus one CMOS-only external control. Do not modify a ROM, NVRAM, APCB, PSP, `$PS1`, voltage field or hardware. Keep SoC ceiling at 1.15 V as an operator requirement, but do not encode a voltage value because the revision-matched consumer and rail mapping remain unresolved.

## Target

- Source ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Source SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Outputs: `docs/research/2026-09-22-community-mclk-uclk-fclk-profile-matrix.md` and `/tmp/profile_matrix_20260922/result.json`

## Action after write

The report and machine-readable matrix were created. No firmware or hardware write occurred. Validation and hashes are recorded in the report.
