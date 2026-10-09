import json, os, shutil, stat, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import waveshare_psp_pipeline as w


def test_inventory_and_manifest():
    clean = b"xxBL_PUBLIC_KEY" + b"0" * 4 + b"TRUSTED_OS" + b"DRIVER_ENTRIESyy"
    patched = clean.replace(b"yy", b"zz")
    x = w.inventory(clean)
    assert x["markers"]["BL_PUBLIC_KEY"][0]["offset"] == 2
    m = w.manifest(clean, patched, "fixture")
    assert m["changed_ranges"] == [{"offset": len(clean) - 2, "size": 2}]


def test_cli_inspect(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"BL_PUBLIC_KEY")
    out = subprocess.check_output(
        [sys.executable, "scripts/waveshare_psp_pipeline.py", "inspect", str(p)]
    )
    assert json.loads(out)["sha256"] == w.sha256(p.read_bytes())


def _run_with_application_python(request, tmp_path):
    application_python = shutil.which("python3")
    assert application_python is not None, "application python3 not found"
    if Path(application_python).resolve() == Path(sys.executable).resolve():
        return False
    env = os.environ.copy()
    # Reuse the installed pure-Python runner, not the parent's native libraries.
    env["PYTHONPATH"] = str(Path(pytest.__file__).resolve().parent.parent)
    result = subprocess.run(
        [application_python, "-m", "pytest", request.node.nodeid, "-q",
         "--basetemp", str(tmp_path / "application-python")],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout, result.stdout + result.stderr
    print(f"Application-Python proof: {request.node.name}, "
          f"{Path(application_python).resolve()}, {result.stdout.strip()}")
    return True


def test_key_creation_is_exclusive_and_private_from_start(tmp_path, monkeypatch, request):
    if _run_with_application_python(request, tmp_path):
        return
    from cryptography.hazmat.primitives.asymmetric import rsa

    # Stub only expensive key generation/serialization; filesystem IO is real.
    monkeypatch.setattr(rsa, "generate_private_key", lambda **kwargs:
                        SimpleNamespace(private_bytes=lambda *args: b"dummy-not-a-key"))
    observed_modes = []
    original_fdopen = os.fdopen

    def checked_fdopen(fd, *args, **kwargs):
        observed_modes.append(stat.S_IMODE(os.fstat(fd).st_mode))
        return original_fdopen(fd, *args, **kwargs)

    monkeypatch.setattr(os, "fdopen", checked_fdopen)
    path = tmp_path / "new" / "dummy.pem"
    w.generate_key(path)
    assert path.read_bytes() == b"dummy-not-a-key"
    assert observed_modes == [0o600]
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        w.generate_key(path)
    assert path.read_bytes() == b"dummy-not-a-key"
    link = tmp_path / "link.pem"
    link.symlink_to(path)
    with pytest.raises(FileExistsError):
        w.generate_key(link)
    assert link.is_symlink()
    assert path.read_bytes() == b"dummy-not-a-key"


@pytest.mark.parametrize("extra", [[], ["--sha256", ""], ["--public-key", "absent.pem"],
    ["--sha256", "0" * 64, "--signature", "absent.sig", "--message", "absent.bin"]])
def test_verify_rejects_missing_or_partial_criteria(tmp_path, extra):
    image = tmp_path / "dummy.bin"
    image.write_bytes(b"fixture")
    result = subprocess.run([sys.executable, "scripts/waveshare_psp_pipeline.py",
                             "verify", str(image), *extra], capture_output=True)
    assert result.returncode == 2
    assert b'"verified": true' not in result.stdout


def test_verify_sha_and_full_pss_criteria(tmp_path, monkeypatch, capsys, request):
    with capsys.disabled():
        if _run_with_application_python(request, tmp_path):
            return
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    image = tmp_path / "dummy.bin"
    image.write_bytes(b"fixture")
    digest = w.sha256(b"fixture")
    base = ["waveshare_psp_pipeline.py", "verify", str(image)]
    monkeypatch.setattr(sys, "argv", base + ["--sha256", digest])
    assert w.main() == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    monkeypatch.setattr(sys, "argv", base + ["--sha256", "0" * 64])
    assert w.main() == 1
    assert json.loads(capsys.readouterr().out)["verified"] is False

    # Disposable in-memory test credential; no private key is serialized to disk.
    key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    public, message, signature = (tmp_path / name for name in
                                  ("dummy-public.pem", "message.bin", "signature.bin"))
    public.write_bytes(key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    message.write_bytes(b"dummy signed message")
    signature.write_bytes(key.sign(message.read_bytes(), padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256()))
    args = ["--public-key", str(public), "--signature", str(signature),
            "--message", str(message)]
    monkeypatch.setattr(sys, "argv", base + args)
    assert w.main() == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    monkeypatch.setattr(sys, "argv", base + args + ["--sha256", "0" * 64])
    assert w.main() == 1
    assert json.loads(capsys.readouterr().out)["verified"] is False
    message.write_bytes(b"tampered dummy message")
    monkeypatch.setattr(sys, "argv", base + args + ["--sha256", digest])
    assert w.main() == 1
    assert json.loads(capsys.readouterr().out)["verified"] is False
