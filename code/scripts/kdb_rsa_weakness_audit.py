#!/usr/bin/env python3
"""Bounded weak-RSA prerequisite audit for the BC-250 public $KDB records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


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


def primes(limit: int):
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p:limit + 1:p] = b"\x00" * (((limit - p * p) // p) + 1)
    return [i for i, value in enumerate(sieve) if value]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    image = args.image.read_bytes()
    if len(image) != 0x1000000:
        raise ValueError("expected exact 16 MiB SPI image")

    specs = [("t50", 0x9DAD00, 0xDD0), ("t51", 0x9DBB00, 0x740)]
    keys = []
    for tag, offset, size in specs:
        blob = image[offset:offset + size]
        body = blob[0x100:]
        record_offset = 0x50
        while record_offset + 0x150 <= len(body):
            record = body[record_offset:record_offset + 0x150]
            rec_size = int.from_bytes(record[0:4], "little")
            exponent = int.from_bytes(record[0x0C:0x10], "little")
            bits = int.from_bytes(record[0x20:0x24], "little")
            if rec_size not in (0, 0x150) or exponent not in (3, 5, 17, 65537) or bits not in (1024, 2048):
                break
            modulus_bytes = record[0x50:0x50 + bits // 8]
            modulus_le = int.from_bytes(modulus_bytes, "little")
            modulus_be = int.from_bytes(modulus_bytes, "big")
            # Select the encoding that has the declared bit length.
            candidates = [("little", modulus_le), ("big", modulus_be)]
            encoding, modulus = min(candidates, key=lambda item: abs(item[1].bit_length() - bits))
            keys.append({
                "source": tag,
                "record_offset": hex(record_offset),
                "index": int.from_bytes(record[4:8], "little"),
                "kid": record[0x10:0x20].hex(),
                "bits_declared": bits,
                "bits_observed": modulus.bit_length(),
                "exponent": exponent,
                "modulus_encoding": encoding,
                "modulus_sha256": hashlib.sha256(modulus_bytes).hexdigest(),
                "n": modulus,
            })
            record_offset += 0x150

    small_primes = primes(100_000)
    for key in keys:
        n = key["n"]
        key["small_prime_factor_le_100000"] = next((p for p in small_primes if n % p == 0), None)
        key["wiener_small_d"] = wiener(key["exponent"], n)
        a = math.isqrt(n)
        if a * a < n:
            a += 1
        fermat = None
        for delta in range(1_000_001):
            b2 = (a + delta) * (a + delta) - n
            b = math.isqrt(b2)
            if b * b == b2:
                p = a + delta - b
                if 1 < p < n and n % p == 0:
                    fermat = delta
                    break
        key["fermat_factor_found_within_1000000_steps"] = fermat is not None
        del key["n"]

    shared = []
    # Reconstruct n from the source bytes for pairwise GCD without publishing it.
    numeric = []
    for key in keys:
        tag, offset, size = next(s for s in specs if s[0] == key["source"])
        ro = int(key["record_offset"], 16)
        rec = image[offset + 0x100 + ro:offset + 0x100 + ro + 0x150]
        raw = rec[0x50:0x50 + key["bits_declared"] // 8]
        numeric.append(int.from_bytes(raw, key["modulus_encoding"]))
    for i in range(len(numeric)):
        for j in range(i + 1, len(numeric)):
            g = math.gcd(numeric[i], numeric[j])
            if 1 < g < numeric[i] and g < numeric[j]:
                shared.append([i, j, g.bit_length()])

    report = {
        "tool": "scripts/kdb_rsa_weakness_audit.py",
        "input": str(args.image),
        "input_size": len(image),
        "input_sha256": hashlib.sha256(image).hexdigest(),
        "key_count": len(keys),
        "unique_modulus_hashes": len({k["modulus_sha256"] for k in keys}),
        "shared_nontrivial_factors": shared,
        "bounds": {"small_prime_limit": 100_000, "fermat_steps": 1_000_000},
        "keys": keys,
        "not_applicable_without_additional_evidence": [
            "small-e ciphertext attacks", "common-modulus ciphertext attack",
            "padding oracle", "CRT fault", "partial-prime Coppersmith",
        ],
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
