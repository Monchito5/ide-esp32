// Archivo: modules/simulacion/frontend/lib/ui/screens/simulacion_screen.dart
import 'package:flutter/material.dart';

import '../../api_simulacion.dart';
import '../../services/simulation_api.dart';
import '../widgets/simulation_controls.dart';
import '../widgets/simulation_terminal.dart';
import '../widgets/virtual_components.dart';
import '../widgets/virtual_board.dart';

/// Pantalla principal del modulo Simulacion.
/// Permite crear, administrar y monitorear sesiones de simulacion ESP32.
class SimulacionScreen extends StatefulWidget {
  const SimulacionScreen({super.key, required this.api});

  final ApiSimulacion api;

  @override
  State<SimulacionScreen> createState() => _SimulacionScreenState();
}

class _SimulacionScreenState extends State<SimulacionScreen> {
  final SimulationService _service = SimulationService();
  List<Map<String, dynamic>> _sesiones = [];
  String? _sesionSeleccionada;
  bool _cargando = false;
  String _mensaje = '';

  @override
  void initState() {
    super.initState();
    _cargarSesiones();
  }

  Future<void> _cargarSesiones() async {
    setState(() => _cargando = true);
    try {
      final r = await widget.api.listarSesiones();
      if (r.ok) {
        setState(() => _sesiones = r.data ?? []);
      } else {
        setState(() => _mensaje = 'Error: ${r.error}');
      }
    } catch (e) {
      setState(() => _mensaje = 'Error: $e');
    } finally {
      setState(() => _cargando = false);
    }
  }

  void _crearSesion() {
    _mostrarDialogoCrearSesion();
  }

  void _mostrarDialogoCrearSesion() {
    String chipSeleccionado = 'ESP32-S3';
    String motorSeleccionado = 'esp_emulator';
    String nombreSesion = '';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Nueva Sesion de Simulacion'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              decoration: const InputDecoration(labelText: 'Nombre'),
              onChanged: (v) => nombreSesion = v,
            ),
            const SizedBox(height: 8),
            DropdownButton<String>(
              value: chipSeleccionado,
              items: const [
                DropdownMenuItem(value: 'ESP32-S3', child: Text('ESP32-S3')),
                DropdownMenuItem(value: 'ESP32', child: Text('ESP32')),
                DropdownMenuItem(value: 'ESP32-C3', child: Text('ESP32-C3')),
              ],
              onChanged: (v) => chipSeleccionado = v ?? 'ESP32-S3',
            ),
            const SizedBox(height: 8),
            DropdownButton<String>(
              value: motorSeleccionado,
              items: const [
                DropdownMenuItem(
                    value: 'esp_emulator', child: Text('ESP Emulator')),
                DropdownMenuItem(value: 'qemu', child: Text('QEMU')),
              ],
              onChanged: (v) => motorSeleccionado = v ?? 'esp_emulator',
            ),
          ],
        ),
        actions: [
          TextButton(
            child: const Text('Cancelar'),
            onPressed: () => Navigator.of(context).pop(),
          ),
          ElevatedButton(
            child: const Text('Crear'),
            onPressed: () async {
              Navigator.of(context).pop();
              final r = await widget.api.crearSesion({
                'chip': chipSeleccionado,
                'motor': motorSeleccionado,
                'nombre': nombreSesion.isEmpty
                    ? 'Sesion ${chipSeleccionado}'
                    : nombreSesion,
              });
              if (r.ok) {
                _cargarSesiones();
                setState(() => _sesionSeleccionada = r.data?['sesion_id']);
              } else {
                setState(() => _mensaje = 'Error: ${r.error}');
              }
            },
          ),
        ],
      ),
    );
  }

  void _iniciarSesion(String sesionId) async {
    final r = await widget.api.iniciarSesion(sesionId);
    if (!r.ok) {
      setState(() => _mensaje = 'Error: ${r.error}');
    } else {
      _cargarSesiones();
    }
  }

  void _detenerSesion(String sesionId) async {
    final r = await widget.api.detenerSesion(sesionId);
    if (!r.ok) {
      setState(() => _mensaje = 'Error: ${r.error}');
    } else {
      _cargarSesiones();
    }
  }

  void _reiniciarSesion(String sesionId) async {
    final r = await widget.api.reiniciarSesion(sesionId);
    if (!r.ok) {
      setState(() => _mensaje = 'Error: ${r.error}');
    } else {
      _cargarSesiones();
    }
  }

  void _eliminarSesion(String sesionId) async {
    await _detenerSesion(sesionId);
    if (_sesionSeleccionada == sesionId) {
      setState(() => _sesionSeleccionada = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.sim_card, color: Color(0xFF1B3A5C), size: 28),
              const SizedBox(width: 8),
              const Text(
                'Simulacion ESP32',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1B3A5C),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (_mensaje.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.red.shade50,
              child: Text(
                _mensaje,
                style: const TextStyle(color: Colors.red, fontSize: 12),
              ),
            ),
          const SizedBox(height: 8),
          Row(
            children: [
              ElevatedButton.icon(
                icon: const Icon(Icons.add),
                label: const Text('Nueva Sesion'),
                onPressed: _crearSesion,
              ),
              const SizedBox(width: 8),
              const Text(
                'Modo: Simulacion Virtual',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
              ),
              const Spacer(),
              ElevatedButton.icon(
                icon: const Icon(Icons.refresh),
                label: const Text('Refrescar'),
                onPressed: _cargarSesiones,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator())
                : _sesiones.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.device_unknown,
                            size: 64, color: Colors.grey),
                        const SizedBox(height: 8),
                        Text(
                          'No hay sesiones de simulacion',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                        const SizedBox(height: 8),
                        ElevatedButton.icon(
                          icon: const Icon(Icons.add),
                          label: const Text('Crear Primera Sesion'),
                          onPressed: _crearSesion,
                        ),
                      ],
                    ),
                    )
                : ListView.builder(
                    itemCount: _sesiones.length,
                    itemBuilder: (context, i) {
                      final s = _sesiones[i];
                      final esSeleccionada = _sesionSeleccionada == s['sesion_id'];
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        child: ListTile(
                          leading: Icon(
                            s['estado'] == 'iniciada'
                                ? Icons.play_circle
                                : Icons.stop_circle,
                            color: s['estado'] == 'iniciada'
                                ? Colors.green
                                : Colors.grey,
                          ),
                          title: Text(s['nombre'] ?? 'Sesion'),
                          subtitle: Text(
                            '${s['chip']} • ${s['motor']} • ${s['estado']}',
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (s['estado'] != 'iniciada')
                                IconButton(
                                  icon: const Icon(Icons.play_arrow,
                                      color: Colors.green),
                                  onPressed: () => _iniciarSesion(s['sesion_id']),
                                ),
                              if (s['estado'] == 'iniciada') ...[
                                IconButton(
                                  icon: const Icon(Icons.stop,
                                      color: Colors.red),
                                  onPressed: () => _detenerSesion(s['sesion_id']),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.restart_alt,
                                      color: Colors.orange),
                                  onPressed: () => _reiniciarSesion(s['sesion_id']),
                                ),
                              ],
                              IconButton(
                                icon: const Icon(Icons.delete,
                                    color: Colors.grey),
                                onPressed: () => _eliminarSesion(s['sesion_id']),
                              ),
                            ],
                          ),
                          onTap: () => setState(() => _sesionSeleccionada = s['sesion_id']),
                          selected: esSeleccionada,
                        ),
                      );
                    },
                  ),
          ),
          if (_sesionSeleccionada != null)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Detalle de Sesion',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  SimulationControls(api: widget.api, sesionId: _sesionSeleccionada!),
                  const SizedBox(height: 16),
                  VirtualComponents(api: widget.api, sesionId: _sesionSeleccionada!),
                  const SizedBox(height: 16),
                  SimulationTerminal(api: widget.api, sesionId: _sesionSeleccionada!),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
