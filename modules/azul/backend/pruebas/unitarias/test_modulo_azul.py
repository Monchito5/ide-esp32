"""Pruebas unitarias del modulo Azul."""
from azul_backend.modulo import NOMBRE_MODULO, VERSION_MODULO, publish, get_logs


def test_identidad_modulo():
    assert NOMBRE_MODULO == "azul"
    assert VERSION_MODULO == "1.0.0"


def test_publish_y_get_logs():
    evento = publish("Mensaje de prueba", "INFO", "test")
    assert evento["message"] == "Mensaje de prueba"
    assert evento["level"] == "INFO"
    logs = get_logs(after_id=0)
    assert len(logs["messages"]) > 0
