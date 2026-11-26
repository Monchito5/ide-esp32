# Integración de PRs Pre-Sprint 3

**Objetivo**: Integrar todas las ramas remotas pendientes en develop, resolver conflictos, corregir violaciones de convención, y preparar el repo para Sprint 3.
**Rama**: `develop` (target), feature branches (source)
**Estrategia**: single-pr (develop → main al final)
**Runner**: `pytest pruebas/ -v` (backend), `flutter test` (frontend)
**Forecast**: ~200 authored changed lines (mostly merge conflict resolutions + fixes)

## Specs

- S1: Mergear `feature/ayuda-integracion` → `develop` sin conflictos. Restaura `url_launcher` y links funcionales en Ayuda.
- S2: Eliminar los 4 archivos `__init__.py` de `feature/sprint-02` (`simulacion_backend/__init__.py`, `application/__init__.py`, `controllers/__init__.py`, `infrastructure/__init__.py`) y mergear → `develop`. Resolver conflicto en `simulation_controls.dart`.
- S3: Corregir imports de `herramientas/routes.py`: cambiar `from modules.herramientas.backend.herramientas_backend.controllers...` a `from herramientas_backend.controllers...`. Igual para `puerto.py`.
- S4: Crear PR `develop` → `main` consolidando Sprint 1+2.
- S5: Rebase `feature/modulo-sketch` sobre `develop`. Resolver conflicto en `constants.py`.
- S6: Rebase `feature/modulo-editor-equipo-rojo` sobre `develop`. Resolver conflictos en `registro_modulos.dart`, `pubspec.yaml`, `constants.py`.
- S7: Reestructurar `feature/modulo-azul-menu-log`: mover archivos de `modulo-azul-menu-log/modules/azul/...` a `modules/azul/...`. Eliminar archivos de empaquetado.
- S8: Agregar `shared/contratos/archivo/api_v1.json` y `sql/07_schema_archivo.sql`.
- S9: Actualizar CI: `.github/workflows/ci-python.yml` y `ci-dart.yml` para incluir Archivo, Simulación, Ayuda.
- S10: Eliminar ramas obsoletas: `feature/ayuda`, `archivo-sprint01`.

## Tasks

- T1 [S1] inline — merge ayuda-integracion → develop — done (99ecf43)
- T2 [S2] inline — clean __init__.py + merge sprint-02 → develop — done (11f68ae)
- T3 [S3] inline — fix herramientas imports — done (d0618c5)
- T4 [S4] inline — PR develop → main — ready (awaiting push authorization)
- T5 [S5] inline — rebase sketch over develop — done (c7f16ee)
- T6 [S6] inline — rebase editor over develop — done (a607bdd)
- T7 [S7] inline — restructure azul module — done (24810b1)
- T8 [S8] inline — add Archivo contract + SQL — done (ccc89df)
- T9 [S9] inline — update CI workflows — done (ccc89df)
- T10 [S10] inline — delete obsolete branches — done

## Log

- L1: "Requiero que revises las pull request remotas de Github con el objetivo de realizar su correcta integración (el proyecto ya tiene su estructura) en sus respectivas ramas de acuerdo con las reglas de convención de trabajo colaborativo en Github y buenas prácticas de Git, y así como también analizar la situación actual del proyecto, se necesita crear un plan integral y detallado acerca de la construcción y validación del resto de sprints (hasta el sprint 6). También se requiere una auditoria a los módulos existentes [...] Cualquier instalación externa o validación, preguntar primero y hacerlo según la confirmación."
- L2 (2026-11-25): Plan aprobado por usuario. Inicio de ejecución.
- L3 (2026-11-25): T1 completado (ayuda-integracion integrada). T2 completado (removidos 4 __init__.py y mergeado sprint-02). T3 completado (corregidos imports en herramientas/routes.py, arduino.py y puerto.py). T5 completado (rebase de sketch sobre develop, resuelto conflicto en constants.py). T6 completado (rebase de editor sobre develop, resueltos 3 conflictos). T7 completado (reestructurado modulo azul de modulo-azul-menu-log/ a modules/azul/, pyproject.toml y pubspec.yaml creados, tests unitarios agregados). T8 y T9 completados (contrato JSON y schema SQL agregados para Archivo, CI actualizado para Python y Dart). T10 completado (ramas locales obsoletas eliminadas). Suite completa de 43 pruebas en backend pasando al 100%. Develop listo para push y PR a main.
