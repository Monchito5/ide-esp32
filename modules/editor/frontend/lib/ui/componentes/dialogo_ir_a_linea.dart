// Archivo: modules/editor/frontend/lib/ui/componentes/dialogo_ir_a_linea.dart
import 'package:flutter/material.dart';

/// Cuadro de dialogo para la funcion "Go to Line" (Ir a la linea).
///
/// Responsabilidad asignada a Dev C (Nathaniel).
class DialogoIrALinea extends StatefulWidget {
  const DialogoIrALinea({
    super.key,
    required this.totalLineas,
    required this.lineaActual,
  });

  final int totalLineas;
  final int lineaActual;

  static Future<int?> mostrar(BuildContext context,
      {required int totalLineas, required int lineaActual}) {
    return showDialog<int>(
      context: context,
      builder: (ctx) => DialogoIrALinea(
        totalLineas: totalLineas,
        lineaActual: lineaActual,
      ),
    );
  }

  @override
  State<DialogoIrALinea> createState() => _DialogoIrALineaState();
}

class _DialogoIrALineaState extends State<DialogoIrALinea> {
  final TextEditingController _controller = TextEditingController();
  String? _error;

  @override
  void initState() {
    super.initState();
    _controller.text = widget.lineaActual.toString();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _confirmar() {
    final int? linea = int.tryParse(_controller.text.trim());
    if (linea == null || linea < 1 || linea > widget.totalLineas) {
      setState(() {
        _error = 'Ingrese una línea válida entre 1 y ${widget.totalLineas}.';
      });
      return;
    }
    Navigator.of(context).pop(linea);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Ir a la línea', style: TextStyle(fontSize: 16)),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Línea actual: ${widget.lineaActual} (Rango disponible: 1 - ${widget.totalLineas})',
            style: const TextStyle(fontSize: 12, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _controller,
            autofocus: true,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: 'Número de línea',
              errorText: _error,
              isDense: true,
              border: const OutlineInputBorder(),
            ),
            onSubmitted: (_) => _confirmar(),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          onPressed: _confirmar,
          child: const Text('Ir'),
        ),
      ],
    );
  }
}
