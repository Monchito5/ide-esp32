# Archivo: modules/editor/backend/editor_backend/controllers/config_controller.py
"""Controlador para la persistencia de configuraciones del editor."""

from editor_backend.models import ConfiguracionEditor

_configuracion_actual = ConfiguracionEditor()


def obtener_configuracion() -> dict:
    """Devuelve la configuración actual del editor."""
    return _configuracion_actual.a_dict()


def actualizar_configuracion(nuevos_valores: dict) -> dict:
    """Actualiza los valores de configuración del editor."""
    global _configuracion_actual

    if "tamanio_fuente" in nuevos_valores:
        # Respetar límites seguros de zoom (8px a 36px)
        _configuracion_actual.tamanio_fuente = max(8, min(36, int(nuevos_valores["tamanio_fuente"])))
    if "tamanio_tabulacion" in nuevos_valores:
        _configuracion_actual.tamanio_tabulacion = max(1, min(8, int(nuevos_valores["tamanio_tabulacion"])))
    if "usar_espacios" in nuevos_valores:
        _configuracion_actual.usar_espacios = bool(nuevos_valores["usar_espacios"])
    if "resaltado_sintaxis" in nuevos_valores:
        _configuracion_actual.resaltado_sintaxis = bool(nuevos_valores["resaltado_sintaxis"])
    if "auto_formato_guardar" in nuevos_valores:
        _configuracion_actual.auto_formato_guardar = bool(nuevos_valores["auto_formato_guardar"])
    if "tema_editor" in nuevos_valores:
        _configuracion_actual.tema_editor = str(nuevos_valores["tema_editor"])

    return {"exitoso": True, "configuracion": _configuracion_actual.a_dict()}
