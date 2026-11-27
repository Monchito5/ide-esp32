# Archivo: modules/simulacion/backend/pruebas/unitarias/test_simulacion_endpoints_s6.py
"""Pruebas HTTP de sesiones, motores, perifericos y reportes en Simulacion (Sprint 6 — S6-02)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from simulacion_backend.modulo import registrar


def test_motores_y_chips_simulacion():
    app = FastAPI()
    registrar(app)
    with TestClient(app) as client:
        r_mot = client.get("/api/v1/simulacion/motores")
        assert r_mot.status_code == 200
        ids_mot = {m["id"] for m in r_mot.json()["motores"]}
        assert "esp_emulator" in ids_mot

        r_chips = client.get("/api/v1/simulacion/chips")
        assert r_chips.status_code == 200
        ids_chips = {c["id"] for c in r_chips.json()["chips"]}
        assert {"ESP32-S3", "ESP32-C3"}.issubset(ids_chips)


def test_ciclo_completo_sesion_perifericos_uart_y_reporte():
    app = FastAPI()
    registrar(app)
    with TestClient(app) as client:
        r_crear = client.post(
            "/api/v1/simulacion/sesiones",
            json={"chip": "ESP32-S3", "motor": "esp_emulator", "nombre": "DemoS6"},
        )
        assert r_crear.status_code == 200
        sesion_id = r_crear.json()["sesion_id"]

        # Flashear antes de iniciar debe devolver 400
        r_pre = client.post(
            f"/api/v1/simulacion/sesiones/{sesion_id}/flashear",
            json={"archivo": "app.bin", "direccion": "0x10000"},
        )
        assert r_pre.status_code == 400

        r_ini = client.post(f"/api/v1/simulacion/sesiones/{sesion_id}/iniciar")
        assert r_ini.status_code == 200
        assert r_ini.json()["estado"] == "iniciada"

        r_flash = client.post(
            f"/api/v1/simulacion/sesiones/{sesion_id}/flashear",
            json={"archivo": "s3_firmware.bin", "direccion": "0x10000", "version": "2.0.0"},
        )
        assert r_flash.status_code == 200
        assert r_flash.json()["firmware_cargado"] == "s3_firmware.bin"

        r_comp = client.post(
            f"/api/v1/simulacion/sesiones/{sesion_id}/componentes",
            json={"id": "led-s3", "tipo": "led", "puerto": "GPIO48"},
        )
        assert r_comp.status_code == 200
        assert r_comp.json()["puerto"] == "GPIO48"

        r_cmd = client.post(
            f"/api/v1/simulacion/sesiones/{sesion_id}/comandos",
            json={"comando": "GPIO_SET 48 1"},
        )
        assert r_cmd.status_code == 200
        assert "OK:" in r_cmd.json()["respuesta"]

        r_rep = client.get(f"/api/v1/simulacion/sesiones/{sesion_id}/reportes")
        assert r_rep.status_code == 200
        rep = r_rep.json()
        assert rep["firmware"]["archivo"] == "s3_firmware.bin"
        assert len(rep["componentes"]) == 1

        r_rei = client.post(f"/api/v1/simulacion/sesiones/{sesion_id}/reiniciar")
        assert r_rei.status_code == 200
        assert r_rei.json()["estado"] == "iniciada"

        r_det = client.post(f"/api/v1/simulacion/sesiones/{sesion_id}/detener")
        assert r_det.status_code == 200
        assert r_det.json()["estado"] == "detenida"
