import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'servicios/api_sketch.dart';
import 'ui/vistas/vista_principal.dart';

/// Implementacion del contrato ModuloIde para Sketch.
class ModuloSketch implements ModuloIde {
  ModuloSketch({ApiSketch? api}) : _api = api ?? ApiSketch();

  final ApiSketch _api;

  @override
  String get id => 'sketch';

  @override
  String get nombre => 'Sketch';

  @override
  IconData get icono => Icons.code;

  @override
  Widget construirVista(BuildContext context) {
    return VistaPrincipal(api: _api);
  }
}
