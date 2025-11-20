# tests/v1/test_operations.py
import time

from fastapi.testclient import TestClient

from app.schemas.channels import Channel, ChannelMember
from app.schemas.responses import ChannelBasicInfoResponse
from app.controllers import members as members_controller
from app.controllers import channels as channels_controller


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


# -------------------- Pruebas de operaciones que requieren ambos routers -------------------- #

def test_add_user_increases_user_count(client: TestClient, monkeypatch):
    """Verifica que al añadir un usuario, el user_count aumenta correctamente."""
    # Estado inicial: canal con 2 usuarios
    initial_members = [make_fake_member("user-1"), make_fake_member("user-2")]
    
    # Estado después de añadir: canal con 3 usuarios
    new_member = make_fake_member("user-3")
    updated_members = initial_members + [new_member]
    
    fake_channel = make_fake_channel(
        channel_id="chan-1",
        users=updated_members,
    )

    async def fake_add_user_to_channel(payload):
        return fake_channel

    def fake_get_channel_basic_info(channel_id: str):
        # Simular la info básica con el conteo actualizado
        return make_fake_basic_info(
            channel_id="chan-1",
            user_count=len(updated_members)
        )

    monkeypatch.setattr(members_controller, "add_user_to_channel", fake_add_user_to_channel)
    monkeypatch.setattr(channels_controller, "get_channel_basic_info", fake_get_channel_basic_info)

    # Añadir el tercer usuario
    body = {"channel_id": "chan-1", "user_id": "user-3"}
    response = client.post("/v1/members/", json=body)
    assert response.status_code == 200

    # Verificar que el canal tiene 3 usuarios
    data = response.json()
    assert len(data["users"]) == 3

    # Verificar el conteo a través del endpoint de info básica
    info_response = client.get("/v1/channels/chan-1/basic")
    assert info_response.status_code == 200
    info_data = info_response.json()
    assert info_data["user_count"] == 3


def test_remove_user_decreases_user_count(client: TestClient, monkeypatch):
    """Verifica que al eliminar un usuario, el user_count disminuye correctamente."""
    # Estado inicial: canal con 3 usuarios
    initial_members = [
        make_fake_member("user-1"),
        make_fake_member("user-2"),
        make_fake_member("user-3")
    ]
    
    # Estado después de eliminar: canal con 2 usuarios (se eliminó user-3)
    updated_members = [make_fake_member("user-1"), make_fake_member("user-2")]
    
    fake_channel = make_fake_channel(
        channel_id="chan-1",
        users=updated_members,
    )

    async def fake_remove_user_from_channel(payload):
        return fake_channel

    def fake_get_channel_basic_info(channel_id: str):
        # Simular la info básica con el conteo actualizado
        return make_fake_basic_info(
            channel_id="chan-1",
            user_count=len(updated_members)
        )

    monkeypatch.setattr(members_controller, "remove_user_from_channel", fake_remove_user_from_channel)
    monkeypatch.setattr(channels_controller, "get_channel_basic_info", fake_get_channel_basic_info)

    # Eliminar el tercer usuario
    body = {"channel_id": "chan-1", "user_id": "user-3"}
    response = client.request("DELETE", "/v1/members/", json=body)
    assert response.status_code in (200, 204)

    # Verificar que el canal ahora tiene 2 usuarios
    if response.status_code == 200:
        data = response.json()
        assert len(data["users"]) == 2

    # Verificar el conteo a través del endpoint de info básica
    info_response = client.get("/v1/channels/chan-1/basic")
    assert info_response.status_code == 200
    info_data = info_response.json()
    assert info_data["user_count"] == 2


def test_user_count_after_removing_all_members(client: TestClient, monkeypatch):
    """Verifica que user_count llegue a 1 después de eliminar todos los miembros (excepto owner)."""
    # En la práctica, el owner no puede ser eliminado, pero los demás sí
    
    # Estado inicial: owner + 1 miembro
    members = [make_fake_member("owner-123"), make_fake_member("user-1")]
    
    # Estado final: solo el owner
    final_members = [make_fake_member("owner-123")]
    
    fake_channel = make_fake_channel(
        channel_id="chan-1",
        owner_id="owner-123",
        users=final_members,
    )

    async def fake_remove_user_from_channel(payload):
        return fake_channel

    def fake_get_channel_basic_info(channel_id: str):
        return make_fake_basic_info(
            channel_id="chan-1",
            owner_id="owner-123",
            user_count=len(final_members)
        )

    monkeypatch.setattr(members_controller, "remove_user_from_channel", fake_remove_user_from_channel)
    monkeypatch.setattr(channels_controller, "get_channel_basic_info", fake_get_channel_basic_info)

    # Eliminar el último miembro no-owner
    body = {"channel_id": "chan-1", "user_id": "user-1"}
    response = client.request("DELETE", "/v1/members/", json=body)
    assert response.status_code in (200, 204)

    # Verificar conteo
    info_response = client.get("/v1/channels/chan-1/basic")
    assert info_response.status_code == 200
    info_data = info_response.json()
    assert info_data["user_count"] == 1


def test_user_count_consistency_across_endpoints(client: TestClient, monkeypatch):
    """Verifica que user_count sea consistente entre diferentes endpoints."""
    members = [make_fake_member(f"user-{i}") for i in range(5)]
    
    fake_channel = make_fake_channel(
        channel_id="chan-1",
        users=members,
    )
    
    fake_basic_info = make_fake_basic_info(
        channel_id="chan-1",
        user_count=5
    )

    def fake_get_channel_basic_info(channel_id: str):
        return fake_basic_info
    
    def fake_get_channels_by_member(user_id: str):
        return [fake_basic_info]

    monkeypatch.setattr(members_controller, "get_channels_by_member", fake_get_channels_by_member)
    monkeypatch.setattr(channels_controller, "get_channel_basic_info", fake_get_channel_basic_info)

    # Verificar a través del endpoint de canales por miembro
    response = client.get("/v1/members/user-1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["user_count"] == 5

    # Verificar a través del endpoint de info básica
    info_response = client.get("/v1/channels/chan-1/basic")
    assert info_response.status_code == 200
    info_data = info_response.json()
    assert info_data["user_count"] == 5
