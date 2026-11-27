"""Pruebas unitarias del modulo Menu-Log."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from menu_log_backend.modulo import (
    NOMBRE_MODULO,
    VERSION_MODULO,
    get_logs,
    publish,
    registrar,
)


def test_identidad_modulo():
    assert NOMBRE_MODULO == "menu-log"
    assert VERSION_MODULO == "1.0.0"


def test_publish_y_get_logs():
    evento = publish("Mensaje de prueba menu-log", "INFO", "test")
    assert evento["message"] == "Mensaje de prueba menu-log"
    assert evento["level"] == "INFO"
    logs = get_logs(after_id=0)
    assert len(logs["messages"]) > 0


def test_endpoints_http_menu_log():
    app = FastAPI()
    registrar(app)
    with TestClient(app) as client:
        r_post = client.post(
            "/api/v1/menu-log/logs",
            json={"level": "WARNING", "message": "Aviso menu-log", "source": "ide"},
        )
        assert r_post.status_code == 200
        r_get = client.get("/api/v1/menu-log/logs")
        assert r_get.status_code == 200
        assert any(m["message"] == "Aviso menu-log" for m in r_get.json()["messages"])
