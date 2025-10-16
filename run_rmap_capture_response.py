#!/usr/bin/env python3
import sys, json, pgpy
from pathlib import Path
import rmap.compat_helpers as ch
import rmap.rmap_client as rc

# 我们保留刚才成功的加密逻辑（因为已经可用）
def _pgp_encrypt_armored_body_fixed(pubkey, plaintext_json):
    if isinstance(pubkey, str) and Path(pubkey).is_file():
        pubkey = Path(pubkey).read_text()
    key, _ = pgpy.PGPKey.from_blob(pubkey)
    msg = pgpy.PGPMessage.new(plaintext_json)
    enc = key.encrypt(msg)
    return str(enc)

ch._pgp_encrypt_armored_body = rc._pgp_encrypt_armored_body = _pgp_encrypt_armored_body_fixed

# 覆盖 decrypt_forgiving_json 以拦截响应并保存
orig_decrypt = ch.decrypt_forgiving_json

def dump_payload_wrapper(client_priv, payload):
    print("🪶 Intercepted server response — saving before decryption...")
    p = Path("/tmp/rmap_response_payload.asc")
    p.write_text(str(payload))
    print(f"✅ Saved raw payload to {p}")
    try:
        return orig_decrypt(client_priv, payload)
    except Exception as e:
        print("⚠️ Decrypt failed but payload saved:", e)
        raise

ch.decrypt_forgiving_json = dump_payload_wrapper
print("✅ Patched decrypt_forgiving_json to dump server payloads.")

# 配置
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, ".")
except Exception as e:
    print("⚠️ rmap-client raised:", e)
