#!/usr/bin/env bash
set -euo pipefail

# === 配置：把下面这个值替换成 group13 中出现的那条 64-hex 串 ===
TARGET64="fd3ca97bf1689edfd2b9bb72a5efd3ca97b5fc16ac785a27b7f1de96f7ad89c6"

BEST="best_flags.txt"
if [[ ! -f "$BEST" ]]; then
  echo "❌ $BEST not found. Run decode_probe.py first."
  exit 1
fi

echo "Target SHA256: $TARGET64"
echo "Scanning candidates from $BEST ..."
echo

hit=0
while read -r line; do
  # 跳过分组标题与空行
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^=== ]] && continue

  cand="$line"

  # 仅接受 40-hex 的候选
  if [[ ! "$cand" =~ ^[a-fA-F0-9]{40}$ ]]; then
    continue
  fi

  # Hypothesis A: SHA256(ASCII(flag40))
  sha_ascii=$(printf "%s" "$cand" | sha256sum | awk '{print $1}')
  # Hypothesis B: SHA256(raw20bytes(flag40))
  raw=$(printf "%s" "$cand" | xxd -r -p | sha256sum | awk '{print $1}')

  if [[ "$sha_ascii" == "$TARGET64" ]]; then
    echo "🎯 MATCH (ASCII)  flag40=$cand"
    echo "    SHA256(ASCII(flag40)) == TARGET64"
    hit=1
  fi

  if [[ "$raw" == "$TARGET64" ]]; then
    echo "🎯 MATCH (RAW20)  flag40=$cand"
    echo "    SHA256(raw20bytes(flag40)) == TARGET64"
    hit=1
  fi
done < <(grep -E '^[a-f0-9]{40}$' "$BEST" | tr 'A-F' 'a-f')

if [[ "$hit" -eq 0 ]]; then
  echo "ℹ️  No direct SHA256 match found under the two hypotheses."
  echo "    Try more key/iv derivations in aes_probe.py or inspect decode_probe_report.txt for more clues."
fi
