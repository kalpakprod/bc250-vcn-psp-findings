import lzma, struct
P = "evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin"   # booted this morning
C = "evidence/programmer/reads/20260924-v003c/post-v003c-readback.bin" # v003c, does not boot
pre = open(P,"rb").read(); post = open(C,"rb").read()

# 1. exact diff regions pre(post) vs post(candidate), gap 0x2000
d=[i for i in range(len(pre)) if pre[i]!=post[i]]
regs=[]; s=p=d[0]
for i in d[1:]:
    if i-p>0x2000: regs.append((s,p)); s=i
    p=i
regs.append((s,p))
print("1. pre-vs-post regions:", ", ".join(f"{hex(a)}-{hex(b)} len={hex(b-a+1)}" for a,b in regs))
for a,b in regs:
    outside = not (0xAE0088 <= a and b <= 0xC2654B)
    print("   ", hex(a), "-", hex(b), "OUTSIDE intended window" if outside else "inside intended capsule window")

# 2. what is at the APCB token block
for name,img in (("pre ",pre),("post",post)):
    seg=img[0xAB1008:0xAB1B70]
    print("2. %s APCB 0xAB1008..0xAB1B6F head: %s  nonzero=%d/%d" %
          (name, seg[:32].hex(), sum(1 for c in seg if c not in (0,0xff)), len(seg)))

# 3. the region right AFTER the intended capsule end (0xC2654B..0xC30A6B) -- was in the pre-vs-post diff
for name,img in (("pre ",pre),("post",post)):
    seg=img[0xC26540:0xC26600]
    print("3. %s 0xC26540..0xC265FF head: %s" % (name, seg[:48].hex()))

# 4. LZMA stream parameters of the inner-FV capsule in both images (FORMAT_ALONE header)
def lz_info(img, off=0xAE0088):
    hdr=img[off:off+13]
    props=hdr[0]; lc=props%9; r=props//9; lp=r%5; pb=r//5
    dictsz=struct.unpack_from("<I",hdr,5)[0]
    usz=struct.unpack_from("<Q",hdr,9+0)[0] if len(hdr)>=17 else None; hdr=img[off:off+17]
    return lc,lp,pb,dictsz,usz
print("4. LZMA (lc,lp,pb,dict,declared_outsize):")
print("   pre :", lz_info(pre))
print("   post:", lz_info(post))
try:
    dec=lzma.decompress(pre[0xAE0088:0xC28000])
    print("   pre  decompressed size:", hex(len(dec)))
except Exception as e:
    print("   pre  lzma fail:", e)
try:
    dec=lzma.decompress(post[0xAE0088:0xC30000])
    print("   post decompressed size:", hex(len(dec)))
except Exception as e:
    print("   post lzma fail:", e)

# 5. does the ORIGINAL size 0x432000 (le: 00 20 43 00) appear as a constant anywhere?
for pat,name in ((b"\x00\x20\x43\x00","0x432000(original FV size)"),
                 (b"\x00\x60\x43\x00","0x436000(grown FV size)")):
    hits=[]; i=0
    while len(hits)<12:
        j=pre.find(pat,i)
        if j<0: break
        hits.append(j); i=j+1
    print("5. pre  contains %-24s at: %s" % (name, [hex(h) for h in hits] or "none"))

# 6. morning(booted) vs FD donor: what the reset-to-donor actually erased
donor = open("","rb").read()
d=[i for i in range(len(pre)) if pre[i]!=donor[i]]
regs=[]; s=p=d[0]
for i in d[1:]:
    if i-p>0x2000: regs.append((s,p)); s=i
    p=i
regs.append((s,p))
print("6. morning-vs-donor regions:", ", ".join(f"{hex(a)}-{hex(b)} len={hex(b-a+1)}" for a,b in regs))
