# Sprint 6 — Integración de PRs Pendientes, Renombrado `menu-log`, Pruebas Completas y Validación E2E

**Objetivo**: Corregir anomalías reales detectadas en `COM3`, renombrar `azul` -> `menu-log`, integrar selectivamente los PRs abiertos (`#7` `archivo-sprint02`, `#6` `feature/modulo-sketch` y cierre limpio de `#5`), completar las suites unitarias/integración/E2E (flujo 1–7) con cobertura >= 70% y validar CI completo.
**Rama**: `develop` | **Estrategia**: `work-unit-commits` (autorizado por el usuario) | **Runners**: `pytest --cov` y `flutter test`
**Forecast**: ~1200 authored changed lines | **Engram mirror**: `pending` (`ide-esp32` sin sesión registrada en el proceso Engram)

## Specs

- S1: Resolución de anomalías en logs reales `COM3` y endurecimiento de concurrencia (`monitor_serie.py`, `panel_monitor_serie.dart`, `panel_plotter_serie.dart`): soporte de formato ESP32 HAL/Arduino (`[1203297][W][STA.cpp:137]` -> `WARN`), validación gramatical de línea completa en `parsear_linea_plotter` (evitando canales espurios como `{"Reason": 201.0}` o `clock div:1`), hidratación de estado entre pestañas y eliminación de `409 Conflict` desde Plotter, y cola asíncrona por lotes (`executemany`) hacia SQLite.
- S2: Renombrado completo `azul` -> `menu-log` (`modules/menu-log`, `menu_log_backend`, `menu_log_ui`, `/api/v1/menu-log`, `08_schema_menu_log.sql`, `shared/contratos/menu-log/`).
- S3: Integración limpia de PRs remotos abiertos (`#7` `FileManager` y nuevos endpoints en `archivo_backend` + `api_archivo.dart` excluyendo archivos truncados/Tkinter; `#6` explorador de archivos, exportación de `.bin` y `sketch_ui` sin perder `/compilar-codigo`; `#5` cerrado/integrado bajo `menu-log`).
- S4: Suite completa de pruebas unitarias e integración backend (`S6-01` `test_archivo.py`, `S6-02` `test_simulacion_endpoints_s6.py`, `S6-03` `test_editor_api_s6.py`, `S6-04` `test_archivos.py` + `test_exportacion.py`, `S6-05` `test_sprint05_monitor_plotter_logs.py`, `S6-06` `test_flujo_completo_e2e.py` flujo 1–7, `S6-07` `test_registro_modulos_pep420.py`) con cobertura `>= 70%` (`71.61%` observado, `S6-09`).
- S5: Suite de widgets y smoke test Flutter (`S6-08`, `S6-11`: `sprint06_modulos_e2e_test.dart`, `9/9` verde) + workflows CI Python y Dart actualizados para todos los módulos (`S6-10`) + validación en placa física `ESP32-S3` (`COM3`, MAC `DC:B4:D9:14:57:2C`).

## Tasks

- T1 [S1, S2] inline — Corrección de anomalías `COM3`, persistencia SQLite por lotes y renombrado `azul` -> `menu-log` — done
- T2 [S3] inline — Integración quirúrgica de PR `#6` (`feature/modulo-sketch`), PR `#7` (`archivo-sprint02`) y PR `#5` (`menu-log`) — done
- T3 [S4, S5] inline — Pruebas unitarias (`Archivo`, `Editor`, `Simulación`, `Sketch`), integración E2E (pasos 1–7 + PEP 420), widgets Flutter (`9/9`), cobertura `71.61%` (`>= 70%`), CI y prueba en vivo `COM3` (`ESP32-S3 DevKitC-1`, `DC:B4:D9:14:57:2C`) — done

## Log

- L1: "Lo autorizo, y añado tareas prioritarias pendientes por hacer: 1. Resolver los conflictos de riesgo que has encontrado (4)... 2. Revisar PR de ramas remotas en Github... 2.1 (Extra): Renombrar 'azul' pues el nombre de este módulo no es el color del equipo sino 'menu-log' 3. Analizar y solucionar el comportamiento anormal de los siguientes logs... Continuar con el siguiente paso natural según el artefacto del Plan Integral."
- L2 (2026-11-27): Completados T1, T2 y T3: `92/92` pruebas Python en verde (`71.61%` cobertura), `9/9` pruebas Flutter en verde (`0` avisos en `flutter analyze`), `0` archivos `__init__.py`, y validación en hardware real sobre `COM3` (`ESP32-S3 DevKitC-1`, `DC:B4:D9:14:57:2C`, boot ROM `esp32s3-20210327` sin canales falsos).
