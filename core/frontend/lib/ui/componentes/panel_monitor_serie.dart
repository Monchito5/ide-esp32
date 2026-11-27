// Archivo: core/frontend/lib/ui/componentes/panel_monitor_serie.dart
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

/// Modelo ligero de un evento en el Monitor Serie.
class EventoMonitorSerie {
  const EventoMonitorSerie({
    required this.seq,
    required this.fecha,
    required this.puerto,
    required this.baudrate,
    required this.direccion,
    required this.nivel,
    required this.linea,
    this.canales = const {},
  });

  factory EventoMonitorSerie.fromJson(Map<String, dynamic> json) {
    final rawCanales = json['canales'];
    final mapaCanales = <String, double>{};
    if (rawCanales is Map) {
      rawCanales.forEach((k, v) {
        if (v is num) {
          mapaCanales[k.toString()] = v.toDouble();
        }
      });
    }
    return EventoMonitorSerie(
      seq: (json['seq'] as num?)?.toInt() ?? 0,
      fecha: json['fecha']?.toString() ?? '',
      puerto: json['puerto']?.toString() ?? 'VIRTUAL',
      baudrate: (json['baudrate'] as num?)?.toInt() ?? 115200,
      direccion: json['direccion']?.toString() ?? 'RX',
      nivel: json['nivel']?.toString() ?? 'INFO',
      linea: json['linea']?.toString() ?? '',
      canales: mapaCanales,
    );
  }

  final int seq;
  final String fecha;
  final String puerto;
  final int baudrate;
  final String direccion;
  final String nivel;
  final String linea;
  final Map<String, double> canales;
}

/// Terminal interactiva del Monitor Serie (Sprint 5).
class PanelMonitorSerie extends StatefulWidget {
  const PanelMonitorSerie({
    super.key,
    required this.apiBase,
    required this.puertoSugerido,
    required this.modoSimulacion,
    this.eventosIniciales = const [],
    this.onLogIde,
    this.onAbrirPlotter,
  });

  final String apiBase;
  final String puertoSugerido;
  final bool modoSimulacion;
  final List<EventoMonitorSerie> eventosIniciales;
  final void Function(String mensaje)? onLogIde;
  final VoidCallback? onAbrirPlotter;

  @override
  State<PanelMonitorSerie> createState() => _PanelMonitorSerieState();
}

class _PanelMonitorSerieState extends State<PanelMonitorSerie> {
  static const List<int> _baudrates = [
    9600,
    19200,
    38400,
    57600,
    74880,
    115200,
    230400,
    460800,
    921600,
  ];

  late final TextEditingController _puertoCtrl;
  final TextEditingController _comandoCtrl = TextEditingController();
  final TextEditingController _buscarCtrl = TextEditingController();
  final TextEditingController _regexCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();

  int _baudrate = 115200;
  String _framing = '8N1';
  bool _autoReconectar = true;
  bool _mostrarTimestamps = true;
  bool _autoScroll = true;
  String _nivelFiltro = 'TODOS';
  String _formatoExportacion = 'csv';

  bool _conectado = false;
  String _estadoConexion = 'desconectado';
  int _ultimoSeq = 0;
  String? _errorRegex;
  Timer? _timerPolling;
  late List<EventoMonitorSerie> _eventos;

  @override
  void initState() {
    super.initState();
    final sugerido = widget.puertoSugerido.trim();
    final puertoInicial = (widget.modoSimulacion ||
            sugerido.isEmpty ||
            sugerido == 'No detectado' ||
            sugerido == 'Buscando...')
        ? 'VIRTUAL'
        : sugerido;
    _puertoCtrl = TextEditingController(text: puertoInicial);
    _eventos = List<EventoMonitorSerie>.of(widget.eventosIniciales);
    if (_eventos.isNotEmpty) {
      _ultimoSeq = _eventos.last.seq;
    } else {
      _hidratarSesionActiva();
    }
  }

  Future<void> _hidratarSesionActiva() async {
    try {
      final resp = await http
          .get(Uri.parse('${widget.apiBase}/herramientas/monitor-serie/estado'))
          .timeout(const Duration(milliseconds: 900));
      if (!mounted || resp.statusCode != 200) return;
      final estado = jsonDecode(resp.body) as Map<String, dynamic>;
      final activo = estado['conectado'] == true ||
          estado['estado']?.toString() == 'reconectando';
      if (!activo) return;
      setState(() {
        _conectado = estado['conectado'] == true;
        _estadoConexion = estado['estado']?.toString() ?? 'conectado';
        final p = estado['puerto']?.toString() ?? '';
        if (p.isNotEmpty) _puertoCtrl.text = p;
        final b = (estado['baudrate'] as num?)?.toInt();
        if (b != null && _baudrates.contains(b)) _baudrate = b;
      });
      await _sincronizarEventos();
      if (!mounted) return;
      _iniciarPolling();
    } catch (_) {
      // Sin backend disponible o en entorno de pruebas aislado.
    }
  }

  @override
  void dispose() {
    _timerPolling?.cancel();
    _puertoCtrl.dispose();
    _comandoCtrl.dispose();
    _buscarCtrl.dispose();
    _regexCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  (int, double, String) _decodificarFraming() {
    switch (_framing) {
      case '8E1':
        return (8, 1.0, 'E');
      case '7E1':
        return (7, 1.0, 'E');
      case '8N2':
        return (8, 2.0, 'N');
      default:
        return (8, 1.0, 'N');
    }
  }

  Future<void> _alternarConexion() async {
    if (_conectado || _estadoConexion == 'reconectando') {
      await _desconectar();
    } else {
      await _conectar();
    }
  }

  Future<void> _conectar() async {
    final puerto =
        _puertoCtrl.text.trim().isEmpty ? 'VIRTUAL' : _puertoCtrl.text.trim();
    final (databits, stopbits, parity) = _decodificarFraming();
    final modo = (widget.modoSimulacion || puerto.toUpperCase() == 'VIRTUAL')
        ? 'emulado'
        : 'auto';

    try {
      final resp = await http
          .post(
            Uri.parse('${widget.apiBase}/herramientas/monitor-serie/conectar'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'puerto': puerto,
              'baudrate': _baudrate,
              'databits': databits,
              'stopbits': stopbits,
              'parity': parity,
              'modo': modo,
              'auto_reconectar': _autoReconectar,
            }),
          )
          .timeout(const Duration(seconds: 3));

      if (!mounted) return;
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        setState(() {
          _conectado = data['conectado'] == true;
          _estadoConexion = data['estado']?.toString() ?? 'conectado';
        });
        widget.onLogIde?.call(
          'Monitor Serie conectado en $puerto ($_baudrate $_framing).',
        );
        await _sincronizarEventos();
        if (!mounted) return;
        _iniciarPolling();
        return;
      }
      _agregarEventoLocal(
        direccion: 'SYS',
        nivel: 'ERROR',
        linea: 'Fallo al conectar ($puerto): HTTP ${resp.statusCode}',
      );
    } catch (_) {
      if (!mounted) return;
      // Modo local autonomo cuando el backend no esta levantado.
      setState(() {
        _conectado = true;
        _estadoConexion = 'conectado_local';
      });
      _agregarEventoLocal(
        direccion: 'SYS',
        nivel: 'INFO',
        linea: 'Sesion local activa en $puerto ($_baudrate $_framing).',
      );
    }
  }

  Future<void> _desconectar() async {
    _timerPolling?.cancel();
    _timerPolling = null;
    try {
      await http
          .post(
            Uri.parse(
                '${widget.apiBase}/herramientas/monitor-serie/desconectar'),
          )
          .timeout(const Duration(seconds: 2));
    } catch (_) {
      // Ignorar si estaba en sesion local.
    }
    if (!mounted) return;
    setState(() {
      _conectado = false;
      _estadoConexion = 'desconectado';
    });
    _agregarEventoLocal(
      direccion: 'SYS',
      nivel: 'INFO',
      linea: 'Monitor Serie desconectado.',
    );
  }

  void _iniciarPolling() {
    _timerPolling?.cancel();
    _timerPolling = Timer.periodic(const Duration(milliseconds: 350), (_) {
      if (!_conectado && _estadoConexion != 'reconectando') {
        _timerPolling?.cancel();
        return;
      }
      _sincronizarEventos();
    });
  }

  Future<void> _sincronizarEventos() async {
    if (_estadoConexion == 'conectado_local') return;
    try {
      final uri =
          Uri.parse('${widget.apiBase}/herramientas/monitor-serie/eventos')
              .replace(queryParameters: {'desde_seq': '$_ultimoSeq'});
      final resp = await http.get(uri).timeout(const Duration(seconds: 2));
      if (!mounted || resp.statusCode != 200) return;
      final data = jsonDecode(resp.body) as Map<String, dynamic>;
      final estado = data['estado'] as Map<String, dynamic>?;
      final lista = (data['eventos'] as List?) ?? const [];

      setState(() {
        if (estado != null) {
          _conectado = estado['conectado'] == true;
          _estadoConexion = estado['estado']?.toString() ?? _estadoConexion;
        }
        for (final raw in lista) {
          if (raw is Map<String, dynamic>) {
            final ev = EventoMonitorSerie.fromJson(raw);
            if (ev.seq > _ultimoSeq) {
              _ultimoSeq = ev.seq;
              _eventos.add(ev);
            }
          }
        }
        if (_eventos.length > 1500) {
          _eventos.removeRange(0, _eventos.length - 1500);
        }
      });
      _desplazarAlFinal();
    } catch (_) {
      // Mantener ultimo estado conocido ante microcortes.
    }
  }

  void _agregarEventoLocal({
    required String direccion,
    required String nivel,
    required String linea,
  }) {
    setState(() {
      _ultimoSeq += 1;
      _eventos.add(
        EventoMonitorSerie(
          seq: _ultimoSeq,
          fecha: DateTime.now().toUtc().toIso8601String(),
          puerto: _puertoCtrl.text.trim().isEmpty
              ? 'VIRTUAL'
              : _puertoCtrl.text.trim(),
          baudrate: _baudrate,
          direccion: direccion,
          nivel: nivel,
          linea: linea,
        ),
      );
    });
    _desplazarAlFinal();
  }

  void _desplazarAlFinal() {
    if (!_autoScroll) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.jumpTo(_scrollCtrl.position.maxScrollExtent);
      }
    });
  }

  Future<void> _enviarComando([String? predefinido]) async {
    final texto = (predefinido ?? _comandoCtrl.text).trim();
    if (texto.isEmpty) return;
    if (predefinido == null) {
      _comandoCtrl.clear();
    }

    if (!_conectado) {
      await _conectar();
    }

    if (_estadoConexion == 'conectado_local') {
      _agregarEventoLocal(direccion: 'TX', nivel: 'INFO', linea: texto);
      if (texto.toUpperCase() == 'PLOT') {
        _agregarEventoLocal(
          direccion: 'RX',
          nivel: 'INFO',
          linea: 'I (1100) ESP32S3: temp:26.8,hum:58.4,volt:3.31',
        );
      } else if (texto.toUpperCase() == 'ERROR_TEST') {
        _agregarEventoLocal(
          direccion: 'RX',
          nivel: 'ERROR',
          linea: 'E (1200) ESP32S3: Fallo simulado en sensor I2C',
        );
      } else {
        _agregarEventoLocal(
          direccion: 'RX',
          nivel: 'INFO',
          linea: 'I (1050) ESP32S3: OK ($texto)',
        );
      }
      return;
    }

    try {
      final resp = await http
          .post(
            Uri.parse('${widget.apiBase}/herramientas/monitor-serie/enviar'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'datos': texto, 'agregar_salto_linea': true}),
          )
          .timeout(const Duration(seconds: 2));
      if (resp.statusCode == 409) {
        if (!mounted) return;
        setState(() {
          _conectado = false;
          _estadoConexion = 'desconectado';
        });
        await _conectar();
        if (!mounted || !_conectado) return;
        final reintento = await http
            .post(
              Uri.parse('${widget.apiBase}/herramientas/monitor-serie/enviar'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'datos': texto, 'agregar_salto_linea': true}),
            )
            .timeout(const Duration(seconds: 2));
        if (reintento.statusCode == 200) {
          await _sincronizarEventos();
        }
        return;
      }
      if (resp.statusCode == 200) {
        await _sincronizarEventos();
      }
    } catch (e) {
      if (!mounted) return;
      _agregarEventoLocal(
        direccion: 'SYS',
        nivel: 'WARN',
        linea: 'No se pudo transmitir comando: $e',
      );
    }
  }

  Future<void> _limpiarConsola() async {
    try {
      await http
          .post(
              Uri.parse('${widget.apiBase}/herramientas/monitor-serie/limpiar'))
          .timeout(const Duration(seconds: 1));
    } catch (_) {}
    if (!mounted) return;
    setState(() => _eventos.clear());
  }

  List<EventoMonitorSerie> _eventosFiltrados() {
    RegExp? patron;
    final regexTxt = _regexCtrl.text.trim();
    if (regexTxt.isNotEmpty) {
      try {
        patron = RegExp(regexTxt);
        _errorRegex = null;
      } on FormatException catch (e) {
        _errorRegex = e.message;
      }
    } else {
      _errorRegex = null;
    }

    final buscar = _buscarCtrl.text.trim().toLowerCase();
    return _eventos.where((ev) {
      if (_nivelFiltro != 'TODOS' &&
          ev.nivel.toUpperCase() != _nivelFiltro.toUpperCase()) {
        return false;
      }
      if (buscar.isNotEmpty && !ev.linea.toLowerCase().contains(buscar)) {
        return false;
      }
      if (patron != null && !patron.hasMatch(ev.linea)) {
        return false;
      }
      return true;
    }).toList();
  }

  String _formatearExportacionLocal(List<EventoMonitorSerie> lista) {
    if (_formatoExportacion == 'json') {
      return const JsonEncoder.withIndent('  ').convert({
        'total': lista.length,
        'formato': 'json',
        'eventos': lista
            .map(
              (e) => {
                'seq': e.seq,
                'fecha': e.fecha,
                'puerto': e.puerto,
                'baudrate': e.baudrate,
                'direccion': e.direccion,
                'nivel': e.nivel,
                'linea': e.linea,
                'canales': e.canales,
              },
            )
            .toList(),
      });
    }
    if (_formatoExportacion == 'csv') {
      final sb = StringBuffer(
        'seq,fecha,puerto,baudrate,direccion,nivel,linea\n',
      );
      for (final e in lista) {
        final escapada = e.linea.replaceAll('"', '""');
        sb.writeln(
          '${e.seq},${e.fecha},${e.puerto},${e.baudrate},${e.direccion},${e.nivel},"$escapada"',
        );
      }
      return sb.toString();
    }
    return lista
        .map(
          (e) =>
              '[${e.fecha}] [${e.puerto}@${e.baudrate}] [${e.direccion}] [${e.nivel}] ${e.linea}',
        )
        .join('\n');
  }

  Future<void> _exportarLogs() async {
    String contenido;
    try {
      final params = <String, String>{
        'formato': _formatoExportacion,
        if (_nivelFiltro != 'TODOS') 'nivel': _nivelFiltro,
        if (_buscarCtrl.text.trim().isNotEmpty)
          'buscar': _buscarCtrl.text.trim(),
        if (_regexCtrl.text.trim().isNotEmpty && _errorRegex == null)
          'regex': _regexCtrl.text.trim(),
      };
      final uri = Uri.parse('${widget.apiBase}/herramientas/logs/exportar')
          .replace(queryParameters: params);
      final resp = await http.get(uri).timeout(const Duration(seconds: 2));
      if (resp.statusCode == 200 && resp.bodyBytes.isNotEmpty) {
        contenido = utf8.decode(resp.bodyBytes);
      } else {
        contenido = _formatearExportacionLocal(_eventosFiltrados());
      }
    } catch (_) {
      contenido = _formatearExportacionLocal(_eventosFiltrados());
    }

    if (!mounted) return;
    widget.onLogIde?.call(
      'Logs exportados en formato ${_formatoExportacion.toUpperCase()}.',
    );

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          'Exportación de Logs (${_formatoExportacion.toUpperCase()})',
          style: const TextStyle(fontSize: 15),
        ),
        content: SizedBox(
          width: 540,
          height: 300,
          child: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFF14191F),
              borderRadius: BorderRadius.circular(4),
            ),
            child: SingleChildScrollView(
              child: SelectableText(
                contenido.isEmpty ? '(Sin registros para exportar)' : contenido,
                style: const TextStyle(
                  color: Colors.greenAccent,
                  fontFamily: 'monospace',
                  fontSize: 11,
                ),
              ),
            ),
          ),
        ),
        actions: [
          TextButton.icon(
            onPressed: () {
              Clipboard.setData(ClipboardData(text: contenido));
              Navigator.of(ctx).pop();
            },
            icon: const Icon(Icons.copy, size: 16),
            label: const Text('Copiar al portapapeles'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }

  Color _colorNivel(EventoMonitorSerie ev) {
    if (ev.direccion == 'TX') return Colors.cyanAccent;
    if (ev.direccion == 'SYS') return Colors.lightBlueAccent;
    switch (ev.nivel.toUpperCase()) {
      case 'ERROR':
        return Colors.redAccent.shade100;
      case 'WARN':
        return Colors.amberAccent;
      case 'DEBUG':
        return Colors.grey.shade400;
      default:
        return const Color(0xFFB9F6CA);
    }
  }

  String _horaCorta(String iso) {
    if (iso.length >= 19 && iso.contains('T')) {
      return iso.substring(11, iso.length > 23 ? 23 : iso.length);
    }
    return iso;
  }

  @override
  Widget build(BuildContext context) {
    final filtrados = _eventosFiltrados();
    final esReconectando = _estadoConexion == 'reconectando';

    return Container(
      color: const Color(0xFFF6F8FA),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Barra superior de configuracion serial y exportacion
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            color: Colors.white,
            child: Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                const Icon(Icons.usb, size: 18, color: Color(0xFF1E3A5F)),
                const Text(
                  'Monitor Serie',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                SizedBox(
                  width: 105,
                  height: 32,
                  child: TextField(
                    key: const Key('monitor_puerto_input'),
                    controller: _puertoCtrl,
                    style: const TextStyle(fontSize: 12),
                    decoration: const InputDecoration(
                      labelText: 'Puerto',
                      isDense: true,
                      border: OutlineInputBorder(),
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    ),
                  ),
                ),
                DropdownButton<int>(
                  key: const Key('monitor_baudrate_dropdown'),
                  value: _baudrate,
                  isDense: true,
                  items: _baudrates
                      .map(
                        (b) => DropdownMenuItem<int>(
                          value: b,
                          child: Text('$b baud',
                              style: const TextStyle(fontSize: 12)),
                        ),
                      )
                      .toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => _baudrate = val);
                  },
                ),
                DropdownButton<String>(
                  value: _framing,
                  isDense: true,
                  items: const ['8N1', '8E1', '7E1', '8N2']
                      .map(
                        (f) => DropdownMenuItem<String>(
                          value: f,
                          child: Text(f, style: const TextStyle(fontSize: 12)),
                        ),
                      )
                      .toList(),
                  onChanged: (val) {
                    if (val != null) setState(() => _framing = val);
                  },
                ),
                FilterChip(
                  label: const Text('Auto-USB', style: TextStyle(fontSize: 11)),
                  selected: _autoReconectar,
                  visualDensity: VisualDensity.compact,
                  onSelected: (v) => setState(() => _autoReconectar = v),
                ),
                FilledButton.icon(
                  key: const Key('monitor_btn_conectar'),
                  onPressed: _alternarConexion,
                  style: FilledButton.styleFrom(
                    backgroundColor: (_conectado || esReconectando)
                        ? Colors.red.shade700
                        : const Color(0xFF1E6F50),
                    visualDensity: VisualDensity.compact,
                  ),
                  icon: Icon(
                    (_conectado || esReconectando)
                        ? Icons.link_off
                        : Icons.link,
                    size: 16,
                  ),
                  label: Text(
                    (_conectado || esReconectando) ? 'Desconectar' : 'Conectar',
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: _conectado
                        ? Colors.green.shade50
                        : (esReconectando
                            ? Colors.amber.shade50
                            : Colors.grey.shade200),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _conectado
                        ? 'Conectado'
                        : (esReconectando ? 'Reconectando USB...' : 'Inactivo'),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: _conectado
                          ? Colors.green.shade800
                          : (esReconectando
                              ? Colors.orange.shade900
                              : Colors.black54),
                    ),
                  ),
                ),
                DropdownButton<String>(
                  key: const Key('monitor_formato_exportar'),
                  value: _formatoExportacion,
                  isDense: true,
                  items: const [
                    DropdownMenuItem(
                        value: 'csv',
                        child: Text('CSV', style: TextStyle(fontSize: 12))),
                    DropdownMenuItem(
                        value: 'txt',
                        child: Text('TXT', style: TextStyle(fontSize: 12))),
                    DropdownMenuItem(
                        value: 'json',
                        child: Text('JSON', style: TextStyle(fontSize: 12))),
                  ],
                  onChanged: (v) {
                    if (v != null) setState(() => _formatoExportacion = v);
                  },
                ),
                OutlinedButton.icon(
                  key: const Key('monitor_btn_exportar'),
                  onPressed: _exportarLogs,
                  style: OutlinedButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                  ),
                  icon: const Icon(Icons.download, size: 15),
                  label: const Text('Exportar', style: TextStyle(fontSize: 12)),
                ),
                IconButton(
                  tooltip: 'Limpiar terminal',
                  visualDensity: VisualDensity.compact,
                  onPressed: _limpiarConsola,
                  icon: const Icon(Icons.delete_sweep, size: 18),
                ),
                if (widget.onAbrirPlotter != null)
                  TextButton.icon(
                    onPressed: widget.onAbrirPlotter,
                    icon: const Icon(Icons.show_chart, size: 16),
                    label:
                        const Text('Plotter', style: TextStyle(fontSize: 12)),
                  ),
              ],
            ),
          ),
          const Divider(height: 1),
          // Barra de filtros: nivel, busqueda y regex
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            color: Colors.grey.shade100,
            child: Wrap(
              spacing: 6,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                for (final niv in const [
                  'TODOS',
                  'INFO',
                  'WARN',
                  'ERROR',
                  'DEBUG',
                ])
                  ChoiceChip(
                    key: Key('monitor_chip_nivel_$niv'),
                    label: Text(niv, style: const TextStyle(fontSize: 11)),
                    selected: _nivelFiltro == niv,
                    visualDensity: VisualDensity.compact,
                    onSelected: (_) => setState(() => _nivelFiltro = niv),
                  ),
                SizedBox(
                  width: 155,
                  height: 30,
                  child: TextField(
                    key: const Key('monitor_buscar_input'),
                    controller: _buscarCtrl,
                    onChanged: (_) => setState(() {}),
                    style: const TextStyle(fontSize: 12),
                    decoration: const InputDecoration(
                      hintText: 'Buscar texto...',
                      prefixIcon: Icon(Icons.search, size: 15),
                      isDense: true,
                      border: OutlineInputBorder(),
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    ),
                  ),
                ),
                SizedBox(
                  width: 165,
                  height: 30,
                  child: TextField(
                    key: const Key('monitor_regex_input'),
                    controller: _regexCtrl,
                    onChanged: (_) => setState(() {}),
                    style: const TextStyle(fontSize: 12),
                    decoration: InputDecoration(
                      hintText: 'Filtro Regex...',
                      isDense: true,
                      border: const OutlineInputBorder(),
                      errorStyle: const TextStyle(fontSize: 0, height: 0),
                      enabledBorder: OutlineInputBorder(
                        borderSide: BorderSide(
                          color: _errorRegex != null
                              ? Colors.red
                              : Colors.grey.shade400,
                        ),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 6),
                    ),
                  ),
                ),
                FilterChip(
                  label:
                      const Text('Timestamps', style: TextStyle(fontSize: 11)),
                  selected: _mostrarTimestamps,
                  visualDensity: VisualDensity.compact,
                  onSelected: (v) => setState(() => _mostrarTimestamps = v),
                ),
                FilterChip(
                  label:
                      const Text('Autoscroll', style: TextStyle(fontSize: 11)),
                  selected: _autoScroll,
                  visualDensity: VisualDensity.compact,
                  onSelected: (v) => setState(() => _autoScroll = v),
                ),
                if (_errorRegex != null)
                  const Text(
                    'Regex inválida',
                    style: TextStyle(color: Colors.red, fontSize: 11),
                  ),
              ],
            ),
          ),
          const Divider(height: 1),
          // Consola serial interactiva
          Expanded(
            child: Container(
              color: const Color(0xFF14191F),
              padding: const EdgeInsets.all(8),
              child: filtrados.isEmpty
                  ? const Center(
                      child: Text(
                        'Sin tramas seriales que mostrar. Pulsa "Conectar" o envía un comando (ej. STATUS, PLOT).',
                        style: TextStyle(
                          color: Colors.white54,
                          fontFamily: 'monospace',
                          fontSize: 12,
                        ),
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollCtrl,
                      itemCount: filtrados.length,
                      itemBuilder: (context, index) {
                        final ev = filtrados[index];
                        final ts = _mostrarTimestamps
                            ? '[${_horaCorta(ev.fecha)}] '
                            : '';
                        final prefijoDir = ev.direccion == 'TX' ? '>> ' : '';
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 1.5),
                          child: SelectableText(
                            '$ts[${ev.nivel}] $prefijoDir${ev.linea}',
                            style: TextStyle(
                              color: _colorNivel(ev),
                              fontFamily: 'monospace',
                              fontSize: 12,
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ),
          // Barra inferior de envio TX
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 34,
                    child: TextField(
                      key: const Key('monitor_tx_input'),
                      controller: _comandoCtrl,
                      onSubmitted: (_) => _enviarComando(),
                      style: const TextStyle(
                          fontFamily: 'monospace', fontSize: 12),
                      decoration: const InputDecoration(
                        hintText:
                            'Enviar comando al ESP32 (ej. STATUS, PLOT, AT)...',
                        isDense: true,
                        border: OutlineInputBorder(),
                        contentPadding:
                            EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                ActionChip(
                  label: const Text('STATUS', style: TextStyle(fontSize: 11)),
                  visualDensity: VisualDensity.compact,
                  onPressed: () => _enviarComando('STATUS'),
                ),
                const SizedBox(width: 4),
                ActionChip(
                  label: const Text('PLOT', style: TextStyle(fontSize: 11)),
                  visualDensity: VisualDensity.compact,
                  onPressed: () => _enviarComando('PLOT'),
                ),
                const SizedBox(width: 6),
                FilledButton.icon(
                  key: const Key('monitor_btn_enviar'),
                  onPressed: _enviarComando,
                  style: FilledButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                  ),
                  icon: const Icon(Icons.send, size: 15),
                  label: const Text('Enviar', style: TextStyle(fontSize: 12)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
