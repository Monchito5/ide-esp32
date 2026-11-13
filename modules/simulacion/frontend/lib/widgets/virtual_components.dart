// Archivo: modules/simulacion/frontend/lib/widgets/virtual_components.dart
import 'package:flutter/material.dart';

import '../../api_simulacion.dart';

/// Widget de componentes virtuales para la simulacion ESP32.
class VirtualComponents extends StatefulWidget {
  const VirtualComponents({
    super.key,
    required this.api,
    required this.sesionId,
  });

  final ApiSimulacion api;
  final String sesionId;

  @override
  State<VirtualComponents> createState() => _VirtualComponentsState();
}

class _VirtualComponentsState extends State<VirtualComponents> {
  List<Map<String, dynamic>> _componentes = [];
  bool _cargando = false;
  String _tipoSeleccionado = 'led';
  String _puertoSeleccionado = 'GPIO2';

  @override
  void initState() {
    super.initState();
    _cargarComponentes();
  }

  Future<void> _cargarComponentes() async {
    setState(() => _cargando = true);
    final r = await widget.api.obtenerReporte(widget.sesionId);
    if (r.ok) {
      setState(() => _componentes = r.data?['componentes'] ?? []);
    }
    setState(() => _cargando = false);
  }

  Future<void> _agregarComponente() async {
    final r = await widget.api.agregarComponente(
      widget.sesionId,
      {
        'id': 'comp_${DateTime.now().millisecondsSinceEpoch}',
        'tipo': _tipoSeleccionado,
        'puerto': _puertoSeleccionado,
      },
    );
    if (r.ok) {
      _cargarComponentes();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${r.error}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Componentes Virtuales',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                DropdownButton<String>(
                  value: _tipoSeleccionado,
                  items: const [
                    DropdownMenuItem(value: 'led', child: Text('LED')),
                    DropdownMenuItem(value: 'button', child: Text('Pulsador')),
                    DropdownMenuItem(value: 'sensor', child: Text('Sensor')),
                    DropdownMenuItem(value: 'display', child: Text('Pantalla')),
                  ],
                  onChanged: (v) => setState(() => _tipoSeleccionado = v ?? 'led'),
                ),
                const SizedBox(width: 8),
                DropdownButton<String>(
                  value: _puertoSeleccionado,
                  items: const [
                    DropdownMenuItem(value: 'GPIO2', child: Text('GPIO2')),
                    DropdownMenuItem(value: 'GPIO4', child: Text('GPIO4')),
                    DropdownMenuItem(value: 'GPIO5', child: Text('GPIO5')),
                    DropdownMenuItem(value: 'GPIO18', child: Text('GPIO18')),
                    DropdownMenuItem(value: 'GPIO19', child: Text('GPIO19')),
                    DropdownMenuItem(value: 'GPIO21', child: Text('GPIO21')),
                    DropdownMenuItem(value: 'GPIO22', child: Text('GPIO22')),
                    DropdownMenuItem(value: 'GPIO23', child: Text('GPIO23')),
                  ],
                  onChanged: (v) => setState(() => _puertoSeleccionado = v ?? 'GPIO2'),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text('Agregar'),
                  onPressed: _agregarComponente,
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (_componentes.isEmpty)
              const Text(
                'No hay componentes virtuales',
                style: TextStyle(color: Colors.grey, fontSize: 12),
              )
            else
              ..._componentes.map((c) => ListTile(
                leading: Icon(_iconoParaTipo(c['tipo']), color: Colors.blue),
                title: Text(c['tipo']),
                subtitle: Text('Puerto: ${c['puerto']} • Estado: ${c['estado']}'),
                trailing: Switch(
                  value: c['estado'] == 'activo',
                  onChanged: (_) {},
                ),
              )),
          ],
        ),
      ),
    );
  }

  IconData _iconoParaTipo(String tipo) {
    switch (tipo) {
      case 'led': return Icons.lightbulb;
      case 'button': return Icons.touch_app;
      case 'sensor': return Icons.sensors;
      case 'display': return Icons.display;
      default: return Icons.devices;
    }
  }
}
