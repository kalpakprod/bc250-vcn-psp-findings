import struct
import unittest

from scripts.nvar_audit import parse_records, read_typed


class NvarAuditTests(unittest.TestCase):
    @staticmethod
    def record(name: bytes, body: bytes, *, size_extra: int = 0) -> bytes:
        # NVAR header: signature, size, link/sequence, two state bytes, name-index byte.
        payload = b"NVAR" + b"\x00\x00" + b"\xff\xff" + b"\x00\x82" + b"\x00" + name + b"\x00" + body
        size = len(payload) + size_extra
        return payload[:4] + struct.pack("<H", size) + payload[6:]

    def test_parse_name_body_and_little_endian_fields(self):
        body = bytearray(0x720)
        body[0x316] = 0x23
        body[0x704:0x706] = struct.pack("<H", 1400)
        body[0x70C:0x710] = struct.pack("<I", 130000)
        data = b"prefix" + self.record(b"AmdSetup", bytes(body))
        records, errors, first = parse_records(data, 0x1000)
        self.assertEqual(errors, [])
        self.assertEqual(first, 6)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["absolute_offset"], "0x1006")
        self.assertEqual(records[0]["body_length"], len(body))
        self.assertEqual(read_typed(bytes(body), 0x704, "u16"), 1400)
        self.assertEqual(read_typed(bytes(body), 0x70C, "u32"), 130000)

    def test_security_name_is_redacted(self):
        data = self.record(b"db", b"secret-material")
        records, errors, _ = parse_records(data)
        self.assertEqual(errors, [])
        self.assertEqual(records[0]["name"], "<redacted-security-variable>")
        self.assertTrue(records[0]["security_like"])
        self.assertNotIn("body_sha256", records[0])

    def test_truncated_record_is_reported(self):
        data = b"NVAR" + struct.pack("<H", 0x100) + b"\x00\x00\x00\x82\x00AmdSetup\x00"
        records, errors, _ = parse_records(data)
        self.assertEqual(records, [])
        self.assertTrue(any("truncated" in error for error in errors))

    def test_invalid_size_is_reported(self):
        data = b"NVAR" + struct.pack("<H", 5) + b"\x00\x00\x00\x82\x00"
        records, errors, _ = parse_records(data)
        self.assertEqual(records, [])
        self.assertTrue(any("invalid NVAR size" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
