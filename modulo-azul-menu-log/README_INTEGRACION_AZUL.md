# Equipo Azul — Flutter + FastAPI, monorepo IDE ESP32 v6.0

Este paquete es un **overlay** para copiar dentro del repositorio existente. No sustituye el shell del Equipo Gris ni implementa el compilador ESP-IDF de Sketch. La integración final con los registradores reales no se puede validar sin el código fuente actualizado del monorepo.

## Archivos

- `modules/azul/frontend/lib/panel_azul.dart`: menú y Log Flutter, navegación por callback, polling de mensajes y trabajos.
- `modules/azul/backend/azul_backend/modulo.py`: API FastAPI, mensajes y trabajos de compilación en segundo plano.
- `shared/contratos/azul/compilacion.schema.json`: contrato de respuesta Sketch.
- `sql/02_schema_azul.sql`: esquema **opcional** de persistencia futura, no utilizado actualmente.

## Conectar al backend existente

En el registrador central del backend (no crear otro FastAPI):

```python
from azul_backend.modulo import registrar
from sketch_backend import compilar  # EJEMPLO: reemplazar por import real del equipo Sketch

registrar(app, compile_adapter=compilar)
```

La función `compilar(ruta: str, publicar: Callable[[str, str], None]) -> dict` debe publicar mensajes mediante `publicar(mensaje, nivel)` y devolver `{"success": bool, "errors": [str], "artifacts": [str], "exit_code": int | None}`. **El import y la función Sketch son ilustrativos, no existen en este paquete.** Si no se conecta un adaptador, POST `/api/v1/azul/compile` responde 503.

Para instalar el módulo backend, el registrador de paquetes del monorepo debe incluir la carpeta `modules/azul/backend` en su Python path o empaquetarlo según las convenciones de `docs/desarrollo/CONVENCES_CODIGO.md`. Añadir el nombre al listado `MODULOS_REGISTRADOS` (o su equivalente real) y registrar el módulo según el cargador existente. No agregar `__init__.py` si las reglas del monorepo lo prohíben.

Definir `ESP32_PROJECTS_ROOT` con la ruta de la carpeta autorizada de proyectos **en el servidor backend**. Las rutas fuera de esta carpeta se rechazan. Ejemplo PowerShell: `$env:ESP32_PROJECTS_ROOT="C:\\ESP32\\proyectos"`.

## Conectar al frontend existente

Asegurarse de que `http` esté en `apps/ide/pubspec.yaml`. Integrar el widget en la shell existente:

```dart
PanelAzul(
  apiBase: Uri.parse('http://127.0.0.1:8000/'),
  onNavigate: (seccion) => navegarConRegistroCentral(seccion), // adaptar al shell real
)
```

El contrato exacto de `ModuloIde` y el archivo de registro central deben consultarse en el repositorio. El widget no implementa esa interfaz porque no tenemos su firma real. Evitar duplicar el menú global del Equipo Gris: si ya existe, montar solamente el Log o adaptar el menú a su sistema de navegación.

## Endpoints

- `POST /api/v1/azul/logs` `{ "level":"INFO", "message":"...", "source":"sketch" }`
- `GET /api/v1/azul/logs?after_id=0` obtiene eventos nuevos
- `POST /api/v1/azul/compile` `{ "project_path":"C:\\ESP32\\proyectos\\demo" }` devuelve 202 con `job_id`
- `GET /api/v1/azul/compile/{job_id}` devuelve `queued`, `running`, `completed` o `failed` y el resultado final

El frontend consulta mensajes y estado cada dos segundos. Los trabajos de compilación se ejecutan en un hilo separado. **No se probó contra ESP-IDF real ni contra la aplicación oficial**.

## Restricciones antes de producción

La API no tiene autenticación, los registros y trabajos son en memoria, no se limpian trabajos antiguos y el backend debe configurar CORS para Flutter Web. No exponer estos endpoints en una red sin autenticación y controles de acceso. Si Sketch usa código bloqueante, el hilo separado evita bloquear la API, pero deben controlar concurrencia y cancelación. Los artefactos devueltos son rutas, no descargas automáticas.
