import 'package:flutter/material.dart';

import '../../servicios/api_herramientas.dart';
import '../../servicios/api_ide.dart';

/// Vista principal del modulo Herramientas orientada al ecosistema Espressif ESP-IDF.
class VistaPrincipal extends StatefulWidget {
  const VistaPrincipal({super.key, required this.api, required this.ideApi});

  final ApiHerramientas api;
  final ApiIde ideApi;

  @override
  State<VistaPrincipal> createState() => _VistaPrincipalState();
}

class _VistaPrincipalState extends State<VistaPrincipal> {
  List<Map<String, dynamic>> _puertos = const [];
  String _estado = 'Verificando backend y toolchain Espressif...';
  bool _moduloActivo = false;

  @override
  void initState() {
    super.initState();
    _refrescar();
  }

  Future<void> _refrescar() async {
    final rPuertos = await widget.api.listarPuertos();
    if (!rPuertos.ok) {
      if (!mounted) return;
      setState(() => _estado = 'Error puertos: ${rPuertos.error}');
      return;
    }

    final moduloActivo = await widget.ideApi.moduloActivo('herramientas');
    if (!mounted) return;

    final lista = rPuertos.data ?? const [];
    final espDetectadas = lista.where((p) => p['es_esp32'] == true).length;

    setState(() {
      _puertos = lista;
      _moduloActivo = moduloActivo;
      _estado =
          'Puertos: ${_puertos.length} (ESP32: $espDetectadas) | Modulo: ${moduloActivo ? "Activo" : "Inactivo"}';
    });
  }

  void _mostrarMensaje(String mensaje, {bool esError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(mensaje),
        backgroundColor: esError ? Colors.red : Colors.teal.shade700,
      ),
    );
  }

  Widget _contenidoPrincipal() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(
                    _moduloActivo ? Icons.check_circle : Icons.error,
                    color: _moduloActivo ? Colors.green : Colors.red,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _estado,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ElevatedButton.icon(
                onPressed: _refrescar,
                icon: const Icon(Icons.refresh),
                label: const Text('Refrescar'),
              ),
              ElevatedButton.icon(
                onPressed: () async {
                  final r = await widget.api.detectarPlaca(sondear: true);
                  if (!r.ok) {
                    _mostrarMensaje('Deteccion: ${r.error}', esError: true);
                    return;
                  }
                  final rec = r.data?['recomendada'] as Map<String, dynamic>?;
                  if (rec != null) {
                    _mostrarMensaje(
                      'Detectada ${rec['placa_sugerida']} (${rec['target_idf']}) en ${rec['dispositivo']}',
                    );
                  } else {
                    _mostrarMensaje(
                      'No se detectaron placas Espressif ESP32 conectadas.',
                      esError: true,
                    );
                  }
                },
                icon: const Icon(Icons.usb),
                label: const Text('Detectar Placa ESP32'),
              ),
              ElevatedButton.icon(
                onPressed: () async {
                  final r = await widget.api.estadoEspIdf();
                  if (!r.ok) {
                    _mostrarMensaje('Estado ESP-IDF: ${r.error}',
                        esError: true);
                    return;
                  }
                  final disp = r.data?['esp_idf_disponible'] == true;
                  final ver = r.data?['version'] ?? 'No instalado';
                  _mostrarMensaje(
                    disp
                        ? 'Espressif ESP-IDF disponible: $ver'
                        : 'ESP-IDF no detectado (configure IDF_PATH).',
                    esError: !disp,
                  );
                },
                icon: const Icon(Icons.developer_board),
                label: const Text('Estado ESP-IDF'),
              ),
              ElevatedButton.icon(
                onPressed: () async {
                  final r = await widget.api.listarPlacasSoportadas();
                  if (!r.ok) {
                    _mostrarMensaje('Perfiles: ${r.error}', esError: true);
                    return;
                  }
                  _mostrarMensaje(
                    'Perfiles Espressif soportados: ${r.data?.length ?? 0}',
                  );
                },
                icon: const Icon(Icons.memory),
                label: const Text('Perfiles ESP-IDF'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Puertos Serie (${_puertos.length})',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: ListView.builder(
                    itemCount: _puertos.length,
                    itemBuilder: (context, i) {
                      final p = _puertos[i];
                      final esEsp = p['es_esp32'] == true;
                      final placa = p['placa_sugerida'] as String?;
                      final target = p['target_idf'] as String?;
                      return ListTile(
                        leading: Icon(
                          esEsp ? Icons.developer_board : Icons.usb,
                          color: esEsp ? Colors.green : null,
                        ),
                        title: Text(p['dispositivo']?.toString() ?? ''),
                        subtitle: Text(
                          esEsp && placa != null
                              ? '$placa (target: $target) — ${p['descripcion'] ?? ''}'
                              : (p['descripcion']?.toString() ?? ''),
                        ),
                        trailing: Text(p['fabricante']?.toString() ?? ''),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return _contenidoPrincipal();
  }
}
