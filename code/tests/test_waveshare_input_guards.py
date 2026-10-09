"""Native pure guards used by production; no SDK/device or network execution."""
from pathlib import Path
import subprocess
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "candidates/waveshare-adapter-safe-v001/src"

FIXTURE = r'''
#include "bridge/usb_identity_gate.h"
#include "network_config.h"
#include <cstdio>
#include <cstring>

#define CHECK(value) do { if (!(value)) { std::fprintf(stderr, "guard assertion line %d\n", __LINE__); return 1; } } while (0)
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (std::strcmp(argv[1], "hid") == 0) {
        // Actual Report ID2 descriptors: standard DS5 count47; Edge count63.
        // Both use8-bit payload elements, with one in-band reportID byte here.
        constexpr size_t min_wire_bytes=47;
        uint8_t ds5[48]={0x02},edge[64]={0x02};
        CHECK(usb_set_report_length_ok(0,ds5,sizeof(ds5),min_wire_bytes));
        CHECK(usb_set_report_length_ok(0,edge,sizeof(edge),min_wire_bytes));
        for(size_t size=0;size<sizeof(ds5);++size)
            CHECK(!usb_set_report_length_ok(0,ds5,size,min_wire_bytes));
        CHECK(!usb_set_report_length_ok(0,nullptr,0,min_wire_bytes));
        CHECK(!usb_set_report_length_ok(0,nullptr,sizeof(edge),min_wire_bytes));
        // Command/feature reports are not misclassified as in-band state0x02.
        CHECK(usb_set_report_length_ok(0xf6,ds5,1,min_wire_bytes));
        CHECK(usb_set_report_length_ok(0x80,edge,1,min_wire_bytes));
        ds5[0]=0x03;
        CHECK(usb_set_report_length_ok(0,ds5,1,min_wire_bytes));
        ds5[0]=0x02;
        CHECK(!usb_set_report_length_ok(0,ds5,sizeof(ds5),min_wire_bytes+1));
        // Exercise the actual bounded copy helper called by state_update.
        // A47-byte payload has no spare bytes that may be read as padding.
        uint8_t short_payload[47],edge_payload[63];
        std::memset(short_payload,0x5a,sizeof(short_payload));
        std::memset(edge_payload,0xa5,sizeof(edge_payload));
        struct { uint8_t bytes[63]; uint8_t canary; } update{};
        update.canary=0x7e;
        usb_copy_set_state_payload(update.bytes,sizeof(update.bytes),
                                   short_payload,sizeof(short_payload));
        for(size_t i=0;i<47;++i)CHECK(update.bytes[i]==0x5a);
        for(size_t i=47;i<63;++i)CHECK(update.bytes[i]==0);
        CHECK(update.canary==0x7e);
        usb_copy_set_state_payload(update.bytes,sizeof(update.bytes),
                                   edge_payload,sizeof(edge_payload));
        for(size_t i=0;i<63;++i)CHECK(update.bytes[i]==0xa5);
        CHECK(update.canary==0x7e);
        // Destination cap is honored even if a larger input is supplied.
        uint8_t capped[47]{};
        usb_copy_set_state_payload(capped,sizeof(capped),edge_payload,sizeof(edge_payload));
        for(size_t i=0;i<47;++i)CHECK(capped[i]==0xa5);
        return 0;
    }
    if (std::strcmp(argv[1], "http") != 0) return 2;
    // Synthetic public fixture token, never owner credentials.
    const char *token="0123456789abcdef0123456789abcdef";
    const char *valid="GET /api/status HTTP/1.1\r\nHost: local\r\nauthorization: bEaReR 0123456789abcdef0123456789abcdef\r\n\r\n";
    CHECK(adapter_http_token_ok(valid,std::strlen(valid),token));
    const char *canonical="GET /api/status HTTP/1.1\r\nAuthorization: Bearer 0123456789abcdef0123456789abcdef\r\n\r\n";
    CHECK(adapter_http_token_ok(canonical,std::strlen(canonical),token));
    const char *bad="GET /api/status HTTP/1.1\r\nauthorization: Bearer 0123456789abcdeF0123456789abcdef\r\n\r\n";
    CHECK(!adapter_http_token_ok(bad,std::strlen(bad),token));
    const char *body="GET /api/status HTTP/1.1\r\nHost: local\r\n\r\nAuthorization: Bearer 0123456789abcdef0123456789abcdef\r\n\r\n";
    CHECK(!adapter_http_token_ok(body,std::strlen(body),token));
    CHECK(!adapter_http_token_ok(canonical,std::strlen(canonical)-2,token));
    const char *malformed="GET / HTTP/1.1\r\nauthorization: Bearer0123456789abcdef0123456789abcdef\r\n\r\n";
    CHECK(!adapter_http_token_ok(malformed,std::strlen(malformed),token));
    const char *duplicate="GET / HTTP/1.1\r\nauthorization: Bearer 0123456789abcdef0123456789abcdef\r\nAuthorization: Bearer 0123456789abcdef0123456789abcdef\r\n\r\n";
    CHECK(!adapter_http_token_ok(duplicate,std::strlen(duplicate),token));
    CHECK(!adapter_http_token_ok(canonical,std::strlen(canonical),""));
    return 0;
}
'''


@pytest.fixture(scope="module")
def native_guard():
    cache = Path.home() / ".cache/bc250-audit-fixes"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="usb-http-native-", dir=cache) as tmp:
        source = Path(tmp) / "guard.cpp"
        binary = Path(tmp) / "guard"
        source.write_text(FIXTURE)
        compiled = subprocess.run(
            ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(SRC), str(source), "-o", str(binary)],
            capture_output=True, text=True, timeout=20,
        )
        assert compiled.returncode == 0, compiled.stderr
        yield binary


def test_hid_full_state_and_all_short_or_zero_reports(native_guard):
    result = subprocess.run([str(native_guard), "hid"], capture_output=True,
                            text=True, timeout=5)
    assert result.returncode == 0, result.stderr


def test_http_case_insensitive_names_exact_token_and_no_body_auth(native_guard):
    result = subprocess.run([str(native_guard), "http"], capture_output=True,
                            text=True, timeout=5)
    assert result.returncode == 0, result.stderr
