// Archivo: modules/editor/frontend/lib/nucleo/search_manager.dart
import 'dart:math';
import 'package:flutter/material.dart';
import 'syntax_highlighter.dart';

/// Coincidencia individual de búsqueda en el documento activo.
class CoincidenciaBusqueda {
  const CoincidenciaBusqueda({
    required this.inicio,
    required this.fin,
    required this.texto,
  });

  final int inicio;
  final int fin;
  final String texto;
}

/// Gestor de búsqueda y reemplazo en el archivo activo.
///
/// Responsabilidad asignada a Dev B (Cesar) y Dev C (Nathaniel).
class SearchManager extends ChangeNotifier {
  SearchManager({required this.controller});

  final CppSyntaxHighlighterController controller;

  String _terminoBusqueda = '';
  String _terminoReemplazo = '';
  bool _sensibleMayusculas = false;
  bool _palabraCompleta = false;
  bool _barraVisible = false;

  final List<CoincidenciaBusqueda> _coincidencias = [];
  int _indiceActual = -1;

  // Getters
  String get terminoBusqueda => _terminoBusqueda;
  String get terminoReemplazo => _terminoReemplazo;
  bool get sensibleMayusculas => _sensibleMayusculas;
  bool get palabraCompleta => _palabraCompleta;
  bool get barraVisible => _barraVisible;
  int get totalCoincidencias => _coincidencias.length;
  int get indiceActual => _indiceActual;
  List<CoincidenciaBusqueda> get coincidencias => List.unmodifiable(_coincidencias);

  void setBarraVisible(bool visible) {
    _barraVisible = visible;
    if (!visible) {
      _limpiarBusqueda();
    }
    notifyListeners();
  }

  void setSensibleMayusculas(bool valor) {
    _sensibleMayusculas = valor;
    buscar(_terminoBusqueda);
  }

  void setPalabraCompleta(bool valor) {
    _palabraCompleta = valor;
    buscar(_terminoBusqueda);
  }

  void setTerminoReemplazo(String valor) {
    _terminoReemplazo = valor;
    notifyListeners();
  }

  /// REQ-016: Use Selection for Find
  void useSelectionForFind() {
    final seleccion = controller.selection;
    if (!seleccion.isCollapsed) {
      final texto = seleccion.textInside(controller.text);
      if (texto.isNotEmpty) {
        _terminoBusqueda = texto;
        _barraVisible = true;
        buscar(texto);
      }
    } else {
      _barraVisible = true;
      notifyListeners();
    }
  }

  /// REQ-004 / REQ-022: Find
  void buscar(String termino) {
    _terminoBusqueda = termino;
    _coincidencias.clear();
    _indiceActual = -1;

    if (termino.isEmpty) {
      notifyListeners();
      return;
    }

    final String textoDoc = controller.text;
    String patron = RegExp.escape(termino);
    if (_palabraCompleta) {
      patron = r'\b' + patron + r'\b';
    }

    final RegExp regex = RegExp(
      patron,
      caseSensitive: _sensibleMayusculas,
      multiLine: true,
    );

    for (final Match match in regex.allMatches(textoDoc)) {
      _coincidencias.add(CoincidenciaBusqueda(
        inicio: match.start,
        fin: match.end,
        texto: match.group(0)!,
      ));
    }

    if (_coincidencias.isNotEmpty) {
      // Ubicar la coincidencia más cercana a la posición actual del cursor
      final cursor = controller.selection.baseOffset;
      int proximo = 0;
      for (int i = 0; i < _coincidencias.length; i++) {
        if (_coincidencias[i].inicio >= cursor) {
          proximo = i;
          break;
        }
      }
      _seleccionarCoincidencia(proximo);
    }

    notifyListeners();
  }

  void _seleccionarCoincidencia(int indice) {
    if (indice < 0 || indice >= _coincidencias.length) return;
    _indiceActual = indice;
    final c = _coincidencias[indice];

    controller.selection = TextSelection(
      baseOffset: c.inicio,
      extentOffset: c.fin,
    );
  }

  /// REQ-014: Find Next (con comportamiento circular de final a inicio)
  void findNext() {
    if (_coincidencias.isEmpty) return;
    final int siguiente = (_indiceActual + 1) % _coincidencias.length;
    _seleccionarCoincidencia(siguiente);
    notifyListeners();
  }

  /// REQ-015: Find Previous (con comportamiento circular de inicio a final)
  void findPrevious() {
    if (_coincidencias.isEmpty) return;
    final int anterior = (_indiceActual - 1 + _coincidencias.length) % _coincidencias.length;
    _seleccionarCoincidencia(anterior);
    notifyListeners();
  }

  /// Reemplaza la coincidencia activa actual
  void replace(String reemplazo) {
    if (_indiceActual < 0 || _indiceActual >= _coincidencias.length) return;

    final c = _coincidencias[_indiceActual];
    final String antes = controller.text.substring(0, c.inicio);
    final String despues = controller.text.substring(c.fin);

    controller.text = '$antes$reemplazo$despues';
    buscar(_terminoBusqueda);
  }

  /// Reemplaza todas las coincidencias en el documento activo
  void replaceAll(String reemplazo) {
    if (_coincidencias.isEmpty) return;

    String patron = RegExp.escape(_terminoBusqueda);
    if (_palabraCompleta) {
      patron = r'\b' + patron + r'\b';
    }

    final RegExp regex = RegExp(
      patron,
      caseSensitive: _sensibleMayusculas,
      multiLine: true,
    );

    controller.text = controller.text.replaceAll(regex, reemplazo);
    buscar(_terminoBusqueda);
  }

  void _limpiarBusqueda() {
    _coincidencias.clear();
    _indiceActual = -1;
  }
}
