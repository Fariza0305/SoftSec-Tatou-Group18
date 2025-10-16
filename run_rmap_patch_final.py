#!/usr/bin/env python3
import sys, json, pgpy
from pathlib import Path
import rmap.compat_helpers as ch
import rmap.rmap_client as rc
import types

def load_public_key_fixed(path):
    data = Path(path).read_text()
    key, _ = pgpy.PGPKey.from_blob(data)
    return key

def encrypt_json_fixed(data, key):
    print("DEBUG: [FINAL PATCH] encrypt_json_fixed called; key type:", type(key))
    if isinstance(key, str):
        if Path(key).is_file():
            keydata = Path(key).read_text()
        else:
            keydata = key
        key, _ = pgpy.PGPKey.from_blob(keydata)
        print("DEBUG: [FINAL PATCH] converted to:", type(key))
    msg = pgpy.PGPMessage.new(json.dumps(data))
    enc_msg = key.encrypt(msg)
    return str(enc_msg)

# Apply to compat_helpers
ch.load_public_key = load_public_key_fixed
ch.encrypt_json = encrypt_json_fixed

# Apply to rmap_client globals (overwrite internal references)
rc.encrypt_json = encrypt_json_fixed
rc.load_public_key = load_public_key_fixed
rc.__dict__['encrypt_json'] = encrypt_json_fixed

# Also check inside try_send_payload if it imported encrypt_json locally
import inspect
import re

src = inspect.getsource(rc.try_send_payload)
if "encrypt_json(" in src:
    print("✅ Found inline encrypt_json call in try_send_payload — forcing monkeypatch")
    rc.try_send_payload.__globals__['encrypt_json'] = encrypt_json_fixed
else:
    print("⚠️ Could not find encrypt_json in try_send_payload source — may be using another name")

print("✅ All encrypt_json references patched.")

# === CONFIG ===
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

# === EXECUTE ===
try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, ".")
except Exception as e:
    print("⚠️ rmap-client raised:", e)
    from pathlib import Path
    p = Path("/tmp/rmap_payload.asc")
    if p.exists():
        print(f"✅ Payload captured at {p} ({p.stat().st_size} bytes)")
    else:
        print("❌ No payload saved.")
