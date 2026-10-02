// Archivo: modules/herramientas/frontend/lib/modulo_herramientas.dart
import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'servicios/api_herramientas.dart';
import 'ui/vistas/vista_principal.dart';

/// Implementacion del contrato ModuloIde para el modulo Herramientas.
class ModuloHerramientas implements ModuloIde {
  ModuloHerramientas({ApiHerramientas? api}) : _api = api ?? ApiHerramientas();

  final ApiHerramientas _api;

  @override
  String get id => 'herramientas';

  @override
  String get nombre => 'Herramientas';

  @override
  IconData get icono => Icons.build;

  @override
  Widget construirVista(BuildContext context) => VistaPrincipal(api: _api);
}
