"""
补充剩余路由的基础测试（每个路由3-4个测试用例）

覆盖的路由：
- /api/health
- /api/get-watermarking-methods  
- /api/list-versions/<doc_id>
- /api/list-all-versions
- /debug-db
"""
import pytest
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.src import server as srv


class FakeCursor:
    """模拟数据库游标"""
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

        # SELECT * FROM DOCUMENTS WHERE ID= AND OWNER_ID=
        if "SELECT * FROM DOCUMENTS WHERE ID=" in sql_u and "AND OWNER_ID=" in sql_u:
            doc_id, owner_id = params[0], params[1]
            row = next((d for d in self.store["docs"] if d["id"] == doc_id and d["owner_id"] == owner_id), None)
            self._rows = [row] if row else []
            return

        # SELECT ... FROM VERSIONS WHERE DOC_ID= ORDER BY
        if "FROM VERSIONS WHERE DOC_ID=" in sql_u:
            doc_id = params[0]
            rows = [v for v in self.store["versions"] if v.get("doc_id") == doc_id]
            self._rows = rows
            return

        # SELECT ... FROM VERSIONS WHERE OWNER_ID= ORDER BY
        if "FROM VERSIONS WHERE OWNER_ID=" in sql_u:
            owner_id = params[0]
            rows = [v for v in self.store["versions"] if v.get("owner_id") == owner_id]
            self._rows = rows
            return
        
        # SELECT DATABASE() AS DB
        if "SELECT DATABASE() AS DB" in sql_u:
            self._rows = [{"db": "tatou", "host": "localhost", "port": 3306}]
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
def fake_db_with_versions(monkeypatch):
    """伪造数据库，包含文档和版本"""
    store = {
        "users": [{"id": 1, "login": "testuser", "email": "test@example.com"}],
        "docs": [
            {"id": 1, "name": "doc1.pdf", "path": "/tmp/doc1.pdf", "owner_id": 1},
            {"id": 2, "name": "doc2.pdf", "path": "/tmp/doc2.pdf", "owner_id": 1},
        ],
        "versions": [
            {
                "id": 1,
                "doc_id": 1,
                "owner_id": 1,
                "link": "link1",
                "method": "attachment",
                "intended_for": "",
                "secret": "secret1",
                "creation": "2024-01-01T00:00:00"
            },
            {
                "id": 2,
                "doc_id": 1,
                "owner_id": 1,
                "link": "link2",
                "method": "metadata",
                "intended_for": "",
                "secret": "secret2",
                "creation": "2024-01-02T00:00:00"
            },
            {
                "id": 3,
                "doc_id": 2,
                "owner_id": 1,
                "link": "link3",
                "method": "qr",
                "intended_for": "user@example.com",
                "secret": "secret3",
                "creation": "2024-01-03T00:00:00"
            }
        ]
    }
    monkeypatch.setattr(srv, "get_db", lambda: FakeConn(store))
    return store


# ==================== /api/health ====================
class TestApiHealth:
    """测试 /api/health 路由"""
    
    def test_health_success(self):
        """✅ 测试健康检查成功"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
    
    def test_health_wrong_method(self):
        """❌ 测试错误的HTTP方法"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/health")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_health_returns_json(self):
        """✅ 验证返回JSON格式"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/api/health")
        assert response.content_type == "application/json"


# ==================== /api/get-watermarking-methods ====================
class TestGetWatermarkingMethods:
    """测试 /api/get-watermarking-methods 路由"""
    
    def test_get_methods_success(self):
        """✅ 测试获取水印方法列表"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/api/get-watermarking-methods")
        assert response.status_code == 200
        data = response.get_json()
        
        assert "methods" in data
        assert "count" in data
        assert isinstance(data["methods"], list)
        assert data["count"] >= 0
    
    def test_get_methods_contains_known_methods(self):
        """✅ 验证包含已知的水印方法"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/api/get-watermarking-methods")
        data = response.get_json()
        
        method_names = [m.get("name") for m in data["methods"]]
        # 至少应该有这些方法之一
        known_methods = ["attachment", "metadata", "qr"]
        assert any(m in method_names for m in known_methods)
    
    def test_get_methods_wrong_method(self):
        """❌ 测试错误的HTTP方法"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/api/get-watermarking-methods")
        assert response.status_code == 405


# ==================== /api/list-versions/<doc_id> ====================
class TestListVersions:
    """测试 /api/list-versions/<doc_id> 路由"""
    
    def test_list_versions_success(self, fake_db_with_versions):
        """✅ 测试列出文档版本"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.get(
            "/api/list-versions/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "versions" in data
        assert "count" in data
        assert data["count"] >= 0
        assert isinstance(data["versions"], list)
    
    def test_list_versions_no_auth(self, fake_db_with_versions):
        """❌ 测试未认证"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/api/list-versions/1")
        assert response.status_code == 401
    
    def test_list_versions_nonexistent_doc(self, fake_db_with_versions):
        """❌ 测试不存在的文档"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.get(
            "/api/list-versions/999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_list_versions_wrong_method(self, fake_db_with_versions):
        """❌ 测试错误的HTTP方法"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.post(
            "/api/list-versions/1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 405


# ==================== /api/list-all-versions ====================
class TestListAllVersions:
    """测试 /api/list-all-versions 路由"""
    
    def test_list_all_versions_success(self, fake_db_with_versions):
        """✅ 测试列出所有版本"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.get(
            "/api/list-all-versions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "versions" in data
        assert "count" in data
        assert isinstance(data["versions"], list)
    
    def test_list_all_versions_no_auth(self, fake_db_with_versions):
        """❌ 测试未认证"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/api/list-all-versions")
        assert response.status_code == 401
    
    def test_list_all_versions_includes_doc_id(self, fake_db_with_versions):
        """✅ 验证包含doc_id字段"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        token = "1.token"
        response = client.get(
            "/api/list-all-versions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        data = response.get_json()
        if data["count"] > 0:
            # 验证第一个版本包含doc_id
            assert "doc_id" in data["versions"][0]


# ==================== /debug-db ====================
class TestDebugDB:
    """测试 /debug-db 路由"""
    
    def test_debug_db_success(self, fake_db_with_versions):
        """✅ 测试数据库调试信息"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/debug-db")
        assert response.status_code == 200
        # 返回的是字符串格式的数据库信息
        assert response.data is not None
    
    def test_debug_db_contains_info(self, fake_db_with_versions):
        """✅ 验证包含数据库信息"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.get("/debug-db")
        data = response.get_data(as_text=True)
        # 应该包含数据库相关信息
        assert len(data) > 0
    
    def test_debug_db_wrong_method(self, fake_db_with_versions):
        """❌ 测试错误的HTTP方法"""
        srv.app.testing = True
        client = srv.app.test_client()
        
        response = client.post("/debug-db")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


