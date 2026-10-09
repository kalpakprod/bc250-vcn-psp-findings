# Evaluation: XanMod kernel for the universal BC250 kernel

Date: 2026-09-21. Evaluator: root. Skill: external-stack-evaluation.

## G7 supersede note

The first version of this record (REJECT, 2026-09-21 ~19:00) evaluated the
STALE GitHub mirror `github.com/xanmod/linux` (heads through 6.11, tags
through 6.11.5-xanmod1) and wrongly concluded upstream was frozen. The
operator corrected: real upstream is **GitLab** `gitlab.com/xanmod/linux`
(branch `7.2`, tags through `7.2.6-xanmod1`, Sep 2026) plus
`gitlab.com/xanmod/linux-patches` (`linux-7.2.y-xanmod`, Aug 21 2026).
This record supersedes the REJECT. Lesson: verify the canonical repo
(xanmod.org links GitLab) before a freshness verdict.

## Item and scope

XanMod 7.2 (`gitlab.com/xanmod/linux`, GPL-2.0) as base or patch donor for
`linux-cachyos-bore-vcn-bc250` (7.2-stable, BORE + MastaG BC250 set + local
VCN delta) for board BC250-01.

## State

**ADAPT** (cherry-pick tunables; NOT the base).

## Reason

- Base stays MastaG + CachyOS-bore: proven BC250 boot path, native BORE
  variant (`prepare-pkgbuild.sh`), CachyOS/Arch config family matching the
  board. XanMod is Debian-oriented (APT repo, .deb configs) with zero
  BC250/VCN content — rebasing would trade a proven boot for config-port
  risk with no BC250 gain.
- Hard conflict: XanMod `0006-XANMOD-fair-Set-scheduler-tunable-latencies`
  touches `kernel/sched/fair.c`, which BORE rewrites heavily — stacking
  BORE on XanMod invites rejects; CachyOS-bore already resolved this.
- Adaptable (small, reviewable, non-sched): block/mq-deadline tweaks
  (0007-0010), vfs/mm tunes (0012-0014), cpufreq tunes (0015), le9uo
  (`mm/0001`), BBRv3 (`net/tcp`), Clear-partial, x86-64 ISA levels
  (`kconfig/`). Each applies onto a CachyOS-bore tree independently;
  verify per-patch with `patch --dry-run`, keep the ones that apply
  cleanly, skip on first reject (no hand-porting in v1).
- No BORE in XanMod (feature list + patch inventory confirm) — BORE still
  comes from CachyOS.

## Source / revision / date / license

- `https://gitlab.com/xanmod/linux`, branch `7.2` (`08752fbe`),
  tag `7.2.6-xanmod1`, Sep 2026. `https://gitlab.com/xanmod/linux-patches`,
  commit `6e34b2e` (Aug 21 2026). Checked 2026-09-21 via ls-remote +
  depth-1 clone of linux-patches (`/tmp/xanmod-p`, 10 dirs).
- License: GPLv2 (xanmod.org statement; `LICENSE` file present in
  linux-patches, not line-verified this run).

## Inspected files

- `/tmp/xanmod-p/linux-7.2.y-xanmod/`: `xanmod/` (18 patches, listed),
  `net/`, `mm/0001` (le9uo), `zen/` (2), `kconfig/` (3), plus `binder/`,
  `clearlinux/`, `pci_acso/`, `userns/`, `valve/` (names only).
- xanmod.org feature list (via web_fetch): LLVM/Polly, MGLRU default,
  SCX support (mainline Kconfig), BBRv3 default, le9uo, Clear-partial,
  Graysky CPU opts. No BORE anywhere.
- Stale mirror for contrast: github.com/xanmod/linux (6.11 max, 1430 tags).

## Evidence

- `git ls-remote` (GitLab): `7.2` head + `7.2.6-xanmod1` tag exist.
- Patch inventory above (directory listing, not full content review).
- Conflict prediction for 0006 vs BORE is structural (same file,
  both non-trivial) — untested, recorded as prediction, not fact.

## Unknowns

- Full per-patch content review (only names + one-line summaries read).
- Dry-run results against the CachyOS-bore 7.2 tree (build-host step).
- XanMod .config delta (not needed — not the base).

## Security risks

- Cherry-picks are small upstream-reviewed tunes; risk low. Each patch
  keeps its origin header; rollback = drop the patch, rebuild.
- No code copied into the repo yet; no execution; no network exposure.

## Effect on the project

- Spec updated: `specs/2026-09-21-universal-bore-vcn-kernel.md` D1 addendum
  (ADAPT list, base unchanged). No standard-stack change (no D-link
  beyond the kernel decision already recorded).

## Next action

- On the build host: `patch --dry-run` each ADAPT candidate against the
  prepared CachyOS-bore+BC250+VCN tree; keep clean applies, log rejects.
- Revisit base choice only if MastaG-bore path fails to boot (then U3
  fallback kernels still cover the board).
