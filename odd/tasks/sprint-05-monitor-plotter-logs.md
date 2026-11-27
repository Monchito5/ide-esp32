# Sprint 5 — Monitor Serie, Plotter Serie y Exportación de Logs

**Objetivo**: Implementar comunicación serial bidireccional en tiempo real (`pyserial` + WebSocket + REST), filtros por nivel/texto/regex, parser numérico multicanal para el Plotter Serie, manejo resiliente de desconexión/reconexión USB y exportación de logs en CSV, TXT y JSON, con paneles interactivos en Flutter.
**Rama**: `develop` | **Estrategia**: `single-pr` (preguntar antes de commit/push según AGENTS.md) | **Runners**: `pytest` y `flutter test`
**Forecast**: ~850 authored changed lines | **Engram mirror**: `pending` (`ide-esp32` sin sesión registrada en el proceso Engram)

## Specs

- S1: Monitor Serie Backend (`POST /api/v1/herramientas/monitor-serie/conectar`, `POST /api/v1/herramientas/monitor-serie/desconectar`, `GET /api/v1/herramientas/monitor-serie/estado`, `POST /api/v1/herramientas/monitor-serie/enviar`, `GET /api/v1/herramientas/monitor-serie/eventos`, `POST /api/v1/herramientas/monitor-serie/limpiar` y `WS /api/v1/herramientas/monitor-serie/stream`): puente bidireccional sobre `pyserial` y modo virtual/emulado con baudios configurables (`9600`, `19200`, `38400`, `57600`, `74880`, `115200`, `230400`, `460800`, `921600`), `databits`, `stopbits`, `parity` y persistencia SQLite (`sql/10_schema_sprint5_monitor.sql`).
- S2: Filtros del Monitor Serie (`S5-03`): clasificación automática de severidad ESP-IDF/estándar (`INFO`, `WARN`, `ERROR`, `DEBUG`) y filtrado tanto en servidor como en UI por `nivel`, texto libre (`buscar`) y expresión regular segura (`regex`).
- S3: Plotter Serie y Parser Numérico Multicanal (`POST /api/v1/herramientas/plotter/parsear`, `GET /api/v1/herramientas/plotter/muestras`, `S5-04`, `S5-05`): extracción en tiempo real de series numéricas en formatos `clave:valor`, `clave=valor`, `SENSOR:canal:valor`, JSON y columnas numéricas, ignorando texto no numérico, con selección de canales, colores, ventana de muestras y escala Y automática o manual.
- S4: Exportación de Logs (`GET /api/v1/herramientas/logs/exportar?formato=csv|txt|json`, `S5-06`): exportación filtrada de eventos seriales y logs del sistema con cabeceras de descarga apropiadas.
- S5: Reconexión y Desconexión Graceful (`S5-07`): detección limpia de pérdida de puerto USB (`SerialException`/`OSError`), liberación inmediata del descriptor, transición a estado `reconectando` cuando `auto_reconectar=true` y recuperación automática al reconectar el dispositivo sin bloquear el backend.
- S6: Interfaz Flutter (`panel_monitor_serie.dart`, `panel_plotter_serie.dart`, `layout_principal.dart`, `api_herramientas.dart`) + Contratos JSON + Pruebas Unitarias e Integración (`S5-02`, `S5-05`, `S5-08`, `S5-09`): terminal interactiva en `NavigationRail` (`Monitor`, índice 3) y graficador multicanal nativo `CustomPainter` sin dependencias externas (`Plotter`, índice 4), validados con `pytest` y `flutter test`.

## Tasks

- T1 [S1, S2, S3, S4, S5] inline — Esquema SQL `10_schema_sprint5_monitor.sql`, controlador `monitor_serie.py` (sesiones `pyserial`/emuladas, WebSocket `asyncio.to_thread`, filtros anti-ReDoS, parser numérico, reconexión USB sin fugas de descriptores y exportación CSV/TXT/JSON), rutas y contrato JSON — done (6/6 Sprint 5 pytest green)
- T2 [S6] inline — Paneles Flutter (`panel_monitor_serie.dart`, `panel_plotter_serie.dart`), cliente `ApiHerramientas` e integración en `LayoutPrincipal` — done (`flutter analyze` 0 issues)
- T3 [S1, S2, S3, S4, S5, S6] inline — Pruebas unitarias e integración Python (`test_sprint05_monitor_plotter_logs.py`), pruebas de widgets Flutter (`sprint05_monitor_plotter_test.dart`) y verificación independiente de concurrencia (Risk item 4) — done (pendiente confirmación de validación física en ESP32-S3 y commit/push)

## Log

- L1: "Si lo autorizo, puedes continuar con el Sprint 5, actualmente se cuenta con un módulo fisico de esp32 s3 para realizar pruebas."
- L2 (2026-11-27): "Continúa, solo responde lo siguiente ¿es posible evitar las rutas absolutas en el proyecto? ya que la idea es empaquetar para una versión ejecutable en ordenador, otra versión portable  y en web ¿Cómo sería posiblle evitar las rutas absolutas para añadir las dependencias que lo impiden al proyecto?" / "Continúa"
- L3 (2026-11-27): Completados T1, T2 y T3 sin dependencias externas. Aplicado lote correctivo de verificación independiente (Risk item 4 — concurrencia): `stop_event` por sesión y cierre bajo `_lock`, `_tx_lock`, `asyncio.to_thread` en WebSocket, validación anti-ReDoS, guardas `mounted` + chip `DEBUG` en Flutter y contrato `POST /monitor-serie/limpiar`.
