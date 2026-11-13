import 'package:flutter/material.dart';

import '../../servicios/api_herramientas.dart';
import '../../servicios/api_ide.dart';

/// Vista principal del modulo Herramientas con barra lateral de navegacion.
///
/// Fusiona la vista original de herramientas (estado, botones rapidos y lista
/// de puertos) con la barra lateral (NavigationRail) del mockup:
/// Sketch, Placas, Librerias, Monitor, Plotter e Informacion de la placa.
class VistaPrincipal extends StatefulWidget {
  const VistaPrincipal({super.key, required this.api, required this.ideApi});

  final ApiHerramientas api;
  final ApiIde ideApi;

  @override
  State<VistaPrincipal> createState() => _VistaPrincipalState();
}

class _VistaPrincipalState extends State<VistaPrincipal> {
  List<Map<String, dynamic>> _puertos = const [];
  String _estado = 'Verificando backend...';
  bool _moduloActivo = false;

  @override
  void initState() {
    super.initState();
    _refrescar();
  }

  Future<void> _refrescar() async {
    // Obtener puertos serie
    final rPuertos = await widget.api.listarPuertos();
    if (!rPuertos.ok) {
      setState(() => _estado = 'Error puertos: ${rPuertos.error}');
      return;
    }

    // Verificar si el modulo esta activo
    final moduloActivo = await widget.ideApi.moduloActivo('herramientas');

    setState(() {
      _puertos = rPuertos.data ?? const [];
      _moduloActivo = moduloActivo;
      _estado =
          'Puertos detectados: ${_puertos.length} | Modulo: ${moduloActivo ? "Activo" : "Inactivo"}';
    });
  }

  void _mostrarError(String mensaje) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(mensaje), backgroundColor: Colors.red),
    );
  }

  Widget _contenidoPrincipal() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Estado general
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        _moduloActivo ? Icons.check_circle : Icons.error,
                        color: _moduloActivo ? Colors.green : Colors.red,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _estado,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Botones de acciones rapidas
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
                  final r = await widget.api.listarPlacas();
                  if (!r.ok) _mostrarError('Placas: ${r.error}');
                },
                icon: const Icon(Icons.memory),
                label: const Text('Placas Arduino'),
              ),
              ElevatedButton.icon(
                onPressed: () async {
                  final r = await widget.api.versionArduinoCli();
                  if (!r.ok) _mostrarError('Version Arduino: ${r.error}');
                },
                icon: const Icon(Icons.info),
                label: const Text('Version Arduino'),
              ),
              ElevatedButton.icon(
                onPressed: () async {
                  final r = await widget.api.estadoPlatformIO();
                  if (!r.ok) _mostrarError('Estado PlatformIO: ${r.error}');
                },
                icon: const Icon(Icons.build),
                label: const Text('Estado PlatformIO'),
              ),
              ElevatedButton.icon(
                onPressed: () async {
                  final r = await widget.api.versionEspIdf();
                  if (!r.ok) _mostrarError('Version ESP-IDF: ${r.error}');
                },
                icon: const Icon(Icons.settings),
                label: const Text('Version ESP-IDF'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Lista de puertos
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Puertos Serie ($_puertos.length)',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: ListView.builder(
                    itemCount: _puertos.length,
                    itemBuilder: (context, i) {
                      final p = _puertos[i];
                      return ListTile(
                        leading: const Icon(Icons.usb),
                        title: Text(p['dispositivo'] ?? ''),
                        subtitle: Text(p['descripcion'] ?? ''),
                        trailing: Text(p['fabricante'] ?? ''),
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
