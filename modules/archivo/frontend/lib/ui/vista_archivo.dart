// Archivo: modules/archivo/frontend/lib/ui/vista_archivo.dart
import 'package:flutter/material.dart';

import '../api_archivo.dart';

/// Vista del modulo Archivo: lista de recientes y acciones del menu Archivo.
class VistaArchivo extends StatefulWidget {
  const VistaArchivo({super.key, required this.api});

  final ApiArchivo api;

  @override
  State<VistaArchivo> createState() => _VistaArchivoState();
}

class _VistaArchivoState extends State<VistaArchivo> {
  List<String> _recientes = const [];
  bool _cargando = false;

  @override
  void initState() {
    super.initState();
    _cargarRecientes();
  }

  Future<void> _cargarRecientes() async {
    setState(() => _cargando = true);
    final r = await widget.api.obtenerSubmenus();
    setState(() => _cargando = false);
    if (!r.ok) {
      _mostrarError('Submenus: ${r.error}');
      return;
    }
    final archivos = r.data?['files'] as List?;
    setState(() {
      _recientes = (archivos ?? const []).cast<String>();
    });
  }

  void _mostrarSnack(String mensaje, {bool esError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(mensaje),
        backgroundColor: esError ? Colors.red : Colors.green,
      ),
    );
  }

  Future<void> _ejecutar(ResultadoApi<Map<String, dynamic>> r, String etiqueta) async {
    if (!r.ok) {
      _mostrarSnack('$etiqueta: ${r.error}', esError: true);
      return;
    }
    _mostrarSnack('$etiqueta: ${r.data?['result'] ?? r.data?['mensaje'] ?? 'ok'}');
    await _cargarRecientes();
  }

  Widget _boton(IconData icono, String etiqueta, Future<ResultadoApi<Map<String, dynamic>>> Function() accion) {
    return ElevatedButton.icon(
      onPressed: () async {
        final r = await accion();
        await _ejecutar(r, etiqueta);
      },
      icon: Icon(icono),
      label: Text(etiqueta),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Acciones del menu Archivo
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Archivo',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _boton(Icons.description_new, 'Nuevo sketch', widget.api.nuevoSketch),
                      _boton(Icons.folder_open, 'Abrir archivo', () async {
                        final r = await widget.api.abrirArchivo(filepath: '');
                        await _ejecutar(r, 'Abrir archivo');
                      }),
                      _boton(Icons.save, 'Guardar archivo', () async {
                        final r = await widget.api.guardarArchivo(filepath: '', content: '');
                        await _ejecutar(r, 'Guardar archivo');
                      }),
                      _boton(Icons.save_as, 'Guardar como', () async {
                        final r = await widget.api.guardarComo(filepath: '', content: '');
                        await _ejecutar(r, 'Guardar como');
                      }),
                      _boton(Icons.refresh, 'Recargar sketch', () async {
                        final r = await widget.api.recargarSketch(filepath: '');
                        await _ejecutar(r, 'Recargar sketch');
                      }),
                      _boton(Icons.close, 'Cerrar sketch', () async {
                        final r = await widget.api.cerrarSketch(filepath: '');
                        await _ejecutar(r, 'Cerrar sketch');
                      }),
                      _boton(Icons.template, 'Plantilla base', widget.api.obtenerPlantillaBase),
                      _boton(Icons.info, 'Info sketch', () async {
                        final r = await widget.api.obtenerInfoSketch(filepath: '');
                        await _ejecutar(r, 'Info sketch');
                      }),
                      _boton(Icons.restore, 'Restablecer preferencias', widget.api.restablecerPreferencias),
                      _boton(Icons.delete, 'Limpiar recientes', widget.api.limpiarRecientes),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Lista de archivos recientes
          Text(
            'Archivos recientes (${_recientes.length})',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator())
                : _recientes.isEmpty
                ? const Center(child: Text('Sin archivos recientes'))
                : ListView.builder(
                    itemCount: _recientes.length,
                    itemBuilder: (context, i) {
                      final ruta = _recientes[i];
                      return ListTile(
                        leading: const Icon(Icons.description),
                        title: Text(ruta.split('/').last),
                        subtitle: Text(ruta),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  void _mostrarError(String mensaje) {
    _mostrarSnack(mensaje, esError: true);
  }
}
