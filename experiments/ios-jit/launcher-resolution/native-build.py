#!/usr/bin/env python3
"""Read-only verifier; build25 must never rebuild the accepted renderer stage."""
import hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=R/'.build/ios-jit/launcher-backbuffer-renderer'
expected={'stage/ios-arm64/libFNA3D.a':'605628b5f18d3571502bbe9f5f991f30e160dbf7641d924f867e2555c156081d','host/libFNA3D.0.dylib':'5c2ee8c743b2fbc768b712fdc3c05bcd68684e977a20b889b250e9d913328d82','receipt.json':'2460bf83d4579a524f569e5b7fe7e41e25f9910dc98550fb701cd9cb9c862935'}
for name,digest in expected.items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,name
print('PASS_ACCEPTED_BUILD24_RENDERER_READ_ONLY',P)
