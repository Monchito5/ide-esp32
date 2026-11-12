# Archivo: core/backend/ide_core/config/setup.py
"""Arranque del IDE (patron AppConfig)."""

import sys
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ide_core.config.constants import (
    DIRECTORIO_MONOREPO,
    ERR_FALLO_DB,
    HOST_API,
    MSG_EXITO_DB,
    PUERTO_API,
    TITULO_IDE,
    VERSION_CORE,
)
from ide_core.config.registro_modulos import registrar_modulos
from ide_core.config.routes import configurar_rutas_base
from ide_core.db.connection import (
    ErrorConexion,
    aplicar_esquemas_completos,
    get_conn,
    init_pool,
)
from ide_core.utils.logger import log_sistema

# Asegura que los paquetes de modulos y sus backend sean importables
# aunque se ejecute desde core/backend sin una instalacion editable.
# - Raiz del monorepo: permite from modules.herramientas.backend.....
# - modules/*/backend: permite from herramientas_backend.modulo (top-level).
_rutas_modulos = [str(DIRECTORIO_MONOREPO)]
_rutas_modulos.extend(str(p) for p in sorted(DIRECTORIO_MONOREPO.glob("modules/*/backend")))
for _ruta_str in _rutas_modulos:
    if _ruta_str not in sys.path:
        sys.path.insert(0, _ruta_str)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Configuracion y arranque del core del IDE."""

    @classmethod
    def establecer_conexion(cls) -> bool:
        """Establece conexion con la base de datos y aplica esquemas."""
        try:
            init_pool()
            conn = get_conn()
            conn.close()
            aplicar_esquemas_completos()
            log_sistema.info(MSG_EXITO_DB)
            return True
        except ErrorConexion:
            log_sistema.error(ERR_FALLO_DB)
            return False
        except (OSError, RuntimeError) as exc:  # pylint: disable=broad-exception-caught
            log_sistema.exception(exc)
            return False

    @classmethod
    def crear_app(cls) -> FastAPI:
        """Crea y configura la instancia de FastAPI."""
        aplicacion = FastAPI(title=TITULO_IDE, version=VERSION_CORE)
        aplicacion.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        aplicacion.include_router(configurar_rutas_base())
        registrar_modulos(aplicacion)
        return aplicacion

    @classmethod
    def iniciar_app(cls, recargar: bool = False) -> None:
        """Inicia el servidor uvicorn."""
        uvicorn.run(
            "ide_core.config.setup:app_instancia",
            host=HOST_API,
            port=PUERTO_API,
            reload=recargar,
        )


app = AppConfig()
app_instancia = AppConfig.crear_app()
