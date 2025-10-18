#!/usr/bin/env bash
set -euo pipefail

targets=(
10.11.202.5
10.11.202.6
10.11.202.7
10.11.202.9
10.11.202.10
10.11.202.11
10.11.202.13
10.11.202.14
10.11.202.15
10.11.202.16
)

mkdir -p recon_out
echo "🧭 HTTP 基础摸底（仅公开信息）"

for ip in "${targets[@]}"; do
  outdir="recon_out/$ip"
  mkdir -p "$outdir"
  echo "=================================="
  echo "📡 $ip:5000"

  # 1) 响应头（看服务器类型/框架/缓存/跨域）
  echo "—— headers ——" | tee "$outdir/headers.txt"
  curl -sS -m 5 -I "http://$ip:5000/" | tee -a "$outdir/headers.txt" || true

  # 2) 常见公开文件（不含攻击）
  for p in / /index.html /login.html /signup.html /robots.txt /sitemap.xml /humans.txt /.well-known/security.txt; do
    curl -sS -m 5 "http://$ip:5000$p" -o "$outdir$(echo $p | sed 's#/#_#g; s#^_$#/index.html#')" || true
  done

  # 3) 首页提取 href/src（只取一层）
  echo "—— href/src 提取 ——" | tee "$outdir/links.txt"
  if [[ -s "$outdir/_index.html" ]]; then
    grep -Eo 'href="[^"]+"|src="[^"]+"' "$outdir/_index.html" \
      | sed -E 's/^(href|src)="(.*)"/\2/' \
      | sort -u | tee -a "$outdir/links.txt"
  fi

  # 4) 允许方法（OPTIONS），看看是否暴露 JSON/表单入口（只对 / 与已知页）
  echo "—— OPTIONS ——" | tee "$outdir/options.txt"
  for p in / /login.html /signup.html; do
    curl -sS -m 5 -i -X OPTIONS "http://$ip:5000$p" | tee -a "$outdir/options.txt" >/dev/null || true
    echo "----" >> "$outdir/options.txt"
  done
done

echo "✅ 基础摸底完成，结果在 recon_out/"
