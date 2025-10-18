#!/usr/bin/env bash
set -euo pipefail
PORT=5000
OUT=surface_report.txt
: > "$OUT"

paths=(
  "/" "/login" "/signup" "/upload" "/share" "/download" "/api" "/api/docs"
  "/health" "/metrics" "/admin" "/debug" "/config" "/status"
  "/static/" "/static/style.css" "/static/app.js" "/robots.txt" "/sitemap.xml"
)

echo "🔎 surface scan -> $OUT"
while read -r ip; do
  [[ -z "$ip" ]] && continue
  echo "============================" | tee -a "$OUT"
  echo "📡 $ip" | tee -a "$OUT"
  for p in "${paths[@]}"; do
    url="http://$ip:$PORT$p"
    code=$(curl -m 4 -sk -o /tmp/s.out -w "%{http_code}" "$url" || true)
    if [[ "$code" =~ ^2|3 ]]; then
      title=$(grep -o '<title>[^<]*' /tmp/s.out | head -1 | sed 's/<title>//')
      echo "✅ $url  [HTTP $code]  $title" | tee -a "$OUT"
      # 抽取可疑链接
      grep -Eo 'href="[^"]+"' /tmp/s.out | sed 's/href=//g' | tr -d '"' | head -5 | sed 's/^/    link: /' | tee -a "$OUT"
      grep -Eo 'action="[^"]+"' /tmp/s.out | sed 's/action=//g' | tr -d '"' | head -3 | sed 's/^/    form: /' | tee -a "$OUT"
    else
      echo "ℹ️  $url  [HTTP $code]" | tee -a "$OUT"
    fi
  done
done < targets.txt
echo "✅ done. 查看 $OUT"
