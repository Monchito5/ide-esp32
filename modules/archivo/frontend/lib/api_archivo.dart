// Archivo: modules/archivo/frontend/lib/api_archivo.dart
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Resultado estandarizado de una peticion a la API de Archivo.
/// Nunca lanza excepciones por fallos de conexión: las devuelve como error.
class ResultadoApi<T> {
  final bool ok;
  final T? data;
  final String? error;

  ResultadoApi.ok(this.data)
      : ok = true,
        error = null;
  ResultadoApi.error(this.error)
      : ok = false,
        data = null;
}

/// Cliente HTTP para las rutas del modulo Archivo.
/// baseUrl: http://127.0.0.1:8765/api/v1/archivo
class ApiArchivo {
  ApiArchivo({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1/archivo';

  final String baseUrl;

  Future<ResultadoApi<T>> _ejecutar<T>(
    Future<http.Response> request,
    T Function(dynamic) parse,
  ) async {
    try {
      final r = await request;
      if (r.statusCode != 200 && r.statusCode != 201) {
        return ResultadoApi.error('Error HTTP ${r.statusCode}');
      }
      return ResultadoApi.ok(parse(jsonDecode(r.body)));
    } on SocketException {
      return ResultadoApi.error('No se pudo conectar con el backend');
    } on FormatException {
      return ResultadoApi.error('Respuesta invalida del backend');
    } catch (e) {
      return ResultadoApi.error('Error inesperado: $e');
    }
  }

  /// --- Menu Archivo local ---

  Future<ResultadoApi<Map<String, dynamic>>> nuevoSketch() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/nuevo')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> abrirArchivo({
    required String filepath,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/abrir'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'filepath': filepath}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> guardarArchivo({
    required String filepath,
    required String content,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/guardar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'filepath': filepath, 'content': content}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> guardarComo({
    required String filepath,
    required String content,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/guardar-como'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'filepath': filepath, 'content': content}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> cerrarSketch({
    required String filepath,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/cerrar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'filepath': filepath}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> recargarSketch({
    required String filepath,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/recargar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'filepath': filepath}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerPlantillaBase() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/plantilla-base')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerInfoSketch({
    required String filepath,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(
        Uri.parse('$baseUrl/info-sketch').replace(queryParameters: {
          'filepath': filepath,
        }),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerSubmenus() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/submenus')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerPreferencias() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/preferencias')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> actualizarPreferencias({
    required Map<String, dynamic> prefs,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.put(
        Uri.parse('$baseUrl/preferencias'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(prefs),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> restablecerPreferencias() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/restablecer-preferencias')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> limpiarRecientes() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/limpiar-recientes')),
      (d) => d as Map<String, dynamic>,
    );
  }

  /// --- ESP-IDF puente compilador ---

  Future<ResultadoApi<Map<String, dynamic>>> prepararProyectoEspidf({
    String projectName = 'esp32_sketch',
    required List<http.MultipartFile> files,
  }) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/espidf/preparar'),
      )..fields['project_name'] = projectName;
      request.files.addAll(files);
      final streamed = await request.send();
      final r = await http.Response.fromStream(streamed);
      if (r.statusCode != 200 && r.statusCode != 201) {
        return ResultadoApi.error('Error HTTP ${r.statusCode}');
      }
      return ResultadoApi.ok(jsonDecode(r.body) as Map<String, dynamic>);
    } on SocketException {
      return ResultadoApi.error('No se pudo conectar con el backend');
    } on FormatException {
      return ResultadoApi.error('Respuesta invalida del backend');
    } catch (e) {
      return ResultadoApi.error('Error inesperado: $e');
    }
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerRutaCompilador({
    required String projectId,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/espidf/$projectId/ruta-compilador')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> entregarResultados({
    required Map<String, dynamic> request,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/espidf/entregar-resultados'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(request),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> descargarBinario({
    required String projectId,
    required String relPath,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(
        Uri.parse('$baseUrl/espidf/$projectId/descargar-bin')
            .replace(queryParameters: {'rel_path': relPath}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> limpiarProyecto({
    required String projectId,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.delete(Uri.parse('$baseUrl/espidf/$projectId')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> crearRespaldo({
    required String filepath,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/avanzado/respaldo'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'filepath': filepath}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }
}
