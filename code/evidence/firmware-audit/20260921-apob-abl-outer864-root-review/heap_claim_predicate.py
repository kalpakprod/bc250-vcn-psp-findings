#!/usr/bin/env python3
import json, pathlib, sys
p=pathlib.Path(sys.argv[1]).resolve()
s=p.read_text()
if 'HEAP claim status: WITHDRAWN' in s:
    status='withdrawn'
elif 'payload copy via 0x6B78' in s or '0x6B78` as copying a payload' in s or '0x6B78` copies payload' in s:
    status='asserted'
else:
    status='unknown'
print(json.dumps({'path': str(p), 'heap_claim_status': status}, sort_keys=True))
expected=sys.argv[2]
sys.exit(0 if status==expected else 1)
