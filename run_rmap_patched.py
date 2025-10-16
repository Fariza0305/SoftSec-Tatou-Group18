#!/usr/bin/env python3
import sys, json, pgpy
from pathlib import Path
import rmap.compat_helpers as ch
import rmap.rmap_client as rc

# === PATCH 1: load_public_key ===
def load_public_key_fixed(path):
    data = Path(path).read_text()
    key, _ = pgpy.PGPKey.from_blob(data)
    return key
ch.load_public_key = load_public_key_fixed

# === PATCH 2: encrypt_json ===
def encrypt_json_fixed(data, key):
    if isinstance(key, str):
        if Path(key).is_file():
            keydata = Path(key).read_text()
        else:
            keydata = key
        key, _ = pgpy.PGPKey.from_blob(keydata)
    msg = pgpy.PGPMessage.new(json.dumps(data))
    enc_msg = key.encrypt(msg)
    return str(enc_msg)
ch.encrypt_json = encrypt_json_fixed

print("✅ Patched rmap.compat_helpers (load_public_key + encrypt_json)")

# === YOUR CONFIG ===
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

# === RUN ===
try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, ".")
except Exception as e:
    print("⚠️ rmap-client raised:", e)
