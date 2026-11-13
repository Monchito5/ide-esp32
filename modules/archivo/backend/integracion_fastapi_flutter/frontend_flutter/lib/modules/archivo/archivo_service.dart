// Servicio HTTP en Dart (Flutter) para enviar código fuente (UploadFile) al Módulo de Archivo,
// estructurar el proyecto ESP-IDF y recibir los binarios (.bin) y registros para la UI de Log.

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'archivo_models.dart';

class ArchivoApiService {
  final String baseUrl;

  ArchivoApiService({this.baseUrl = 'http://127.0.0.1:8000/api/archivo'});

  Map<String, String> get _headers => {
        'Content-Type': 'application/json; charset=UTF-8',
      };

  /// 1. Enviar archivos de código fuente escritos por el usuario en Flutter (Multipart UploadFile)
  ///    para que el Módulo de Archivo cree el directorio temporal con estructura ESP-IDF.
  Future<ESPIDFProjectPreparedResponse> enviarCodigoYPrepararESPIDF({
    required String projectName,
    required Map<String, String> sourceFiles, // {"main.c": "#include ...", "helper.h": "..."}
  }) async {
    final uri = Uri.parse('$baseUrl/espidf/preparar');
    final request = http.MultipartRequest('POST', uri);
    request.fields['project_name'] = projectName;

    sourceFiles.forEach((filename, codeContent) {
      request.files.add(
        http.MultipartFile.fromString(
          'files',
          codeContent,
          filename: filename,
        ),
      );
    });

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return ESPIDFProjectPreparedResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  /// 2. Recibir los archivos .bin generados y los logs de compilación/errores para la UI de Log
  Future<BuildAndFilesDeliveryResponse> obtenerResultadosCompilacionYBinarios({
    required String projectId,
    required bool compilationSuccess,
    String compilerStdout = '',
    List<String> compilerStderr = const [],
    bool includeBase64 = true,
  }) async {
    final uri = Uri.parse('$baseUrl/espidf/entregar-resultados');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'project_id': projectId,
        'compilation_success': compilationSuccess,
        'compiler_stdout': compilerStdout,
        'compiler_stderr': compilerStderr,
        'include_base64': includeBase64,
      }),
    );
    return BuildAndFilesDeliveryResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  /// 3. Funciones adicionales del menú Archivo (Nuevo, Abrir, Guardar, Submenús, Preferencias)
  Future<ArchivoActionResponse> nuevoSketch() async {
    final uri = Uri.parse('$baseUrl/nuevo');
    final response = await http.post(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
  }

  Future<ArchivoActionResponse> abrirArchivo(String filepath) async {
    final uri = Uri.parse('$baseUrl/abrir');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({'filepath': filepath}),
    );
    return ArchivoActionResponse.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
  }

  Future<ArchivoActionResponse> guardarArchivo({
    required String filepath,
    required String content,
  }) async {
    final uri = Uri.parse('$baseUrl/guardar');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'filepath': filepath,
        'content': content,
      }),
    );
    return ArchivoActionResponse.fromJson(jsonDecode(utf8.decode(response.bodyBytes)));
  }
}
