#!/usr/bin/env python3
"""Deterministic BC-250 latency/bandwidth/ALU A/B harness (read-only, stdlib only).

Purpose: replace participant/photo latency claims ("140 ns", "131.4 ns") with a
same-binary, same-input, repeatable measurement that carries an explicit method
identity, so an OC request can be classified as a measurable gain, inconclusive,
or no measurable effect.

Hard constraints (enforced, not by convention):
  * writes nothing except its own --out JSON and a temporary build directory;
  * no /dev/mem, no PCI config, no SMU/mailbox, no sysfs writes, no firmware,
    NVRAM, or hardware mutation of any kind;
  * refuses to label results as BC-250 results unless the local DRM device is the
    BC-250 APU (1002:13fe) or --allow-non-bc250 is passed, in which case the
    result is stamped host_is_bc250=false and must not be reported as board data;
  * a pure-Python fallback is reported as a proxy, never as a latency device.

Evidence class: `emulated-or-host-tested` for this workstation. On the board the
same command is `hardware-verified` for the exercised runtime path only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "bc250-perf/v1"
SCHEMA_COMPARE = "bc250-perf-compare/v1"
BC250_PCI_IDS = {("0x1002", "0x13fe")}

LATENCY_SIZES_FULL = (
    1 << 16,
    1 << 18,
    1 << 20,
    4 << 20,
    8 << 20,
    16 << 20,
    64 << 20,
    256 << 20,
)
LATENCY_SIZES_QUICK = (1 << 16, 1 << 20, 8 << 20, 64 << 20)
ACCESSES_FULL, ACCESSES_QUICK = 3_000_000, 400_000
BW_BYTES_FULL, BW_BYTES_QUICK = 256 << 20, 64 << 20
BW_REPEATS_FULL, BW_REPEATS_QUICK = 8, 4
ALU_ITERS_FULL, ALU_ITERS_QUICK = 200_000_000, 20_000_000
CC_CANDIDATES = ("cc", "gcc", "clang")
FALLBACK_MAX_BYTES = 4 << 20
FALLBACK_SEED = 0xC0FFEE
# Working sets at or below this size are treated as cache-resident. A real
# clock/timing change must not make them measurably slower; if it does, the
# sample pair is incoherent and no performance claim is allowed.
CACHE_DOMAIN_CEILING_BYTES = 4 << 20

HELPER_SOURCE = r"""
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

static uint64_t rng_state;
static uint64_t rng_next(void) {
    uint64_t x = rng_state;
    x ^= x >> 12; x ^= x << 25; x ^= x >> 27;
    rng_state = x;
    return x * 2685821657736338717ull;
}
static double now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

static int do_latency(size_t bytes, size_t accesses, uint64_t seed) {
    size_t n = bytes / 8, i;
    uint64_t *perm, *chain, cur = 0;
    volatile uint64_t sink = 0;
    size_t warm, j;
    double t0, t1;
    if (n < 64 || accesses < 1000) return 3;
    perm = malloc(n * sizeof(uint64_t));
    chain = malloc(n * sizeof(uint64_t));
    if (!perm || !chain) return 4;
    for (i = 0; i < n; i++) perm[i] = i;
    rng_state = seed;
    for (i = n - 1; i > 0; i--) {
        uint64_t t;
        j = (size_t)(rng_next() % (uint64_t)(i + 1));
        t = perm[i]; perm[i] = perm[j]; perm[j] = t;
    }
    for (i = 0; i < n; i++) chain[perm[i]] = perm[(i + 1) % n];
    free(perm);
    warm = accesses / 10;
    if (warm < 1000) warm = 1000;
    for (i = 0; i < warm; i++) cur = chain[cur];
    t0 = now_ns();
    for (i = 0; i < accesses; i++) { cur = chain[cur]; sink ^= cur; }
    t1 = now_ns();
    printf("{\"mode\":\"latency\",\"bytes\":%zu,\"accesses\":%zu,\"ns_per_access\":%.4f,\"sink\":%llu}\n",
           bytes, accesses, (t1 - t0) / (double)accesses, (unsigned long long)sink);
    free(chain);
    return 0;
}

static int do_bandwidth(size_t bytes, size_t repeats) {
    unsigned char *src = malloc(bytes), *dst = malloc(bytes);
    size_t r, i;
    double t0, t1;
    volatile unsigned sink = 0;
    if (!src || !dst) { free(src); free(dst); return 4; }
    for (i = 0; i < bytes; i += 4096) src[i] = (unsigned char)(i >> 12);
    t0 = now_ns();
    for (r = 0; r < repeats; r++) { memcpy(dst, src, bytes); sink ^= dst[(r * 7919) % bytes]; }
    t1 = now_ns();
    printf("{\"mode\":\"bandwidth\",\"bytes\":%zu,\"repeats\":%zu,\"gb_per_s\":%.4f,\"sink\":%u}\n",
           bytes, repeats, ((double)bytes * (double)repeats) / (t1 - t0), (unsigned)sink);
    free(src); free(dst);
    return 0;
}

static int do_alu(size_t iters) {
    uint64_t a = 1, b = 2, c = 3, d = 4;
    size_t i;
    double t0, t1;
    for (i = 0; i < 1000; i++) { a = a ^ b; b = b + c; c = c + d; d = d + a; a = (a << 1) | (a >> 63); }
    t0 = now_ns();
    for (i = 0; i < iters; i++) { a = a ^ b; b = b + c; c = c + d; d = d + a; a = (a << 1) | (a >> 63); }
    t1 = now_ns();
    printf("{\"mode\":\"alu\",\"iters\":%zu,\"ns_per_op\":%.4f,\"sink\":%llu}\n",
           iters, (t1 - t0) / (double)iters, (unsigned long long)(a ^ b ^ c ^ d));
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s latency|bandwidth|alu ...\n", argv[0]); return 2; }
    if (strcmp(argv[1], "latency") == 0 && argc == 5)
        return do_latency((size_t)strtoull(argv[2], 0, 10), (size_t)strtoull(argv[3], 0, 10),
                          (uint64_t)strtoull(argv[4], 0, 10));
    if (strcmp(argv[1], "bandwidth") == 0 && argc == 4)
        return do_bandwidth((size_t)strtoull(argv[2], 0, 10), (size_t)strtoull(argv[3], 0, 10));
    if (strcmp(argv[1], "alu") == 0 && argc == 3)
        return do_alu((size_t)strtoull(argv[2], 0, 10));
    fprintf(stderr, "bad arguments\n");
    return 2;
}
"""


def read_text(path: str | Path) -> str | None:
    try:
        return Path(path).read_text(errors="replace").strip()
    except OSError:
        return None


def detect_gpu_pci_ids() -> list[list[str]]:
    ids: list[list[str]] = []
    for vendor_file in sorted(Path("/sys/class/drm").glob("card*/device/vendor")):
        vendor = read_text(vendor_file)
        device = read_text(vendor_file.with_name("device"))
        if vendor and device:
            ids.append([vendor, device])
    return ids


def host_metadata() -> dict[str, Any]:
    cpuinfo = read_text("/proc/cpuinfo") or ""
    meminfo = read_text("/proc/meminfo") or ""
    cpu_model = None
    for line in cpuinfo.splitlines():
        if line.lower().startswith("model name"):
            cpu_model = line.split(":", 1)[1].strip()
            break
    mem_total_kib = None
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            mem_total_kib = line.split()[1]
            break
    ids = detect_gpu_pci_ids()
    return {
        "kernel": os.uname().release,
        "arch": os.uname().machine,
        "cpu_model": cpu_model,
        "cpu_count": os.cpu_count(),
        "page_size": os.sysconf("SC_PAGE_SIZE"),
        "governor": read_text("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
        "transparent_hugepage": read_text(
            "/sys/kernel/mm/transparent_hugepage/enabled"
        ),
        "mem_total_kib": mem_total_kib,
        "drm_pci_ids": ids,
        "host_is_bc250": any(tuple(pair) in BC250_PCI_IDS for pair in ids),
        "external_benchmarks": {
            name: shutil.which(name)
            for name in ("lat_mem_rd", "tinymembench", "mbw", "sysbench", "mlc", "perf")
        },
        "python": sys.version.split()[0],
        "hostname_collected": False,
        "kernel_cmdline_collected": False,
    }


def compile_helper(tmpdir: Path) -> dict[str, Any]:
    src = tmpdir / "perf_probe.c"
    binary = tmpdir / "perf_probe"
    src.write_text(HELPER_SOURCE)
    last: dict[str, Any] = {
        "kind": "no-compiler",
        "cc": None,
        "helper_sha256": None,
        "compile_returncode": None,
        "helper_path": None,
        "latency_metric_class": "proxy-interpreter-overhead",
    }
    for cc in CC_CANDIDATES:
        exe = shutil.which(cc)
        if not exe:
            continue
        proc = subprocess.run(
            [exe, "-O2", "-std=c11", "-o", str(binary), str(src)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode == 0 and binary.exists():
            return {
                "kind": "compiled-c-helper",
                "cc": exe,
                "helper_sha256": hashlib.sha256(HELPER_SOURCE.encode()).hexdigest(),
                "helper_path": str(binary),
                "compile_returncode": 0,
                "latency_metric_class": "dependent-load",
            }
        last = {
            "kind": "compile-failed",
            "cc": exe,
            "helper_sha256": None,
            "compile_returncode": proc.returncode,
            "helper_path": None,
            "latency_metric_class": "proxy-interpreter-overhead",
            "stderr_tail": (proc.stderr or "")[-400:],
        }
    return last


def run_helper(binary: str, args: list[str], timeout: float = 120.0) -> dict[str, Any]:
    proc = subprocess.run(
        [binary] + args, capture_output=True, text=True, timeout=timeout
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"helper {args} exit {proc.returncode}: {(proc.stderr or '').strip()[:200]}"
        )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def python_fallback_trial(
    sizes: tuple[int, ...], accesses: int, bw_bytes: int, bw_repeats: int
) -> dict[str, float]:
    """Proxy metrics only: bytearray slice copy (C-level memcpy) plus an interpreted chain."""
    metrics: dict[str, float] = {}
    src = bytearray(b"\x5a" * 4096) * (bw_bytes // 4096)
    dst = bytearray(len(src))
    t0 = time.perf_counter_ns()
    for _ in range(bw_repeats):
        dst[:] = src
    t1 = time.perf_counter_ns()
    metrics[f"bandwidth_gbs@{bw_bytes}"] = (len(src) * bw_repeats) / (t1 - t0)
    del src, dst
    for size in sizes:
        used = min(size, FALLBACK_MAX_BYTES)
        n = max(used // 64, 1024)
        perm = list(range(n))
        random.Random(FALLBACK_SEED).shuffle(perm)
        chain = [0] * n
        for i, item in enumerate(perm):
            chain[item] = perm[(i + 1) % n]
        acc = 0
        iters = max(accesses // 8, 1000)
        t0 = time.perf_counter_ns()
        for _ in range(iters):
            acc = chain[acc]
        t1 = time.perf_counter_ns()
        metrics[f"latency_proxy_ns@{used}"] = (t1 - t0) / iters
    return metrics


def one_trial(
    method: dict[str, Any],
    sizes: tuple[int, ...],
    accesses: int,
    bw_bytes: int,
    bw_repeats: int,
    alu_iters: int,
) -> dict[str, float]:
    metrics: dict[str, float] = {}
    if method["kind"] == "compiled-c-helper":
        binary = method["helper_path"]
        for size in sizes:
            out = run_helper(
                binary, ["latency", str(size), str(accesses), str(0x2545F4914F6CDD1D)]
            )
            metrics[f"latency_ns@{out['bytes']}"] = out["ns_per_access"]
        out = run_helper(binary, ["bandwidth", str(bw_bytes), str(bw_repeats)])
        metrics[f"bandwidth_gbs@{out['bytes']}"] = out["gb_per_s"]
        out = run_helper(binary, ["alu", str(alu_iters)])
        metrics["alu_ns_per_op"] = out["ns_per_op"]
    else:
        metrics = python_fallback_trial(sizes, accesses, bw_bytes, bw_repeats)
    return metrics


def summarize(trials: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    keys = sorted({k for t in trials for k in t})
    summary: dict[str, dict[str, float]] = {}
    for key in keys:
        values = [t[key] for t in trials if isinstance(t.get(key), (int, float))]
        if not values:
            continue
        if len(values) >= 4:
            q1, _, q3 = statistics.quantiles(values, n=4)
        else:
            q1, q3 = min(values), max(values)
        summary[key] = {
            "n": len(values),
            "median": statistics.median(values),
            "q1": q1,
            "q3": q3,
            "min": min(values),
            "max": max(values),
        }
    return summary


def classify(
    baseline: list[float], modified: list[float], higher_is_better: bool = False
) -> dict[str, Any]:
    """Compare two sample sets. Latency/ns metrics are lower-is-better; throughput is not."""
    med_b, med_m = statistics.median(baseline), statistics.median(modified)
    delta_pct = (med_m - med_b) / med_b * 100.0
    if len(baseline) >= 4:
        q1b, _, q3b = statistics.quantiles(baseline, n=4)
    else:
        q1b, q3b = min(baseline), max(baseline)
    if len(modified) >= 4:
        q1m, _, q3m = statistics.quantiles(modified, n=4)
    else:
        q1m, q3m = min(modified), max(modified)
    below = sum(1 for v in modified if v < med_b) / len(modified)
    disjoint = q3m < q1b or q3b < q1m
    separated = disjoint or below >= 0.8 or below <= 0.2
    gain_pct = delta_pct if not higher_is_better else -delta_pct
    if gain_pct <= -5.0 and separated:
        verdict = "MEASURABLE_IMPROVEMENT"
    elif gain_pct >= 5.0 and separated:
        verdict = "MEASURABLE_REGRESSION"
    elif abs(gain_pct) < 2.0:
        verdict = "NO_MEASURABLE_EFFECT"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "lower_is_better": not higher_is_better,
        "baseline_median": med_b,
        "modified_median": med_m,
        "baseline_iqr": [q1b, q3b],
        "modified_iqr": [q1m, q3m],
        "delta_pct": delta_pct,
        "modified_below_baseline_median_fraction": below,
        "iqr_disjoint": disjoint,
        "verdict": verdict,
    }


def compare_documents(base: dict[str, Any], mod: dict[str, Any]) -> dict[str, Any]:
    base_trials = [t["metrics"] for t in base["trials"]]
    mod_trials = [t["metrics"] for t in mod["trials"]]
    keys = sorted({k for t in base_trials + mod_trials for k in t})
    metrics: dict[str, Any] = {}
    for key in keys:
        b = [t[key] for t in base_trials if isinstance(t.get(key), (int, float))]
        m = [t[key] for t in mod_trials if isinstance(t.get(key), (int, float))]
        if b and m:
            metrics[key] = classify(b, m, higher_is_better=key.startswith("bandwidth_"))
    alu_pct = metrics.get("alu_ns_per_op", {}).get("delta_pct")
    alu_ok = alu_pct is None or abs(alu_pct) <= 3.0
    pb, pm = base.get("parameters", {}), mod.get("parameters", {})
    checks = {
        "same_kernel": base.get("host", {}).get("kernel")
        == mod.get("host", {}).get("kernel"),
        "same_cpu_affinity": pb.get("cpu") == pm.get("cpu"),
        "same_method": base.get("method", {}).get("kind")
        == mod.get("method", {}).get("kind"),
        "same_helper_sha256": base.get("method", {}).get("helper_sha256")
        == mod.get("method", {}).get("helper_sha256"),
        "same_sizes": pb.get("sizes") == pm.get("sizes"),
        "same_iteration_counts": (
            pb.get("accesses"),
            pb.get("bw_bytes"),
            pb.get("bw_repeats"),
            pb.get("alu_iters"),
        )
        == (
            pm.get("accesses"),
            pm.get("bw_bytes"),
            pm.get("bw_repeats"),
            pm.get("alu_iters"),
        ),
        "min_trials_each_3": min(pb.get("repeats", 0), pm.get("repeats", 0)) >= 3,
        "alu_drift_within_3pct": alu_ok,
    }
    valid = all(checks.values())
    latency_keys = [k for k in metrics if k.startswith("latency_ns@")]
    primary = (
        max(latency_keys, key=lambda k: int(k.split("@")[1])) if latency_keys else None
    )
    cache_regressions = [
        k
        for k in latency_keys
        if int(k.split("@")[1]) <= CACHE_DOMAIN_CEILING_BYTES
        and metrics[k]["verdict"] == "MEASURABLE_REGRESSION"
    ]
    bw_regressions = [
        k
        for k in metrics
        if k.startswith("bandwidth_gbs@")
        and metrics[k]["verdict"] == "MEASURABLE_REGRESSION"
    ]
    coherence_ok = not cache_regressions and not bw_regressions
    if primary is None:
        overall = "PROXY_METHOD_LATENCY_UNUSED"
    elif not valid:
        overall = "INVALID_RUN_PAIR"
    elif metrics[primary]["verdict"] == "MEASURABLE_IMPROVEMENT" and not coherence_ok:
        overall = "INCOHERENT_RESULT"
    else:
        overall = metrics[primary]["verdict"]
    return {
        "schema": SCHEMA_COMPARE,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "baseline_label": base.get("label"),
        "modified_label": mod.get("label"),
        "baseline_host_is_bc250": base.get("host_is_bc250"),
        "modified_host_is_bc250": mod.get("host_is_bc250"),
        "alu_delta_pct": alu_pct,
        "equivalence_checks": checks,
        "run_pair_valid": valid,
        "coherence_ok": coherence_ok,
        "cache_domain_regressions": cache_regressions,
        "bandwidth_regressions": bw_regressions,
        "cache_domain_ceiling_bytes": CACHE_DOMAIN_CEILING_BYTES,
        "primary_latency_metric": primary,
        "metrics": metrics,
        "overall_verdict": overall,
        "rule": (
            "improvement requires primary DRAM latency verdict MEASURABLE_IMPROVEMENT "
            "AND no cache-domain or bandwidth regression; ALU drift > limit invalidates the pair"
        ),
        "thresholds": {
            "improvement_latency_pct": 5.0,
            "inconclusive_band_pct": 2.0,
            "alu_drift_limit_pct": 3.0,
            "iqr_disjoint_or_below_fraction": 0.8,
        },
    }


def cmd_run(args: argparse.Namespace) -> int:
    quick = args.quick
    meta = host_metadata()
    if args.cpu is not None:
        os.sched_setaffinity(0, {args.cpu})
    meta["cpu_affinity_effective"] = sorted(os.sched_getaffinity(0))
    if not meta["host_is_bc250"] and not args.allow_non_bc250:
        print(
            json.dumps(
                {
                    "refused": "host DRM ids are not the BC-250 APU 1002:13fe; "
                    "pass --allow-non-bc250 for a method self-test only",
                    "drm_pci_ids": meta["drm_pci_ids"],
                }
            ),
            file=sys.stderr,
        )
        return 2
    sizes = LATENCY_SIZES_QUICK if quick else LATENCY_SIZES_FULL
    accesses = ACCESSES_QUICK if quick else ACCESSES_FULL
    bw_bytes = BW_BYTES_QUICK if quick else BW_BYTES_FULL
    bw_repeats = BW_REPEATS_QUICK if quick else BW_REPEATS_FULL
    alu_iters = ALU_ITERS_QUICK if quick else ALU_ITERS_FULL
    repeats = args.repeats if args.repeats else (1 if quick else 5)
    tmpdir = Path(tempfile.mkdtemp(prefix="bc250-perf-"))
    try:
        method = {
            "kind": "python-fallback",
            "cc": None,
            "helper_sha256": None,
            "compile_returncode": None,
            "helper_path": None,
            "latency_metric_class": "proxy-interpreter-overhead",
        }
        if args.method != "python":
            method = compile_helper(tmpdir)
            if method["kind"] != "compiled-c-helper" and args.method == "c":
                sys.stderr.write(
                    json.dumps({"error": "C helper build failed", "detail": method})
                    + "\n"
                )
                return 3
        trials = []
        for index in range(repeats):
            metrics = one_trial(
                method, sizes, accesses, bw_bytes, bw_repeats, alu_iters
            )
            trials.append({"index": index, "metrics": metrics})
        doc = {
            "schema": SCHEMA,
            "label": args.label,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "host_is_bc250": meta["host_is_bc250"],
            "host": meta,
            "method": {k: v for k, v in method.items() if k != "helper_path"},
            "parameters": {
                "sizes": list(sizes),
                "accesses": accesses,
                "bw_bytes": bw_bytes,
                "bw_repeats": bw_repeats,
                "alu_iters": alu_iters,
                "repeats": repeats,
                "quick": quick,
                "compiler_used": method.get("cc"),
                "cpu": args.cpu,
            },
            "trials": trials,
            "summary": summarize([t["metrics"] for t in trials]),
            "hardware_mutation": False,
            "evidence_note": (
                "BC-250 runtime measurement"
                if meta["host_is_bc250"]
                else "NON-BC-250 host: method self-test only, not board data"
            ),
            "notes": args.notes or "",
        }
        text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
        if args.out:
            Path(args.out).write_text(text)
            print(
                json.dumps(
                    {
                        "written": args.out,
                        "label": args.label,
                        "repeats": repeats,
                        "method": method["kind"],
                        "host_is_bc250": meta["host_is_bc250"],
                    }
                )
            )
        else:
            print(text, end="")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def cmd_compare(args: argparse.Namespace) -> int:
    base = json.loads(Path(args.compare[0]).read_text())
    mod = json.loads(Path(args.compare[1]).read_text())
    doc = compare_documents(base, mod)
    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(text)
        print(
            json.dumps(
                {
                    "written": args.out,
                    "overall_verdict": doc["overall_verdict"],
                    "primary_latency_metric": doc["primary_latency_metric"],
                    "run_pair_valid": doc["run_pair_valid"],
                }
            )
        )
    else:
        print(text, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="run one measurement snapshot (JSON out)")
    run.add_argument("--label", default="unnamed")
    run.add_argument("--out")
    run.add_argument(
        "--repeats",
        type=int,
        default=0,
        help="trials per snapshot (default 5, or 1 with --quick)",
    )
    run.add_argument("--quick", action="store_true")
    run.add_argument("--method", choices=("auto", "c", "python"), default="auto")
    run.add_argument("--allow-non-bc250", action="store_true")
    run.add_argument("--notes", default="")
    run.add_argument(
        "--cpu",
        type=int,
        default=None,
        help="pin this harness and its helper to one CPU",
    )
    run.set_defaults(func=cmd_run)
    cmp_ = sub.add_parser(
        "compare", help="compare two snapshots with the decision rule"
    )
    cmp_.add_argument("compare", nargs=2, metavar=("BASELINE_JSON", "MODIFIED_JSON"))
    cmp_.add_argument("--out")
    cmp_.set_defaults(func=cmd_compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
