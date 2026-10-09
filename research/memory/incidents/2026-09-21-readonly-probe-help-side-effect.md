# G7 correction: clock-probe `--help` executed a workstation read

Date: 2026-09-21 (Asia/Almaty). Actor: root-directed Task 7 worker.

## Disproved assumption

I invoked `python3 scripts/probe_bc250_clocks_readonly.py --help` while checking tool availability. This script has no argument parser or help branch: `__main__` unconditionally calls `main()`. The command exited 0 after reading and emitting workstation metadata, including `/proc/cmdline`, DMI fields, and local DRM sysfs. Therefore `--help` is **not safe** for this particular script; its availability and behavior must be assessed by static inspection only. Do not repeat this invocation.

## Observed boundary

The only DRM device in the emitted result was local `card1`, device `0x1900`, explicitly skipped against the script's default target `0x13fe`; `cards` was empty. This was an unintended, read-only workstation metadata collection, **not** a BC-250 board connection, a board capture, a new firmware probe, or evidence of board state. There was no network access, install, firmware/NVRAM/register write, or other hardware mutation. Exact command-line and DMI values are deliberately excluded from this incident record and all project artifacts.

## Corrected procedure

Before requesting `--help` from any project script, inspect the entrypoint for an argument parser and prove that help exits before input reads, system inspection, or other effects. For `scripts/probe_bc250_clocks_readonly.py`, use static inspection only. `argparse`-backed offline tools may use `--help` only after confirming parser-first control flow. Keep any future target capture behind the existing runbook's board identity gate; a host ID of `0x1900` is not a BC-250 identity.

## Evidence and remaining scope

The invocation and correction are also recorded in `docs/action-logs/2026-09-21-task7-tool-readiness.md`. The source inspection confirms the unconditional read path and the explicit `0x13fe` filter. No raw workstation output was saved as a project evidence file; sensitive host metadata from that stdout is not reproduced here. No conclusion about present board connectivity or state follows.
