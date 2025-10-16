#!/usr/bin/env python3
import sys, json, pgpy
from pathlib import Path

# import modules
import rmap.compat_helpers as ch
import rmap.rmap_client as rc

def load_public_key_fixed(path):
    """Force-load a proper pgpy.PGPKey object from .asc public key"""
    data = Path(path).read_text()
    key, _ = pgpy.PGPKey.from_blob(data)
    return key

def encrypt_json_fixed(data, key):
    """Force encrypt JSON data with pgpy.PGPKey"""
    # Debug: print type of incoming 'key'
    print("DEBUG: encrypt_json_fixed called; incoming key type:", type(key))
    if isinstance(key, str):
        if Path(key).is_file():
            keydata = Path(key).read_text()
        else:
            keydata = key
        key, _ = pgpy.PGPKey.from_blob(keydata)
        print("DEBUG: loaded pgpy key from string/path; key type now:", type(key))
    if not isinstance(key, pgpy.PGPKey):
        raise TypeError(f"Expected pgpy.PGPKey, got {type(key)}")
    msg = pgpy.PGPMessage.new(json.dumps(data))
    enc_msg = key.encrypt(msg)
    return str(enc_msg)

# Patch both compat_helpers and rmap_client module-level references
ch.load_public_key = load_public_key_fixed
ch.encrypt_json = encrypt_json_fixed

# Ensure rmap_client local references are also overwritten (in-case they were imported)
setattr(rc, "load_public_key", load_public_key_fixed)
setattr(rc, "encrypt_json", encrypt_json_fixed)

print("✅ Patched load_public_key & encrypt_json in both rmap.compat_helpers and rmap.rmap_client")

# config (edit if necessary)
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

# Run the client logic in-process
try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, ".")
except Exception as e:
    print("⚠️ rmap-client raised (expected on decrypt failure or other):", repr(e))
    # If payload got saved by previous wrapper, report location
    from pathlib import Path
    p = Path("/tmp/rmap_payload.asc")
    if p.exists():
        print("Saved payload at /tmp/rmap_payload.asc (size bytes):", p.stat().st_size)
    else:
        print("/tmp/rmap_payload.asc not present")
