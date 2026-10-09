
import sys, os, hashlib
sys.path.insert(0, r"C:\Users\OWNER\tmp_bc250\upstream\PSPTool")
from psptool.psptool import PSPTool
from psptool.pubkey_file import PubkeyFile
from psptool.header_file import HeaderFile

out_root = r"C:\Users\OWNER\tmp_bc250\recon\keys_raw"
roms = [
    ("robin3",  r"C:\Users\OWNER\tmp_bc250\recon\robin3_extracted\Robin3.00"),
    ("cezanne", r"C:\Users\OWNER\tmp_bc250\recon\cezanne_a3mstx_370e\A3MSTX_3.70E"),
    ("renoir",  r"C:\Users\OWNER\tmp_bc250\recon\renoir_a3mstx_360\A3MSTX_3.60"),
]
for name, rom in roms:
    pt = PSPTool.from_file(rom, verbose=False)
    for ri, r in enumerate(pt.blob.roms):
        for di, d in enumerate(r.directories):
            outdir = os.path.join(out_root, f"{name}_d{di}")
            os.makedirs(outdir, exist_ok=True)
            for ei, f in enumerate(d.files):
                if f is None: continue
                try:
                    b = f.get_bytes()
                except Exception as e:
                    print(f"{name} d{di} e{ei}: get_bytes err {e}")
                    continue
                t = f.get_readable_type().replace("~", "_").replace(" ", "_")
                fp = os.path.join(outdir, f"d{di:02d}_e{ei:02d}_{t}.bin")
                open(fp, "wb").write(b)
                line = f"{name} d{di} e{ei} {t:38s} sz={len(b):6d} md5={hashlib.md5(b).hexdigest()[:4].upper()}"
                extra = ""
                if isinstance(f, PubkeyFile):
                    try:
                        extra = (f" | ver={f.version} usage={f.get_readable_key_usage()} "
                                f"kid={f.key_id.magic} cert={f.certifying_id.magic} "
                                f"bits={f.modulus_bits} sf={f.security_features}")
                    except Exception as e:
                        extra = f" | pubkey parse err {e}"
                print(line + extra)
