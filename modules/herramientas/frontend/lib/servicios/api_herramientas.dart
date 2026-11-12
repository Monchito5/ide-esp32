// Archivo: modules/herramientas/frontend/lib/servicios/api_herramientas.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Cliente HTTP para las rutas del modulo Herramientas.
/// Soporta los endpoints del sprint-02: Arduino CLI, PlatformIO y ESP-IDF.
class ApiHerramientas {
  ApiHerramientas({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1/herramientas';

  final String baseUrl;

  /// --- Puerto Serie ---

  Future<List<Map<String, dynamic>>> listarPuertos() async {
    final r = await http.get(Uri.parse('$baseUrl/puertos'));
    if (r.statusCode != 200) {
      throw Exception('Error al listar puertos (${r.statusCode})');
    }
    final datos = jsonDecode(r.body) as Map<String, dynamic>;
    return (datos['puertos'] as List).cast<Map<String, dynamic>>();
  }

  /// --- Arduino CLI ---

  Future<Map<String, dynamic>> versionArduinoCli() async {
    final r = await http.get(Uri.parse('$baseUrl/arduino/version'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar arduino-cli');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> listarPlacas() async {
    final r = await http.get(Uri.parse('$baseUrl/arduino/placas'));
    if (r.statusCode != 200) {
      throw Exception('Error al listar placas (${r.statusCode})');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// --- Reportes ---

  Future<Map<String, dynamic>> resumenFlash() async {
    final r = await http.get(Uri.parse('$baseUrl/reportes/flash'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar reporte de flash');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// --- PlatformIO ---

  Future<Map<String, dynamic>> estadoPlatformIO() async {
    final r = await http.get(Uri.parse('$baseUrl/platformio/estado'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar estado PlatformIO');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> iniciarProyectoPlatformIO() async {
    final r = await http.post(Uri.parse('$baseUrl/platformio/iniciar'));
    if (r.statusCode != 200 && r.statusCode != 201) {
      throw Exception('Error al iniciar proyecto PlatformIO (${r.statusCode})');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> compilarProyectoPlatformIO() async {
    final r = await http.post(Uri.parse('$baseUrl/platformio/compilar'));
    if (r.statusCode != 200) {
      throw Exception('Error al compilar proyecto PlatformIO (${r.statusCode})');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> flashearFirmwarePlatformIO(
      {String? puerto}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/platformio/flashear'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'puerto': puerto}),
    );
    if (r.statusCode != 200) {
      throw Exception('Error al flashear firmware (${r.statusCode})');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> puertosDisponiblesPlatformIO() async {
    final r = await http.get(Uri.parse('$baseUrl/platformio/puertos-disponibles'));
    if (r.statusCode != 200) {
      throw Exception('Error al listar puertos PlatformIO (${r.statusCode})');
    }
    final datos = jsonDecode(r.body) as Map<String, dynamic>;
    return (datos['puertos'] as List).cast<Map<String, dynamic>>();
  }

  /// --- ESP-IDF ---

  Future<Map<String, dynamic>> versionEspIdf() async {
    final r = await http.get(Uri.parse('$baseUrl/esp-idf/version'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar version ESP-IDF');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> sdkConfigEspIdf() async {
    final r = await http.get(Uri.parse('$baseUrl/esp-idf/sdkconfig'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar sdkconfig ESP-IDF');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> menuConfigEspIdf() async {
    final r = await http.get(Uri.parse('$baseUrl/esp-idf/menuconfig'));
    if (r.statusCode != 200) {
      throw Exception('Error al abrir menuconfig ESP-IDF');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }
}