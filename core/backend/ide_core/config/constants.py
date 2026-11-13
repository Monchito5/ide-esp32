# Archivo: core/backend/ide_core/config/constants.py
"""Constantes globales del core del IDE."""

from pathlib import Path

# Identidad del IDE
TITULO_IDE = "IDE ESP32 - Monorepo"
NOMBRE_CORE = "IDE ESP32 - Core"
VERSION_CORE = "1.0.0"

# Mensajes
MSG_EXITO_DB = "Conexion a la base de datos del IDE establecida."
ERR_FALLO_DB = "No se pudo conectar con la base de datos."

# Rutas (raiz del monorepo)
DIRECTORIO_MONOREPO = Path(__file__).resolve().parents[4]
DIRECTORIO_DATOS = DIRECTORIO_MONOREPO / "datos"
DIRECTORIO_LOGS = DIRECTORIO_MONOREPO / "logs"
RUTA_BD = DIRECTORIO_DATOS / "ide.db"
RUTA_LOG = DIRECTORIO_LOGS / "ide.log"
DIRECTORIO_SQL = DIRECTORIO_MONOREPO / "sql"

# API
HOST_API = "127.0.0.1"
PUERTO_API = 8765
PREFIJO_API = "/api/v1"

# Modulos registrados (lista explicita)
# Agregar aqui cada nuevo modulo backend que deba cargarse.
MODULOS_REGISTRADOS = [
    "herramientas_backend.modulo",
    "sketch_backend.modulo",
]

