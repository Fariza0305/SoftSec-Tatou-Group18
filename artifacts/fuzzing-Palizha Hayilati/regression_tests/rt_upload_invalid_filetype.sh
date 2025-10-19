#!/usr/bin/env bash
set -euo pipefail
BASE_URL=${BASE_URL:-http://localhost:5000}
EMAIL=${EMAIL:-fuzzer@test.com}
PASSWORD=${PASSWORD:-FuzzerTest123!}
LOGIN_NAME=${LOGIN_NAME:-fuzzer_test}

# Ensure user exists (idempotent)
curl -s -S -X POST "$BASE_URL/api/create-user" \
  -H 'Content-Type: application/json' \
  -d "{\"login\":\"$LOGIN_NAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  -o /dev/null -w '' || true

# Obtain token
LOGIN_RESP=$(curl -s -S -X POST "$BASE_URL/api/login" -H 'Content-Type: application/json' -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
TOKEN=$(RESP="$LOGIN_RESP" python3 -c 'import os,json; print(json.loads(os.environ.get("RESP","{}")) .get("token",""))' || true)
if [ -z "$TOKEN" ]; then
  echo "Failed to obtain token" >&2
  exit 1
fi

# Upload non-PDF file; expect 400
STATUS=$(curl -s -S -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/upload-document" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/etc/hostname;type=text/plain" \
  -F "name=text.txt")
if [ "$STATUS" != "400" ]; then
  echo "Expected 400, got $STATUS" >&2
  exit 2
fi

echo "PASS: upload invalid filetype returns 400"
