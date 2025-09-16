import requests
import json
import sys

def extract_watermark():
    # 配置参数
    base_url = "http://localhost:5000"
    token = "eyJ1aWQiOjEsImxvZ2luIjoiTXJfSW1wb3J0YW50IiwiZW1haWwiOiJpbXBvcnRhbnRAMTYzLmNvbSJ9.aMg7Mw.zOLMTEm8TlVpe7iIkxhWzN3707A"
    document_id = "12"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("=== 开始提取水印 ===")
    
    # 首先查看可用的水印方法
    print("1. 获取可用的水印方法...")
    try:
        response = requests.get(f"{base_url}/api/get-watermarking-methods")
        if response.status_code == 200:
            methods_data = response.json()
            print("✅ 可用水印方法:")
            for method in methods_data.get('methods', []):
                print(f"   - {method['name']}: {method['description']}")
        else:
            print(f"❌ 获取方法失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 获取方法错误: {e}")
        return False
    
    # 查看现有的水印版本
    print("\n2. 查看现有水印版本...")
    try:
        response = requests.get(f"{base_url}/api/list-versions/{document_id}", headers=headers)
        if response.status_code == 200:
            versions = response.json()
            print("✅ 现有水印版本:")
            for version in versions.get('versions', []):
                print(f"   - ID: {version.get('id')}")
                print(f"     方法: {version.get('method')}")
                print(f"     目标用户: {version.get('intended_for')}")
                print(f"     链接: {version.get('link')}")
                print()
        else:
            print(f"❌ 获取版本失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取版本错误: {e}")
    
    # 尝试提取水印
    print("\n3. 尝试提取水印...")
    
    # 定义测试用例
    test_cases = [
        # toy-eof 方法测试
        {"method": "toy-eof", "key": "mr_important_secret_2024"},
        {"method": "toy-eof", "key": "secret_key_123"},
        {"method": "toy-eof", "key": "mr_important_secure_key"},
        
        # bash-bridge-eof 方法测试（不需要key）
        {"method": "bash-bridge-eof"},
        
        # 尝试不同的参数组合
        {"method": "toy-eof", "key": "mr_important_secret_2024", "position": "end"},
        {"method": "toy-eof", "key": "mr_important_secret_2024", "position": "eof"},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {json.dumps(params)}")
        
        try:
            response = requests.post(
                f"{base_url}/api/read-watermark/{document_id}",
                headers=headers,
                json=params,
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 提取成功!")
                print(f"响应: {json.dumps(result, indent=2)}")
                
                # 检查是否包含flag
                if 'secret' in result:
                    secret = result['secret']
                    if '5126abec43e87982665c425f774ce9331772148a' in secret:
                        print("🎉 成功提取到Flag 1!")
                        return True
                    else:
                        print("⚠️ 提取到水印，但不包含Flag")
                return True
                
            else:
                print(f"响应: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    
    print("\n❌ 所有提取尝试都失败了")
    return False

def manual_extract():
    print("\n=== 尝试手动提取水印 ===")
    print("手动检查水印文件内容...")
    
    try:
        # 检查文件大小
        import os
        watermarked_size = os.path.getsize("mr_important_watermarked.pdf")
        original_size = os.path.getsize("flag.pdf") if os.path.exists("flag.pdf") else 0
        
        print(f"水印文件大小: {watermarked_size} bytes")
        if original_size > 0:
            print(f"原始文件大小: {original_size} bytes")
            print(f"大小差异: {watermarked_size - original_size} bytes")
        
        # 读取文件末尾内容
        with open("mr_important_watermarked.pdf", "rb") as f:
            f.seek(-100, 2)  # 跳到文件末尾前100字节
            end_content = f.read(100)
        
        print("文件末尾内容 (ASCII):")
        ascii_content = "".join([chr(b) if 32 <= b <= 126 else "." for b in end_content])
        print(ascii_content)
        
        print("\n文件末尾内容 (Hex):")
        for i in range(0, len(end_content), 16):
            line = end_content[i:i+16]
            hex_str = " ".join([f"{b:02x}" for b in line])
            ascii_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in line])
            print(f"{i:04x}: {hex_str:<48} {ascii_str}")
            
    except Exception as e:
        print(f"手动提取错误: {e}")

if __name__ == "__main__":
    if not extract_watermark():
        manual_extract()
