#!/usr/bin/env python3
import sys, json, base64, pgpy
from pathlib import Path
import rmap.compat_helpers as ch
import rmap.rmap_client as rc

# --- define our patch encryptors ---
def _pgp_encrypt_armored_body_fixed(pubkey, plaintext_json):
    print("DEBUG: [_pgp_encrypt_armored_body_fixed] called; key type:", type(pubkey))
    if isinstance(pubkey, str):
        if Path(pubkey).is_file():
            pubkey = Path(pubkey).read_text()
        key, _ = pgpy.PGPKey.from_blob(pubkey)
    elif isinstance(pubkey, pgpy.PGPKey):
        key = pubkey
    else:
        key, _ = pgpy.PGPKey.from_blob(str(pubkey))
    msg = pgpy.PGPMessage.new(plaintext_json)
    enc = key.encrypt(msg)
    return str(enc)

def _pgp_encrypt_armored_and_base64_fixed(pubkey, plaintext_json):
    armored = _pgp_encrypt_armored_body_fixed(pubkey, plaintext_json)
    return base64.b64encode(armored.encode()).decode()

def _pgp_encrypt_armored_body_and_base64_fixed(pubkey, plaintext_json):
    enc = _pgp_encrypt_armored_body_fixed(pubkey, plaintext_json)
    body = enc.split("-----BEGIN PGP MESSAGE-----")[-1]
    body = body.replace("-----END PGP MESSAGE-----", "").strip()
    return base64.b64encode(body.encode()).decode()

# patch both compat_helpers and rmap_client module globals
for mod in (ch, rc):
    mod._pgp_encrypt_armored_body = _pgp_encrypt_armored_body_fixed
    mod._pgp_encrypt_armored_and_base64 = _pgp_encrypt_armored_and_base64_fixed
    mod._pgp_encrypt_armored_body_and_base64 = _pgp_encrypt_armored_body_and_base64_fixed

print("✅ Patched all three _pgp_encrypt_* functions in compat_helpers and rmap_client")

# === CONFIG ===
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

# === RUN ===
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
