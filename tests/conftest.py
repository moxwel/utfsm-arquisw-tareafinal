# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import main as main_module
from app.routers.v1 import channels as channels_router
from app.routers.v1 import members as members_router


@pytest.fixture(autouse=True)
def mock_infrastructure(monkeypatch):
    """Mock de Mongo y RabbitMQ para todos los tests."""
    monkeypatch.setattr(main_module, "connect_to_mongo", lambda: None)
    monkeypatch.setattr(main_module, "close_mongo_connection", lambda: None)

    async def fake_connect_to_rabbitmq():
        return None

    async def fake_close_rabbitmq_connection():
        return None

    monkeypatch.setattr(main_module, "connect_to_rabbitmq_all", fake_connect_to_rabbitmq)
    monkeypatch.setattr(main_module, "close_rabbitmq_connection_all", fake_close_rabbitmq_connection)

    async def fake_publish_message_main(*args, **kwargs):
        return None

    monkeypatch.setattr(channels_router, "publish_message_main", fake_publish_message_main, raising=False)
    monkeypatch.setattr(members_router, "publish_message_main", fake_publish_message_main, raising=False)

    yield


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP de prueba para la app FastAPI."""
    return TestClient(app)
