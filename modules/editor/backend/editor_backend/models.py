# Archivo: modules/editor/backend/editor_backend/models.py
"""Modelos de dominio del modulo Editor (Equipo Rojo)."""

from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class ConfiguracionEditor:
    """Configuración del editor de código."""

    tamanio_fuente: int = 14
    tamanio_tabulacion: int = 2
    usar_espacios: bool = True
    resaltado_sintaxis: bool = True
    auto_formato_guardar: bool = False
    tema_editor: str = "monokai"

    def a_dict(self) -> dict:
        return asdict(self)


@dataclass
class CoincidenciaArchivo:
    """Representa una coincidencia de búsqueda dentro de un archivo."""

    archivo: str
    linea: int
    columna: int
    texto_linea: str

    def a_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResultadoBusquedaArchivos:
    """Resumen de resultados de búsqueda sobre múltiples archivos."""

    termino: str
    total_coincidencias: int = 0
    archivos_afectados: int = 0
    coincidencias: List[dict] = field(default_factory=list)

    def a_dict(self) -> dict:
        return asdict(self)
