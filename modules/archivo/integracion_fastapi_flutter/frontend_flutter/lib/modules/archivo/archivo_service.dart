// Servicio HTTP en Dart (Flutter) para enviar código fuente (UploadFile) al Módulo de Archivo,
// estructurar el proyecto ESP-IDF y consumir las operaciones locales del menú Archivo.

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
    required Map<String, String>
        sourceFiles, // {"main.c": "#include ...", "helper.h": "..."}
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

  /// 3. Funciones locales del menú Archivo y gestión de proyectos
  Future<ArchivoActionResponse> nuevoSketch() async {
    final uri = Uri.parse('$baseUrl/nuevo');
    final response = await http.post(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> abrirArchivo(String filepath) async {
    final uri = Uri.parse('$baseUrl/abrir');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({'filepath': filepath}),
    );
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> guardarArchivo({
    required String filepath,
    required String content,
    bool createProjectFolder = true,
  }) async {
    final uri = Uri.parse('$baseUrl/guardar');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'filepath': filepath,
        'content': content,
        'create_project_folder': createProjectFolder,
      }),
    );
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> cerrarArchivo() async {
    final uri = Uri.parse('$baseUrl/cerrar');
    final response = await http.post(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> obtenerProyectoActual() async {
    final uri = Uri.parse('$baseUrl/actual');
    final response = await http.get(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> obtenerArchivosProyecto({
    String? projectPath,
  }) async {
    final uri = Uri.parse('$baseUrl/proyecto/archivos').replace(
      queryParameters: (projectPath != null && projectPath.isNotEmpty)
          ? {'project_path': projectPath}
          : null,
    );
    final response = await http.get(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> crearArchivoEnProyecto({
    required String filename,
    String? projectDir,
    String content = '',
  }) async {
    final uri = Uri.parse('$baseUrl/proyecto/archivo');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'filename': filename,
        if (projectDir != null) 'project_dir': projectDir,
        'content': content,
      }),
    );
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> limpiarRecientes() async {
    final uri = Uri.parse('$baseUrl/recientes');
    final response = await http.delete(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> restablecerPreferencias() async {
    final uri = Uri.parse('$baseUrl/preferencias/restablecer');
    final response = await http.post(uri, headers: _headers);
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  Future<ArchivoActionResponse> obtenerInfoSketch({
    String? filepath,
    String? content,
  }) async {
    final uri = Uri.parse('$baseUrl/avanzado/info');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        if (filepath != null) 'filepath': filepath,
        if (content != null) 'content': content,
      }),
    );
    return ArchivoActionResponse.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }
}
