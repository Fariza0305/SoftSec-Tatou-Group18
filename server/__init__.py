# server/__init__.py
# ✅ 自动导入 server/src/server.py 中定义的 Flask app 实例

from importlib import import_module

_server_module = import_module("server.src.server")
app = getattr(_server_module, "app")

__all__ = ["app"]
