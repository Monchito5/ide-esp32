# Archivo: modules/simulacion/backend/simulacion_backend/application/simulacion_service.py
"""Servicio de aplicacion para el modulo de simulacion ESP32."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from simulacion_backend.application.simulacion_session import SimulacionSession


class SimulacionService:
    """Servicio de aplicacion para gestionar sesiones de simulacion ESP32."""

    def __init__(self) -> None:
        self._sesiones: Dict[str, SimulacionSession] = {}
        self._websockets: Dict[str, List[Any]] = {}

    def listar_motores(self) -> List[dict]:
        """Lista los motores de simulacion disponibles."""
        return [
            {
                "id": "esp_emulator",
                "nombre": "ESP Emulator",
                "version": "1.0.0",
                "soporta_wasm": True,
                "soporta_cli": True,
                "chips_soportados": ["ESP32-S3", "ESP32", "ESP32-C3"],
                "descripcion": "Emulador oficial de Espressif para ESP32",
            },
            {
                "id": "qemu",
                "nombre": "QEMU",
                "version": "opcional",
                "soporta_wasm": False,
                "soporta_cli": True,
                "chips_soportados": ["ESP32-S3"],
                "descripcion": "QEMU de Espressif (adaptador opcional)",
            },
        ]

    def listar_chips(self) -> List[dict]:
        """Lista los chips ESP32 soportados para simulacion."""
        return [
            {
                "id": "ESP32-S3",
                "nombre": "ESP32-S3",
                "arquitectura": "Xtensa Dual-Core 32-bit LX7",
                "frecuencia_mhz": 240,
                "flash_mb": 16,
                "psram_mb": 8,
                "motores_soportados": ["esp_emulator"],
            },
            {
                "id": "ESP32",
                "nombre": "ESP32",
                "arquitectura": "Xtensa Dual-Core 32-bit LX6",
                "frecuencia_mhz": 240,
                "flash_mb": 4,
                "psram_mb": 0,
                "motores_soportados": ["esp_emulator"],
            },
            {
                "id": "ESP32-C3",
                "nombre": "ESP32-C3",
                "arquitectura": "RISC-V Single-Core 32-bit",
                "frecuencia_mhz": 160,
                "flash_mb": 4,
                "psram_mb": 0,
                "motores_soportados": ["esp_emulator"],
            },
        ]

    def listar_sesiones(self) -> List[dict]:
        """Lista todas las sesiones de simulacion."""
        return [s.obtener_estado() for s in self._sesiones.values()]

    def obtener_sesion(self, sesion_id: str) -> Optional[dict]:
        """Obtiene el estado de una sesion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            return None
        return sesion.obtener_estado()

    def obtener_estado_sesion(self, sesion_id: str) -> Optional[dict]:
        """Obtiene el estado actual de una sesion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            return None
        return sesion.obtener_estado()

    def crear_sesion(self, datos_sesion: dict) -> dict:
        """Crea una nueva sesion de simulacion."""
        chip = datos_sesion.get("chip", "ESP32-S3")
        motor = datos_sesion.get("motor", "esp_emulator")
        nombre = datos_sesion.get("nombre", f"Sesion-{chip}")

        chips = {c["id"]: c for c in self.listar_chips()}
        if chip not in chips:
            raise ValueError(f"Chip no soportado: {chip}")

        motores_disponibles = chips[chip]["motores_soportados"]
        if motor not in motores_disponibles:
            raise ValueError(
                f"Motor '{motor}' no soportado para chip '{chip}'. "
                f"Motores disponibles: {motores_disponibles}"
            )

        sesion_id = datos_sesion.get("sesion_id") or f"sesion-{uuid.uuid4().hex[:8]}"

        if sesion_id in self._sesiones:
            raise ValueError(f"Ya existe una sesion con el ID: {sesion_id}")

        sesion = SimulacionSession(
            sesion_id=sesion_id,
            nombre=nombre,
            chip=chip,
            motor=motor,
        )
        self._sesiones[sesion_id] = sesion
        self._websockets[sesion_id] = []

        return sesion.obtener_estado()

    def iniciar_sesion(self, sesion_id: str) -> dict:
        """Inicia la simulacion de una sesion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.iniciar()

    def detener_sesion(self, sesion_id: str) -> dict:
        """Detiene la simulacion de una sesion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.detener()

    def reiniciar_sesion(self, sesion_id: str) -> dict:
        """Reinicia la simulacion de una sesion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.reiniciar()

    def flashear_sesion(self, sesion_id: str, datos_flasheo: dict) -> dict:
        """Flashea firmware en una sesion de simulacion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.flashear(datos_flasheo)

    def enviar_comando(self, sesion_id: str, datos_comando: dict) -> dict:
        """Envia un comando UART a una sesion de simulacion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.enviar_comando(datos_comando)

    def agregar_componente(self, sesion_id: str, datos_componente: dict) -> dict:
        """Agrega un componente virtual a una sesion de simulacion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.agregar_componente(datos_componente)

    def obtener_reporte(self, sesion_id: str) -> dict:
        """Obtiene el reporte de una sesion de simulacion."""
        sesion = self._sesiones.get(sesion_id)
        if not sesion:
            raise KeyError(f"Sesion no encontrada: {sesion_id}")
        return sesion.obtener_reporte()

    async def conectar_websocket(self, sesion_id: str, websocket: Any) -> None:
        """Registra un WebSocket para una sesion."""
        if sesion_id not in self._websockets:
            self._websockets[sesion_id] = []
        self._websockets[sesion_id].append(websocket)

    async def desconectar_websocket(self, sesion_id: str, websocket: Any) -> None:
        """Desregistra un WebSocket de una sesion."""
        if sesion_id in self._websockets:
            try:
                self._websockets[sesion_id].remove(websocket)
            except ValueError:
                pass

    async def notificar_evento(self, sesion_id: str, evento: dict) -> None:
        """Notifica un evento a todos los WebSockets conectados a una sesion."""
        websockets = self._websockets.get(sesion_id, [])
        desconectados: List[Any] = []
        for ws in websockets:
            try:
                await ws.send_json(evento)
            except Exception:
                desconectados.append(ws)
        for ws in desconectados:
            try:
                websockets.remove(ws)
            except ValueError:
                pass
