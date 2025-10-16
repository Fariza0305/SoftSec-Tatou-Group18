#!/usr/bin/env python3
import sys, json, pgpy
import rmap.compat_helpers as ch
from pathlib import Path

def encrypt_json_fixed(data, key):
    """Force encrypt JSON data with pgpy.PGPKey"""
    if isinstance(key, str):
        # 如果传入的是路径字符串，就先读取
        if Path(key).is_file():
            keydata = Path(key).read_text()
        else:
            keydata = key
        key, _ = pgpy.PGPKey.from_blob(keydata)
    if not isinstance(key, pgpy.PGPKey):
        raise TypeError(f"Expected PGPKey, got {type(key)}")

    msg = pgpy.PGPMessage.new(json.dumps(data))
    enc_msg = key.encrypt(msg)
    return str(enc_msg)

# 替换原函数
ch.encrypt_json = encrypt_json_fixed
print("✅ Patched rmap.compat_helpers.encrypt_json to use pgpy.PGPKey.encrypt() properly.")
