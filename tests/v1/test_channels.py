# tests/v1/test_channels.py
import time

from fastapi.testclient import TestClient

from app.schemas.channels import Channel
from app.schemas.responses import ChannelBasicInfoResponse
from app.routers.v1 import channels as channels_router


# --------- Helpers para armar objetos falsos (Pydantic) --------- #

def make_fake_channel(
    channel_id: str = "fake-channel-id",
    name: str = "general",
    owner_id: str = "owner-123",
    is_active: bool = True,
    channel_type: str = "public",
) -> Channel:
    """Construye un Channel Pydantic para usar en mocks."""
    now = time.time()
    data = {
        "id": channel_id,
        "_id": channel_id,  # alias de Mongo si lo usas
        "name": name,
        "owner_id": owner_id,
        "users": [],
        "is_active": is_active,
        "channel_type": channel_type,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    return Channel.model_validate(data)


def make_fake_basic_info(
    channel_id: str = "fake-channel-id",
    name: str = "general",
    owner_id: str = "owner-123",
    channel_type: str = "public",
    user_count: int = 0,
) -> ChannelBasicInfoResponse:
    """Construye un ChannelBasicInfoResponse para listar canales."""
    now = time.time()
    data = {
        "id": channel_id,
        "name": name,
        "owner_id": owner_id,
        "channel_type": channel_type,
        "created_at": now,
        "user_count": user_count,
    }
    return ChannelBasicInfoResponse.model_validate(data)


# -------------------- POST /v1/channels/ -------------------- #

def test_create_channel_success(client: TestClient, monkeypatch):
    fake_channel = make_fake_channel()

    def fake_db_create_channel(payload):
        return fake_channel

    monkeypatch.setattr(channels_router, "db_create_channel", fake_db_create_channel)

    body = {
        "name": "general",
        "owner_id": "owner-123",
        "channel_type": "public",
    }

    response = client.post("/v1/channels/", json=body)

    # Puede ser 200 o 201, según definiste el endpoint
    assert response.status_code in (200, 201)

    data = response.json()
    # Lo usual es que se devuelva algo con "id"
    assert "id" in data
    assert data["id"] == fake_channel.id


def test_create_channel_validation_error(client: TestClient):
    """
    Segundo test del POST:
    si falta un campo requerido, FastAPI debería responder 422.
    """
    # Falta owner_id
    body = {
        "name": "general",
        "channel_type": "public",
    }

    response = client.post("/v1/channels/", json=body)
    assert response.status_code == 422


# -------------------- GET /v1/channels/ -------------------- #

def test_list_channels_success(client: TestClient, monkeypatch):
    def fake_db_get_all_channels_paginated(skip: int, limit: int):
        return [
            make_fake_basic_info(channel_id="1", name="general"),
            make_fake_basic_info(channel_id="2", name="random"),
        ]

    monkeypatch.setattr(
        channels_router,
        "db_get_all_channels_paginated",
        fake_db_get_all_channels_paginated,
    )

    response = client.get("/v1/channels/?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {c["id"] for c in data} == {"1", "2"}


def test_list_channels_invalid_page_size(client: TestClient):
    """
    Segundo test del GET /v1/channels/:
    page_size demasiado grande -> 422 según tu validación.
    """
    response = client.get("/v1/channels/?page=1&page_size=1000")
    assert response.status_code == 422


# -------------------- GET /v1/channels/{channel_id} -------------------- #

def test_get_channel_by_id_success(client: TestClient, monkeypatch):
    fake_channel = make_fake_channel(channel_id="abc123")

    def fake_db_get_channel_by_id(channel_id: str):
        assert channel_id == "abc123"
        return fake_channel

    monkeypatch.setattr(channels_router, "db_get_channel_by_id", fake_db_get_channel_by_id)

    response = client.get("/v1/channels/abc123")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "abc123"
    assert data["name"] == "general"
    assert data["owner_id"] == "owner-123"


def test_get_channel_by_id_not_found(client: TestClient, monkeypatch):
    def fake_db_get_channel_by_id(channel_id: str):
        return None

    monkeypatch.setattr(channels_router, "db_get_channel_by_id", fake_db_get_channel_by_id)

    response = client.get("/v1/channels/non-existent")
    assert response.status_code == 404


# -------------------- PUT /v1/channels/{channel_id} -------------------- #

def test_update_channel_success(client: TestClient, monkeypatch):
    def fake_db_update_channel(channel_id: str, update_data):
        # Devolvemos un canal con el nombre actualizado
        return make_fake_channel(channel_id=channel_id, name="nuevo-nombre")

    monkeypatch.setattr(channels_router, "db_update_channel", fake_db_update_channel)

    body = {"name": "nuevo-nombre"}

    response = client.put("/v1/channels/abc123", json=body)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "abc123"
    assert data["name"] == "nuevo-nombre"


def test_update_channel_not_found(client: TestClient, monkeypatch):
    def fake_db_update_channel(channel_id: str, update_data):
        return None

    monkeypatch.setattr(channels_router, "db_update_channel", fake_db_update_channel)

    response = client.put("/v1/channels/no-existe", json={"name": "x"})
    assert response.status_code == 404


# -------------------- DELETE /v1/channels/{channel_id} -------------------- #

def test_deactivate_channel_success(client: TestClient, monkeypatch):
    """
    Caso: canal existe y está activo -> se desactiva correctamente.
    """
    active_channel = make_fake_channel(is_active=True)

    def fake_db_get_channel_by_id(channel_id: str):
        return active_channel

    def fake_db_deactivate_channel(channel_id: str):
        return make_fake_channel(channel_id=channel_id, is_active=False)

    monkeypatch.setattr(channels_router, "db_get_channel_by_id", fake_db_get_channel_by_id)
    monkeypatch.setattr(channels_router, "db_deactivate_channel", fake_db_deactivate_channel)

    response = client.delete("/v1/channels/abc123")
    # Puede ser 200 o 204 según tu implementación
    assert response.status_code in (200, 204)

    if response.status_code == 200:
        data = response.json()
        assert data["id"] == "abc123"


def test_deactivate_channel_already_inactive(client: TestClient, monkeypatch):
    """
    Segundo test: canal ya inactivo -> 409 (conflicto).
    """
    inactive_channel = make_fake_channel(is_active=False)

    def fake_db_get_channel_by_id(channel_id: str):
        return inactive_channel

    monkeypatch.setattr(channels_router, "db_get_channel_by_id", fake_db_get_channel_by_id)

    response = client.delete("/v1/channels/abc123")
    assert response.status_code == 409


# -------------------- POST /v1/channels/{channel_id}/reactivate -------------------- #

def test_reactivate_channel_success(client: TestClient, monkeypatch):
    inactive_channel = make_fake_channel(is_active=False)

    def fake_db_get_channel_by_id(channel_id: str):
        return inactive_channel

    def fake_db_reactivate_channel(channel_id: str):
        return make_fake_channel(channel_id=channel_id, is_active=True)

    monkeypatch.setattr(channels_router, "db_get_channel_by_id", fake_db_get_channel_by_id)
    monkeypatch.setattr(channels_router, "db_reactivate_channel", fake_db_reactivate_channel)

    response = client.post("/v1/channels/abc123/reactivate")
    assert response.status_code in (200, 201)

    data = response.json()
    assert data["id"] == "abc123"


def test_reactivate_channel_already_active(client: TestClient, monkeypatch):
    active_channel = make_fake_channel(is_active=True)

    def fake_db_get_channel_by_id(channel_id: str):
        return active_channel

    monkeypatch.setattr(channels_router, "db_get_channel_by_id", fake_db_get_channel_by_id)

    response = client.post("/v1/channels/abc123/reactivate")
    assert response.status_code == 409


# -------------------- GET /v1/channels/{channel_id}/basic -------------------- #

def test_get_basic_channel_info_success(client: TestClient, monkeypatch):
    fake_basic = make_fake_basic_info(channel_id="abc123", name="general")

    def fake_db_get_basic_channel_info(channel_id: str):
        return fake_basic

    monkeypatch.setattr(
        channels_router,
        "db_get_basic_channel_info",
        fake_db_get_basic_channel_info,
    )

    response = client.get("/v1/channels/abc123/basic")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "abc123"
    assert data["name"] == "general"


def test_get_basic_channel_info_not_found(client: TestClient, monkeypatch):
    def fake_db_get_basic_channel_info(channel_id: str):
        return None

    monkeypatch.setattr(
        channels_router,
        "db_get_basic_channel_info",
        fake_db_get_basic_channel_info,
    )

    response = client.get("/v1/channels/no-existe/basic")
    assert response.status_code == 404
