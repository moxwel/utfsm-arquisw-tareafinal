# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import main as main_module
from app.routers.v1 import channels as channels_router
from app.routers.v1 import members as members_router


@pytest.fixture(autouse=True)
def mock_infrastructure(monkeypatch):
    """
    Este fixture se aplica automáticamente en TODOS los tests.

    - Evita conexiones reales a MongoDB y RabbitMQ en startup/shutdown.
    - Reemplaza publish_message_main por una función dummy.
    """

    # --- MongoEngine (startup/shutdown) ---
    monkeypatch.setattr(main_module, "connect_to_mongo", lambda: None)
    monkeypatch.setattr(main_module, "close_mongo_connection", lambda: None)

    # --- RabbitMQ (startup/shutdown) ---
    async def fake_connect_to_rabbitmq():
        return None

    async def fake_close_rabbitmq_connection():
        return None

    monkeypatch.setattr(main_module, "connect_to_rabbitmq", fake_connect_to_rabbitmq)
    monkeypatch.setattr(main_module, "close_rabbitmq_connection", fake_close_rabbitmq_connection)

    # --- RabbitMQ (publicación de eventos) ---
    async def fake_publish_message_main(*args, **kwargs):
        # Podrías guardar los mensajes aquí si quisieras testearlos.
        return None

    monkeypatch.setattr(channels_router, "publish_message_main", fake_publish_message_main, raising=False)
    monkeypatch.setattr(members_router, "publish_message_main", fake_publish_message_main, raising=False)

    # yield para que pytest pueda hacer teardown si hiciera falta
    yield


@pytest.fixture
def client() -> TestClient:
    """
    Cliente de pruebas para la API, de alcance función (por defecto).
    Cada test que recibe `client` obtiene un TestClient nuevo.
    """
    return TestClient(app)
