#!/usr/bin/env python3
"""Pure fixed-frame encoding for a trusted private flash client; no device access."""

import struct
import zlib


def digest(value):
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("SHA256 hex required")
    raw = bytes.fromhex(value)
    if len(raw) != 32 or not any(raw):
        raise ValueError("Nonzero SHA256 required")
    return raw


def approval(
    tag,
    jedec,
    generation,
    image,
    approved,
    backup1,
    backup2,
    recovery=False,
    protected=False,
):
    """Caller attestations must come from verified preflight/owner decision, not this codec."""
    if not recovery or not protected:
        raise ValueError("Recovery and protected-region confirmations required")
    if image != approved or backup1 != backup2:
        raise ValueError("Digest binding mismatch")
    if (
        not 0 < tag < 2**64
        or jedec not in {0xC22018, 0xEF4018}
        or not 0 <= generation < 2**32
    ):
        raise ValueError("Expected adapter/chip/generation required")
    body = struct.pack(">BBHQII", 1, 3, 0, tag, jedec, generation)
    body += b"".join(digest(v) for v in (image, approved, backup1, backup2))
    return body + struct.pack(">I", zlib.crc32(body))


def sector(address, image, data):
    if (
        type(address) is not int
        or address < 0
        or address > 0x1000000 - 4096
        or address % 4096
    ):
        raise ValueError("Aligned bounded sector required")
    if not isinstance(data, bytes) or len(data) != 4096:
        raise ValueError("Exact immutable sector bytes required")
    body = struct.pack(">BBHI", 1, 0, 0, address) + digest(image) + data
    return body + struct.pack(">I", zlib.crc32(body))
