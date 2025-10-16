#!/usr/bin/env python3
import sys
from pathlib import Path

# 调整下面两个路径为你实际的私钥 / 目标公钥 / 服务器 IP
CLIENT_PRIV = "/home/lab/tatou/server/keys/server/Group_18_priv_unprotected.asc"
SERVER_PUB = "/home/lab/tatou/server/keys/clients/Group_10.asc"
SERVER = "10.11.202.5"
IDENTITY = "GROUP_18"
OUTDIR = "."

# 运行前请激活虚拟环境： source ~/tatou/.venv/bin/activate
try:
    import rmap.rmap_client as rc
    import rmap.compat_helpers as ch
except Exception as e:
    print("Error importing rmap package:", e)
    sys.exit(2)

orig = ch.decrypt_forgiving_json

def wrapper(client_priv, payload):
    # 保存 payload 到 /tmp
    p = Path("/tmp/rmap_payload.asc")
    try:
        if isinstance(payload, bytes):
            p.write_bytes(payload)
        else:
            # 如果是 JSON 或 str，尽量写为文本
            p.write_text(str(payload))
    except Exception as e:
        print("Failed to write payload to /tmp/rmap_payload.asc:", e)
    # 然后调用原始函数 (会继续抛出原来的错误)
    return orig(client_priv, payload)

# monkeypatch
ch.decrypt_forgiving_json = wrapper

# 调用 rmap client run
try:
    rc.rmap_client_run(CLIENT_PRIV, SERVER_PUB, SERVER, IDENTITY, OUTDIR)
except Exception as e:
    print("rmap-client raised (this is expected if decrypt fails):", repr(e))
    print("Saved payload to /tmp/rmap_payload.asc if it was present.")
    sys.exit(0)
