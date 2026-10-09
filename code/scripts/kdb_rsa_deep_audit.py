#!/usr/bin/env python3
"""Deep weak-key audit across every BC-250-related image in the repo.

Extends scripts/kdb_rsa_weakness_audit.py (which used hardcoded offsets on
one dump and trial division only to 1e5 / Fermat 1e6):

- key discovery: the signature scan from scripts/psp_ps1_verify.py
  (u32 size==0x150, e@+0x0C in {3,5,17,65537}, bits@+0x20 in {1024,2048},
  kid@+0x10, modulus@+0x50) -> works on any image, no hardcoded offsets;
- per unique modulus: trial division to 1e6, Pollard-Brent rho with a
  wall-clock budget, Fermat to a step budget, Wiener small-d;
- ROCA (Infineon) fingerprint: n mod p in <e> subgroup of Z_p* for the
  first 54 primes;
- batch GCD across ALL unique moduli from ALL images;
- cross-image kid->modulus consistency (a kid with two moduli anywhere
  would reopen the forgeable-anchor question closed on 2026-09-19).

Honesty: a negative result is NOT proof of unfactorability. A 2048-bit
modulus with nothing structurally wrong is out of reach; only the listed
structural weakness classes could have fallen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from psp_ps1_verify import kdb_keys  # noqa: E402  (scanning discovery)

ROOT = Path(__file__).resolve().parents[1]

TRIAL_LIMIT = 1_000_000
FERMAT_STEPS = 5_000_000
RHO_SECONDS = 60.0

IMAGES = [
    "evidence/donor/retroweb-20260916/BC250_2.00.bin",
    "evidence/donor/retroweb-20260916/BC250_3.00.bin",
    "evidence/donor/retroweb-20260916/BC250_3.00_CHIPSETMENU.bin",
    "evidence/donor/retroweb-20260916/BC250_5.00.bin",
    "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin",
    "evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3",
    "evidence/donor/chat-oc-profiles-20260904/01_BC250_SYNC_FclkUclk_1to1_Mclk1750_StockCPU.bin",
    "evidence/donor/chat-oc-profiles-20260904/02_BC250_SYNC_Full_1to1to1_1333MHz_StockCPU.bin",
    "evidence/donor/chat-oc-profiles-20260904/03_BC250_SYNC_Full_1to1to1_1750MHz_StockCPU.bin",
    "evidence/donor/chat-oc-profiles-20260904/dfg_idx06_up_130.bin",
    "evidence/programmer/reads/20260911/read-a.bin",
    "evidence/programmer/reads/20260912/read-h-prewrite-d3b2-retest.bin",
]
EXTRA_GLOB = "~/.cache/bc250/c0a-extract/**/*.bin"


def small_primes(limit: int) -> list[int]:
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p : limit + 1 : p] = b"\x00" * (((limit - p * p) // p) + 1)
    return [i for i, v in enumerate(sieve) if v]


def trial_division(n: int, primes: list[int]) -> int | None:
    for p in primes:
        if p * p > n:
            return None
        if n % p == 0:
            return p
    return None


def fermat(n: int, steps: int) -> tuple[int, int] | None:
    a = math.isqrt(n)
    if a * a < n:
        a += 1
    for _ in range(steps):
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            return a - b, a + b
        a += 1
    return None


def brent_rho(n: int, budget_s: float) -> dict:
    """Pollard-Brent with a wall-clock budget; several (c, seed) rounds."""
    deadline = time.monotonic() + budget_s
    rounds = 0
    iters = 0
    if n % 2 == 0:
        return {"factor": 2, "rounds": 0, "iterations": 0}
    while time.monotonic() < deadline:
        rounds += 1
        y = random.randrange(2, n)
        c = random.randrange(1, n - 1)
        m = 128
        g = r = q = 1
        x = ys = y
        while g == 1:
            if time.monotonic() > deadline:
                return {"factor": None, "rounds": rounds, "iterations": iters}
            x = y
            for _ in range(r):
                y = (y * y + c) % n
                iters += 1
            k = 0
            while k < r and g == 1:
                ys = y
                lim = min(m, r - k)
                for _ in range(lim):
                    y = (y * y + c) % n
                    q = q * abs(x - y) % n
                    iters += 1
                g = math.gcd(q, n)
                k += m
            r *= 2
            if g == n:
                break
        if g in (1, n):
            continue
        # backtrack once for the rare q == 0 collapse
        y = ys
        g2 = 1
        while g2 == 1:
            g2 = math.gcd(abs(x - y), n)
            y = (y * y + c) % n
        if g2 not in (1, n):
            return {"factor": g2, "rounds": rounds, "iterations": iters}
    return {"factor": None, "rounds": rounds, "iterations": iters}


def convergents(e: int, n: int):
    cf = []
    a, b = e, n
    while b:
        cf.append(a // b)
        a, b = b, a % b
    p0, p1, q0, q1 = 0, 1, 1, 0
    for value in cf:
        p0, p1 = p1, value * p1 + p0
        q0, q1 = q1, value * q1 + q0
        yield p1, q1


def wiener(e: int, n: int) -> bool:
    for k, d in convergents(e, n):
        if not k or (e * d - 1) % k:
            continue
        phi = (e * d - 1) // k
        s = n - phi + 1
        disc = s * s - 4 * n
        if disc >= 0:
            root = math.isqrt(disc)
            if root * root == disc and (s + root) % 2 == 0:
                p = (s + root) // 2
                if p > 1 and n % p == 0:
                    return True
    return False


def roca_fingerprint(n: int, e: int, primes: list[int]) -> dict:
    """ROCA detection: n mod p inside the subgroup <e> of Z_p* for all p.

    Infineon ROCA primes are p = k*M + e^a; then n = p*q keeps n mod p
    inside <e> for the small primes dividing the primorial M. All-primes
    membership is the published detection signature.
    """
    passed, failed = 0, []
    for p in primes[:54]:
        if p in (2,):
            continue
        np = n % p
        if np == 0:
            failed.append(p)
            continue
        # subgroup generated by e mod p
        elem = e % p
        if elem == 0:
            failed.append(p)
            continue
        sub = {elem}
        cur = elem
        while True:
            cur = cur * elem % p
            if cur == elem or cur == 1:
                break
            sub.add(cur)
        sub.add(1)
        if np in sub:
            passed += 1
        else:
            failed.append(p)
    return {"passed": passed, "failed_sample": failed[:8], "suspect": not failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evidence/firmware-audit/20260924-kdb-deep-audit/result.json",
    )
    ap.add_argument("--rho-seconds", type=float, default=RHO_SECONDS)
    ap.add_argument("--skip-rho", action="store_true")
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    images = []
    for rel in IMAGES:
        p = ROOT / rel
        if p.exists():
            images.append(p)
    c0a_dir = Path.home() / ".cache/bc250/c0a-extract"
    if c0a_dir.exists():
        for p in c0a_dir.rglob("*"):
            if p.is_file() and p.stat().st_size == 0x1000000:
                images.append(p)

    primes = small_primes(TRIAL_LIMIT)
    keys_by_modulus: dict[str, dict] = {}
    kid_moduli: dict[str, set[str]] = {}
    image_reports = []
    for img in images:
        data = img.read_bytes()
        keys = kdb_keys(data)
        rep = {
            "image": str(img.relative_to(ROOT))
            if str(img).startswith(str(ROOT))
            else str(img),
            "sha256_16": hashlib.sha256(data).hexdigest()[:16],
            "keys": len(keys),
        }
        for kid, (e, mod_bytes) in keys.items():
            n = int.from_bytes(mod_bytes, "little")
            mh = hashlib.sha256(mod_bytes).hexdigest()
            kid_moduli.setdefault(kid, set()).add(mh)
            if mh in keys_by_modulus:
                keys_by_modulus[mh]["kids"].add(kid)
                keys_by_modulus[mh]["images"].append(rep["image"])
                continue
            keys_by_modulus[mh] = {
                "kid": kid,
                "e": e,
                "bits": len(mod_bytes) * 8,
                "modulus_sha256": mh,
                "n": n,
                "kids": {kid},
                "images": [rep["image"]],
            }
        image_reports.append(rep)
        print(f"{rep['image']}: {len(keys)} keys")

    # cross-image consistency
    inconsistent = {k: sorted(v) for k, v in kid_moduli.items() if len(v) > 1}

    results = []
    t0 = time.time()
    for mh, k in sorted(keys_by_modulus.items()):
        n = k["n"]
        entry = {
            "kid": sorted(k["kids"]),
            "e": k["e"],
            "bits": k["bits"],
            "modulus_sha256": mh,
            "images": sorted(set(k["images"])),
        }
        entry["trial_division_1e6"] = trial_division(n, primes)
        entry["fermat_5e6"] = fermat(n, FERMAT_STEPS) if k["bits"] == 2048 else None
        entry["wiener_small_d"] = wiener(k["e"], n)
        entry["roca"] = roca_fingerprint(n, k["e"], primes)
        if a.skip_rho:
            entry["rho"] = {"skipped": True}
        else:
            entry["rho"] = brent_rho(n, a.rho_seconds)
        results.append(entry)
        fact = (
            entry["trial_division_1e6"]
            or (entry["rho"] or {}).get("factor")
            or entry["fermat_5e6"]
        )
        print(
            f"  kid {entry['kid'][0][:8]}… bits={k['bits']} "
            f"trial={'HIT ' + str(fact) if fact else 'no'} "
            f"roca={'SUSPECT' if entry['roca']['suspect'] else 'no'} "
            f"rho={'FACTOR ' + str(entry['rho']['factor']) if entry['rho'].get('factor') else 'no'}"
        )

    # batch GCD across all unique moduli
    mods = [(mh, k["n"]) for mh, k in keys_by_modulus.items()]
    shared = []
    for i in range(len(mods)):
        for j in range(i + 1, len(mods)):
            g = math.gcd(mods[i][1], mods[j][1])
            if g > 1:
                shared.append([mods[i][0][:16], mods[j][0][:16], str(g)])

    out = {
        "tool": "scripts/kdb_rsa_deep_audit.py",
        "bounds": {
            "trial_division_limit": TRIAL_LIMIT,
            "fermat_steps": FERMAT_STEPS,
            "rho_seconds_per_key": None if a.skip_rho else a.rho_seconds,
            "roca_primes": 53,
        },
        "images": image_reports,
        "unique_moduli": len(keys_by_modulus),
        "cross_image_kid_consistency": {
            "inconsistent_kids": inconsistent,
            "verdict": "CONSISTENT"
            if not inconsistent
            else "INCONSISTENT (reopen forgeable-anchor question)",
        },
        "batch_gcd_shared_factors": shared,
        "keys": results,
        "elapsed_seconds": round(time.time() - t0, 1),
        "honesty": "negative results close only the listed structural classes; a sound 2048-bit RSA modulus is out of reach",
    }
    a.output.write_text(json.dumps(out, indent=2) + "\n")
    print(
        f"\nunique moduli: {len(keys_by_modulus)}  shared GCDs: {len(shared)}  "
        f"inconsistent kids: {len(inconsistent)}  -> {a.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
