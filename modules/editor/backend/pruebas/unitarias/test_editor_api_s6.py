# Archivo: modules/editor/backend/pruebas/unitarias/test_editor_api_s6.py
"""Pruebas unitarias y de endpoints HTTP para el modulo Editor (Sprint 6 — S6-03)."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from editor_backend.modulo import registrar
from fastapi import FastAPI
from fastapi.testclient import TestClient

import ide_core.db.connection as db_conn


@contextmanager
def _bd_aislada(tmp_path: Path):
    ruta_orig = db_conn.RUTA_BD
    pool_orig = db_conn._POOL_ACTIVO
    db_conn.RUTA_BD = tmp_path / "test_editor_s6.db"
    db_conn._POOL_ACTIVO = False
    try:
        db_conn.init_pool()
        db_conn.aplicar_esquemas_completos()
        yield
    finally:
        db_conn.RUTA_BD = ruta_orig
        db_conn._POOL_ACTIVO = pool_orig


def test_formato_codigo_cpp():
    app = FastAPI()
    registrar(app)
    with TestClient(app) as client:
        codigo_desordenado = (
            '#include <stdio.h>\nvoid app_main(){\nif(true){\nprintf("hola");\n}\n}'
        )
        r = client.post(
            "/api/v1/editor/formato",
            json={"codigo": codigo_desordenado, "tab_size": 2},
        )
        assert r.status_code == 200
        cuerpo = r.json()
        assert "codigo_formateado" in cuerpo
        assert (
            "  if" in cuerpo["codigo_formateado"]
            or "printf" in cuerpo["codigo_formateado"]
        )


def test_buscar_y_reemplazar_en_archivos(tmp_path: Path):
    carpeta = tmp_path / "proyecto_esp"
    carpeta.mkdir()
    archivo_c = carpeta / "main.c"
    archivo_c.write_text(
        "void app_main(void) {\n  int baud_rate = 9600;\n}\n",
        encoding="utf-8",
    )

    app = FastAPI()
    registrar(app)
    with TestClient(app) as client:
        r_busq = client.post(
            "/api/v1/editor/buscar-archivos",
            json={
                "termino": "baud_rate",
                "directorio": str(carpeta),
                "sensible_mayusculas": True,
                "palabra_completa": True,
            },
        )
        assert r_busq.status_code == 200
        assert r_busq.json()["total_coincidencias"] == 1

        r_reemp = client.post(
            "/api/v1/editor/reemplazar-archivos",
            json={
                "termino": "9600",
                "reemplazo": "115200",
                "directorio": str(carpeta),
                "sensible_mayusculas": False,
            },
        )
        assert r_reemp.status_code == 200
        assert "115200" in archivo_c.read_text(encoding="utf-8")


def test_configuracion_editor_get_y_put(tmp_path: Path):
    with _bd_aislada(tmp_path):
        app = FastAPI()
        registrar(app)
        with TestClient(app) as client:
            r_get = client.get("/api/v1/editor/configuracion")
            assert r_get.status_code == 200

            r_put = client.put(
                "/api/v1/editor/configuracion",
                json={"tamanio_fuente": 15, "tamanio_tabulacion": 4},
            )
            assert r_put.status_code == 200
