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

  /// --- Puerto Serie y Deteccion Nativa Espressif ---

  Future<ResultadoApi<List<Map<String, dynamic>>>> listarPuertos() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/puertos')),
      (d) => (d['puertos'] as List).cast<Map<String, dynamic>>(),
    );
  }

  Future<ResultadoApi<List<Map<String, dynamic>>>>
      listarPlacasSoportadas() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/placas-soportadas')),
      (d) => (d['placas'] as List).cast<Map<String, dynamic>>(),
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> detectarPlaca({
    String? puerto,
    bool sondear = false,
  }) async {
    final params = <String, String>{
      'sondear': sondear ? 'true' : 'false',
      if (puerto != null && puerto.isNotEmpty) 'puerto': puerto,
    };
    final uri =
        Uri.parse('$baseUrl/detectar-placa').replace(queryParameters: params);
    return _ejecutar<Map<String, dynamic>>(
      http.get(uri),
      (d) => d as Map<String, dynamic>,
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

  /// --- Reportes e Historial de Flasheo (Sprint 4) ---

  Future<ResultadoApi<Map<String, dynamic>>> resumenFlash() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/reportes/flash')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<List<Map<String, dynamic>>>> historialFlash() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/historial-flash')),
      (d) => (d['historial'] as List).cast<Map<String, dynamic>>(),
    );
  }

  /// --- Particiones, Certificados SSL (NVS) y esptool (Sprint 4) ---

  Future<ResultadoApi<List<Map<String, dynamic>>>>
      listarPlantillasParticiones() async {
    return _ejecutar<List<Map<String, dynamic>>>(
      http.get(Uri.parse('$baseUrl/particiones/plantillas')),
      (d) => (d['plantillas'] as List).cast<Map<String, dynamic>>(),
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> generarTablaParticiones({
    String? csvContenido,
    String? plantillaId,
    String nombre = 'partition-table',
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/particiones/generar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'csv_contenido': csvContenido,
          'plantilla_id': plantillaId,
          'nombre': nombre,
        }),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> generarCertificadosNvs({
    String? caCert,
    String? clientCert,
    String? clientKey,
    String namespace = 'ssl_certs',
    int tamanioBytes = 0x6000,
    String offset = '0x9000',
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/certificados/generar-nvs'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'ca_cert': caCert,
          'client_cert': clientCert,
          'client_key': clientKey,
          'namespace': namespace,
          'tamanio_bytes': tamanioBytes,
          'offset': offset,
        }),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> flashearBootloader({
    required String bootloaderPath,
    required String target,
    String? puerto,
    String modo = 'emulado',
    bool verificar = true,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/esptool/bootloader'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'bootloader_path': bootloaderPath,
          'target': target,
          'puerto': puerto,
          'modo': modo,
          'verificar': verificar,
        }),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> flashearCompleto({
    required String target,
    required String bootloaderPath,
    required String partitionsPath,
    required String appPath,
    String? nvsCertsPath,
    String? puerto,
    String modo = 'emulado',
    bool verificar = true,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/esptool/flash-completo'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'target': target,
          'puerto': puerto,
          'modo': modo,
          'bootloader_path': bootloaderPath,
          'partitions_path': partitionsPath,
          'nvs_certs_path': nvsCertsPath,
          'app_path': appPath,
          'verificar': verificar,
        }),
      ),
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

  /// --- ESP-IDF (Toolchain Nativo Principal) ---

  Future<ResultadoApi<Map<String, dynamic>>> estadoEspIdf() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/esp-idf/estado')),
      (d) => d as Map<String, dynamic>,
    );
  }

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

  /// --- Monitor Serie, Plotter Serie y Exportacion de Logs (Sprint 5) ---

  Future<ResultadoApi<Map<String, dynamic>>> conectarMonitorSerie({
    String puerto = 'VIRTUAL',
    int baudrate = 115200,
    int databits = 8,
    double stopbits = 1.0,
    String parity = 'N',
    String modo = 'auto',
    bool autoReconectar = true,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/monitor-serie/conectar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'puerto': puerto,
          'baudrate': baudrate,
          'databits': databits,
          'stopbits': stopbits,
          'parity': parity,
          'modo': modo,
          'auto_reconectar': autoReconectar,
        }),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> desconectarMonitorSerie() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/monitor-serie/desconectar')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> estadoMonitorSerie() async {
    return _ejecutar<Map<String, dynamic>>(
      http.get(Uri.parse('$baseUrl/monitor-serie/estado')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> enviarMonitorSerie({
    required String datos,
    bool agregarSaltoLinea = true,
  }) async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(
        Uri.parse('$baseUrl/monitor-serie/enviar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'datos': datos,
          'agregar_salto_linea': agregarSaltoLinea,
        }),
      ),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> listarEventosMonitorSerie({
    int desdeSeq = 0,
    String? nivel,
    String? buscar,
    String? regex,
    int limite = 500,
  }) async {
    final params = <String, String>{
      'desde_seq': '$desdeSeq',
      'limite': '$limite',
      if (nivel != null && nivel.isNotEmpty && nivel != 'TODOS') 'nivel': nivel,
      if (buscar != null && buscar.isNotEmpty) 'buscar': buscar,
      if (regex != null && regex.isNotEmpty) 'regex': regex,
    };
    final uri = Uri.parse('$baseUrl/monitor-serie/eventos')
        .replace(queryParameters: params);
    return _ejecutar<Map<String, dynamic>>(
      http.get(uri),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> limpiarMonitorSerie() async {
    return _ejecutar<Map<String, dynamic>>(
      http.post(Uri.parse('$baseUrl/monitor-serie/limpiar')),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<Map<String, dynamic>>> obtenerMuestrasPlotter({
    int desdeSeq = 0,
    int ventana = 120,
  }) async {
    final uri = Uri.parse('$baseUrl/plotter/muestras').replace(
      queryParameters: {
        'desde_seq': '$desdeSeq',
        'ventana': '$ventana',
      },
    );
    return _ejecutar<Map<String, dynamic>>(
      http.get(uri),
      (d) => d as Map<String, dynamic>,
    );
  }

  Future<ResultadoApi<String>> exportarLogs({
    String formato = 'txt',
    String? nivel,
    String? buscar,
    String? regex,
  }) async {
    final params = <String, String>{
      'formato': formato,
      if (nivel != null && nivel.isNotEmpty && nivel != 'TODOS') 'nivel': nivel,
      if (buscar != null && buscar.isNotEmpty) 'buscar': buscar,
      if (regex != null && regex.isNotEmpty) 'regex': regex,
    };
    final uri =
        Uri.parse('$baseUrl/logs/exportar').replace(queryParameters: params);
    try {
      final r = await http.get(uri);
      if (r.statusCode != 200) {
        return ResultadoApi.error('Error HTTP ${r.statusCode}');
      }
      return ResultadoApi.ok(utf8.decode(r.bodyBytes));
    } on SocketException {
      return ResultadoApi.error('No se pudo conectar con el backend');
    } catch (e) {
      return ResultadoApi.error('Error inesperado: $e');
    }
  }
}
