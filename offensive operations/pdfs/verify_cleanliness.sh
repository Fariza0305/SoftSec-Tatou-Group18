#!/usr/bin/env bash
set -euo pipefail

# 可自定义的关键词（大小写不敏感）
PATTERN='watermark|axel|tatou|fingerprint|do[[:space:]]+not[[:space:]]+distribute|gAAAAA|secret[_-]?digest|p0[_-]?salt|p0[_-]?mac'

# 依赖提示（尽量不中断）
need() {
  command -v "$1" >/dev/null 2>&1 || echo "⚠️  缺少 $1 ，建议安装：sudo apt-get install -y $2" >&2
}
need exiftool exiftool
need pdftotext poppler-utils
need strings binutils

# 目标集合：传参则用参数；否则 *.pdf
FILES=("$@")
if [ ${#FILES[@]} -eq 0 ]; then
  mapfile -t FILES < <(ls -1 *.pdf 2>/dev/null || true)
fi
if [ ${#FILES[@]} -eq 0 ]; then
  echo "❌ 没找到 PDF。用法：./verify_cleanliness.sh file1.pdf [file2.pdf ...]"
  exit 1
fi

TS=$(date +"%Y%m%d_%H%M%S")
OUT_TXT="clean_audit_report_${TS}.txt"
OUT_CSV="clean_audit_report_${TS}.csv"

echo "file,meta_hits,strings_hits,text_hits,status" > "$OUT_CSV"
{
  echo "=== PDF Cleanliness Audit ($TS) ==="
  echo "Patterns: $PATTERN"
  echo

  for f in "${FILES[@]}"; do
    [ -f "$f" ] || continue
    echo "=============================="
    echo "📄 $f"

    # 1) 元数据 / XMP 关键字段
    META_TMP=$(mktemp)
    if command -v exiftool >/dev/null 2>&1; then
      exiftool -s -Title -Subject -Keywords -Creator -Producer -Author "$f" > "$META_TMP" 2>/dev/null || true
      META_HITS=$(grep -E -i -n "$PATTERN" "$META_TMP" | wc -l || true)
    else
      META_HITS=0
    fi

    # 2) 二进制/对象流粗扫
    STR_HITS=$(strings -a "$f" 2>/dev/null | grep -E -i -n "$PATTERN" | wc -l || true)

    # 3) 文字层（提取后再搜）
    TXT_TMP=$(mktemp)
    if command -v pdftotext >/dev/null 2>&1; then
      pdftotext "$f" - 2>/dev/null > "$TXT_TMP" || true
      TXT_HITS=$(grep -E -i -n "$PATTERN" "$TXT_TMP" | wc -l || true)
    else
      TXT_HITS=0
    fi

    # 状态
    TOTAL=$(( META_HITS + STR_HITS + TXT_HITS ))
    if [ "$TOTAL" -eq 0 ]; then
      STATUS="PASS"
    else
      STATUS="FAIL"
    fi

    printf "  - meta_hits:    %s\n" "$META_HITS"
    printf "  - strings_hits: %s\n" "$STR_HITS"
    printf "  - text_hits:    %s\n" "$TXT_HITS"
    printf "  => STATUS: %s\n" "$STATUS"

    # 命中样本（各取前 5 行上下文）
    if [ "$META_HITS" -gt 0 ]; then
      echo "  [meta samples]"
      grep -E -i -n "$PATTERN" "$META_TMP" | head -5 | sed 's/^/    /'
    fi
    if [ "$STR_HITS" -gt 0 ]; then
      echo "  [strings samples]"
      strings -a "$f" | grep -E -i -n "$PATTERN" | head -5 | sed 's/^/    /'
    fi
    if [ "$TXT_HITS" -gt 0 ]; then
      echo "  [text samples]"
      grep -E -i -n "$PATTERN" "$TXT_TMP" | head -5 | sed 's/^/    /'
    fi

    echo "$f,$META_HITS,$STR_HITS,$TXT_HITS,$STATUS" >> "$OUT_CSV"

    rm -f "$META_TMP" "$TXT_TMP"
    echo
  done
} | tee "$OUT_TXT"

echo "✅ 完成。"
echo "文本报告: $OUT_TXT"
echo "CSV 汇总 : $OUT_CSV"
