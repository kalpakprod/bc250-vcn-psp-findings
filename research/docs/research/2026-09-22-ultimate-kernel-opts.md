# DeepResearch: ultimate BC250 kernel optimizations (workflow deep-research)

Date: 2026-09-22. Method: 6 parallel researchers (LTO, PGO, CachyOS
inventory, cflags, Zen2 runtime, sched-mm) + critic + gap follow-up +
synthesis; external search via opencli/reddit only; all material
claims rechecked by root (G8) against board + seed configs.

## Verified baseline (root-rechecked, not worker-claimed)

- Running 7.2.6-1.1: GCC 16.2.1, LTO_NONE=y, SCHED_BORE=y,
  HZ_1000=y, NO_HZ_FULL=y (`/proc/version` + `/proc/config.gz`).
- Seed board.config (7.2.0 era): clang 22.1.8 + LTO_CLANG_THIN=y,
  NO BORE line (MastaG default = EEVDF + ThinLTO).
- Finding: 1.1 implicitly TRADED ThinLTO for BORE (CachyOS ships
  BORE variants as GCC/no-LTO, ThinLTO only on default EEVDF).
  Nobody ships BORE+ThinLTO combined — pkgrel3 can be first.

## Ranked plan (synthesis, evidence-scoped)

- Rank 0 KEEP: BORE + NO_HZ_FULL + HZ_1000 + O3 + x86-64-v3 +
  znver2 + mitigations=off. Lowest risk, proven boot.
- Rank 1 RESTORE ThinLTO/clang on BORE (pkgrel3): LLVM=1 +
  _use_llvm_lto=thin, clang/llvm/lld makedeps. Expected 0-1% FPS,
  ~0% 1%-low (no citable kernel-LTO-to-FPS numbers exist anywhere:
  phoronix bot-walled, Cachy #286 numerics auth-gated). Risk LOW:
  0008/0004/0016 plain-C, CFI-off, no LTO-hostile constructs;
  DKMS/kCFI risks (nvidia/vmware/realtek) absent here.
- Rank 2 DO NOT: FullLTO (Cachy lead: ~= Thin, 1-thread link) or
  GCC-LTO (needs out-of-tree patches). High cost, ~0% delta.
- Rank 3 AutoFDO (deferred): only quantified opt (+1-2% per
  ptr1337 on default EEVDF v3/v4+zen4). BLOCKER: collection needs
  Zen3+BRS / Zen4 amd_lbr_v2 / Intel LBR — Zen2 BC250 cannot
  collect natively; foreign-profile reuse explicitly unproven and
  kernel.org warns about wrong-objective profiles. Only after
  Rank 1 green + A/B abort-on-regression. Risk MEDIUM-HIGH.
- Rank 4 Propeller/GCOV: no FPS numbers in evidence; after
  ThinLTO proven. Risk unknown.

## Unresolved (preserved)

- No citable kernel-LTO-to-gaming-FPS numbers (all gates above).
- AutoFDO reuse across different patched BORE kernels: uninvestigated.
- Zen2-native collection unsupported; cross-platform reuse
  gaming-representativeness unproven.
- OS/userspace opts (Mesa, compositor, governor, IRQ, fs) were
  outside this workflow's scope.

## Next verifications

- Rank 1: LLVM=1 + thin in phase scripts; rebuild; confirm
  CC_IS_CLANG + LTO_CLANG_THIN=y + BORE=y; boot + VCN/game smoke +
  FPS/1%-low A/B on same save/scene.
- Rank 3 (only after Rank 1): Cachy default profile + source
  confirmation; rebuild with CLANG_AUTOFDO_PROFILE; A/B vs
  ThinLTO-only; abort on regression.
