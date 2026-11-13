// Archivo: modules/editor/frontend/lib/nucleo/edit_manager.dart
import 'dart:math';
import 'package:flutter/services.dart';
import 'syntax_highlighter.dart';

/// Snapshot de estado para el historial de Undo / Redo.
class SnapshotEdicion {
  const SnapshotEdicion({
    required this.texto,
    required this.seleccion,
  });

  final String texto;
  final TextSelection seleccion;
}

/// Gestor de comandos de edicion (Edit Manager).
///
/// Responsabilidad asignada a Dev A (Victor) con funciones compartidas
/// con Dev B y Dev C. Centraliza la logica comun para el menu y los atajos.
class EditManager {
  EditManager({
    required this.controller,
    this.tamanoTabulacion = 2,
  }) {
    _guardarSnapshotInicial();
  }

  final CppSyntaxHighlighterController controller;
  int tamanoTabulacion;

  final List<SnapshotEdicion> _historialUndo = [];
  final List<SnapshotEdicion> _historialRedo = [];
  static const int _maxHistorial = 100;
  bool _enOperacionHistorial = false;

  void _guardarSnapshotInicial() {
    _historialUndo.add(SnapshotEdicion(
      texto: controller.text,
      seleccion: controller.selection,
    ));
  }

  /// Registra el estado actual antes de aplicar una modificacion.
  void registrarCambio() {
    if (_enOperacionHistorial) return;

    if (_historialUndo.isNotEmpty &&
        _historialUndo.last.texto == controller.text) {
      return;
    }

    _historialUndo.add(SnapshotEdicion(
      texto: controller.text,
      seleccion: controller.selection,
    ));

    if (_historialUndo.length > _maxHistorial) {
      _historialUndo.removeAt(0);
    }
    _historialRedo.clear();
  }

  // --- REQ-001: Undo ---
  bool canUndo() => _historialUndo.length > 1;

  void undo() {
    if (!canUndo()) return;
    _enOperacionHistorial = true;

    // Guardar estado actual en Redo
    _historialRedo.add(SnapshotEdicion(
      texto: controller.text,
      seleccion: controller.selection,
    ));

    _historialUndo.removeLast(); // Quitar estado actual
    final SnapshotEdicion anterior = _historialUndo.last;

    controller.value = TextEditingValue(
      text: anterior.texto,
      selection: anterior.seleccion,
    );

    _enOperacionHistorial = false;
  }

  // --- REQ-002: Redo ---
  bool canRedo() => _historialRedo.isNotEmpty;

  void redo() {
    if (!canRedo()) return;
    _enOperacionHistorial = true;

    final SnapshotEdicion siguiente = _historialRedo.removeLast();
    _historialUndo.add(SnapshotEdicion(
      texto: siguiente.texto,
      seleccion: siguiente.seleccion,
    ));

    controller.value = TextEditingValue(
      text: siguiente.texto,
      selection: siguiente.seleccion,
    );

    _enOperacionHistorial = false;
  }

  // --- REQ-003: Copy ---
  Future<void> copy() async {
    final seleccion = controller.selection;
    if (seleccion.isCollapsed) return;

    final textoSeleccionado = seleccion.textInside(controller.text);
    await Clipboard.setData(ClipboardData(text: textoSeleccionado));
  }

  // --- REQ-005: Cut ---
  Future<void> cut() async {
    final seleccion = controller.selection;
    if (seleccion.isCollapsed) return;

    registrarCambio();
    final textoSeleccionado = seleccion.textInside(controller.text);
    await Clipboard.setData(ClipboardData(text: textoSeleccionado));

    final String antes = seleccion.textBefore(controller.text);
    final String despues = seleccion.textAfter(controller.text);

    controller.value = TextEditingValue(
      text: '$antes$despues',
      selection: TextSelection.collapsed(offset: antes.length),
    );
  }

  // --- REQ-006: Paste ---
  Future<void> paste() async {
    final datos = await Clipboard.getData(Clipboard.kTextPlain);
    final textoPegar = datos?.text ?? '';
    if (textoPegar.isEmpty) return;

    registrarCambio();
    final seleccion = controller.selection;
    final int start = min(seleccion.start, seleccion.end);
    final int end = max(seleccion.start, seleccion.end);

    final String textoActual = controller.text;
    final String antes = start >= 0 ? textoActual.substring(0, start) : '';
    final String despues = end >= 0 ? textoActual.substring(end) : '';

    final nuevoTexto = '$antes$textoPegar$despues';
    final nuevoCursor = antes.length + textoPegar.length;

    controller.value = TextEditingValue(
      text: nuevoTexto,
      selection: TextSelection.collapsed(offset: nuevoCursor),
    );
  }

  // --- REQ-007: Select All ---
  void selectAll() {
    controller.selection = TextSelection(
      baseOffset: 0,
      extentOffset: controller.text.length,
    );
  }

  // --- REQ-008 / REQ-022: Go to Line (1-indexed con validación) ---
  bool goToLine(int numeroLinea) {
    final lineas = controller.text.split('\n');
    final totalLineas = lineas.length;

    if (numeroLinea < 1 || numeroLinea > totalLineas) {
      return false; // Fuera de rango
    }

    int offset = 0;
    for (int i = 0; i < numeroLinea - 1; i++) {
      offset += lineas[i].length + 1; // +1 por el salto de línea
    }

    final longitudLinea = lineas[numeroLinea - 1].length;
    controller.selection = TextSelection(
      baseOffset: offset,
      extentOffset: offset + longitudLinea,
    );
    return true;
  }

  // --- REQ-009: Copy for Forum (Markdown) ---
  Future<void> copyForForum() async {
    final String codigo = controller.selection.isCollapsed
        ? controller.text
        : controller.selection.textInside(controller.text);

    final String formatoMarkdown = '```cpp\n$codigo\n```';
    await Clipboard.setData(ClipboardData(text: formatoMarkdown));
  }

  // --- REQ-010: Comment / Uncomment (Toggle //) ---
  void toggleComment() {
    registrarCambio();
    final String texto = controller.text;
    final TextSelection seleccion = controller.selection;

    final int start = min(seleccion.start, seleccion.end);
    final int end = max(seleccion.start, seleccion.end);

    // Encontrar líneas afectadas
    final lineas = texto.split('\n');
    int acumulado = 0;
    int inicioLineaIndex = 0;
    int finLineaIndex = 0;

    for (int i = 0; i < lineas.length; i++) {
      final int finLineaActual = acumulado + lineas[i].length;
      if (start >= acumulado && start <= finLineaActual + 1) {
        inicioLineaIndex = i;
      }
      if (end >= acumulado && end <= finLineaActual + 1) {
        finLineaIndex = i;
        break;
      }
      acumulado = finLineaActual + 1;
    }

    // Verificar si todas las líneas seleccionadas ya están comentadas con //
    bool todasComentadas = true;
    for (int i = inicioLineaIndex; i <= finLineaIndex; i++) {
      if (lineas[i].trim().isNotEmpty && !lineas[i].trimLeft().startsWith('//')) {
        todasComentadas = false;
        break;
      }
    }

    for (int i = inicioLineaIndex; i <= finLineaIndex; i++) {
      if (todasComentadas) {
        // Descomentar
        final primerComentario = lineas[i].indexOf('//');
        if (primerComentario != -1) {
          final antes = lineas[i].substring(0, primerComentario);
          var despues = lineas[i].substring(primerComentario + 2);
          if (despues.startsWith(' ')) despues = despues.substring(1);
          lineas[i] = '$antes$despues';
        }
      } else {
        // Comentar
        if (lineas[i].trim().isNotEmpty) {
          lineas[i] = '// ${lineas[i]}';
        }
      }
    }

    controller.text = lineas.join('\n');
    controller.selection = TextSelection.collapsed(offset: min(start, controller.text.length));
  }

  // --- REQ-011: Increase Indent ---
  void increaseIndent() {
    registrarCambio();
    final String unit = ' ' * tamanoTabulacion;
    final lineas = controller.text.split('\n');
    final seleccion = controller.selection;

    final int start = min(seleccion.start, seleccion.end);
    final int end = max(seleccion.start, seleccion.end);

    int acumulado = 0;
    for (int i = 0; i < lineas.length; i++) {
      final int finLinea = acumulado + lineas[i].length;
      if (finLinea >= start && acumulado <= end) {
        lineas[i] = '$unit${lineas[i]}';
      }
      acumulado = finLinea + 1;
    }

    controller.text = lineas.join('\n');
    controller.selection = TextSelection.collapsed(offset: min(start + unit.length, controller.text.length));
  }

  // --- REQ-012: Decrease Indent ---
  void decreaseIndent() {
    registrarCambio();
    final String unit = ' ' * tamanoTabulacion;
    final lineas = controller.text.split('\n');
    final seleccion = controller.selection;

    final int start = min(seleccion.start, seleccion.end);
    final int end = max(seleccion.start, seleccion.end);

    int acumulado = 0;
    for (int i = 0; i < lineas.length; i++) {
      final int finLinea = acumulado + lineas[i].length;
      if (finLinea >= start && acumulado <= end) {
        if (lineas[i].startsWith(unit)) {
          lineas[i] = lineas[i].substring(unit.length);
        } else if (lineas[i].startsWith(' ')) {
          lineas[i] = lineas[i].replaceFirst(RegExp(r'^\s+'), '');
        }
      }
      acumulado = finLinea + 1;
    }

    controller.text = lineas.join('\n');
    controller.selection = TextSelection.collapsed(offset: max(0, start - unit.length));
  }

  // --- REQ-013: Auto Format local ---
  void autoFormatLocal() {
    registrarCambio();
    final String codigo = controller.text;
    final lineas = codigo.split('\n');
    final String unit = ' ' * tamanoTabulacion;

    int nivel = 0;
    final List<String> resultado = [];

    for (final linea in lineas) {
      final trimmed = linea.trim();

      if (trimmed.isEmpty) {
        resultado.add('');
        continue;
      }

      if (trimmed.startsWith('#')) {
        resultado.add(trimmed);
        continue;
      }

      final int aperturas = '{'.allMatches(trimmed).length;
      final int cierres = '}'.allMatches(trimmed).length;

      if (trimmed.startsWith('}')) {
        nivel = max(0, nivel - 1);
        resultado.add('${unit * nivel}$trimmed');
        nivel = max(0, nivel + aperturas - (cierres - 1));
      } else {
        resultado.add('${unit * nivel}$trimmed');
        nivel = max(0, nivel + aperturas - cierres);
      }
    }

    controller.text = resultado.join('\n');
    controller.selection = const TextSelection.collapsed(offset: 0);
  }
}
