import pgpy
import base64
import json

# 加载私钥
private_key, _ = pgpy.PGPKey.from_file('/home/lab/tatou/offensive operations/Group_24_priv.asc')

# 解锁私钥
with private_key.unlock(passphrase='Group@24rkj') as unlocked_key:
    # 准备 payload
    payload = json.dumps({'document_id': 1})
    message = pgpy.PGPMessage.new(payload)
    signature = unlocked_key.sign(message)
    base64_sig = base64.b64encode(str(signature).encode('utf-8')).decode('utf-8')

# 保存签名到文件
with open('signature.txt', 'w') as f:
    f.write(base64_sig)

print("Signature generated and saved to signature.txt")
