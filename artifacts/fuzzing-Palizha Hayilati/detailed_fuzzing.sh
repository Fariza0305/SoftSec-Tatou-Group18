#!/bin/bash

echo "=== Tatou API 详细扫描工具 ==="
echo "目标: http://localhost:5000/api/api"
echo "开始时间: $(date)"
echo "================================"

# 创建结果目录
mkdir -p fuzzing_results
cd fuzzing_results

# 组合自定义种子与系统字典
SEED_WORDLIST="../fuzzing/seed_endpoints.txt"
SYSTEM_WORDLIST="/usr/share/dirb/wordlists/common.txt"
COMBINED_WORDLIST="wordlist_combined.txt"

if [ -f "$SEED_WORDLIST" ] || [ -f "$SYSTEM_WORDLIST" ]; then
    echo "合并字典: $SEED_WORDLIST + $SYSTEM_WORDLIST -> $COMBINED_WORDLIST"
    # 自定义词优先，随后系统词，去重
    cat "$SEED_WORDLIST" "$SYSTEM_WORDLIST" 2>/dev/null | awk 'NF{ if(!seen[$0]++){ print } }' > "$COMBINED_WORDLIST"
else
    echo "⚠️ 未找到系统字典或种子字典，将仅使用默认内置路径"
    printf "api\nhealthz\n" > "$COMBINED_WORDLIST"
fi

echo ""
echo "1. 检查API状态..."
if curl -s -I http://localhost:5000 | head -1; then
    echo "✅ API正在运行"
else
    echo "❌ API未运行，请先启动API"
    exit 1
fi

echo ""
echo "2. 开始目录扫描..."
echo "使用dirb扫描常见路径..."
echo "----------------------------------------"

# 运行dirb并保存结果
dirb http://localhost:5000/api "$COMBINED_WORDLIST" \
    -o tatou_scan_results.txt \
    -v \
    -S \
    -r

echo ""
echo "3. 分析扫描结果..."
echo "----------------------------------------"

if [ -f tatou_scan_results.txt ]; then
    echo "📊 扫描统计:"
    echo "总返回次数(含所有状态): $(grep -c "CODE:" tatou_scan_results.txt 2>/dev/null || echo 0)"
    
    echo ""
    echo "🔍 发现的有效端点:"
    echo "状态码 200 (成功):"
    grep "CODE:200" tatou_scan_results.txt | head -10
    
    echo ""
    echo "状态码 401 (未鉴权):"
    grep "CODE:401" tatou_scan_results.txt | head -10

    echo ""
    echo "状态码 403 (需要认证):"
    grep "CODE:403" tatou_scan_results.txt | head -10
    
    echo ""
    echo "状态码 405 (方法不允许):"
    grep "CODE:405" tatou_scan_results.txt | head -10

    echo ""
    echo "状态码 500 (服务器错误):"
    grep "CODE:500" tatou_scan_results.txt | head -10
    
    echo ""
    echo "其他状态码:"
    grep -E "CODE:[0-9]+" tatou_scan_results.txt | grep -v -E "(CODE:200|CODE:401|CODE:403|CODE:405|CODE:500)" | head -10
    
    echo ""
    echo "📁 完整结果已保存到: tatou_scan_results.txt"
    
    # 生成简单报告
    cat > scan_summary.txt << EOL
Tatou API 扫描摘要
==================
扫描时间: $(date)
目标: http://localhost:5000/api

有效端点 (200):
$(grep "CODE:200" tatou_scan_results.txt)

需要认证或未鉴权 (401/403):
$(grep -E "CODE:(401|403)" tatou_scan_results.txt)

方法受限 (405):
$(grep "CODE:405" tatou_scan_results.txt)

需要认证的端点 (403):
$(grep "CODE:403" tatou_scan_results.txt)

服务器错误 (500):
$(grep "CODE:500" tatou_scan_results.txt)

总返回次数(含所有状态): $(grep -c "CODE:" tatou_scan_results.txt 2>/dev/null || echo 0)
健康检查: /healthz -> $(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/healthz)
下载接口探测: /api/get-version/<token> (fake) -> $(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/get-version/test_token_example)
EOL
    
    echo "📋 摘要报告已保存到: scan_summary.txt"
    
else
    echo "❌ 未找到扫描结果文件"
fi

echo ""
echo "扫描完成！"
echo "结束时间: $(date)"
