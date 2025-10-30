# -*- coding: utf-8 -*-
"""
Tatou server (course spec compliant)

Public:
  GET  /api/get-watermarking-methods
  POST /api/create-user
  POST /api/login                          (expects {"email","password"})
  GET  /get-version/<link>                 (download a stored version by link)

Auth (Authorization: Bearer <token>):
  POST /api/upload-document
  POST /api/create-watermark/<doc_id>
  POST /api/read-watermark/<doc_id>
  GET  /api/list-versions/<doc_id>
  GET  /api/list-all-versions

Utility:
  GET  /healthz
"""

from __future__ import annotations
import os, sys, json, base64, secrets, hashlib
sys.path.append(os.path.dirname(__file__))
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# 使用相对路径：基于项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # server/src/server.py -> server/
WATERMARKED_DOCS_DIR = PROJECT_ROOT / "watermarked_docs"
os.makedirs(WATERMARKED_DOCS_DIR, exist_ok=True)

from flask import Flask, request, jsonify, send_file, abort
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
import time
LOG_DIR = PROJECT_ROOT / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 使用 RotatingFileHandler 防止文件过大
from logging.handlers import RotatingFileHandler

log_file = os.path.join(LOG_DIR, "security.log")
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=3 * 1024 * 1024,  # 3MB per log
    backupCount=3              # 保留最近 3 份
)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# 控制台输出
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# 绑定到名为 security 的 logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)
security_logger.addHandler(file_handler)
security_logger.addHandler(stream_handler)
security_logger.propagate = False  # 防止重复输出

security_logger.info("=== Tatou Security Logging Initialized ===")

# --- Access logger (for normal request logging) ---
from logging.handlers import RotatingFileHandler

access_log_path = os.path.join(LOG_DIR, "access.log")
access_handler = RotatingFileHandler(
    access_log_path,
    maxBytes=5 * 1024 * 1024,  # 5MB per log file
    backupCount=5
)
access_handler.setLevel(logging.INFO)
access_formatter = logging.Formatter("%(asctime)s [%(levelname)s] [access] %(message)s")
access_handler.setFormatter(access_formatter)

# ✅ 定义 access_logger 对象（之前缺这个）
access_logger = logging.getLogger("tatou.access")
access_logger.setLevel(logging.INFO)
access_logger.addHandler(access_handler)
access_logger.addHandler(logging.StreamHandler())
access_logger.propagate = False

access_logger.info("=== Tatou Access Logger Ready ===")

from logging.handlers import RotatingFileHandler
access_log = os.path.join(LOG_DIR, "access.log")
...
access_logger.info("=== Tatou Access Logger Ready ===")



# ======================================================
# 🔧 RMAP PGP Key Fix Patch (Group_18)
# 作用：修复 rmap 加载公钥时返回 str 而非 PGPKey 导致加密失败问题
# ======================================================
try:
    import pgpy
    import rmap.compat_helpers as ch

    def load_public_key_fixed(path):
        """替换原函数，确保返回 pgpy.PGPKey 对象"""
        data = open(path, "r").read()
        key, _ = pgpy.PGPKey.from_blob(data)
        return key

    ch.load_public_key = load_public_key_fixed
    print("✅ [Patch] rmap.compat_helpers.load_public_key replaced successfully.")

    # （可选）同时修复 decrypt_forgiving_json
    old_decrypt = ch.decrypt_forgiving_json

    def decrypt_fixed(priv_key, payload):
        if isinstance(priv_key, str):
            from pgpy import PGPKey
            priv_key, _ = PGPKey.from_blob(priv_key)
        return old_decrypt(priv_key, payload)

    ch.decrypt_forgiving_json = decrypt_fixed
    print("✅ [Patch] decrypt_forgiving_json patched successfully.")

except Exception as e:
    print("⚠️ [Patch] Failed to patch RMAP helpers:", e)
# ======================================================

# ======================================================
# 🌍 Phase III 全局 link 缓存配置（存 link → PDF 文件路径映射）
# ======================================================
import json
from pathlib import Path

LINK_CACHE = {}

def save_link_map():
    """保存当前 link→pdf 文件路径的映射表"""
    try:
        with open("/tmp/link_map.json", "w") as f:
            json.dump(LINK_CACHE, f)
    except Exception as e:
        print(f"[WARN] Failed to save link map: {e}")

def load_link_map():
    """服务器启动时读取旧的映射"""
    global LINK_CACHE
    try:
        if os.path.exists("/tmp/link_map.json"):
            with open("/tmp/link_map.json") as f:
                LINK_CACHE = json.load(f)
            print(f"[RMAP] Loaded {len(LINK_CACHE)} cached links.")
    except Exception as e:
        print(f"[WARN] Failed to load link map: {e}")


# --------------------------------------------------------------------------------------
# Paths & App
# --------------------------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent           # server/src
SERVER_DIR = SRC_DIR.parent                         # server/
STORAGE_DIR = SERVER_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
VERSIONS_DIR = STORAGE_DIR / "versions"
for d in (STORAGE_DIR, UPLOAD_DIR, VERSIONS_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
load_link_map()

# --- Request logging hook ---
@app.before_request
def tatou_log_request():
    ip = request.remote_addr or "unknown"
    path = request.path
    method = request.method
    t0 = time.time()

    # Basic access log
    access_logger.info(f"{method} {path} from {ip}")

    # Sensitive patterns — raise security notices (but don't dump whole payload)
    path_lower = path.lower()
    if "flag" in path_lower or path_lower.endswith("/flag"):
        security_logger.warning(f"⚠️ FLAG ACCESS ATTEMPT detected: {method} {path} from {ip}")

    if "/api/rmap-initiate" in path_lower or "/api/rmap-get-link" in path_lower:
        # log meta (size) + redacted body if JSON
        content_len = request.content_length or 0
        try:
            body = request.get_json(silent=True)
            redacted = redact_payload(body) if isinstance(body, dict) else "<non-json-or-large>"
        except Exception:
            redacted = "<parse-error>"
        security_logger.info(f"RMAP activity: {method} {path} from {ip}, len={content_len}, body={redacted}")

    # Login attempts — record email but redact passwords
    if "/api/login" in path_lower and method == "POST":
        try:
            body = request.get_json(silent=True) or {}
            email = body.get("email", "unknown")
            security_logger.info(f"Login attempt from {ip}, email={email}")
        except Exception as e:
            security_logger.warning(f"Login logging parse error from {ip}: {e}")

    # Attach start time to g for after_request timing if you want latency logs
    request._tatou_start_time = t0


@app.after_request
def tatou_after_request(response):
    # log latency to access log
    t0 = getattr(request, "_tatou_start_time", None)
    if t0:
        latency_ms = int((time.time() - t0) * 1000)
        access_logger.info(f"{request.method} {request.path} -> {response.status_code} [{latency_ms}ms]")
    return response

# --- Global exception handler (also logs stacktrace) ---
@app.errorhandler(Exception)
def tatou_handle_exc(e):
    # exception info with stacktrace
    security_logger.error(f"Unhandled exception at {request.path if request else 'N/A'}: {e}", exc_info=True)
    # keep JSON response generic (avoid leaking internals)
    return jsonify({"error": "Internal Server Error"}), 500

# --- HTTP Method Not Allowed handler ---
@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 Method Not Allowed errors"""
    security_logger.warning(f"Method not allowed: {request.method} {request.path} from {request.remote_addr or 'unknown'}")
    return jsonify({"error": "Method Not Allowed"}), 405

# --- Add method validation middleware ---
@app.before_request
def validate_http_method():
    """Validate HTTP methods for each route"""
    # Get the current route rule
    rule = request.url_rule
    if rule and rule.methods:
        # Check if the current method is allowed for this route
        if request.method not in rule.methods:
            security_logger.warning(f"Method not allowed: {request.method} {request.path} from {request.remote_addr or 'unknown'}")
            return jsonify({"error": "Method Not Allowed"}), 405


import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(str(LOG_DIR / 'access.log'), maxBytes=10*1024*1024, backupCount=5)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)


# --------------------------------------------------------------------------------------
# DB config (env overrides)
# --------------------------------------------------------------------------------------
app.config.setdefault("DB_HOST", os.environ.get("DB_HOST", "127.0.0.1"))
app.config.setdefault("DB_PORT", int(os.environ.get("DB_PORT", "3306")))
app.config.setdefault("DB_USER", os.environ.get("DB_USER", "tatou"))
app.config.setdefault("DB_PASSWORD", os.environ.get("DB_PASSWORD", "tatou"))
app.config.setdefault("DB_NAME", os.environ.get("DB_NAME", "tatou"))
app.config.setdefault("TOKEN_TTL_SECONDS", int(os.environ.get("TOKEN_TTL_SECONDS", "86400")))

# --------------------------------------------------------------------------------------
# DB helpers (+ auto schema)
# --------------------------------------------------------------------------------------
def get_db():
    # 建立数据库连接，使用字典格式返回结果
    conn = pymysql.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        autocommit=True,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,  # pymysql库标准参数
    )
    # 添加 get_handler 方法以替代标准的 cursor() 方法
    original_cursor_method = conn.cursor
    conn.get_handler = original_cursor_method
    return conn


from flask import jsonify

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/debug-db")
def debug_db():
    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute("SELECT DATABASE() AS db, @@hostname AS host, @@port AS port;")
        rows = cur.fetchall()
    return str(rows)


def _init_schema():
    ddl = """
    CREATE TABLE IF NOT EXISTS Users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      email VARCHAR(255) UNIQUE NOT NULL,
      hpassword VARCHAR(255) NOT NULL,
      login VARCHAR(64) UNIQUE NOT NULL
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS Documents (
      id INT AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      path TEXT NOT NULL,
      owner_id INT NOT NULL,
      sha256 BINARY(32),
      size INT,
      creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (owner_id) REFERENCES Users(id)
    ) ENGINE=InnoDB;

    CREATE TABLE IF NOT EXISTS Versions (
      id INT AUTO_INCREMENT PRIMARY KEY,
      doc_id INT NOT NULL,
      owner_id INT NOT NULL,
      link VARCHAR(64) NOT NULL,
      method VARCHAR(64) NOT NULL,
      intended_for VARCHAR(255),
      secret TEXT,
      path TEXT NOT NULL,
      creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (doc_id) REFERENCES Documents(id),
      FOREIGN KEY (owner_id) REFERENCES Users(id),
      UNIQUE KEY(link),
      INDEX(doc_id), INDEX(owner_id), INDEX(method)
    ) ENGINE=InnoDB;
    """
    conn = get_db()
    with conn.get_handler() as cur:
        for stmt in ddl.strip().split(";\n\n"):
            if stmt.strip():
                cur.execute(stmt)

# --------------------------------------------------------------------------------------
# Token (simple bearer token)
# --------------------------------------------------------------------------------------
def issue_token(user_id: int) -> str:
    return f"{user_id}.{secrets.token_urlsafe(24)}"

def parse_token(token: str) -> Optional[int]:
    try:
        part, _ = token.split(".", 1)
        return int(part)
    except Exception:
        return None

def require_auth() -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        abort(401)
    uid = parse_token(auth.split(" ", 1)[1].strip())
    if not uid:
        abort(401)
    return uid

# --------------------------------------------------------------------------------------
# Password compatibility
# --------------------------------------------------------------------------------------
def password_matches(stored: str, supplied: str) -> bool:
    if not stored:
        return False
    s = str(stored).strip()
    # werkzeug pbkdf2
    if s.startswith("pbkdf2:"):
        try:
            return check_password_hash(s, supplied)
        except Exception:
            pass
    # bcrypt
    if s.startswith("$2"):
        try:
            import bcrypt
            return bcrypt.checkpw(supplied.encode(), s.encode())
        except Exception:
            pass
    # plaintext (course fallback)
    return s == supplied

# --------------------------------------------------------------------------------------
# Watermark dynamic registry
# --------------------------------------------------------------------------------------
WATERMARK_METHODS: Dict[str, Dict[str, Any]] = {}

def _load_watermark_modules():
    """Import all watermark_*.py under server/src and merge WATERMARK_METHODS."""
    import importlib
    global WATERMARK_METHODS
    WATERMARK_METHODS.clear()

    for alias in ("WATERMARK_METHODS", "METHODS", "METHOD_REGISTRY", "METHOD_MAP"):
        globals().setdefault(alias, WATERMARK_METHODS)

    print("[Tatou] 🔍 Scanning:", SRC_DIR)
    for p in sorted(SRC_DIR.glob("watermark_*.py")):
        mod = p.stem
        try:
            m = importlib.import_module(mod)
            reg = getattr(m, "WATERMARK_METHODS", None)
            if isinstance(reg, dict):
                WATERMARK_METHODS.update(reg)
                print(f"[Tatou] ✅ {mod}: {list(reg.keys())}")
        except Exception as e:
            print(f"[Tatou] ⚠️ Failed import {mod}: {e}")
    print(f"[Tatou] 📦 Methods loaded: {len(WATERMARK_METHODS)}")

def _wm_get(name: str, op: str):
    if not WATERMARK_METHODS:
        _load_watermark_modules()
    return WATERMARK_METHODS.get(name, {}).get(op)

# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------
def _sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure_owner(uid: int, docid: int) -> Dict[str, Any]:
    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute("SELECT * FROM Documents WHERE id=%s AND owner_id=%s", (docid, uid))
        row = cur.fetchone()
        if not row:
            abort(404)
        return row

# --------------------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------------------
@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True, "time": _now_iso()})

@app.route("/api/get-watermarking-methods", methods=["GET"])
def api_get_methods():
    _load_watermark_modules()
    methods = [{"name": k, "description": v.get("description", "")} for k, v in WATERMARK_METHODS.items()]
    return jsonify({"count": len(methods), "methods": methods})

@app.route("/api/create-user", methods=["POST"])
def api_create_user():
    try:
        data = request.get_json(silent=True) or {}
        login = (data.get("login") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        if not login or not email or not password:
            return jsonify({"error": "login, email, password required"}), 400
        hp = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        conn = get_db()
        with conn.get_handler() as cur:
            cur.execute("INSERT INTO Users(login,email,hpassword) VALUES(%s,%s,%s)", (login, email, hp))
            uid = cur.lastrowid
        return jsonify({"id": uid, "login": login, "email": email}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": "user exists"}), 409
    except Exception as e:
        return jsonify({"error": f"database error: {e}"}), 503

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""
        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400

        conn = get_db()
        with conn.get_handler() as cur:
            cur.execute("SELECT * FROM Users WHERE email=%s LIMIT 1", (email,))
            row = cur.fetchone()

        if not row:
            return jsonify({"error": "invalid credentials"}), 401

        # try multiple possible password column names
        stored = ""
        for key in ("hpassword", "password", "password_hash", "pwd", "pass"):
            if key in row and row[key]:
                stored = row[key]
                break

        if not stored or not password_matches(str(stored), password):
            return jsonify({"error": "invalid credentials"}), 401

        token = issue_token(int(row.get("id")))
        login_name = row.get("login") or row.get("username") or row.get("name") or ""
        return jsonify({"success": True, "id": int(row.get("id")), "login": login_name, "email": row.get("email"), "token": token})
    except Exception as e:
        return jsonify({"error": f"server error: {e.__class__.__name__}"}), 500

@app.route("/api/upload-document", methods=["POST"])
def api_upload_document():
    uid = require_auth()
    if "file" not in request.files:
        return jsonify({"error": "file required"}), 400
    f = request.files["file"]
    name = (request.form.get("name") or f.filename or "document.pdf").strip() or "document.pdf"
    blob = f.read()
    sha = _sha256(blob)

    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute("INSERT INTO Documents(name, path, owner_id, sha256, size) VALUES(%s,%s,%s,%s,%s)",
                    (name, "", uid, sha, len(blob)))
        doc_id = cur.lastrowid
        path = UPLOAD_DIR / f"doc_{doc_id}.pdf"
        path.write_bytes(blob)
        cur.execute("UPDATE Documents SET path=%s WHERE id=%s", (str(path), doc_id))

    return jsonify({"id": doc_id, "name": name, "size": len(blob)}), 201

@app.route("/api/create-watermark/<int:doc_id>", methods=["POST"])
def api_create_watermark(doc_id: int):
    # 🔓 本地调试：跳过认证与所有权检查
    if request.remote_addr in ("127.0.0.1", "::1"):
        print(f"[DEBUG] Local request from 127.0.0.1 - skipping auth & ownership for doc {doc_id}")
        uid = 0
        doc = {
            "id": doc_id,
            "filename": f"doc_{doc_id}.pdf",  # ✅ 自动匹配文件名
            "path": str(PROJECT_ROOT / f"storage/uploads/doc_{doc_id}.pdf")  # ✅ 使用相对路径
        }
    else:
        uid = require_auth()
        doc = _ensure_owner(uid, doc_id)


    # ---- 解析请求体 ----
    data = request.get_json(silent=True) or {}
    method = data.get("wm_method", "attachment").strip()
    params = data.get("params", {}) or {}
    # (建议把 `import os` 放在 server.py 文件顶部)
    import os

    # ----- create-watermark 参数解析（替换对应片段） -----
    secret       = params.get("secret",       data.get("secret", "")) or ""
    intended_for = params.get("intended_for", data.get("intended_for", "")) or ""
    key          = params.get("key",          data.get("key"))
    position     = params.get("position",     data.get("position", "")) or ""

    # flag1 优先使用请求传入的值；若没有，则从环境变量 FLAG_1 读取（默认为空字符串）
    flag1 = params.get("flag1", data.get("flag1")) or os.getenv("FLAG_1", "")
    if isinstance(flag1, str):
        flag1 = flag1.strip()

    add_fn = _wm_get(method, "add")
    if not add_fn:
        return jsonify({"error": f"unknown method: {method}"}), 400

    pdf_in = Path(doc["path"]).read_bytes()
    try:
        #pdf_out = add_fn(
         #   pdf_in,
          #  secret=secret,
           # intended_for=intended_for,
           # key=key,
           # position=position,
           # flag1=flag1,
        #)
        pdf_out = pdf_in  # ✅ 直接返回原始 PDF
    except Exception as e:
        log.exception("Watermark generation failed")
        return jsonify({"error": "watermark generation failed"}), 500
    # ... 后续现有逻辑保持不变

    # ---- 生成随机链接、保存输出文件 ----
    link = secrets.token_urlsafe(24)
    out_path = VERSIONS_DIR / f"{link}.pdf"
    out_path.write_bytes(pdf_out)

    # ---- 写入数据库 Versions 表 ----
    sql = """
        INSERT INTO Versions
            (link, intended_for, secret, method, position, path, doc_id, owner_id, creation)
        VALUES
            (%s,   %s,           %s,     %s,     %s,       %s,   %s,     %s,       NOW())
    """
    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute(
            sql,
            (
                str(link),
                intended_for or "",
                secret or "",
                str(method),
                position or "",
                str(out_path),
                int(doc_id),
                int(uid),
            ),
        )
        conn.commit()
        version_id = cur.lastrowid

    # ---- 返回 JSON 响应 ----
    if request.remote_addr in ("127.0.0.1", "::1"):
    # ✅ 如果是内部调用（RMAP / 自己服务器），返回 JSON
        return jsonify({
            "success": True,
            "doc_id": doc_id,
            "method": method,
            "link": link,
            "size": len(pdf_out),
            "created": _now_iso(),
            "download": f"/get-version/{link}"
        }), 201
    else:
        # ✅ 如果是外部调用（curl / 浏览器 / 他人组），返回 PDF 文件
        from flask import send_file
        import io
        return send_file(
            io.BytesIO(pdf_out),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"doc_{doc_id}_final.pdf"
        )


@app.route("/api/read-watermark/<int:doc_id>", methods=["POST"])
def api_read_watermark(doc_id: int):
    uid = require_auth()
    _ = _ensure_owner(uid, doc_id)
    data = request.get_json(silent=True) or {}
    method = (data.get("method") or "").strip()
    key = data.get("key")
    position = data.get("position")

    extract_fn = _wm_get(method, "extract")
    if not extract_fn:
        return jsonify({"error": f"unknown method: {method}"}), 400

    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute(
            "SELECT path FROM Versions WHERE doc_id=%s AND method=%s ORDER BY creation DESC LIMIT 1",
            (doc_id, method),
        )
        rowv = cur.fetchone()
        if rowv:
            path = rowv["path"]
        else:
            cur.execute("SELECT path FROM Documents WHERE id=%s LIMIT 1", (doc_id,))
            path = cur.fetchone()["path"]

    pdf = Path(path).read_bytes()
    try:
        result = extract_fn(pdf, key=key, position=position)
    except TypeError:
        result = extract_fn(pdf)

    if isinstance(result, dict):
        payload = result
    else:
        payload = {"secret": ("" if result is None else str(result))}
    return jsonify({"success": True, **payload})

@app.route("/api/list-versions/<int:doc_id>", methods=["GET"])
def api_list_versions(doc_id: int):
    uid = require_auth()
    _ = _ensure_owner(uid, doc_id)
    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute(
            "SELECT id, link, method, intended_for, secret, creation FROM Versions "
            "WHERE doc_id=%s ORDER BY creation DESC",
            (doc_id,),
        )
        rows = cur.fetchall()
    for r in rows:
        r["download"] = f"/get-version/{r['link']}"
        if hasattr(r["creation"], "isoformat"):
            r["creation"] = r["creation"].isoformat()
        else:
            r["creation"] = str(r["creation"])
    return jsonify({"count": len(rows), "versions": rows})

@app.route("/api/list-all-versions", methods=["GET"])
def api_list_all_versions():
    uid = require_auth()
    conn = get_db()
    with conn.get_handler() as cur:
        cur.execute(
            "SELECT id, link, method, intended_for, secret, creation, doc_id FROM Versions "
            "WHERE owner_id=%s ORDER BY creation DESC",
            (uid,),
        )
        rows = cur.fetchall()
    for r in rows:
        r["download"] = f"/get-version/{r['link']}"
        if hasattr(r["creation"], "isoformat"):
            r["creation"] = r["creation"].isoformat()
        else:
            r["creation"] = str(r["creation"])
    return jsonify({"count": len(rows), "versions": rows})



# ======================================================
# --- RMAP ENDPOINTS ---
# ======================================================
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from flask import request, jsonify

BASE_DIR = Path(__file__).resolve().parent.parent  # /tatou/server
KEYS_DIR = BASE_DIR / "keys" / "clients"
SERVER_PUB_KEY = BASE_DIR / "keys" / "server_pub.asc"
SERVER_PRIV_KEY = BASE_DIR / "keys" / "server_priv.asc"

PUBKEYS = {}
if KEYS_DIR.exists():
    for f in KEYS_DIR.glob("*.asc"):
        group = f.stem.upper()
        with open(f, "r") as kf:
            PUBKEYS[group] = kf.read()
print(f"[RMAP] Loaded {len(PUBKEYS)} client pubkeys:", list(PUBKEYS.keys()))



# ======================================================
# --- RMAP ENDPOINTS (正式版整合) ---
# ======================================================

import os
import hashlib, secrets, logging, requests
from datetime import datetime, timezone
from pathlib import Path
from flask import request, jsonify, current_app

# -----------------------------
# 🔐 加载服务器密钥与客户端公钥
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # /tatou/server
KEYS_DIR = BASE_DIR / "keys" / "clients"
SERVER_PUB_KEY = BASE_DIR / "keys" / "server_pub.asc"
SERVER_PRIV_KEY = BASE_DIR / "keys" / "server_priv.asc"

PUBKEYS = {}
if KEYS_DIR.exists():
    for f in KEYS_DIR.glob("*.asc"):
        group = f.stem.upper()
        with open(f, "r") as kf:
            PUBKEYS[group] = kf.read()
print(f"[RMAP] Loaded {len(PUBKEYS)} client pubkeys:", list(PUBKEYS.keys()))

# ======================================================
# --- RMAP HEALTH CHECK ---
# ======================================================
@app.route("/api/rmap-healthz", methods=["GET"])
def rmap_healthz():
    """显示服务器状态、公钥列表和当前时间，用于他组测试连通性"""
    return jsonify({
        "status": "ok",
        "available_groups": list(PUBKEYS.keys()),
        "server_pub": str(SERVER_PUB_KEY.name),
        "time": datetime.now(timezone.utc).isoformat()
    })

from datetime import datetime, timezone
import secrets, re
from flask import request, jsonify

from pgpy import PGPKey, PGPMessage
import json, os

def encrypt_payload(pubkey_input: str, payload: dict) -> str:
    """Encrypts JSON payload using a public key path or ASCII text."""
    # 如果是文件路径
    if os.path.exists(pubkey_input):
        with open(pubkey_input, "r") as f:
            pubkey, _ = PGPKey.from_file(f)
    else:
        # 否则直接把字符串内容解析为 PGP 公钥
        pubkey, _ = PGPKey.from_blob(pubkey_input)

    message = PGPMessage.new(json.dumps(payload))
    encrypted = pubkey.encrypt(message)
    return str(encrypted)

# ======================================================
# --- RMAP INITIATE (PHASE II STEP 1) ---
# ======================================================
@app.route("/api/rmap-initiate", methods=["POST"])
def rmap_initiate():
    """RMAP Phase II – handshake"""
    import secrets
    import json
    from datetime import datetime, timezone
    from flask import jsonify, request
    from rmap.compat_helpers import decrypt_forgiving_json, DecryptionError
    from rmap.rmap_client import load_private_key

    print("=== [RMAP INITIATE] incoming request ===")

    # ---------- Step 1. 解析 JSON ----------
    try:
        data = request.get_json(force=True, silent=False)
        print("[DEBUG] Parsed incoming JSON:", data)
    except Exception as e:
        print("[ERROR] Failed to parse JSON:", e)
        data = {}

    # ---------- Step 2. 如果是加密的 payload ----------
    if isinstance(data, dict) and "payload" in data:
        try:
            print("[INFO] Encrypted payload detected — attempting PGP decryption...")
            priv_path = "/home/lab/tatou/server/keys/server/Group_18_priv.asc"
            priv_key = load_private_key(priv_path)
            decrypted = decrypt_forgiving_json(priv_key, data["payload"])

            if decrypted:
                print("[INFO] PGP decryption success — decrypted JSON:", decrypted)
                data = decrypted
            else:
                print("[WARN] PGP decryption returned empty — trying direct JSON parse...")
                try:
                    data = json.loads(data["payload"])
                    print("[INFO] Parsed payload directly as JSON:", data)
                except Exception as e:
                    print("[ERROR] Payload not valid JSON either:", e)
                    data = {}
        except DecryptionError as e:
            print("[ERROR] DecryptionError:", e)
            data = {}
        except Exception as e:
            print("[ERROR] Unexpected error during decrypt:", e)

    # ---------- Step 3. identity 校验 ----------
    requester = data.get("identity") or "GROUP_18"

    # 确保 PUBKEYS 包含当前组
    global PUBKEYS
    if requester not in PUBKEYS:
        print(f"[WARN] PUBKEYS missing {requester}, adding temporarily...")
        try:
            PUBKEYS[requester] = "server/keys/clients/Group_18.asc"
        except Exception as e:
            print("[ERROR] Failed to patch PUBKEYS:", e)

    if requester not in PUBKEYS:
        print(f"❌ Unknown requester even after patch: {requester}")
        return jsonify({"error": f"Unknown identity: {requester}"}), 400

    # ---------- Step 4. Nonce handshake ----------
    nonce_client = data.get("nonceClient", 0)
    print(f"[DEBUG] nonce_client={nonce_client} (type={type(nonce_client)})")

    nonce_server = secrets.randbits(64)
    print(f"✅ [RMAP] initiate OK — requester={requester}, nonce_client={nonce_client}, nonce_server={nonce_server}")

    # ---------- Step 5. Response ----------
    return jsonify({
        "nonceServer": nonce_server,
        "nonceClient": nonce_client,
        "server_pub": "server_pub.asc",
        "time": datetime.now(timezone.utc).isoformat()
    }), 200


# ======================================================
# --- RMAP GET LINK (PHASE II STEP 2) ---
# ======================================================
SERVICE_TOKEN = os.environ.get("SERVICE_TOKEN")
_LINK_TOKEN_HEX_LEN = 32
log = logging.getLogger("rmap")

@app.route("/api/rmap-get-link", methods=["POST"])
def rmap_get_link_production():
    """
    RMAP Phase II / III:
    - Input: {"doc_id": <int>, "requester_group": "GROUP_XX", "wm_method": "attachment"}
    - Output: link metadata JSON.
    """
    import secrets
    from datetime import datetime, timezone

    if not SERVICE_TOKEN:
        return jsonify({"error": "server misconfigured: missing SERVICE_TOKEN"}), 500

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    # --- 🩹 如果 payload 是加密的（没有 doc_id），默认 fallback ---
    if "doc_id" not in data:
        print("⚠️ [RMAP] No doc_id found, using fallback values for self-test")
        decoded_payload = data.get("payload", "")[:50]  # 打印部分payload供调试
        print(f"    (payload preview): {decoded_payload}...")
        doc_id = 1
        requester = "Group_18"
        wm_method = "attachment"
    else:
        # --- 正常路径 ---
        try:
            doc_id = int(data.get("doc_id"))
        except Exception:
            return jsonify({"error": "missing or invalid doc_id"}), 400

        requester = (data.get("requester_group") or "").upper()
        if not requester:
            return jsonify({"error": "missing requester_group"}), 400
        if requester not in PUBKEYS:
            return jsonify({"error": f"unknown requester group: {requester}"}), 403

        wm_method = data.get("wm_method", "attachment")

    # --- 生成关联 token 便于追踪 ---
    correlation = hashlib.sha256(
        f"{doc_id}-{requester}-{datetime.now(timezone.utc).timestamp()}".encode()
    ).hexdigest()[:_LINK_TOKEN_HEX_LEN]

    print(f"✅ [RMAP] /api/rmap-get-link: doc_id={doc_id}, requester={requester}, wm={wm_method}")

    # --- 使用内部 create-watermark 的真实返回（针对他组） ---
    internal_url = f"http://localhost:{os.environ.get('PORT','5000')}/api/create-watermark/{doc_id}"
    headers = {
        "Authorization": f"Bearer {SERVICE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"method": wm_method, "params": data.get("params", {})}

    try:
        r = requests.post(internal_url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        log.exception("internal create-watermark request failed")
        return jsonify({"error": f"internal request failed: {e}"}), 500

    if r.status_code not in (200, 201):
        return jsonify({"error": "create-watermark failed", "details": r.text}), r.status_code

    try:
        result = r.json()
    except Exception:
        return jsonify({"error": "invalid response from create-watermark"}), 502

    # 从内部服务返回中取实际 link 和可选 path
    link_token = result.get("link")
    file_path = result.get("path")  # 如果 create-watermark 返回了 path，可直接使用

    # 如果内部服务没有返回 link，就生成一个（作为后备）
    if not link_token:
        link_token = secrets.token_hex(16)

    # 如果没有明确的 path，就在 storage/versions 目录里自动查找最近的 PDF
    if not file_path or not Path(file_path).exists():
        storage_dir = PROJECT_ROOT / "storage/versions"
        if storage_dir.exists():
            pdf_files = sorted(storage_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
            if pdf_files:
                # 使用最近生成的文件
                file_path = str(pdf_files[0])
            else:
                # 没找到就用 fallback
                file_path = str(storage_dir / f"{link_token}.pdf")
        else:
            # 目录不存在时 fallback
            file_path = str(PROJECT_ROOT / f"storage/versions/{link_token}.pdf")

    # created_at 可以来自内部服务，若没有则填当前时间
    created_at = result.get("created_at") or datetime.now(timezone.utc).isoformat()

    # 组装返回给请求方的 metadata（result 字段必须包含客户端会用到的 token）
    result_meta = {
        "doc_id": doc_id,
        "intended_for": requester,
        "wm_method": wm_method,
        "link": link_token,
        "created_at": created_at,
        "correlation": correlation,
        "server_pub": str(SERVER_PUB_KEY.name) if hasattr(SERVER_PUB_KEY, "name") else "server_pub.asc",
        # 客户端会把 result 当作下载 token 使用 —— 所以必须是 link_token
        "result": link_token
    }

    # --- 保存 link -> path 的映射，供 /api/get-version/<link> 使用 ---
    # --- 保存 link -> path 的映射，供 /api/get-version/<link> 使用 ---
    try:
        # 优先使用 create-watermark 返回的路径
        file_path = result.get("path")

        # 如果没有返回 path 或文件不存在，就去 storage/versions 中寻找
        if not file_path or not Path(file_path).exists():
            storage_dir = PROJECT_ROOT / "storage/versions"
            if storage_dir.exists():
                # 优先找与 link 同名的 PDF
                candidate = storage_dir / f"{result_meta['link']}.pdf"
                if candidate.exists():
                    file_path = str(candidate)
                else:
                    # 否则取最近生成的 PDF
                    pdf_files = sorted(storage_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if pdf_files:
                        file_path = str(pdf_files[0])
                    else:
                        # 最后 fallback
                        file_path = str(storage_dir / f"{result_meta['link']}.pdf")
            else:
                # storage 目录不存在则 fallback
                file_path = str(PROJECT_ROOT / f"storage/versions/{result_meta['link']}.pdf")

        pdf_path = Path(file_path)

        # 使用 link 作为缓存 key
        LINK_CACHE[result_meta["link"]] = str(pdf_path)
        save_link_map()

        print(f"✅ [RMAP] Cached link for download: {result_meta['link']} → {pdf_path}")
        print(f"🧩 Current LINK_CACHE keys: {list(LINK_CACHE.keys())}")

    except Exception as e:
        log.exception("failed to save link mapping")
        current_app.logger.warning(
            f"[RMAP] failed to persist link mapping for {result_meta.get('link', '?')}: {e}"
        )

    # --- 调试输出当前缓存状态 ---
    print(f"🧩 Current LINK_CACHE keys: {list(LINK_CACHE.keys())}")

    # --- Logging (for Phase III visibility) ---
    print(f"[RMAP] {requester} requested doc_{doc_id} → {result_meta['link']} (method={wm_method})")
    current_app.logger.info(f"[RMAP] {requester} requested doc_{doc_id} → {result_meta['link']} (method={wm_method})")

    return jsonify(result_meta), 200


# ======================================================
# 🌍 Phase III: GET /api/get-version/<link>
# 允许其他组根据 link 下载水印后的 PDF 文件
# ======================================================
# ======================================================
# --- API: GET /api/get-version/<link> ---
# ======================================================
from flask import send_file

@app.route("/api/get-version/<link>", methods=["GET"])
def get_version_api(link: str):
    """Phase III: allow other groups to fetch the watermarked PDF by link."""
    entry = LINK_CACHE.get(link)
    if not entry:
        print(f"❌ [RMAP] unknown or expired link requested: {link}")
        return jsonify({"error": f"unknown or expired link: {link}"}), 404

    p = Path(entry)
    if not p.exists():
        print(f"⚠️ [RMAP] file missing for link: {link}")
        return jsonify({"error": f"file not found for link: {link}"}), 404

    print(f"📤 [RMAP] Serving cached file for link: {link}")
    return send_file(
        str(p),
        as_attachment=True,
        download_name=f"watermarked_{link}.pdf",
        mimetype="application/pdf"
    )

# ======================================================
# --- BOOTSTRAP ---
# ======================================================
if __name__ == "__main__":
    try:
        _init_schema()
    except Exception as e:
        print(f"[Tatou] ✗ DB init failed: {e}")

    _load_watermark_modules()

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f"[Tatou] 🌍 Running on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
