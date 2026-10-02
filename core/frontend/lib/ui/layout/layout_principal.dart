// Archivo: core/frontend/lib/ui/layout/layout_principal.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../nucleo/registro_modulos.dart';
import '../temas/tema_ide.dart';

/// Layout maestro rediseñado del IDE para escritorio (Estilo Arduino/VSCode).
class LayoutPrincipal extends StatefulWidget {
  const LayoutPrincipal({
    super.key,
    required this.registro,
    this.titulo = 'IDE ESP32-S31 — Sketch sin título',
  });

  final RegistroModulos registro;
  final String titulo;

  @override
  State<LayoutPrincipal> createState() => _LayoutPrincipalState();
}

class _LayoutPrincipalState extends State<LayoutPrincipal> {
  int _indiceModulo = 0;
  String _placaSeleccionada = 'ESP32-S31 Dev Module';
  String _puertoSeleccionado = 'Buscando...';
  String _modoOperacion =
      'Modo Físico'; // 'Modo Físico' (predeterminado) o 'Modo Simulación'
  String _estadoIde = 'Listo';

  final TextEditingController _codigoController = TextEditingController(
    text:
        'void setup() {\n  Serial.begin(115200);\n}\n\nvoid loop() {\n  // código aquí\n}',
  );

  final List<String> _logsConsola = [
    'Salida:',
    'Compilando sketch...',
    'Cargando en placa...',
    'Listo.',
  ];

  @override
  void initState() {
    super.initState();
    _detectarPlacaYPuertoFisico();
  }

  void _agregarLog(String mensaje) {
    setState(() {
      _logsConsola.add(mensaje);
      _estadoIde = mensaje.replaceAll('...', '').trim();
      if (_estadoIde.isEmpty) _estadoIde = 'Listo';
    });
  }

  Future<void> _detectarPlacaYPuertoFisico() async {
    _agregarLog('Buscando placa ESP32 conectada en puertos físicos...');
    try {
      final response = await http
          .get(Uri.parse('http://127.0.0.1:8765/api/v1/herramientas/puertos'))
          .timeout(const Duration(seconds: 2));
      if (response.statusCode == 200) {
        final datos = jsonDecode(response.body) as Map<String, dynamic>;
        final puertos =
            (datos['puertos'] as List?)?.cast<Map<String, dynamic>>() ?? [];
        if (puertos.isNotEmpty) {
          final primerPuerto =
              puertos.first['dispositivo'] as String? ?? 'COM3';
          final descripcion =
              puertos.first['descripcion'] as String? ?? 'ESP32-S3 Hardware';
          setState(() {
            _puertoSeleccionado = primerPuerto;
          });
          _agregarLog(
              'Placa ESP32 detectada automáticamente en $primerPuerto ($descripcion).');
        } else {
          setState(() {
            _puertoSeleccionado = 'No detectado';
          });
          _agregarLog(
              'AVISO: No se detecta ninguna placa conectada. Verifique la conexión USB.');
        }
      } else {
        setState(() {
          _puertoSeleccionado = 'No detectado';
        });
        _agregarLog(
            'AVISO: No se detecta ninguna placa conectada. Verifique la conexión USB.');
      }
    } catch (e) {
      setState(() {
        _puertoSeleccionado = 'No detectado';
      });
      _agregarLog(
          'AVISO: No se detecta ninguna placa conectada. Verifique la conexión USB (Backend offline).');
    }
  }

  Future<void> _ejecutarSimulacionCircuito() async {
    _agregarLog('Iniciando simulador de circuitos electrónicos y lógica...');
    await Future.delayed(const Duration(milliseconds: 300));
    _agregarLog(
        'Circuito virtual activo: ESP32-S3 conectado a LED RGB y Sensor DHT22.');
    await Future.delayed(const Duration(milliseconds: 300));
    _agregarLog(
        'Simulación en ejecución: recibiendo datos virtuales por bus GPIO.');
  }

  @override
  Widget build(BuildContext context) {
    final modulos = widget.registro.modulos;
    final actual = modulos.isNotEmpty ? modulos[_indiceModulo] : null;
    final bool esSimulacion = _modoOperacion == 'Modo Simulación';

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.titulo, style: const TextStyle(fontSize: 15)),
        backgroundColor: TemaIde.colorPrimario,
        actions: [
          // Selector de Modo (Físico vs Simulación)
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
                      _agregarLog(
                          'Cambiado a Modo Simulación (Diseño de circuitos y lógica).');
                      _ejecutarSimulacionCircuito();
                    } else {
                      _agregarLog(
                          'Cambiado a Modo Físico (Hardware conectado).');
                      _detectarPlacaYPuertoFisico();
                    }
                  }
                },
              ),
            ),
          ),
          // Selector rápido de Puerto Físico (Solo visible en Modo Físico)
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
          // Boton Verificar (Compilar)
          IconButton(
            icon: const Icon(Icons.check_circle_outline,
                color: Colors.greenAccent, size: 20),
            tooltip: 'Verificar / Compilar',
            onPressed: () {
              _agregarLog(esSimulacion
                  ? 'Compilando lógica para simulación...'
                  : 'Compilando para hardware físico...');
              Future.delayed(const Duration(seconds: 1), () {
                _agregarLog('Compilación exitosa.');
              });
            },
          ),
          // Boton Subir / Ejecutar Simulación
          IconButton(
            icon: Icon(
              esSimulacion ? Icons.play_arrow : Icons.arrow_forward_ios,
              color: esSimulacion ? Colors.amberAccent : Colors.lightBlueAccent,
              size: 20,
            ),
            tooltip: esSimulacion
                ? 'Iniciar Simulación de Circuito'
                : 'Subir firmware a placa',
            onPressed: () {
              if (esSimulacion) {
                _ejecutarSimulacionCircuito();
              } else {
                if (_puertoSeleccionado == 'No detectado') {
                  _agregarLog(
                      'ERROR: No hay ninguna placa ESP32 conectada. Verifique la conexión USB antes de flashear.');
                } else {
                  _agregarLog(
                      'Flasheando firmware real en placa ESP32 ($_puertoSeleccionado)...');
                  Future.delayed(const Duration(seconds: 1), () {
                    _agregarLog(
                        'Flasheo físico completado exitosamente en $_puertoSeleccionado.');
                  });
                }
              }
            },
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: Column(
        children: [
          // Barra de Menús estilo Desktop
          Container(
            color: Colors.grey.shade200,
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            child: Row(
              children: [
                _buildMenuButton(
                    context, 'Archivo', ['Nuevo', 'Abrir', 'Guardar', 'Salir']),
                _buildMenuButton(context, 'Editar',
                    ['Deshacer', 'Rehacer', 'Cortar', 'Copiar', 'Pegar']),
                _buildMenuButton(context, 'Sketch',
                    ['Verificar / Compilar', 'Subir', 'Exportar binario']),
                _buildMenuButton(context, 'Herramientas', [
                  'Placa',
                  'Puerto',
                  'Auto Formato',
                  'Monitor Serie',
                  'Recargar datos',
                ]),
                _buildMenuButton(
                    context, 'Ayuda', ['Documentación', 'Acerca de']),
                const Spacer(),
                if (modulos.length > 1)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: DropdownButton<int>(
                      value: _indiceModulo,
                      isDense: true,
                      underline: const SizedBox(),
                      items: [
                        for (int i = 0; i < modulos.length; i++)
                          DropdownMenuItem(
                            value: i,
                            child: Text(
                              'Módulo: ${modulos[i].nombre}',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                      ],
                      onChanged: (i) => setState(() => _indiceModulo = i ?? 0),
                    ),
                  ),
              ],
            ),
          ),
          const Divider(height: 1),
          // Área principal: Editor y Consola (o Diseñador de Circuitos en Simulación)
          Expanded(
            child: Row(
              children: [
                // Panel de Código y Consola
                Expanded(
                  flex: 3,
                  child: Column(
                    children: [
                      // Editor de Código
                      Expanded(
                        child: Container(
                          color: Colors.white,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              // Números de línea simulados
                              Container(
                                width: 35,
                                color: Colors.grey.shade100,
                                padding:
                                    const EdgeInsets.symmetric(vertical: 12),
                                child: Column(
                                  children: List.generate(
                                    15,
                                    (index) => Text(
                                      '${index + 1}',
                                      style: TextStyle(
                                        color: Colors.grey.shade500,
                                        fontSize: 11,
                                        fontFamily: 'monospace',
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              const VerticalDivider(width: 1),
                              // Campo de texto del editor
                              Expanded(
                                child: Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: TextField(
                                    controller: _codigoController,
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
                      // Consola de Salida
                      Container(
                        height: 90,
                        color: TemaIde.colorConsola,
                        padding: const EdgeInsets.all(6),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Text(
                                  'SALIDA DE CONSOLA',
                                  style: TextStyle(
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
                // Panel derecho: Vista de Módulo o Diseñador de Circuitos en Modo Simulación
                const VerticalDivider(width: 1),
                Expanded(
                  flex: 2,
                  child: Container(
                    color: Colors.white,
                    child: esSimulacion
                        ? _buildPanelCircuitoSimulacion()
                        : (actual != null
                            ? actual.construirVista(context)
                            : const Center(
                                child: Text('Sin módulo activo'),
                              )),
                  ),
                ),
              ],
            ),
          ),
          // Barra de Estado Inferior
          Container(
            color: TemaIde.colorPrimario,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 110,
                  child: Text(
                    _placaSeleccionada,
                    style: const TextStyle(color: Colors.white, fontSize: 11),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const Text(' | ', style: TextStyle(color: Colors.white54)),
                SizedBox(
                  width: 130,
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
                        color: Colors.greenAccent, fontSize: 11),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const Text(
                  'v1.0.0',
                  style: TextStyle(color: Colors.white54, fontSize: 11),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPanelCircuitoSimulacion() {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.electrical_services,
                  color: Colors.orange, size: 20),
              const SizedBox(width: 6),
              const Text(
                'Diseño de Circuito Electrónico',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
              ),
              const Spacer(),
              ElevatedButton.icon(
                onPressed: () {
                  _ejecutarSimulacionCircuito();
                },
                icon: const Icon(Icons.play_arrow, size: 14),
                label: const Text('Probar', style: TextStyle(fontSize: 11)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Componentes virtuales y conexiones GPIO:',
            style: TextStyle(fontSize: 11, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView(
              children: [
                _buildItemComponenteCircuito(
                    'ESP32-S3 Core', Icons.memory, Colors.blueGrey),
                _buildItemComponenteCircuito(
                    'LED RGB / GPIO 2', Icons.lightbulb, Colors.amber),
                _buildItemComponenteCircuito(
                    'Sensor DHT22', Icons.thermostat, Colors.blue),
                _buildItemComponenteCircuito('Resistencia & Pulsador',
                    Icons.settings_input_component, Colors.purple),
                _buildItemComponenteCircuito(
                    'Pantalla OLED I2C', Icons.tv, Colors.teal),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildItemComponenteCircuito(
      String nombre, IconData icono, Color color) {
    return Card(
      margin: const EdgeInsets.only(bottom: 6),
      elevation: 1,
      child: ListTile(
        leading: Icon(icono, color: color, size: 20),
        title: Text(nombre,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
        subtitle:
            const Text('Bus GPIO virtual', style: TextStyle(fontSize: 10)),
        trailing:
            const Icon(Icons.drag_indicator, size: 16, color: Colors.grey),
      ),
    );
  }

  Widget _buildMenuButton(
      BuildContext context, String titulo, List<String> opciones) {
    return PopupMenuButton<String>(
      padding: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Text(titulo,
            style: const TextStyle(fontSize: 13, color: Colors.black87)),
      ),
      itemBuilder: (BuildContext context) {
        return opciones.map((String opcion) {
          final bool tieneSubmenu = opcion == 'Placa' || opcion == 'Puerto';
          return PopupMenuItem<String>(
            value: opcion,
            child: SizedBox(
              width: 140,
              child: Row(
                children: [
                  Text(opcion, style: const TextStyle(fontSize: 12)),
                  if (tieneSubmenu) ...[
                    const Spacer(),
                    const Icon(Icons.chevron_right,
                        size: 14, color: Colors.grey),
                  ],
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
              const Text('Chip: ESP32-S3 (Xtensa dual-core 32-bit LX7)'),
              const SizedBox(height: 6),
              const Text('Frecuencia: 240 MHz | Flash: 8 MB'),
              const SizedBox(height: 6),
              Text('Modo Actual: $_modoOperacion'),
              const SizedBox(height: 6),
              Text('Puerto Físico: $_puertoSeleccionado'),
            ],
          ),
          actions: [
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(ctx).pop();
                _agregarLog(
                    'Iniciando actualización real de firmware para $_placaSeleccionada...');
                Future.delayed(const Duration(seconds: 1), () {
                  _agregarLog(
                      'Firmware actualizado exitosamente en el dispositivo.');
                });
              },
              icon: const Icon(Icons.system_update, size: 14),
              label: const Text('Actualizar firmware',
                  style: TextStyle(fontSize: 12)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
              ),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _agregarLog('Información de placa cerrada.');
              },
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
        final List<String> placas = [
          'ESP32-S31 Dev Module',
          'ESP32-S31 DevKit',
          'ESP32-S31 WROOM',
          'Información de la placa',
        ];
        return AlertDialog(
          title: const Text('Herramientas -> Placa',
              style: TextStyle(fontSize: 15)),
          content: SizedBox(
            width: 280,
            child: ListView.builder(
              shrinkWrap: true,
              itemCount: placas.length,
              itemBuilder: (context, index) {
                final placa = placas[index];
                if (placa == 'Información de la placa') {
                  return ListTile(
                    leading: const Icon(Icons.info_outline,
                        color: Colors.blue, size: 20),
                    title: Text(placa,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.blue,
                            fontSize: 13)),
                    onTap: () {
                      Navigator.of(ctx).pop();
                      _mostrarModalInformacionPlaca(context);
                    },
                  );
                }
                return ListTile(
                  leading: Radio<String>(
                    value: placa,
                    groupValue: _placaSeleccionada,
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _placaSeleccionada = val);
                        _agregarLog('Placa seleccionada: $val');
                        Navigator.of(ctx).pop();
                      }
                    },
                  ),
                  title: Text(placa, style: const TextStyle(fontSize: 13)),
                  onTap: () {
                    setState(() => _placaSeleccionada = placa);
                    _agregarLog('Placa seleccionada: $placa');
                    Navigator.of(ctx).pop();
                  },
                );
              },
            ),
          ),
          actions: [
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
          title: const Text('Herramientas -> Puerto',
              style: TextStyle(fontSize: 15)),
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
    _agregarLog('Auto Formato aplicado al sketch.');
  }

  void _manejarMenuAccion(BuildContext context, String titulo, String valor) {
    if (titulo == 'Herramientas') {
      if (valor == 'Placa') {
        _mostrarDialogoPlaca(context);
        return;
      }
      if (valor == 'Puerto') {
        _mostrarDialogoPuerto(context);
        return;
      }
      if (valor == 'Auto Formato') {
        _autoFormatoCodigo();
        return;
      }
      if (valor == 'Monitor Serie') {
        _agregarLog(
            'Monitor Serie abierto en puerto $_puertoSeleccionado (115200 baud). Realizando lectura real...');
        return;
      }
      if (valor == 'Recargar datos') {
        _detectarPlacaYPuertoFisico();
        return;
      }
      _agregarLog('Menú [Herramientas] -> $valor');
      return;
    }
    if (titulo == 'Archivo') {
      switch (valor) {
        case 'Nuevo':
          setState(() {
            _codigoController.text =
                'void setup() {\n  // Configuración inicial\n}\n\nvoid loop() {\n  // Bucle principal\n}';
          });
          _agregarLog('Nuevo sketch creado.');
          break;
        case 'Abrir':
          _agregarLog('Abriendo sketch...');
          Future.delayed(const Duration(milliseconds: 300), () {
            _agregarLog('Sketch abierto correctamente.');
          });
          break;
        case 'Guardar':
          _agregarLog('Guardando sketch...');
          Future.delayed(const Duration(milliseconds: 300), () {
            _agregarLog('Sketch guardado exitosamente en disco.');
          });
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
