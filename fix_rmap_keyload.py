#!/usr/bin/env python3
import sys, pgpy
from pathlib import Path
import rmap.compat_helpers as ch

def load_public_key_fixed(path):
    """Force-load a proper pgpy.PGPKey object from .asc public key"""
    data = Path(path).read_text()
    key, _ = pgpy.PGPKey.from_blob(data)
    if not key.is_public:
        raise RuntimeError("Loaded key is not a public key!")
    return key

# Patch the original function
ch.load_public_key = load_public_key_fixed
print("✅ Patched rmap.compat_helpers.load_public_key to fixed loader")

# Test on one sample key
try:
    test_key = load_public_key_fixed("/home/lab/tatou/server/keys/clients/Group_10.asc")
    print("Loaded key:", type(test_key))
    print("Fingerprint:", test_key.fingerprint)
except Exception as e:
    print("❌ Error while loading key:", e)
    sys.exit(1)
