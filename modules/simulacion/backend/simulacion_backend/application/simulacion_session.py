# Archivo: modules/simulacion/backend/simulacion_backend/application/simulacion_session.py
"""Modelo de sesion de simulacion ESP32."""

import datetime
from typing import Any, Dict, List, Optional


class SimulacionSession:
    """Representa una sesion de simulacion de placa ESP32."""

    ESTADO_CREADA = "creada"
    ESTADO_INICIADA = "iniciada"
    ESTADO_DETENIDA = "detenida"
    ESTADO_ERROR = "error"

    def __init__(
        self,
        sesion_id: str,
        nombre: str,
        chip: str,
        motor: str,
    ) -> None:
        self.sesion_id = sesion_id
        self.nombre = nombre
        self.chip = chip
        self.motor = motor
        self.estado = self.ESTADO_CREADA
        self.fecha_creacion = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.fecha_ultimo_cambio: Optional[str] = None
        self.firmware_cargado: Optional[str] = None
        self.firmware_version: Optional[str] = None
        self.informacion_chip: Dict[str, Any] = {}
        self.componentes: List[Dict[str, Any]] = []
        self.eventos: List[Dict[str, Any]] = []
        self.uart_entrada: List[str] = []
        self.uart_salida: List[str] = []
        self.errores: List[str] = []

    def obtener_estado(self) -> dict:
        """Devuelve el estado actual de la sesion como diccionario."""
        return {
            "sesion_id": self.sesion_id,
            "nombre": self.nombre,
            "chip": self.chip,
            "motor": self.motor,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion,
            "fecha_ultimo_cambio": self.fecha_ultimo_cambio,
            "firmware_cargado": self.firmware_cargado,
            "firmware_version": self.firmware_version,
            "informacion_chip": self.informacion_chip,
            "componentes": self.componentes,
            "errores": self.errores,
        }

    def _cambiar_estado(self, nuevo_estado: str) -> None:
        """Cambia el estado de la sesion y registra la fecha."""
        self.estado = nuevo_estado
        self.fecha_ultimo_cambio = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _agregar_evento(self, tipo: str, mensaje: str, datos: Optional[dict] = None) -> None:
        """Agrega un evento al historial de la sesion."""
        evento = {
            "tipo": tipo,
            "mensaje": mensaje,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "datos": datos or {},
        }
        self.eventos.append(evento)
        if len(self.eventos) > 100:
            self.eventos = self.eventos[-100:]

    def iniciar(self) -> dict:
        """Inicia la simulacion."""
        if self.estado == self.ESTADO_INICIADA:
            return self.obtener_estado()

        self.informacion_chip = {
            "modelo": self.chip,
            "revision": "v1.2",
            "cristal_mhz": 40,
            "flash_mb": 16,
            "psram_mb": 8,
            "mac": "24:6F:28:A1:B2:C3",
        }

        self._cambiar_estado(self.ESTADO_INICIADA)
        self._agregar_evento("inicio", f"Sesion iniciada con motor {self.motor}")
        return self.obtener_estado()

    def detener(self) -> dict:
        """Detiene la simulacion."""
        if self.estado == self.ESTADO_DETENIDA:
            return self.obtener_estado()

        self._cambiar_estado(self.ESTADO_DETENIDA)
        self._agregar_evento("detencion", "Sesion detenida por el usuario")
        return self.obtener_estado()

    def reiniciar(self) -> dict:
        """Reinicia la simulacion."""
        self.detener()
        return self.iniciar()

    def flashear(self, datos_flasheo: dict) -> dict:
        """Flashea firmware en la sesion."""
        if self.estado != self.ESTADO_INICIADA:
            raise ValueError("La sesion debe estar iniciada para flashear")

        archivo = datos_flasheo.get("archivo", "firmware.bin")
        direccion = datos_flasheo.get("direccion", "0x10000")

        self.firmware_cargado = archivo
        self.firmware_version = datos_flasheo.get("version", "1.0.0")

        self._agregar_evento(
            "flasheo",
            f"Firmware flasheado: {archivo} en direccion {direccion}",
            {"archivo": archivo, "direccion": direccion},
        )
        return self.obtener_estado()

    def enviar_comando(self, datos_comando: dict) -> dict:
        """Envia un comando UART a la sesion."""
        if self.estado != self.ESTADO_INICIADA:
            raise ValueError("La sesion debe estar iniciada para enviar comandos")

        comando = datos_comando.get("comando", "")
        self.uart_entrada.append(comando)

        respuesta = f"OK: {comando}"
        self.uart_salida.append(respuesta)

        self._agregar_evento(
            "comando_uart",
            f"Comando enviado: {comando}",
            {"comando": comando, "respuesta": respuesta},
        )
        return {"comando": comando, "respuesta": respuesta}

    def agregar_componente(self, datos_componente: dict) -> dict:
        """Agrega un componente virtual a la sesion."""
        if self.estado != self.ESTADO_INICIADA:
            raise ValueError("La sesion debe estar iniciada para agregar componentes")

        componente_id = datos_componente.get("id", f"comp-{len(self.componentes) + 1}")
        tipo = datos_componente.get("tipo", "led")
        puerto = datos_componente.get("puerto", "GPIO2")

        componente = {
            "id": componente_id,
            "tipo": tipo,
            "puerto": puerto,
            "estado": "inactivo",
            "valor": 0,
        }
        self.componentes.append(componente)

        self._agregar_evento(
            "componente_agregado",
            f"Componente agregado: {tipo} en {puerto}",
            {"componente_id": componente_id, "tipo": tipo, "puerto": puerto},
        )
        return componente

    def obtener_reporte(self) -> dict:
        """Obtiene el reporte completo de la sesion."""
        return {
            "sesion_id": self.sesion_id,
            "nombre": self.nombre,
            "chip": self.chip,
            "motor": self.motor,
            "estado": self.estado,
            "firmware": {
                "archivo": self.firmware_cargado,
                "version": self.firmware_version,
            },
            "informacion_chip": self.informacion_chip,
            "componentes": self.componentes,
            "estadisticas": {
                "eventos_totales": len(self.eventos),
                "comandos_uart_enviados": len(self.uart_entrada),
                "respuestas_uart_recibidas": len(self.uart_salida),
                "errores": len(self.errores),
            },
            "fecha_creacion": self.fecha_creacion,
            "fecha_ultimo_cambio": self.fecha_ultimo_cambio,
        }
