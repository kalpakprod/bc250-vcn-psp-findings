"""Host window -> actual C staging; RP2350 SHA peripheral is not emulated."""
import ctypes as c
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from image_pack import SparseImage, pack_image
from rig_transfer import window_commands
from toctou_plan import PlannedWindow, TOCTOUPlan

SRC = ROOT.parent / "waveshare-adapter-safe-v001/src"

class Stage(c.Structure):
    _fields_ = [("data", c.POINTER(c.c_uint8)), ("digest", c.c_uint8 * 32),
                ("address", c.c_uint32), ("length", c.c_uint32),
                ("received", c.c_uint32), ("active", c.c_bool),
                ("verified", c.c_bool)]

class Payload(c.Structure):
    _fields_ = [("data", c.POINTER(c.c_uint8)), ("length", c.c_uint32),
                ("mark", c.c_uint32), ("interval_m1", c.c_uint32),
                ("read_index", c.c_uint32)]

class RigTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache = Path.home() / ".cache/waveshare-toctou-stage-20261007"
        cache.mkdir(parents=True, exist_ok=True)
        cls.work = tempfile.TemporaryDirectory(dir=cache)
        library = Path(cls.work.name) / "stage.so"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-pedantic", "-shared", "-fPIC", str(SRC / "adapter_toctou_stage.c"),
                        str(SRC / "rig/rig_payload.c"),
                        "-o", str(library)], check=True, capture_output=True)
        cls.lib = c.CDLL(str(library))
        cls.begin = cls.lib.adapter_toctou_stage_begin
        cls.begin.argtypes = [c.POINTER(Stage), c.c_uint32, c.c_uint32, c.c_char_p,
                              c.POINTER(c.c_uint8)]
        cls.begin.restype = c.c_bool
        cls.load = cls.lib.adapter_toctou_stage_load
        cls.load.argtypes = [c.POINTER(Stage), c.c_uint32, c.c_char_p]
        cls.load.restype = c.c_bool
        cls.commit = cls.lib.adapter_toctou_stage_commit
        cls.commit.argtypes = [c.POINTER(Stage), c.POINTER(c.c_uint8)]
        cls.commit.restype = c.c_bool
        cls.prepare = cls.lib.rig_payload_prepare
        cls.prepare.argtypes = [c.POINTER(Stage), c.c_uint32]
        cls.prepare.restype = c.c_bool
        cls.current = cls.lib.rig_payload_current
        cls.current.restype = c.POINTER(Payload)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_verified_plan_window_roundtrip(self):
        stock = SparseImage(pack_image(b"\xff" * 8192))
        raw = b"\xff" * 4096 + bytes(range(256)) * 16
        candidate = SparseImage(pack_image(raw))
        plan = TOCTOUPlan.from_images(stock, candidate, windows=(
            PlannedWindow(2, 4000, 4400, "candidate"),))
        images = {"stock": stock, "candidate": candidate}
        commands = window_commands(plan, images, 0)
        self.assertFalse(any(cmd.startswith("RIG_ARM") for cmd in commands))
        _, address, length, digest = commands[1].split()
        state, buffer = Stage(), (c.c_uint8 * 4096)()
        self.assertTrue(self.begin(c.byref(state), int(address, 16), int(length),
                                   digest.encode(), buffer))
        self.assertEqual(commands[-2], "RIG_PREPARE 2")
        for command in commands[2:-3]:
            _, offset, hexbytes = command.split()
            self.assertTrue(self.load(c.byref(state), int(offset, 16), hexbytes.encode()))
        self.assertEqual(bytes(buffer[:400]), raw[4000:4400])
        actual = (c.c_uint8 * 32).from_buffer_copy(hashlib.sha256(bytes(buffer[:400])).digest())
        self.assertTrue(self.commit(c.byref(state), actual))
        self.assertTrue(state.verified)
        self.assertTrue(self.prepare(c.byref(state), 2))
        payload = self.current().contents
        self.assertEqual((payload.mark, payload.interval_m1, payload.read_index),
                         (0x03000000 | 4000, 3199, 2))
        self.assertEqual(bytes(payload.data[:400]), raw[4000:4400])
        self.lib.rig_payload_clear()
        self.assertFalse(self.current())
        self.assertFalse(self.load(c.byref(state), 400, b"00"))
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            window_commands(plan, {"stock": candidate, "candidate": candidate}, 0)

    def test_incomplete_invalid_and_corrupt_transfers_rejected(self):
        self.assertFalse(self.prepare(None, 2))
        self.assertFalse(self.current())
        state, buffer = Stage(), (c.c_uint8 * 4096)()
        expected = hashlib.sha256(b"abc").hexdigest().encode()
        digest = (c.c_uint8 * 32).from_buffer_copy(hashlib.sha256(b"abc").digest())
        self.assertTrue(self.begin(c.byref(state), 0x9DB560, 3, expected, buffer))
        self.assertFalse(self.prepare(c.byref(state), 2))
        self.assertFalse(self.current())
        self.assertFalse(self.load(c.byref(state), 1, b"61"))
        self.assertFalse(self.load(c.byref(state), 0, b"61ZZ"))
        self.assertEqual(state.received, 0)
        self.assertEqual(buffer[0], 0)
        self.assertTrue(self.load(c.byref(state), 0, b"61"))
        self.assertFalse(self.commit(c.byref(state), digest))
        self.assertTrue(self.load(c.byref(state), 1, b"6264"))
        actual = (c.c_uint8 * 32).from_buffer_copy(hashlib.sha256(bytes(buffer[:3])).digest())
        self.assertFalse(self.commit(c.byref(state), actual))
        self.assertFalse(state.active)
        self.assertFalse(state.verified)
        self.assertFalse(self.prepare(c.byref(state), 2))
        self.assertFalse(self.current())
        self.assertFalse(self.begin(c.byref(state), 0xFFFFFF, 2, expected, buffer))
        self.assertFalse(state.active)

if __name__ == "__main__":
    unittest.main()
