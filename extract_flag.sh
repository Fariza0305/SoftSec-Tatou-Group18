#!/bin/bash

# 提取Base64水印数据
BASE64_DATA="eyJ2IjoxLCJhbGciOiJITUFDLVNIQTI1NiIsIm1hYyI6IjQwOWRmZWQzNzBjODU2ZWRiYWU5YmIxOWNmY2IwNDY4NWM4OTgyZDNlMDlhMDI3YmYwNjBjN2JkYTJjY2FlZmMiLCJzZWNyZXQiOiJabXhoWnpvMU1USTJZV0psWXpRelpUZzNPVGd5TmpZMVl6UXlOV1kzTnpSalpUa3pNekUzTnpJeE5EaGhmSFZ6WlhJNlRYSmZTVzF3YjNKMFlXNTBmSFJwYldVNk1qQXlOQT09In0="

echo "第一步: 解码外层Base64"
JSON_DATA=$(echo "$BASE64_DATA" | base64 -d 2>/dev/null)
echo "$JSON_DATA"
echo ""

# 提取secret字段
SECRET_B64=$(echo "$JSON_DATA" | grep -o '"secret":"[^"]*"' | cut -d'"' -f4)
echo "第二步: 提取secret字段"
echo "Secret (Base64): $SECRET_B64"
echo ""

# 解码secret
echo "第三步: 解码secret"
SECRET_CONTENT=$(echo "$SECRET_B64" | base64 -d 2>/dev/null)
echo "Secret内容: $SECRET_CONTENT"
echo ""

# 检查是否包含Flag
if echo "$SECRET_CONTENT" | grep -q "5126abec43e87982665c425f774ce9331772148a"; then
    echo "🎉 成功提取到Flag 1!"
    echo "Flag: 5126abec43e87982665c425f774ce9331772148a"
else
    echo "❌ 未找到Flag"
    echo "但成功提取到水印内容: $SECRET_CONTENT"
fi
