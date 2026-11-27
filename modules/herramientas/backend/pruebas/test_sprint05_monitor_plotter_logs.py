# Archivo: modules/herramientas/backend/pruebas/test_sprint05_monitor_plotter_logs.py
"""Pruebas unitarias y de integracion para el Sprint 5: Monitor Serie, Plotter y Exportacion de Logs."""

from __future__ import annotations

import csv
import io
import json
from contextlib import contextmanager
from pathlib import Path

import pytest
import serial
from fastapi.testclient import TestClient

import ide_core.db.connection as db_conn
from ide_core.config.setup import AppConfig


@contextmanager
def _bd_temporal_aislada(tmp_path: Path):
    """Redirige temporalmente RUTA_BD a un archivo SQLite aislado y restaura al salir."""
    ruta_original = db_conn.RUTA_BD
    pool_original = db_conn._POOL_ACTIVO
    db_temp = tmp_path / "test_sprint05.db"
    db_conn.RUTA_BD = db_temp
    db_conn._POOL_ACTIVO = False
    try:
        db_conn.init_pool()
        db_conn.aplicar_esquemas_completos()
        yield db_temp
    finally:
        db_conn.RUTA_BD = ruta_original
        db_conn._POOL_ACTIVO = pool_original


def test_parsear_linea_plotter_formatos_espressif_y_sensores():
    """S3 / S5-04: Extrae canales numericos de formatos clave:valor, ESP-IDF, SENSOR, JSON y columnas."""
    from herramientas_backend.controllers.monitor_serie import parsear_linea_plotter

    assert parsear_linea_plotter("temp:25.4,hum:60.1") == {
        "temp": 25.4,
        "hum": 60.1,
    }
    assert parsear_linea_plotter("I (1420) ESP32S3: temp=26.75 hum=58.2 volt:3.31") == {
        "temp": 26.75,
        "hum": 58.2,
        "volt": 3.31,
    }
    assert parsear_linea_plotter("SENSOR:dht22:24.80") == {"dht22": 24.8}
    assert parsear_linea_plotter('{"ax": -0.12, "ay": 0.98, "az": 9.81}') == {
        "ax": -0.12,
        "ay": 0.98,
        "az": 9.81,
    }
    assert parsear_linea_plotter("12.5 45.0 -3.25") == {
        "ch1": 12.5,
        "ch2": 45.0,
        "ch3": -3.25,
    }
    assert parsear_linea_plotter("ESP-ROM:esp32s3-20210327") == {}
    assert parsear_linea_plotter("Sistema iniciado correctamente") == {}
    # Regresion COM3 real: logs diagnosticos HAL/WiFi NO deben generar canales falsos como {"Reason": 201.0}
    assert (
        parsear_linea_plotter(
            "[1203297][W][STA.cpp:137] _onStaArduinoEvent(): Reason: 201 - NO_AP_FOUND"
        )
        == {}
    )
    assert (
        parsear_linea_plotter(
            "[1203305][W][STA.cpp:137] _onStaArduinoEvent(): Reason: 36 - STA_LEAVING"
        )
        == {}
    )


def test_clasificacion_y_filtros_monitor_serie(tmp_path: Path):
    """S2 / S5-03: Clasifica severidad ESP-IDF y filtra por nivel, texto y regex segura."""
    from herramientas_backend.controllers.monitor_serie import (
        clasificar_nivel_linea,
        gestor_monitor_global,
    )

    assert clasificar_nivel_linea("E (200) wifi: desconexion inesperada") == "ERROR"
    assert clasificar_nivel_linea("W (150) adc: voltaje bajo") == "WARN"
    assert clasificar_nivel_linea("I (100) boot: ESP-IDF v6.1.1") == "INFO"
    assert clasificar_nivel_linea("D (90) spi: trama enviada") == "DEBUG"
    assert (
        clasificar_nivel_linea(
            "[1203297][W][STA.cpp:137] _onStaArduinoEvent(): Reason: 201 - NO_AP_FOUND"
        )
        == "WARN"
    )
    assert (
        clasificar_nivel_linea(
            "[1203400][E][STA.cpp:150] _onStaArduinoEvent(): Error critico"
        )
        == "ERROR"
    )

    with _bd_temporal_aislada(tmp_path):
        app = AppConfig.crear_app()
        gestor_monitor_global.reiniciar_para_pruebas()
        with TestClient(app) as client:
            r_conn = client.post(
                "/api/v1/herramientas/monitor-serie/conectar",
                json={
                    "puerto": "VIRTUAL",
                    "baudrate": 115200,
                    "modo": "emulado",
                },
            )
            assert r_conn.status_code == 200

            gestor_monitor_global.inyectar_linea_rx("I (100) sensor: temp=25.40")
            gestor_monitor_global.inyectar_linea_rx("W (110) wifi: rssi=-79")
            gestor_monitor_global.inyectar_linea_rx("E (120) i2c: timeout bus 0")

            r_err = client.get(
                "/api/v1/herramientas/monitor-serie/eventos",
                params={"nivel": "ERROR"},
            )
            assert r_err.status_code == 200
            eventos_err = r_err.json()["eventos"]
            assert len(eventos_err) == 1
            assert "i2c: timeout" in eventos_err[0]["linea"]

            r_regex = client.get(
                "/api/v1/herramientas/monitor-serie/eventos",
                params={"regex": r"temp=\d+\.\d+"},
            )
            assert r_regex.status_code == 200
            assert len(r_regex.json()["eventos"]) == 1

            r_bad_regex = client.get(
                "/api/v1/herramientas/monitor-serie/eventos",
                params={"regex": "[invalido"},
            )
            assert r_bad_regex.status_code == 400

            r_redos_regex = client.get(
                "/api/v1/herramientas/monitor-serie/eventos",
                params={"regex": "(a+)+$"},
            )
            assert r_redos_regex.status_code == 400

            client.post("/api/v1/herramientas/monitor-serie/desconectar")


def test_monitor_serie_flujo_http_y_exportacion_csv_txt_json(tmp_path: Path):
    """S1, S3, S4 / S5-06, S5-09: Conecta, envia comandos, grafica muestras y exporta CSV/TXT/JSON."""
    from herramientas_backend.controllers.monitor_serie import gestor_monitor_global

    with _bd_temporal_aislada(tmp_path):
        app = AppConfig.crear_app()
        gestor_monitor_global.reiniciar_para_pruebas()
        with TestClient(app) as client:
            r_con = client.post(
                "/api/v1/herramientas/monitor-serie/conectar",
                json={
                    "puerto": "VIRTUAL",
                    "baudrate": 115200,
                    "databits": 8,
                    "stopbits": 1.0,
                    "parity": "N",
                    "modo": "emulado",
                },
            )
            assert r_con.status_code == 200
            assert r_con.json()["conectado"] is True

            r_tx = client.post(
                "/api/v1/herramientas/monitor-serie/enviar",
                json={"datos": "PLOT"},
            )
            assert r_tx.status_code == 200
            assert r_tx.json()["enviado"] is True

            r_muestras = client.get("/api/v1/herramientas/plotter/muestras")
            assert r_muestras.status_code == 200
            datos_plotter = r_muestras.json()
            assert datos_plotter["total_muestras"] >= 1
            assert len(datos_plotter["canales_disponibles"]) >= 2

            # Exportacion CSV
            r_csv = client.get(
                "/api/v1/herramientas/logs/exportar",
                params={"formato": "csv"},
            )
            assert r_csv.status_code == 200
            assert "attachment" in r_csv.headers.get("content-disposition", "")
            filas = list(csv.reader(io.StringIO(r_csv.text)))
            assert filas[0] == [
                "seq",
                "fecha",
                "puerto",
                "baudrate",
                "direccion",
                "nivel",
                "linea",
                "canales_json",
            ]
            assert len(filas) >= 3

            # Exportacion TXT
            r_txt = client.get(
                "/api/v1/herramientas/logs/exportar",
                params={"formato": "txt"},
            )
            assert r_txt.status_code == 200
            assert "PLOT" in r_txt.text

            # Exportacion JSON
            r_json = client.get(
                "/api/v1/herramientas/logs/exportar",
                params={"formato": "json"},
            )
            assert r_json.status_code == 200
            payload_json = json.loads(r_json.text)
            assert payload_json["total"] >= 2
            assert isinstance(payload_json["eventos"], list)

            r_disc = client.post("/api/v1/herramientas/monitor-serie/desconectar")
            assert r_disc.status_code == 200
            assert r_disc.json()["conectado"] is False


def test_monitor_serie_websocket_bidireccional(tmp_path: Path):
    """S1 / S5-01, S5-08: Puente WebSocket recibe estado inicial y transmite telemetria en vivo."""
    from herramientas_backend.controllers.monitor_serie import gestor_monitor_global

    with _bd_temporal_aislada(tmp_path):
        app = AppConfig.crear_app()
        gestor_monitor_global.reiniciar_para_pruebas()
        with TestClient(app) as client:
            with client.websocket_connect(
                "/api/v1/herramientas/monitor-serie/stream?puerto=VIRTUAL&baudrate=115200&modo=emulado"
            ) as ws:
                inicial = ws.receive_json()
                assert inicial["tipo"] == "estado"
                assert inicial["estado"]["conectado"] is True

                ws.send_json({"accion": "enviar", "datos": "PLOT"})
                recibidos = []
                for _ in range(4):
                    msg = ws.receive_json()
                    recibidos.append(msg)
                    if (
                        msg.get("tipo") == "evento"
                        and msg["evento"].get("direccion") == "RX"
                        and msg["evento"].get("canales")
                    ):
                        break

                assert any(
                    m.get("tipo") == "evento" and m["evento"].get("canales")
                    for m in recibidos
                )

            gestor_monitor_global.desconectar()

            # Enviar TX mientras esta desconectado por WS devuelve error JSON sin caer el socket
            with client.websocket_connect(
                "/api/v1/herramientas/monitor-serie/stream"
            ) as ws_disc:
                est = ws_disc.receive_json()
                assert est["estado"]["conectado"] is False
                ws_disc.send_json({"accion": "enviar", "datos": "AT"})
                err_msg = ws_disc.receive_json()
                assert err_msg["tipo"] == "error"
                assert err_msg["codigo"] == 409


def test_monitor_serie_desconexion_usb_y_reconexion_automatica(tmp_path: Path):
    """S5 / S5-07: Maneja desconexion abrupta USB sin bloquear y reconecta automaticamente."""
    import time

    from herramientas_backend.controllers.monitor_serie import GestorMonitorSerie

    class PuertoSerialFalso:
        def __init__(self, respuestas: list[bytes | Exception]):
            self._respuestas = list(respuestas)
            self.cerrado = False
            self.escrituras: list[bytes] = []

        @property
        def is_open(self) -> bool:
            return not self.cerrado

        def readline(self) -> bytes:
            if self.cerrado:
                return b""
            if not self._respuestas:
                time.sleep(0.02)
                return b""
            item = self._respuestas.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        def write(self, data: bytes) -> int:
            self.escrituras.append(data)
            return len(data)

        def flush(self) -> None:
            pass

        def close(self) -> None:
            self.cerrado = True

    instancias_creadas: list[PuertoSerialFalso] = []

    def fabrica_serial_simulada(**_kwargs):
        idx = len(instancias_creadas)
        if idx == 0:
            inst = PuertoSerialFalso(
                [
                    b"I (10) esp32s3: temp:31.2,volt:3.30\r\n",
                    serial.SerialException("Dispositivo USB desconectado"),
                ]
            )
        elif idx == 1:
            instancias_creadas.append(PuertoSerialFalso([]))
            raise serial.SerialException("Puerto aun no disponible")
        else:
            inst = PuertoSerialFalso([b"I (500) esp32s3: temp:32.0,volt:3.31\r\n"])
        instancias_creadas.append(inst)
        return inst

    with _bd_temporal_aislada(tmp_path):
        gestor = GestorMonitorSerie(
            serial_factory=fabrica_serial_simulada,
            intervalo_reconexion_s=0.05,
        )
        estado = gestor.conectar(
            puerto="COM7",
            baudrate=115200,
            modo="fisico",
            auto_reconectar=True,
        )
        assert estado["conectado"] is True

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            ev = gestor.obtener_eventos()
            textos = [e["linea"] for e in ev["eventos"]]
            if any("temp:32.0" in t for t in textos) and any(
                "Reconexion" in t or "reconect" in t.lower() for t in textos
            ):
                break
            time.sleep(0.03)

        gestor.desconectar()
        assert instancias_creadas[0].cerrado is True
        eventos_finales = [e["linea"] for e in gestor.obtener_eventos()["eventos"]]
        assert any("temp:31.2" in t for t in eventos_finales)
        assert any(
            "Desconexion" in t or "desconect" in t.lower() for t in eventos_finales
        )
        assert any("temp:32.0" in t for t in eventos_finales)


def test_rutas_existentes_herramientas_preservadas(tmp_path: Path):
    """Regresion: Las rutas previas de placas y particiones mantienen su contrato."""
    with _bd_temporal_aislada(tmp_path):
        app = AppConfig.crear_app()
        with TestClient(app) as client:
            r1 = client.get("/api/v1/herramientas/placas-soportadas")
            r2 = client.get("/api/v1/herramientas/particiones/plantillas")
            assert r1.status_code == 200
            assert r1.json()["total"] >= 5
            assert r2.status_code == 200
            assert r2.json()["total"] >= 3
