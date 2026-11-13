// Archivo: modules/simulacion/frontend/lib/api_simulacion.dart
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Resultado estandarizado de una peticion a la API de simulacion.
/// Nunca lanza excepciones por fallos de conexion: los devuelve como error.
class ResultadoApi<T> {
  final bool ok;
  final T? data;
  final String? error;

  ResultadoApi.ok(this.data) : ok = true, error = null;
  ResultadoApi.error(this.error) : ok = false, data = null;
}

/// Cliente HTTP para las rutas del modulo Simulacion.
class ApiSimulacion {
  ApiSimulacion({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1/simulacion';

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

  Future<ResultadoApi<List<Map<String, dynamic>>>> listarMotores() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/motores')),
      (d) => (d['motores'] as List).cast<Map<String, dynamic>>(),
    );
  }

  Future<ResultadoApi<List<Map<String, dynamic>>>> listarChips() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/chips')),
      (d) => (d['chips'] as List).cast<Map<String, dynamic>>(),
    );
  }

  Future<ResultadoApi<List<Map<String, dynamic>>>> listarSesiones() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/sesiones')),
      (d) => (d['sesiones'] as List).cast<Map<String, dynamic>>(),
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> crearSesion(Map<String, dynamic> datos) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/sesiones'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(datos),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerSesion(String sesionId) async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/sesiones/$sesionId')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> iniciarSesion(String sesionId) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/sesiones/$sesionId/iniciar')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> detenerSesion(String sesionId) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/sesiones/$sesionId/detener')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> reiniciarSesion(String sesionId) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/sesiones/$sesionId/reiniciar')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> flashearSesion(
      String sesionId, Map<String, dynamic> datosFlasheo) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/sesiones/$sesionId/flashear'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(datosFlasheo),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> enviarComando(
      String sesionId, Map<String, dynamic> datosComando) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/sesiones/$sesionId/comandos'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(datosComando),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> agregarComponente(
      String sesionId, Map<String, dynamic> datosComponente) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/sesiones/$sesionId/componentes'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(datosComponente),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerReporte(String sesionId) async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/sesiones/$sesionId/reportes')),
      (d) => d as Map<String, dynamic>,
    );
  }
}
