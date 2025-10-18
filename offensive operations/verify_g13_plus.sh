#!/usr/bin/env bash
set -euo pipefail

# === 把下面替换成你在 Group_13 中看到的 64-hex 目标（SHA256 目标值） ===
TARGET64="fd3ca97bf1689edfd2b9bb72a5efd3ca97b5fc16ac785a27b7f1de96f7ad89c6"

BEST="best_flags.txt"
HINTS="key_hints.txt"

if [[ ! -f "$BEST" ]]; then
  echo "❌ $BEST not found (run decode_probe.py first)." >&2
  exit 1
fi
if [[ ! -f "$HINTS" ]]; then
  echo "❌ $HINTS not found (run metadata_key_finder.py first)." >&2
  exit 1
fi

echo "[*] TARGET64 = $TARGET64"
echo "[*] Loading tokens from $HINTS ..."

# 1) 从 key_hints.txt 提取 token 候选（uuid/hex/关键词附近片段/word）
#    - uuid 有横线/无横线都会收
#    - hex: 32/40/48/64 位
#    - 文本词：长度 4-40 的 “字母数字._-” 片段
mapfile -t TOK_ASCII < <(
  awk 'NF{print}' "$HINTS" \
  | tr -d '\r' \
  | grep -Eo '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[0-9a-fA-F]{32}|[0-9a-fA-F]{40}|[0-9a-fA-F]{48}|[0-9a-fA-F]{64}|[A-Za-z0-9._-]{4,40})' \
  | sed 's/-//g' \
  | awk 'length($0)<=64' \
  | sort -u
)

# 2) 过滤出可能的 HEX token（偶数长度且只含 hex）
mapfile -t TOK_HEX < <(printf "%s\n" "${TOK_ASCII[@]}" \
  | grep -E '^[0-9A-Fa-f]+$' \
  | awk 'length($0)%2==0' \
  | sort -u)

echo "[*] tokens loaded: ascii=" ${#TOK_ASCII[@]} " hex=" ${#TOK_HEX[@]}

# 小工具函数
sha256_hex_ascii() {  # 对ASCII字符串做sha256
  printf "%s" "$1" | sha256sum | awk '{print $1}'
}
sha256_hex_raw() {    # 对原始字节做sha256
  # 从stdin读原始字节
  sha256sum | awk '{print $1}'
}

hmac_sha256_ascii() { # key=ASCII, msg=来自stdin原始字节
  local key="$1"
  openssl dgst -sha256 -mac HMAC -macopt "key:$key" | awk '{print $2}'
}
hmac_sha256_rawkey() { # key=HEX->raw, msg=来自stdin原始字节
  local keyhex="$1"
  openssl dgst -sha256 -mac HMAC -macopt "hexkey:$keyhex" | awk '{print $2}'
}

match() {
  local got="$1"
  [[ "$got" == "$TARGET64" ]]
}

hits=0

echo
echo "[*] Scanning candidates in $BEST ..."
# 3) 遍历 best_flags.txt 中所有 40-hex
while read -r cand; do
  [[ -z "$cand" ]] && continue
  [[ "$cand" =~ ^=== ]] && continue
  [[ ! "$cand" =~ ^[0-9a-fA-F]{40}$ ]] && continue
  flag40=$(echo "$cand" | tr 'A-F' 'a-f')

  # 3.1 基础两种（你已试过，但再跑一遍做记录）
  sha_ascii=$(sha256_hex_ascii "$flag40")
  if match "$sha_ascii"; then
    echo "🎯 MATCH: SHA256(ASCII(flag40))   flag40=$flag40"
    hits=$((hits+1))
  fi
  raw20=$(printf "%s" "$flag40" | xxd -r -p)
  sha_raw=$(printf "%s" "$raw20" | sha256_hex_raw)
  if match "$sha_raw"; then
    echo "🎯 MATCH: SHA256(raw20(flag40))   flag40=$flag40"
    hits=$((hits+1))
  fi

  # 3.2 带 token 的拼接/认证，分别试 ASCII token 与 HEX->raw token
  for tok in "${TOK_ASCII[@]}"; do
    # ASCII token 参与
    # T + ASCII(flag40)
    got=$(sha256_hex_ascii "${tok}${flag40}")
    match "$got" && { echo "🎯 MATCH: SHA256(tok+ASCII(flag40)) tok='$tok' flag40=$flag40"; hits=$((hits+1)); }
    # ASCII(flag40) + T
    got=$(sha256_hex_ascii "${flag40}${tok}")
    match "$got" && { echo "🎯 MATCH: SHA256(ASCII(flag40)+tok) tok='$tok' flag40=$flag40"; hits=$((hits+1)); }
    # T + raw20(flag40)
    got=$(printf "%s" "$tok" | cat - <(printf "%s" "$raw20") | sha256_hex_raw)
    match "$got" && { echo "🎯 MATCH: SHA256(tok+raw20(flag40)) tok='$tok' flag40=$flag40"; hits=$((hits+1)); }
    # raw20(flag40) + T
    got=$(cat <(printf "%s" "$raw20") <(printf "%s" "$tok") | sha256_hex_raw)
    match "$got" && { echo "🎯 MATCH: SHA256(raw20(flag40)+tok) tok='$tok' flag40=$flag40"; hits=$((hits+1)); }

    # HMAC (ASCII key)
    got=$(printf "%s" "$flag40" | hmac_sha256_ascii "$tok")
    match "$got" && { echo "🎯 MATCH: HMAC-SHA256(key=tok_ascii, msg=ASCII(flag40)) tok='$tok' flag40=$flag40"; hits=$((hits+1)); }
    got=$(printf "%s" "$raw20" | hmac_sha256_ascii "$tok")
    match "$got" && { echo "🎯 MATCH: HMAC-SHA256(key=tok_ascii, msg=raw20(flag40)) tok='$tok' flag40=$flag40"; hits=$((hits+1)); }
  done

  for hex in "${TOK_HEX[@]}"; do
    # HEX token 当成原始字节参与
    tokraw=$(printf "%s" "$hex" | xxd -r -p 2>/dev/null || true)
    [[ -z "${tokraw:-}" ]] && continue

    # rawT + ASCII(flag40)
    got=$(cat <(printf "%s" "$tokraw") <(printf "%s" "$flag40") | sha256_hex_raw)
    match "$got" && { echo "🎯 MATCH: SHA256(rawTok+ASCII(flag40)) tokhex='$hex' flag40=$flag40"; hits=$((hits+1)); }
    # ASCII(flag40) + rawT
    got=$(cat <(printf "%s" "$flag40") <(printf "%s" "$tokraw") | sha256_hex_raw)
    match "$got" && { echo "🎯 MATCH: SHA256(ASCII(flag40)+rawTok)) tokhex='$hex' flag40=$flag40"; hits=$((hits+1)); }
    # rawT + raw20(flag40)
    got=$(cat <(printf "%s" "$tokraw") <(printf "%s" "$raw20") | sha256_hex_raw)
    match "$got" && { echo "🎯 MATCH: SHA256(rawTok+raw20(flag40)) tokhex='$hex' flag40=$flag40"; hits=$((hits+1)); }
    # raw20(flag40) + rawT
    got=$(cat <(printf "%s" "$raw20") <(printf "%s" "$tokraw") | sha256_hex_raw)
    match "$got" && { echo "🎯 MATCH: SHA256(raw20(flag40)+rawTok)) tokhex='$hex' flag40=$flag40"; hits=$((hits+1)); }

    # HMAC (raw key)
    got=$(printf "%s" "$flag40" | hmac_sha256_rawkey "$hex")
    match "$got" && { echo "🎯 MATCH: HMAC-SHA256(key=tok_hex, msg=ASCII(flag40)) tokhex='$hex' flag40=$flag40"; hits=$((hits+1)); }
    got=$(printf "%s" "$raw20" | hmac_sha256_rawkey "$hex")
    match "$got" && { echo "🎯 MATCH: HMAC-SHA256(key=tok_hex, msg=raw20(flag40)) tokhex='$hex' flag40=$flag40"; hits=$((hits+1)); }
  done

done < <(awk 'NF && $0 !~ /^===/' "$BEST" | tr 'A-F' 'a-f')

if [[ "$hits" -eq 0 ]]; then
  echo
  echo "ℹ️  No match under extended variants."
  echo "   - 试着补充/手动添加 token（例如你认为像 key/salt 的字符串）到 key_hints.txt 再跑一次；"
  echo "   - 或将疑似 key/iv 直接硬编码到 aes_probe.py 的 derive_keys_from_material() 顶部再跑一轮解密；"
else
  echo
  echo "✅ Found $hits match(es). 以上打印的行里包含命中方式和 flag40。"
fi
