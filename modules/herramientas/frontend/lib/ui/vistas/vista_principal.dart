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
  int _selectedIndex = 0;
  List<Map<String, dynamic>> _puertos = const [];
  String _estado = 'Verificando backend...';
  Map<String, dynamic> _infoIde = {};
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

    // Obtener informacion del modulo y verificar si esta activo
    final infoModulo = await widget.ideApi.infoModuloHerramientas();
    final moduloActivo = await widget.ideApi.moduloActivo('herramientas');

    setState(() {
      _puertos = rPuertos.data ?? const [];
      _infoIde = infoModulo;
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
                  if (_infoIde.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Nombre: ${_infoIde['nombre'] ?? 'N/A'}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      'Version: ${_infoIde['version'] ?? 'N/A'}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
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
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF008A00),
        foregroundColor: Colors.white,
        title: const Text(
          'IDE ESP32-S31',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
        ),
        centerTitle: false,
      ),
      body: Column(
        children: [
          // Barra superior con menus
          Container(
            color: const Color(0xFF1B3A5C),
            height: 28,
            child: Row(
              children: [
                _menuItem('Archivo'),
                _menuItem('Editar'),
                _menuItem('Sketch'),
                _menuDesplegableHerramientas(),
                _menuItem('Ayuda'),
              ],
            ),
          ),
          // Cuerpo principal con barra lateral y contenido a la derecha
          Expanded(
            child: Row(
              children: [
                // Barra lateral (NavigationRail)
                NavigationRail(
                  selectedIndex: _selectedIndex,
                  onDestinationSelected: (index) {
                    setState(() => _selectedIndex = index);
                  },
                  labelType: NavigationRailLabelType.all,
                  backgroundColor: const Color(0xFF172B3D),
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
                  child: _contenidoPrincipal(),
                ),
              ],
            ),
          ),
          // Barra de estado
          Container(
            height: 22,
            color: const Color(0xFF1B3A5C),
            child: Row(
              children: [
                const SizedBox(width: 10),
                const Icon(Icons.devices, color: Colors.white70, size: 14),
                const SizedBox(width: 6),
                Text(
                  'ESP32-S31 Dev Module',
                  style: const TextStyle(color: Colors.white, fontSize: 11),
                ),
                const SizedBox(width: 16),
                const Icon(Icons.usb, color: Colors.white70, size: 14),
                const SizedBox(width: 6),
                Text(
                  'Ninguno',
                  style: const TextStyle(color: Colors.white, fontSize: 11),
                ),
                const Spacer(),
                const Text('Listo',
                    style: TextStyle(color: Colors.white, fontSize: 11)),
                const SizedBox(width: 10),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _menuItem(String texto) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10),
      child: Text(
        texto,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _menuDesplegableHerramientas() {
    return PopupMenuButton<int>(
      icon: const Icon(Icons.build, color: Colors.white, size: 16),
      tooltip: 'Herramientas',
      onSelected: (opcion) {
        switch (opcion) {
          case 0: // Auto Formato
            break;
          case 1: // Gestionar bibliotecas
            setState(() => _selectedIndex = 2);
            break;
          case 2: // Monitor Serie
            setState(() => _selectedIndex = 3);
            break;
          case 3: // Plotter Serie
            setState(() => _selectedIndex = 4);
            break;
          case 4: // Placa
            setState(() => _selectedIndex = 1);
            break;
          case 5: // Puerto
            break;
          case 6: // Recargar datos de la Placa
            _refrescar();
            break;
          case 7: // Obtener informacion de la placa
            break;
          case 8: // Grabar Bootloader
            break;
          case 9: // Actualizador de firmware
            break;
          case 10: // Cargar certificados raiz SSL
            break;
        }
      },
      itemBuilder: (_) => const [
        PopupMenuItem(value: 0, child: Text('Auto Formato')),
        PopupMenuItem(value: 1, child: Text('Gestionar bibliotecas')),
        PopupMenuItem(value: 2, child: Text('Monitor Serie')),
        PopupMenuItem(value: 3, child: Text('Plotter Serie')),
        PopupMenuItem(value: 4, child: Text('Placa')),
        PopupMenuItem(value: 5, child: Text('Puerto')),
        PopupMenuItem(value: 6, child: Text('Recargar datos de la Placa')),
        PopupMenuItem(value: 7, child: Text('Obtener informacion de la placa')),
        PopupMenuItem(value: 8, child: Text('Grabar Bootloader')),
        PopupMenuItem(value: 9, child: Text('Actualizador de firmware')),
        PopupMenuItem(value: 10, child: Text('Cargar certificados raiz SSL')),
      ],
    );
  }
}
