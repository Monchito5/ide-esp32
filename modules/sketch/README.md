# Modulo Sketch - ESP32

## 1. Descripcion

Sketch es el modulo encargado de gestionar la compilacion de proyectos ESP32 mediante ESP-IDF dentro del IDE.

Su backend se integra con el Core central mediante FastAPI y permite iniciar compilaciones, consultar tareas y revisar el estado general del modulo.

## 2. Arquitectura

- backend/sketch_backend/: logica principal del modulo.
- backend/sketch_backend/controllers/: administracion de compilaciones.
- backend/pruebas/: pruebas automatizadas.
- backend/pyproject.toml: configuracion del paquete.

## 3. Integracion con el Core

El modulo se registra mediante la funcion registrar(app).

Su registro se encuentra en:
core/backend/ide_core/config/constants.py

Prefijo de los endpoints:
/api/v1/sketch

## 4. Endpoints disponibles

| Metodo | Endpoint | Funcion |
|---|---|---|
| POST | /api/v1/sketch/compilar | Inicia una compilacion |
| GET | /api/v1/sketch/tareas/{task_id} | Consulta una tarea |
| GET | /api/v1/sketch/estado | Consulta el estado general |

### Iniciar compilacion

Ejemplo de solicitud:

    {
      "project_path": "C:\\ruta\\del\\proyecto",
      "timeout": 1800,
      "target": "esp32"
    }

El campo target es opcional.

### Estados de las tareas

- pending: pendiente.
- running: en ejecucion.
- completed: finalizada correctamente.
- failed: finalizada con errores.

## 5. Ejecucion

Desde la raiz del repositorio:

    $env:PYTHONPATH = "$PWD\core\backend;$PWD\modules\sketch\backend"
    python -m uvicorn ide_core.config.setup:app_instancia --host 127.0.0.1 --port 8765

Servidor:
http://127.0.0.1:8765

Documentacion interactiva:
http://127.0.0.1:8765/docs

## 6. Pruebas automatizadas

Ejecutar desde la raiz del repositorio:

    python -m unittest discover -s .\modules\sketch\backend\pruebas -p "test_*.py" -v

Actualmente se incluyen seis pruebas:

1. Proyecto inexistente.
2. Ausencia de CMakeLists.txt.
3. Tiempo de espera invalido.
4. Error al configurar el objetivo.
5. Error durante la compilacion.
6. Compilacion exitosa e identificacion de archivos BIN.

## 7. Resultado de integracion

Se verifico la integracion con el Core central mediante solicitudes HTTP.

Tambien se realizo una compilacion real del proyecto de ejemplo hello_idf utilizando ESP-IDF.

Resultados:

- Compilacion exitosa.
- Codigo de retorno: 0.
- Generacion de hello_idf.bin.
- Generacion de bootloader.bin.
- Generacion de partition-table.bin.

Las seis pruebas automatizadas finalizaron correctamente.

## 8. Alcance y consideraciones

- La compilacion se realiza mediante ESP-IDF.
- Las tareas se ejecutan en segundo plano.
- Se procesa una compilacion a la vez.
- El estado de las tareas se conserva en memoria mientras el servidor esta activo.
- Los resultados incluyen las rutas de los archivos BIN generados.
- El modulo todavia no realiza el flasheo fisico de la placa.
- La integracion con el frontend Flutter y la coordinacion con el modulo Compilador quedan pendientes.

## 9. Tecnologias

- Python
- FastAPI
- Pydantic
- ESP-IDF
- CMake
- unittest
