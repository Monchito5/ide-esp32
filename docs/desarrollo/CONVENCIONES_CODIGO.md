# Convenciones de Código - IDE ESP32 Monorepo

This is the **single source of truth** for code conventions in this repository. Other docs (`README.md`, `AGENTS.md`, `ARQUITECTURA.md`) reference this file instead of duplicating the content.

## Python

- **Formato**: `black` (line-length=100).
- **Imports**: `isort` (perfil black).
- **Estilo**: `pylint` >= 8.0.
- **Imports absolutos con nombre de paquete único**:
  - Core: `from ide_core.x import y`
  - Módulo: `from herramientas_backend.x import y`
- **PROHIBIDO crear `__init__.py`** (namespace packages PEP 420).
- **Punto de entrada público por backend**: archivo `modulo.py` con `def registrar(app: FastAPI) -> None`.
- **Dependencias**: agregar siempre a `requirements.txt` (raíz), nunca crear requirements locales en `core/` ni en `modules/`.

## Dart

- **Formato**: `dart format` + `flutter analyze`.
- **Widgets**: preferentemente `const`.
- **Cada módulo de frontend** expone **una clase pública única** que implementa `ModuloIde` (nombre: `Modulo<Nombre>`).
- **Dependencias de paquetes Dart** de módulos: dependen de `ide_core` vía `path:` (ver `pubspec.yaml`).

## SQL

- Un archivo por módulo: `sql/02_schema_<modulo>.sql`.
- Los prefijos `NN_` determinan el orden de aplicación.

## Referencia Cruzada

Estas convenciones son aplicadas por los siguientes archivos del proyecto:

| Archivo | Secciones/contenido relacionado |
|---------|----------------------------------|
| `README.md` | Sección "Reglas Críticas" (línea 51): referencia a estas convenciones para la regla de sin `__init__.py`, imports absolutamente centralizados y dependencias en `requirements.txt` raíz. |
| `AGENTS.md` | Sección "Critical Conventions" (líneas 43-49): mismas convenciones de PEP 420, imports y dependencias centralizadas, para guía de agentes OpenCode. |
| `ARQUITECTURA.md` | Página 2 (Referencia a Convenciones): indica que las convenciones de código están en `docs/desarrollo/CONVENCIONES_CODIGO.md`. |
| `CONTRIBUIR.md` | Punto 6: para convenciones de código (sin `__init__.py`, imports absolutamente centralizados, black/isort/formato, dependencias en root `requirements.txt`), consultar `docs/desarrollo/CONVENCIONES_CODIGO.md`. |
| `modules/herramientas/README.md` | Estructura y registro de módulos consistente con estas convenciones (imports absolutotes, sin `__init__.py`, dependencias centralizadas). |