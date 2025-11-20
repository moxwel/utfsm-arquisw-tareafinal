# tests/v1/test_channels.py
import time

from fastapi.testclient import TestClient

from app.schemas.channels import Channel
from app.schemas.responses import ChannelBasicInfoResponse
from app.controllers import channels as channels_controller


# --------- Helpers para armar objetos falsos (Pydantic) --------- #

def make_fake_channel(
    channel_id: str = "fake-channel-id",
    name: str = "general",
    owner_id: str = "owner-123",
    is_active: bool = True,
    channel_type: str = "public",
) -> Channel:
    now = time.time()
    data = {
        "id": channel_id,
        "_id": channel_id,
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

    async def fake_create_channel(payload):
        return fake_channel

    monkeypatch.setattr(channels_controller, "create_channel", fake_create_channel)

    body = {
        "name": "general",
        "owner_id": "owner-123",
        "channel_type": "public",
    }

    response = client.post("/v1/channels/", json=body)
    assert response.status_code == 201

    data = response.json()
    assert "_id" in data
    assert data["_id"] == fake_channel.id
    assert data["name"] == "general"
    assert data["owner_id"] == "owner-123"


def test_create_channel_validation_error(client: TestClient):
    body = {
        "name": "general",
        "channel_type": "public",
    }

    response = client.post("/v1/channels/", json=body)
    assert response.status_code == 422


# -------------------- GET /v1/channels/ -------------------- #

def test_list_channels_success(client: TestClient, monkeypatch):
    def fake_list_channels(page: int, page_size: int):
        return [
            make_fake_basic_info(channel_id="1", name="general"),
            make_fake_basic_info(channel_id="2", name="random"),
        ]

    monkeypatch.setattr(
        channels_controller,
        "list_channels",
        fake_list_channels,
    )

    response = client.get("/v1/channels/?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert {c["id"] for c in data} == {"1", "2"}


def test_list_channels_invalid_page_size(client: TestClient):
    response = client.get("/v1/channels/?page=1&page_size=1000")
    assert response.status_code == 422


# -------------------- GET /v1/channels/{channel_id} -------------------- #

def test_get_channel_by_id_success(client: TestClient, monkeypatch):
    fake_channel = make_fake_channel(channel_id="abc123")

    def fake_get_channel(channel_id: str):
        assert channel_id == "abc123"
        return fake_channel

    monkeypatch.setattr(channels_controller, "get_channel", fake_get_channel)

    response = client.get("/v1/channels/abc123")
    assert response.status_code == 200

    data = response.json()
    assert data["_id"] == "abc123"
    assert data["name"] == "general"
    assert data["owner_id"] == "owner-123"


def test_get_channel_by_id_not_found(client: TestClient, monkeypatch):
    def fake_get_channel(channel_id: str):
        return None

    monkeypatch.setattr(channels_controller, "get_channel", fake_get_channel)

    response = client.get("/v1/channels/non-existent")
    assert response.status_code == 404


# -------------------- PUT /v1/channels/{channel_id} -------------------- #

def test_update_channel_success(client: TestClient, monkeypatch):
    async def fake_update_channel(channel_id: str, update_data):
        return make_fake_channel(channel_id=channel_id, name="nuevo-nombre")

    monkeypatch.setattr(channels_controller, "update_channel", fake_update_channel)

    body = {"name": "nuevo-nombre"}

    response = client.put("/v1/channels/abc123", json=body)
    assert response.status_code == 200

    data = response.json()
    assert data["_id"] == "abc123"
    assert data["name"] == "nuevo-nombre"


def test_update_channel_not_found(client: TestClient, monkeypatch):
    async def fake_update_channel(channel_id: str, update_data):
        return None

    monkeypatch.setattr(channels_controller, "update_channel", fake_update_channel)

    response = client.put("/v1/channels/no-existe", json={"name": "x"})
    assert response.status_code == 404


# -------------------- DELETE /v1/channels/{channel_id} -------------------- #

def test_deactivate_channel_success(client: TestClient, monkeypatch):
    active_channel = make_fake_channel(is_active=True)
    inactive_channel = make_fake_channel(channel_id="abc123", is_active=False)

    async def fake_delete_channel(channel_id: str):
        return active_channel, inactive_channel

    monkeypatch.setattr(channels_controller, "delete_channel", fake_delete_channel)

    response = client.delete("/v1/channels/abc123")
    assert response.status_code in (200, 204)

    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert data["id"] == "abc123"


def test_deactivate_channel_already_inactive(client: TestClient, monkeypatch):
    inactive_channel = make_fake_channel(is_active=False)

    async def fake_delete_channel(channel_id: str):
        return inactive_channel, None

    monkeypatch.setattr(channels_controller, "delete_channel", fake_delete_channel)

    response = client.delete("/v1/channels/abc123")
    assert response.status_code == 409


# -------------------- POST /v1/channels/{channel_id}/reactivate -------------------- #

def test_reactivate_channel_success(client: TestClient, monkeypatch):
    active_channel = make_fake_channel(channel_id="abc123", is_active=True)

    async def fake_reactivate_channel(channel_id: str):
        return active_channel, False

    monkeypatch.setattr(channels_controller, "reactivate_channel", fake_reactivate_channel)

    response = client.post("/v1/channels/abc123/reactivate")
    assert response.status_code in (200, 201)

    data = response.json()
    assert "id" in data
    assert data["id"] == "abc123"


def test_reactivate_channel_already_active(client: TestClient, monkeypatch):
    active_channel = make_fake_channel(is_active=True)

    async def fake_reactivate_channel(channel_id: str):
        return active_channel, True

    monkeypatch.setattr(channels_controller, "reactivate_channel", fake_reactivate_channel)

    response = client.post("/v1/channels/abc123/reactivate")
    assert response.status_code == 409


# -------------------- GET /v1/channels/{channel_id}/basic -------------------- #

def test_get_basic_channel_info_success(client: TestClient, monkeypatch):
    fake_basic = make_fake_basic_info(channel_id="abc123", name="general")

    def fake_get_channel_basic_info(channel_id: str):
        return fake_basic

    monkeypatch.setattr(
        channels_controller,
        "get_channel_basic_info",
        fake_get_channel_basic_info,
    )

    response = client.get("/v1/channels/abc123/basic")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "abc123"
    assert data["name"] == "general"


def test_get_basic_channel_info_not_found(client: TestClient, monkeypatch):
    def fake_get_channel_basic_info(channel_id: str):
        return None

    monkeypatch.setattr(
        channels_controller,
        "get_channel_basic_info",
        fake_get_channel_basic_info,
    )

    response = client.get("/v1/channels/no-existe/basic")
    assert response.status_code == 404
