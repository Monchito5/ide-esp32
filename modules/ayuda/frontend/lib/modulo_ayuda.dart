// Archivo: modules/ayuda/frontend/lib/modulo_ayuda.dart
import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'ui/vista_ayuda.dart';

/// Implementacion del contrato [ModuloIde] para el modulo de Ayuda.
class ModuloAyuda implements ModuloIde {
  const ModuloAyuda();

  @override
  String get id => 'ayuda';

  @override
  String get nombre => 'Ayuda';

  @override
  IconData get icono => Icons.help_outline;

  @override
  Widget construirVista(BuildContext context) => const VistaAyuda();
}
