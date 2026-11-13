// Archivo: modules/simulacion/frontend/lib/ui/screens/configuracion_screen.dart
import 'package:flutter/material.dart';

/// Pantalla de configuracion del modulo Simulacion.
class ConfiguracionScreen extends StatefulWidget {
  const ConfiguracionScreen({super.key});

  @override
  State<ConfiguracionScreen> createState() => _ConfiguracionScreenState();
}

class _ConfiguracionScreenState extends State<ConfiguracionScreen> {
  String _motorSeleccionado = 'esp_emulator';
  String _chipPredeterminado = 'ESP32-S3';
  int _tiempoEsperaPredeterminado = 30;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Configuracion de Simulacion',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1B3A5C),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Motor de Emulador Predeterminado',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  DropdownButton<String>(
                    value: _motorSeleccionado,
                    items: const [
                      DropdownMenuItem(
                        value: 'esp_emulator',
                        child: Text('ESP Emulator'),
                      ),
                      DropdownMenuItem(value: 'qemu', child: Text('QEMU')),
                    ],
                    onChanged: (v) => setState(
                      () => _motorSeleccionado = v ?? 'esp_emulator',
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Chip Predeterminado',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  DropdownButton<String>(
                    value: _chipPredeterminado,
                    items: const [
                      DropdownMenuItem(
                        value: 'ESP32-S3',
                        child: Text('ESP32-S3'),
                      ),
                      DropdownMenuItem(value: 'ESP32', child: Text('ESP32')),
                      DropdownMenuItem(
                        value: 'ESP32-C3',
                        child: Text('ESP32-C3'),
                      ),
                    ],
                    onChanged: (v) =>
                        setState(() => _chipPredeterminado = v ?? 'ESP32-S3'),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Tiempo de Espera Predeterminado (segundos)',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    decoration: const InputDecoration(
                      labelText: 'Tiempo de espera',
                      hintText: '30',
                    ),
                    keyboardType: TextInputType.number,
                    onChanged: (v) => setState(
                      () => _tiempoEsperaPredeterminado = int.tryParse(v) ?? 30,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.save),
                    label: const Text('Guardar Configuracion'),
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Configuracion guardada')),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
