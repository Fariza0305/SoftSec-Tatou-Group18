#!/usr/bin/env python3
import sys, json, pgpy
from pathlib import Path
import rmap.compat_helpers as ch
import rmap.rmap_client as rc

# 定义一个 wrapper 来捕获服务器返回的 payload
orig_decrypt = ch.decrypt_forgiving_json if hasattr(ch, "decrypt_forgiving_json") else None

def dump_payload_wrapper(client_priv, payload):
    print("🪶 Intercepted server response — saving before decryption...")
    p = Path("/tmp/rmap_response_payload.asc")
    p.write_text(str(payload))
    print(f"✅ Saved raw payload to {p}")
    try:
        if orig_decrypt:
            return orig_decrypt(client_priv, payload)
        else:
            print("⚠️ No original decrypt found, returning raw payload.")
            return payload
    except Exception as e:
        print("⚠️ Decrypt failed but payload saved:", e)
        raise

# 🔧 覆盖 rmap_client 模块自己的 decrypt_forgiving_json 引用
rc.decrypt_forgiving_json = dump_payload_wrapper
print("✅ Patched rmap_client.decrypt_forgiving_json (will save payloads).")

# 配置
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "Group_18"

# 运行
try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, ".")
except Exception as e:
    print("⚠️ rmap-client raised:", e)
