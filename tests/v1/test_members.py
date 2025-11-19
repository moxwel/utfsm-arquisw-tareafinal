# tests/v1/test_members.py
import time

from fastapi.testclient import TestClient

from app.schemas.channels import Channel, ChannelMember
from app.schemas.responses import ChannelBasicInfoResponse
from app.routers.v1 import members as members_router


def make_fake_member(user_id: str, joined_at: float | None = None, status: str = "normal") -> ChannelMember:
    if joined_at is None:
        joined_at = time.time()
    return ChannelMember.model_validate({"id": user_id, "joined_at": joined_at, "status": status})


def make_fake_channel(
    channel_id: str = "fake-channel-id",
    name: str = "general",
    owner_id: str = "owner-123",
    is_active: bool = True,
    channel_type: str = "public",
    users: list[ChannelMember] | None = None,
) -> Channel:
    now = time.time()
    if users is None:
        users = []
    data = {
        "id": channel_id,
        "_id": channel_id,
        "name": name,
        "owner_id": owner_id,
        "users": users,
        "is_active": is_active,
        "channel_type": channel_type,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    return Channel.model_validate(data)


def make_fake_basic_info(
    channel_id: str,
    name: str = "general",
    owner_id: str = "owner-123",
    channel_type: str = "public",
    user_count: int = 1,
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


# -------------------- POST /v1/members/ -------------------- #

def test_add_user_to_channel_success(client: TestClient, monkeypatch):
    member = make_fake_member("user-123")
    fake_channel = make_fake_channel(
        channel_id="chan-1",
        users=[member],
    )

    def fake_db_add_user_to_channel(channel_id: str, user_id: str):
        assert channel_id == "chan-1"
        assert user_id == "user-123"
        return fake_channel

    monkeypatch.setattr(members_router, "db_add_user_to_channel", fake_db_add_user_to_channel)

    body = {"channel_id": "chan-1", "user_id": "user-123"}

    response = client.post("/v1/members/", json=body)
    assert response.status_code == 200

    data = response.json()
    assert data["_id"] == "chan-1"
    assert data["owner_id"] == "owner-123"

def test_add_user_to_channel_not_found_or_already_member(client: TestClient, monkeypatch):
    def fake_db_add_user_to_channel(channel_id: str, user_id: str):
        return None

    monkeypatch.setattr(members_router, "db_add_user_to_channel", fake_db_add_user_to_channel)

    body = {"channel_id": "chan-1", "user_id": "user-123"}
    response = client.post("/v1/members/", json=body)
    assert response.status_code == 404


# -------------------- DELETE /v1/members/ -------------------- #

def test_remove_user_from_channel_success(client: TestClient, monkeypatch):
    member = make_fake_member("user-123")
    fake_channel = make_fake_channel(
        channel_id="chan-1",
        users=[member],
    )

    def fake_db_remove_user_from_channel(channel_id: str, user_id: str):
        assert channel_id == "chan-1"
        assert user_id == "user-123"
        return fake_channel

    monkeypatch.setattr(members_router, "db_remove_user_from_channel", fake_db_remove_user_from_channel)

    body = {"channel_id": "chan-1", "user_id": "user-123"}

    response = client.request("DELETE", "/v1/members/", json=body)
    assert response.status_code in (200, 204)

    if response.status_code == 200:
        data = response.json()
        assert data["_id"] == "chan-1"

def test_remove_user_from_channel_not_found(client: TestClient, monkeypatch):
    def fake_db_remove_user_from_channel(channel_id: str, user_id: str):
        return None

    monkeypatch.setattr(members_router, "db_remove_user_from_channel", fake_db_remove_user_from_channel)

    body = {"channel_id": "chan-1", "user_id": "user-999"}
    response = client.request("DELETE", "/v1/members/", json=body)
    assert response.status_code == 404


# -------------------- GET /v1/members/{user_id} -------------------- #

def test_list_channels_by_member_success(client: TestClient, monkeypatch):
    def fake_db_get_channels_by_member_id(user_id: str):
        assert user_id == "user-123"
        return [
            make_fake_basic_info(channel_id="chan-1"),
            make_fake_basic_info(channel_id="chan-2"),
        ]

    monkeypatch.setattr(
        members_router,
        "db_get_channels_by_member_id",
        fake_db_get_channels_by_member_id,
    )

    response = client.get("/v1/members/user-123")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert {c["id"] for c in data} == {"chan-1", "chan-2"}


def test_list_channels_by_member_empty(client: TestClient, monkeypatch):
    def fake_db_get_channels_by_member_id(user_id: str):
        return []

    monkeypatch.setattr(
        members_router,
        "db_get_channels_by_member_id",
        fake_db_get_channels_by_member_id,
    )

    response = client.get("/v1/members/user-without-channels")
    assert response.status_code == 200
    assert response.json() == []


# -------------------- GET /v1/members/owner/{owner_id} -------------------- #

def test_list_channels_by_owner_success(client: TestClient, monkeypatch):
    def fake_db_get_channels_by_owner_id(owner_id: str):
        assert owner_id == "owner-123"
        return [
            make_fake_basic_info(channel_id="chan-1", owner_id=owner_id),
        ]

    monkeypatch.setattr(
        members_router,
        "db_get_channels_by_owner_id",
        fake_db_get_channels_by_owner_id,
    )

    response = client.get("/v1/members/owner/owner-123")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["owner_id"] == "owner-123"


def test_list_channels_by_owner_empty(client: TestClient, monkeypatch):
    def fake_db_get_channels_by_owner_id(owner_id: str):
        return []

    monkeypatch.setattr(
        members_router,
        "db_get_channels_by_owner_id",
        fake_db_get_channels_by_owner_id,
    )

    response = client.get("/v1/members/owner/no-channels")
    assert response.status_code == 200
    assert response.json() == []


# -------------------- GET /v1/members/channel/{channel_id} -------------------- #

def test_list_members_by_channel_success(client: TestClient, monkeypatch):
    def fake_db_get_channel_member_ids(channel_id: str, skip: int, limit: int):
        assert channel_id == "chan-1"
        return [make_fake_member("user-1"), make_fake_member("user-2")]

    monkeypatch.setattr(
        members_router,
        "db_get_channel_member_ids",
        fake_db_get_channel_member_ids,
    )

    response = client.get("/v1/members/channel/chan-1?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert {m["id"] for m in data} == {"user-1", "user-2"}


def test_list_members_by_channel_invalid_page_size(client: TestClient):
    response = client.get("/v1/members/channel/chan-1?page=1&page_size=1000")
    assert response.status_code == 422


# -------------------- Pruebas de user_count -------------------- #

def test_user_count_reflects_multiple_additions(client: TestClient, monkeypatch):
    """Verifica que múltiples adiciones de usuarios se reflejen en user_count."""
    # Simular añadir usuarios uno por uno y verificar que el conteo aumenta
    
    # Estado 1: 1 usuario (owner)
    members_1 = [make_fake_member("owner-123")]
    channel_1 = make_fake_channel(channel_id="chan-1", users=members_1)
    
    # Estado 2: 2 usuarios
    members_2 = members_1 + [make_fake_member("user-1")]
    channel_2 = make_fake_channel(channel_id="chan-1", users=members_2)
    
    # Estado 3: 3 usuarios
    members_3 = members_2 + [make_fake_member("user-2")]
    channel_3 = make_fake_channel(channel_id="chan-1", users=members_3)
    
    call_count = {"count": 0}
    
    def fake_db_add_user_to_channel(channel_id: str, user_id: str):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return channel_2
        elif call_count["count"] == 2:
            return channel_3
        return None

    monkeypatch.setattr(members_router, "db_add_user_to_channel", fake_db_add_user_to_channel)

    # Primera adición
    body = {"channel_id": "chan-1", "user_id": "user-1"}
    response = client.post("/v1/members/", json=body)
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 2
    
    # Segunda adición
    body = {"channel_id": "chan-1", "user_id": "user-2"}
    response = client.post("/v1/members/", json=body)
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 3
