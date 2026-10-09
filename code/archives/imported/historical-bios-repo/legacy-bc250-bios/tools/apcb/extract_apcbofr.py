# Extract AmdApcbObrDxe / AmdApcbObrSmm PE32 images from decompressed FVMAIN.
import struct

DEC = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\FV@ae0000_0b_9E21FD93_78.LZMA.dec"
d = open(DEC, "rb").read()

TARGETS = {
    0xa5550: "AmdApcbObrDxe",
    0x309198: "AmdApcbObrSmm",
}
OUT = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"

for fstart, name in TARGETS.items():
    ftype = d[fstart + 0x12]
    size = d[fstart + 0x14] | (d[fstart + 0x15] << 8) | (d[fstart + 0x16] << 16)
    o = fstart + 0x18
    end = fstart + size
    while o + 4 <= end:
        ssz = d[o] | (d[o + 1] << 8) | (d[o + 2] << 16)
        stp = d[o + 3]
        if ssz < 4 or o + ssz > end:
            break
        print("%s: section type=%02x @%#x size=%#x" % (name, stp, o, ssz))
        if stp == 0x10:
            fn = OUT + "\\" + name + ".PE32"
            open(fn, "wb").write(d[o + 4:o + ssz])
            print("  saved %s (%d bytes)" % (fn, ssz - 4))
        if stp == 0x15:
            print("  UI:", d[o + 4:o + ssz].decode("utf-16-le", "ignore").rstrip("\x00"))
        if stp == 0x13:  # DEPEX
            dep = d[o + 4:o + ssz]
            print("  DEPEX:", dep.hex(" "))
        if stp == 0x12:  # version
            pass
        o += ssz
        o = (o + 3) & ~3
