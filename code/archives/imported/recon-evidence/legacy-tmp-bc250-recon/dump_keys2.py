
import sys, os, hashlib
sys.path.insert(0, r"C:\Users\OWNER\tmp_bc250\upstream\PSPTool")
from psptool.psptool import PSPTool
from psptool.pubkey_file import PubkeyFile
out_root = r"C:\Users\OWNER\tmp_bc250\recon\keys_raw"
roms = [
    ("robin1",  r"C:\Users\OWNER\tmp_bc250\recon\robin1_bios\Robin1.00"),
    ("robin5",  r"C:\Users\OWNER\tmp_bc250\recon\robin5_bios\Robin5.00"),
]
for name, rom in roms:
    pt = PSPTool.from_file(rom, verbose=False)
    for ri, r in enumerate(pt.blob.roms):
        for di, d in enumerate(r.directories):
            for ei, f in enumerate(d.files):
                if f is None: continue
                t = f.get_readable_type()
                if not any(k in t for k in ("KEY","UNLOCK","GASKET","POLICY")): continue
                try:
                    b = f.get_bytes()
                except Exception as e:
                    print(f"{name} d{di} e{ei}: err {e}"); continue
                outdir = os.path.join(out_root, f"{name}_d{di}")
                os.makedirs(outdir, exist_ok=True)
                safe = t.replace("~","_").replace(" ","_")
                open(os.path.join(outdir, f"d{di:02d}_e{ei:02d}_{safe}.bin"), "wb").write(b)
                extra = ""
                if isinstance(f, PubkeyFile):
                    try:
                        extra = f" | ver={f.version} usage={f.key_usage} kid={f.key_id.magic} cert={f.certifying_id.magic} bits={f.modulus_bits}"
                    except Exception as e:
                        extra = f" | perr {e}"
                print(f"{name} d{di} e{ei} {t:38s} sz={len(b):6d} md5={hashlib.md5(b).hexdigest()[:4].upper()}{extra}")
