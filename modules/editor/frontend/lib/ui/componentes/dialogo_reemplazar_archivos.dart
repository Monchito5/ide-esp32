// Archivo: modules/editor/frontend/lib/ui/componentes/dialogo_reemplazar_archivos.dart
import 'package:flutter/material.dart';
import '../../servicios/api_editor.dart';

/// Cuadro de dialogo para buscar y reemplazar texto en multiples archivos del proyecto.
///
/// Responsabilidad asignada a Dev C (Nathaniel).
class DialogoReemplazarArchivos extends StatefulWidget {
  const DialogoReemplazarArchivos({
    super.key,
    required this.api,
    this.terminoInicial = '',
  });

  final ApiEditor api;
  final String terminoInicial;

  static Future<void> mostrar(BuildContext context,
      {required ApiEditor api, String terminoInicial = ''}) {
    return showDialog<void>(
      context: context,
      builder: (ctx) => DialogoReemplazarArchivos(
        api: api,
        terminoInicial: terminoInicial,
      ),
    );
  }

  @override
  State<DialogoReemplazarArchivos> createState() =>
      _DialogoReemplazarArchivosState();
}

class _DialogoReemplazarArchivosState extends State<DialogoReemplazarArchivos> {
  late final TextEditingController _terminoController;
  final TextEditingController _reemplazoController = TextEditingController();
  bool _sensibleMayusculas = false;
  bool _cargando = false;
  String _mensajeResultado = '';

  @override
  void initState() {
    super.initState();
    _terminoController = TextEditingController(text: widget.terminoInicial);
  }

  @override
  void dispose() {
    _terminoController.dispose();
    _reemplazoController.dispose();
    super.dispose();
  }

  Future<void> _ejecutarReemplazo() async {
    final termino = _terminoController.text.trim();
    final reemplazo = _reemplazoController.text;

    if (termino.isEmpty) {
      setState(() => _mensajeResultado = 'Especifique el término a buscar.');
      return;
    }

    setState(() {
      _cargando = true;
      _mensajeResultado = 'Procesando archivos del proyecto...';
    });

    final res = await widget.api.reemplazarEnArchivos(
      termino,
      reemplazo,
      sensibleMayusculas: _sensibleMayusculas,
    );

    setState(() {
      _cargando = false;
      if (res['exitoso'] == true) {
        final mod = res['archivos_modificados'] ?? 0;
        final tot = res['total_reemplazos'] ?? 0;
        _mensajeResultado = 'Éxito: $tot reemplazos en $mod archivo(s).';
      } else {
        _mensajeResultado = 'Error: ${res['error'] ?? 'No se pudo completar el reemplazo.'}';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.find_replace, size: 20, color: Color(0xFF007ACC)),
          SizedBox(width: 8),
          Text('Reemplazar en archivos', style: TextStyle(fontSize: 16)),
        ],
      ),
      content: SizedBox(
        width: 420,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _terminoController,
              decoration: const InputDecoration(
                labelText: 'Texto a buscar',
                isDense: true,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _reemplazoController,
              decoration: const InputDecoration(
                labelText: 'Reemplazar con',
                isDense: true,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Checkbox(
                  value: _sensibleMayusculas,
                  onChanged: (v) =>
                      setState(() => _sensibleMayusculas = v ?? false),
                ),
                const Text('Sensible a mayúsculas',
                    style: TextStyle(fontSize: 12)),
              ],
            ),
            if (_mensajeResultado.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                _mensajeResultado,
                style: TextStyle(
                  fontSize: 12,
                  color: _mensajeResultado.startsWith('Éxito')
                      ? Colors.green
                      : Colors.orange,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
            if (_cargando) ...[
              const SizedBox(height: 8),
              const LinearProgressIndicator(),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cerrar'),
        ),
        ElevatedButton(
          onPressed: _cargando ? null : _ejecutarReemplazo,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF007ACC),
            foregroundColor: Colors.white,
          ),
          child: const Text('Reemplazar todo'),
        ),
      ],
    );
  }
}
