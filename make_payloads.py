#!/usr/bin/env python3
"""
make_payloads.py
生成两种 PGP-ASCII-ARMOR payload：
  - /tmp/payload_armored_json.asc         : armor 中直接包含 JSON
  - /tmp/payload_armored_b64json.asc     : armor 中包含 base64(JSON)

用法：在虚拟环境里运行： python make_payloads.py
"""
import json, base64, sys
from pathlib import Path
try:
    from pgpy import PGPKey, PGPMessage
except Exception as e:
    print("ERROR: cannot import pgpy:", e, file=sys.stderr)
    sys.exit(2)

# 请按需修改这个公钥路径（目标组的公钥）
PUBKEY_PATH = "/home/lab/tatou/server/keys/clients/Group_13.asc"

# 简单 payload（你可以修改）
payload_obj = {"identity": "Group_18", "nonceClient": 1234567890}
payload_json = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True)

# load public key robustly (PGPy may return tuple or PGPKey)
keydata = Path(PUBKEY_PATH)
if not keydata.exists():
    print(f"ERROR: public key not found: {PUBKEY_PATH}", file=sys.stderr)
    sys.exit(3)

res = PGPKey.from_file(str(keydata))
pubkey = res[0] if isinstance(res, tuple) else res

# Method A: ASCII-armored PGP containing raw JSON
msgA = PGPMessage.new(payload_json)
encA = pubkey.encrypt(msgA)
armoredA = str(encA)

# Method B: ASCII-armored PGP containing base64(JSON)
b64 = base64.b64encode(payload_json.encode()).decode()
msgB = PGPMessage.new(b64)
encB = pubkey.encrypt(msgB)
armoredB = str(encB)

# write outputs
outA = Path("/tmp/payload_armored_json.asc")
outB = Path("/tmp/payload_armored_b64json.asc")
outA.write_text(armoredA)
outB.write_text(armoredB)

print("Wrote:")
print("  ", outA)
print("  ", outB)
print()
print("Preview (first 120 chars of armoredA):")
print(armoredA[:120])
