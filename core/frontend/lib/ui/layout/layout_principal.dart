// Archivo: core/frontend/lib/ui/layout/layout_principal.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../nucleo/acciones_ayuda.dart';
import '../../nucleo/registro_modulos.dart';
import '../temas/tema_ide.dart';

const String _plantillaEspIdfPredeterminada = '''#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

void app_main(void) {
  printf("IDE ESP32 — Firmware iniciado con Espressif ESP-IDF\\n");
  while (1) {
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}''';

const List<Map<String, dynamic>> _perfilesEspressifLocales = [
  {
    'nombre': 'ESP32-S3 DevKitC-1',
    'target_idf': 'esp32s3',
    'chip': 'ESP32-S3',
    'arquitectura': 'Xtensa dual-core 32-bit LX7',
    'frecuencia_mhz': 240,
    'flash_mb': 8,
    'bootloader_offset': '0x0',
  },
  {
    'nombre': 'ESP32-C3 DevKitM-1',
    'target_idf': 'esp32c3',
    'chip': 'ESP32-C3',
    'arquitectura': 'RISC-V single-core 32-bit',
    'frecuencia_mhz': 160,
    'flash_mb': 4,
    'bootloader_offset': '0x0',
  },
  {
    'nombre': 'ESP32 DevKitC V4',
    'target_idf': 'esp32',
    'chip': 'ESP32',
    'arquitectura': 'Xtensa dual-core 32-bit LX6',
    'frecuencia_mhz': 240,
    'flash_mb': 4,
    'bootloader_offset': '0x1000',
  },
  {
    'nombre': 'ESP32-S2 Saola-1',
    'target_idf': 'esp32s2',
    'chip': 'ESP32-S2',
    'arquitectura': 'Xtensa single-core 32-bit LX7',
    'frecuencia_mhz': 240,
    'flash_mb': 4,
    'bootloader_offset': '0x1000',
  },
  {
    'nombre': 'ESP32-C6 DevKitC-1',
    'target_idf': 'esp32c6',
    'chip': 'ESP32-C6',
    'arquitectura': 'RISC-V 32-bit (Wi-Fi 6 / BLE / 802.15.4)',
    'frecuencia_mhz': 160,
    'flash_mb': 8,
    'bootloader_offset': '0x0',
  },
];

/// Layout maestro del IDE orientado al flujo nativo Espressif ESP-IDF.
class LayoutPrincipal extends StatefulWidget {
  const LayoutPrincipal({
    super.key,
    required this.registro,
    this.titulo = 'IDE ESP32 — Proyecto ESP-IDF',
    this.accionesAyuda,
  });

  final RegistroModulos registro;
  final String titulo;

  /// Acciones del modulo de Ayuda; si es null el menu solo registra el evento.
  final AccionesAyuda? accionesAyuda;

  @override
  State<LayoutPrincipal> createState() => _LayoutPrincipalState();
}

class _LayoutPrincipalState extends State<LayoutPrincipal> {
  static const String _apiBase = 'http://127.0.0.1:8765/api/v1';

  int _indiceNavRail = 0;
  List<Map<String, dynamic>> _perfilesPlacas =
      List.of(_perfilesEspressifLocales);
  String _placaSeleccionada = 'ESP32-S3 DevKitC-1';
  String _targetIdfSeleccionado = 'esp32s3';
  String _puertoSeleccionado = 'Buscando...';
  String? _macDetectada;
  String _modoOperacion = 'Modo Físico';
  String _estadoIde = 'Listo';
  bool _compilando = false;

  final TextEditingController _codigoController = TextEditingController(
    text: _plantillaEspIdfPredeterminada,
  );

  final List<String> _logsConsola = [
    'Salida:',
    'Entorno IDE ESP32 inicializado (Toolchain objetivo: Espressif ESP-IDF).',
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _inicializarConexionHardware();
    });
  }

  @override
  void dispose() {
    _codigoController.dispose();
    super.dispose();
  }

  Map<String, dynamic> _perfilActual() {
    for (final perfil in _perfilesPlacas) {
      if (perfil['nombre'] == _placaSeleccionada) {
        return perfil;
      }
    }
    return _perfilesPlacas.first;
  }

  void _seleccionarPlacaPorNombre(String nombrePlaca) {
    Map<String, dynamic>? encontrado;
    for (final perfil in _perfilesPlacas) {
      if (perfil['nombre'] == nombrePlaca) {
        encontrado = perfil;
        break;
      }
    }
    setState(() {
      _placaSeleccionada = nombrePlaca;
      if (encontrado != null && encontrado['target_idf'] != null) {
        _targetIdfSeleccionado = encontrado['target_idf'].toString();
      }
    });
  }

  void _agregarLog(String mensaje) {
    if (!mounted) return;
    setState(() {
      _logsConsola.add(mensaje);
      _estadoIde = mensaje.replaceAll('...', '').trim();
      if (_estadoIde.isEmpty) _estadoIde = 'Listo';
    });
  }

  Future<void> _inicializarConexionHardware() async {
    await _cargarCatalogoPlacas();
    await _detectarPlacaYPuertoFisico();
  }

  Future<void> _cargarCatalogoPlacas() async {
    try {
      final resp = await http
          .get(Uri.parse('$_apiBase/herramientas/placas-soportadas'))
          .timeout(const Duration(seconds: 2));
      if (resp.statusCode == 200) {
        final datos = jsonDecode(resp.body) as Map<String, dynamic>;
        final lista =
            (datos['placas'] as List?)?.cast<Map<String, dynamic>>() ?? [];
        if (lista.isNotEmpty && mounted) {
          setState(() {
            _perfilesPlacas = lista;
          });
        }
      }
    } catch (_) {
      // Mantiene el catalogo local de perfiles Espressif si el backend esta offline.
    }
  }

  Future<void> _detectarPlacaYPuertoFisico(
      {bool sondearEsptool = false}) async {
    _agregarLog(
      sondearEsptool
          ? 'Sondeando placa ESP32 con Espressif esptool...'
          : 'Detectando placas Espressif ESP32 en puertos USB...',
    );
    try {
      final uri = Uri.parse(
        '$_apiBase/herramientas/detectar-placa?sondear=${sondearEsptool ? "true" : "false"}',
      );
      final response = await http.get(uri).timeout(
            Duration(seconds: sondearEsptool ? 6 : 2),
          );
      if (response.statusCode == 200) {
        final datos = jsonDecode(response.body) as Map<String, dynamic>;
        final recomendada = datos['recomendada'] as Map<String, dynamic>?;
        if (datos['detectada'] == true && recomendada != null) {
          final puerto = recomendada['dispositivo']?.toString() ?? 'COM3';
          final placa =
              recomendada['placa_sugerida']?.toString() ?? _placaSeleccionada;
          final target =
              recomendada['target_idf']?.toString() ?? _targetIdfSeleccionado;
          final mac = recomendada['mac']?.toString();
          if (mounted) {
            setState(() {
              _puertoSeleccionado = puerto;
              _placaSeleccionada = placa;
              _targetIdfSeleccionado = target;
              _macDetectada = mac;
            });
          }
          final detalleMac = mac != null ? ' | MAC: $mac' : '';
          _agregarLog(
            'Placa detectada: $placa (target ESP-IDF: $target) en $puerto$detalleMac.',
          );
          return;
        }
      }

      if (mounted) {
        setState(() {
          _puertoSeleccionado = 'No detectado';
          _macDetectada = null;
        });
      }
      _agregarLog(
        'AVISO: No se detecto placa ESP32 en USB. Puedes compilar con ESP-IDF o usar Modo Simulacion.',
      );
    } catch (_) {
      if (mounted) {
        setState(() {
          _puertoSeleccionado = 'No detectado';
          _macDetectada = null;
        });
      }
      _agregarLog(
        'AVISO: Backend local no disponible en 127.0.0.1:8765 (deteccion USB offline).',
      );
    }
  }

  Future<void> _verificarEstadoEspIdf() async {
    _agregarLog('Consultando estado de Espressif ESP-IDF y esptool...');
    try {
      final resp = await http
          .get(Uri.parse('$_apiBase/herramientas/esp-idf/estado'))
          .timeout(const Duration(seconds: 4));
      if (resp.statusCode == 200) {
        final d = jsonDecode(resp.body) as Map<String, dynamic>;
        final idfOk = d['esp_idf_disponible'] == true;
        final esptoolOk = d['esptool_disponible'] == true;
        final version = d['version'] ?? 'No detectada';
        final ruta = d['idf_path'] ?? d['idf_py_en_path'] ?? 'No configurada';
        _agregarLog(
          'ESP-IDF: ${idfOk ? "Disponible ($version) en $ruta" : "No instalado (configure IDF_PATH)"} | '
          'esptool: ${esptoolOk ? "Disponible" : "No encontrado"}',
        );
      } else {
        _agregarLog(
            'Error HTTP ${resp.statusCode} al consultar estado ESP-IDF.');
      }
    } catch (e) {
      _agregarLog('No se pudo consultar el backend para ESP-IDF: $e');
    }
  }

  Future<void> _compilarConEspIdf({bool mostrarRutasBinarios = false}) async {
    if (_compilando) return;
    setState(() => _compilando = true);
    _agregarLog(
      'Iniciando compilacion nativa Espressif ESP-IDF para $_placaSeleccionada (target: $_targetIdfSeleccionado)...',
    );

    try {
      final resp = await http
          .post(
            Uri.parse('$_apiBase/sketch/compilar-codigo'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'codigo': _codigoController.text,
              'nombre_proyecto': 'esp32_sketch',
              'nombre_archivo': 'main.c',
              'target': _targetIdfSeleccionado,
              'incluir_base64': false,
            }),
          )
          .timeout(const Duration(minutes: 10));

      if (resp.statusCode == 200) {
        final datos = jsonDecode(resp.body) as Map<String, dynamic>;
        final advertencias =
            (datos['warnings'] as List?)?.map((e) => e.toString()).toList() ??
                const [];
        for (final adv in advertencias) {
          _agregarLog(adv);
        }

        final logs = datos['compilation_logs']?.toString() ?? '';
        if (logs.trim().isNotEmpty) {
          final lineas = logs.trim().split('\n');
          final ultimas =
              lineas.length > 8 ? lineas.sublist(lineas.length - 8) : lineas;
          for (final l in ultimas) {
            if (l.trim().isNotEmpty) _agregarLog('[idf.py] $l');
          }
        }

        if (datos['success'] == true) {
          final binarios =
              (datos['binaries'] as List?)?.cast<Map<String, dynamic>>() ?? [];
          _agregarLog(
            datos['result_summary']?.toString() ??
                'Compilacion ESP-IDF completada exitosamente.',
          );
          for (final bin in binarios) {
            final nombre = bin['filename'];
            final offset = bin['flash_offset'];
            final bytes = bin['size_bytes'];
            final extra =
                mostrarRutasBinarios ? ' -> ${bin['absolute_path']}' : '';
            _agregarLog('  Artefacto: $nombre @ $offset ($bytes bytes)$extra');
          }
        } else {
          final errores =
              (datos['errors'] as List?)?.map((e) => e.toString()).toList() ??
                  const [];
          _agregarLog(
            datos['result_summary']?.toString() ??
                'Fallo en la compilacion ESP-IDF.',
          );
          for (final err in errores) {
            _agregarLog('ERROR ESP-IDF: $err');
          }
        }
      } else {
        _agregarLog(
          'Error del servidor al compilar (HTTP ${resp.statusCode}): ${resp.body}',
        );
      }
    } catch (e) {
      _agregarLog(
        'No se pudo conectar al motor de compilacion ESP-IDF en el backend: $e',
      );
    } finally {
      if (mounted) {
        setState(() => _compilando = false);
      }
    }
  }

  Future<void> _ejecutarSimulacionCircuito() async {
    _agregarLog(
      'Iniciando sesion virtual para $_placaSeleccionada ($_targetIdfSeleccionado)...',
    );
    try {
      final resp = await http
          .post(
            Uri.parse('$_apiBase/simulacion/sesiones'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'chip': _perfilActual()['chip'] ?? 'ESP32-S3',
              'motor': 'esp_emulator',
              'nombre': 'Sesion $_placaSeleccionada',
            }),
          )
          .timeout(const Duration(seconds: 3));
      if (resp.statusCode == 200 || resp.statusCode == 201) {
        final d = jsonDecode(resp.body) as Map<String, dynamic>;
        _agregarLog(
          'Sesion de simulacion activa (ID: ${d['sesion_id'] ?? 'virtual'}) para $_placaSeleccionada.',
        );
        return;
      }
    } catch (_) {
      // Fallback informativo local si el backend no responde.
    }
    _agregarLog(
      'Modo Simulacion preparado localmente para $_placaSeleccionada ($_targetIdfSeleccionado).',
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool esSimulacion = _modoOperacion == 'Modo Simulación';
    final lineasCodigo = _codigoController.text.split('\n').length;
    final totalLineas = lineasCodigo < 15 ? 15 : lineasCodigo;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.titulo, style: const TextStyle(fontSize: 15)),
        backgroundColor: TemaIde.colorPrimario,
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 8),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              decoration: BoxDecoration(
                color: esSimulacion ? Colors.orange.shade700 : Colors.white24,
                borderRadius: BorderRadius.circular(4),
              ),
              child: DropdownButton<String>(
                value: _modoOperacion,
                dropdownColor: TemaIde.colorPrimario,
                style: const TextStyle(color: Colors.white, fontSize: 11),
                underline: const SizedBox(),
                items: <String>[
                  'Modo Físico',
                  'Modo Simulación',
                ].map<DropdownMenuItem<String>>((String value) {
                  return DropdownMenuItem<String>(
                    value: value,
                    child: Text(value),
                  );
                }).toList(),
                onChanged: (String? newValue) {
                  if (newValue != null) {
                    setState(() => _modoOperacion = newValue);
                    if (newValue == 'Modo Simulación') {
                      _agregarLog('Cambiado a Modo Simulación.');
                      _ejecutarSimulacionCircuito();
                    } else {
                      _agregarLog('Cambiado a Modo Físico (Hardware USB).');
                      _detectarPlacaYPuertoFisico();
                    }
                  }
                },
              ),
            ),
          ),
          if (!esSimulacion)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 8),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: DropdownButton<String>(
                  value: _puertoSeleccionado,
                  dropdownColor: TemaIde.colorPrimario,
                  style: const TextStyle(color: Colors.white, fontSize: 11),
                  underline: const SizedBox(),
                  items: <String>[
                    _puertoSeleccionado,
                    'COM3',
                    'COM4',
                    '/dev/ttyUSB0',
                    '/dev/ttyACM0',
                    'No detectado',
                  ]
                      .toSet()
                      .toList()
                      .map<DropdownMenuItem<String>>((String value) {
                    return DropdownMenuItem<String>(
                      value: value,
                      child: Text(value),
                    );
                  }).toList(),
                  onChanged: (String? newValue) {
                    if (newValue != null) {
                      setState(() => _puertoSeleccionado = newValue);
                      _agregarLog('Puerto físico seleccionado: $newValue');
                    }
                  },
                ),
              ),
            ),
          IconButton(
            icon: _compilando
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.greenAccent,
                    ),
                  )
                : const Icon(
                    Icons.check_circle_outline,
                    color: Colors.greenAccent,
                    size: 20,
                  ),
            tooltip: 'Compilar con ESP-IDF',
            onPressed: _compilando ? null : () => _compilarConEspIdf(),
          ),
          IconButton(
            icon: Icon(
              esSimulacion ? Icons.play_arrow : Icons.arrow_forward_ios,
              color: esSimulacion ? Colors.amberAccent : Colors.lightBlueAccent,
              size: 20,
            ),
            tooltip: esSimulacion
                ? 'Iniciar Simulación de Placa'
                : 'Compilar y preparar flasheo esptool',
            onPressed: () async {
              if (esSimulacion) {
                await _ejecutarSimulacionCircuito();
              } else {
                if (_puertoSeleccionado == 'No detectado' ||
                    _puertoSeleccionado == 'Buscando...') {
                  _agregarLog(
                    'ERROR: No hay placa ESP32 detectada en USB. Conecte la placa o elija un puerto antes de flashear.',
                  );
                } else {
                  await _compilarConEspIdf(mostrarRutasBinarios: true);
                }
              }
            },
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: Column(
        children: [
          Container(
            color: Colors.grey.shade200,
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            child: Row(
              children: [
                _buildMenuButton(
                  context,
                  'Archivo',
                  ['Nuevo', 'Abrir', 'Guardar', 'Salir'],
                ),
                _buildMenuButton(
                  context,
                  'Editar',
                  ['Deshacer', 'Rehacer', 'Cortar', 'Copiar', 'Pegar'],
                ),
                _buildMenuButton(
                  context,
                  'Sketch',
                  ['Verificar / Compilar', 'Subir', 'Exportar binario'],
                ),
                _buildMenuButton(context, 'Herramientas', [
                  'Placa',
                  'Puerto',
                  'Detectar placa ESP32',
                  'Estado ESP-IDF',
                  'Auto Formato',
                  'Monitor Serie',
                  'Recargar datos',
                ]),
                _buildMenuButton(context, 'Ayuda', [
                  'Documentación',
                  'Preguntas frecuentes',
                  'Créditos',
                  'Acerca de',
                  'Enlaces rápidos',
                ]),
                const Spacer(),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: Row(
              children: [
                NavigationRail(
                  selectedIndex: _indiceNavRail,
                  onDestinationSelected: (index) {
                    setState(() => _indiceNavRail = index);
                    if (index == 1) {
                      _mostrarDialogoPlaca(context);
                    } else if (index == 5) {
                      _mostrarModalInformacionPlaca(context);
                    }
                  },
                  labelType: NavigationRailLabelType.all,
                  backgroundColor: TemaIde.colorPrimario,
                  selectedIconTheme: const IconThemeData(
                    color: Color(0xFF5D9BC3),
                  ),
                  unselectedIconTheme: const IconThemeData(
                    color: Color(0xFFA9B9C9),
                  ),
                  selectedLabelTextStyle: const TextStyle(
                    color: Color(0xFF5D9BC3),
                    fontWeight: FontWeight.bold,
                  ),
                  unselectedLabelTextStyle: const TextStyle(
                    color: Color(0xFFA9B9C9),
                  ),
                  destinations: const [
                    NavigationRailDestination(
                      icon: Icon(Icons.code),
                      label: Text('Sketch'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.memory),
                      label: Text('Placas'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.library_books),
                      label: Text('Librerías'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.computer),
                      label: Text('Monitor'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.show_chart),
                      label: Text('Plotter'),
                    ),
                    NavigationRailDestination(
                      icon: Icon(Icons.info_outline),
                      label: Text('Info.'),
                    ),
                  ],
                ),
                const VerticalDivider(width: 1, thickness: 1),
                Expanded(
                  flex: 1,
                  child: Column(
                    children: [
                      Expanded(
                        child: Container(
                          color: Colors.white,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 38,
                                color: Colors.grey.shade100,
                                padding:
                                    const EdgeInsets.symmetric(vertical: 12),
                                child: ListView.builder(
                                  physics: const NeverScrollableScrollPhysics(),
                                  itemCount: totalLineas,
                                  itemBuilder: (context, index) => Text(
                                    '${index + 1}',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      color: Colors.grey.shade500,
                                      fontSize: 11,
                                      fontFamily: 'monospace',
                                    ),
                                  ),
                                ),
                              ),
                              const VerticalDivider(width: 1),
                              Expanded(
                                child: Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: TextField(
                                    controller: _codigoController,
                                    onChanged: (_) => setState(() {}),
                                    maxLines: null,
                                    keyboardType: TextInputType.multiline,
                                    style: const TextStyle(
                                      fontFamily: 'monospace',
                                      fontSize: 13,
                                    ),
                                    decoration: const InputDecoration(
                                      border: InputBorder.none,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const Divider(height: 1),
                      Container(
                        height: 110,
                        color: TemaIde.colorConsola,
                        padding: const EdgeInsets.all(6),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  'SALIDA ESP-IDF (${_targetIdfSeleccionado.toUpperCase()})',
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 2),
                            Expanded(
                              child: ListView.builder(
                                itemCount: _logsConsola.length,
                                itemBuilder: (context, index) {
                                  return Text(
                                    _logsConsola[index],
                                    style: const TextStyle(
                                      color: TemaIde.colorTextoConsola,
                                      fontFamily: 'monospace',
                                      fontSize: 11,
                                    ),
                                  );
                                },
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Container(
            color: TemaIde.colorPrimario,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 185,
                  child: Text(
                    '$_placaSeleccionada ($_targetIdfSeleccionado)',
                    style: const TextStyle(color: Colors.white, fontSize: 11),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const Text(' | ', style: TextStyle(color: Colors.white54)),
                SizedBox(
                  width: 140,
                  child: Text(
                    esSimulacion
                        ? 'Simulación'
                        : 'Físico: $_puertoSeleccionado',
                    style: TextStyle(
                      color: esSimulacion ? Colors.amberAccent : Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const Text(' | ', style: TextStyle(color: Colors.white54)),
                Expanded(
                  child: Text(
                    _estadoIde,
                    style: const TextStyle(
                      color: Colors.greenAccent,
                      fontSize: 11,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const Text(
                  'ESP-IDF | v1.0.0',
                  style: TextStyle(color: Colors.white54, fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuButton(
    BuildContext context,
    String titulo,
    List<String> opciones,
  ) {
    return PopupMenuButton<String>(
      padding: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(
          titulo,
          style: const TextStyle(fontSize: 13, color: Colors.black87),
        ),
      ),
      itemBuilder: (BuildContext context) {
        return opciones.map((String opcion) {
          final bool tieneSubmenu = opcion == 'Placa' || opcion == 'Puerto';
          return PopupMenuItem<String>(
            value: opcion,
            child: SizedBox(
              width: 195,
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      opcion,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
                  if (tieneSubmenu)
                    const Icon(
                      Icons.chevron_right,
                      size: 14,
                      color: Colors.grey,
                    ),
                ],
              ),
            ),
          );
        }).toList();
      },
      onSelected: (String valor) {
        _manejarMenuAccion(context, titulo, valor);
      },
    );
  }

  void _mostrarModalInformacionPlaca(BuildContext context) {
    final perfil = _perfilActual();
    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        return AlertDialog(
          title: Row(
            children: [
              const Icon(Icons.memory, color: Colors.blueAccent),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Información: $_placaSeleccionada',
                  style: const TextStyle(fontSize: 15),
                ),
              ),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Modelo: $_placaSeleccionada'),
              const SizedBox(height: 6),
              Text(
                'Target ESP-IDF: $_targetIdfSeleccionado | Chip: ${perfil['chip'] ?? 'ESP32-S3'}',
              ),
              const SizedBox(height: 6),
              Text(
                'Arquitectura: ${perfil['arquitectura'] ?? 'Xtensa 32-bit'}',
              ),
              const SizedBox(height: 6),
              Text(
                'Frecuencia: ${perfil['frecuencia_mhz'] ?? 240} MHz | Flash: ${perfil['flash_mb'] ?? 8} MB | Bootloader: ${perfil['bootloader_offset'] ?? '0x0'}',
              ),
              const SizedBox(height: 6),
              Text('Modo Actual: $_modoOperacion'),
              const SizedBox(height: 6),
              Text('Puerto Físico: $_puertoSeleccionado'),
              if (_macDetectada != null) ...[
                const SizedBox(height: 6),
                Text('MAC (esptool): $_macDetectada'),
              ],
            ],
          ),
          actions: [
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(ctx).pop();
                _detectarPlacaYPuertoFisico(sondearEsptool: true);
              },
              icon: const Icon(Icons.usb, size: 14),
              label: const Text(
                'Sondear con esptool',
                style: TextStyle(fontSize: 12),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
              ),
            ),
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Regresar', style: TextStyle(fontSize: 12)),
            ),
          ],
        );
      },
    );
  }

  void _mostrarDialogoPlaca(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        final nombresPlacas = _perfilesPlacas
            .map((p) => p['nombre']?.toString() ?? '')
            .where((n) => n.isNotEmpty)
            .toList();
        final opciones = [...nombresPlacas, 'Información de la placa'];

        return AlertDialog(
          title: const Text(
            'Herramientas -> Placa (Espressif ESP-IDF)',
            style: TextStyle(fontSize: 15),
          ),
          content: SizedBox(
            width: 330,
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: opciones.length,
              itemBuilder: (context, index) {
                final opcion = opciones[index];
                if (opcion == 'Información de la placa') {
                  return ListTile(
                    leading: const Icon(
                      Icons.info_outline,
                      color: Colors.blue,
                      size: 20,
                    ),
                    title: Text(
                      opcion,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.blue,
                        fontSize: 13,
                      ),
                    ),
                    onTap: () {
                      Navigator.of(ctx).pop();
                      _mostrarModalInformacionPlaca(context);
                    },
                  );
                }
                final perfil = _perfilesPlacas[index];
                final target = perfil['target_idf']?.toString() ?? '';
                return ListTile(
                  leading: Radio<String>(
                    value: opcion,
                    groupValue: _placaSeleccionada,
                    onChanged: (val) {
                      if (val != null) {
                        _seleccionarPlacaPorNombre(val);
                        _agregarLog(
                          'Placa seleccionada: $val (target ESP-IDF: $_targetIdfSeleccionado)',
                        );
                        Navigator.of(ctx).pop();
                      }
                    },
                  ),
                  title: Text(opcion, style: const TextStyle(fontSize: 13)),
                  subtitle: Text(
                    'idf.py set-target $target',
                    style: const TextStyle(fontSize: 11),
                  ),
                  onTap: () {
                    _seleccionarPlacaPorNombre(opcion);
                    _agregarLog(
                      'Placa seleccionada: $opcion (target ESP-IDF: $_targetIdfSeleccionado)',
                    );
                    Navigator.of(ctx).pop();
                  },
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _detectarPlacaYPuertoFisico(sondearEsptool: true);
              },
              child: const Text('Autodetectar', style: TextStyle(fontSize: 12)),
            ),
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Cerrar', style: TextStyle(fontSize: 12)),
            ),
          ],
        );
      },
    );
  }

  void _mostrarDialogoPuerto(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext ctx) {
        final List<String> puertos = [
          _puertoSeleccionado,
          'COM3',
          'COM4',
          '/dev/ttyUSB0',
          '/dev/ttyACM0',
          'No detectado',
        ].toSet().toList();
        return AlertDialog(
          title: const Text(
            'Herramientas -> Puerto',
            style: TextStyle(fontSize: 15),
          ),
          content: SizedBox(
            width: 280,
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: puertos.length,
              itemBuilder: (context, index) {
                final puerto = puertos[index];
                return ListTile(
                  leading: Radio<String>(
                    value: puerto,
                    groupValue: _puertoSeleccionado,
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _puertoSeleccionado = val);
                        _agregarLog('Puerto físico configurado: $val');
                        Navigator.of(ctx).pop();
                      }
                    },
                  ),
                  title: Text(puerto, style: const TextStyle(fontSize: 13)),
                  onTap: () {
                    setState(() => _puertoSeleccionado = puerto);
                    _agregarLog('Puerto físico configurado: $puerto');
                    Navigator.of(ctx).pop();
                  },
                );
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _detectarPlacaYPuertoFisico();
              },
              child: const Text('Redetectar', style: TextStyle(fontSize: 12)),
            ),
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Cerrar', style: TextStyle(fontSize: 12)),
            ),
          ],
        );
      },
    );
  }

  void _autoFormatoCodigo() {
    final texto = _codigoController.text;
    final lineas = texto.split('\n');
    final buffer = StringBuffer();
    int indentacion = 0;
    for (var linea in lineas) {
      final limpia = linea.trim();
      if (limpia.isEmpty) {
        buffer.writeln();
        continue;
      }
      if (limpia.startsWith('}')) {
        indentacion = indentacion > 2 ? indentacion - 2 : 0;
      }
      buffer.writeln('${' ' * indentacion}$limpia');
      if (limpia.endsWith('{')) {
        indentacion += 2;
      }
    }
    setState(() {
      _codigoController.text = buffer.toString().trim();
    });
    _agregarLog('Auto Formato aplicado al código fuente.');
  }

  void _manejarMenuAccion(BuildContext context, String titulo, String valor) {
    if (titulo == 'Ayuda') {
      final AccionesAyuda? acciones = widget.accionesAyuda;
      if (acciones == null) {
        _agregarLog('Módulo de Ayuda no disponible.');
        return;
      }
      if (valor == 'Documentación') {
        acciones.abrirDocumentacion?.call(context);
      } else if (valor == 'Preguntas frecuentes') {
        acciones.abrirPreguntasFrecuentes?.call(context);
      } else if (valor == 'Créditos') {
        acciones.abrirCreditos?.call(context);
      } else if (valor == 'Acerca de') {
        acciones.abrirAcercaDe?.call(context);
      } else if (valor == 'Enlaces rápidos') {
        acciones.abrirEnlacesRapidos?.call(context);
      }
      return;
    }
    if (titulo == 'Sketch') {
      if (valor == 'Verificar / Compilar') {
        _compilarConEspIdf();
        return;
      }
      if (valor == 'Exportar binario') {
        _compilarConEspIdf(mostrarRutasBinarios: true);
        return;
      }
      if (valor == 'Subir') {
        if (_puertoSeleccionado == 'No detectado' ||
            _puertoSeleccionado == 'Buscando...') {
          _agregarLog(
            'ERROR: Conecte y seleccione un puerto válido antes de flashear.',
          );
        } else {
          _compilarConEspIdf(mostrarRutasBinarios: true);
        }
        return;
      }
    }
    if (titulo == 'Herramientas') {
      if (valor == 'Placa') {
        _mostrarDialogoPlaca(context);
        return;
      }
      if (valor == 'Puerto') {
        _mostrarDialogoPuerto(context);
        return;
      }
      if (valor == 'Detectar placa ESP32') {
        _detectarPlacaYPuertoFisico(sondearEsptool: true);
        return;
      }
      if (valor == 'Estado ESP-IDF') {
        _verificarEstadoEspIdf();
        return;
      }
      if (valor == 'Auto Formato') {
        _autoFormatoCodigo();
        return;
      }
      if (valor == 'Monitor Serie') {
        _agregarLog(
          'Monitor Serie preparado para $_puertoSeleccionado (115200 baud).',
        );
        return;
      }
      if (valor == 'Recargar datos') {
        _inicializarConexionHardware();
        return;
      }
      _agregarLog('Menú [Herramientas] -> $valor');
      return;
    }
    if (titulo == 'Archivo') {
      switch (valor) {
        case 'Nuevo':
          setState(() {
            _codigoController.text = _plantillaEspIdfPredeterminada;
          });
          _agregarLog('Nuevo proyecto C para Espressif ESP-IDF inicializado.');
          break;
        case 'Abrir':
          _agregarLog('Usa el módulo Archivo para abrir proyectos locales.');
          break;
        case 'Guardar':
          _agregarLog('Proyecto sincronizado en área de trabajo.');
          break;
        case 'Salir':
          _agregarLog('Cerrando IDE...');
          break;
        default:
          _agregarLog('Menú [Archivo] -> $valor');
      }
      return;
    }
    _agregarLog('Menú [$titulo] -> $valor');
  }
}
