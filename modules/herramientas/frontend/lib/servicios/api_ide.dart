// Archivo: modules/herramientas/frontend/lib/servicios/api_ide.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Cliente HTTP para las rutas de nivel IDE del modulo Herramientas.
/// Proporciona acceso a funcionalidades globales del IDE a través del backend.
class ApiIde {
  ApiIde({String? baseUrl})
      : baseUrl = baseUrl ?? 'http://127.0.0.1:8765/api/v1';

  final String baseUrl;

  /// Obtiene el estado de salud del IDE
  Future<Map<String, dynamic>> salud() async {
    final r = await http.get(Uri.parse('$baseUrl/salud'));
    if (r.statusCode != 200) {
      throw Exception('Error al consultar salud del IDE');
    }
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// Lista los modulos instalados
  Future<List<Map<String, dynamic>>> modulos() async {
    final r = await http.get(Uri.parse('$baseUrl/modulos'));
    if (r.statusCode != 200) {
      throw Exception('Error al listar modulos');
    }
    final datos = jsonDecode(r.body) as Map<String, dynamic>;
    return (datos['modulos'] as List).cast<Map<String, dynamic>>();
  }

  /// Verifica si un modulo específico está activo
  Future<bool> moduloActivo(String nombreModulo) async {
    final listaModulos = await modulos();
    return listaModulos
        .any((m) => m['nombre'] == nombreModulo && m['activo'] == true);
  }

  /// Obtiene información del modulo Herramientas
  Future<Map<String, dynamic>> infoModuloHerramientas() async {
    final listaModulos = await modulos();
    final herramienta = listaModulos.firstWhere(
      (m) => m['nombre'] == 'herramientas',
      orElse: () => <String, dynamic>{},
    );
    return herramienta;
  }
}
