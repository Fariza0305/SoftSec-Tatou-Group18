#!/bin/bash

echo "=== Tatou API Fuzzing 工具 ==="
echo "目标: http://localhost:5000"
echo "开始时间: $(date)"
echo "================================"

# 检查API是否运行
echo ""
echo "1. 检查API是否运行..."
if curl -s http://localhost:5000 > /dev/null; then
    echo "✅ API正在运行"
else
    echo "❌ API未运行，请先启动API"
    exit 1
fi

# 创建结果目录
mkdir -p fuzzing_results
cd fuzzing_results

# 组合自定义种子与系统字典
SEED_WORDLIST="../fuzzing/seed_endpoints.txt"
SYSTEM_WORDLIST="/usr/share/dirb/wordlists/common.txt"
COMBINED_WORDLIST="wordlist_combined.txt"

if [ -f "$SEED_WORDLIST" ] || [ -f "$SYSTEM_WORDLIST" ]; then
    echo "合并字典: $SEED_WORDLIST + $SYSTEM_WORDLIST -> $COMBINED_WORDLIST"
    # 将自定义词优先，随后系统词，去重
    cat "$SEED_WORDLIST" "$SYSTEM_WORDLIST" 2>/dev/null | awk 'NF{ if(!seen[$0]++){ print } }' > "$COMBINED_WORDLIST"
else
    echo "⚠️ 未找到系统字典或种子字典，将仅使用默认内置路径"
    printf "api\nhealthz\n" > "$COMBINED_WORDLIST"
fi

echo ""
echo "2. 开始目录fuzzing (dirb)..."
echo "使用wordlist: $COMBINED_WORDLIST"
echo "扫描过程会显示在下方:"
echo "----------------------------------------"

# 运行dirb并显示详细输出
dirb http://localhost:5000 "$COMBINED_WORDLIST" \
    -o tatou_dirb_results.txt \
    -v \
    -S

echo ""
echo "3. 分析dirb结果..."
echo "----------------------------------------"

echo "📊 Dirb 扫描结果:"
if [ -f tatou_dirb_results.txt ]; then
    echo "发现的响应(含鉴权/方法限制):"
    grep -E "CODE:(200|401|403|405|500)" tatou_dirb_results.txt | head -20
    echo ""
    echo "计数统计:"
    echo "  200: $(grep -c "CODE:200" tatou_dirb_results.txt 2>/dev/null || echo 0)"
    echo "  401: $(grep -c "CODE:401" tatou_dirb_results.txt 2>/dev/null || echo 0)"
    echo "  403: $(grep -c "CODE:403" tatou_dirb_results.txt 2>/dev/null || echo 0)"
    echo "  405: $(grep -c "CODE:405" tatou_dirb_results.txt 2>/dev/null || echo 0)"
    echo "  500: $(grep -c "CODE:500" tatou_dirb_results.txt 2>/dev/null || echo 0)"
    echo "  其他: $(grep -E "CODE:[0-9]+" tatou_dirb_results.txt | grep -v -E "CODE:(200|401|403|405|500)" | wc -l | tr -d ' ')"
    echo ""
    echo "总返回次数(含所有状态): $(grep -c "CODE:" tatou_dirb_results.txt 2>/dev/null || echo 0)"
    echo ""
    echo "目标化探测:"
    HZ=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/healthz)
    echo "  GET /healthz -> $HZ"
    GV=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/get-version/test_token_example)
    echo "  GET /api/get-version/<token> (fake) -> $GV"
else
    echo "❌ 未找到dirb结果文件"
fi

echo ""
echo "扫描完成！查看 fuzzing_results/ 目录获取详细结果"
echo "结束时间: $(date)"
