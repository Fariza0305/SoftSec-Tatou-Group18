"""
/api/login 路由测试（精简版）
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.src import server as srv
from werkzeug.security import generate_password_hash


class MockDBHandler:
    def __init__(self, store):
        self.store = store
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        sql_u = " ".join(sql.split()).upper()
        params = params or ()

        if "SELECT * FROM USERS WHERE EMAIL=" in sql_u:
            email = params[0] if params else ""
            row = next((u for u in self.store["users"] if u["email"] == email), None)
            self._rows = [row] if row else []
            return

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    def __init__(self, store):
        self.store = store

    def get_handler(self):
        return MockDBHandler(self.store)

    def commit(self):
        return None


@pytest.fixture()
def fake_db_with_users(monkeypatch):
    store = {
        "users": [
            {
                "id": 1,
                "login": "testuser",
                "email": "test@example.com",
                "hpassword": generate_password_hash("password123", method="pbkdf2:sha256")
            }
        ],
        "docs": [],
        "versions": []
    }
    monkeypatch.setattr(srv, "get_db", lambda: FakeConn(store))
    return store


class TestLogin:
    """测试登录功能"""
    
    def test_login_success(self, fake_db_with_users):
        """✅ 测试成功登录"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data.get("success") is True
        assert "token" in data
        assert "id" in data
    
    def test_login_missing_credentials(self, fake_db_with_users):
        """❌ 测试缺少凭证"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/login", json={
            "email": "test@example.com"
            # 缺少password
        })
        
        assert response.status_code == 400
    
    def test_login_wrong_password(self, fake_db_with_users):
        """❌ 测试错误密码"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
    
    def test_login_nonexistent_user(self, fake_db_with_users):
        """❌ 测试不存在的用户"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
