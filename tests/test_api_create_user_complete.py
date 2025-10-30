"""
/api/create-user 路由的完整测试

测试所有成功和错误情况，不只是"触发第一个错误"。
目标：完整覆盖用户创建功能的所有代码路径。
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.src import server as srv


class FakeCursor:
    """模拟数据库游标"""
    def __init__(self, store):
        self.store = store
        self.lastrowid = 0
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        sql_u = " ".join(sql.split()).upper()
        params = params or ()

        if sql_u.startswith("INSERT INTO USERS"):
            # 检查是否重复
            login = params[0] if len(params) > 0 else ""
            email = params[1] if len(params) > 1 else ""
            
            for u in self.store["users"]:
                if u.get("login") == login or u.get("email") == email:
                    import pymysql
                    raise pymysql.err.IntegrityError("Duplicate entry")
            
            self.lastrowid = len(self.store["users"]) + 1
            self.store["users"].append({
                "id": self.lastrowid,
                "login": login,
                "email": email,
                "hpassword": params[2] if len(params) > 2 else ""
            })
            return

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    def __init__(self, store):
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)

    def commit(self):
        return None


@pytest.fixture()
def fake_db(monkeypatch):
    """伪造数据库"""
    store = {"users": [], "docs": [], "versions": []}
    monkeypatch.setattr(srv, "get_db", lambda: FakeConn(store))
    return store


class TestCreateUserSuccess:
    """测试成功创建用户"""
    
    def test_create_user_basic_success(self, fake_db):
        """✅ 测试基本成功情况"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/create-user", json={
            "login": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # 验证返回数据
        assert "id" in data
        assert data["login"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data  # 不应该返回密码
        
        # 验证数据库
        assert len(fake_db["users"]) == 1
        assert fake_db["users"][0]["login"] == "testuser"
        assert fake_db["users"][0]["email"] == "test@example.com"


class TestCreateUserErrors:
    """测试错误情况"""
    
    def test_create_user_missing_fields(self, fake_db):
        """❌ 测试缺少必需字段"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/create-user", json={
            "email": "test@example.com"
            # 缺少login和password
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


    
    def test_create_user_duplicate(self, fake_db):
        """❌ 测试重复用户"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        # 第一次创建
        response1 = client.post("/api/create-user", json={
            "login": "duplicate",
            "email": "dup@example.com",
            "password": "pass123"
        })
        assert response1.status_code == 201
        
        # 第二次创建（重复）
        response2 = client.post("/api/create-user", json={
            "login": "duplicate",
            "email": "dup@example.com",
            "password": "pass456"
        })
        
        assert response2.status_code == 409
        data = response2.get_json()
        assert "error" in data


class TestSecurityUtils:
    """测试 security_utils 模块的所有功能"""
    
    def test_sanitize_string_basic(self):
        """✅ 测试基本字符串清理"""
        from server.src.security_utils import sanitize_string
        
        result = sanitize_string("<script>alert('xss')</script>", allow_html=False)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_string_max_length(self):
        """✅ 测试字符串长度限制"""
        from server.src.security_utils import sanitize_string
        
        long_string = "a" * 1000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_non_string(self):
        """✅ 测试非字符串输入"""
        from server.src.security_utils import sanitize_string
        
        result = sanitize_string(12345)
        assert result == ""
    
    def test_sanitize_string_allow_html(self):
        """✅ 测试允许HTML"""
        from server.src.security_utils import sanitize_string
        
        html_input = "<b>bold</b>"
        result = sanitize_string(html_input, allow_html=True)
        assert result == html_input
    
    def test_validate_username_success(self):
        """✅ 测试有效用户名"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("test_user-123")
        assert valid is True
        assert error is None
    
    def test_validate_username_too_short(self):
        """❌ 测试用户名太短"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("ab")
        assert valid is False
        assert "at least 3 characters" in error
    
    def test_validate_username_too_long(self):
        """❌ 测试用户名太长"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("a" * 51)
        assert valid is False
        assert "at most 50 characters" in error
    
    def test_validate_username_xss_attack(self):
        """❌ 测试XSS攻击"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("<script>alert('xss')</script>")
        assert valid is False
        assert "invalid characters" in error.lower()
    
    def test_validate_username_path_traversal(self):
        """❌ 测试路径遍历"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("../../etc/passwd")
        assert valid is False
        assert "invalid characters" in error.lower()
    
    def test_validate_username_javascript(self):
        """❌ 测试JavaScript注入"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("javascript:alert(1)")
        assert valid is False
    
    def test_validate_username_empty(self):
        """❌ 测试空用户名"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("")
        assert valid is False
        assert "required" in error.lower()
    
    def test_validate_username_special_chars(self):
        """❌ 测试特殊字符"""
        from server.src.security_utils import validate_username
        
        valid, error = validate_username("user@example.com")
        assert valid is False
        assert "can only contain" in error.lower()
    
    def test_validate_email_success(self):
        """✅ 测试有效邮箱"""
        from server.src.security_utils import validate_email
        
        valid, error = validate_email("test@example.com")
        assert valid is True
        assert error is None
    
    def test_validate_email_invalid_format(self):
        """❌ 测试无效邮箱格式"""
        from server.src.security_utils import validate_email
        
        valid, error = validate_email("notanemail")
        assert valid is False
        assert "format" in error.lower()
    
    def test_validate_email_too_short(self):
        """❌ 测试邮箱太短"""
        from server.src.security_utils import validate_email
        
        valid, error = validate_email("a@b")
        assert valid is False
        assert "length" in error.lower()
    
    def test_validate_email_too_long(self):
        """❌ 测试邮箱太长"""
        from server.src.security_utils import validate_email
        
        long_email = "a" * 250 + "@example.com"
        valid, error = validate_email(long_email)
        assert valid is False
        assert "length" in error.lower()
    
    def test_validate_email_xss(self):
        """❌ 测试邮箱XSS"""
        from server.src.security_utils import validate_email
        
        valid, error = validate_email("<script>@example.com")
        assert valid is False
    
    def test_validate_email_empty(self):
        """❌ 测试空邮箱"""
        from server.src.security_utils import validate_email
        
        valid, error = validate_email("")
        assert valid is False
        assert "required" in error.lower()
    
    def test_validate_identity_success(self):
        """✅ 测试有效身份"""
        from server.src.security_utils import validate_identity
        
        valid, error = validate_identity("GROUP_18")
        assert valid is True
        assert error is None
    
    def test_validate_identity_path_traversal(self):
        """❌ 测试路径遍历"""
        from server.src.security_utils import validate_identity
        
        valid, error = validate_identity("../etc/passwd")
        assert valid is False
        assert "format" in error.lower()
    
    def test_validate_identity_xxe(self):
        """❌ 测试XXE攻击"""
        from server.src.security_utils import validate_identity
        
        valid, error = validate_identity("<?xml version='1.0'?>")
        assert valid is False
    
    def test_validate_identity_empty(self):
        """❌ 测试空身份"""
        from server.src.security_utils import validate_identity
        
        valid, error = validate_identity("")
        assert valid is False
        assert "required" in error.lower()
    
    def test_sanitize_error_message_debug_mode(self):
        """✅ 测试调试模式错误消息"""
        from server.src.security_utils import sanitize_error_message
        
        error = ValueError("Detailed error message")
        result = sanitize_error_message(error, debug=True)
        assert "Detailed error message" in result
    
    def test_sanitize_error_message_production_mode(self):
        """✅ 测试生产模式错误消息"""
        from server.src.security_utils import sanitize_error_message
        
        error = ValueError("Detailed error message")
        result = sanitize_error_message(error, debug=False)
        assert "Detailed error message" not in result
        assert "Invalid input" in result
    
    def test_sanitize_error_message_integrity_error(self):
        """✅ 测试IntegrityError映射"""
        from server.src.security_utils import sanitize_error_message
        
        class IntegrityError(Exception):
            pass
        
        error = IntegrityError("Unique constraint failed")
        result = sanitize_error_message(error, debug=False)
        assert "conflict" in result.lower()
    
    def test_sanitize_error_message_unknown_error(self):
        """✅ 测试未知错误类型"""
        from server.src.security_utils import sanitize_error_message
        
        class CustomError(Exception):
            pass
        
        error = CustomError("Custom error")
        result = sanitize_error_message(error, debug=False)
        assert "Internal server error" in result
    
    def test_safe_jsonify_with_sanitization(self):
        """✅ 测试安全JSON响应"""
        from server.src.security_utils import safe_jsonify
        
        srv.app.testing = True
        with srv.app.app_context():
            data = {"message": "<script>alert('xss')</script>"}
            response = safe_jsonify(data, sanitize_output=True)
            assert response.status_code == 200
    
    def test_safe_jsonify_without_sanitization(self):
        """✅ 测试不清理的JSON响应"""
        from server.src.security_utils import safe_jsonify
        
        srv.app.testing = True
        with srv.app.app_context():
            data = {"message": "normal text"}
            response = safe_jsonify(data, sanitize_output=False)
            assert response.status_code == 200
    
    def test_validate_file_upload_success(self, fake_db):
        """✅ 测试有效文件上传"""
        from server.src.security_utils import validate_file_upload
        
        # 创建假文件
        class FakeFile:
            def __init__(self):
                self.filename = "test.pdf"
                self.content = b"%PDF-1.4\n%%EOF"
                self.position = 0
            
            def seek(self, pos, whence=0):
                if whence == 2:  # SEEK_END
                    self.position = len(self.content)
                else:
                    self.position = pos
            
            def tell(self):
                return self.position if self.position <= len(self.content) else len(self.content)
        
        file = FakeFile()
        valid, error = validate_file_upload(file)
        assert valid is True
        assert error is None
    
    def test_validate_file_upload_no_file(self):
        """❌ 测试无文件"""
        from server.src.security_utils import validate_file_upload
        
        valid, error = validate_file_upload(None)
        assert valid is False
        assert "No file" in error
    
    def test_validate_file_upload_wrong_extension(self, fake_db):
        """❌ 测试错误文件类型"""
        from server.src.security_utils import validate_file_upload
        
        class FakeFile:
            filename = "test.txt"
            def seek(self, pos, whence=0):
                pass
            def tell(self):
                return 1000
        
        file = FakeFile()
        valid, error = validate_file_upload(file)
        assert valid is False
        assert "PDF" in error
    
    def test_validate_file_upload_path_traversal(self, fake_db):
        """❌ 测试路径遍历"""
        from server.src.security_utils import validate_file_upload
        
        class FakeFile:
            filename = "../../etc/passwd.pdf"
            def seek(self, pos, whence=0):
                pass
            def tell(self):
                return 1000
        
        file = FakeFile()
        valid, error = validate_file_upload(file)
        assert valid is False
        assert "Invalid filename" in error
    
    def test_validate_file_upload_too_large(self, fake_db):
        """❌ 测试文件过大"""
        from server.src.security_utils import validate_file_upload
        
        class FakeFile:
            filename = "huge.pdf"
            def seek(self, pos, whence=0):
                pass
            def tell(self):
                return 20 * 1024 * 1024  # 20MB
        
        file = FakeFile()
        valid, error = validate_file_upload(file)
        assert valid is False
        assert "too large" in error.lower()
    
    def test_validate_file_upload_empty(self, fake_db):
        """❌ 测试空文件"""
        from server.src.security_utils import validate_file_upload
        
        class FakeFile:
            filename = "empty.pdf"
            def seek(self, pos, whence=0):
                pass
            def tell(self):
                return 0
        
        file = FakeFile()
        valid, error = validate_file_upload(file)
        assert valid is False
        assert "empty" in error.lower()
    
    def test_add_security_headers(self):
        """✅ 测试安全响应头"""
        from server.src.security_utils import add_security_headers
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        with app.app_context():
            response = jsonify({"test": "data"})
            response = add_security_headers(response)
            
            assert 'X-Content-Type-Options' in response.headers
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
            assert 'X-Frame-Options' in response.headers
            assert response.headers['X-Frame-Options'] == 'DENY'
            assert 'X-XSS-Protection' in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

