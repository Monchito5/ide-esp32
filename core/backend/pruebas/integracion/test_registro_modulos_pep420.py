# Archivo: core/backend/pruebas/integracion/test_registro_modulos_pep420.py
"""Prueba de integracion de registro de modulos, health check y convencion PEP 420 (Sprint 6 — S6-07)."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

import ide_core.db.connection as db_conn
from ide_core.config.constants import DIRECTORIO_MONOREPO, MODULOS_REGISTRADOS
from ide_core.config.setup import AppConfig


@contextmanager
def _bd_aislada(tmp_path: Path):
    ruta_orig = db_conn.RUTA_BD
    pool_orig = db_conn._POOL_ACTIVO
    db_conn.RUTA_BD = tmp_path / "test_registro_s6.db"
    db_conn._POOL_ACTIVO = False
    try:
        db_conn.init_pool()
        db_conn.aplicar_esquemas_completos()
        yield
    finally:
        db_conn.RUTA_BD = ruta_orig
        db_conn._POOL_ACTIVO = pool_orig


def test_ausencia_estricta_de_init_py_pep420():
    """Garantiza que ningun paquete del monorepo contenga archivos __init__.py."""
    carpetas_auditadas = ("core", "modules", "apps", "shared", "sql")
    encontrados: list[str] = []
    ignorar = {".git", "venv", ".venv", "build", "dist", ".pytest_cache", "__pycache__"}
    for nombre in carpetas_auditadas:
        raiz = DIRECTORIO_MONOREPO / nombre
        if not raiz.exists():
            continue
        for ruta in raiz.rglob("__init__.py"):
            if not any(parte in ignorar for parte in ruta.parts):
                encontrados.append(str(ruta.relative_to(DIRECTORIO_MONOREPO)))
    assert (
        encontrados == []
    ), f"Violacion PEP 420 (__init__.py detectados): {encontrados}"


def test_todos_los_modulos_se_registran_y_responden_health_check(tmp_path: Path):
    """Verifica que los 6 modulos backend se cargan en FastAPI y exponen sus prefijos."""
    esperados = {
        "herramientas_backend.modulo",
        "archivo_backend.modulo",
        "simulacion_backend.modulo",
        "sketch_backend.modulo",
        "editor_backend.modulo",
        "menu_log_backend.modulo",
    }
    assert esperados.issubset(set(MODULOS_REGISTRADOS))

    with _bd_aislada(tmp_path):
        app = AppConfig.crear_app()
        rutas_montadas = set(app.openapi().get("paths", {}).keys())
        assert "/api/v1/salud" in rutas_montadas
        assert "/api/v1/herramientas/placas-soportadas" in rutas_montadas
        assert "/api/v1/archivo/nuevo" in rutas_montadas
        assert "/api/v1/simulacion/motores" in rutas_montadas
        assert "/api/v1/sketch/compilar-codigo" in rutas_montadas
        assert "/api/v1/editor/formato" in rutas_montadas
        assert "/api/v1/menu-log/logs" in rutas_montadas

        with TestClient(app) as client:
            r_salud = client.get("/api/v1/salud")
            assert r_salud.status_code == 200
            assert r_salud.json()["estado"] == "ok"

            r_mods = client.get("/api/v1/modulos")
            assert r_mods.status_code == 200
            assert "modulos" in r_mods.json()
