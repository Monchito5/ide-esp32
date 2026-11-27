// Archivo: core/frontend/lib/ui/componentes/panel_plotter_serie.dart
import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

/// Muestra individual multicanal para el Plotter Serie.
class MuestraPlotter {
  const MuestraPlotter({
    required this.seq,
    required this.canales,
  });

  final int seq;
  final Map<String, double> canales;
}

/// Visualizador grafico multicanal en tiempo real para datos seriales (Sprint 5).
class PanelPlotterSerie extends StatefulWidget {
  const PanelPlotterSerie({
    super.key,
    required this.apiBase,
    this.muestrasIniciales = const [],
    this.onLogIde,
  });

  final String apiBase;
  final List<MuestraPlotter> muestrasIniciales;
  final void Function(String mensaje)? onLogIde;

  @override
  State<PanelPlotterSerie> createState() => _PanelPlotterSerieState();
}

class _PanelPlotterSerieState extends State<PanelPlotterSerie> {
  static const List<Color> _paletaCanales = [
    Color(0xFF00E5FF),
    Color(0xFFFFCA28),
    Color(0xFF69F0AE),
    Color(0xFFFF5252),
    Color(0xFFE040FB),
    Color(0xFFFF9100),
  ];

  final TextEditingController _yMinCtrl = TextEditingController(text: '0');
  final TextEditingController _yMaxCtrl = TextEditingController(text: '100');

  late List<MuestraPlotter> _muestras;
  final Set<String> _canalesOcultos = <String>{};
  final List<String> _canalesDetectados = <String>[];
  int _ventanaMuestras = 60;
  bool _escalaAuto = true;
  bool _enVivo = false;
  int _ultimoSeq = 0;
  int _pasoDemo = 0;
  Timer? _timerEnVivo;

  @override
  void initState() {
    super.initState();
    _muestras = List<MuestraPlotter>.of(widget.muestrasIniciales);
    for (final m in _muestras) {
      if (m.seq > _ultimoSeq) _ultimoSeq = m.seq;
      for (final c in m.canales.keys) {
        if (!_canalesDetectados.contains(c)) {
          _canalesDetectados.add(c);
        }
      }
    }
    if (_muestras.isEmpty) {
      _sincronizarDesdeBackend();
    }
  }

  @override
  void dispose() {
    _timerEnVivo?.cancel();
    _yMinCtrl.dispose();
    _yMaxCtrl.dispose();
    super.dispose();
  }

  void _alternarEnVivo(bool activo) {
    _timerEnVivo?.cancel();
    setState(() => _enVivo = activo);
    if (activo) {
      _sincronizarDesdeBackend();
      _timerEnVivo = Timer.periodic(const Duration(milliseconds: 400), (_) {
        if (!_enVivo) return;
        _sincronizarDesdeBackend();
      });
    }
  }

  Future<void> _sincronizarDesdeBackend() async {
    try {
      final uri =
          Uri.parse('${widget.apiBase}/herramientas/plotter/muestras').replace(
        queryParameters: {
          'desde_seq': '$_ultimoSeq',
          'ventana': '$_ventanaMuestras',
        },
      );
      final resp = await http.get(uri).timeout(const Duration(seconds: 2));
      if (!mounted || resp.statusCode != 200) return;
      final data = jsonDecode(resp.body) as Map<String, dynamic>;
      final recibidas = (data['muestras'] as List?) ?? const [];
      if (recibidas.isEmpty) return;

      setState(() {
        for (final raw in recibidas) {
          if (raw is Map<String, dynamic>) {
            final seq = (raw['seq'] as num?)?.toInt() ?? (_ultimoSeq + 1);
            final mapaRaw = raw['canales'];
            final mapa = <String, double>{};
            if (mapaRaw is Map) {
              mapaRaw.forEach((k, v) {
                if (v is num) mapa[k.toString()] = v.toDouble();
              });
            }
            if (seq > _ultimoSeq && mapa.isNotEmpty) {
              _ultimoSeq = seq;
              for (final c in mapa.keys) {
                if (!_canalesDetectados.contains(c)) {
                  _canalesDetectados.add(c);
                }
              }
              _muestras.add(MuestraPlotter(seq: seq, canales: mapa));
            }
          }
        }
        if (_muestras.length > 500) {
          _muestras.removeRange(0, _muestras.length - 500);
        }
      });
    } catch (_) {
      // Silencioso si el backend aun no tiene muestras activas.
    }
  }

  Future<void> _generarRafagaMuestras() async {
    try {
      final estadoResp = await http
          .get(Uri.parse('${widget.apiBase}/herramientas/monitor-serie/estado'))
          .timeout(const Duration(seconds: 1));
      if (estadoResp.statusCode == 200) {
        final est = jsonDecode(estadoResp.body) as Map<String, dynamic>;
        final conectado = est['conectado'] == true;
        final modo = est['modo']?.toString() ?? 'fisico';
        if (conectado && modo == 'emulado') {
          final resp = await http
              .post(
                Uri.parse(
                    '${widget.apiBase}/herramientas/monitor-serie/enviar'),
                headers: {'Content-Type': 'application/json'},
                body:
                    jsonEncode({'datos': 'PLOT', 'agregar_salto_linea': true}),
              )
              .timeout(const Duration(seconds: 2));
          if (resp.statusCode == 200) {
            await _sincronizarDesdeBackend();
            return;
          }
        } else if (conectado) {
          await _sincronizarDesdeBackend();
          if (_muestras.isNotEmpty) return;
        }
      }
    } catch (_) {}

    if (!mounted) return;
    setState(() {
      for (int i = 0; i < 6; i++) {
        _pasoDemo += 1;
        _ultimoSeq += 1;
        final ang = _pasoDemo * 0.4;
        final muestra = <String, double>{
          'temp': double.parse((26.0 + 3.5 * math.sin(ang)).toStringAsFixed(2)),
          'hum': double.parse(
              (58.0 + 7.0 * math.cos(ang * 0.8)).toStringAsFixed(2)),
          'volt': double.parse(
              (3.30 + 0.05 * math.sin(ang * 1.4)).toStringAsFixed(3)),
        };
        for (final c in muestra.keys) {
          if (!_canalesDetectados.contains(c)) {
            _canalesDetectados.add(c);
          }
        }
        _muestras.add(MuestraPlotter(seq: _ultimoSeq, canales: muestra));
      }
    });
    widget.onLogIde?.call('Muestras multicanal añadidas al Plotter Serie.');
  }

  Color _colorCanal(int idx) => _paletaCanales[idx % _paletaCanales.length];

  @override
  Widget build(BuildContext context) {
    final ventanaVisible = _muestras.length > _ventanaMuestras
        ? _muestras.sublist(_muestras.length - _ventanaMuestras)
        : _muestras;

    final yMinManual = double.tryParse(_yMinCtrl.text.trim()) ?? 0.0;
    final yMaxManual = double.tryParse(_yMaxCtrl.text.trim()) ?? 100.0;

    return Container(
      color: const Color(0xFFF6F8FA),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            color: Colors.white,
            child: Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                const Icon(Icons.show_chart,
                    size: 18, color: Color(0xFF1E3A5F)),
                const Text(
                  'Plotter Serie Multicanal',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                FilterChip(
                  key: const Key('plotter_chip_en_vivo'),
                  label: const Text('En vivo', style: TextStyle(fontSize: 11)),
                  selected: _enVivo,
                  visualDensity: VisualDensity.compact,
                  onSelected: _alternarEnVivo,
                ),
                FilledButton.tonalIcon(
                  key: const Key('plotter_btn_muestra'),
                  onPressed: _generarRafagaMuestras,
                  style: FilledButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                  ),
                  icon: const Icon(Icons.bolt, size: 15),
                  label: const Text('Capturar / Demo',
                      style: TextStyle(fontSize: 12)),
                ),
                DropdownButton<int>(
                  key: const Key('plotter_ventana_dropdown'),
                  value: _ventanaMuestras,
                  isDense: true,
                  items: const [30, 60, 120, 240]
                      .map(
                        (n) => DropdownMenuItem<int>(
                          value: n,
                          child: Text('Ventana: $n',
                              style: const TextStyle(fontSize: 12)),
                        ),
                      )
                      .toList(),
                  onChanged: (v) {
                    if (v != null) setState(() => _ventanaMuestras = v);
                  },
                ),
                FilterChip(
                  key: const Key('plotter_chip_escala_auto'),
                  label: const Text('Escala Y Auto',
                      style: TextStyle(fontSize: 11)),
                  selected: _escalaAuto,
                  visualDensity: VisualDensity.compact,
                  onSelected: (v) => setState(() => _escalaAuto = v),
                ),
                if (!_escalaAuto) ...[
                  SizedBox(
                    width: 72,
                    height: 30,
                    child: TextField(
                      controller: _yMinCtrl,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(fontSize: 11),
                      decoration: const InputDecoration(
                        labelText: 'Y mín',
                        isDense: true,
                        border: OutlineInputBorder(),
                        contentPadding:
                            EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      ),
                    ),
                  ),
                  SizedBox(
                    width: 72,
                    height: 30,
                    child: TextField(
                      controller: _yMaxCtrl,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(fontSize: 11),
                      decoration: const InputDecoration(
                        labelText: 'Y máx',
                        isDense: true,
                        border: OutlineInputBorder(),
                        contentPadding:
                            EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      ),
                    ),
                  ),
                ],
                IconButton(
                  tooltip: 'Limpiar gráfica',
                  visualDensity: VisualDensity.compact,
                  onPressed: () => setState(() {
                    _muestras.clear();
                    _canalesDetectados.clear();
                    _canalesOcultos.clear();
                  }),
                  icon: const Icon(Icons.delete_outline, size: 18),
                ),
              ],
            ),
          ),
          if (_canalesDetectados.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              color: Colors.grey.shade100,
              child: Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  for (int i = 0; i < _canalesDetectados.length; i++)
                    Builder(
                      builder: (context) {
                        final nombre = _canalesDetectados[i];
                        final visible = !_canalesOcultos.contains(nombre);
                        final ultimoValor = ventanaVisible.isNotEmpty
                            ? ventanaVisible.last.canales[nombre]
                            : null;
                        final etiqueta = ultimoValor != null
                            ? '$nombre: ${ultimoValor.toStringAsFixed(2)}'
                            : nombre;
                        return FilterChip(
                          key: Key('plotter_canal_$nombre'),
                          avatar: CircleAvatar(
                            backgroundColor: _colorCanal(i),
                            radius: 5,
                          ),
                          label: Text(etiqueta,
                              style: const TextStyle(fontSize: 11)),
                          selected: visible,
                          visualDensity: VisualDensity.compact,
                          onSelected: (sel) {
                            setState(() {
                              if (sel) {
                                _canalesOcultos.remove(nombre);
                              } else {
                                _canalesOcultos.add(nombre);
                              }
                            });
                          },
                        );
                      },
                    ),
                ],
              ),
            ),
          const Divider(height: 1),
          Expanded(
            child: Container(
              margin: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF10161D),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.blueGrey.shade800),
              ),
              child: ventanaVisible.isEmpty
                  ? const Center(
                      child: Text(
                        'Sin muestras numéricas aún.\nEnvía tramas tipo "temp:25.4,hum:60.1" o pulsa "Capturar / Demo".',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white54,
                          fontFamily: 'monospace',
                          fontSize: 12,
                        ),
                      ),
                    )
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: CustomPaint(
                        key: const Key('plotter_canvas'),
                        painter: _PlotterMultiCanalPainter(
                          muestras: ventanaVisible,
                          canalesOrdenados: _canalesDetectados,
                          canalesOcultos: _canalesOcultos,
                          paleta: _paletaCanales,
                          escalaAuto: _escalaAuto,
                          yMinManual: yMinManual,
                          yMaxManual: yMaxManual,
                        ),
                        child: const SizedBox.expand(),
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PlotterMultiCanalPainter extends CustomPainter {
  _PlotterMultiCanalPainter({
    required this.muestras,
    required this.canalesOrdenados,
    required this.canalesOcultos,
    required this.paleta,
    required this.escalaAuto,
    required this.yMinManual,
    required this.yMaxManual,
  });

  final List<MuestraPlotter> muestras;
  final List<String> canalesOrdenados;
  final Set<String> canalesOcultos;
  final List<Color> paleta;
  final bool escalaAuto;
  final double yMinManual;
  final double yMaxManual;

  @override
  void paint(Canvas canvas, Size size) {
    const double padIzq = 48;
    const double padDer = 14;
    const double padArr = 14;
    const double padAba = 22;

    final anchoUtil = math.max(1.0, size.width - padIzq - padDer);
    final altoUtil = math.max(1.0, size.height - padArr - padAba);

    double yMin = yMinManual;
    double yMax = yMaxManual;
    if (escalaAuto) {
      double? minDetectado;
      double? maxDetectado;
      for (final m in muestras) {
        for (final entry in m.canales.entries) {
          if (canalesOcultos.contains(entry.key)) continue;
          minDetectado = minDetectado == null
              ? entry.value
              : math.min(minDetectado, entry.value);
          maxDetectado = maxDetectado == null
              ? entry.value
              : math.max(maxDetectado, entry.value);
        }
      }
      yMin = minDetectado ?? 0.0;
      yMax = maxDetectado ?? 1.0;
      if ((yMax - yMin).abs() < 1e-6) {
        yMin -= 1.0;
        yMax += 1.0;
      } else {
        final margen = (yMax - yMin) * 0.1;
        yMin -= margen;
        yMax += margen;
      }
    } else if (yMax <= yMin) {
      yMax = yMin + 1.0;
    }

    final gridPaint = Paint()
      ..color = const Color(0xFF263238)
      ..strokeWidth = 1.0;

    const int divisionesY = 4;
    for (int i = 0; i <= divisionesY; i++) {
      final frac = i / divisionesY;
      final y = padArr + altoUtil * (1.0 - frac);
      canvas.drawLine(
          Offset(padIzq, y), Offset(padIzq + anchoUtil, y), gridPaint);

      final valorEtiqueta = yMin + (yMax - yMin) * frac;
      final tp = TextPainter(
        text: TextSpan(
          text: valorEtiqueta.toStringAsFixed(1),
          style: const TextStyle(
            color: Colors.white54,
            fontSize: 10,
            fontFamily: 'monospace',
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: padIzq - 4);
      tp.paint(canvas, Offset(padIzq - tp.width - 4, y - tp.height / 2));
    }

    final total = muestras.length;
    for (int cIdx = 0; cIdx < canalesOrdenados.length; cIdx++) {
      final canal = canalesOrdenados[cIdx];
      if (canalesOcultos.contains(canal)) continue;

      final color = paleta[cIdx % paleta.length];
      final trazoPaint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.0
        ..isAntiAlias = true;

      final path = Path();
      bool iniciado = false;
      Offset? ultimoPunto;

      for (int i = 0; i < total; i++) {
        final valor = muestras[i].canales[canal];
        if (valor == null) continue;
        final x = total <= 1
            ? padIzq + anchoUtil / 2
            : padIzq + (i / (total - 1)) * anchoUtil;
        final normY = ((valor - yMin) / (yMax - yMin)).clamp(0.0, 1.0);
        final y = padArr + altoUtil * (1.0 - normY);
        final pt = Offset(x, y);
        if (!iniciado) {
          path.moveTo(pt.dx, pt.dy);
          iniciado = true;
        } else {
          path.lineTo(pt.dx, pt.dy);
        }
        ultimoPunto = pt;
      }

      if (iniciado) {
        canvas.drawPath(path, trazoPaint);
        if (ultimoPunto != null) {
          canvas.drawCircle(
            ultimoPunto,
            3.2,
            Paint()..color = color,
          );
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant _PlotterMultiCanalPainter oldDelegate) => true;
}
