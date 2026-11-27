// Archivo: modules/simulacion/frontend/lib/widgets/virtual_board.dart
import 'package:flutter/material.dart';

/// Widget que representa visualmente una placa ESP32 virtual.
class VirtualBoard extends StatelessWidget {
  const VirtualBoard({
    super.key,
    required this.estado,
    this.chipModelo = 'ESP32-S3',
  });

  final String estado;
  final String chipModelo;

  @override
  Widget build(BuildContext context) {
    final colorEstado = estado == 'iniciada'
        ? Colors.green.shade400
        : Colors.grey.shade400;

    return Card(
      elevation: 4,
      child: Container(
        width: 260,
        height: 180,
        decoration: BoxDecoration(
          color: Colors.grey.shade900,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Container(
              height: 50,
              decoration: const BoxDecoration(
                color: Color(0xFF1B3A5C),
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(8),
                  topRight: Radius.circular(8),
                ),
              ),
              child: Center(
                child: Text(
                  'ESP32 Virtual',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: Colors.orange.shade700,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white, width: 2),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    chipModelo.replaceAll('ESP32-', ''),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Text(
                    'CPU',
                    style: TextStyle(color: Colors.white70, fontSize: 8),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: colorEstado.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: colorEstado, width: 1),
              ),
              child: Text(
                estado.toUpperCase(),
                style: TextStyle(
                  color: colorEstado,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const Spacer(),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _ledIndicador('PWR', estado == 'iniciada'),
                const SizedBox(width: 8),
                _ledIndicador('TX', estado == 'iniciada'),
                const SizedBox(width: 8),
                _ledIndicador('RX', estado == 'iniciada'),
              ],
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  Widget _ledIndicador(String nombre, bool encendido) {
    return Column(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: encendido ? Colors.green : Colors.grey.shade700,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 1),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          nombre,
          style: const TextStyle(color: Colors.white70, fontSize: 8),
        ),
      ],
    );
  }
}
