"""Real stock-signature controls, host crypto only. No ROM or key writes."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import psp_ps1_verify as verifier
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

source = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
image = source.read_bytes()
sha = hashlib.sha256(image).hexdigest()
assert sha == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
keys = verifier.kdb_keys(image)
results = []
for _, typ, size, offset in verifier.psp_entries(image):
    if typ not in (2, 0x28):
        continue
    _, parsed, _ = verifier.verify_container(image[offset : offset + size], keys)
    _, data, signature, (e, modulus) = parsed
    public = rsa.RSAPublicNumbers(e, int.from_bytes(modulus, "little")).public_key()
    cases = [
        ("original", data, signature),
        (
            "body_one_bit",
            data[:0x180] + bytes([data[0x180] ^ 1]) + data[0x181:],
            signature,
        ),
        ("signature_one_bit", data, bytes([signature[0] ^ 1]) + signature[1:]),
    ]
    observed = []
    for name, message, sig in cases:
        try:
            public.verify(
                sig,
                message,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                hashes.SHA256(),
            )
            status = "ACCEPT"
        except InvalidSignature:
            status = "REJECT"
        observed.append(status)
        results.append({"type": hex(typ), "input": name, "result": status})
    assert observed == ["ACCEPT", "REJECT", "REJECT"]
assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
print(
    json.dumps(
        {
            "classification": "HOST_CRYPTO_NOT_NATIVE_PSP",
            "tests": results,
            "source_unchanged": True,
        },
        indent=2,
    )
)
