// Archivo: modules/editor/frontend/lib/nucleo/syntax_highlighter.dart
import 'package:flutter/material.dart';

/// Controlador de texto con resaltado de sintaxis C/C++/Arduino para ESP32.
///
/// Responsabilidad asignada a Dev B (Cesar).
class CppSyntaxHighlighterController extends TextEditingController {
  CppSyntaxHighlighterController({String? text}) : super(text: text);

  // Palabras reservadas estándar de C/C++
  static final Set<String> _palabrasReservadas = {
    'auto', 'break', 'case', 'catch', 'class', 'const', 'continue',
    'default', 'delete', 'do', 'else', 'enum', 'explicit', 'export',
    'extern', 'for', 'friend', 'goto', 'if', 'inline', 'mutable',
    'namespace', 'new', 'noexcept', 'nullptr', 'operator', 'private',
    'protected', 'public', 'register', 'reinterpret_cast', 'return',
    'sizeof', 'static', 'static_assert', 'static_cast', 'struct',
    'switch', 'template', 'this', 'throw', 'try', 'typedef', 'typeid',
    'typename', 'union', 'using', 'virtual', 'volatile', 'while',
  };

  // Tipos de datos en C/C++ y embebidos ESP32
  static final Set<String> _tiposDatos = {
    'void', 'bool', 'char', 'short', 'int', 'long', 'float', 'double',
    'signed', 'unsigned', 'size_t', 'uint8_t', 'uint16_t', 'uint32_t',
    'uint64_t', 'int8_t', 'int16_t', 'int32_t', 'int64_t', 'String',
    'esp_err_t', 'gpio_num_t', 'TaskHandle_t', 'QueueHandle_t',
  };

  // Funciones y constantes integradas de Arduino y ESP32
  static final Set<String> _builtinsArduinoEsp32 = {
    'setup', 'loop', 'pinMode', 'digitalWrite', 'digitalRead',
    'analogRead', 'analogWrite', 'analogReadMilliVolts', 'delay',
    'delayMicroseconds', 'micros', 'millis', 'pulseIn', 'pulseInLong',
    'shiftIn', 'shiftOut', 'tone', 'noTone', 'attachInterrupt',
    'detachInterrupt', 'interrupts', 'noInterrupts', 'Serial', 'Serial1',
    'Serial2', 'Wire', 'SPI', 'WiFi', 'BluetoothSerial', 'EEPROM',
    'HIGH', 'LOW', 'INPUT', 'OUTPUT', 'INPUT_PULLUP', 'INPUT_PULLDOWN',
    'LED_BUILTIN', 'true', 'false', 'CHANGE', 'FALLING', 'RISING',
    'esp_restart', 'esp_deep_sleep_start', 'vTaskDelay', 'xTaskCreate',
  };

  // Estilos de color para la sintaxis (Estilo Arduino IDE 2 / VSCode)
  static const Color colorPalabraClave = Color(0xFFC586C0); // Magenta/Púrpura
  static const Color colorTipoDato = Color(0xFF4EC9B0);     // Verde azulado
  static const Color colorBuiltin = Color(0xFFDCDCAA);      // Amarillo claro
  static const Color colorString = Color(0xFFCE9178);       // Naranja rojizo
  static const Color colorNumero = Color(0xFFB5CEA8);       // Verde menta
  static const Color colorComentario = Color(0xFF6A9955);   // Verde oliva
  static const Color colorDirectiva = Color(0xFF9CDCFE);    // Azul cielo
  static const Color colorOperador = Color(0xFFD4D4D4);     // Blanco/Gris claro
  static const Color colorTextoPorDefecto = Color(0xFFD4D4D4);

  @override
  TextSpan buildTextSpan({
    required BuildContext context,
    TextStyle? style,
    required bool withComposing,
  }) {
    final List<TextSpan> spans = [];
    final String codigo = text;

    if (codigo.isEmpty) {
      return TextSpan(style: style, text: '');
    }

    final TextStyle baseStyle = (style ?? const TextStyle()).copyWith(
      fontFamily: 'monospace',
      color: colorTextoPorDefecto,
    );

    // Expresión regular para tokenizar C/C++
    // 1: Comentarios de bloque /* ... */ o una línea // ...
    // 2: Directivas #include, #define
    // 3: Cadenas "..." o '...'
    // 4: Números (hexadecimal 0x... o decimal)
    // 5: Palabras / Identificadores
    // 6: Operadores y otros
    final RegExp tokenRegex = RegExp(
      r'(/\*[\s\S]*?\*/|//[^\n]*)'             // 1: Comentarios
      r'|(#[a-zA-Z_]+[^\n]*)'                   // 2: Preprocesador
      r'|("([^"\\]|\\.)*"|' r"'([^'\\]|\\.)*')" // 3: Cadenas y chars
      r'|\b(0x[0-9a-fA-F]+|\d+(\.\d+)?)\b'     // 4: Números
      r'|([a-zA-Z_][a-zA-Z0-9_]*)'              // 5: Identificadores
      r'|([{}()\[\],;.+\-*/%=!<>|&~^?:]+)',     // 6: Símbolos
      multiLine: true,
    );

    int ultimoIndice = 0;

    for (final Match match in tokenRegex.allMatches(codigo)) {
      if (match.start > ultimoIndice) {
        spans.add(TextSpan(
          text: codigo.substring(ultimoIndice, match.start),
          style: baseStyle,
        ));
      }

      final String matchText = match.group(0)!;

      if (matchText.startsWith('//') || matchText.startsWith('/*')) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(
            color: colorComentario,
            fontStyle: FontStyle.italic,
          ),
        ));
      } else if (matchText.startsWith('#')) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(
            color: colorDirectiva,
            fontWeight: FontWeight.bold,
          ),
        ));
      } else if (matchText.startsWith('"') || matchText.startsWith("'")) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(color: colorString),
        ));
      } else if (RegExp(r'^(0x[0-9a-fA-F]+|\d+(\.\d+)?)$').hasMatch(matchText)) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(color: colorNumero),
        ));
      } else if (_palabrasReservadas.contains(matchText)) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(
            color: colorPalabraClave,
            fontWeight: FontWeight.bold,
          ),
        ));
      } else if (_tiposDatos.contains(matchText)) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(
            color: colorTipoDato,
            fontWeight: FontWeight.w600,
          ),
        ));
      } else if (_builtinsArduinoEsp32.contains(matchText)) {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle.copyWith(color: colorBuiltin),
        ));
      } else {
        spans.add(TextSpan(
          text: matchText,
          style: baseStyle,
        ));
      }

      ultimoIndice = match.end;
    }

    if (ultimoIndice < codigo.length) {
      spans.add(TextSpan(
        text: codigo.substring(ultimoIndice),
        style: baseStyle,
      ));
    }

    return TextSpan(style: baseStyle, children: spans);
  }
}
