# Archivo: core/backend/pruebas/integracion/test_flujo_completo_e2e.py
"""Prueba de integracion End-to-End de los 7 pasos del IDE ESP32 (Sprint 6 — S6-06)."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import ide_core.db.connection as db_conn
from ide_core.config.setup import AppConfig


@contextmanager
def _bd_e2e_aislada(tmp_path: Path):
    ruta_orig = db_conn.RUTA_BD
    pool_orig = db_conn._POOL_ACTIVO
    db_conn.RUTA_BD = tmp_path / "test_flujo_e2e.db"
    db_conn._POOL_ACTIVO = False
    try:
        db_conn.init_pool()
        db_conn.aplicar_esquemas_completos()
        yield
    finally:
        db_conn.RUTA_BD = ruta_orig
        db_conn._POOL_ACTIVO = pool_orig


def _compilador_espidf_determinista(
    project_path: str, timeout: int = 1800, target: str | None = None
) -> dict:
    """Simula la salida binaria exacta de idf.py build con cabeceras magicas 0xE9 de Espressif."""
    raiz = Path(project_path)
    build = raiz / "build"
    (build / "bootloader").mkdir(parents=True, exist_ok=True)
    (build / "partition_table").mkdir(parents=True, exist_ok=True)

    boot_bin = build / "bootloader" / "bootloader.bin"
    part_bin = build / "partition_table" / "partition-table.bin"
    app_bin = build / "e2e_app.bin"

    boot_bin.write_bytes(b"\xe9\x02\x02\x20" + b"\x11" * 252)
    # Cabecera 0xAA50 valida de 32 bytes para partition table
    entrada_factory = (
        b"\xaa\x50\x00\x00"
        + (0x10000).to_bytes(4, "little")
        + (0x100000).to_bytes(4, "little")
        + b"factory".ljust(16, b"\x00")
        + (0).to_bytes(4, "little")
    )
    part_bin.write_bytes(entrada_factory + b"\xff" * 32)
    app_bin.write_bytes(b"\xe9\x04\x02\x20" + b"\x22" * 508)

    return {
        "success": True,
        "returncode": 0,
        "stdout": f"Project build complete ({target or 'esp32s3'}).",
        "stderr": "",
        "error": None,
        "bin_files": [str(boot_bin), str(part_bin), str(app_bin)],
        "command": ["idf.py", "build"],
    }


def test_flujo_completo_7_pasos_ide_esp32(tmp_path: Path):
    """
    Valida de principio a fin los 7 pasos del flujo integral:
    1. Seleccionar/detectar placa (ESP32-S3 DevKitC-1)
    2. Elegir modo de ejecucion y validar toolchain Espressif
    3. Compilar firmware CMake ESP-IDF -> artefactos .bin con offsets S3 (0x0)
    4. Ejecutar simulacion virtual y cargar binario
    5. Realizar pruebas de flasheo orquestado + verificacion SHA-256
    6. Probar perifericos (GPIO/UART) y Monitor/Plotter Serie en tiempo real
    7. Generar reportes de sesion, flasheo y exportacion CSV de logs
    """
    from herramientas_backend.controllers.monitor_serie import gestor_monitor_global

    with _bd_e2e_aislada(tmp_path):
        app = AppConfig.crear_app()
        gestor_monitor_global.reiniciar_para_pruebas()

        with TestClient(app) as client:
            # Paso 1: Seleccionar placa ESP32-S3 DevKitC-1
            r_placas = client.get("/api/v1/herramientas/placas-soportadas")
            assert r_placas.status_code == 200
            placa_s3 = next(
                p for p in r_placas.json()["placas"] if p["target_idf"] == "esp32s3"
            )
            assert placa_s3["bootloader_offset"] == "0x0"

            # Paso 2: Validar estado del ecosistema y motores disponibles
            r_idf = client.get("/api/v1/herramientas/esp-idf/estado")
            assert r_idf.status_code == 200
            assert r_idf.json()["framework_principal"] == "Espressif ESP-IDF"

            r_motores = client.get("/api/v1/simulacion/motores")
            assert r_motores.status_code == 200

            # Paso 3: Compilar codigo fuente C para ESP-IDF (esp32s3)
            codigo_c = (
                "#include <stdio.h>\n"
                'void app_main(void) { printf("temp:27.5,hum:61.0\\n"); }\n'
            )
            with patch(
                "sketch_backend.controllers.compilacion.compilar_proyecto",
                side_effect=_compilador_espidf_determinista,
            ):
                r_comp = client.post(
                    "/api/v1/sketch/compilar-codigo",
                    json={
                        "codigo": codigo_c,
                        "nombre_archivo": "main.c",
                        "nombre_proyecto": "e2e_s3",
                        "target": "esp32s3",
                    },
                )
            assert r_comp.status_code == 200
            datos_comp = r_comp.json()
            assert datos_comp["success"] is True
            binarios = {b["filename"]: b for b in datos_comp["binaries"]}
            assert binarios["bootloader.bin"]["flash_offset"] == "0x0"
            assert binarios["partition-table.bin"]["flash_offset"] == "0x8000"
            assert binarios["e2e_app.bin"]["flash_offset"] == "0x10000"

            # Verificar que el modulo menu-log recibio el evento de compilacion
            r_mlog = client.get("/api/v1/menu-log/logs")
            assert r_mlog.status_code == 200
            assert len(r_mlog.json()["messages"]) >= 1

            # Paso 4: Iniciar sesion de simulacion ESP32-S3 y flashear app
            r_ses = client.post(
                "/api/v1/simulacion/sesiones",
                json={"chip": "ESP32-S3", "motor": "esp_emulator", "nombre": "E2E-S3"},
            )
            assert r_ses.status_code == 200
            sesion_id = r_ses.json()["sesion_id"]
            assert (
                client.post(
                    f"/api/v1/simulacion/sesiones/{sesion_id}/iniciar"
                ).status_code
                == 200
            )
            assert (
                client.post(
                    f"/api/v1/simulacion/sesiones/{sesion_id}/flashear",
                    json={
                        "archivo": binarios["e2e_app.bin"]["filename"],
                        "direccion": "0x10000",
                    },
                ).status_code
                == 200
            )

            # Paso 5: Flasheo completo orquestado (Bootloader + Particiones + App) con verificacion
            r_part = client.post(
                "/api/v1/herramientas/particiones/generar",
                json={"plantilla_id": "single_app_ssl_nvs", "nombre": "e2e_parts"},
            )
            assert r_part.status_code == 200

            r_flash = client.post(
                "/api/v1/herramientas/esptool/flash-completo",
                json={
                    "target": "esp32s3",
                    "modo": "emulado",
                    "bootloader_path": binarios["bootloader.bin"]["absolute_path"],
                    "partitions_path": r_part.json()["bin_path"],
                    "app_path": binarios["e2e_app.bin"]["absolute_path"],
                    "verificar": True,
                },
            )
            assert r_flash.status_code == 200
            assert r_flash.json()["exitoso"] is True
            assert r_flash.json()["verificado"] is True

            # Paso 6: Probar perifericos (GPIO + UART) y Monitor/Plotter Serie
            assert (
                client.post(
                    f"/api/v1/simulacion/sesiones/{sesion_id}/componentes",
                    json={"id": "sensor-i2c", "tipo": "dht22", "puerto": "GPIO4"},
                ).status_code
                == 200
            )
            assert (
                client.post(
                    f"/api/v1/simulacion/sesiones/{sesion_id}/comandos",
                    json={"comando": "READ_SENSOR"},
                ).status_code
                == 200
            )

            assert (
                client.post(
                    "/api/v1/herramientas/monitor-serie/conectar",
                    json={"puerto": "VIRTUAL", "baudrate": 115200, "modo": "emulado"},
                ).status_code
                == 200
            )
            assert (
                client.post(
                    "/api/v1/herramientas/monitor-serie/enviar",
                    json={"datos": "PLOT"},
                ).status_code
                == 200
            )
            r_plot = client.get("/api/v1/herramientas/plotter/muestras")
            assert r_plot.status_code == 200
            assert r_plot.json()["total_muestras"] >= 4

            # Paso 7: Generar reportes consolidados y exportar logs CSV
            r_rep_sim = client.get(f"/api/v1/simulacion/sesiones/{sesion_id}/reportes")
            assert r_rep_sim.status_code == 200
            assert r_rep_sim.json()["chip"] == "ESP32-S3"

            r_rep_flash = client.get("/api/v1/herramientas/historial-flash")
            assert r_rep_flash.status_code == 200
            assert r_rep_flash.json()["total"] >= 1

            r_exp = client.get(
                "/api/v1/herramientas/logs/exportar", params={"formato": "csv"}
            )
            assert r_exp.status_code == 200
            assert "temp" in r_exp.text

            client.post("/api/v1/herramientas/monitor-serie/desconectar")
            client.post(f"/api/v1/simulacion/sesiones/{sesion_id}/detener")
