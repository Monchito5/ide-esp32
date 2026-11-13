# Archivo: modules/simulacion/backend/simulacion_backend/schemas.py
"""Esquemas Pydantic para el modulo Simulacion."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChipModelo(BaseModel):
    """Modelo de un chip ESP32 soportado."""

    id: str
    nombre: str
    arquitectura: str
    frecuencia_mhz: int
    flash_mb: int
    psram_mb: int
    motores_soportados: List[str]


class MotorModelo(BaseModel):
    """Modelo de un motor de simulacion."""

    id: str
    nombre: str
    version: str
    soporta_wasm: bool
    soporta_cli: bool
    chips_soportados: List[str]
    descripcion: str


class SesionCrearRequest(BaseModel):
    """Peticion para crear una sesion de simulacion."""

    chip: str = "ESP32-S3"
    motor: str = "esp_emulator"
    nombre: Optional[str] = None
    sesion_id: Optional[str] = None


class SesionRespuesta(BaseModel):
    """Respuesta de una sesion de simulacion."""

    sesion_id: str
    nombre: str
    chip: str
    motor: str
    estado: str
    fecha_creacion: str
    fecha_ultimo_cambio: Optional[str] = None
    firmware_cargado: Optional[str] = None
    firmware_version: Optional[str] = None
    informacion_chip: Dict[str, Any] = {}
    componentes: List[Dict[str, Any]] = []
    errores: List[str] = []


class ComandoUARTRequest(BaseModel):
    """Peticion para enviar un comando UART a una sesion."""

    comando: str


class ComponenteVirtualRequest(BaseModel):
    """Peticion para agregar un componente virtual a una sesion."""

    id: str
    tipo: str
    puerto: str


class FlashearRequest(BaseModel):
    """Peticion para flashear firmware en una sesion."""

    archivo: str
    direccion: str = "0x10000"
    version: Optional[str] = None


class ReporteSesion(BaseModel):
    """Reporte completo de una sesion de simulacion."""

    sesion_id: str
    nombre: str
    chip: str
    motor: str
    estado: str
    firmware: Dict[str, Any]
    informacion_chip: Dict[str, Any]
    componentes: List[Dict[str, Any]]
    estadisticas: Dict[str, Any]
    fecha_creacion: str
    fecha_ultimo_cambio: Optional[str] = None


class EventoWebSocket(BaseModel):
    """Evento enviado por WebSocket a una sesion."""

    tipo: str
    sesion_id: str
    mensaje: str
    timestamp: str
    datos: Optional[Dict[str, Any]] = None
