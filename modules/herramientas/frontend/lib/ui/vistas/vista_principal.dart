// Archivo: modules/herramientas/frontend/lib/ui/vistas/vista_principal.dart
import 'package:flutter/material.dart';

import '../../servicios/api_herramientas.dart';

/// Vista principal del modulo Herramientas.
class VistaPrincipal extends StatefulWidget {
  const VistaPrincipal({super.key, required this.api});
  final ApiHerramientas api;

  @override
  State<VistaPrincipal> createState() => _VistaPrincipalState();
}

class _VistaPrincipalState extends State<VistaPrincipal> {
  List<Map<String, dynamic>> _puertos = const [];
  String _estado = 'Verificando backend...';

  @override
  void initState() {
    super.initState();
    _refrescar();
  }

  Future<void> _refrescar() async {
    try {
      final puertos = await widget.api.listarPuertos();
      setState(() {
        _puertos = puertos;
        _estado = 'Puertos detectados: ${puertos.length}';
      });
    } catch (e) {
      setState(() => _estado = 'Error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(_estado, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.builder(
              itemCount: _puertos.length,
              itemBuilder: (context, i) {
                final p = _puertos[i];
                return ListTile(
                  leading: const Icon(Icons.usb),
                  title: Text(p['dispositivo'] ?? ''),
                  subtitle: Text(p['descripcion'] ?? ''),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
