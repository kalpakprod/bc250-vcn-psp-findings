#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def mutate_u32_le(buf: bytearray, off: int, value: int) -> None:
    buf[off : off + 4] = int(value & 0xFFFFFFFF).to_bytes(4, "little")


def random_u32(rng: random.Random) -> int:
    choices = [
        0,
        1,
        2,
        0x7F,
        0xFF,
        0x100,
        0x3FFF,
        0x7FFFFFFF,
        0xFFFFFFFF,
    ]
    if rng.random() < 0.65:
        return rng.choice(choices)
    return rng.getrandbits(32)


def mutate_slb2(seed: bytes, rng: random.Random) -> bytearray:
    data = bytearray(seed)

    if data[:4] != b"SLB2":
        return data

    # Header fields in SLB2 layout used by this repo parser.
    version_off = 4
    file_count_off = 12
    block_count_off = 16
    entries_off = 32
    entry_size = 48

    # Keep magic but mutate parser-facing metadata heavily.
    if rng.random() < 0.25:
        # Unsupported versions exercise version rejection paths.
        data[version_off : version_off + 8] = rng.getrandbits(64).to_bytes(8, "little")

    mutate_u32_le(data, file_count_off, random_u32(rng))
    mutate_u32_le(data, block_count_off, random_u32(rng))

    # Corrupt random bytes globally.
    for _ in range(rng.randint(1, 16)):
        pos = rng.randrange(0, len(data))
        data[pos] ^= rng.randrange(1, 256)

    # Corrupt a few entry records if they exist.
    max_entries = max(0, (len(data) - entries_off) // entry_size)
    edit_entries = min(max_entries, rng.randint(1, 8))
    for _ in range(edit_entries):
        idx = rng.randrange(0, max_entries) if max_entries > 0 else 0
        base = entries_off + idx * entry_size
        if base + entry_size > len(data):
            break
        # offset_blocks
        mutate_u32_le(data, base + 0, random_u32(rng))
        # content_size
        mutate_u32_le(data, base + 4, random_u32(rng))
        # reserved low/high
        mutate_u32_le(data, base + 8, random_u32(rng))
        mutate_u32_le(data, base + 12, random_u32(rng))
        # name bytes
        for j in range(base + 16, base + 48):
            if rng.random() < 0.35:
                data[j] = rng.randrange(0, 256)

    return data


def run_case(mut_path: Path, timeout_s: float) -> tuple[str, str]:
    cmd = [
        "python3",
        "-c",
        (
            "from pathlib import Path;"
            "import tempfile, shutil;"
            "from pupx.parser import PupPackage;"
            "p=PupPackage.load(r'" + str(mut_path) + "');"
            "d=tempfile.mkdtemp(prefix='fuzz_extract_');"
            "p.extract_all(d);"
            "shutil.rmtree(d, ignore_errors=True)"
        ),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(Path(__file__).resolve().parents[1]),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return "timeout", "process timeout"

    if cp.returncode == 0:
        return "ok", "no exception"

    stderr = (cp.stderr or "").strip().splitlines()
    last = stderr[-1] if stderr else (cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else "non-zero exit")
    if "MemoryError" in cp.stderr:
        return "memory_error", last
    if "EOFError" in cp.stderr:
        return "eof_error", last
    if "ValueError" in cp.stderr:
        return "value_error", last
    return "crash", last


def main() -> int:
    ap = argparse.ArgumentParser(description="Mini fuzzing campaign for torus2 SLB2 parser/loader")
    ap.add_argument("--seed", required=True, help="Path to seed SLB2 file (e.g., stage0/torus2_firmware.bin)")
    ap.add_argument("--iterations", type=int, default=200, help="Number of fuzz cases")
    ap.add_argument("--timeout", type=float, default=1.5, help="Timeout per test case (seconds)")
    ap.add_argument("--out", default="fuzz_out/torus2_slb2", help="Output directory for corpus and report")
    ap.add_argument("--rand-seed", type=int, default=1337, help="PRNG seed for reproducibility")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    seed_path = Path(args.seed)
    if not seed_path.is_absolute():
        seed_path = (root / seed_path).resolve()
    out_dir = (root / args.out).resolve()
    cases_dir = out_dir / "cases"

    out_dir.mkdir(parents=True, exist_ok=True)
    cases_dir.mkdir(parents=True, exist_ok=True)

    seed = seed_path.read_bytes()
    rng = random.Random(args.rand_seed)

    started = time.time()
    stats: dict[str, int] = {}
    findings: list[dict[str, object]] = []

    for i in range(args.iterations):
        case_name = f"case_{i:04d}.slb2"
        case_path = cases_dir / case_name
        mut = mutate_slb2(seed, rng)
        case_path.write_bytes(mut)

        status, detail = run_case(case_path, args.timeout)
        stats[status] = stats.get(status, 0) + 1

        if status in {"timeout", "memory_error", "crash"}:
            findings.append(
                {
                    "case": case_name,
                    "status": status,
                    "detail": detail,
                    "size": len(mut),
                }
            )

    elapsed = time.time() - started
    report = {
        "seed": str(seed_path),
        "iterations": args.iterations,
        "timeout_s": args.timeout,
        "rand_seed": args.rand_seed,
        "elapsed_s": round(elapsed, 3),
        "stats": stats,
        "findings": findings,
    }

    (out_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Torus2 SLB2 Fuzz Report",
        "",
        f"- Seed: {seed_path}",
        f"- Iterations: {args.iterations}",
        f"- Timeout per case: {args.timeout}s",
        f"- Random seed: {args.rand_seed}",
        f"- Elapsed: {elapsed:.3f}s",
        "",
        "## Stats",
        "",
    ]
    for k in sorted(stats):
        lines.append(f"- {k}: {stats[k]}")
    lines.append("")
    lines.append("## Notable Findings")
    lines.append("")
    if findings:
        for f in findings[:50]:
            lines.append(f"- {f['case']}: {f['status']} ({f['detail']})")
    else:
        lines.append("- No timeouts/memory_error/crash in this run")

    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Done. Report: {out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
