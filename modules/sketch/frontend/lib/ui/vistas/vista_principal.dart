import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../servicios/api_sketch.dart';

class VistaPrincipal extends StatefulWidget {
  const VistaPrincipal({super.key, required this.api});

  final ApiSketch api;

  @override
  State<VistaPrincipal> createState() => _VistaPrincipalState();
}

class _VistaPrincipalState extends State<VistaPrincipal> {
  final TextEditingController _rutaController = TextEditingController();

  Timer? _temporizador;
  bool _ocupado = false;

  String _estado = 'Sin compilaciones';
  String? _taskId;
  String? _error;

  Map<String, dynamic>? _resultado;

  bool _cargandoArchivos = false;
  String? _errorArchivos;
  List<Map<String, dynamic>> _archivosProyecto = [];

  Future<void> _explorarArchivos() async {
    final ruta = _rutaController.text.trim();

    if (ruta.isEmpty) {
      _mostrarMensaje('Introduce la ruta del proyecto ESP-IDF.');
      return;
    }

    setState(() {
      _cargandoArchivos = true;
      _errorArchivos = null;
      _archivosProyecto = [];
    });

    try {
      final respuesta = await widget.api.consultarArchivos(projectPath: ruta);

      final items = respuesta['items'];

      if (!mounted) return;

      setState(() {
        _archivosProyecto = items is List
            ? items
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item))
                .toList()
            : [];
        _cargandoArchivos = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _cargandoArchivos = false;
        _errorArchivos = e.toString();
      });
    }
  }

  @override
  void dispose() {
    _temporizador?.cancel();
    _rutaController.dispose();
    super.dispose();
  }

  Future<void> _iniciarCompilacion() async {
    final ruta = _rutaController.text.trim();

    if (ruta.isEmpty) {
      _mostrarMensaje('Introduce la ruta del proyecto ESP-IDF.');
      return;
    }

    _temporizador?.cancel();

    setState(() {
      _ocupado = true;
      _estado = 'Iniciando compilacion...';
      _taskId = null;
      _error = null;
      _resultado = null;
    });

    try {
      final respuesta = await widget.api.iniciarCompilacion(projectPath: ruta);

      if (!mounted) return;

      final id = respuesta['task_id']?.toString();

      if (id == null || id.isEmpty) {
        throw Exception('El backend no devolvio el identificador de tarea.');
      }

      setState(() {
        _taskId = id;
        _estado = respuesta['status']?.toString() ?? 'pending';
      });

      await _consultarTarea();

      if (mounted && _ocupado) {
        _temporizador = Timer.periodic(
          const Duration(seconds: 2),
          (_) => _consultarTarea(),
        );
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _ocupado = false;
        _estado = 'Error';
        _error = e.toString();
      });
    }
  }

  Future<void> _consultarTarea() async {
    final id = _taskId;

    if (id == null) return;

    try {
      final respuesta = await widget.api.consultarTarea(id);

      if (!mounted) return;

      final estado = respuesta['status']?.toString() ?? 'desconocido';
      final resultado = respuesta['result'];

      setState(() {
        _estado = estado;
        _error = respuesta['error']?.toString();
        _resultado =
            resultado is Map ? Map<String, dynamic>.from(resultado) : null;
      });

      if (estado == 'completed' || estado == 'failed') {
        _temporizador?.cancel();

        setState(() {
          _ocupado = false;
        });
      }
    } catch (e) {
      if (!mounted) return;

      _temporizador?.cancel();

      setState(() {
        _ocupado = false;
        _estado = 'Error de consulta';
        _error = e.toString();
      });
    }
  }

  Future<void> _descargarBinario(String nombreArchivo) async {
    final id = _taskId;

    if (id == null) {
      _mostrarMensaje('No hay una tarea de compilacion disponible.');
      return;
    }

    final uri = Uri.parse(
      '${widget.api.baseUrl}/sketch/tareas/'
      '${Uri.encodeComponent(id)}/binarios/'
      '${Uri.encodeComponent(nombreArchivo)}',
    );

    try {
      final abierto = await launchUrl(uri, mode: LaunchMode.platformDefault);

      if (!abierto && mounted) {
        _mostrarMensaje('No se pudo abrir la descarga.');
      }
    } catch (e) {
      if (mounted) {
        _mostrarMensaje('Error al descargar: $e');
      }
    }
  }

  void _mostrarMensaje(String mensaje) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(mensaje)));
  }

  Color _colorEstado() {
    switch (_estado) {
      case 'completed':
        return Colors.green;
      case 'failed':
      case 'Error':
      case 'Error de consulta':
        return Colors.red;
      case 'running':
      case 'pending':
      case 'Iniciando compilacion...':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _colorEstado();
    final archivosBinarios = _resultado?['bin_files'] is List
        ? (_resultado!['bin_files'] as List)
            .map((archivo) => archivo.toString())
            .toList()
        : <String>[];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 950),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.code, size: 30),
                  const SizedBox(width: 12),
                  Text(
                    'Sketch',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Gestion de proyectos y compilacion con ESP-IDF',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 28),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Proyecto ESP-IDF',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Introduce la ruta local de la carpeta del proyecto.',
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _rutaController,
                        enabled: !_ocupado,
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.folder_open),
                          hintText: r'C:\proyectos\mi_proyecto',
                        ),
                      ),
                      const SizedBox(height: 18),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: _ocupado ? null : _iniciarCompilacion,
                          icon: const Icon(Icons.build),
                          label: const Text('Iniciar compilacion'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Explorador del proyecto',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed:
                              _cargandoArchivos ? null : _explorarArchivos,
                          icon: _cargandoArchivos
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.folder_open),
                          label: Text(
                            _cargandoArchivos
                                ? 'Explorando proyecto...'
                                : 'Explorar archivos',
                          ),
                        ),
                      ),
                      if (_errorArchivos != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          _errorArchivos!,
                          style: const TextStyle(color: Colors.red),
                        ),
                      ],
                      if (_archivosProyecto.isNotEmpty) ...[
                        const Divider(height: 24),
                        Text(
                          '${_archivosProyecto.length} elementos encontrados',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(height: 8),
                        for (final archivo in _archivosProyecto)
                          ListTile(
                            dense: true,
                            leading: Icon(
                              archivo['type'] == 'directory'
                                  ? Icons.folder
                                  : Icons.insert_drive_file_outlined,
                              color: archivo['type'] == 'directory'
                                  ? Colors.amber
                                  : null,
                            ),
                            title: Text(archivo['name']?.toString() ?? ''),
                            subtitle: Text(archivo['path']?.toString() ?? ''),
                            trailing: archivo['type'] == 'file'
                                ? Text(
                                    '${((archivo['size'] as num?) ?? 0) ~/ 1024} KB',
                                  )
                                : null,
                          ),
                      ],
                      if (!_cargandoArchivos &&
                          _errorArchivos == null &&
                          _archivosProyecto.isEmpty)
                        const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Text(
                            'Introduce un proyecto y pulsa Explorar archivos.',
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Estado de compilacion',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Icon(
                            _ocupado
                                ? Icons.sync
                                : _estado == 'completed'
                                    ? Icons.check_circle
                                    : _estado == 'failed'
                                        ? Icons.error
                                        : Icons.info_outline,
                            color: color,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              _estado,
                              style: TextStyle(
                                color: color,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          if (_ocupado)
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                        ],
                      ),
                      if (_taskId != null) ...[
                        const SizedBox(height: 12),
                        SelectableText('ID de tarea: $_taskId'),
                      ],
                      if (_error != null && _error!.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        const Text(
                          'Error',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.red,
                          ),
                        ),
                        const SizedBox(height: 6),
                        SelectableText(_error!),
                      ],
                    ],
                  ),
                ),
              ),
              if (_resultado != null) ...[
                if (archivosBinarios.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Archivos generados',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 12),
                          for (final ruta in archivosBinarios)
                            ListTile(
                              leading: const Icon(
                                Icons.insert_drive_file_outlined,
                              ),
                              title: Text(ruta.split(RegExp(r'[\\/]')).last),
                              subtitle: SelectableText(ruta),
                              trailing: IconButton(
                                tooltip: 'Descargar binario',
                                icon: const Icon(Icons.download),
                                onPressed: () => _descargarBinario(
                                  ruta.split(RegExp(r'[\\/]')).last,
                                ),
                              ),
                              dense: true,
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 20),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Resultado de compilacion',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 12),
                        SelectableText(
                          const JsonEncoder.withIndent('  ')
                              .convert(_resultado),
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
