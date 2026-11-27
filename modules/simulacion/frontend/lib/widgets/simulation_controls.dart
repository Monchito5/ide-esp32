// Archivo: modules/simulacion/frontend/lib/widgets/simulation_controls.dart
import 'package:flutter/material.dart';

import '../../api_simulacion.dart';

/// Controles de simulacion: iniciar, detener, reiniciar, flashear.
class SimulationControls extends StatefulWidget {
  const SimulationControls({
    super.key,
    required this.api,
    required this.sesionId,
  });

  final ApiSimulacion api;
  final String sesionId;

  @override
  State<SimulationControls> createState() => _SimulationControlsState();
}

class _SimulationControlsState extends State<SimulationControls> {
  final SimulationService _service = SimulationService();
  Map<String, dynamic> _estado = {};
  bool _cargando = false;

  @override
  void initState() {
    super.initState();
    _cargarEstado();
  }

  Future<void> _cargarEstado() async {
    final r = await widget.api.obtenerSesion(widget.sesionId);
    if (r.ok) {
      setState(() => _estado = r.data ?? {});
    }
  }

  Future<void> _ejecutarAccion(
    String accion,
    Future<Map<String, dynamic>> future,
  ) async {
    setState(() => _cargando = true);
    final r = await future;
    setState(() => _cargando = false);
    if (!r.ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${r.error}'),
          backgroundColor: Colors.red,
        ),
      );
    } else {
      setState(() => _estado = r.data ?? {});
    }
  }

  @override
  Widget build(BuildContext context) {
    final estado = _estado['estado'] ?? 'desconocido';
    final estaActiva = estado == 'iniciada';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Controles de Simulacion',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Text('Estado: '),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: estaActiva
                        ? Colors.green.withOpacity(0.2)
                        : Colors.grey.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: estaActiva ? Colors.green : Colors.grey,
                    ),
                  ),
                  child: Text(
                    estado.toUpperCase(),
                    style: TextStyle(
                      color: estaActiva ? Colors.green : Colors.grey,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Iniciar'),
                    onPressed: estaActiva
                        ? null
                        : () => _ejecutarAccion(
                            'iniciar',
                            widget.api.iniciarSesion(widget.sesionId),
                          ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.stop),
                    label: const Text('Detener'),
                    onPressed: !estaActiva
                        ? null
                        : () => _ejecutarAccion(
                            'detener',
                            widget.api.detenerSesion(widget.sesionId),
                          ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.restart_alt),
                    label: const Text('Reiniciar'),
                    onPressed: !estaActiva
                        ? null
                        : () => _ejecutarAccion(
                            'reiniciar',
                            widget.api.reiniciarSesion(widget.sesionId),
                          ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.file_upload),
                    label: const Text('Flashear'),
                    onPressed: !estaActiva
                        ? null
                        : () => _mostrarDialogoFlashear(),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              _estado['firmware_cargado'] != null
                  ? 'Firmware: ${_estado['firmware_cargado']}'
                  : 'Sin firmware cargado',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _mostrarDialogoFlashear() async {
    String archivo = '';
    String direccion = '0x10000';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Flashear Firmware'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: const InputDecoration(labelText: 'Archivo (.bin)'),
              onChanged: (v) => archivo = v,
            ),
            const SizedBox(height: 8),
            TextField(
              decoration: const InputDecoration(labelText: 'Direccion'),
              onChanged: (v) => direccion = v,
            ),
          ],
        ),
        actions: [
          TextButton(
            child: const Text('Cancelar'),
            onPressed: () => Navigator.of(context).pop(),
          ),
          ElevatedButton(
            child: const Text('Flashear'),
            onPressed: () async {
              Navigator.of(context).pop();
              final r = await widget.api.flashearSesion(widget.sesionId, {
                'archivo': archivo,
                'direccion': direccion,
              });
              if (!r.ok) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Error: ${r.error}'),
                    backgroundColor: Colors.red,
                  ),
                );
              } else {
                setState(() => _estado = r.data ?? {});
              }
            },
          ),
        ],
      ),
    );
  }
}
