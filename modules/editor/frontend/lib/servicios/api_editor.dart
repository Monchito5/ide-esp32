// Archivo: modules/editor/frontend/lib/servicios/api_editor.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Cliente HTTP para el backend del modulo Editor.
class ApiEditor {
  ApiEditor({String? urlBase, http.Client? cliente})
      : urlBase = urlBase ?? 'http://127.0.0.1:8765/api/v1/editor',
        _cliente = cliente ?? http.Client();

  final String urlBase;
  final http.Client _cliente;

  /// Formatea codigo C/C++/Arduino mediante el backend.
  Future<Map<String, dynamic>> formatearCodigo(
      String codigo, {int tabSize = 2}) async {
    try {
      final respuesta = await _cliente.post(
        Uri.parse('$urlBase/formato'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'codigo': codigo, 'tab_size': tabSize}),
      );
      if (respuesta.statusCode == 200) {
        return jsonDecode(respuesta.body) as Map<String, dynamic>;
      }
      return {
        'exitoso': false,
        'codigo_formateado': codigo,
        'error': 'Error HTTP ${respuesta.statusCode}'
      };
    } catch (e) {
      return {
        'exitoso': false,
        'codigo_formateado': codigo,
        'error': e.toString()
      };
    }
  }

  /// Busca coincidencias en los archivos del proyecto.
  Future<Map<String, dynamic>> buscarEnArchivos(
    String termino, {
    String? directorio,
    bool sensibleMayusculas = false,
    bool palabraCompleta = false,
  }) async {
    try {
      final respuesta = await _cliente.post(
        Uri.parse('$urlBase/buscar-archivos'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'termino': termino,
          'directorio': directorio,
          'sensible_mayusculas': sensibleMayusculas,
          'palabra_completa': palabraCompleta,
        }),
      );
      if (respuesta.statusCode == 200) {
        return jsonDecode(respuesta.body) as Map<String, dynamic>;
      }
      return {'total_coincidencias': 0, 'archivos': []};
    } catch (_) {
      return {'total_coincidencias': 0, 'archivos': []};
    }
  }

  /// Reemplaza texto en los archivos del proyecto.
  Future<Map<String, dynamic>> reemplazarEnArchivos(
    String termino,
    String reemplazo, {
    String? directorio,
    bool sensibleMayusculas = false,
  }) async {
    try {
      final respuesta = await _cliente.post(
        Uri.parse('$urlBase/reemplazar-archivos'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'termino': termino,
          'reemplazo': reemplazo,
          'directorio': directorio,
          'sensible_mayusculas': sensibleMayusculas,
        }),
      );
      if (respuesta.statusCode == 200) {
        return jsonDecode(respuesta.body) as Map<String, dynamic>;
      }
      return {'exitoso': false, 'archivos_modificados': 0};
    } catch (e) {
      return {'exitoso': false, 'error': e.toString()};
    }
  }

  /// Obtiene la configuracion guardada del editor.
  Future<Map<String, dynamic>> obtenerConfiguracion() async {
    try {
      final respuesta = await _cliente.get(Uri.parse('$urlBase/configuracion'));
      if (respuesta.statusCode == 200) {
        return jsonDecode(respuesta.body) as Map<String, dynamic>;
      }
      return {};
    } catch (_) {
      return {};
    }
  }
}
