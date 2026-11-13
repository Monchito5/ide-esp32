// Archivo: modules/simulacion/frontend/lib/widgets/simulation_terminal.dart
import 'package:flutter/material.dart';

/// Terminal de consola para la simulacion.
/// Muestra la salida UART y permite enviar comandos al dispositivo virtual.
class SimulationTerminal extends StatefulWidget {
  const SimulationTerminal({super.key, required this.sesionId});

  final String sesionId;

  @override
  State<SimulationTerminal> createState() => _SimulationTerminalState();
}

class _SimulationTerminalState extends State<SimulationTerminal> {
  final List<String> _lineas = [];
  final TextEditingController _controlador = TextEditingController();
  bool _autoscroll = true;
  final ScrollController _scrollController = ScrollController();

  void _agregarLinea(String texto) {
    setState(() {
      _lineas.insert(0, texto);
      if (_lineas.length > 200) {
        _lineas.removeLast();
      }
    });
    if (_autoscroll) {
      _scrollController.jumpTo(0);
    }
  }

  void _enviarComando() {
    final comando = _controlador.text.trim();
    if (comando.isEmpty) return;
    _agregarLinea('> $comando');
    _controlador.clear();
  }

  @override
  void dispose() {
    _controlador.dispose();
    _scrollController.dispose();
    super.dispose();
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
              'Consola UART',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 8),
            Container(
              height: 200,
              color: const Color(0xFF1E1E1E),
              child: ListView.builder(
                controller: _scrollController,
                reverse: true,
                itemCount: _lineas.length,
                itemBuilder: (context, i) {
                  final esComando = _lineas[i].startsWith('>');
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 1),
                    child: Text(
                      _lineas[i],
                      style: TextStyle(
                        color: esComando
                            ? Colors.cyan
                            : const Color(0xFF8DC63F),
                        fontFamily: 'monospace',
                        fontSize: 11,
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controlador,
                    decoration: const InputDecoration(
                      hintText: 'Comando UART...',
                      border: InputBorder.none,
                      isDense: true,
                    ),
                    onSubmitted: (_) => _enviarComando(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _enviarComando,
                ),
                const SizedBox(width: 8),
                Checkbox(
                  value: _autoscroll,
                  onChanged: (v) => setState(() => _autoscroll = v ?? true),
                ),
                const Text('Autoscroll', style: TextStyle(fontSize: 11)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
