// Archivo: modules/archivo/frontend/lib/modulo_archivo.dart
import 'package:flutter/material.dart';
import 'package:ide_core/ide_core.dart';

import 'api_archivo.dart';
import 'ui/vista_archivo.dart';

/// Implementacion del contrato ModuloIde para el modulo Archivo.
class ModuloArchivo implements ModuloIde {
  ModuloArchivo({ApiArchivo? api}) : _api = api ?? ApiArchivo();

  final ApiArchivo _api;

  @override
  String get id => 'archivo';

  @override
  String get nombre => 'Archivo';

  @override
  IconData get icono => Icons.folder;

  @override
  Widget construirVista(BuildContext context) => VistaArchivo(api: _api);
}
