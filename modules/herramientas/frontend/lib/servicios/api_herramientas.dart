// Archivo: modules/herramientas/frontend/lib/servicios/api_herramientas.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Cliente HTTP para las rutas del modulo Herramientas.
class ApiHerramientas {
  ApiHerramientas({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1/herramientas';

  final String baseUrl;

  Future<List<Map<String, dynamic>>> listarPuertos() async {
    final r = await http.get(Uri.parse('$baseUrl/puertos'));
    if (r.statusCode != 200) {
      throw Exception('Error al listar puertos (${r.statusCode})');
    }
    final datos = jsonDecode(r.body) as Map<String, dynamic>;
    return (datos['puertos'] as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> versionArduinoCli() async {
    final r = await http.get(Uri.parse('$baseUrl/arduino/version'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar arduino-cli');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }
}
