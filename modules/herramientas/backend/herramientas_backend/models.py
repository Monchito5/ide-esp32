# Archivo: modules/herramientas/backend/herramientas_backend/models.py
"""Modelos de dominio del modulo Herramientas - Capa de Dominio.

Entidades de negocio puras con reglas de negocio encapsuladas.
Estos modelos no tienen dependencias de frameworks, APIs o bases de datos.
Sirven como base para las capas superiores y pueden ser testeados aisladamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PuertoSerie:
    """Modelo de dominio que representa un puerto serie detectado."""

    dispositivo: str
    descripcion: str = ""
    fabricante: str = ""
    vid: Optional[int] = None
    pid: Optional[int] = None

    def __repr__(self) -> str:
        return f"PuertoSerie(dispositivo={self.dispositivo!r}, vid={self.vid}, pid={self.pid})"


@dataclass
class ConfiguracionESP32:
    """Modelo de dominio con configuracion basica del ESP32."""

    nombre: str
    version: str = "1.0.0"
    activa: bool = True

    def __repr__(self) -> str:
        return f"ConfiguracionESP32(nombre={self.nombre!r}, version={self.version!r})"


@dataclass
class ConfiguracionIDESxt:
    """Modelo de dominio para configuracion del IDE."""

    titulo: str = "IDE ESP32"
    version: str = "1.0.0"
    host: str = "127.0.0.1"
    puerto: int = 8765

    def __repr__(self) -> str:
        return f"ConfiguracionIDESxt(titulo={self.titulo!r})"


@dataclass
class Herramienta:
    """Entidad base que representa una herramienta del IDE."""

    id: str
    nombre: str
    descripcion: str = ""

    def __repr__(self) -> str:
        return f"Herramienta(id={self.id!r}, nombre={self.nombre!r})"


# Clase Puerto para compatibilidad con controladores existentes
@dataclass
class Puerto:
    """Clase Puerto para compatibilidad con controladores existentes."""

    dispositivo: str
    descripcion: str = ""
    fabricante: str = ""
    vid: Optional[int] = None
    pid: Optional[int] = None

    def a_dict(self) -> dict:
        """Convierte el Puerto a diccionario."""
        return {
            "dispositivo": self.dispositivo,
            "descripcion": self.descripcion,
            "fabricante": self.fabricante,
            "vid": self.vid,
            "pid": self.pid,
        }
