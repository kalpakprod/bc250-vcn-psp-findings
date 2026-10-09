import sys, hashlib, struct
from pathlib import Path
sys.path.insert(0, str(Path("scripts").resolve()))
from build_vcn_o3_candidate import decompress_inner, walk_inner_fv, sha256

PRE  = Path("evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin").read_bytes()   # booted this morning
POST = Path("evidence/programmer/reads/20260924-v003c/post-v003c-readback.bin").read_bytes() # v003c no-boot
DON  = Path("evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3").read_bytes()           # builder base

def report(tag, img):
    c = decompress_inner(img)
    inv, flen = walk_inner_fv(c["fv"])
    lz = img[c["cpos"]+24+c["guided_hdr"].__len__():][:5]
    hdr = bytes(lz)
    props = hdr[0]; lc=props%9; r=props//9; lp=r%5; pb=r//5
    try:
        dictsz = struct.unpack_from("<I", hdr, 1)[0]
    except Exception:
        dictsz = None
    print(f"{tag}: LZMA props lc={lc} lp={lp} pb={pb} dict={hex(dictsz) if dictsz else 'n/a'}")
    print(f"{tag}: raw-prefix sha16 {sha256(c['raw'])[:16]} raw_len={hex(len(c['raw']))}")
    print(f"{tag}: FV len={hex(flen)} files={len(inv)}")
    return c, inv, flen, sha256(c["raw"])

cpre, inv_pre, flen_pre, rpre = report("PRE ", PRE)
cpost, inv_post, flen_post, rpost = report("POST", POST)
cdon, inv_don, flen_don, rdon = report("DONOR", DON)

print()
print("raw-prefix PRE==DONOR:", rpre == rdon, " POST==DONOR:", rpost == rdon)
print("FV size  PRE==DONOR:", flen_pre == flen_don, " POST==DONOR:", flen_post == flen_don)

def keys(inv):
    return {(f["guid"], f["type"], f["size"], f["sha"]) for f in inv}
kpre, kpost, kdon = keys(inv_pre), keys(inv_post), keys(inv_don)
print("FV file sets:")
print("  PRE files in DONOR:", len(kpre & kdon), "/", len(kpre))
print("  PRE files NOT in DONOR:", len(kpre - kdon))
print("  DONOR files NOT in PRE:", len(kdon - kpre))
print("  POST files in DONOR:", len(kpost & kdon), "/", len(kpost))
print("  POST files NOT in DONOR:", len(kpost - kdon))
print("  PRE vs POST common files:", len(kpre & kpost))
print("  DONOR files NOT in PRE (first 12, guid,type,size):")
for g,t,s,_ in sorted(kdon - kpre)[:12]:
    print("     ", g, hex(t), hex(s))
