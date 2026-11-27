import 'dart:convert';

import 'package:http/http.dart' as http;

/// Servicio HTTP para comunicarse con el backend del modulo Sketch.
class ApiSketch {
  ApiSketch({String? baseUrl, http.Client? cliente})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1',
        _cliente = cliente ?? http.Client();

  final String baseUrl;
  final http.Client _cliente;

  /// Solicita iniciar una compilacion ESP-IDF.
  Future<Map<String, dynamic>> iniciarCompilacion({
    required String projectPath,
    int timeout = 1800,
    String? target,
  }) async {
    final uri = Uri.parse('$baseUrl/sketch/compilar');

    final respuesta = await _cliente.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'project_path': projectPath,
        'timeout': timeout,
        'target': target,
      }),
    );

    if (respuesta.statusCode != 202) {
      throw Exception(
        'No se pudo iniciar la compilacion '
        '(${respuesta.statusCode}): ${respuesta.body}',
      );
    }

    return jsonDecode(respuesta.body) as Map<String, dynamic>;
  }

  /// Consulta el estado y resultado de una tarea.
  Future<Map<String, dynamic>> consultarTarea(String taskId) async {
    final uri = Uri.parse('$baseUrl/sketch/tareas/$taskId');
    final respuesta = await _cliente.get(uri);

    if (respuesta.statusCode != 200) {
      throw Exception(
        'No se pudo consultar la tarea '
        '(${respuesta.statusCode}): ${respuesta.body}',
      );
    }

    return jsonDecode(respuesta.body) as Map<String, dynamic>;
  }

  /// Obtiene los archivos y directorios de un proyecto ESP-IDF.
  Future<Map<String, dynamic>> consultarArchivos({
    required String projectPath,
  }) async {
    final uri = Uri.parse('$baseUrl/sketch/archivos')
        .replace(queryParameters: {'project_path': projectPath});

    final respuesta = await _cliente.get(uri);

    if (respuesta.statusCode != 200) {
      throw Exception(
        'No se pudieron consultar los archivos '
        '(${respuesta.statusCode}): ${respuesta.body}',
      );
    }

    return jsonDecode(respuesta.body) as Map<String, dynamic>;
  }

  /// Libera el cliente HTTP cuando deja de utilizarse.
  void cerrar() {
    _cliente.close();
  }
}
