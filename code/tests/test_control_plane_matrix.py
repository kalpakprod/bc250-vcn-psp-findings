"""Deterministic acceptance matrix for the BC250 control-plane boundary.

These checks deliberately stay host-side: they inspect the finite callable
surface and wire-contract source, and run the package preflight without
starting a Decky service or touching hardware.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "candidates/bc250-decky-native/bc250-quick-access"
BACKEND = PLUGIN / "main.py"
UI = PLUGIN / "src/index.tsx"
CONTRACT = PLUGIN / "src/contract.ts"


def _operations_from_contract() -> set[str]:
    text = CONTRACT.read_text(encoding="utf-8")
    match = re.search(r"CONTROL_OPERATIONS\s*=\s*\[(.*?)\]\s*as const", text, re.S)
    assert match, "CONTROL_OPERATIONS must remain a finite literal list"
    return set(re.findall(r'"([a-z][a-z0-9_]*)"', match.group(1)))


def _callables_from_ui() -> set[str]:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (PLUGIN / "src").rglob("*.ts*")
        if path.suffix in {".ts", ".tsx"}
    )
    found = set(re.findall(r'callable<[^>]+>\("([a-z][a-z0-9_]*)"\)', source))
    # A typed custom wrapper is still a finite Decky operation. Keep parity
    # checking the literal operation at its dispatch boundary.
    found.update(re.findall(r'operation:\s*"([a-z][a-z0-9_]*)"', source))
    return found


def _methods_from_backend() -> set[str]:
    return set(
        re.findall(
            r"^\s+(?:async )?def ([a-z][a-z0-9_]*)\(",
            BACKEND.read_text(encoding="utf-8"),
            re.M,
        )
    )


def test_callable_parity_is_exact():
    operations = _operations_from_contract()
    ui = _callables_from_ui()
    backend = _methods_from_backend()
    assert operations == ui, (
        f"contract/UI drift: missing={operations - ui}, extra={ui - operations}"
    )
    assert operations <= backend, f"backend missing operations: {operations - backend}"


def test_contract_has_fail_closed_schema_guards():
    text = CONTRACT.read_text(encoding="utf-8")
    for guard in (
        "isCapability",
        "isCapabilityAvailable",
        "isControlRequest",
        "isControlResult",
        "isControlStatus",
        "parseControlRequest",
        "parseControlResult",
    ):
        assert f"function {guard}" in text or f"const {guard}" in text
    for field in (
        "CAPABILITY_STATES",
        "OPERATION_STATUSES",
        "isTransactionMetadata",
        "isReadbackMetadata",
    ):
        assert field in text


def test_capability_classification_fails_closed():
    text = CONTRACT.read_text(encoding="utf-8")
    assert re.search(
        r"isCapabilityAvailable\s*=.*?value\.state === \"available\"", text, re.S
    )
    assert "missing, blocked, degraded, or malformed" in text


def test_controller_focus_structure_is_explicit():
    text = "\n".join(
        path.read_text(encoding="utf-8") for path in (PLUGIN / "src").rglob("*.tsx")
    )
    # Source-structure check only, not a physical controller-focus test.
    # The first status row is focusable and repeated actions use busy guards.
    assert "focusable" in text
    assert text.count("disabled={busy}") >= 10
    assert "PanelSectionRow" in text and "PanelSection" in text


def test_packaging_preflight_typechecks_without_network_or_hardware():
    package = json.loads((PLUGIN / "package.json").read_text(encoding="utf-8"))
    assert package["scripts"]["build"] == "rollup -c"
    result = subprocess.run(
        ["pnpm", "exec", "tsc", "--noEmit"],
        cwd=PLUGIN,
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (PLUGIN / "plugin.json").is_file()


def test_wire_guards_reject_failure_injections():
    cache = Path.home() / ".cache/bc250-test-matrix"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as directory:
        compiled = subprocess.run(
            [
                "pnpm",
                "exec",
                "tsc",
                str(CONTRACT),
                "--target",
                "es2020",
                "--module",
                "commonjs",
                "--outDir",
                directory,
                "--skipLibCheck",
            ],
            cwd=PLUGIN,
            text=True,
            capture_output=True,
            timeout=60,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        js = r"""
const assert = require("node:assert/strict");
const c = require(process.argv[1]);
const now = "2026-10-01T00:00:00Z";
assert.deepEqual([...c.CAPABILITY_STATES].sort(), ["available", "degraded", "unavailable", "blocked"].sort());
assert.deepEqual([...c.OPERATION_STATUSES].sort(), ["accepted", "running", "succeeded", "failed", "rejected"].sort());
for (const operation of c.CONTROL_OPERATIONS) {
  assert.equal(c.isControlRequest({version: 1, requestId: "fixture", operation}), true);
}
for (const operation of ["shell", "smn_write", "arbitrary_register", "", null]) {
  assert.equal(c.isControlRequest({version: 1, requestId: "fixture", operation}), false);
}
for (const state of c.CAPABILITY_STATES) {
  const value = {id: "cpu", state, observedAt: now};
  assert.equal(c.isCapability(value), true);
  assert.equal(c.isCapabilityAvailable(value), state === "available");
}
for (const value of [null, {}, [], {id: "cpu", state: "available", observedAt: "broken"}]) {
  assert.equal(c.isCapabilityAvailable(value), false);
}
assert.equal(c.isControlStatus({version: 1, capabilities: [{id: "cpu", state: "blocked"}]}), true);
assert.equal(c.isControlStatus({version: 1, capabilities: [{id: "cpu", state: "available"}, {id: "cpu", state: "blocked"}]}), false);
const success = {version: 1, requestId: "fixture", status: "succeeded", ok: true};
assert.equal(c.isControlResult(success), true);
assert.equal(c.isControlResult({...success, ok: false}), false);
assert.equal(c.isControlResult({...success, status: "failed", ok: false}), false);
assert.equal(c.isControlResult({...success, status: "failed", ok: false, error: {code: "fixture_error", message: "Injected failure"}}), true);
assert.equal(c.isReadbackMetadata({attempted: false, verified: true, observedAt: now}), false);
assert.equal(c.isReadbackMetadata({attempted: true, verified: true}), false);
assert.equal(c.isReadbackMetadata({attempted: true, verified: true, observedAt: now, hash: "a".repeat(64)}), true);
assert.equal(c.isTransactionMetadata({id: "fixture", phase: "rollback", startedAt: now, completedAt: "2026-09-30T00:00:00Z"}), false);
assert.throws(() => c.parseControlRequest({}), TypeError);
assert.throws(() => c.parseControlResult({}), TypeError);
process.stdout.write("wire guard matrix OK\n");
"""
        result = subprocess.run(
            ["node", "-e", js, str(Path(directory) / "contract.js")],
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout == "wire guard matrix OK\n"


def test_no_hardware_write_literals_in_contract():
    text = CONTRACT.read_text(encoding="utf-8").lower()
    assert "subprocess" not in text and "/dev/" not in text


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
