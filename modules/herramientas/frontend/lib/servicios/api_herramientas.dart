import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Resultado estandarizado de una peticion a la API de herramientas.
/// Nunca lanza excepciones por fallos de conexión: los devuelve como error.
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

/// Cliente HTTP para las rutas del modulo Herramientas.
/// Soporta los endpoints del sprint-02: Arduino CLI, PlatformIO y ESP-IDF.
class ApiHerramientas {
  ApiHerramientas({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1/herramientas';

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

  /// --- Puerto Serie ---

  Future<ResultadoApi<List<Map<String, dynamic>>>> listarPuertos() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/puertos')),
      (d) => (d['puertos'] as List).cast<Map<String, dynamic>>(),
    );
  }

  /// --- Arduino CLI ---

  Future<ResultadoApi<Map<String, dynamic>>> versionArduinoCli() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/arduino/version')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<List<Map<String, dynamic>>>> listarPlacas() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/arduino/placas')),
      (d) => (d['placas'] as List).cast<Map<String, dynamic>>(),
    );
  }

  /// --- Reportes ---

  Future<ResultadoApi<Map<String, dynamic>>> resumenFlash() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/reportes/flash')),
      (d) => d as Map<String, dynamic>,
    );
  }

  /// --- PlatformIO ---

  Future<ResultadoApi<Map<String, dynamic>>> estadoPlatformIO() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/platformio/estado')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> iniciarProyectoPlatformIO() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/platformio/iniciar')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>>
      compilarProyectoPlatformIO() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/platformio/compilar')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> flashearFirmwarePlatformIO(
      {String? puerto}) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/platformio/flashear'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'puerto': puerto}),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<List<Map<String, dynamic>>>>
      puertosDisponiblesPlatformIO() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/platformio/puertos-disponibles')),
      (d) => (d['puertos'] as List).cast<Map<String, dynamic>>(),
    );
  }

  /// --- ESP-IDF ---

  Future<ResultadoApi<Map<String, dynamic>>> versionEspIdf() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/esp-idf/version')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> sdkConfigEspIdf() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/esp-idf/sdkconfig')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> menuConfigEspIdf() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/esp-idf/menuconfig')),
      (d) => d as Map<String, dynamic>,
    );
  }
}
