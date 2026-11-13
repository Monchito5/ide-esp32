"""Pruebas unitarias del modulo Editor (Equipo Rojo)."""

from editor_backend.controllers.config_controller import (
    actualizar_configuracion,
    obtener_configuracion,
)
from editor_backend.controllers.format_controller import formatear_codigo_cpp
from editor_backend.controllers.search_controller import buscar_en_archivos
from editor_backend.models import ConfiguracionEditor
from editor_backend.modulo import NOMBRE_MODULO, VERSION_MODULO, registrar
from editor_backend.routes import router


def test_modulo_identificado():
    assert NOMBRE_MODULO == "editor"
    assert VERSION_MODULO == "1.0.0"


def test_models_configuracion():
    cfg = ConfiguracionEditor(tamanio_fuente=16, tamanio_tabulacion=4)
    d = cfg.a_dict()
    assert d["tamanio_fuente"] == 16
    assert d["tamanio_tabulacion"] == 4
    assert d["usar_espacios"] is True


def test_formatear_codigo_cpp_basico():
    codigo_desordenado = "void setup(){\nSerial.begin(115200);\n}"
    resultado = formatear_codigo_cpp(codigo_desordenado, tab_size=2)
    assert resultado["exitoso"] is True
    assert "  Serial.begin(115200);" in resultado["codigo_formateado"]


def test_controlador_configuracion():
    cfg = obtener_configuracion()
    assert "tamanio_fuente" in cfg

    actualizado = actualizar_configuracion({"tamanio_fuente": 18, "tema_editor": "dracula"})
    assert actualizado["exitoso"] is True
    assert actualizado["configuracion"]["tamanio_fuente"] == 18
    assert actualizado["configuracion"]["tema_editor"] == "dracula"


def test_rutas_editor():
    assert router is not None
    rutas = [r.path for r in router.routes]
    assert "/api/v1/editor/formato" in rutas
    assert "/api/v1/editor/buscar-archivos" in rutas
    assert "/api/v1/editor/reemplazar-archivos" in rutas
    assert "/api/v1/editor/configuracion" in rutas
