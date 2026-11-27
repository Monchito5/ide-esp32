// Archivo: modules/simulacion/frontend/lib/services/simulation_api.dart
/// Servicios de simulacion ESP32.
library simulacion_api;

import 'package:http/http.dart' as http;

import 'dart:convert';

/// Servicio de alto nivel para operaciones de simulacion.
class SimulationService {
  final String baseUrl;
  SimulationService({this.baseUrl = 'http://127.0.0.1:8765/api/v1/simulacion'});

  Future<Map<String, dynamic>> post(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final r = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: body != null ? jsonEncode(body) : null,
    );
    if (r.statusCode != 200 && r.statusCode != 201) {
      throw Exception('Error HTTP ${r.statusCode}: ${r.body}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> get(String endpoint) async {
    final uri = Uri.parse('$baseUrl$endpoint');
    final r = await http.get(uri);
    if (r.statusCode != 200) {
      throw Exception('Error HTTP ${r.statusCode}: ${r.body}');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }
}
