// Archivo: core/frontend/lib/servicios/api_core.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Cliente HTTP basico para el core del IDE.
class ApiCore {
  ApiCore({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1';

  final String baseUrl;

  Future<Map<String, dynamic>> salud() async {
    final r = await http.get(Uri.parse('$baseUrl/salud'));
    if (r.statusCode != 200) {
      throw Exception('Core no disponible (${r.statusCode})');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> modulos() async {
    final r = await http.get(Uri.parse('$baseUrl/modulos'));
    if (r.statusCode != 200) {
      throw Exception('Error al listar modulos (${r.statusCode})');
    }
    final datos = jsonDecode(r.body) as Map<String, dynamic>;
    return (datos['modulos'] as List).cast<Map<String, dynamic>>();
  }
}
