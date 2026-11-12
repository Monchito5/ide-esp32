// Archivo: core/frontend/lib/nucleo/modulo_ide.dart
import 'package:flutter/material.dart';

/// Contrato que todo modulo del IDE debe implementar en su frontend.
abstract class ModuloIde {
  /// Identificador unico (snake_case).
  String get id;

  /// Nombre visible en la barra lateral.
  String get nombre;

  /// Icono representativo.
  IconData get icono;

  /// Construye la vista principal del modulo.
  Widget construirVista(BuildContext context);
}
