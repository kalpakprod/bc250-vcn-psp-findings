#!/usr/bin/env python3
"""Assess SMU + board after the 0x2A wedge (NO 0x2A smoke): alive(), guarded open(), close."""
import sys, os, pathlib, traceback
lib=pathlib.Path(os.getcwd())/'bc250-smu-unlock'
for p in (lib, pathlib.Path(os.getcwd())/'daveconde-bc250-vcn-enable'):
    sys.path.insert(0,str(p))
from bc250_smu import Bc250Smu
print("cwd=",os.getcwd(),flush=True)
u=Bc250Smu()
try:
    print("alive=",u.alive(),flush=True)
    try:
        print("open_before=",u.secure_access_enabled(),flush=True)
    except Exception as e:
        print("open_err(str)=",(str(e)[:120]),flush=True)
finally:
    try: u.close()
    except Exception as e: print("close_err=",str(e)[:80],flush=True)
print("ASSESS_DONE",flush=True)
