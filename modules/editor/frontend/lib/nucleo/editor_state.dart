// Archivo: modules/editor/frontend/lib/nucleo/editor_state.dart
import 'dart:math';
import 'package:flutter/material.dart';
import 'edit_manager.dart';
import 'search_manager.dart';
import 'syntax_highlighter.dart';

/// Estado global del editor de código (Editor View Settings y Core).
///
/// Responsabilidad compartida: Dev A (Editor Core), Dev C (View Settings y Atajos).
class EditorState extends ChangeNotifier {
  EditorState({String? codigoInicial}) {
    controller = CppSyntaxHighlighterController(
      text: codigoInicial ??
          '// IDE ESP32 - Sketch\n'
          '#include <Arduino.h>\n\n'
          'const int LED_PIN = 2;\n\n'
          'void setup() {\n'
          '  Serial.begin(115200);\n'
          '  pinMode(LED_PIN, OUTPUT);\n'
          '  Serial.println("ESP32-S3 Iniciado correctamente.");\n'
          '}\n\n'
          'void loop() {\n'
          '  digitalWrite(LED_PIN, HIGH);\n'
          '  delay(500);\n'
          '  digitalWrite(LED_PIN, LOW);\n'
          '  delay(500);\n'
          '}\n',
    );

    editManager = EditManager(controller: controller);
    searchManager = SearchManager(controller: controller);

    controller.addListener(_alCambiarTexto);
  }

  late final CppSyntaxHighlighterController controller;
  late final EditManager editManager;
  late final SearchManager searchManager;

  // REQ-018 y REQ-019: Ajuste visual de tamaño de fuente
  double _tamanioFuente = 14.0;
  static const double tamanioMinimo = 8.0;
  static const double tamanioMaximo = 36.0;
  static const double incrementoPaso = 2.0;

  double get tamanioFuente => _tamanioFuente;

  int _lineaActual = 1;
  int _columnaActual = 1;

  int get lineaActual => _lineaActual;
  int get columnaActual => _columnaActual;
  int get totalLineas => controller.text.split('\n').length;
  int get totalCaracteres => controller.text.length;

  void _alCambiarTexto() {
    _actualizarPosicionCursor();
    notifyListeners();
  }

  void _actualizarPosicionCursor() {
    final seleccion = controller.selection;
    final int offset = max(0, seleccion.baseOffset);
    final String texto = controller.text;

    if (offset > texto.length) return;

    final String textoHastaCursor = texto.substring(0, offset);
    final lineas = textoHastaCursor.split('\n');

    _lineaActual = lineas.length;
    _columnaActual = lineas.isEmpty ? 1 : lineas.last.length + 1;
  }

  /// REQ-018: Increase Font Size
  void increaseFontSize() {
    if (_tamanioFuente + incrementoPaso <= tamanioMaximo) {
      _tamanioFuente += incrementoPaso;
      notifyListeners();
    }
  }

  /// REQ-019: Decrease Font Size
  void decreaseFontSize() {
    if (_tamanioFuente - incrementoPaso >= tamanioMinimo) {
      _tamanioFuente -= incrementoPaso;
      notifyListeners();
    }
  }

  /// Restablece el tamaño de fuente al valor predeterminado (14px)
  void resetFontSize() {
    _tamanioFuente = 14.0;
    notifyListeners();
  }

  @override
  void dispose() {
    controller.removeListener(_alCambiarTexto);
    controller.dispose();
    searchManager.dispose();
    super.dispose();
  }
}
