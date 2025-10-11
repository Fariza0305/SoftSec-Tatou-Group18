import os
import io
import hashlib
import datetime as dt
from pathlib import Path
from functools import wraps

from flask import Flask, jsonify, request, g, send_file, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# === 5.2 Listing 2: 导入 RMAP 库 ===
from rmap.identity_manager import IdentityManager
from rmap.rmap import RMAP

# 仅用于在内存中给 PDF 写入 metadata（最小侵入，不改你们的水印方法）
from pypdf import PdfReader, PdfWriter

# 你项目里的水印实现模块（保持不动）
try:
    from wm_mod import WMUtils, WatermarkingMethod
except Exception:
    WMUtils = None
    class WatermarkingMethod:
        pass


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")

    # ------- 基础配置 -------
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret"))
    app.config.setdefault("TOKEN_TTL_SECONDS", int(os.environ.get("TOKEN_TTL_SECONDS", "86400")))
    app.config.setdefault("DB_USER", os.environ.get("DB_USER", "root"))
    app.config.setdefault("DB_PASSWORD", os.environ.get("DB_PASSWORD", "password"))
    app.config.setdefault("DB_HOST", os.environ.get("DB_HOST", "127.0.0.1"))
    app.config.setdefault("DB_PORT", int(os.environ.get("DB_PORT", "3306")))
    app.config.setdefault("DB_NAME", os.environ.get("DB_NAME", "tatou"))
    # --- force SECRET_KEY fallback if missing ---
    if not app.config.get("SECRET_KEY"):
        import os as _os
        app.config["SECRET_KEY"] = _os.environ.get("SECRET_KEY","dev-secret")
    

    storage_root = os.environ.get("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "..", "storage"))
    app.config["STORAGE_DIR"] = Path(storage_root).resolve()
    app.config["STORAGE_DIR"].mkdir(parents=True, exist_ok=True)

    # ------- RMAP 初始化 -------
    base_dir = Path(__file__).resolve().parent.parent  # server/src/..
    app.config.setdefault("CLIENT_KEYS_DIR", base_dir / "keys" / "clients")
    app.config.setdefault("SERVER_PUB",     base_dir / "keys" / "server" / "server_pub.asc")
    app.config.setdefault("SERVER_PRIV",    base_dir / "keys" / "server" / "server_priv.asc")

    print(f"[RMAP] Initializing with clients_dir={app.config['CLIENT_KEYS_DIR']}")
    if not Path(app.config["SERVER_PUB"]).exists():
        print(f"[RMAP] Warning: server public key not found: {app.config['SERVER_PUB']}")
    if not Path(app.config["SERVER_PRIV"]).exists():
        print(f"[RMAP] Warning: server private key not found: {app.config['SERVER_PRIV']}")

    try:
        identity_mgr = IdentityManager(
            client_keys_dir=str(app.config["CLIENT_KEYS_DIR"]),
            server_public_key_path=str(app.config["SERVER_PUB"]),
            server_private_key_path=str(app.config["SERVER_PRIV"]),
            # server_private_key_passphrase=os.getenv("SERVER_PRIV_PASSPHRASE")
        )
        rmap = RMAP(identity_mgr)
        print("[RMAP] ✓ initialization successful")
    except Exception as e:
        print(f"[RMAP] ✗ initialization failed: {e}")
        rmap = None
        identity_mgr = None

    app.extensions = getattr(app, "extensions", {})
    app.extensions["identity_mgr"] = identity_mgr
    app.extensions["rmap"] = rmap

    # ------------------------------
    # DB engine helpers
    # ------------------------------
    def db_url() -> str:
        return (
            f"mysql+pymysql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}"
            f"@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}?charset=utf8mb4"
        )

    def get_engine():
        eng = app.config.get("_ENGINE")
        if eng is None:
            eng = create_engine(db_url(), pool_pre_ping=True, future=True)
            app.config["_ENGINE"] = eng
        return eng

    # ------------------------------
    # Auth helpers
    # ------------------------------
    def _serializer():
        return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="tatou-auth")

    def _auth_error(msg: str, code: int = 401):
        return jsonify({"error": msg}), code

    def require_auth(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return _auth_error("Missing or invalid Authorization header")
            token = auth.split(" ", 1)[1].strip()
            try:
                data = _serializer().loads(token, max_age=app.config["TOKEN_TTL_SECONDS"])
            except SignatureExpired:
                return _auth_error("Token expired")
            except BadSignature:
                return _auth_error("Invalid token")
            g.user = {"id": int(data["uid"]), "login": data["login"], "email": data.get("email")}
            return f(*args, **kwargs)
        return wrapper

    # ------------------------------
    # Utils
    # ------------------------------
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _safe_resolve_under_storage(p: str, storage_root: Path) -> Path:
        storage_root = storage_root.resolve()
        fp = Path(p)
        if not fp.is_absolute():
            fp = storage_root / fp
        fp = fp.resolve()
        try:
            fp.relative_to(storage_root)
        except ValueError:
            raise RuntimeError(f"path {fp} escapes storage root {storage_root}")
        return fp

    # ------------------------------
    # Static & Health
    # ------------------------------
    @app.route("/<path:filename>")
    def static_files(filename):
        return app.send_static_file(filename)

    @app.route("/")
    def home():
        return app.send_static_file("index.html")

    @app.get("/healthz")
    def healthz():
        try:
            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        return jsonify({"message": "The server is up and running.", "db_connected": db_ok}), 200

    # ------------------------------
    # Users
    # ------------------------------
    @app.post("/api/create-user")
    def create_user():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        login = (payload.get("login") or "").strip()
        password = payload.get("password") or ""
        if not email or not login or not password:
            return jsonify({"error": "email, login, and password are required"}), 400

        hpw = generate_password_hash(password)

        try:
            with get_engine().begin() as conn:
                res = conn.execute(
                    text("INSERT INTO Users (email, hpassword, login) VALUES (:email, :hpw, :login)"),
                    {"email": email, "hpw": hpw, "login": login},
                )
                uid = int(res.lastrowid)
                row = conn.execute(
                    text("SELECT id, email, login FROM Users WHERE id = :id"),
                    {"id": uid},
                ).one()
        except IntegrityError:
            return jsonify({"error": "email or login already exists"}), 409
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        return jsonify({"id": row.id, "email": row.email, "login": row.login}), 201

    @app.post("/api/login")
    def login():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip()
        password = payload.get("password") or ""
        if not email or not password:
            return jsonify({"error": "email and password are required"}), 400
        try:
            with get_engine().connect() as conn:
                row = conn.execute(
                    text("SELECT id, email, login, hpassword FROM Users WHERE email = :email LIMIT 1"),
                    {"email": email},
                ).first()
        except Exception:
            current_app.logger.exception("DB error during login")
            return jsonify({"error": "database error"}), 503

        valid = False
        if row:
            try:
                valid = check_password_hash(row.hpassword, password)
            except Exception:
                current_app.logger.exception("Password check failed for user %s", email)
                valid = False

        if not valid:
            return jsonify({"error": "invalid credentials"}), 401

        try:
            token = _serializer().dumps({"uid": int(row.id), "login": row.login, "email": row.email})
        except Exception:
            current_app.logger.exception("Token serialization failed for user %s", email)
            return jsonify({"error": "internal error"}), 500

        return jsonify({"token": token, "token_type": "bearer", "expires_in": app.config["TOKEN_TTL_SECONDS"]}), 200

    # ------------------------------
    # Documents
    # ------------------------------
    @app.post("/api/upload-document")
    @require_auth
    def upload_document():
        if "file" not in request.files:
            return jsonify({"error": "file is required (multipart/form-data)"}), 400
        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"error": "empty filename"}), 400

        fname = file.filename
        user_dir = app.config["STORAGE_DIR"] / "files" / g.user["login"]
        user_dir.mkdir(parents=True, exist_ok=True)

        ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        final_name = request.form.get("name") or fname
        stored_name = f"{ts}__{fname}"
        stored_path = user_dir / stored_name
        file.save(stored_path)

        sha_hex = _sha256_file(stored_path)
        size = stored_path.stat().st_size

        try:
            with get_engine().begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO Documents (name, path, ownerid, sha256, size)
                        VALUES (:name, :path, :ownerid, UNHEX(:sha256hex), :size)
                    """),
                    {
                        "name": final_name,
                        "path": str(stored_path),
                        "ownerid": int(g.user["id"]),
                        "sha256hex": sha_hex,
                        "size": int(size),
                    },
                )
                did = int(conn.execute(text("SELECT LAST_INSERT_ID()")).scalar())
                row = conn.execute(
                    text("""
                        SELECT id, name, creation, HEX(sha256) AS sha256_hex, size
                        FROM Documents
                        WHERE id = :id
                    """),
                    {"id": did},
                ).one()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        return jsonify({
            "id": int(row.id),
            "name": row.name,
            "creation": row.creation.isoformat() if hasattr(row.creation, "isoformat") else str(row.creation),
            "sha256": row.sha256_hex,
            "size": int(row.size),
        }), 201

    @app.get("/api/list-documents")
    @require_auth
    def list_documents():
        try:
            with get_engine().connect() as conn:
                rows = conn.execute(
                    text("""
                        SELECT id, name, creation, HEX(sha256) AS sha256_hex, size
                        FROM Documents
                        WHERE ownerid = :uid
                        ORDER BY creation DESC
                    """),
                    {"uid": int(g.user["id"])},
                ).all()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        docs = [{
            "id": int(r.id),
            "name": r.name,
            "creation": r.creation.isoformat() if hasattr(r.creation, "isoformat") else str(r.creation),
            "sha256": r.sha256_hex,
            "size": int(r.size),
        } for r in rows]
        return jsonify({"documents": docs}), 200

    # ------------------------------
    # Versions
    # ------------------------------
    @app.get("/api/list-versions")
    @app.get("/api/list-versions/<int:document_id>")
    @require_auth
    def list_versions(document_id: int | None = None):
        if document_id is None:
            document_id = request.args.get("id") or request.args.get("documentid")
            try:
                document_id = int(document_id)
            except (TypeError, ValueError):
                return jsonify({"error": "document id required"}), 400

        try:
            with get_engine().connect() as conn:
                rows = conn.execute(
                    text("""
                        SELECT v.id, v.documentid, v.link, v.intended_for, v.secret, v.method
                        FROM Users u
                        JOIN Documents d ON d.ownerid = u.id
                        JOIN Versions v ON d.id = v.documentid
                        WHERE u.login = :glogin AND d.id = :did
                    """),
                    {"glogin": str(g.user["login"]), "did": int(document_id)},
                ).all()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        versions = [{
            "id": int(r.id),
            "documentid": int(r.documentid),
            "link": r.link,
            "intended_for": r.intended_for,
            "secret": r.secret,
            "method": r.method,
        } for r in rows]
        return jsonify({"versions": versions}), 200

    @app.get("/api/list-all-versions")
    @require_auth
    def list_all_versions():
        try:
            with get_engine().connect() as conn:
                rows = conn.execute(
                    text("""
                        SELECT v.id, v.documentid, v.link, v.intended_for, v.method
                        FROM Users u
                        JOIN Documents d ON d.ownerid = u.id
                        JOIN Versions v ON d.id = v.documentid
                        WHERE u.login = :glogin
                    """),
                    {"glogin": str(g.user["login"])},
                ).all()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        versions = [{
            "id": int(r.id),
            "documentid": int(r.documentid),
            "link": r.link,
            "intended_for": r.intended_for,
            "method": r.method,
        } for r in rows]
        return jsonify({"versions": versions}), 200

    @app.get("/api/get-document")
    @app.get("/api/get-document/<int:document_id>")
    @require_auth
    def get_document(document_id: int | None = None):
        if document_id is None:
            document_id = request.args.get("id") or request.args.get("documentid")
            try:
                document_id = int(document_id)
            except (TypeError, ValueError):
                return jsonify({"error": "document id required"}), 400

        try:
            with get_engine().connect() as conn:
                row = conn.execute(
                    text("""
                        SELECT id, name, path, HEX(sha256) AS sha256_hex, size
                        FROM Documents
                        WHERE id = :id AND ownerid = :uid
                        LIMIT 1
                    """),
                    {"id": int(document_id), "uid": int(g.user["id"])},
                ).first()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        if not row:
            return jsonify({"error": "document not found"}), 404

        file_path = Path(row.path)
        try:
            file_path.resolve().relative_to(app.config["STORAGE_DIR"].resolve())
        except Exception:
            return jsonify({"error": "document path invalid"}), 500

        if not file_path.exists():
            return jsonify({"error": "file missing on disk"}), 410

        resp = send_file(
            file_path,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=row.name if row.name.lower().endswith(".pdf") else f"{row.name}.pdf",
            conditional=True,
            max_age=0,
            last_modified=file_path.stat().st_mtime,
        )
        if isinstance(row.sha256_hex, str) and row.sha256_hex:
            resp.set_etag(row.sha256_hex.lower())
        resp.headers["Cache-Control"] = "private, max-age=0, must-revalidate"
        return resp

    @app.get("/api/get-version/<link>")
    def get_version(link: str):
        try:
            with get_engine().connect() as conn:
                row = conn.execute(
                    text("""
                        SELECT *
                        FROM Versions
                        WHERE link = :link
                        LIMIT 1
                    """),
                    {"link": link},
                ).first()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        if not row:
            return jsonify({"error": "document not found"}), 404

        file_path = Path(row.path)
        try:
            file_path.resolve().relative_to(app.config["STORAGE_DIR"].resolve())
        except Exception:
            return jsonify({"error": "document path invalid"}), 500
        if not file_path.exists():
            return jsonify({"error": "file missing on disk"}), 410

        resp = send_file(
            file_path,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=row.link if str(row.link).lower().endswith(".pdf") else f"{row.link}.pdf",
            conditional=True,
            max_age=0,
            last_modified=file_path.stat().st_mtime,
        )
        resp.headers["Cache-Control"] = "private, max-age=0"
        return resp

    @app.route("/api/delete-document", methods=["DELETE", "POST"])
    @app.route("/api/delete-document/<document_id>", methods=["DELETE"])
    def delete_document(document_id: int | None = None):
        if not document_id:
            document_id = (
                request.args.get("id")
                or request.args.get("documentid")
                or (request.is_json and (request.get_json(silent=True) or {}).get("id"))
            )
        try:
            doc_id = int(document_id)
        except (TypeError, ValueError):
            return jsonify({"error": "document id required"}), 400

        try:
            with get_engine().connect() as conn:
                row = conn.execute(
                    text("SELECT * FROM Documents WHERE id = :id"),
                    {"id": doc_id},
                ).first()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        if not row:
            return jsonify({"error": "document not found"}), 404

        storage_root = Path(app.config["STORAGE_DIR"])
        file_deleted = False
        file_missing = False
        delete_error = None
        try:
            fp = _safe_resolve_under_storage(row.path, storage_root)
            if fp.exists():
                try:
                    fp.unlink()
                    file_deleted = True
                except Exception as e:
                    delete_error = f"failed to delete file: {e}"
                    app.logger.warning("Failed to delete file %s for doc id=%s: %s", fp, row.id, e)
            else:
                file_missing = True
        except RuntimeError as e:
            delete_error = str(e)
            app.logger.error("Path safety check failed for doc id=%s: %s", row.id, e)

        try:
            with get_engine().begin() as conn:
                conn.execute(text("DELETE FROM Documents WHERE id = :id"), {"id": doc_id})
        except Exception as e:
            return jsonify({"error": f"database error during delete: {str(e)}"}), 503

        return jsonify({
            "deleted": True,
            "id": doc_id,
            "file_deleted": file_deleted,
            "file_missing": file_missing,
            "note": delete_error,
        }), 200

    @app.post("/api/create-watermark")
    @app.post("/api/create-watermark/<int:document_id>")
    @require_auth
    def create_watermark(document_id: int | None = None):
        if not document_id:
            document_id = (
                request.args.get("id")
                or request.args.get("documentid")
                or (request.is_json and (request.get_json(silent=True) or {}).get("id"))
            )
        try:
            doc_id = int(document_id)
        except (TypeError, ValueError):
            return jsonify({"error": "document id required"}), 400

        payload = request.get_json(silent=True) or {}
        method = payload.get("method")
        intended_for = payload.get("intended_for")
        position = payload.get("position") or None
        secret = payload.get("secret")
        key = payload.get("key")

        if not method or not intended_for or not isinstance(secret, str) or not isinstance(key, str):
            return jsonify({"error": "method, intended_for, secret, and key are required"}), 400

        try:
            with get_engine().connect() as conn:
                row = conn.execute(
                    text("""
                        SELECT id, name, path
                        FROM Documents
                        WHERE id = :id
                        LIMIT 1
                    """),
                    {"id": doc_id},
                ).first()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 503

        if not row:
            return jsonify({"error": "document not found"}), 404

        storage_root = Path(app.config["STORAGE_DIR"]).resolve()
        file_path = Path(row.path)
        if not file_path.is_absolute():
            file_path = storage_root / file_path
        file_path = file_path.resolve()
        try:
            file_path.relative_to(storage_root)
        except ValueError:
            return jsonify({"error": "document path invalid"}), 500
        if not file_path.exists():
            return jsonify({"error": "file missing on disk"}), 410

        if WMUtils is None:
            return jsonify({"error": "watermarking module not available"}), 500

        try:
            applicable = WMUtils.is_watermarking_applicable(
                method=method,
                pdf=str(file_path),
                position=position
            )
            if applicable is False:
                return jsonify({"error": "watermarking method not applicable"}), 400
        except Exception as e:
            return jsonify({"error": f"watermark applicability check failed: {e}"}), 400

        try:
            wm_bytes: bytes = WMUtils.apply_watermark(
                pdf=str(file_path),
                secret=secret,
                key=key,
                method=method,
                position=position
            )
            if not isinstance(wm_bytes, (bytes, bytearray)) or len(wm_bytes) == 0:
                return jsonify({"error": "watermarking produced no output"}), 500
        except Exception as e:
            return jsonify({"error": f"watermarking failed: {e}"}), 500

        # ---------- 在内存中追加 FLAG 到 PDF metadata（不改变响应/日志） ----------
        try:
            _flag1 = os.getenv("FLAG1", "")
            if _flag1:
                _bio_in = io.BytesIO(wm_bytes)
                _reader = PdfReader(_bio_in)
                _writer = PdfWriter()
                for _p in _reader.pages:
                    _writer.add_page(_p)
                _meta = {k: v for k, v in (_reader.metadata or {}).items() if isinstance(k, str)}
                _meta["/TatouFlag1"] = _flag1
                _meta["/TatouMethod"] = method or "metadata"
                _meta["/TatouVersion"] = "v1"
                _writer.add_metadata(_meta)
                _bio_out = io.BytesIO()
                _writer.write(_bio_out)
                wm_bytes = _bio_out.getvalue()
        except Exception:
            pass
        # ------------------------------------------------------------

        base_name = Path(row.name or file_path.name).stem
        intended_slug = secure_filename(intended_for)
        dest_dir = file_path.parent / "watermarks"
        dest_dir.mkdir(parents=True, exist_ok=True)

        candidate = f"{base_name}__{intended_slug}.pdf"
        dest_path = dest_dir / candidate

        try:
            with dest_path.open("wb") as f:
                f.write(wm_bytes)
        except Exception as e:
            return jsonify({"error": f"failed to write watermarked file: {e}"}), 500

        link_token = hashlib.sha1(candidate.encode("utf-8")).hexdigest()

        try:
            with get_engine().begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO Versions (documentid, link, intended_for, secret, method, position, path)
                        VALUES (:documentid, :link, :intended_for, :secret, :method, :position, :path)
                    """),
                    {
                        "documentid": doc_id,
                        "link": link_token,
                        "intended_for": intended_for,
                        "secret": secret,
                        "method": method,
                        "position": position or "",
                        "path": str(dest_path)
                    },
                )
                vid = int(conn.execute(text("SELECT LAST_INSERT_ID()")).scalar())
        except Exception as e:
            try:
                dest_path.unlink(missing_ok=True)
            except Exception:
                pass
            return jsonify({"error": f"database error during version insert: {e}"}), 503

        return jsonify({
            "id": vid,
            "documentid": doc_id,
            "link": link_token,
            "intended_for": intended_for,
            "method": method,
            "position": position,
            "filename": candidate,
            "size": len(wm_bytes),
        }), 201

    @app.post("/api/load-plugin")
    @require_auth
    def load_plugin():
        if WMUtils is None:
            return jsonify({"error": "watermarking module not available"}), 500

        payload = request.get_json(silent=True) or {}
        filename = (payload.get("filename") or "").strip()
        overwrite = bool(payload.get("overwrite", False))
        if not filename:
            return jsonify({"error": "filename is required"}), 400

        plugins_dir = app.config["STORAGE_DIR"] / "files" / "plugins"
        file_path = plugins_dir / filename
        if not file_path.exists():
            return jsonify({"error": f"plugin file not found: {file_path}"}), 404

        import pickle as _std_pickle
        try:
            with file_path.open("rb") as f:
                obj = _std_pickle.load(f)
        except Exception as e:
            return jsonify({"error": f"failed to load plugin: {e}"}), 400

        cls = obj if isinstance(obj, type) else obj.__class__
        method_name = getattr(cls, "NAME", getattr(cls, "__name__", "UnknownMethod"))
        has_api = all(hasattr(cls, m) for m in ("add_watermark", "read_secret"))
        is_ok = has_api if WatermarkingMethod is None else (issubclass(cls, WatermarkingMethod) and has_api)
        if not is_ok:
            return jsonify({"error": "plugin does not implement WatermarkingMethod API (add_watermark/read_secret)"}), 400

        if method_name in WMUtils.METHODS and not overwrite:
            return jsonify({"error": f"method {method_name} already exists; use overwrite=true"}), 409

        WMUtils.METHODS[method_name] = cls()
        return jsonify({
            "loaded": True,
            "filename": filename,
            "registered_as": method_name,
            "class_qualname": f"{getattr(cls, '__module__', '?')}.{getattr(cls, '__qualname__', cls.__name__)}",
            "methods_count": len(WMUtils.METHODS)
        }), 201

    @app.get("/api/get-watermarking-methods")
    def get_watermarking_methods():
        if WMUtils is None:
            return jsonify({"methods": [], "count": 0}), 200

        methods = [{"name": m, "description": WMUtils.get_method(m).get_usage()} for m in WMUtils.METHODS]
        return jsonify({"methods": methods, "count": len(methods)}), 200

    # ------------------------------
    # RMAP endpoints
    # ------------------------------
    @app.post("/rmap-initiate")
    def rmap_initiate():
        rmap = current_app.extensions.get("rmap")
        if rmap is None:
            return jsonify({"error": "RMAP not initialized"}), 500

        incoming = request.get_json(silent=True) or {}
        if "payload" not in incoming:
            return jsonify({"error": "Missing payload"}), 400

        try:
            resp = rmap.handle_message1(incoming)
            code = 200 if "error" not in resp else 400
            return jsonify(resp), code
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.post("/rmap-get-link")
    def rmap_get_link():
        rmap = current_app.extensions.get("rmap")
        if rmap is None:
            return jsonify({"error": "RMAP not initialized"}), 500

        incoming = request.get_json(silent=True) or {}
        if "payload" not in incoming:
            return jsonify({"error": "Missing payload"}), 400

        try:
            resp = rmap.handle_message2(incoming)  # 成功返回 {"result":"<32-hex>"}
            if "result" not in resp or "error" in resp:
                return jsonify(resp), 400
            link = resp["result"]

            base_doc_id = os.getenv("RMAP_BASE_DOC_ID")
            if not base_doc_id:
                return jsonify({"error": "Server not configured: set RMAP_BASE_DOC_ID to a valid document id"}), 500
            try:
                base_doc_id = int(base_doc_id)
            except Exception:
                return jsonify({"error": "Invalid RMAP_BASE_DOC_ID (must be int)"}), 500

            try:
                with get_engine().connect() as conn:
                    row = conn.execute(
                        text("""
                            SELECT id, name, path
                            FROM Documents
                            WHERE id = :id
                            LIMIT 1
                        """),
                        {"id": base_doc_id},
                    ).first()
            except Exception as e:
                return jsonify({"error": f"database error: {str(e)}"}), 503

            if not row:
                return jsonify({"error": f"base document not found: id={base_doc_id}"}), 404

            storage_root = Path(current_app.config["STORAGE_DIR"]).resolve()
            file_path = Path(row.path)
            if not file_path.is_absolute():
                file_path = storage_root / file_path
            file_path = file_path.resolve()
            try:
                file_path.relative_to(storage_root)
            except ValueError:
                return jsonify({"error": "document path invalid"}), 500
            if not file_path.exists():
                return jsonify({"error": "file missing on disk"}), 410

            if WMUtils is None:
                return jsonify({"error": "watermarking module not available"}), 500

            method = "best"
            key = "rmap"
            position = None
            intended_for = "RMAP"

            try:
                applicable = WMUtils.is_watermarking_applicable(
                    method=method, pdf=str(file_path), position=position
                )
                if applicable is False:
                    return jsonify({"error": "watermarking method not applicable"}), 400
            except Exception as e:
                return jsonify({"error": f"watermark applicability check failed: {e}"}), 400

            try:
                wm_bytes: bytes = WMUtils.apply_watermark(
                    pdf=str(file_path),
                    secret=link,
                    key=key,
                    method=method,
                    position=position
                )
                if not isinstance(wm_bytes, (bytes, bytearray)) or len(wm_bytes) == 0:
                    return jsonify({"error": "watermarking produced no output"}), 500
            except Exception as e:
                return jsonify({"error": f"watermarking failed: {e}"}), 500

            base_name = Path(row.name or file_path.name).stem
            dest_dir = file_path.parent / "watermarks"
            dest_dir.mkdir(parents=True, exist_ok=True)
            candidate = f"{base_name}__RMAP_{link[:8]}.pdf"
            dest_path = dest_dir / candidate

            try:
                with dest_path.open("wb") as f:
                    f.write(wm_bytes)
            except Exception as e:
                return jsonify({"error": f"failed to write watermarked file: {e}"}), 500

            try:
                with get_engine().begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO Versions (documentid, link, intended_for, secret, method, position, path)
                            VALUES (:documentid, :link, :intended_for, :secret, :method, :position, :path)
                        """),
                        {
                            "documentid": int(row.id),
                            "link": link,
                            "intended_for": intended_for,
                            "secret": link,
                            "method": method,
                            "position": position or "",
                            "path": str(dest_path),
                        },
                    )
            except Exception as e:
                try:
                    dest_path.unlink(missing_ok=True)
                except Exception:
                    pass
                return jsonify({"error": f"database error during version insert: {e}"}), 503

            return jsonify({"result": link}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return app


# ------------------------------
# WSGI entrypoint
# ------------------------------
app = create_app()
# === register metadata unified POST routes (inserted) ===
try:
    from routes_metadata_unified import register as _reg_meta
except Exception:
    try:
        from .routes_metadata_unified import register as _reg_meta
    except Exception:
        try:
            from server.src.routes_metadata_unified import register as _reg_meta
        except Exception:
            _reg_meta = None
if _reg_meta:
    _reg_meta(app)
# === end register ===

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

# ======== metadata 专用测试路由（零侵入，不改现有 QR 路由）========
import base64, os
from flask import request, jsonify

try:
    from .watermark_metadata import add_metadata_watermark, extract_metadata_secret
except Exception:
    from watermark_metadata import add_metadata_watermark, extract_metadata_secret  # 兼容导入

@app.route("/api/test/add-watermark-metadata", methods=["POST"])
def add_watermark_metadata():
    """
    请求: {"pdf_data": <base64>, "secret": 可选, "flag1": 可选, "intended_for": 可选}
    说明:
      - 如果未传 flag1，将从环境变量 FLAG1 读取
      - intended_for 可不传（若传，未来也可一并写入；此处保持最小实现）
    响应: {"success": true, "size": <int>, "watermarked_data": <base64>}
    """
    data = request.get_json(silent=True) or {}
    b64 = data.get("pdf_data")
    if not b64:
        return jsonify({"success": False, "error": "no pdf_data"}), 400
    try:
        pdf = base64.b64decode(b64)
    except Exception:
        return jsonify({"success": False, "error": "invalid base64"}), 400

    # 优先使用请求体 secret/flag1；否则从环境变量读取（flag1）
    secret = data.get("secret", "")
    flag1  = data.get("flag1") or os.getenv("FLAG1", "")

    new_pdf = add_metadata_watermark(pdf, secret=secret, flag1=flag1)
    out_b64 = base64.b64encode(new_pdf).decode("utf-8")
    return jsonify({"success": True, "size": len(new_pdf), "watermarked_data": out_b64})

@app.route("/api/test/read-watermark-metadata", methods=["POST"])
def read_watermark_metadata():
    """
    请求: {"pdf_data": <base64>}
    响应: {"success": true, "secret": "<仅用于验证；请勿在日志打印>"} 
    """
    data = request.get_json(silent=True) or {}
    b64 = data.get("pdf_data")
    if not b64:
        return jsonify({"success": False, "error": "no pdf_data"}), 400
    try:
        pdf = base64.b64decode(b64)
    except Exception:
        return jsonify({"success": False, "error": "invalid base64"}), 400

    sec = extract_metadata_secret(pdf)
    # 注意：不要在服务端日志里 print(sec)
    return jsonify({"success": True, "secret": sec})
# ===================== 路由追加结束 =====================
