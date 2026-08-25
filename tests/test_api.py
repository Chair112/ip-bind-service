import time
import pytest
from fastapi.testclient import TestClient
import app.main  # Импортируем модуль целиком
from app.storage import BindingStorage

# Явно получаем экземпляр FastAPI из модуля main
# (Это сработает, если в main.py он называется app и не перекрыт импортами)
fastapi_app = app.main.app

@pytest.fixture
def storage():
    """Создаём свежий storage для каждого теста."""
    return BindingStorage()

@pytest.fixture
def short_ttl_storage():
    """Storage с коротким TTL в 1 секунду"""
    return BindingStorage(ttl_seconds=1)

@pytest.fixture
def client(storage):
    """Тестовый клиент, который использует наш storage."""
    original = app.main.storage
    app.main.storage = storage
    yield TestClient(fastapi_app) 
    app.main.storage = original

@pytest.fixture
def short_client(short_ttl_storage):
    """Клиент с short_ttl_storage — для тестов TTL."""
    original = app.main.storage
    app.main.storage = short_ttl_storage
    yield TestClient(fastapi_app) 
    app.main.storage = original

# ---------- Тесты ----------

def test_returns_ip_direct(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ip"] == "testclient"
    assert data["name"] is None
    assert data["bound"] is False

def test_x_forwarded_for_first_wins(client):
    resp = client.get("/", headers={"X-Forwarded-For": "203.0.113.10, 10.0.0.1"})
    assert resp.json()["ip"] == "203.0.113.10"

def test_forwarded_header_rfc7239(client):
    resp = client.get("/", headers={"Forwarded": "for=198.51.100.17;proto=https"})
    assert resp.json()["ip"] == "198.51.100.17"

def test_forwarded_ipv6(client):
    resp = client.get("/", headers={"Forwarded": 'For="[2001:db8::1]:8080"'})
    assert resp.json()["ip"] == "2001:db8::1"

def test_bind_name_stores_ip(client):
    resp = client.get("/?name=my-laptop")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "my-laptop"
    assert data["bound"] is True
    resp2 = client.get("/bindings/my-laptop")
    assert resp2.status_code == 200
    assert resp2.json()["ip"] == "testclient"

def test_binding_ttl_expires(short_client, short_ttl_storage):
    """Через TTL секунд привязка исчезает."""
    short_ttl_storage.set("host-x", "1.2.3.4")
    assert short_ttl_storage.get("host-x") == "1.2.3.4"
    time.sleep(1.2)
    assert short_ttl_storage.get("host-x") is None
    resp = short_client.get("/bindings/host-x")
    assert resp.status_code == 404

def test_binding_overwrite_refreshes_ttl(short_ttl_storage):
    """Перезапись привязки обновляет время жизни."""
    short_ttl_storage.ttl = 2
    short_ttl_storage.set("h", "1.1.1.1")
    time.sleep(1.0)
    short_ttl_storage.set("h", "2.2.2.2")
    time.sleep(1.2)
    assert short_ttl_storage.get("h") == "2.2.2.2"

def test_cleanup_removes_expired(short_ttl_storage):
    """Фоновая чистка удаляет протухшие записи."""
    short_ttl_storage.set("a", "1.1.1.1")
    short_ttl_storage.set("b", "2.2.2.2")
    time.sleep(1.2)
    removed = short_ttl_storage.cleanup()
    assert removed == 2
    assert short_ttl_storage.get("a") is None