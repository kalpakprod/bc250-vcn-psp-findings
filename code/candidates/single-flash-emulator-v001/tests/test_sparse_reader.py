"""Real C reader against containers produced by the existing Python packer."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from image_pack import pack_image


class SparseReaderTests(unittest.TestCase):
    def test_actual_c_reader_and_failed_reopen(self):
        cache = Path.home() / ".cache/waveshare-psp-reader-20261007"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            work = Path(directory)
            image = b"\xff" * 4096 + b"A" * 4096
            (work / "image.spm").write_bytes(pack_image(image))
            source = work / "test.c"
            source.write_text(r'''
#include "sparse_reader.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    assert(argc == 2);
    FILE *f = fopen(argv[1], "rb"); assert(f);
    assert(fseek(f, 0, SEEK_END) == 0);
    long n = ftell(f); assert(n > 0); rewind(f);
    unsigned char *b = malloc((size_t)n); assert(b);
    assert(fread(b, 1, (size_t)n, f) == (size_t)n); fclose(f);
    bc250_sparse_reader_t r;
    assert(bc250_sparse_open(&r, b, (size_t)n));
    unsigned char out[4];
    assert(bc250_sparse_read(&r, 4094, out, 4));
    assert(out[0] == 255 && out[1] == 255 && out[2] == 'A' && out[3] == 'A');
    assert(bc250_sparse_read(&r, 8191, out, 1) && out[0] == 'A');
    assert(!bc250_sparse_read(&r, 8192, out, 1));
    assert(!bc250_sparse_read(&r, 0xffffffffu, out, 4));
    assert(bc250_sparse_read(&r, 8192, NULL, 0));
    /* A truncated replacement must invalidate the old view. */
    assert(!bc250_sparse_open(&r, b, (size_t)n - 1));
    assert(!bc250_sparse_read(&r, 0, out, 1));
    /* Duplicate payload index in two pages is structurally invalid. */
    b[64] = b[65] = b[66] = b[67] = 0;
    assert(!bc250_sparse_open(&r, b, (size_t)n));
    free(b); return 0;
}
''')
            subprocess.run([
                "cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                "-I", str(ROOT / "src"), str(source),
                str(ROOT / "src/sparse_reader.c"), "-o", str(work / "reader"),
            ], check=True, capture_output=True)
            subprocess.run([str(work / "reader"), str(work / "image.spm")],
                           check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
