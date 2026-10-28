import pytest
from fastapi.testclient import TestClient

from app import api
from cargar_csv import load_fixture


@pytest.fixture(autouse=True)
def datos_frescos():
    """Cada prueba parte de los 16 pedidos recién cargados en DRAFT."""
    api.orders.clear()
    api.orders.update(load_fixture())


@pytest.fixture
def client():
    return TestClient(api.app)


def test_get_pedido_existente(client):
    r = client.get("/orders/O001")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "DRAFT"
    assert body["units"] == 4
    assert body["total"] == "2100.00"
    assert body["discount_rate"] == "0.10"


def test_get_pedido_inexistente_404(client):
    assert client.get("/orders/O999").status_code == 404


def test_confirm_pedido_inexistente_404(client):
    r = client.post("/orders/O999/confirm")
    assert r.status_code == 404


def test_confirm_exitoso_200(client):
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 200
    assert r.json() == {"id": "O013", "status": "CONFIRMED"}


def test_confirm_doble_409(client):
    assert client.post("/orders/O013/confirm").status_code == 200
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 409
    assert client.get("/orders/O013").json()["events"] == ["OrderConfirmed"]


def test_confirm_pedido_vacio_422(client):
    assert client.post("/orders/O007/confirm").status_code == 422


def test_confirm_cliente_inactivo_422(client):
    assert client.post("/orders/O003/confirm").status_code == 422


def test_ship_sin_guia_422(client):
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert r.status_code == 422
    assert client.get("/orders/O012").json()["status"] == "CONFIRMED"


def test_ship_exitoso(client):
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": "G-1"})
    assert r.status_code == 200
    assert r.json()["status"] == "SHIPPED"


def test_ship_desde_draft_409(client):
    r = client.post("/orders/O012/ship", json={"tracking_number": "G-1"})
    assert r.status_code == 409


def test_cancel_desde_shipped_409(client):
    client.post("/orders/O014/confirm")
    client.post("/orders/O014/ship", json={"tracking_number": "G-2"})
    r = client.post("/orders/O014/cancel", json={"reason": "Cliente lo pidió"})
    assert r.status_code == 409
    assert client.get("/orders/O014").json()["status"] == "SHIPPED"


def test_cancel_exitoso(client):
    client.post("/orders/O002/confirm")
    r = client.post("/orders/O002/cancel", json={"reason": "Cliente lo pidió"})
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"


def test_cancel_sin_motivo_422(client):
    client.post("/orders/O002/confirm")
    r = client.post("/orders/O002/cancel", json={"reason": ""})
    assert r.status_code == 422