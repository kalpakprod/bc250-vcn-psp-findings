#!/usr/bin/env python3
"""Offline, bounded PSP directory inspection and candidate preparation."""

from __future__ import annotations
import argparse, hashlib, json, os, struct
from pathlib import Path
from typing import Any

MARKERS = (b"BL_PUBLIC_KEY", b"TRUSTED_OS", b"DRIVER_ENTRIES")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def locate(data: bytes, marker: bytes) -> list[dict[str, int]]:
    out = []
    p = 0
    while (p := data.find(marker, p)) >= 0:
        out.append({"offset": p, "size": len(marker)})
        p += 1
    return out


def parse_psp_directory(data: bytes, offset: int | None = None) -> dict[str, Any]:
    """Parse proven AMD $PSP header (count at +8, 16-byte entries). Unknown fields stay UNKNOWN."""
    if offset is None:
        offset = data.find(b"$PSP")
    if offset < 0 or offset + 16 > len(data) or data[offset : offset + 4] != b"$PSP":
        return {"offset": "UNKNOWN", "count": "UNKNOWN", "entries": []}
    count = struct.unpack_from("<I", data, offset + 8)[0]
    entries = []
    end = offset + 0x10 + count * 16
    if count > 0x10000 or end > len(data):
        return {"offset": offset, "count": "UNKNOWN", "entries": []}
    for i in range(count):
        o = offset + 0x10 + i * 16
        typ, size, loc = struct.unpack_from("<IIQ", data, o)
        if typ == 0xFFFFFFFF:
            break
        entries.append({"index": i, "type": typ, "size": size, "location": loc})
    return {
        "offset": offset,
        "count": len(entries),
        "entries": entries,
        "checksum": struct.unpack_from("<I", data, offset + 4)[0],
    }


def inventory(data: bytes, path: str = "") -> dict[str, Any]:
    return {
        "path": path,
        "size": len(data),
        "sha256": sha256(data),
        "markers": {m.decode(): locate(data, m) for m in MARKERS},
        "psp_directory": parse_psp_directory(data),
    }


def changed_ranges(a: bytes, b: bytes) -> list[dict[str, int]]:
    out = []
    n = max(len(a), len(b))
    i = 0
    while i < n:
        if a[i : i + 1] != b[i : i + 1]:
            s = i
            while i < n and a[i : i + 1] != b[i : i + 1]:
                i += 1
            out.append({"offset": s, "size": i - s})
        else:
            i += 1
    return out


def manifest(original: bytes, candidate: bytes, label: str) -> dict[str, Any]:
    return {
        "format": "waveshare-psp-manifest-v2",
        "label": label,
        "clean": {"size": len(original), "sha256": sha256(original)},
        "patched": {"size": len(candidate), "sha256": sha256(candidate)},
        "changed_ranges": changed_ranges(original, candidate),
        "clean_markers": inventory(original)["markers"],
        "patched_markers": inventory(candidate)["markers"],
        "rollback": {"supported": True},
    }


def apply_patch(
    clean: Path, output: Path, offset: int, payload: bytes
) -> dict[str, Any]:
    data = clean.read_bytes()
    if offset < 0 or offset + len(payload) > len(data):
        raise ValueError("patch range outside image")
    candidate = bytearray(data)
    candidate[offset : offset + len(payload)] = payload
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    return manifest(data, bytes(candidate), output.name)


def rollback(original: Path, candidate: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(original.read_bytes())


def generate_key(path: Path, bits: int = 2048) -> None:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(payload)


def verify_pss(public_key: Path, message: bytes, signature: bytes) -> bool:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    try:
        serialization.load_pem_public_key(public_key.read_bytes()).verify(
            signature,
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    i = sp.add_parser("inspect")
    i.add_argument("image", type=Path)
    i.add_argument("--manifest", type=Path)
    p = sp.add_parser("patch")
    p.add_argument("clean", type=Path)
    p.add_argument("patched", type=Path)
    p.add_argument("--manifest", type=Path, required=True)
    k = sp.add_parser("keygen")
    k.add_argument("path", type=Path)
    v = sp.add_parser("verify")
    v.add_argument("image", type=Path)
    v.add_argument("--sha256")
    v.add_argument("--public-key", type=Path)
    v.add_argument("--signature", type=Path)
    v.add_argument("--message", type=Path)
    a = ap.parse_args()
    if a.cmd == "inspect":
        obj = inventory(a.image.read_bytes(), str(a.image))
        print(json.dumps(obj, indent=2, sort_keys=True))
        a.manifest and a.manifest.write_text(
            json.dumps(obj, indent=2, sort_keys=True) + "\n"
        )
    elif a.cmd == "patch":
        obj = manifest(a.clean.read_bytes(), a.patched.read_bytes(), a.patched.name)
        a.manifest.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
        print(json.dumps(obj, indent=2, sort_keys=True))
    elif a.cmd == "keygen":
        generate_key(a.path)
        print(json.dumps({"path": str(a.path), "type": "RSA-2048"}))
    else:
        signature_options = (a.public_key, a.signature, a.message)
        has_signature = all(option is not None for option in signature_options)
        if any(option is not None for option in signature_options) and not has_signature:
            ap.error('--public-key, --signature and --message must be supplied together')
        if a.sha256 is None and not has_signature:
            ap.error('verify requires --sha256 or complete signature criteria')
        if a.sha256 is not None and (len(a.sha256) != 64 or any(
                c not in '0123456789abcdefABCDEF' for c in a.sha256)):
            ap.error('--sha256 must be a 64-digit hexadecimal digest')
        data = a.image.read_bytes()
        ok = a.sha256 is None or sha256(data).lower() == a.sha256.lower()
        if has_signature:
            ok = (
                verify_pss(
                    a.public_key, a.message.read_bytes(), a.signature.read_bytes()
                )
                and ok
            )
        print(json.dumps({"sha256": sha256(data), "verified": ok}, sort_keys=True))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
