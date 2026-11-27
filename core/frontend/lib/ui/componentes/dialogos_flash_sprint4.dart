// Archivo: core/frontend/lib/ui/componentes/dialogos_flash_sprint4.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const Map<String, String> _plantillasCsvLocales = {
  'single_app': '''# Name, Type, SubType, Offset, Size, Flags
nvs, data, nvs, 0x9000, 0x6000,
phy_init, data, phy, 0xf000, 0x1000,
factory, app, factory, 0x10000, 0x100000,''',
  'single_app_ssl_nvs': '''# Name, Type, SubType, Offset, Size, Flags
nvs, data, nvs, 0x9000, 0x6000,
phy_init, data, phy, 0xf000, 0x1000,
factory, app, factory, 0x10000, 0x180000,
storage, data, spiffs, 0x190000, 0x60000,''',
  'factory_ota': '''# Name, Type, SubType, Offset, Size, Flags
nvs, data, nvs, 0x9000, 0x4000,
otadata, data, ota, 0xd000, 0x2000,
phy_init, data, phy, 0xf000, 0x1000,
ota_0, app, ota_0, 0x10000, 0x140000,
ota_1, app, ota_1, 0x150000, 0x140000,''',
};

/// Dialogo para grabar el Bootloader de segunda etapa con esptool o Bootloader Emulado.
Future<void> mostrarDialogoGrabarBootloader({
  required BuildContext context,
  required String apiBase,
  required String placaNombre,
  required String targetIdf,
  required String puertoActual,
  required String offsetBootloader,
  String? rutaBootloaderInicial,
  required void Function(String mensaje) onLog,
}) async {
  final rutaCtrl = TextEditingController(text: rutaBootloaderInicial ?? '');
  String modo =
      (puertoActual == 'No detectado' || puertoActual == 'Buscando...')
          ? 'emulado'
          : 'fisico';
  bool verificar = true;

  await showDialog<void>(
    context: context,
    builder: (ctx) {
      return StatefulBuilder(
        builder: (ctx, setModalState) {
          return AlertDialog(
            title: Text(
              'Grabar Bootloader — $placaNombre ($offsetBootloader)',
              style: const TextStyle(fontSize: 15),
            ),
            content: SizedBox(
              width: 460,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Target ESP-IDF: $targetIdf | Offset ROM Bootloader: $offsetBootloader',
                    style:
                        const TextStyle(fontSize: 12, color: Colors.blueGrey),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: rutaCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Ruta absoluta de bootloader.bin',
                      hintText: r'C:\...\build\bootloader\bootloader.bin',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: modo,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Modo de grabación',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'emulado',
                        child: Text(
                            'Bootloader Emulado (validación 0xE9 + SHA-256)'),
                      ),
                      DropdownMenuItem(
                        value: 'fisico',
                        child: Text(
                            'Hardware Físico (Espressif esptool write-flash)'),
                      ),
                    ],
                    onChanged: (v) {
                      if (v != null) setModalState(() => modo = v);
                    },
                  ),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    value: verificar,
                    title: const Text(
                      'Verificar integridad tras escritura (verify-flash / SHA-256)',
                      style: TextStyle(fontSize: 12),
                    ),
                    onChanged: (v) =>
                        setModalState(() => verificar = v ?? true),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cancelar'),
              ),
              ElevatedButton.icon(
                icon: const Icon(Icons.bolt, size: 16),
                label: const Text('Grabar Bootloader'),
                onPressed: () async {
                  final ruta = rutaCtrl.text.trim();
                  Navigator.of(ctx).pop();
                  if (ruta.isEmpty) {
                    onLog(
                      'AVISO: Compila primero el proyecto ESP-IDF o ingresa la ruta de bootloader.bin.',
                    );
                    return;
                  }
                  onLog(
                    'Grabando bootloader ($modo) en offset $offsetBootloader para $targetIdf...',
                  );
                  try {
                    final resp = await http
                        .post(
                          Uri.parse('$apiBase/herramientas/esptool/bootloader'),
                          headers: {'Content-Type': 'application/json'},
                          body: jsonEncode({
                            'bootloader_path': ruta,
                            'target': targetIdf,
                            'puerto': modo == 'fisico' ? puertoActual : null,
                            'modo': modo,
                            'verificar': verificar,
                          }),
                        )
                        .timeout(const Duration(seconds: 60));
                    final d = jsonDecode(resp.body) as Map<String, dynamic>;
                    if (d['exitoso'] == true) {
                      onLog(
                        'Bootloader grabado en ${d['offset']} | Verificado: ${d['verificado']} | SHA-256: ${d['sha256']?.toString().substring(0, 12)}...',
                      );
                    } else {
                      onLog('ERROR Bootloader: ${d['error']}');
                    }
                  } catch (e) {
                    onLog('Error de conexión al grabar bootloader: $e');
                  }
                },
              ),
            ],
          );
        },
      );
    },
  );
}

/// Editor visual de Tablas de Particiones ESP-IDF (CSV <-> partition-table.bin).
Future<void> mostrarDialogoParticiones({
  required BuildContext context,
  required String apiBase,
  required void Function(String binPath) onParticionGenerada,
  required void Function(String mensaje) onLog,
}) async {
  String plantillaSeleccionada = 'single_app_ssl_nvs';
  final csvCtrl = TextEditingController(
    text: _plantillasCsvLocales[plantillaSeleccionada],
  );
  List<Map<String, dynamic>> vistaPrevia = const [];
  String? mensajeEstado;

  await showDialog<void>(
    context: context,
    builder: (ctx) {
      return StatefulBuilder(
        builder: (ctx, setModalState) {
          return AlertDialog(
            title: const Text(
              'Editor de Tabla de Particiones ESP-IDF (0x8000)',
              style: TextStyle(fontSize: 15),
            ),
            content: SizedBox(
              width: 540,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    DropdownButtonFormField<String>(
                      value: plantillaSeleccionada,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Plantilla oficial Espressif',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'single_app',
                          child: Text('Single Factory App (sin OTA)'),
                        ),
                        DropdownMenuItem(
                          value: 'single_app_ssl_nvs',
                          child: Text('Factory App + NVS Certificados SSL'),
                        ),
                        DropdownMenuItem(
                          value: 'factory_ota',
                          child: Text('Dual OTA (ota_0 + ota_1)'),
                        ),
                      ],
                      onChanged: (val) {
                        if (val != null &&
                            _plantillasCsvLocales.containsKey(val)) {
                          setModalState(() {
                            plantillaSeleccionada = val;
                            csvCtrl.text = _plantillasCsvLocales[val]!;
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 10),
                    TextField(
                      controller: csvCtrl,
                      maxLines: 6,
                      style: const TextStyle(
                          fontFamily: 'monospace', fontSize: 12),
                      decoration: const InputDecoration(
                        labelText:
                            'Definición CSV (Name, Type, SubType, Offset, Size, Flags)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    if (mensajeEstado != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        mensajeEstado!,
                        style:
                            const TextStyle(fontSize: 12, color: Colors.teal),
                      ),
                    ],
                    if (vistaPrevia.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      ...vistaPrevia.map(
                        (p) => Text(
                          '• ${p['nombre']} (${p['tipo']}/${p['subtipo']}) -> ${p['offset']} [${p['size']}]',
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 11,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cerrar'),
              ),
              ElevatedButton.icon(
                icon: const Icon(Icons.table_view, size: 16),
                label: const Text('Generar partition-table.bin'),
                onPressed: () async {
                  try {
                    final resp = await http
                        .post(
                          Uri.parse(
                              '$apiBase/herramientas/particiones/generar'),
                          headers: {'Content-Type': 'application/json'},
                          body: jsonEncode({
                            'csv_contenido': csvCtrl.text,
                            'nombre': 'partition-table',
                          }),
                        )
                        .timeout(const Duration(seconds: 20));
                    final d = jsonDecode(resp.body) as Map<String, dynamic>;
                    if (d['exitoso'] == true) {
                      final binPath = d['bin_path'].toString();
                      final lista = (d['particiones'] as List?)
                              ?.cast<Map<String, dynamic>>() ??
                          [];
                      onParticionGenerada(binPath);
                      onLog(
                        'Tabla de particiones generada (${d['generador']}): $binPath (${d['size_bytes']} bytes)',
                      );
                      setModalState(() {
                        vistaPrevia = lista;
                        mensajeEstado =
                            'Generado en 0x8000 (${d['size_bytes']} bytes) — listo para Flasheo Completo.';
                      });
                    } else {
                      setModalState(() {
                        mensajeEstado = 'Error: ${d['error']}';
                      });
                      onLog('ERROR Particiones: ${d['error']}');
                    }
                  } catch (e) {
                    onLog('No se pudo generar partition-table.bin: $e');
                  }
                },
              ),
            ],
          );
        },
      );
    },
  );
}

/// Panel de carga y generacion de particion NVS con Certificados SSL/TLS X.509.
Future<void> mostrarDialogoCertificadosSsl({
  required BuildContext context,
  required String apiBase,
  required void Function(String nvsBinPath) onNvsGenerado,
  required void Function(String mensaje) onLog,
}) async {
  final caCtrl = TextEditingController(
    text: '-----BEGIN CERTIFICATE-----\n'
        'MIIBszCCAVmgAwIBAgIUESP32ROOTCADEMOCERTIFICATE0123456789ABCDEF==\n'
        '-----END CERTIFICATE-----',
  );
  final clientCertCtrl = TextEditingController();
  final clientKeyCtrl = TextEditingController();
  final namespaceCtrl = TextEditingController(text: 'ssl_certs');
  final offsetCtrl = TextEditingController(text: '0x9000');

  await showDialog<void>(
    context: context,
    builder: (ctx) {
      return AlertDialog(
        title: const Text(
          'Certificados SSL/TLS en Partición NVS',
          style: TextStyle(fontSize: 15),
        ),
        content: SizedBox(
          width: 540,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: namespaceCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Namespace NVS',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: offsetCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Offset NVS',
                          border: OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: caCtrl,
                  maxLines: 4,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                  decoration: const InputDecoration(
                    labelText: 'Certificado Raíz CA (PEM X.509)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: clientCertCtrl,
                  maxLines: 3,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                  decoration: const InputDecoration(
                    labelText: 'Certificado Cliente mTLS (Opcional PEM)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: clientKeyCtrl,
                  maxLines: 3,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
                  decoration: const InputDecoration(
                    labelText: 'Llave Privada Cliente (Opcional PEM)',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancelar'),
          ),
          ElevatedButton.icon(
            icon: const Icon(Icons.lock_outline, size: 16),
            label: const Text('Empaquetar en NVS (.bin)'),
            onPressed: () async {
              Navigator.of(ctx).pop();
              onLog('Empaquetando certificados SSL en imagen binaria NVS...');
              try {
                final resp = await http
                    .post(
                      Uri.parse(
                          '$apiBase/herramientas/certificados/generar-nvs'),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({
                        'ca_cert': caCtrl.text.trim().isEmpty
                            ? null
                            : caCtrl.text.trim(),
                        'client_cert': clientCertCtrl.text.trim().isEmpty
                            ? null
                            : clientCertCtrl.text.trim(),
                        'client_key': clientKeyCtrl.text.trim().isEmpty
                            ? null
                            : clientKeyCtrl.text.trim(),
                        'namespace': namespaceCtrl.text.trim(),
                        'offset': offsetCtrl.text.trim(),
                      }),
                    )
                    .timeout(const Duration(seconds: 25));
                final d = jsonDecode(resp.body) as Map<String, dynamic>;
                if (d['exitoso'] == true) {
                  final binPath = d['nvs_bin_path'].toString();
                  onNvsGenerado(binPath);
                  onLog(
                    'Partición NVS SSL generada (${d['generador']}) @ ${d['offset']}: $binPath | SHA-256: ${d['sha256']?.toString().substring(0, 12)}...',
                  );
                } else {
                  onLog('ERROR Certificados SSL: ${d['error']}');
                }
              } catch (e) {
                onLog('Error al generar partición NVS SSL: $e');
              }
            },
          ),
        ],
      );
    },
  );
}

/// Wizard de Flasheo Completo Orquestado (Bootloader + Partitions + NVS SSL + App) + Historial.
Future<void> mostrarWizardFlasheoCompleto({
  required BuildContext context,
  required String apiBase,
  required String placaNombre,
  required String targetIdf,
  required String puertoActual,
  required String offsetBootloader,
  String? bootloaderInicial,
  String? partitionsInicial,
  String? nvsSslInicial,
  String? appInicial,
  required void Function(String mensaje) onLog,
}) async {
  final bootCtrl = TextEditingController(text: bootloaderInicial ?? '');
  final partCtrl = TextEditingController(text: partitionsInicial ?? '');
  final nvsCtrl = TextEditingController(text: nvsSslInicial ?? '');
  final appCtrl = TextEditingController(text: appInicial ?? '');
  String modo =
      (puertoActual == 'No detectado' || puertoActual == 'Buscando...')
          ? 'emulado'
          : 'fisico';
  bool verificar = true;
  List<Map<String, dynamic>> historial = const [];

  try {
    final rHist = await http
        .get(Uri.parse('$apiBase/herramientas/historial-flash'))
        .timeout(const Duration(seconds: 2));
    if (rHist.statusCode == 200) {
      final body = jsonDecode(rHist.body) as Map<String, dynamic>;
      historial = (body['historial'] as List?)?.cast<Map<String, dynamic>>() ??
          const [];
    }
  } catch (_) {}

  if (!context.mounted) return;

  await showDialog<void>(
    context: context,
    builder: (ctx) {
      return StatefulBuilder(
        builder: (ctx, setModalState) {
          return AlertDialog(
            title: Text(
              'Flasheo Completo Orquestado — $placaNombre ($targetIdf)',
              style: const TextStyle(fontSize: 15),
            ),
            content: SizedBox(
              width: 560,
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    DropdownButtonFormField<String>(
                      value: modo,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Destino de Flasheo',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      items: [
                        const DropdownMenuItem(
                          value: 'emulado',
                          child: Text(
                            'Bootloader Emulado + Verificación Readback SHA-256',
                          ),
                        ),
                        DropdownMenuItem(
                          value: 'fisico',
                          child: Text(
                            'Hardware Físico con Espressif esptool ($puertoActual)',
                          ),
                        ),
                      ],
                      onChanged: (v) {
                        if (v != null) setModalState(() => modo = v);
                      },
                    ),
                    const SizedBox(height: 10),
                    TextField(
                      controller: bootCtrl,
                      decoration: InputDecoration(
                        labelText: '1. Bootloader ($offsetBootloader)',
                        border: const OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: partCtrl,
                      decoration: const InputDecoration(
                        labelText: '2. Tabla de Particiones (0x8000)',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: nvsCtrl,
                      decoration: const InputDecoration(
                        labelText:
                            '3. Certificados SSL NVS (0x9000 — opcional)',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: appCtrl,
                      decoration: const InputDecoration(
                        labelText: '4. Aplicación Firmware (0x10000)',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                    ),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: verificar,
                      title: const Text(
                        'Ejecutar verificación post-flasheo (verify-flash / SHA-256)',
                        style: TextStyle(fontSize: 12),
                      ),
                      onChanged: (v) =>
                          setModalState(() => verificar = v ?? true),
                    ),
                    if (historial.isNotEmpty) ...[
                      const Divider(),
                      const Text(
                        'Últimas operaciones registradas en BD:',
                        style: TextStyle(
                            fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      ...historial.take(3).map(
                            (h) => Text(
                              '• [${h['modo']}] ${h['tipo_operacion']} (${h['chip_target']}) — '
                              '${h['exitoso'] == true ? "OK" : "ERROR"} | Verificado: ${h['verificado']}',
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 11,
                              ),
                            ),
                          ),
                    ],
                  ],
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Cancelar'),
              ),
              ElevatedButton.icon(
                icon: const Icon(Icons.system_security_update_good, size: 16),
                label: const Text('Ejecutar Flasheo Completo'),
                onPressed: () async {
                  Navigator.of(ctx).pop();
                  if (bootCtrl.text.trim().isEmpty ||
                      partCtrl.text.trim().isEmpty ||
                      appCtrl.text.trim().isEmpty) {
                    onLog(
                      'AVISO: Se requieren las rutas de Bootloader, Particiones y Firmware App (compila con ESP-IDF primero).',
                    );
                    return;
                  }
                  onLog(
                    'Iniciando Flasheo Completo ($modo) para $placaNombre ($targetIdf)...',
                  );
                  try {
                    final resp = await http
                        .post(
                          Uri.parse(
                              '$apiBase/herramientas/esptool/flash-completo'),
                          headers: {'Content-Type': 'application/json'},
                          body: jsonEncode({
                            'target': targetIdf,
                            'puerto': modo == 'fisico' ? puertoActual : null,
                            'modo': modo,
                            'bootloader_path': bootCtrl.text.trim(),
                            'partitions_path': partCtrl.text.trim(),
                            'nvs_certs_path': nvsCtrl.text.trim().isEmpty
                                ? null
                                : nvsCtrl.text.trim(),
                            'app_path': appCtrl.text.trim(),
                            'verificar': verificar,
                          }),
                        )
                        .timeout(const Duration(minutes: 3));
                    final d = jsonDecode(resp.body) as Map<String, dynamic>;
                    if (d['exitoso'] == true) {
                      onLog(
                        '${d['salida']} | SHA-256 global: ${d['sha256']?.toString().substring(0, 12)}...',
                      );
                    } else {
                      onLog('ERROR Flasheo Completo: ${d['error']}');
                    }
                  } catch (e) {
                    onLog('Fallo de red en Flasheo Completo: $e');
                  }
                },
              ),
            ],
          );
        },
      );
    },
  );
}
