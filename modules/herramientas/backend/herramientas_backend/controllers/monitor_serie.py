# Archivo: modules/herramientas/backend/herramientas_backend/controllers/monitor_serie.py
"""Controlador del Monitor Serie, Plotter Serie multicanal y Exportacion de Logs (Sprint 5)."""

from __future__ import annotations

import asyncio
import csv
import io
import json
import math
import queue
import re
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Optional

import serial
from fastapi import HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ide_core.db.connection import conexion
from ide_core.models.base import ejecutar

BAUDRATES_SOPORTADOS: list[int] = [
    9600,
    19200,
    38400,
    57600,
    74880,
    115200,
    230400,
    460800,
    921600,
]

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_PREFIJO_IDF_RE = re.compile(r"^([IWEVD])\s*\(\d+\)\s*[^:]+:\s*")
_PREFIJO_HAL_RE = re.compile(r"^\[\s*\d+\s*\]\[\s*([IWEVD])\s*\](?:\[[^\]]*\])?\s*")
_DIAGNOSTICO_NO_PLOT_RE = re.compile(
    r"^(?:[EWDV]\s*\(\d+\)|\[\s*\d+\s*\]\[\s*[EWDV]\s*\])"
)
_PREFIJO_TS_RE = re.compile(r"^\[?\d{2}:\d{2}:\d{2}(?:\.\d+)?\]?\s*")
_SENSOR_TAG_RE = re.compile(
    r"^SENSOR:([A-Za-z0-9_.-]+):([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)$",
    re.IGNORECASE,
)
_ESPACIO_KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_.-]*)\s*([:=])\s*([-+]?\d)")
_TOKEN_KV_ESTRICTO_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_.-]*)[:=]([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)$"
)
_NUMERO_PURO_RE = re.compile(r"^[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$")

_MAPA_BYTESIZE = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
}
_MAPA_STOPBITS = {
    1.0: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2.0: serial.STOPBITS_TWO,
}
_MAPA_PARITY = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
    "M": serial.PARITY_MARK,
    "S": serial.PARITY_SPACE,
}


class SolicitudConectarMonitor(BaseModel):
    puerto: str = "VIRTUAL"
    baudrate: int = Field(default=115200, gt=0)
    databits: Literal[5, 6, 7, 8] = 8
    stopbits: Literal[1.0, 1.5, 2.0] = 1.0
    parity: Literal["N", "E", "O", "M", "S"] = "N"
    modo: Literal["auto", "fisico", "emulado"] = "auto"
    auto_reconectar: bool = True


class SolicitudEnviarSerial(BaseModel):
    datos: str
    agregar_salto_linea: bool = True


class SolicitudParsearPlotter(BaseModel):
    lineas: list[str]


def limpiar_ansi(texto: str) -> str:
    """Elimina secuencias de escape ANSI de una linea serial."""
    return _ANSI_ESCAPE_RE.sub("", texto or "").strip()


def clasificar_nivel_linea(linea: str) -> str:
    """Clasifica el nivel de severidad de una linea de log ESP-IDF, HAL Arduino o estandar."""
    limpia = limpiar_ansi(linea)
    if not limpia:
        return "INFO"

    coincidencia = re.match(r"^([IWEVD])\s*\(\d+\)", limpia) or _PREFIJO_HAL_RE.match(
        limpia
    )
    if coincidencia:
        codigo = coincidencia.group(1).upper()
        if codigo == "E":
            return "ERROR"
        if codigo == "W":
            return "WARN"
        if codigo in ("D", "V"):
            return "DEBUG"
        return "INFO"

    mayus = limpia.upper()
    if any(
        palabra in mayus
        for palabra in ("ERROR", "FAIL", "PANIC", "GURU MEDITATION", "TRACEBACK")
    ):
        return "ERROR"
    if any(palabra in mayus for palabra in ("WARN", "WARNING")):
        return "WARN"
    if "DEBUG" in mayus:
        return "DEBUG"
    return "INFO"


def parsear_linea_plotter(linea: str) -> dict[str, float]:
    """Extrae pares canal->valor numerico unicamente de tramas reales de telemetria."""
    limpia = limpiar_ansi(linea)
    if not limpia or _DIAGNOSTICO_NO_PLOT_RE.match(limpia):
        return {}

    cuerpo = _PREFIJO_IDF_RE.sub("", limpia)
    cuerpo = _PREFIJO_HAL_RE.sub("", cuerpo)
    cuerpo = _PREFIJO_TS_RE.sub("", cuerpo).strip()
    if not cuerpo:
        return {}

    m_sensor = _SENSOR_TAG_RE.match(cuerpo)
    if m_sensor:
        valor = float(m_sensor.group(2))
        return {m_sensor.group(1): valor} if math.isfinite(valor) else {}

    if (cuerpo.startswith("{") and cuerpo.endswith("}")) or (
        cuerpo.startswith("[") and cuerpo.endswith("]")
    ):
        try:
            cargado = json.loads(cuerpo)
            if isinstance(cargado, dict):
                canales_json: dict[str, float] = {}
                for clave, val in cargado.items():
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        fval = float(val)
                        if math.isfinite(fval):
                            canales_json[str(clave)] = fval
                return canales_json
            if isinstance(cargado, list) and cargado:
                if all(
                    isinstance(v, (int, float)) and not isinstance(v, bool)
                    for v in cargado
                ):
                    return {
                        f"ch{idx + 1}": float(v)
                        for idx, v in enumerate(cargado)
                        if math.isfinite(float(v))
                    }
        except (ValueError, TypeError):
            pass

    normalizado_kv = _ESPACIO_KV_RE.sub(r"\1\2\3", cuerpo)
    tokens_kv = [t for t in re.split(r"[\s,;]+", normalizado_kv) if t]
    if tokens_kv and all(_TOKEN_KV_ESTRICTO_RE.match(t) for t in tokens_kv):
        resultado_kv: dict[str, float] = {}
        for token in tokens_kv:
            m_kv = _TOKEN_KV_ESTRICTO_RE.match(token)
            if m_kv is not None:
                fval = float(m_kv.group(2))
                if math.isfinite(fval):
                    resultado_kv[m_kv.group(1)] = fval
        if resultado_kv:
            return resultado_kv

    partes = [p for p in re.split(r"[\s,;]+", cuerpo) if p]
    if partes and all(_NUMERO_PURO_RE.match(p) for p in partes):
        resultado_cols: dict[str, float] = {}
        for idx, token in enumerate(partes):
            fval = float(token)
            if math.isfinite(fval):
                resultado_cols[f"ch{idx + 1}"] = fval
        return resultado_cols

    return {}


def _tiene_riesgo_redos(patron: str) -> bool:
    """Detecta cuantificadores anidados, alternancias cuantificadas y retroreferencias."""
    if re.search(r"\\[1-9]", patron):
        return True
    pila_grupos: list[dict[str, bool]] = []
    en_clase = False
    escapado = False
    n = len(patron)
    i = 0
    while i < n:
        ch = patron[i]
        if escapado:
            escapado = False
            i += 1
            continue
        if ch == "\\":
            escapado = True
            i += 1
            continue
        if en_clase:
            if ch == "]":
                en_clase = False
            i += 1
            continue
        if ch == "[":
            en_clase = True
            i += 1
            continue
        if ch == "(":
            pila_grupos.append({"cuantificador": False, "alternancia": False})
            i += 1
            continue
        if ch == ")" and pila_grupos:
            grupo = pila_grupos.pop()
            j = i + 1
            while j < n and patron[j].isspace():
                j += 1
            cuantificado_afuera = j < n and patron[j] in ("+", "*", "?", "{")
            if cuantificado_afuera and (grupo["cuantificador"] or grupo["alternancia"]):
                return True
            if pila_grupos and (grupo["cuantificador"] or cuantificado_afuera):
                pila_grupos[-1]["cuantificador"] = True
            i += 1
            continue
        if pila_grupos:
            if ch in ("+", "*", "{"):
                pila_grupos[-1]["cuantificador"] = True
            elif ch == "|":
                pila_grupos[-1]["alternancia"] = True
        i += 1
    return False


def compilar_filtro_regex(patron: Optional[str]) -> Optional[re.Pattern[str]]:
    """Valida y compila una expresion regular de usuario de forma segura."""
    if not patron:
        return None
    if len(patron) > 256:
        raise HTTPException(
            status_code=400,
            detail="La expresion regular excede la longitud maxima permitida (256).",
        )
    if _tiene_riesgo_redos(patron):
        raise HTTPException(
            status_code=400,
            detail="Expresion regular rechazada por cuantificadores anidados no seguros.",
        )
    try:
        return re.compile(patron)
    except re.error as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Expresion regular invalida: {exc}",
        ) from exc


def evento_cumple_filtros(
    evento: dict[str, Any],
    nivel: Optional[str] = None,
    buscar: Optional[str] = None,
    patron_re: Optional[re.Pattern[str]] = None,
) -> bool:
    """Evalua si un evento serial satisface los criterios de filtrado."""
    if nivel and nivel.upper() not in ("TODOS", "ALL", ""):
        if str(evento.get("nivel", "")).upper() != nivel.upper():
            return False
    linea = str(evento.get("linea", ""))
    if buscar:
        if buscar.lower() not in linea.lower():
            return False
    if patron_re is not None:
        if not patron_re.search(linea):
            return False
    return True


class GestorMonitorSerie:
    """Administra la sesion activa del Monitor Serie (pyserial fisico o emulado)."""

    def __init__(
        self,
        serial_factory: Optional[Callable[..., Any]] = None,
        intervalo_reconexion_s: float = 0.5,
        max_eventos: int = 2000,
    ) -> None:
        self._serial_factory = serial_factory or serial.Serial
        self._intervalo_reconexion_s = intervalo_reconexion_s
        self._lock = threading.RLock()
        self._tx_lock = threading.Lock()
        self._eventos: deque[dict[str, Any]] = deque(maxlen=max_eventos)
        self._seq: int = 0
        self._conectado: bool = False
        self._estado: str = "desconectado"
        self._sesion_id: str = ""
        self._ultimo_error: Optional[str] = None
        self._config: dict[str, Any] = {
            "puerto": "VIRTUAL",
            "baudrate": 115200,
            "databits": 8,
            "stopbits": 1.0,
            "parity": "N",
            "modo": "emulado",
            "auto_reconectar": True,
        }
        self._serial_handle: Any = None
        self._stop_event = threading.Event()
        self._hilo_lector: Optional[threading.Thread] = None
        self._paso_onda: int = 0
        self._cola_sqlite: queue.Queue[tuple[Any, ...]] = queue.Queue(maxsize=4096)
        self._hilo_sqlite = threading.Thread(
            target=self._bucle_persistencia_sqlite,
            name="serial-sqlite-writer",
            daemon=True,
        )
        self._hilo_sqlite.start()

    def _bucle_persistencia_sqlite(self) -> None:
        """Drena en lotes asincronos los eventos seriales hacia SQLite sin bloquear pyserial."""
        sql_insert = """
            INSERT INTO herramientas_eventos_serie
                (sesion_id, puerto, baudrate, direccion, nivel, linea, canales_json, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        while True:
            primera = self._cola_sqlite.get()
            lote = [primera]
            while len(lote) < 64:
                try:
                    lote.append(self._cola_sqlite.get_nowait())
                except queue.Empty:
                    break
            try:
                with conexion() as conn:
                    conn.executemany(sql_insert, lote)
            except Exception:
                # En pruebas unitarias sin pool SQLite activo se conserva en memoria.
                pass
            finally:
                for _ in lote:
                    self._cola_sqlite.task_done()

    def sincronizar_persistencia(self, timeout_s: float = 0.5) -> None:
        """Espera de forma acotada a que la cola de escritura SQLite quede vacia."""
        limite = time.monotonic() + timeout_s
        while self._cola_sqlite.unfinished_tasks > 0 and time.monotonic() < limite:
            time.sleep(0.005)

    def reiniciar_para_pruebas(self) -> None:
        """Detiene cualquier sesion activa y limpia el buffer en memoria."""
        self.desconectar()
        self.sincronizar_persistencia()
        with self._lock:
            self._eventos.clear()
            self._seq = 0
            self._paso_onda = 0
            self._ultimo_error = None

    def _resolver_modo(self, puerto: str, modo: str) -> str:
        if modo in ("fisico", "emulado"):
            return modo
        normalizado = (puerto or "").strip().upper()
        if normalizado in (
            "",
            "VIRTUAL",
            "EMULADO",
            "SIMULADO",
            "BUSCANDO...",
            "COM10",
        ):
            return "emulado"
        return "fisico"

    def _abrir_serial_fisico(self, cfg: dict[str, Any]) -> Any:
        return self._serial_factory(
            port=cfg["puerto"],
            baudrate=int(cfg["baudrate"]),
            bytesize=_MAPA_BYTESIZE.get(int(cfg["databits"]), serial.EIGHTBITS),
            stopbits=_MAPA_STOPBITS.get(float(cfg["stopbits"]), serial.STOPBITS_ONE),
            parity=_MAPA_PARITY.get(str(cfg["parity"]).upper(), serial.PARITY_NONE),
            timeout=0.2,
            write_timeout=0.5,
        )

    def _registrar_evento(
        self,
        linea: str,
        direccion: str = "RX",
        nivel_forzado: Optional[str] = None,
    ) -> dict[str, Any]:
        texto = limpiar_ansi(linea)
        nivel = nivel_forzado or clasificar_nivel_linea(texto)
        canales = parsear_linea_plotter(texto) if direccion == "RX" else {}
        marca_tiempo = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

        with self._lock:
            self._seq += 1
            evento = {
                "seq": self._seq,
                "sesion_id": self._sesion_id or "sin-sesion",
                "fecha": marca_tiempo,
                "puerto": self._config["puerto"],
                "baudrate": self._config["baudrate"],
                "direccion": direccion,
                "nivel": nivel,
                "linea": texto,
                "canales": canales,
            }
            self._eventos.append(evento)

        fila_bd = (
            evento["sesion_id"],
            evento["puerto"],
            int(evento["baudrate"]),
            evento["direccion"],
            evento["nivel"],
            evento["linea"],
            json.dumps(canales, ensure_ascii=False) if canales else None,
            evento["fecha"],
        )
        try:
            self._cola_sqlite.put_nowait(fila_bd)
        except queue.Full:
            pass

        return evento

    def inyectar_linea_rx(self, linea: str) -> dict[str, Any]:
        """Permite inyectar una linea RX sintetica (emulacion y pruebas)."""
        return self._registrar_evento(linea, direccion="RX")

    def conectar(
        self,
        puerto: str = "VIRTUAL",
        baudrate: int = 115200,
        databits: int = 8,
        stopbits: float = 1.0,
        parity: str = "N",
        modo: str = "auto",
        auto_reconectar: bool = True,
    ) -> dict[str, Any]:
        """Abre una sesion de monitoreo serial sobre hardware real o entorno emulado."""
        self.desconectar()
        modo_efectivo = self._resolver_modo(puerto, modo)
        cfg = {
            "puerto": puerto.strip() or "VIRTUAL",
            "baudrate": int(baudrate),
            "databits": int(databits),
            "stopbits": float(stopbits),
            "parity": parity.upper(),
            "modo": modo_efectivo,
            "auto_reconectar": bool(auto_reconectar),
        }

        sesion_id = f"mon-{uuid.uuid4().hex[:10]}"
        stop_event = threading.Event()

        if modo_efectivo == "fisico":
            try:
                handle = self._abrir_serial_fisico(cfg)
            except (serial.SerialException, OSError) as exc:
                with self._lock:
                    self._config = cfg
                    self._conectado = False
                    self._estado = "error"
                    self._ultimo_error = str(exc)
                raise HTTPException(
                    status_code=503,
                    detail=f"No se pudo abrir el puerto serie {cfg['puerto']}: {exc}",
                ) from exc

            with self._lock:
                self._stop_event = stop_event
                self._config = cfg
                self._sesion_id = sesion_id
                self._serial_handle = handle
                self._conectado = True
                self._estado = "conectado"
                self._ultimo_error = None

            self._registrar_evento(
                f"Conectado a {cfg['puerto']} ({cfg['baudrate']} {cfg['databits']}{cfg['parity']}{int(cfg['stopbits']) if cfg['stopbits'] == int(cfg['stopbits']) else cfg['stopbits']})",
                direccion="SYS",
                nivel_forzado="INFO",
            )
            estado_inicial = self.obtener_estado()
            hilo = threading.Thread(
                target=self._bucle_lectura_fisica,
                args=(sesion_id, stop_event),
                name=f"serial-reader-{cfg['puerto']}",
                daemon=True,
            )
            with self._lock:
                self._hilo_lector = hilo
            hilo.start()
            return estado_inicial
        else:
            with self._lock:
                self._stop_event = stop_event
                self._config = cfg
                self._sesion_id = sesion_id
                self._serial_handle = None
                self._conectado = True
                self._estado = "conectado"
                self._ultimo_error = None

            self._registrar_evento(
                f"Sesion serial emulada activa en {cfg['puerto']} ({cfg['baudrate']} baud).",
                direccion="SYS",
                nivel_forzado="INFO",
            )

        return self.obtener_estado()

    def _cerrar_handle_actual(self, esperado: Any = None) -> None:
        with self._lock:
            if esperado is not None and self._serial_handle is not esperado:
                handle = esperado
            else:
                handle = self._serial_handle
                self._serial_handle = None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass

    def _bucle_lectura_fisica(
        self, sesion_id: str, stop_event: threading.Event
    ) -> None:
        while not stop_event.is_set():
            with self._lock:
                if stop_event.is_set() or self._sesion_id != sesion_id:
                    break
                handle = self._serial_handle
                cfg = dict(self._config)

            if handle is None:
                if not cfg.get("auto_reconectar", True):
                    break
                if stop_event.wait(self._intervalo_reconexion_s):
                    break
                try:
                    nuevo = self._abrir_serial_fisico(cfg)
                except (serial.SerialException, OSError) as exc:
                    with self._lock:
                        if self._sesion_id == sesion_id:
                            self._ultimo_error = str(exc)
                    continue

                abortado = False
                with self._lock:
                    if stop_event.is_set() or self._sesion_id != sesion_id:
                        abortado = True
                    else:
                        self._serial_handle = nuevo
                        self._conectado = True
                        self._estado = "conectado"
                        self._ultimo_error = None
                if abortado:
                    try:
                        nuevo.close()
                    except Exception:
                        pass
                    break

                self._registrar_evento(
                    f"Reconexion USB exitosa en {cfg['puerto']} ({cfg['baudrate']} baud).",
                    direccion="SYS",
                    nivel_forzado="INFO",
                )
                continue

            try:
                crudo = handle.readline()
                if crudo:
                    texto = crudo.decode("utf-8", errors="replace")
                    for sublinea in texto.splitlines():
                        if sublinea.strip():
                            self._registrar_evento(sublinea, direccion="RX")
            except (
                serial.SerialException,
                OSError,
                TypeError,
                AttributeError,
            ) as exc:
                self._cerrar_handle_actual(esperado=handle)
                with self._lock:
                    if stop_event.is_set() or self._sesion_id != sesion_id:
                        break
                    self._conectado = False
                    self._ultimo_error = str(exc)
                    reconectar = bool(self._config.get("auto_reconectar", True))
                    self._estado = (
                        "reconectando" if reconectar else "desconectado_error"
                    )

                self._registrar_evento(
                    f"Desconexion USB detectada en {cfg['puerto']}: {exc}",
                    direccion="SYS",
                    nivel_forzado="WARN" if reconectar else "ERROR",
                )
                if not reconectar:
                    break

    def desconectar(self) -> dict[str, Any]:
        """Cierra de manera limpia la sesion serial y detiene hilos lectores."""
        with self._lock:
            stop_ev = self._stop_event
            stop_ev.set()
            hilo = self._hilo_lector
            self._hilo_lector = None
            estaba_activo = self._conectado or self._estado == "reconectando"
            puerto = self._config.get("puerto", "VIRTUAL")
            self._sesion_id = ""
            self._conectado = False
            self._estado = "desconectado"

        self._cerrar_handle_actual()
        if (
            hilo is not None
            and hilo.is_alive()
            and hilo is not threading.current_thread()
        ):
            hilo.join(timeout=1.0)
        self._cerrar_handle_actual()

        if estaba_activo:
            self._registrar_evento(
                f"Sesion serial cerrada en {puerto}.",
                direccion="SYS",
                nivel_forzado="INFO",
            )
        self.sincronizar_persistencia()
        return self.obtener_estado()

    def enviar(self, datos: str, agregar_salto_linea: bool = True) -> dict[str, Any]:
        """Envia un comando al dispositivo conectado o al emulador ESP32."""
        with self._lock:
            conectado = self._conectado
            modo = self._config.get("modo", "emulado")
            handle = self._serial_handle

        if not conectado:
            raise HTTPException(
                status_code=409,
                detail="El Monitor Serie no esta conectado.",
            )

        carga = datos if not agregar_salto_linea else f"{datos.rstrip()}\r\n"

        if modo == "fisico":
            if handle is None:
                raise HTTPException(
                    status_code=503,
                    detail="Descriptor de puerto serie no disponible.",
                )
            try:
                with self._tx_lock:
                    bytes_escritos = handle.write(carga.encode("utf-8"))
                    handle.flush()
            except (
                serial.SerialException,
                OSError,
                TypeError,
                AttributeError,
            ) as exc:
                self._cerrar_handle_actual(esperado=handle)
                with self._lock:
                    reconectar = bool(self._config.get("auto_reconectar", True))
                    self._conectado = False
                    self._estado = (
                        "reconectando" if reconectar else "desconectado_error"
                    )
                    self._ultimo_error = str(exc)
                raise HTTPException(
                    status_code=503,
                    detail=f"Error al escribir en el puerto serie: {exc}",
                ) from exc
        else:
            bytes_escritos = len(carga.encode("utf-8"))

        ev_tx = self._registrar_evento(
            datos.strip(), direccion="TX", nivel_forzado="INFO"
        )

        if modo == "emulado":
            self._responder_comando_emulado(datos.strip())

        return {
            "enviado": True,
            "bytes_escritos": bytes_escritos,
            "evento_tx": ev_tx,
        }

    def _responder_comando_emulado(self, comando: str) -> None:
        cmd = comando.upper()
        if cmd == "AT":
            self._registrar_evento("OK", direccion="RX")
            return
        if cmd in ("STATUS", "INFO"):
            self._registrar_evento(
                "I (1200) ESP32S3: heap=286720,temp:35.8,volt:3.31",
                direccion="RX",
            )
            return
        if cmd in ("PLOT", "SENSOR", "MUESTRA"):
            for _ in range(4):
                self._paso_onda += 1
                angulo = self._paso_onda * 0.45
                temp = round(26.5 + 3.2 * math.sin(angulo), 2)
                hum = round(58.0 + 6.5 * math.cos(angulo * 0.7), 2)
                volt = round(3.30 + 0.04 * math.sin(angulo * 1.3), 3)
                self._registrar_evento(
                    f"I ({1000 + self._paso_onda * 100}) ESP32S3: temp:{temp},hum:{hum},volt:{volt}",
                    direccion="RX",
                )
            return
        if cmd == "ERROR_TEST":
            self._registrar_evento(
                "E (1500) ESP32S3: Fallo simulado en lectura de periferico I2C",
                direccion="RX",
            )
            return
        self._registrar_evento(
            f"I (1300) ESP32S3: eco='{comando}'",
            direccion="RX",
        )

    def limpiar_eventos(self) -> dict[str, Any]:
        """Vacia el buffer circular activo de la sesion."""
        with self._lock:
            eliminados = len(self._eventos)
            self._eventos.clear()
        return {"limpiado": True, "eventos_eliminados": eliminados}

    def obtener_estado(self) -> dict[str, Any]:
        """Devuelve el estado actual de la conexion serial."""
        with self._lock:
            return {
                "conectado": self._conectado,
                "estado": self._estado,
                "sesion_id": self._sesion_id,
                "puerto": self._config["puerto"],
                "baudrate": self._config["baudrate"],
                "databits": self._config["databits"],
                "stopbits": self._config["stopbits"],
                "parity": self._config["parity"],
                "modo": self._config["modo"],
                "auto_reconectar": self._config["auto_reconectar"],
                "ultimo_seq": self._seq,
                "eventos_en_memoria": len(self._eventos),
                "ultimo_error": self._ultimo_error,
                "baudrates_soportados": BAUDRATES_SOPORTADOS,
            }

    def obtener_eventos(
        self,
        desde_seq: int = 0,
        nivel: Optional[str] = None,
        buscar: Optional[str] = None,
        regex: Optional[str] = None,
        limite: int = 500,
    ) -> dict[str, Any]:
        """Obtiene eventos seriales filtrados a partir de un cursor incremental."""
        patron_re = compilar_filtro_regex(regex)
        with self._lock:
            instantanea = list(self._eventos)
            ultimo_seq = self._seq

        filtrados = [
            ev
            for ev in instantanea
            if int(ev["seq"]) > desde_seq
            and evento_cumple_filtros(
                ev, nivel=nivel, buscar=buscar, patron_re=patron_re
            )
        ]
        if limite > 0 and len(filtrados) > limite:
            filtrados = filtrados[-limite:]

        return {
            "total": len(filtrados),
            "ultimo_seq": ultimo_seq,
            "estado": self.obtener_estado(),
            "eventos": filtrados,
        }

    def obtener_muestras_plotter(
        self,
        desde_seq: int = 0,
        ventana: int = 120,
    ) -> dict[str, Any]:
        """Retorna las muestras numericas multicanal listas para graficar."""
        with self._lock:
            instantanea = list(self._eventos)
            ultimo_seq = self._seq

        muestras: list[dict[str, Any]] = []
        canales_set: list[str] = []
        for ev in instantanea:
            canales = ev.get("canales") or {}
            if not canales:
                continue
            for nombre_canal in canales.keys():
                if nombre_canal not in canales_set:
                    canales_set.append(nombre_canal)
            if int(ev["seq"]) > desde_seq:
                muestras.append(
                    {
                        "seq": ev["seq"],
                        "fecha": ev["fecha"],
                        "canales": canales,
                    }
                )

        if ventana > 0 and len(muestras) > ventana:
            muestras = muestras[-ventana:]

        return {
            "total_muestras": len(muestras),
            "ultimo_seq": ultimo_seq,
            "canales_disponibles": canales_set,
            "muestras": muestras,
        }


gestor_monitor_global = GestorMonitorSerie()


def conectar_monitor_serie(solicitud: SolicitudConectarMonitor) -> dict[str, Any]:
    """POST /api/v1/herramientas/monitor-serie/conectar."""
    return gestor_monitor_global.conectar(
        puerto=solicitud.puerto,
        baudrate=solicitud.baudrate,
        databits=solicitud.databits,
        stopbits=solicitud.stopbits,
        parity=solicitud.parity,
        modo=solicitud.modo,
        auto_reconectar=solicitud.auto_reconectar,
    )


def desconectar_monitor_serie() -> dict[str, Any]:
    """POST /api/v1/herramientas/monitor-serie/desconectar."""
    return gestor_monitor_global.desconectar()


def estado_monitor_serie() -> dict[str, Any]:
    """GET /api/v1/herramientas/monitor-serie/estado."""
    return gestor_monitor_global.obtener_estado()


def enviar_monitor_serie(solicitud: SolicitudEnviarSerial) -> dict[str, Any]:
    """POST /api/v1/herramientas/monitor-serie/enviar."""
    return gestor_monitor_global.enviar(
        datos=solicitud.datos,
        agregar_salto_linea=solicitud.agregar_salto_linea,
    )


def listar_eventos_monitor_serie(
    desde_seq: int = Query(default=0, ge=0),
    nivel: Optional[str] = Query(default=None),
    buscar: Optional[str] = Query(default=None),
    regex: Optional[str] = Query(default=None),
    limite: int = Query(default=500, ge=1, le=2000),
) -> dict[str, Any]:
    """GET /api/v1/herramientas/monitor-serie/eventos."""
    return gestor_monitor_global.obtener_eventos(
        desde_seq=desde_seq,
        nivel=nivel,
        buscar=buscar,
        regex=regex,
        limite=limite,
    )


def limpiar_monitor_serie() -> dict[str, Any]:
    """POST /api/v1/herramientas/monitor-serie/limpiar."""
    return gestor_monitor_global.limpiar_eventos()


def parsear_lote_plotter(solicitud: SolicitudParsearPlotter) -> dict[str, Any]:
    """POST /api/v1/herramientas/plotter/parsear."""
    muestras: list[dict[str, Any]] = []
    canales_vistos: list[str] = []
    for idx, linea in enumerate(solicitud.lineas):
        canales = parsear_linea_plotter(linea)
        if canales:
            for c in canales.keys():
                if c not in canales_vistos:
                    canales_vistos.append(c)
            muestras.append({"indice": idx, "linea": linea, "canales": canales})
    return {
        "total_muestras": len(muestras),
        "canales_disponibles": canales_vistos,
        "muestras": muestras,
    }


def obtener_muestras_plotter_endpoint(
    desde_seq: int = Query(default=0, ge=0),
    ventana: int = Query(default=120, ge=1, le=2000),
) -> dict[str, Any]:
    """GET /api/v1/herramientas/plotter/muestras."""
    return gestor_monitor_global.obtener_muestras_plotter(
        desde_seq=desde_seq,
        ventana=ventana,
    )


def _obtener_eventos_para_exportar(
    nivel: Optional[str],
    buscar: Optional[str],
    regex: Optional[str],
    limite: int,
) -> list[dict[str, Any]]:
    """Obtiene eventos en memoria o respaldados en SQLite aplicando los filtros solicitados."""
    patron_re = compilar_filtro_regex(regex)
    en_memoria = gestor_monitor_global.obtener_eventos(
        desde_seq=0,
        nivel=nivel,
        buscar=buscar,
        regex=regex,
        limite=limite,
    )["eventos"]
    if en_memoria:
        return en_memoria

    gestor_monitor_global.sincronizar_persistencia()
    try:
        filas_bd = ejecutar(
            """
            SELECT id AS seq, fecha, puerto, baudrate, direccion, nivel, linea, canales_json
            FROM herramientas_eventos_serie
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        )
    except Exception:
        filas_bd = []

    eventos_bd: list[dict[str, Any]] = []
    for fila in reversed(filas_bd):
        canales_raw = fila.get("canales_json")
        try:
            canales = json.loads(canales_raw) if canales_raw else {}
        except (ValueError, TypeError):
            canales = {}
        ev = {
            "seq": fila.get("seq", 0),
            "fecha": fila.get("fecha", ""),
            "puerto": fila.get("puerto", ""),
            "baudrate": fila.get("baudrate", 115200),
            "direccion": fila.get("direccion", "RX"),
            "nivel": fila.get("nivel", "INFO"),
            "linea": fila.get("linea", ""),
            "canales": canales,
        }
        if evento_cumple_filtros(ev, nivel=nivel, buscar=buscar, patron_re=patron_re):
            eventos_bd.append(ev)
    return eventos_bd


def exportar_logs_herramientas(
    formato: Literal["csv", "txt", "json"] = Query(default="txt"),
    nivel: Optional[str] = Query(default=None),
    buscar: Optional[str] = Query(default=None),
    regex: Optional[str] = Query(default=None),
    limite: int = Query(default=1000, ge=1, le=5000),
) -> Response:
    """GET /api/v1/herramientas/logs/exportar?formato=csv|txt|json."""
    eventos = _obtener_eventos_para_exportar(
        nivel=nivel,
        buscar=buscar,
        regex=regex,
        limite=limite,
    )
    marca = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if formato == "csv":
        salida_csv = io.StringIO()
        escritor = csv.writer(salida_csv, lineterminator="\n")
        escritor.writerow(
            [
                "seq",
                "fecha",
                "puerto",
                "baudrate",
                "direccion",
                "nivel",
                "linea",
                "canales_json",
            ]
        )
        for ev in eventos:
            escritor.writerow(
                [
                    ev.get("seq", ""),
                    ev.get("fecha", ""),
                    ev.get("puerto", ""),
                    ev.get("baudrate", ""),
                    ev.get("direccion", ""),
                    ev.get("nivel", ""),
                    ev.get("linea", ""),
                    json.dumps(ev.get("canales") or {}, ensure_ascii=False),
                ]
            )
        return Response(
            content=salida_csv.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="monitor_serie_{marca}.csv"'
            },
        )

    if formato == "json":
        cuerpo_json = json.dumps(
            {
                "exportado_en": datetime.now(timezone.utc).isoformat(),
                "total": len(eventos),
                "eventos": eventos,
            },
            ensure_ascii=False,
            indent=2,
        )
        return Response(
            content=cuerpo_json,
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="monitor_serie_{marca}.json"'
            },
        )

    lineas_txt = [
        f"[{ev.get('fecha', '')}] [{ev.get('puerto', '')}@{ev.get('baudrate', '')}] "
        f"[{ev.get('direccion', 'RX')}] [{ev.get('nivel', 'INFO')}] {ev.get('linea', '')}"
        for ev in eventos
    ]
    return Response(
        content="\n".join(lineas_txt) + ("\n" if lineas_txt else ""),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="monitor_serie_{marca}.txt"'
        },
    )


async def monitor_serie_ws(
    websocket: WebSocket,
    puerto: Optional[str] = Query(default=None),
    baudrate: int = Query(default=115200),
    databits: int = Query(default=8),
    stopbits: float = Query(default=1.0),
    parity: str = Query(default="N"),
    modo: str = Query(default="auto"),
    auto_reconectar: bool = Query(default=True),
    nivel: Optional[str] = Query(default=None),
    buscar: Optional[str] = Query(default=None),
    regex: Optional[str] = Query(default=None),
) -> None:
    """WS /api/v1/herramientas/monitor-serie/stream — Puente WebSocket bidireccional."""
    await websocket.accept()
    try:
        patron_re = compilar_filtro_regex(regex)
    except HTTPException as exc:
        await websocket.send_json({"tipo": "error", "detalle": exc.detail})
        await websocket.close(code=1008)
        return

    estado_actual = gestor_monitor_global.obtener_estado()
    if puerto and (not estado_actual["conectado"] or estado_actual["puerto"] != puerto):
        try:
            estado_actual = await asyncio.to_thread(
                gestor_monitor_global.conectar,
                puerto=puerto,
                baudrate=baudrate,
                databits=databits,
                stopbits=stopbits,
                parity=parity,
                modo=modo,
                auto_reconectar=auto_reconectar,
            )
        except HTTPException as exc:
            await websocket.send_json({"tipo": "error", "detalle": exc.detail})
            await websocket.close(code=1011)
            return

    ultimo_seq = int(estado_actual.get("ultimo_seq", 0))
    await websocket.send_json({"tipo": "estado", "estado": estado_actual})

    try:
        while True:
            lote = gestor_monitor_global.obtener_eventos(
                desde_seq=ultimo_seq, limite=200
            )
            for ev in lote["eventos"]:
                ultimo_seq = max(ultimo_seq, int(ev["seq"]))
                if evento_cumple_filtros(
                    ev, nivel=nivel, buscar=buscar, patron_re=patron_re
                ):
                    await websocket.send_json({"tipo": "evento", "evento": ev})

            try:
                mensaje_entrante = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.05,
                )
            except asyncio.TimeoutError:
                continue

            if not mensaje_entrante:
                continue

            try:
                comando_json = json.loads(mensaje_entrante)
            except ValueError:
                comando_json = {"accion": "enviar", "datos": mensaje_entrante}

            accion = str(comando_json.get("accion", "enviar")).lower()
            if accion == "desconectar":
                nuevo_estado = await asyncio.to_thread(
                    gestor_monitor_global.desconectar
                )
                await websocket.send_json({"tipo": "estado", "estado": nuevo_estado})
                break
            if accion == "estado":
                await websocket.send_json(
                    {"tipo": "estado", "estado": gestor_monitor_global.obtener_estado()}
                )
            elif accion == "enviar":
                datos_tx = str(comando_json.get("datos", ""))
                if datos_tx:
                    try:
                        await asyncio.to_thread(gestor_monitor_global.enviar, datos_tx)
                    except HTTPException as exc:
                        await websocket.send_json(
                            {
                                "tipo": "error",
                                "codigo": exc.status_code,
                                "detalle": exc.detail,
                            }
                        )
    except WebSocketDisconnect:
        return
