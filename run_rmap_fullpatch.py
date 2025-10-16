#!/usr/bin/env python3
import sys, json, base64, pgpy
from pathlib import Path
import rmap.compat_helpers as ch
import rmap.rmap_client as rc

# ========= ENCRYPT PATCH =========
def _pgp_encrypt_armored_body_fixed(pubkey, plaintext_json):
    print("DEBUG: [_pgp_encrypt_armored_body_fixed] called; key type:", type(pubkey))
    if isinstance(pubkey, str) and Path(pubkey).is_file():
        pubkey = Path(pubkey).read_text()
    key, _ = pgpy.PGPKey.from_blob(pubkey)
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

for mod in (ch, rc):
    mod._pgp_encrypt_armored_body = _pgp_encrypt_armored_body_fixed
    mod._pgp_encrypt_armored_and_base64 = _pgp_encrypt_armored_and_base64_fixed
    mod._pgp_encrypt_armored_body_and_base64 = _pgp_encrypt_armored_body_and_base64_fixed

print("✅ Patched all _pgp_encrypt_* methods in compat_helpers and rmap_client")

# ========= DECRYPT PATCH =========
orig_decrypt = ch.decrypt_forgiving_json if hasattr(ch, "decrypt_forgiving_json") else None

def dump_payload_wrapper(client_priv, payload):
    print("🪶 Intercepted server response — saving before decryption...")
    p = Path("/tmp/rmap_response_payload.asc")
    p.write_text(str(payload))
    print(f"✅ Saved raw payload to {p}")
    if orig_decrypt:
        try:
            return orig_decrypt(client_priv, payload)
        except Exception as e:
            print("⚠️ Decrypt failed but payload saved:", e)
            raise
    else:
        return payload

rc.decrypt_forgiving_json = dump_payload_wrapper
print("✅ Patched rmap_client.decrypt_forgiving_json to capture responses")

# ========= CONFIG =========
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

# ========= RUN =========
try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, ".")
except Exception as e:
    print("⚠️ rmap-client raised:", e)
