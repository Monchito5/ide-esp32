// Archivo: modules/herramientas/frontend/lib/modulo_herramientas.dart
import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'servicios/api_herramientas.dart';
import 'servicios/api_ide.dart';
import 'ui/vistas/vista_principal.dart';

/// Implementacion del contrato ModuloIde para el modulo Herramientas.
class ModuloHerramientas implements ModuloIde {
  ModuloHerramientas({ApiHerramientas? api, ApiIde? ideApi})
      : _api = api ?? ApiHerramientas(),
        _ideApi = ideApi ?? ApiIde();

  final ApiHerramientas _api;
  final ApiIde _ideApi;

  @override
  String get id => 'herramientas';

  @override
  String get nombre => 'Herramientas';

  @override
  IconData get icono => Icons.build;

  @override
  Widget construirVista(BuildContext context) =>
      VistaPrincipal(api: _api, ideApi: _ideApi);
}