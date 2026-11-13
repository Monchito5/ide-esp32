// Modelos de datos en Dart para la comunicación entre Flutter y el Módulo de Archivo (FastAPI + ESP-IDF)

class GeneratedBinary {
  final String filename;
  final String relativePath;
  final String absolutePath;
  final int sizeBytes;
  final String? flashOffset;
  final String downloadUrl;
  final String? contentBase64;

  GeneratedBinary({
    required this.filename,
    required this.relativePath,
    required this.absolutePath,
    required this.sizeBytes,
    this.flashOffset,
    required this.downloadUrl,
    this.contentBase64,
  });

  factory GeneratedBinary.fromJson(Map<String, dynamic> json) {
    return GeneratedBinary(
      filename: json['filename'] as String? ?? '',
      relativePath: json['relative_path'] as String? ?? '',
      absolutePath: json['absolute_path'] as String? ?? '',
      sizeBytes: json['size_bytes'] as int? ?? 0,
      flashOffset: json['flash_offset'] as String?,
      downloadUrl: json['download_url'] as String? ?? '',
      contentBase64: json['content_base64'] as String?,
    );
  }
}

class ESPIDFProjectPreparedResponse {
  final bool success;
  final String projectId;
  final String projectName;
  final String projectAbsolutePath;
  final List<String> createdFiles;
  final String message;
  final List<String> errors;

  ESPIDFProjectPreparedResponse({
    required this.success,
    required this.projectId,
    required this.projectName,
    required this.projectAbsolutePath,
    required this.createdFiles,
    required this.message,
    required this.errors,
  });

  factory ESPIDFProjectPreparedResponse.fromJson(Map<String, dynamic> json) {
    return ESPIDFProjectPreparedResponse(
      success: json['success'] as bool? ?? false,
      projectId: json['project_id'] as String? ?? '',
      projectName: json['project_name'] as String? ?? '',
      projectAbsolutePath: json['project_absolute_path'] as String? ?? '',
      createdFiles: (json['created_files'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      message: json['message'] as String? ?? '',
      errors: (json['errors'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
    );
  }
}

class BuildAndFilesDeliveryResponse {
  final bool success;
  final String status;
  final String projectId;
  final String projectAbsolutePath;
  final String resultSummary;
  final String compilationLogs;
  final List<String> errors;
  final List<GeneratedBinary> binaries;

  BuildAndFilesDeliveryResponse({
    required this.success,
    required this.status,
    required this.projectId,
    required this.projectAbsolutePath,
    required this.resultSummary,
    required this.compilationLogs,
    required this.errors,
    required this.binaries,
  });

  factory BuildAndFilesDeliveryResponse.fromJson(Map<String, dynamic> json) {
    return BuildAndFilesDeliveryResponse(
      success: json['success'] as bool? ?? false,
      status: json['status'] as String? ?? '',
      projectId: json['project_id'] as String? ?? '',
      projectAbsolutePath: json['project_absolute_path'] as String? ?? '',
      resultSummary: json['result_summary'] as String? ?? '',
      compilationLogs: json['compilation_logs'] as String? ?? '',
      errors: (json['errors'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      binaries: (json['binaries'] as List<dynamic>? ?? [])
          .map((b) => GeneratedBinary.fromJson(b as Map<String, dynamic>))
          .toList(),
    );
  }

  /// Formatea la respuesta para inyectarla directamente en la UI del "Log" en Flutter
  String toLogEntry() {
    final buffer = StringBuffer();
    buffer.writeln('=== [$status] $resultSummary ===');
    buffer.writeln('Directorio ESP-IDF: $projectAbsolutePath');
    if (compilationLogs.isNotEmpty) {
      buffer.writeln('\n--- Salida del Compilador (ESP-IDF) ---');
      buffer.writeln(compilationLogs);
    }
    if (errors.isNotEmpty) {
      buffer.writeln('\n--- Errores Detectados ---');
      for (final err in errors) {
        buffer.writeln(' [ERROR] $err');
      }
    }
    if (binaries.isNotEmpty) {
      buffer.writeln('\n--- Archivos Binarios (.bin) Listos para Flasheo ---');
      for (final bin in binaries) {
        buffer.writeln(
          ' • ${bin.filename} (${bin.sizeBytes} bytes) | Offset: ${bin.flashOffset ?? "N/A"} | Descarga: ${bin.downloadUrl}',
        );
      }
    }
    return buffer.toString();
  }
}

class ArchivoActionResponse {
  final bool success;
  final String action;
  final String result;
  final List<String> errors;
  final List<String> files;
  final String? content;
  final String encoding;
  final Map<String, dynamic> metadata;

  ArchivoActionResponse({
    required this.success,
    required this.action,
    required this.result,
    required this.errors,
    required this.files,
    this.content,
    this.encoding = 'utf-8',
    this.metadata = const {},
  });

  factory ArchivoActionResponse.fromJson(Map<String, dynamic> json) {
    return ArchivoActionResponse(
      success: json['success'] as bool? ?? false,
      action: json['action'] as String? ?? '',
      result: json['result'] as String? ?? '',
      errors: (json['errors'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      files: (json['files'] as List<dynamic>? ?? [])
          .map((f) => f.toString())
          .toList(),
      content: json['content'] as String?,
      encoding: json['encoding'] as String? ?? 'utf-8',
      metadata: (json['metadata'] as Map<String, dynamic>?) ?? {},
    );
  }
}

class IDEPreferences {
  final String language;
  final String theme;
  final String fontFamily;
  final int fontSize;
  final String sketchbookPath;
  final bool autoBackupOnSave;

  IDEPreferences({
    required this.language,
    required this.theme,
    required this.fontFamily,
    required this.fontSize,
    required this.sketchbookPath,
    required this.autoBackupOnSave,
  });

  Map<String, dynamic> toJson() => {
        'language': language,
        'theme': theme,
        'font_family': fontFamily,
        'font_size': fontSize,
        'sketchbook_path': sketchbookPath,
        'auto_backup_on_save': autoBackupOnSave,
      };
}
